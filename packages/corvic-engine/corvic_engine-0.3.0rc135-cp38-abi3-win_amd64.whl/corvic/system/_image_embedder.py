import abc
import asyncio
import dataclasses
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from typing import TYPE_CHECKING, Protocol, cast

import numpy as np
import polars as pl

from corvic import result
from corvic.system._embedder import (
    EmbedImageContext,
    EmbedImageResult,
    ImageEmbedder,
)

if TYPE_CHECKING:
    from PIL import Image
    from torch import FloatTensor


class RandomImageEmbedder(ImageEmbedder):
    """Embed inputs by choosing random vectors.

    Useful for testing.
    """

    @classmethod
    def model_name(cls) -> str:
        return "random"

    def embed(
        self, context: EmbedImageContext
    ) -> result.Ok[EmbedImageResult] | result.InvalidArgumentError:
        rng = np.random.default_rng()

        match context.expected_coordinate_bitwidth:
            case 64:
                coord_dtype = pl.Float64()
            case 32:
                coord_dtype = pl.Float32()

        return result.Ok(
            EmbedImageResult(
                context=context,
                embeddings=pl.Series(
                    rng.random(
                        size=(len(context.inputs), context.expected_vector_length)
                    ),
                    dtype=pl.List(
                        coord_dtype,
                    ),
                ),
            )
        )

    async def aembed(
        self,
        context: EmbedImageContext,
        worker_threads: ThreadPoolExecutor | None = None,
    ) -> result.Ok[EmbedImageResult] | result.InvalidArgumentError:
        return await asyncio.get_running_loop().run_in_executor(
            worker_threads, self.embed, context
        )


def image_from_bytes(
    image: bytes, mode: str = "RGB"
) -> result.Ok["Image.Image"] | result.InvalidArgumentError:
    from PIL import Image, UnidentifiedImageError

    try:
        return result.Ok(Image.open(BytesIO(initial_bytes=image)).convert(mode=mode))
    except UnidentifiedImageError:
        return result.InvalidArgumentError("invalid image format")


class TransformersImageModel(Protocol):
    """Generic class for a Model from transformers."""

    def eval(self): ...
    def get_image_features(*, pixel_values: "FloatTensor") -> "FloatTensor": ...


class TransformersProcessor(Protocol):
    """Generic class for a Processor from transformers."""

    def __call__(self, *, images: list["Image.Image"], return_tensors: str): ...


@dataclasses.dataclass
class LoadedModels:
    model: TransformersImageModel
    processor: TransformersProcessor


class HFModelImageEmbedder(ImageEmbedder):
    """Generic image embedder from hugging face models."""

    @classmethod
    @abc.abstractmethod
    def model_revision(cls) -> str: ...

    @abc.abstractmethod
    def load_models(self) -> LoadedModels: ...

    def embed(
        self, context: EmbedImageContext
    ) -> result.Ok[EmbedImageResult] | result.InvalidArgumentError:
        images = list["Image.Image"]()
        for initial_bytes in context.inputs:
            match image_from_bytes(image=initial_bytes):
                case result.Ok(image):
                    images.append(image)
                case result.InvalidArgumentError() as err:
                    return err

        match context.expected_coordinate_bitwidth:
            case 64:
                coord_dtype = pl.Float64()
            case 32:
                coord_dtype = pl.Float32()

        if not images:
            return result.Ok(
                EmbedImageResult(
                    context=context,
                    embeddings=pl.Series(
                        dtype=pl.List(
                            coord_dtype,
                        ),
                    ),
                )
            )

        models = self.load_models()
        model = models.model
        processor = models.processor
        model.eval()

        import torch

        with torch.no_grad():
            inputs = cast(
                dict[str, torch.FloatTensor],
                processor(images=images, return_tensors="pt"),
            )
            image_features = model.get_image_features(
                pixel_values=inputs["pixel_values"]
            )

        image_features_numpy = image_features.numpy()
        return result.Ok(
            EmbedImageResult(
                context=context,
                embeddings=pl.Series(
                    values=image_features_numpy[:, : context.expected_vector_length],
                    dtype=pl.List(
                        coord_dtype,
                    ),
                ),
            )
        )

    async def aembed(
        self,
        context: EmbedImageContext,
        worker_threads: ThreadPoolExecutor | None = None,
    ) -> result.Ok[EmbedImageResult] | result.InvalidArgumentError:
        return await asyncio.get_running_loop().run_in_executor(
            worker_threads, self.embed, context
        )


class Clip(HFModelImageEmbedder):
    """Clip image embedder.

    CLIP (Contrastive Language-Image Pre-Training) is a neural network trained
    on a variety of (image, text) pairs. It can be instructed in natural language
    to predict the most relevant text snippet, given an image, without
    directly optimizing for the task, similarly to the zero-shot capabilities of
    GPT-2 and 3. We found CLIP matches the performance of the original ResNet50
    on ImageNet “zero-shot” without using any of the original 1.28M labeled examples,
    overcoming several major challenges in computer vision.
    """

    @classmethod
    def model_name(cls) -> str:
        return "openai/clip-vit-base-patch32"

    @classmethod
    def model_revision(cls) -> str:
        return "5812e510083bb2d23fa43778a39ac065d205ed4d"

    def load_models(self) -> LoadedModels:
        from transformers.models.clip import (
            CLIPModel,
            CLIPProcessor,
        )

        model = cast(
            TransformersImageModel,
            CLIPModel.from_pretrained(  # pyright: ignore[reportUnknownMemberType]
                pretrained_model_name_or_path=self.model_name(),
                revision=self.model_revision(),
            ),
        )
        processor = cast(
            TransformersProcessor,
            CLIPProcessor.from_pretrained(  # pyright: ignore[reportUnknownMemberType]
                pretrained_model_name_or_path=self.model_name(),
                revision=self.model_revision(),
                use_fast=False,
            ),
        )
        return LoadedModels(model=model, processor=processor)


class SigLIP2(HFModelImageEmbedder):
    """SigLIP2 image embedder."""

    @classmethod
    def model_name(cls) -> str:
        return "google/siglip2-base-patch16-512"

    @classmethod
    def model_revision(cls) -> str:
        return "a89f5c5093f902bf39d3cd4d81d2c09867f0724b"

    def load_models(self):
        from transformers.models.auto.modeling_auto import AutoModel
        from transformers.models.auto.processing_auto import AutoProcessor

        model = cast(
            TransformersImageModel,
            AutoModel.from_pretrained(  # pyright: ignore[reportUnknownMemberType]
                pretrained_model_name_or_path=self.model_name(),
                revision=self.model_revision(),
                device_map="auto",
            ),
        )
        processor = cast(
            TransformersProcessor,
            AutoProcessor.from_pretrained(  # pyright: ignore[reportUnknownMemberType]
                pretrained_model_name_or_path=self.model_name(),
                revision=self.model_revision(),
                use_fast=True,
            ),
        )
        return LoadedModels(model=model, processor=processor)


class CombinedImageEmbedder(ImageEmbedder):
    @classmethod
    def model_name(cls) -> str:
        raise result.InvalidArgumentError(
            "CombinedImageEmbedder does not have a specific model name"
        )

    def __init__(self):
        self._embedders = {
            emb.model_name(): emb()
            for emb in [Clip, SigLIP2, RandomImageEmbedder, IdentityImageEmbedder]
        }

    def embed(
        self, context: EmbedImageContext
    ) -> result.Ok[EmbedImageResult] | result.InvalidArgumentError:
        embedder = self._embedders.get(context.model_name, None)
        if not embedder:
            return result.InvalidArgumentError(
                f"Unknown model name {context.model_name}"
            )
        return embedder.embed(context)

    async def aembed(
        self,
        context: EmbedImageContext,
        worker_threads: ThreadPoolExecutor | None = None,
    ) -> result.Ok[EmbedImageResult] | result.InvalidArgumentError:
        return await asyncio.get_running_loop().run_in_executor(
            worker_threads, self.embed, context
        )


class IdentityImageEmbedder(ImageEmbedder):
    """A deterministic image embedder.

    Embedding Process:
        - The input image is flattened into a 1D array of pixel intensity values
            (grayscale) with a max value of 127.
        - Pixel intensities are normalized to [0.0, 1.0] by dividing by 128.
        - The resulting list is truncated or padded to match the expected vector length.
    """

    @classmethod
    def model_name(cls) -> str:
        return "identity"

    def _image_to_embedding(
        self, image: "Image.Image", vector_length: int, *, normalization: bool = False
    ) -> list[float]:
        """Convert image data to a deterministic embedding vector.

        Use pixel intensity values to generate embeddings, with a value max of 127 so
        the embeddings are the same as those generated using ASCII with the
        IdentityTextEmbedder.
        """
        image_greyscale = np.array(image.convert("L"))

        pixel_values = pl.Series("pixels", image_greyscale.flatten().tolist()) % 128

        if normalization:
            pixel_values = pixel_values / 127

        if len(pixel_values) < vector_length:
            pixel_values = pixel_values.extend_constant(
                0, vector_length - len(pixel_values)
            )
        elif len(pixel_values) > vector_length:
            pixel_values = pixel_values[:vector_length]

        return pixel_values.to_list()

    def embed(
        self, context: EmbedImageContext
    ) -> result.Ok[EmbedImageResult] | result.InvalidArgumentError:
        images = list["Image.Image"]()

        for initial_bytes in context.inputs:
            match image_from_bytes(image=initial_bytes):
                case result.Ok(image):
                    images.append(image)
                case result.InvalidArgumentError() as err:
                    return err

        match context.expected_coordinate_bitwidth:
            case 64:
                coord_dtype = pl.Float64()
            case 32:
                coord_dtype = pl.Float32()

        if not images:
            return result.Ok(
                EmbedImageResult(
                    context=context,
                    embeddings=pl.Series(
                        dtype=pl.List(
                            coord_dtype,
                        ),
                    ),
                )
            )

        embeddings = [
            self._image_to_embedding(image, context.expected_vector_length)
            for image in images
        ]

        return result.Ok(
            EmbedImageResult(
                context=context,
                embeddings=pl.Series(
                    values=embeddings,
                    dtype=pl.List(coord_dtype),
                ),
            )
        )

    async def aembed(
        self,
        context: EmbedImageContext,
        worker_threads: ThreadPoolExecutor | None = None,
    ) -> result.Ok[EmbedImageResult] | result.InvalidArgumentError:
        return await asyncio.get_running_loop().run_in_executor(
            worker_threads, self.embed, context
        )

    def preimage(
        self,
        embedding: list[float],
        image_shape: tuple[int, int],
        *,
        normalized: bool = False,
    ) -> "Image.Image":
        """Reconstruct an image from a given embedding vector."""
        from PIL import Image

        if normalized:
            pixel_values = [round(value * 127) for value in embedding]
        else:
            pixel_values = [round(value) for value in embedding]

        num_pixels = image_shape[0] * image_shape[1]
        pixel_values = pixel_values[:num_pixels]

        image = Image.new("L", image_shape)
        image.putdata(pixel_values)

        return image
