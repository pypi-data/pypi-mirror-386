"""Operations that construct tables.

Each operation is the head of a log of one or more operations that when executed
produce a table.

To add a new operation type:

1. Add a protobuf message definition detailing the operations's arguments.

1. Add the operation to the TableComputeOp message as part of the oneof called "op"

1. Write a wrapper class that inherits from corvic.table.ops._Base (in this file).
   The wrapper should include properties for accessing the fields of the message.

1. Add the wrapper class to the "Op" union at the bottom of this file.

1. Note the mapping between the TableComputeOp field name for the new op and the
   wrapper class in corvic.table.ops._COMPUTE_OP_FIELD_NAME_TO_OP (in this file).

1. Add a case to the match statement in corvic.table.ops.from_proto.
"""

from __future__ import annotations

import dataclasses
import functools
import threading
from abc import ABC, abstractmethod
from collections import OrderedDict
from collections.abc import Iterable, Mapping, Sequence
from typing import (
    Any,
    Final,
    Literal,
    TypeAlias,
    cast,
    get_args,
    overload,
)

import cachetools
import more_itertools
import polars as pl
import pyarrow as pa
from google.protobuf import json_format, struct_pb2
from more_itertools import flatten

import corvic.op_graph.feature_types as feature_type
from corvic import eorm, pa_scalar, result
from corvic.op_graph._schema import Field
from corvic.op_graph.aggregation import Aggregation
from corvic.op_graph.aggregation import from_proto as aggregation_from_proto
from corvic.op_graph.encoders import EncodedColumn
from corvic.op_graph.encoders import from_proto as encoder_type_from_proto
from corvic.op_graph.errors import OpParseError
from corvic.op_graph.feature_types import FeatureType, ForeignKey
from corvic.op_graph.feature_types import from_proto as ftype_from_proto
from corvic.op_graph.row_filters import RowFilter
from corvic.op_graph.row_filters import from_proto as row_filters_from_proto
from corvic.op_graph.sample_strategy import SampleStrategy
from corvic.op_graph.sample_strategy import from_proto as sample_strategy_from_proto
from corvic.pa_scalar import PyValue, Scalar, from_value, to_value
from corvic.proto_wrapper import OneofProtoWrapper
from corvic_generated.algorithm.graph.v1 import graph_pb2
from corvic_generated.orm.v1 import table_pb2

ProtoOp = (
    table_pb2.SelectFromStagingOp
    | table_pb2.RenameColumnsOp
    | table_pb2.JoinOp
    | table_pb2.SelectColumnsOp
    | table_pb2.LimitRowsOp
    | table_pb2.OffsetRowsOp
    | table_pb2.OrderByOp
    | table_pb2.FilterRowsOp
    | table_pb2.DistinctRowsOp
    | table_pb2.UpdateMetadataOp
    | table_pb2.SetMetadataOp
    | table_pb2.RemoveFromMetadataOp
    | table_pb2.UpdateFeatureTypesOp
    | table_pb2.RollupByAggregationOp
    | table_pb2.EmptyOp
    | table_pb2.EmbedNode2vecFromEdgeListsOp
    | table_pb2.EmbeddingMetricsOp
    | table_pb2.EmbeddingCoordinatesOp
    | table_pb2.ReadFromParquetOp
    | table_pb2.SelectFromVectorStagingOp
    | table_pb2.ConcatOp
    | table_pb2.UnnestStructOp
    | table_pb2.NestIntoStructOp
    | table_pb2.AddLiteralColumnOp
    | table_pb2.CombineColumnsOp
    | table_pb2.EmbedColumnOp
    | table_pb2.EncodeColumnOp
    | table_pb2.AggregateColumnsOp
    | table_pb2.CorrelateColumnsOp
    | table_pb2.HistogramColumnOp
    | table_pb2.ConvertColumnToStringOp
    | table_pb2.AddRowIndexOp
    | table_pb2.OutputCsvOp
    | table_pb2.TruncateListOp
    | table_pb2.UnionOp
    | table_pb2.EmbedImageColumnOp
    | table_pb2.AddDecisionTreeSummaryOp
    | table_pb2.UnnestListOp
    | table_pb2.SampleRowsOp
    | table_pb2.DescribeColumnsOp
    | table_pb2.InMemoryInputOp
)


@overload
def from_proto(
    proto: table_pb2.TableComputeOp,
    parent_ops: list[Op] | None = None,
    *,
    skip_validate: bool = False,
) -> Op: ...


@overload
def from_proto(
    proto: table_pb2.SelectFromStagingOp,
    parent_ops: list[Op] | None = None,
    *,
    skip_validate: bool = False,
) -> SelectFromStaging: ...


@overload
def from_proto(
    proto: table_pb2.RenameColumnsOp,
    parent_ops: list[Op] | None = None,
    *,
    skip_validate: bool = False,
) -> RenameColumns: ...


@overload
def from_proto(
    proto: table_pb2.JoinOp,
    parent_ops: list[Op] | None = None,
    *,
    skip_validate: bool = False,
) -> Join: ...


@overload
def from_proto(
    proto: table_pb2.SelectColumnsOp,
    parent_ops: list[Op] | None = None,
    *,
    skip_validate: bool = False,
) -> SelectColumns: ...


@overload
def from_proto(
    proto: table_pb2.LimitRowsOp,
    parent_ops: list[Op] | None = None,
    *,
    skip_validate: bool = False,
) -> LimitRows: ...


@overload
def from_proto(
    proto: table_pb2.OffsetRowsOp,
    parent_ops: list[Op] | None = None,
    *,
    skip_validate: bool = False,
) -> OffsetRows: ...


@overload
def from_proto(
    proto: table_pb2.OrderByOp,
    parent_ops: list[Op] | None = None,
    *,
    skip_validate: bool = False,
) -> OrderBy: ...


@overload
def from_proto(
    proto: table_pb2.FilterRowsOp,
    parent_ops: list[Op] | None = None,
    *,
    skip_validate: bool = False,
) -> FilterRows: ...


@overload
def from_proto(
    proto: table_pb2.DistinctRowsOp,
    parent_ops: list[Op] | None = None,
    *,
    skip_validate: bool = False,
) -> DistinctRows: ...


@overload
def from_proto(
    proto: table_pb2.UpdateMetadataOp,
    parent_ops: list[Op] | None = None,
    *,
    skip_validate: bool = False,
) -> UpdateMetadata: ...


@overload
def from_proto(
    proto: table_pb2.SetMetadataOp,
    parent_ops: list[Op] | None = None,
    *,
    skip_validate: bool = False,
) -> SetMetadata: ...


@overload
def from_proto(
    proto: table_pb2.RemoveFromMetadataOp,
    parent_ops: list[Op] | None = None,
    *,
    skip_validate: bool = False,
) -> RemoveFromMetadata: ...


@overload
def from_proto(
    proto: table_pb2.UpdateFeatureTypesOp,
    parent_ops: list[Op] | None = None,
    *,
    skip_validate: bool = False,
) -> UpdateFeatureTypes: ...


@overload
def from_proto(
    proto: table_pb2.RollupByAggregationOp,
    parent_ops: list[Op] | None = None,
    *,
    skip_validate: bool = False,
) -> RollupByAggregation: ...


@overload
def from_proto(
    proto: table_pb2.EmptyOp,
    parent_ops: list[Op] | None = None,
    *,
    skip_validate: bool = False,
) -> Empty: ...


@overload
def from_proto(
    proto: table_pb2.InMemoryInputOp,
    parent_ops: list[Op] | None = None,
    *,
    skip_validate: bool = False,
) -> InMemoryInput: ...


@overload
def from_proto(
    proto: table_pb2.EmbedNode2vecFromEdgeListsOp,
    parent_ops: list[Op] | None = None,
    *,
    skip_validate: bool = False,
) -> EmbedNode2vecFromEdgeLists: ...


@overload
def from_proto(
    proto: table_pb2.EmbeddingMetricsOp,
    parent_ops: list[Op] | None = None,
    *,
    skip_validate: bool = False,
) -> EmbeddingMetrics: ...


@overload
def from_proto(
    proto: table_pb2.EmbeddingCoordinatesOp,
    parent_ops: list[Op] | None = None,
    *,
    skip_validate: bool = False,
) -> EmbeddingCoordinates: ...


@overload
def from_proto(
    proto: table_pb2.ReadFromParquetOp,
    parent_ops: list[Op] | None = None,
    *,
    skip_validate: bool = False,
) -> ReadFromParquet: ...


@overload
def from_proto(
    proto: table_pb2.SelectFromVectorStagingOp,
    parent_ops: list[Op] | None = None,
    *,
    skip_validate: bool = False,
) -> SelectFromVectorStaging: ...


@overload
def from_proto(
    proto: table_pb2.ConcatOp,
    parent_ops: list[Op] | None = None,
    *,
    skip_validate: bool = False,
) -> Concat: ...


@overload
def from_proto(
    proto: table_pb2.UnnestStructOp,
    parent_ops: list[Op] | None = None,
    *,
    skip_validate: bool = False,
) -> UnnestStruct: ...


@overload
def from_proto(
    proto: table_pb2.NestIntoStructOp,
    parent_ops: list[Op] | None = None,
    *,
    skip_validate: bool = False,
) -> NestIntoStruct: ...


@overload
def from_proto(
    proto: table_pb2.AddLiteralColumnOp,
    parent_ops: list[Op] | None = None,
    *,
    skip_validate: bool = False,
) -> AddLiteralColumn: ...


@overload
def from_proto(
    proto: table_pb2.CombineColumnsOp,
    parent_ops: list[Op] | None = None,
    *,
    skip_validate: bool = False,
) -> CombineColumns: ...


@overload
def from_proto(
    proto: table_pb2.EmbedColumnOp,
    parent_ops: list[Op] | None = None,
    *,
    skip_validate: bool = False,
) -> EmbedColumn: ...


@overload
def from_proto(
    proto: table_pb2.EncodeColumnOp,
    parent_ops: list[Op] | None = None,
    *,
    skip_validate: bool = False,
) -> EncodeColumns: ...


@overload
def from_proto(
    proto: table_pb2.AggregateColumnsOp,
    parent_ops: list[Op] | None = None,
    *,
    skip_validate: bool = False,
) -> AggregateColumns: ...


@overload
def from_proto(
    proto: table_pb2.CorrelateColumnsOp,
    parent_ops: list[Op] | None = None,
    *,
    skip_validate: bool = False,
) -> CorrelateColumns: ...


@overload
def from_proto(
    proto: table_pb2.HistogramColumnOp,
    parent_ops: list[Op] | None = None,
    *,
    skip_validate: bool = False,
) -> HistogramColumn: ...


@overload
def from_proto(
    proto: table_pb2.ConvertColumnToStringOp,
    parent_ops: list[Op] | None = None,
    *,
    skip_validate: bool = False,
) -> ConvertColumnToString: ...


@overload
def from_proto(
    proto: table_pb2.AddRowIndexOp,
    parent_ops: list[Op] | None = None,
    *,
    skip_validate: bool = False,
) -> AddRowIndex: ...


@overload
def from_proto(
    proto: table_pb2.OutputCsvOp,
    parent_ops: list[Op] | None = None,
    *,
    skip_validate: bool = False,
) -> OutputCsv: ...


@overload
def from_proto(
    proto: table_pb2.TruncateListOp,
    parent_ops: list[Op] | None = None,
    *,
    skip_validate: bool = False,
) -> TruncateList: ...


@overload
def from_proto(
    proto: table_pb2.UnionOp,
    parent_ops: list[Op] | None = None,
    *,
    skip_validate: bool = False,
) -> Union: ...


@overload
def from_proto(
    proto: table_pb2.EmbedImageColumnOp,
    parent_ops: list[Op] | None = None,
    *,
    skip_validate: bool = False,
) -> EmbedImageColumn: ...


@overload
def from_proto(
    proto: table_pb2.AddDecisionTreeSummaryOp,
    parent_ops: list[Op] | None = None,
    *,
    skip_validate: bool = False,
) -> AddDecisionTreeSummary: ...


@overload
def from_proto(
    proto: table_pb2.UnnestListOp,
    parent_ops: list[Op] | None = None,
    *,
    skip_validate: bool = False,
) -> UnnestList: ...


@overload
def from_proto(
    proto: table_pb2.SampleRowsOp,
    parent_ops: list[Op] | None = None,
    *,
    skip_validate: bool = False,
) -> SampleRows: ...


@overload
def from_proto(
    proto: table_pb2.DescribeColumnsOp,
    parent_ops: list[Op] | None = None,
    *,
    skip_validate: bool = False,
) -> DescribeColumns: ...


def from_proto(  # noqa: C901, PLR0915
    proto: ProtoOp | table_pb2.TableComputeOp,
    parent_ops: list[Op] | None = None,
    *,
    skip_validate: bool = False,
) -> Op:
    """Create an Op wrapper around an Op protobuf message."""
    match proto:
        case table_pb2.TableComputeOp():
            pass
        case table_pb2.EmptyOp():
            proto = table_pb2.TableComputeOp(empty=proto)
        case table_pb2.InMemoryInputOp():
            proto = table_pb2.TableComputeOp(in_memory_input=proto)
        case table_pb2.SelectFromStagingOp():
            proto = table_pb2.TableComputeOp(select_from_staging=proto)
        case table_pb2.RenameColumnsOp():
            proto = table_pb2.TableComputeOp(rename_columns=proto)
        case table_pb2.JoinOp():
            proto = table_pb2.TableComputeOp(join=proto)
        case table_pb2.SelectColumnsOp():
            proto = table_pb2.TableComputeOp(select_columns=proto)
        case table_pb2.LimitRowsOp():
            proto = table_pb2.TableComputeOp(limit_rows=proto)
        case table_pb2.OffsetRowsOp():
            proto = table_pb2.TableComputeOp(offset_rows=proto)
        case table_pb2.OrderByOp():
            proto = table_pb2.TableComputeOp(order_by=proto)
        case table_pb2.FilterRowsOp():
            proto = table_pb2.TableComputeOp(filter_rows=proto)
        case table_pb2.DistinctRowsOp():
            proto = table_pb2.TableComputeOp(distinct_rows=proto)
        case table_pb2.UpdateMetadataOp():
            proto = table_pb2.TableComputeOp(update_metadata=proto)
        case table_pb2.SetMetadataOp():
            proto = table_pb2.TableComputeOp(set_metadata=proto)
        case table_pb2.RemoveFromMetadataOp():
            proto = table_pb2.TableComputeOp(remove_from_metadata=proto)
        case table_pb2.UpdateFeatureTypesOp():
            proto = table_pb2.TableComputeOp(update_feature_types=proto)
        case table_pb2.RollupByAggregationOp():
            proto = table_pb2.TableComputeOp(rollup_by_aggregation=proto)
        case table_pb2.EmbedNode2vecFromEdgeListsOp():
            proto = table_pb2.TableComputeOp(embed_node2vec_from_edge_lists=proto)
        case table_pb2.EmbeddingMetricsOp():
            proto = table_pb2.TableComputeOp(embedding_metrics=proto)
        case table_pb2.EmbeddingCoordinatesOp():
            proto = table_pb2.TableComputeOp(embedding_coordinates=proto)
        case table_pb2.ReadFromParquetOp():
            proto = table_pb2.TableComputeOp(read_from_parquet=proto)
        case table_pb2.SelectFromVectorStagingOp():
            proto = table_pb2.TableComputeOp(select_from_vector_staging=proto)
        case table_pb2.ConcatOp():
            proto = table_pb2.TableComputeOp(concat=proto)
        case table_pb2.UnnestStructOp():
            proto = table_pb2.TableComputeOp(unnest_struct=proto)
        case table_pb2.NestIntoStructOp():
            proto = table_pb2.TableComputeOp(nest_into_struct=proto)
        case table_pb2.AddLiteralColumnOp():
            proto = table_pb2.TableComputeOp(add_literal_column=proto)
        case table_pb2.CombineColumnsOp():
            proto = table_pb2.TableComputeOp(combine_columns=proto)
        case table_pb2.EmbedColumnOp():
            proto = table_pb2.TableComputeOp(embed_column=proto)
        case table_pb2.EncodeColumnOp():
            proto = table_pb2.TableComputeOp(encode_column=proto)
        case table_pb2.AggregateColumnsOp():
            proto = table_pb2.TableComputeOp(aggregate_columns=proto)
        case table_pb2.CorrelateColumnsOp():
            proto = table_pb2.TableComputeOp(correlate_columns=proto)
        case table_pb2.HistogramColumnOp():
            proto = table_pb2.TableComputeOp(histogram_column=proto)
        case table_pb2.ConvertColumnToStringOp():
            proto = table_pb2.TableComputeOp(convert_column_string=proto)
        case table_pb2.AddRowIndexOp():
            proto = table_pb2.TableComputeOp(row_index=proto)
        case table_pb2.OutputCsvOp():
            proto = table_pb2.TableComputeOp(output_csv=proto)
        case table_pb2.TruncateListOp():
            proto = table_pb2.TableComputeOp(truncate_list=proto)
        case table_pb2.UnionOp():
            proto = table_pb2.TableComputeOp(union=proto)
        case table_pb2.EmbedImageColumnOp():
            proto = table_pb2.TableComputeOp(embed_image_column=proto)
        case table_pb2.AddDecisionTreeSummaryOp():
            proto = table_pb2.TableComputeOp(add_decision_tree_summary=proto)
        case table_pb2.UnnestListOp():
            proto = table_pb2.TableComputeOp(unnest_list=proto)
        case table_pb2.SampleRowsOp():
            proto = table_pb2.TableComputeOp(sample_rows=proto)
        case table_pb2.DescribeColumnsOp():
            proto = table_pb2.TableComputeOp(describe_columns=proto)
    return _from_compute_op(proto, parent_ops, skip_validate=skip_validate)


def empty() -> Op:
    return from_proto(table_pb2.EmptyOp(), skip_validate=True)


def in_memory_input(
    input_name: str,
    *,
    schema: Schema | None = None,
) -> InMemoryInput:
    schema_bytes = schema.to_arrow().serialize().to_pybytes() if schema else None
    ft_protos = [field.ftype.to_proto() for field in schema] if schema else []
    return from_proto(
        table_pb2.InMemoryInputOp(
            input_name=input_name,
            arrow_schema=schema_bytes,
            feature_types=ft_protos,
        ),
        skip_validate=True,
    )


def from_bytes(serialized_proto: bytes) -> Op:
    """Deserialize an Op protobuf message directly into a wrapper."""
    if not serialized_proto:
        return empty()

    proto = table_pb2.TableComputeOp()
    _ = proto.ParseFromString(serialized_proto)
    return from_proto(proto)


def from_staging(
    blob_names: Sequence[str],
    arrow_schema: pa.Schema,
    feature_types: Sequence[FeatureType],
    expected_rows: int,
) -> result.Ok[SelectFromStaging] | result.InvalidArgumentError:
    """Build a SelectFromStaging Op."""
    if len(arrow_schema) != len(feature_types):
        return result.InvalidArgumentError(
            "length of arrow_schema must match length of feature_types"
        )
    if any(
        isinstance(feature, ForeignKey) and not feature.referenced_source_id
        for feature in feature_types
    ):
        return result.InvalidArgumentError(
            "referenced_source_id cannot be empty in foreign key"
        )
    return result.Ok(
        from_proto(
            table_pb2.SelectFromStagingOp(
                blob_names=blob_names,
                arrow_schema=arrow_schema.serialize().to_pybytes(),
                feature_types=[
                    feature_type.to_proto() for feature_type in feature_types
                ],
                expected_rows=expected_rows,
            ),
            skip_validate=True,
        )
    )


def from_parquet(
    blob_names: Sequence[str],
    arrow_schema: pa.Schema,
    feature_types: Sequence[FeatureType],
    expected_rows: int,
) -> result.Ok[ReadFromParquet] | result.InvalidArgumentError:
    """Build a ReadFromParquet Op."""
    if len(arrow_schema) != len(feature_types):
        return result.InvalidArgumentError(
            "length of arrow_schema must match length of feature_types"
        )
    if any(
        isinstance(feature, ForeignKey) and not feature.referenced_source_id
        for feature in feature_types
    ):
        return result.InvalidArgumentError(
            "referenced_source_id cannot be empty in foreign key"
        )
    return result.Ok(
        from_proto(
            table_pb2.ReadFromParquetOp(
                blob_names=blob_names,
                arrow_schema=arrow_schema.serialize().to_pybytes(),
                feature_types=[
                    feature_type.to_proto() for feature_type in feature_types
                ],
                expected_rows=expected_rows,
            ),
            skip_validate=True,
        )
    )


def embed_node2vec_from_edge_lists(
    edge_list_tables: Sequence[EdgeListTable], params: graph_pb2.Node2VecParameters
) -> result.Ok[EmbedNode2vecFromEdgeLists]:
    return result.Ok(
        from_proto(
            table_pb2.EmbedNode2vecFromEdgeListsOp(
                edge_list_tables=[
                    edge_list.to_proto() for edge_list in edge_list_tables
                ],
                node2vec_parameters=params,
            ),
            skip_validate=True,
        )
    )


def _validate_embedding_column(
    table: Op, embedding_column_name: str
) -> result.Ok[None] | result.InvalidArgumentError:
    embedding_field = table.schema.get(embedding_column_name)
    if not embedding_field:
        return result.InvalidArgumentError(
            "no column with the given name", given_name=embedding_column_name
        )
    dtype = embedding_field.dtype
    if isinstance(dtype, pa.ListType | pa.LargeListType | pa.FixedSizeListType):
        dtype = cast(
            "pa.ListType[pa.DataType] | pa.LargeListType[pa.DataType] \
                | pa.FixedSizeListType[pa.DataType]",
            dtype,
        )
        inner_dtype = dtype.value_field.type
        if not (
            pa.types.is_floating(inner_dtype)
            | pa.types.is_integer(inner_dtype)
            | pa.types.is_boolean(inner_dtype)
        ):
            return result.InvalidArgumentError(
                "embedding column dtype must be a list of floats"
            )
    else:
        return result.InvalidArgumentError(
            "embedding column dtype must be a list of floats"
        )

    return result.Ok(None)


def quality_metrics_from_embedding(
    table: Op, embedding_column_name: str
) -> result.Ok[EmbeddingMetrics] | result.InvalidArgumentError:
    match _validate_embedding_column(table, embedding_column_name):
        case result.InvalidArgumentError() as err:
            return err
        case result.Ok():
            return result.Ok(
                from_proto(
                    table_pb2.EmbeddingMetricsOp(
                        table=table.to_proto(),
                        embedding_column_name=embedding_column_name,
                    ),
                    skip_validate=True,
                )
            )


def coordinates_from_embedding(
    table: Op,
    embedding_column_name: str,
    output_dims: int,
    metric: Literal["cosine", "euclidean"] = "cosine",
) -> result.Ok[EmbeddingCoordinates] | result.InvalidArgumentError:
    match _validate_embedding_column(table, embedding_column_name):
        case result.InvalidArgumentError() as err:
            return err
        case result.Ok():
            return result.Ok(
                from_proto(
                    table_pb2.EmbeddingCoordinatesOp(
                        table=table.to_proto(),
                        n_components=output_dims,
                        metric=metric,
                        embedding_column_name=embedding_column_name,
                    ),
                    skip_validate=True,
                )
            )


def concat(
    tables: list[Op], how: ConcatMethod = "vertical", *, rechunk: bool = False
) -> result.Ok[Concat | Empty] | result.InvalidArgumentError:
    if not tables:
        return result.Ok(from_proto(table_pb2.EmptyOp(), skip_validate=True))
    schema = tables[0].schema.to_arrow()

    if how == "vertical":
        schema = tables[0].schema.to_arrow()
        for table in tables[1:]:
            if schema != table.schema.to_arrow():
                return result.InvalidArgumentError("table schemas do not match")

    return result.Ok(
        from_proto(
            table_pb2.ConcatOp(tables=[table.to_proto() for table in tables], how=how),
            skip_validate=True,
        )
    )


def union(
    tables: list[Op], *, distinct: bool = False
) -> result.Ok[Union | Empty] | result.InvalidArgumentError:
    if not tables:
        return result.Ok(from_proto(table_pb2.EmptyOp(), skip_validate=True))
    schema = tables[0].schema.to_arrow()
    for table in tables[1:]:
        if schema != table.schema.to_arrow():
            return result.InvalidArgumentError("table schemas do not match")

    return result.Ok(
        from_proto(
            table_pb2.UnionOp(
                sources=[table.to_proto() for table in tables], distinct=distinct
            ),
            skip_validate=True,
        )
    )


def _table_compute_op_cache_key(
    proto: table_pb2.TableComputeOp, parent_ops: list[Op] | None, *, skip_validate: bool
):
    # N.B. parent_op is not part of the hash key on purpose. Since
    # ops in op-graphs are immutable it's safe to reuse parent
    # in arbitrary graphs.
    return proto.SerializeToString(deterministic=True)


def _list_elem_type(
    dtype: pa.ListType | pa.FixedSizeListType | pa.LargeListType,
) -> pa.DataType:
    return dtype.value_type


@cachetools.cached(
    cache=cachetools.LRUCache(maxsize=128),
    key=_table_compute_op_cache_key,
    lock=threading.Lock(),
)
def _from_compute_op(
    proto: table_pb2.TableComputeOp, parent_ops: list[Op] | None, *, skip_validate: bool
) -> Op:
    if not skip_validate:
        import protovalidate

        protovalidate.validate(proto)
    field_name = proto.WhichOneof(_Base.oneof_name())
    if not field_name:
        # If no field is set promote to the empty op. This matches the behavior in
        # from_bytes where an empty string is promoted to empty.
        return empty()
    new_op_type = _COMPUTE_OP_FIELD_NAME_TO_OP.get(field_name)
    if new_op_type is None:
        raise result.InvalidArgumentError(
            "unsupported operation type", operation_type=field_name
        )
    return new_op_type(proto, parent_ops if parent_ops else [])


class _Base(OneofProtoWrapper[table_pb2.TableComputeOp], ABC):
    """Base type for all log operations.

    Each operation is the head of a log, potentially referencing other operations
    to construct tables.

    Operations are serialized by protobuf, but the main way to use
    operations are the wrapper classes, which handle convenience properties,
    and the main way to construct ops is via this class, which validates parameters
    and implicit arguments.
    """

    _parents: list[Op]

    def __init__(self, proto: table_pb2.TableComputeOp, parents: list[Op]):
        super().__init__(proto)
        self._parents = parents

    @functools.cached_property
    def schema(self) -> Schema:
        if isinstance(self, Op):
            return Schema.from_ops(self)
        raise result.InvalidArgumentError("unsupported schema on op")

    @classmethod
    def oneof_name(cls) -> str:
        return "op"

    @classmethod
    def expected_oneof_field(cls) -> str:
        """Returns the name of field for this type in the root proto op type."""
        if cls not in _OP_TO_COMPUTE_OP_FIELD_NAME:
            raise OpParseError(
                "operation field name must registered in _COMPUTE_OP_FIELD_NAME_TO_OP"
            )
        return _OP_TO_COMPUTE_OP_FIELD_NAME[cls]

    @abstractmethod
    def sources(self) -> list[Op]:
        """Returns the source tables that this operation depends on (empty if none)."""

    def _check_columns_valid(
        self, columns: Mapping[str, Any] | Sequence[str] | str
    ) -> result.Ok[None] | result.InvalidArgumentError:
        if isinstance(columns, str):
            columns = [columns]

        if not columns:
            return result.InvalidArgumentError("columns cannot be empty")

        for column in columns:
            if not self.schema.has_column(column):
                return result.InvalidArgumentError(
                    "op schema has no column with that name", name=column
                )
        if len(set(columns)) != len(columns):
            return result.InvalidArgumentError("columns must be unique")
        return result.Ok(None)

    def _check_join_columns(
        self,
        right: Op,
        left_join_columns: Sequence[str],
        right_join_columns: Sequence[str],
    ) -> result.Ok[None] | result.InvalidArgumentError:
        if len(left_join_columns) != len(right_join_columns):
            return result.InvalidArgumentError(
                "number of matching columns must be the same"
            )

        match self._check_columns_valid(left_join_columns):
            case result.InvalidArgumentError() as err:
                return err
            case result.Ok():
                pass
        match right._check_columns_valid(right_join_columns):  # noqa: SLF001
            case result.InvalidArgumentError() as err:
                return err
            case result.Ok():
                pass

        for left_field_name, right_field_name in zip(
            left_join_columns, right_join_columns, strict=False
        ):
            left_field = self.schema.get(left_field_name)
            right_field = right.schema.get(right_field_name)
            if not left_field or not right_field:
                return result.InvalidArgumentError("schema does not contain column")
        return result.Ok(None)

    def join(
        self,
        right: Op,
        left_on: Sequence[str] | str,
        right_on: Sequence[str] | str,
        how: table_pb2.JoinType | Literal["inner", "left outer"],
    ):
        if isinstance(how, str):
            match how:
                case "inner":
                    how = table_pb2.JOIN_TYPE_INNER
                case "left outer":
                    how = table_pb2.JOIN_TYPE_LEFT_OUTER
        if how == table_pb2.JOIN_TYPE_UNSPECIFIED:
            return result.InvalidArgumentError("how must be specified")

        if isinstance(left_on, str):
            left_on = [left_on]
        if isinstance(right_on, str):
            right_on = [right_on]

        match self._check_join_columns(
            right,
            left_join_columns=left_on,
            right_join_columns=right_on,
        ):
            case result.InvalidArgumentError() as err:
                return err
            case result.Ok():
                pass

        return result.Ok(
            from_proto(
                table_pb2.JoinOp(
                    left_source=self.to_proto(),
                    right_source=right.to_proto(),
                    left_join_columns=left_on,
                    right_join_columns=right_on,
                    how=how,
                ),
                skip_validate=True,
            )
        )

    def rename_columns(
        self, old_name_to_new: Mapping[str, str]
    ) -> result.InvalidArgumentError | result.Ok[RenameColumns]:
        match self._check_columns_valid(old_name_to_new):
            case result.InvalidArgumentError() as err:
                return err
            case _:
                pass

        new_names = set(old_name_to_new.values())
        if len(new_names) != len(old_name_to_new):
            return result.InvalidArgumentError("table column names must be unique")

        for new_name in new_names:
            if self.schema.has_column(new_name) and new_name not in old_name_to_new:
                return result.InvalidArgumentError(
                    "op schema already has a column with that name", name=new_name
                )

        return result.Ok(
            from_proto(
                table_pb2.RenameColumnsOp(
                    source=self._proto, old_names_to_new=old_name_to_new
                ),
                skip_validate=True,
            )
        )

    def select_columns(self, columns: Sequence[str]):
        if isinstance(columns, str):
            # N.B. if we dont explicitly handle the lone string type like this
            # we end up in the unfortuname situation where keys_to_remove
            # silently becomes a list of one character string.
            # I.e., a string is a valid sequence of strings
            columns = [columns]

        if len(columns) > 0:
            match self._check_columns_valid(columns):
                case result.InvalidArgumentError() as err:
                    return err
                case result.Ok():
                    pass

        return result.Ok(
            from_proto(
                table_pb2.SelectColumnsOp(source=self._proto, columns=columns),
                skip_validate=True,
            )
        )

    def limit_rows(
        self, num_rows: int
    ) -> result.Ok[LimitRows] | result.InvalidArgumentError:
        if num_rows <= 0:
            return result.InvalidArgumentError("num_rows must be positive")
        if isinstance(self, LimitRows):
            proto = self.to_proto().limit_rows
            proto.num_rows = min(proto.num_rows, num_rows)
        else:
            proto = table_pb2.LimitRowsOp(source=self._proto, num_rows=num_rows)
        return result.Ok(from_proto(proto, skip_validate=True))

    def offset_rows(
        self, num_rows: int
    ) -> result.Ok[OffsetRows] | result.InvalidArgumentError:
        if num_rows <= 0:
            return result.InvalidArgumentError("num_rows must be positive")
        proto = table_pb2.OffsetRowsOp(source=self._proto, num_rows=num_rows)
        return result.Ok(from_proto(proto, skip_validate=True))

    def order_by(
        self, columns: Sequence[str], *, desc: bool
    ) -> result.Ok[OrderBy] | result.InvalidArgumentError:
        match self._check_columns_valid(columns):
            case result.InvalidArgumentError() as err:
                return err
            case result.Ok():
                pass

        proto = table_pb2.OrderByOp(source=self._proto, columns=columns, desc=desc)
        return result.Ok(from_proto(proto, skip_validate=True))

    def update_metadata(
        self, metadata_updates: Mapping[str, Any]
    ) -> result.Ok[UpdateMetadata]:
        proto = table_pb2.UpdateMetadataOp(source=self._proto)
        proto.metadata_updates.update(metadata_updates)
        return result.Ok(from_proto(proto, skip_validate=True))

    def set_metadata(self, new_metadata: Mapping[str, Any]) -> result.Ok[SetMetadata]:
        proto = table_pb2.SetMetadataOp(source=self._proto)
        proto.new_metadata.update(new_metadata)
        return result.Ok(from_proto(proto, skip_validate=True))

    def remove_from_metadata(
        self, keys_to_remove: Sequence[str]
    ) -> result.Ok[RemoveFromMetadata]:
        if isinstance(keys_to_remove, str):
            # N.B. if we dont explicitly handle the lone string type like this
            # we end up in the unfortunate situation where keys_to_remove
            # silently becomes a list of one character string.
            # I.e., a string is a valid sequence of strings
            keys_to_remove = [keys_to_remove]
        proto = table_pb2.RemoveFromMetadataOp(
            source=self._proto, keys_to_remove=keys_to_remove
        )
        return result.Ok(from_proto(proto, skip_validate=True))

    def update_feature_types(
        self, new_feature_types: Mapping[str, FeatureType]
    ) -> result.Ok[UpdateFeatureTypes] | result.InvalidArgumentError:
        match self._check_columns_valid(new_feature_types):
            case result.InvalidArgumentError() as err:
                return err
            case result.Ok():
                pass

        if any(
            isinstance(feature, ForeignKey) and not feature.referenced_source_id
            for feature in new_feature_types.values()
        ):
            return result.InvalidArgumentError(
                "referenced_source_id cannot be empty in foreign key"
            )

        new_feature_types_proto = {
            k: v.to_proto() for k, v in new_feature_types.items()
        }

        if isinstance(self, UpdateFeatureTypes):
            proto = self.to_proto().update_feature_types
            for name, ftype in proto.new_feature_types.items():
                if name not in new_feature_types_proto:
                    new_feature_types_proto[name] = ftype
            proto = table_pb2.UpdateFeatureTypesOp(
                source=proto.source, new_feature_types=new_feature_types_proto
            )
        else:
            proto = table_pb2.UpdateFeatureTypesOp(
                source=self._proto, new_feature_types=new_feature_types_proto
            )
        return result.Ok(from_proto(proto, skip_validate=True))

    def rollup_by_aggregation(  # noqa: C901
        self,
        group_by: Sequence[str] | str,
        target: str,
        aggregation: (
            table_pb2.AggregationType
            | Literal["count", "avg", "mode", "min", "max", "sum"]
        ),
    ) -> result.Ok[RollupByAggregation] | result.InvalidArgumentError:
        match self._check_columns_valid(group_by):
            case result.InvalidArgumentError() as err:
                return err
            case result.Ok():
                pass
        match self._check_columns_valid(target):
            case result.InvalidArgumentError() as err:
                return err
            case result.Ok():
                pass

        if isinstance(aggregation, str):
            match aggregation:
                case "count":
                    aggregation = table_pb2.AGGREGATION_TYPE_COUNT
                case "avg":
                    aggregation = table_pb2.AGGREGATION_TYPE_AVG
                case "mode":
                    aggregation = table_pb2.AGGREGATION_TYPE_MODE
                case "min":
                    aggregation = table_pb2.AGGREGATION_TYPE_MIN
                case "max":
                    aggregation = table_pb2.AGGREGATION_TYPE_MAX
                case "sum":
                    aggregation = table_pb2.AGGREGATION_TYPE_SUM

        if aggregation == table_pb2.AGGREGATION_TYPE_UNSPECIFIED:
            return result.InvalidArgumentError("aggregation must be specified")

        if isinstance(group_by, str):
            group_by = [group_by]

        return result.Ok(
            from_proto(
                table_pb2.RollupByAggregationOp(
                    source=self.to_proto(),
                    group_by_column_names=group_by,
                    target_column_name=target,
                    aggregation_type=aggregation,
                ),
                skip_validate=True,
            )
        )

    def filter_rows(self, row_filter: RowFilter) -> result.Ok[FilterRows]:
        return result.Ok(
            from_proto(
                table_pb2.FilterRowsOp(
                    source=self.to_proto(), row_filter=row_filter.to_proto()
                ),
                skip_validate=True,
            )
        )

    def unnest_struct(
        self, column_name: str
    ) -> result.Ok[UnnestStruct] | result.InvalidArgumentError:
        struct_field = self.schema.get(column_name)
        if struct_field is None or not isinstance(struct_field.dtype, pa.StructType):
            return result.InvalidArgumentError(
                "no struct column with given name", column_name=column_name
            )

        for i in range(struct_field.dtype.num_fields):
            new_col_name = struct_field.dtype.field(i).name
            existing_field = self.schema.get(new_col_name)

            if existing_field is not None:
                return result.InvalidArgumentError(
                    "unnesting the struct would cause a column name conflict",
                    conflicting_column=new_col_name,
                )
        return result.Ok(
            from_proto(
                table_pb2.UnnestStructOp(
                    source=self.to_proto(), struct_column_name=column_name
                ),
                skip_validate=True,
            )
        )

    def unnest_list(
        self, list_column_name: str, new_column_names: Sequence[str]
    ) -> result.Ok[UnnestList] | result.InvalidArgumentError:
        if isinstance(new_column_names, str):
            new_column_names = [new_column_names]
        list_field = self.schema.get(column_name=list_column_name)
        if list_field is None or not isinstance(list_field.dtype, pa.LargeListType):
            return result.InvalidArgumentError(
                "no list column with given name", column_name=list_column_name
            )

        for new_column_name in new_column_names:
            existing_field = self.schema.get(new_column_name)

            if existing_field is not None:
                return result.InvalidArgumentError(
                    "unnesting the list would cause a column name conflict",
                    conflicting_column=new_column_name,
                )

        return result.Ok(
            from_proto(
                table_pb2.UnnestListOp(
                    source=self.to_proto(),
                    list_column_name=list_column_name,
                    column_names=new_column_names,
                ),
                skip_validate=True,
            )
        )

    def nest_into_struct(
        self, struct_column_name: str, column_names_to_nest: Sequence[str]
    ) -> result.Ok[NestIntoStruct] | result.InvalidArgumentError:
        if isinstance(column_names_to_nest, str):
            column_names_to_nest = [column_names_to_nest]
        if (
            self.schema.has_column(struct_column_name)
            and struct_column_name not in column_names_to_nest
        ):
            return result.InvalidArgumentError(
                "column with that name already exists", column_name=struct_column_name
            )
        if not column_names_to_nest:
            return result.InvalidArgumentError(
                "must provide at least one column to nest"
            )

        if len(set(column_names_to_nest)) != len(column_names_to_nest):
            return result.InvalidArgumentError("nested column names must be unique")

        for name in column_names_to_nest:
            if not self.schema.has_column(name):
                return result.InvalidArgumentError(
                    "no column with given name", column_name=name
                )

        return result.Ok(
            from_proto(
                table_pb2.NestIntoStructOp(
                    source=self.to_proto(),
                    struct_column_name=struct_column_name,
                    column_names_to_nest=column_names_to_nest,
                ),
                skip_validate=True,
            )
        )

    def distinct_rows(self) -> result.Ok[DistinctRows]:
        return result.Ok(
            from_proto(
                table_pb2.DistinctRowsOp(source=self.to_proto()), skip_validate=True
            )
        )

    def add_column(
        self,
        column: pl.Series,
        ftype: FeatureType | None = None,
    ) -> result.Ok[AddLiteralColumn] | result.InvalidArgumentError:
        column_name = column.name
        if self.schema.has_column(column_name):
            return result.InvalidArgumentError(
                "a column already exists with that name",
                column_name=column_name,
            )

        # TODO(aneesh): See https://github.com/pola-rs/polars/issues/23111 for
        # and remove the rechunk eventually.
        field = column.to_frame().rechunk().to_arrow().schema.field(column_name)
        dtype = field.type

        if ftype is None:
            ftype = Field.decode_feature_type(dtype)

        # Convert array to record batch with dummy column to use pa_scalar and then
        # remove the dummy column.
        # TODO(aneesh): See https://github.com/pola-rs/polars/issues/23111 for
        # and remove the rechunk eventually.
        value_batch = pa.record_batch(
            [column.rechunk().to_arrow()], schema=pa.schema([field]), metadata=None
        )
        structs = pa_scalar.batch_to_structs(value_batch)
        literal_values = [
            more_itertools.one(struct.fields.values()) for struct in structs
        ]

        proto_op = table_pb2.AddLiteralColumnOp(
            source=self._proto,
            column_arrow_schema=pa.schema([pa.field(column_name, dtype)])
            .serialize()
            .to_pybytes(),
            column_feature_type=ftype.to_proto(),
            literals=literal_values,
        )

        return result.Ok(
            from_proto(
                proto_op,
                skip_validate=True,
            )
        )

    def add_literal_column(
        self,
        column_name: str,
        literal: struct_pb2.Value | Scalar | PyValue,
        dtype: pa.DataType,
        ftype: FeatureType | None = None,
    ) -> result.Ok[AddLiteralColumn] | result.InvalidArgumentError:
        if self.schema.has_column(column_name):
            return result.InvalidArgumentError(
                "a column already exists with that name",
                column_name=column_name,
            )
        if ftype is None:
            ftype = Field.decode_feature_type(dtype)

        literal_value = to_value(literal)

        match from_value(literal_value, dtype):
            case result.Ok():
                pass
            case result.InvalidArgumentError() as err:
                return err

        proto_op = table_pb2.AddLiteralColumnOp(
            source=self._proto,
            column_arrow_schema=pa.schema([pa.field(column_name, dtype)])
            .serialize()
            .to_pybytes(),
            column_feature_type=ftype.to_proto(),
            literals=[literal_value],
        )

        return result.Ok(from_proto(proto_op, skip_validate=True))

    def concat_string(
        self,
        column_names: list[str],
        combined_column_name: str,
        separator: str,
        list_separator: str,
    ) -> result.Ok[CombineColumns] | result.InvalidArgumentError:
        for col in column_names:
            field = self.schema.get(col)
            if not field:
                return result.InvalidArgumentError(
                    "no column with given name", given_name=col
                )
            if pa.types.is_binary(field.dtype) | pa.types.is_large_binary(field.dtype):
                return result.InvalidArgumentError(
                    "cannot concat binary columns", given_name=col
                )

        if self.schema.has_column(combined_column_name):
            return result.InvalidArgumentError(
                "name given for combined column already exists"
            )

        return result.Ok(
            from_proto(
                table_pb2.CombineColumnsOp(
                    source=self._proto,
                    column_names=column_names,
                    combined_column_name=combined_column_name,
                    concat_string=table_pb2.ConcatString(
                        separator=separator,
                        list_separator=list_separator,
                    ),
                ),
                skip_validate=True,
            )
        )

    def embed_column(
        self,
        column_name: str,
        embedding_column_name: str,
        model_name: str,
        tokenizer_name: str,
        expected_vector_length: int,
        expected_coordinate_bitwidth: Literal[32, 64],
    ):
        if not self.schema.has_column(column_name):
            return result.InvalidArgumentError(
                "no column with given name", given_name=column_name
            )

        if self.schema.has_column(embedding_column_name):
            return result.InvalidArgumentError(
                "name given for embedding column already exists"
            )

        match expected_coordinate_bitwidth:
            case 32:
                bwidth_value = table_pb2.FLOAT_BIT_WIDTH_32
            case 64:
                bwidth_value = table_pb2.FLOAT_BIT_WIDTH_64

        return result.Ok(
            from_proto(
                table_pb2.EmbedColumnOp(
                    source=self._proto,
                    column_name=column_name,
                    embedding_column_name=embedding_column_name,
                    model_name=model_name,
                    tokenizer_name=tokenizer_name,
                    expected_vector_length=expected_vector_length,
                    expected_coordinate_bitwidth=bwidth_value,
                ),
                skip_validate=True,
            )
        )

    def encode_columns(
        self,
        encoded_columns: list[EncodedColumn],
    ) -> result.Ok[EncodeColumns] | result.InvalidArgumentError:
        new_encoded_columns = list[table_pb2.EncodedColumn]()
        for encoded_column in encoded_columns:
            if not self.schema.has_column(encoded_column.column_name):
                return result.InvalidArgumentError(
                    "no column with given name", given_name=encoded_column.column_name
                )

            if self.schema.has_column(encoded_column.encoded_column_name):
                return result.InvalidArgumentError(
                    "name given for encoded column already exists"
                )
            new_encoded_columns.append(
                table_pb2.EncodedColumn(
                    column_name=encoded_column.column_name,
                    encoded_column_name=encoded_column.encoded_column_name,
                    encoder=encoded_column.encoder.to_proto(),
                )
            )

        if isinstance(self, EncodeColumns):
            old_encoded_columns = [
                table_pb2.EncodedColumn(
                    column_name=encoded_column.column_name,
                    encoded_column_name=encoded_column.encoded_column_name,
                    encoder=encoded_column.encoder.to_proto(),
                )
                for encoded_column in self.encoded_columns
            ]
            old_encoded_columns.extend(new_encoded_columns)
            proto = table_pb2.EncodeColumnOp(
                source=self.source.to_proto(),
                encoded_columns=old_encoded_columns,
            )
        else:
            proto = table_pb2.EncodeColumnOp(
                source=self._proto,
                encoded_columns=new_encoded_columns,
            )
        return result.Ok(
            from_proto(
                proto,
                skip_validate=True,
            )
        )

    def aggregate_columns(
        self,
        column_names: Sequence[str],
        aggregation: Aggregation,
    ):
        """Aggregates the specified columns using the provided aggregation function.

        This method computes the aggregation for each column specified in `column_names`
        and returns the results as a single-row table.
        """
        if isinstance(column_names, str):
            column_names = [column_names]

        for col in column_names:
            if not self.schema.has_column(col):
                return result.InvalidArgumentError(
                    "no column with given name", given_name=col
                )

        return result.Ok(
            from_proto(
                table_pb2.AggregateColumnsOp(
                    source=self._proto,
                    column_names=column_names,
                    aggregation=aggregation.to_proto(),
                ),
                skip_validate=True,
            )
        )

    def correlate_columns(
        self,
        column_names: Sequence[str],
    ) -> result.Ok[CorrelateColumns]:
        if isinstance(column_names, str):
            column_names = [column_names]
        return result.Ok(
            from_proto(
                table_pb2.CorrelateColumnsOp(
                    source=self._proto,
                    column_names=column_names,
                ),
                skip_validate=True,
            )
        )

    def histogram(
        self,
        column_name: str,
        breakpoint_column_name: str = "breakpoint",
        count_column_name: str = "count",
    ) -> result.Ok[HistogramColumn]:
        """Bin values into buckets and count their occurrences."""
        return result.Ok(
            from_proto(
                table_pb2.HistogramColumnOp(
                    source=self._proto,
                    column_name=column_name,
                    breakpoint_column_name=breakpoint_column_name,
                    count_column_name=count_column_name,
                ),
                skip_validate=True,
            )
        )

    def concat_list(
        self,
        column_names: list[str],
        concat_list_column_name: str,
    ) -> result.Ok[CombineColumns] | result.InvalidArgumentError:
        """Horizontally concatenate columns into a single list column."""
        if len(column_names) == 0:
            return result.InvalidArgumentError("column_names is empty")

        for col in column_names:
            if not self.schema.has_column(col):
                return result.InvalidArgumentError(
                    "no column with given name", given_name=col
                )

        if self.schema.has_column(concat_list_column_name):
            return result.InvalidArgumentError(
                "name given for concat_list column already exists"
            )

        return result.Ok(
            from_proto(
                table_pb2.CombineColumnsOp(
                    source=self._proto,
                    column_names=column_names,
                    combined_column_name=concat_list_column_name,
                    concat_list=table_pb2.ConcatList(),
                ),
                skip_validate=True,
            )
        )

    def add_row_index(
        self,
        row_index_column_name: str,
        *,
        offset: int = 0,
    ) -> result.Ok[AddRowIndex] | result.InvalidArgumentError:
        if self.schema.has_column(row_index_column_name):
            return result.InvalidArgumentError(
                "name given for row index column already exists"
            )
        if offset < 0:
            return result.InvalidArgumentError("row index offset cannot be negative")
        return result.Ok(
            from_proto(
                table_pb2.AddRowIndexOp(
                    source=self._proto,
                    row_index_column_name=row_index_column_name,
                    offset=offset,
                ),
                skip_validate=True,
            )
        )

    def convert_column_to_string(
        self,
        column_name: str,
    ) -> result.Ok[ConvertColumnToString] | result.InvalidArgumentError:
        if not self.schema.has_column(column_name):
            return result.InvalidArgumentError(
                "no column with given name", given_name=column_name
            )
        if isinstance(self.schema[column_name].dtype, pa.StructType):
            return result.InvalidArgumentError(
                "converting struct columns to strings is not supported",
                column_name=column_name,
            )
        return result.Ok(
            from_proto(
                table_pb2.ConvertColumnToStringOp(
                    source=self._proto,
                    column_name=column_name,
                ),
                skip_validate=True,
            )
        )

    def output_csv(
        self, *, url: str, include_header: bool
    ) -> result.Ok[OutputCsv] | result.InvalidArgumentError:
        # Some execution engines don't support nested dtypes
        for field in self.schema:
            dtype = field.dtype
            if isinstance(
                dtype,
                pa.StructType | pa.ListType | pa.LargeListType | pa.FixedSizeListType,
            ):
                dtype = cast(
                    "pa.StructType | pa.ListType[pa.DataType] \
                        | pa.LargeListType[pa.DataType] \
                        | pa.FixedSizeListType[pa.DataType]",
                    dtype,
                )
                return result.InvalidArgumentError(
                    "nested fields are not supported",
                    name=field.name,
                    dtype=str(dtype),
                )
        return result.Ok(
            from_proto(
                table_pb2.OutputCsvOp(
                    source=self._proto,
                    csv_url=url,
                    include_header=include_header,
                ),
                skip_validate=True,
            )
        )

    def truncate_list(
        self,
        list_column_name: str,
        target_list_length: int,
        *,
        padding_value: float | str | bool,
    ) -> result.Ok[TruncateList] | result.InvalidArgumentError:
        if not self.schema.has_column(list_column_name):
            return result.InvalidArgumentError(
                "no column with given name", column_name=list_column_name
            )
        column_type = self.schema[list_column_name].dtype
        if not isinstance(
            column_type,
            pa.ListType | pa.LargeListType | pa.FixedSizeListType,
        ):
            return result.InvalidArgumentError(
                "given column must be a list", column_name=list_column_name
            )
        column_type = cast(
            "pa.ListType[pa.DataType] | pa.LargeListType[pa.DataType] \
                | pa.FixedSizeListType[pa.DataType]",
            column_type,
        )
        elem_type = _list_elem_type(column_type)
        if target_list_length < 1:
            return result.InvalidArgumentError(
                "target list length must be a positive integer",
                given_length=target_list_length,
            )

        padding = to_value(padding_value)
        match from_value(padding, elem_type):
            case result.Ok():
                pass
            case result.InvalidArgumentError() as err:
                return err

        proto_op = table_pb2.TruncateListOp(
            source=self._proto,
            list_column_name=list_column_name,
            target_column_length=target_list_length,
            padding_value=padding,
            column_arrow_schema=pa.schema([pa.field("padding_value", elem_type)])
            .serialize()
            .to_pybytes(),
        )

        return result.Ok(
            from_proto(
                proto_op,
                skip_validate=True,
            )
        )

    def embed_image_column(
        self,
        column_name: str,
        embedding_column_name: str,
        model_name: str,
        expected_vector_length: int,
        expected_coordinate_bitwidth: Literal[32, 64],
    ):
        column_name_schema = self.schema.get(column_name)
        if not column_name_schema:
            return result.InvalidArgumentError(
                "no column with given name", given_name=column_name
            )

        if column_name_schema.ftype != feature_type.image():
            return result.InvalidArgumentError(
                "no image column with given name", given_name=column_name
            )

        if self.schema.has_column(embedding_column_name):
            return result.InvalidArgumentError(
                "name given for embedding column already exists"
            )

        match expected_coordinate_bitwidth:
            case 32:
                bwidth_value = table_pb2.FLOAT_BIT_WIDTH_32
            case 64:
                bwidth_value = table_pb2.FLOAT_BIT_WIDTH_64

        return result.Ok(
            from_proto(
                table_pb2.EmbedImageColumnOp(
                    source=self._proto,
                    column_name=column_name,
                    embedding_column_name=embedding_column_name,
                    model_name=model_name,
                    expected_vector_length=expected_vector_length,
                    expected_coordinate_bitwidth=bwidth_value,
                ),
                skip_validate=True,
            )
        )

    def add_decision_tree_summary(
        self,
        feature_column_names: Sequence[str],
        label_column_name: str,
        max_depth: int,
        output_metric_key: str = "decision_tree",
        classes_names: Sequence[str] | None = None,
    ):
        """Add Decision Tree Summary.

        Args:
            feature_column_names: Name of the feature columns.
            label_column_name: Name of the label column.
            max_depth: The maximum depth of the tree.
            output_metric_key: Metric key used to store the decision tree.
            classes_names: Names of each of the target classes in ascending
                numerical order.

        Returns:
            An AddDecisionTreeSummaryOp.
        """
        if max_depth < 0:
            return result.InvalidArgumentError("max_depth must be strictly positive")

        return result.Ok(
            from_proto(
                table_pb2.AddDecisionTreeSummaryOp(
                    source=self._proto,
                    feature_column_names=feature_column_names,
                    label_column_name=label_column_name,
                    classes_names=classes_names,
                    max_depth=max_depth,
                    output_metric_key=output_metric_key,
                ),
                skip_validate=True,
            )
        )

    def sample_rows(
        self,
        sample_strategy: SampleStrategy,
        num_rows: int,
    ):
        if num_rows < 0:
            return result.InvalidArgumentError("num_rows must be non-negative")

        return result.Ok(
            from_proto(
                table_pb2.SampleRowsOp(
                    source=self._proto,
                    sample_strategy=sample_strategy.to_proto(),
                    num_rows=num_rows,
                ),
                skip_validate=True,
            ),
        )

    def describe(
        self,
        column_names: Sequence[str],
        interpolation: RollingInterpolationMethod = "nearest",
        statistic_column_name="statistic",
    ):
        if isinstance(column_names, str):
            column_names = [column_names]
        return result.Ok(
            from_proto(
                table_pb2.DescribeColumnsOp(
                    source=self._proto,
                    column_names=column_names,
                    statistic_column_name=statistic_column_name,
                    interpolation=interpolation,
                ),
                skip_validate=True,
            )
        )


class SelectFromStaging(_Base):
    """Construct a table by selecting rows from the staging collection.

    These operations are leaf operations that describe data sources.
    """

    @property
    def blob_names(self) -> Sequence[str]:
        return self._proto.select_from_staging.blob_names

    @functools.cached_property
    def arrow_schema(self) -> pa.Schema:
        return pa.ipc.read_schema(
            pa.py_buffer(self._proto.select_from_staging.arrow_schema)
        )

    @functools.cached_property
    def feature_types(self) -> Sequence[FeatureType]:
        return [
            ftype_from_proto(feature_type)
            for feature_type in self._proto.select_from_staging.feature_types
        ]

    @property
    def expected_rows(self) -> int:
        return self._proto.select_from_staging.expected_rows

    def sources(self):
        return list[Op]()


class RenameColumns(_Base):
    """Rename the columns in the result of another operation.

    Useful for resolving conflicts that would happen during joins,
    or just for adjusting poor source names.
    """

    @property
    def source(self) -> Op:
        if self._parents:
            return self._parents[0]
        return from_proto(self._proto.rename_columns.source, skip_validate=True)

    @property
    def old_name_to_new(self) -> Mapping[str, str]:
        return self._proto.rename_columns.old_names_to_new

    def sources(self):
        return [self.source]


class UpdateFeatureTypes(_Base):
    """Patch FeatureType of a table schema."""

    @property
    def source(self) -> Op:
        if self._parents:
            return self._parents[0]
        return from_proto(self._proto.update_feature_types.source, skip_validate=True)

    @functools.cached_property
    def new_feature_types(self) -> Mapping[str, FeatureType]:
        return {
            k: ftype_from_proto(v)
            for k, v in self._proto.update_feature_types.new_feature_types.items()
        }

    def sources(self):
        return [self.source]


class Join(_Base):
    """Join two tables together to produce a new table.

    All unique columns from the constituent tables appear in the
    results. Order matters, left columns will be preferred on conflict
    and the names for left columns will be preferred when names for
    the join columns differ.
    """

    @property
    def left_source(self) -> Op:
        if self._parents:
            return self._parents[0]
        return from_proto(self._proto.join.left_source, skip_validate=True)

    @property
    def right_source(self) -> Op:
        if len(self._parents) > 1:
            return self._parents[1]
        return from_proto(self._proto.join.right_source, skip_validate=True)

    @property
    def left_join_columns(self) -> Sequence[str]:
        return self._proto.join.left_join_columns

    @property
    def right_join_columns(self) -> Sequence[str]:
        return self._proto.join.right_join_columns

    @property
    def how(self):
        return self._proto.join.how

    def sources(self):
        return [self.left_source, self.right_source]


class SelectColumns(_Base):
    """Enumerate the columns from a source table that should be kept."""

    @property
    def columns(self) -> Sequence[str]:
        return self._proto.select_columns.columns

    @property
    def source(self) -> Op:
        if self._parents:
            return self._parents[0]
        return from_proto(self._proto.select_columns.source, skip_validate=True)

    def sources(self):
        return [self.source]


class LimitRows(_Base):
    """Limit the number of rows in a table."""

    @property
    def num_rows(self) -> int:
        return self._proto.limit_rows.num_rows

    @property
    def source(self) -> Op:
        if self._parents:
            return self._parents[0]
        return from_proto(self._proto.limit_rows.source, skip_validate=True)

    def sources(self):
        return [self.source]


class OffsetRows(_Base):
    """Limit the number of rows in a table."""

    @property
    def num_rows(self) -> int:
        return self._proto.offset_rows.num_rows

    @property
    def source(self) -> Op:
        if self._parents:
            return self._parents[0]
        return from_proto(self._proto.offset_rows.source, skip_validate=True)

    def sources(self):
        return [self.source]


class OrderBy(_Base):
    """Order the rows in a table."""

    @property
    def source(self) -> Op:
        if self._parents:
            return self._parents[0]
        return from_proto(self._proto.order_by.source, skip_validate=True)

    @property
    def columns(self) -> Sequence[str]:
        return self._proto.order_by.columns

    @property
    def desc(self) -> bool:
        return self._proto.order_by.desc

    def sources(self):
        return [self.source]


class FilterRows(_Base):
    """Filter rows by applying a predicate."""

    @property
    def source(self) -> Op:
        if self._parents:
            return self._parents[0]
        return from_proto(self._proto.filter_rows.source, skip_validate=True)

    @property
    def row_filter(self) -> RowFilter:
        return row_filters_from_proto(self._proto.filter_rows.row_filter)

    def sources(self):
        return [self.source]


class DistinctRows(_Base):
    """Remove duplicate rows from the table."""

    @property
    def source(self) -> Op:
        if self._parents:
            return self._parents[0]
        return from_proto(self._proto.distinct_rows.source, skip_validate=True)

    def sources(self):
        return [self.source]


class UpdateMetadata(_Base):
    """Update table-wide metadata, overwriting old values."""

    @functools.cached_property
    def metadata_updates(self) -> Mapping[str, Any]:
        return json_format.MessageToDict(self._proto.update_metadata.metadata_updates)

    @property
    def source(self) -> Op:
        if self._parents:
            return self._parents[0]
        return from_proto(self._proto.update_metadata.source, skip_validate=True)

    def sources(self):
        return [self.source]


class SetMetadata(_Base):
    """Update table-wide metadata, overwriting old values."""

    @functools.cached_property
    def new_metadata(self) -> Mapping[str, Any]:
        return json_format.MessageToDict(self._proto.set_metadata.new_metadata)

    @property
    def source(self) -> Op:
        if self._parents:
            return self._parents[0]
        return from_proto(self._proto.set_metadata.source, skip_validate=True)

    def sources(self):
        return [self.source]


class RemoveFromMetadata(_Base):
    """Update table-wide metadata, overwriting old values."""

    @property
    def keys_to_remove(self) -> Sequence[str]:
        return self._proto.remove_from_metadata.keys_to_remove

    @property
    def source(self) -> Op:
        if self._parents:
            return self._parents[0]
        return from_proto(self._proto.remove_from_metadata.source, skip_validate=True)

    def sources(self):
        return [self.source]


class RollupByAggregation(_Base):
    """Compute an aggregation rollup and add it as a new column."""

    @property
    def source(self) -> Op:
        if self._parents:
            return self._parents[0]
        return from_proto(self._proto.rollup_by_aggregation.source, skip_validate=True)

    @property
    def group_by_column_names(self) -> Sequence[str]:
        return self._proto.rollup_by_aggregation.group_by_column_names

    @property
    def target_column_name(self) -> str:
        return self._proto.rollup_by_aggregation.target_column_name

    @property
    def aggregation_type(self):
        return self._proto.rollup_by_aggregation.aggregation_type

    def sources(self):
        return [self.source]


class Empty(_Base):
    """An operation the produces an empty table."""

    def sources(self):
        return list[Op]()


class InMemoryInput(_Base):
    """An operation the produces an empty table."""

    @property
    def input_name(self) -> str:
        return self._proto.in_memory_input.input_name

    @functools.cached_property
    def arrow_schema(self) -> pa.Schema | None:
        schema_bytes = self._proto.in_memory_input.arrow_schema
        if not schema_bytes:
            return None
        return pa.ipc.read_schema(pa.py_buffer(schema_bytes))

    @functools.cached_property
    def feature_types(self) -> list[feature_type.FeatureType] | None:
        feature_types = self._proto.in_memory_input.feature_types
        if not feature_types:
            return None
        return [feature_type.from_proto(ft) for ft in feature_types]

    def sources(self):
        return list[Op]()


@dataclasses.dataclass(frozen=True)
class EdgeListTable:
    """A table bundled with edge metadata."""

    table: Op
    start_column_name: str
    end_column_name: str
    start_entity_name: str
    end_entity_name: str

    @classmethod
    def from_proto(cls, proto: table_pb2.EdgeListTable):
        return cls(
            from_proto(proto.table, skip_validate=True),
            start_column_name=proto.start_column_name,
            end_column_name=proto.end_column_name,
            start_entity_name=proto.start_entity_name,
            end_entity_name=proto.end_entity_name,
        )

    def to_proto(self):
        return table_pb2.EdgeListTable(
            table=self.table.to_proto(),
            start_column_name=self.start_column_name,
            end_column_name=self.end_column_name,
            start_entity_name=self.start_entity_name,
            end_entity_name=self.end_entity_name,
        )


class EmbedNode2vecFromEdgeLists(_Base):
    """Consume several tables as edge lists, produce node2vec embedding."""

    @functools.cached_property
    def edge_list_tables(self):
        return [
            EdgeListTable.from_proto(edge_list)
            for edge_list in self._proto.embed_node2vec_from_edge_lists.edge_list_tables
        ]

    @property
    def ndim(self):
        return self._proto.embed_node2vec_from_edge_lists.node2vec_parameters.ndim

    @property
    def walk_length(self):
        return (
            self._proto.embed_node2vec_from_edge_lists.node2vec_parameters.walk_length
        )

    @property
    def window(self):
        return self._proto.embed_node2vec_from_edge_lists.node2vec_parameters.window

    @property
    def p(self):
        return self._proto.embed_node2vec_from_edge_lists.node2vec_parameters.p

    @property
    def q(self):
        return self._proto.embed_node2vec_from_edge_lists.node2vec_parameters.q

    @property
    def alpha(self):
        return self._proto.embed_node2vec_from_edge_lists.node2vec_parameters.alpha

    @property
    def min_alpha(self):
        return self._proto.embed_node2vec_from_edge_lists.node2vec_parameters.min_alpha

    @property
    def negative(self):
        return self._proto.embed_node2vec_from_edge_lists.node2vec_parameters.negative

    @property
    def epochs(self):
        return self._proto.embed_node2vec_from_edge_lists.node2vec_parameters.epochs

    def sources(self):
        return [edge_list.table for edge_list in self.edge_list_tables]


class EmbeddingMetrics(_Base):
    """Compute embedding metrics metadata."""

    @property
    def table(self) -> Op:
        if self._parents:
            return self._parents[0]
        return from_proto(self._proto.embedding_metrics.table, skip_validate=True)

    @property
    def embedding_column_name(self) -> str:
        return self._proto.embedding_metrics.embedding_column_name

    def sources(self):
        return [self.table]


class EmbeddingCoordinates(_Base):
    """Compute embedding coordinates."""

    @property
    def table(self) -> Op:
        if self._parents:
            return self._parents[0]
        return from_proto(self._proto.embedding_coordinates.table, skip_validate=True)

    @property
    def embedding_column_name(self) -> str:
        return self._proto.embedding_coordinates.embedding_column_name

    @property
    def n_components(self) -> int:
        return self._proto.embedding_coordinates.n_components

    @property
    def metric(self) -> str:
        return self._proto.embedding_coordinates.metric

    def sources(self):
        return [self.table]


class ReadFromParquet(_Base):
    """Read table from parquet files."""

    @property
    def blob_names(self) -> Sequence[str]:
        return self._proto.read_from_parquet.blob_names

    @functools.cached_property
    def arrow_schema(self) -> pa.Schema:
        return pa.ipc.read_schema(
            pa.py_buffer(self._proto.read_from_parquet.arrow_schema)
        )

    @functools.cached_property
    def feature_types(self) -> Sequence[FeatureType]:
        return [
            ftype_from_proto(feature_type)
            for feature_type in self._proto.read_from_parquet.feature_types
        ]

    @property
    def expected_rows(self) -> int:
        return self._proto.read_from_parquet.expected_rows

    def sources(self):
        return list[Op]()


class SelectFromVectorStaging(_Base):
    """Read table from parquet files."""

    @property
    def input_vector(self) -> Sequence[float]:
        return self._proto.select_from_vector_staging.input_vector

    @property
    def blob_names(self) -> Sequence[str]:
        return self._proto.select_from_vector_staging.blob_names

    @property
    def similarity_metric(self) -> str:
        return self._proto.select_from_vector_staging.similarity_metric

    @property
    def vector_column_name(self) -> str:
        return self._proto.select_from_vector_staging.vector_column_name

    @property
    def expected_rows(self) -> int:
        return self._proto.select_from_vector_staging.expected_rows

    def sources(self):
        return list[Op]()

    @functools.cached_property
    def arrow_schema(self) -> pa.Schema:
        return pa.ipc.read_schema(
            pa.py_buffer(self._proto.select_from_vector_staging.arrow_schema)
        )

    @functools.cached_property
    def feature_types(self) -> Sequence[FeatureType]:
        return [
            ftype_from_proto(feature_type)
            for feature_type in self._proto.select_from_vector_staging.feature_types
        ]


ConcatMethod = Literal[
    "vertical",
    "vertical_relaxed",
    "diagonal",
    "diagonal_relaxed",
    "horizontal",
    "align",
]


class Concat(_Base):
    """Concatenate tables."""

    @functools.cached_property
    def tables(self) -> list[Op]:
        return [
            from_proto(table, skip_validate=True) for table in self._proto.concat.tables
        ]

    @property
    def how(self) -> ConcatMethod:
        if self._proto.concat.how == "":
            return "vertical"
        if self._proto.concat.how not in get_args(ConcatMethod):
            raise result.InvalidArgumentError("how attribute should be a ConcatMethod")
        return cast(ConcatMethod, self._proto.concat.how)

    def sources(self):
        return self.tables


class UnnestStruct(_Base):
    """Unnest a struct column."""

    @property
    def source(self) -> Op:
        return from_proto(self._proto.unnest_struct.source, skip_validate=True)

    @property
    def struct_column_name(self) -> str:
        return self._proto.unnest_struct.struct_column_name

    def sources(self):
        return [self.source]


class NestIntoStruct(_Base):
    """Nest columns into a single struct column."""

    @property
    def source(self) -> Op:
        return from_proto(self._proto.nest_into_struct.source, skip_validate=True)

    @property
    def struct_column_name(self) -> str:
        return self._proto.nest_into_struct.struct_column_name

    @property
    def column_names_to_nest(self) -> Sequence[str]:
        return self._proto.nest_into_struct.column_names_to_nest

    def sources(self):
        return [self.source]


class AddLiteralColumn(_Base):
    """Add a new column were all entries are a particular literal value."""

    @property
    def source(self) -> Op:
        return from_proto(self._proto.add_literal_column.source, skip_validate=True)

    @functools.cached_property
    def literals(self) -> Sequence[struct_pb2.Value]:
        op = self._proto.add_literal_column
        if op.HasField("literal"):
            return [op.literal]
        return op.literals

    def literals_as_py(self) -> Sequence[PyValue]:
        return [
            from_value(literal, self.dtype).unwrap_or_raise().as_py()
            for literal in self.literals
        ]

    @property
    def dtype(self) -> pa.DataType:
        return self.column_arrow_schema.field(0).type

    @functools.cached_property
    def column_arrow_schema(self) -> pa.Schema:
        return pa.ipc.read_schema(
            pa.py_buffer(self._proto.add_literal_column.column_arrow_schema)
        )

    @functools.cached_property
    def column_feature_type(self) -> FeatureType:
        return ftype_from_proto(self._proto.add_literal_column.column_feature_type)

    def sources(self):
        return [self.source]


class CombineColumns(_Base):
    """Combine columns by applying a reducer creating the result as a new column."""

    @property
    def source(self) -> Op:
        return from_proto(self._proto.combine_columns.source, skip_validate=True)

    @property
    def column_names(self) -> Sequence[str]:
        return self._proto.combine_columns.column_names

    @property
    def combined_column_name(self) -> str:
        return self._proto.combine_columns.combined_column_name

    @property
    def reduction(self) -> table_pb2.ConcatString | table_pb2.ConcatList:
        which_reduction = self._proto.combine_columns.WhichOneof("reduction")
        if not which_reduction:
            raise result.InternalError("no reduction set")
        return self._proto.combine_columns.__getattribute__(which_reduction)

    def sources(self):
        return [self.source]


class EmbedColumn(_Base):
    """Embed each entry in a column, add the results as a new column."""

    @property
    def source(self) -> Op:
        return from_proto(self._proto.embed_column.source, skip_validate=True)

    @property
    def column_name(self) -> str:
        return self._proto.embed_column.column_name

    @property
    def embedding_column_name(self) -> str:
        return self._proto.embed_column.embedding_column_name

    @property
    def model_name(self) -> str:
        return self._proto.embed_column.model_name

    @property
    def tokenizer_name(self) -> str:
        return self._proto.embed_column.tokenizer_name

    @property
    def expected_vector_length(self) -> int:
        return self._proto.embed_column.expected_vector_length

    @property
    def expected_coordinate_bitwidth(self) -> Literal[32, 64]:
        match self._proto.embed_column.expected_coordinate_bitwidth:
            case table_pb2.FLOAT_BIT_WIDTH_32:
                return 32
            case table_pb2.FLOAT_BIT_WIDTH_64:
                return 64
            case _:
                raise result.InternalError(
                    "embedding coordinate bitwidth not specified"
                )

    def sources(self):
        return [self.source]


class EncodeColumns(_Base):
    """Encode each entry in a column, add the results as a new column."""

    @property
    def source(self) -> Op:
        return from_proto(self._proto.encode_column.source, skip_validate=True)

    @property
    def encoded_columns(self) -> list[EncodedColumn]:
        # Legacy EncodeColumnOp
        if self._proto.encode_column.column_name:
            return [
                EncodedColumn(
                    column_name=self._proto.encode_column.column_name,
                    encoded_column_name=self._proto.encode_column.encoded_column_name,
                    encoder=encoder_type_from_proto(self._proto.encode_column.encoder),
                )
            ]

        args = list[EncodedColumn]()
        for encoded_column in self._proto.encode_column.encoded_columns:
            args.append(
                EncodedColumn(
                    column_name=encoded_column.column_name,
                    encoded_column_name=encoded_column.encoded_column_name,
                    encoder=encoder_type_from_proto(encoded_column.encoder),
                )
            )

        return args

    def sources(self):
        return [self.source]


class AggregateColumns(_Base):
    """Compute various aggregation in a column."""

    @property
    def source(self) -> Op:
        return from_proto(self._proto.aggregate_columns.source, skip_validate=True)

    @property
    def column_names(self) -> Sequence[str]:
        return self._proto.aggregate_columns.column_names

    @property
    def aggregation(self) -> Aggregation:
        return aggregation_from_proto(self._proto.aggregate_columns.aggregation)

    def sources(self):
        return [self.source]


class CorrelateColumns(_Base):
    """Compute pairwise correlation coefficients between columns."""

    @property
    def source(self) -> Op:
        return from_proto(self._proto.correlate_columns.source, skip_validate=True)

    @property
    def column_names(self) -> Sequence[str]:
        return self._proto.correlate_columns.column_names

    def sources(self):
        return [self.source]


class HistogramColumn(_Base):
    """Bin values into buckets and count their occurrences."""

    @property
    def source(self) -> Op:
        return from_proto(self._proto.histogram_column.source, skip_validate=True)

    @property
    def column_name(self) -> str:
        return self._proto.histogram_column.column_name

    @property
    def breakpoint_column_name(self) -> str:
        return self._proto.histogram_column.breakpoint_column_name

    @property
    def count_column_name(self) -> str:
        return self._proto.histogram_column.count_column_name

    def sources(self):
        return [self.source]


class ConvertColumnToString(_Base):
    """Convert column type to string.

    Converts arrays/lists to a comma joined string without brackets.
    """

    @property
    def source(self) -> Op:
        return from_proto(self._proto.convert_column_string.source, skip_validate=True)

    @property
    def column_name(self) -> str:
        return self._proto.convert_column_string.column_name

    def sources(self):
        return [self.source]


class AddRowIndex(_Base):
    """Adds column holding the row index or each row starting at given offset."""

    @property
    def source(self) -> Op:
        return from_proto(self._proto.row_index.source, skip_validate=True)

    @property
    def row_index_column_name(self) -> str:
        return self._proto.row_index.row_index_column_name

    @property
    def offset(self) -> int:
        return self._proto.row_index.offset

    def sources(self):
        return [self.source]


class OutputCsv(_Base):
    """Writes out source as a csv to given url."""

    @property
    def source(self) -> Op:
        return from_proto(self._proto.output_csv.source, skip_validate=True)

    @property
    def csv_url(self) -> str:
        return self._proto.output_csv.csv_url

    @property
    def include_header(self) -> bool:
        return self._proto.output_csv.include_header

    def sources(self):
        return [self.source]


class TruncateList(_Base):
    """Truncates or pads a list column to the specified length."""

    @property
    def source(self) -> Op:
        return from_proto(self._proto.truncate_list.source, skip_validate=True)

    @property
    def column_name(self) -> str:
        return self._proto.truncate_list.list_column_name

    @property
    def target_column_length(self) -> int:
        return self._proto.truncate_list.target_column_length

    @property
    def padding_value(self) -> struct_pb2.Value:
        return self._proto.truncate_list.padding_value

    @functools.cached_property
    def padding_value_as_py(self) -> PyValue:
        return from_value(self.padding_value, self.dtype).unwrap_or_raise().as_py()

    @functools.cached_property
    def dtype(self) -> pa.DataType:
        return (
            pa.ipc.read_schema(
                pa.py_buffer(self._proto.truncate_list.column_arrow_schema)
            )
            .field(0)
            .type
        )

    def sources(self):
        return [self.source]


class Union(_Base):
    """Returns a union of all the rows from sources.

    A SQL-like union; like concat but result is allowed to be unordered.
    """

    @property
    def distinct(self) -> bool:
        return self._proto.union.distinct

    def sources(self) -> list[Op]:
        return [
            from_proto(entry, skip_validate=True) for entry in self._proto.union.sources
        ]


class EmbedImageColumn(_Base):
    """Embed each image entry in a column, add the results as a new column."""

    @property
    def source(self) -> Op:
        return from_proto(self._proto.embed_image_column.source, skip_validate=True)

    @property
    def column_name(self) -> str:
        return self._proto.embed_image_column.column_name

    @property
    def embedding_column_name(self) -> str:
        return self._proto.embed_image_column.embedding_column_name

    @property
    def model_name(self) -> str:
        return self._proto.embed_image_column.model_name

    @property
    def expected_vector_length(self) -> int:
        return self._proto.embed_image_column.expected_vector_length

    @property
    def expected_coordinate_bitwidth(self) -> Literal[32, 64]:
        match self._proto.embed_image_column.expected_coordinate_bitwidth:
            case table_pb2.FLOAT_BIT_WIDTH_32:
                return 32
            case table_pb2.FLOAT_BIT_WIDTH_64:
                return 64
            case _:
                raise result.InternalError(
                    "embedding coordinate bitwidth not specified"
                )

    def sources(self):
        return [self.source]


class AddDecisionTreeSummary(_Base):
    """Add a decision tree summary."""

    @property
    def source(self) -> Op:
        return from_proto(
            self._proto.add_decision_tree_summary.source, skip_validate=True
        )

    @property
    def feature_column_names(self) -> Sequence[str]:
        return self._proto.add_decision_tree_summary.feature_column_names

    @property
    def label_column_name(self) -> str:
        return self._proto.add_decision_tree_summary.label_column_name

    @property
    def classes_names(self) -> Sequence[str] | None:
        return (
            self._proto.add_decision_tree_summary.classes_names
            if len(self._proto.add_decision_tree_summary.classes_names)
            else None
        )

    @property
    def max_depth(self) -> int:
        return self._proto.add_decision_tree_summary.max_depth

    @property
    def output_metric_key(self) -> str:
        return self._proto.add_decision_tree_summary.output_metric_key

    def sources(self):
        return [self.source]


class UnnestList(_Base):
    """Unnest a list column."""

    @property
    def source(self) -> Op:
        return from_proto(self._proto.unnest_list.source, skip_validate=True)

    @property
    def list_column_name(self) -> str:
        return self._proto.unnest_list.list_column_name

    @property
    def column_names(self) -> Sequence[str]:
        return self._proto.unnest_list.column_names

    def sources(self):
        return [self.source]


class SampleRows(_Base):
    """Sample the number of rows in a table."""

    @property
    def source(self) -> Op:
        return from_proto(self._proto.sample_rows.source, skip_validate=True)

    @property
    def sample_strategy(self) -> SampleStrategy:
        return sample_strategy_from_proto(self._proto.sample_rows.sample_strategy)

    @property
    def num_rows(self) -> int:
        return self._proto.sample_rows.num_rows

    def sources(self):
        return [self.source]


RollingInterpolationMethod: TypeAlias = Literal[
    "nearest", "higher", "lower", "midpoint", "linear"
]


class DescribeColumns(_Base):
    """Summary statistics for columns."""

    @property
    def source(self) -> Op:
        return from_proto(self._proto.describe_columns.source, skip_validate=True)

    @property
    def column_names(self) -> Sequence[str]:
        return self._proto.describe_columns.column_names

    @property
    def statistic_column_name(self) -> str:
        return self._proto.describe_columns.statistic_column_name

    @property
    def interpolation(self) -> RollingInterpolationMethod:
        if self._proto.describe_columns.interpolation == "":
            return "nearest"
        if self._proto.describe_columns.interpolation not in get_args(
            RollingInterpolationMethod
        ):
            raise result.InvalidArgumentError(
                "interpolation attribute should be a RollingInterpolationMethod"
            )
        return cast(
            RollingInterpolationMethod, self._proto.describe_columns.interpolation
        )

    def sources(self):
        return [self.source]


Op = (
    SelectFromStaging
    | RenameColumns
    | Join
    | SelectColumns
    | LimitRows
    | OffsetRows
    | OrderBy
    | FilterRows
    | DistinctRows
    | UpdateMetadata
    | SetMetadata
    | RemoveFromMetadata
    | UpdateFeatureTypes
    | RollupByAggregation
    | Empty
    | EmbedNode2vecFromEdgeLists
    | EmbeddingMetrics
    | EmbeddingCoordinates
    | ReadFromParquet
    | SelectFromVectorStaging
    | Concat
    | UnnestStruct
    | NestIntoStruct
    | AddLiteralColumn
    | CombineColumns
    | EmbedColumn
    | EncodeColumns
    | AggregateColumns
    | CorrelateColumns
    | HistogramColumn
    | ConvertColumnToString
    | AddRowIndex
    | OutputCsv
    | TruncateList
    | Union
    | EmbedImageColumn
    | AddDecisionTreeSummary
    | UnnestList
    | SampleRows
    | DescribeColumns
    | InMemoryInput
)

_COMPUTE_OP_FIELD_NAME_TO_OP: Final = {
    "select_from_staging": SelectFromStaging,
    "rename_columns": RenameColumns,
    "join": Join,
    "select_columns": SelectColumns,
    "limit_rows": LimitRows,
    "offset_rows": OffsetRows,
    "order_by": OrderBy,
    "filter_rows": FilterRows,
    "distinct_rows": DistinctRows,
    "update_metadata": UpdateMetadata,
    "set_metadata": SetMetadata,
    "remove_from_metadata": RemoveFromMetadata,
    "update_feature_types": UpdateFeatureTypes,
    "rollup_by_aggregation": RollupByAggregation,
    "empty": Empty,
    "embed_node2vec_from_edge_lists": EmbedNode2vecFromEdgeLists,
    "embedding_metrics": EmbeddingMetrics,
    "embedding_coordinates": EmbeddingCoordinates,
    "read_from_parquet": ReadFromParquet,
    "select_from_vector_staging": SelectFromVectorStaging,
    "concat": Concat,
    "unnest_struct": UnnestStruct,
    "nest_into_struct": NestIntoStruct,
    "add_literal_column": AddLiteralColumn,
    "combine_columns": CombineColumns,
    "embed_column": EmbedColumn,
    "encode_column": EncodeColumns,
    "aggregate_columns": AggregateColumns,
    "correlate_columns": CorrelateColumns,
    "histogram_column": HistogramColumn,
    "convert_column_string": ConvertColumnToString,
    "row_index": AddRowIndex,
    "output_csv": OutputCsv,
    "truncate_list": TruncateList,
    "union": Union,
    "embed_image_column": EmbedImageColumn,
    "add_decision_tree_summary": AddDecisionTreeSummary,
    "unnest_list": UnnestList,
    "sample_rows": SampleRows,
    "describe_columns": DescribeColumns,
    "in_memory_input": InMemoryInput,
}

_OP_TO_COMPUTE_OP_FIELD_NAME: Final[dict[type[Any], str]] = {
    op: name for name, op in _COMPUTE_OP_FIELD_NAME_TO_OP.items()
}


def _make_schema_from_node2vec_params(n2v_op: EmbedNode2vecFromEdgeLists):
    if not n2v_op.edge_list_tables:
        raise result.InvalidArgumentError(
            "unable to infer schema: empty edge table list"
        )

    dtypes: set[pa.DataType] = set()
    for edge_list in n2v_op.edge_list_tables:
        schema = edge_list.table.schema.to_arrow()
        dtypes.add(schema.field(edge_list.start_column_name).type)
        dtypes.add(schema.field(edge_list.end_column_name).type)

    fields = [pa.field(f"column_{i}", dtype) for i, dtype in enumerate(dtypes)]
    # An extra field is added to id fields for the source name
    fields.append(pa.field(f"column_{len(dtypes)}", pa.large_string()))

    return Schema(
        [
            Field(
                "id",
                pa.struct(fields),
                feature_type.identifier(),
            ),
            Field(
                "embedding",
                pa.large_list(value_type=pa.float32()),
                feature_type.embedding(),
            ),
        ]
    )


def _make_schema_for_embedding_coordinates(op: EmbeddingCoordinates):
    def gen_fields() -> Iterable[Field]:
        for field in op.table.schema:
            if field != op.embedding_column_name:
                yield field
            else:
                yield Field(
                    op.embedding_column_name,
                    pa.large_list(value_type=pa.float32()),
                    feature_type.embedding(),
                )

    return Schema(list(gen_fields()))


def _make_schema_for_unnest_struct(op: UnnestStruct):
    schema = op.source.schema

    def gen_fields() -> Iterable[Field]:
        for field in schema:
            if field.name == op.struct_column_name:
                if not isinstance(field.dtype, pa.StructType):
                    raise result.InvalidArgumentError(
                        "unnest cannot be done on a non-struct column"
                    )

                yield from (
                    Field.from_arrow(field.dtype.field(i))
                    for i in range(field.dtype.num_fields)
                )
            else:
                yield field

    return Schema(list(gen_fields()))


def _make_schema_for_nest_into_struct(op: NestIntoStruct):
    schema = op.source.schema

    return Schema(
        [
            *(field for field in schema if field.name not in op.column_names_to_nest),
            Field.from_arrow(
                pa.field(
                    op.struct_column_name,
                    pa.struct(
                        field.to_arrow()
                        for field in schema
                        if field.name in op.column_names_to_nest
                    ),
                )
            ),
        ]
    )


def _make_schema_for_add_literal_column(op: AddLiteralColumn):
    return Schema(
        [
            *op.source.schema,
            Field.from_arrow(op.column_arrow_schema.field(0), op.column_feature_type),
        ]
    )


def _make_schema_for_combine_columns(op: CombineColumns):
    match op.reduction:
        case table_pb2.ConcatString():
            dtype, ftype = pa.large_utf8(), feature_type.text()

        case table_pb2.ConcatList():
            schema = op.source.schema
            ftype = schema[0].ftype
            for column in schema:
                if column.ftype != ftype:
                    ftype = feature_type.unknown()

            if op.column_names:
                dtype = (
                    pl.DataFrame(schema=schema.to_polars())
                    .with_columns(
                        pl.concat_list(*op.column_names).alias(op.combined_column_name)
                    )
                    .to_arrow()
                    .schema.field(op.combined_column_name)
                    .type
                )
            else:
                dtype = (
                    pl.DataFrame(schema=schema.to_polars())
                    .with_columns(
                        pl.Series(op.combined_column_name, [], pl.List(pl.Float32))
                    )
                    .to_arrow()
                    .schema.field(op.combined_column_name)
                    .type
                )
    return Schema(
        [
            *op.source.schema,
            Field(name=op.combined_column_name, dtype=dtype, ftype=ftype),
        ]
    )


def _make_schema_for_embed_column(op: EmbedColumn):
    match op.expected_coordinate_bitwidth:
        case 64:
            inner_dtype = pa.float64()
        case 32:
            inner_dtype = pa.float32()
    return Schema(
        [
            *op.source.schema,
            Field(
                op.embedding_column_name,
                pa.large_list(inner_dtype),
                feature_type.embedding(),
            ),
        ]
    )


def _make_schema_for_encode_columns(op: EncodeColumns):
    def gen_fields() -> Iterable[Field]:
        for encoder_arg in op.encoded_columns:
            pyarrow_dtype = (
                pl.Series(
                    name=encoder_arg.encoded_column_name,
                    dtype=encoder_arg.encoder.output_dtype,
                )
                .to_arrow()
                .type
            )
            field = Field(
                encoder_arg.encoded_column_name,
                pyarrow_dtype,
                feature_type.unknown(),
            )
            yield field

    return Schema(
        [
            *op.source.schema,
            *gen_fields(),
        ]
    )


def _make_schema_for_aggregate_columns(op: AggregateColumns):
    schema = op.source.schema

    fields: list[Field] = []
    for column_name in op.column_names:
        field = schema[column_name]
        pyarrow_dtype = (
            pl.Series(field.name, dtype=op.aggregation.output_dtype(field.to_polars()))
            .to_arrow()
            .type
        )
        new_field = Field(
            field.name,
            pyarrow_dtype,
            field.ftype,
        )

        fields.append(new_field)

    return Schema(
        fields,
    )


def _make_schema_for_concat(op: Concat):
    dataframes: list[pl.DataFrame] = []
    ftypes: dict[str, FeatureType] = {}
    for source in op.sources():
        schema = source.schema
        dataframe = pl.DataFrame(schema=schema.to_polars())
        dataframes.append(dataframe)
        for field in schema:
            ftypes[field.name] = field.ftype

    polars_schema = pl.concat(dataframes, how=op.how).schema
    arrow_schema = pl.DataFrame(schema=polars_schema).to_arrow().schema
    fields = [
        Field(
            field.name,
            field.type,
            ftypes[field.name],
        )
        for field in arrow_schema
    ]
    return Schema(fields)


def _make_schema_for_correlate_columns(op: CorrelateColumns):
    fields = [
        Field(
            field.name,
            pa.float32(),
            field.ftype,
        )
        for field in op.source.schema
        if field.name in op.column_names
    ]
    return Schema(fields)


def _make_schema_for_histogram_column(op: HistogramColumn):
    fields = [
        Field(
            op.breakpoint_column_name,
            pa.float64(),
            op.source.schema[op.column_name].ftype,
        ),
        Field(
            op.count_column_name,
            pa.uint32(),
            feature_type.numerical(),
        ),
    ]
    return Schema(fields)


def _make_schema_for_embed_image_column(op: EmbedImageColumn):
    match op.expected_coordinate_bitwidth:
        case 64:
            inner_dtype = pa.float64()
        case 32:
            inner_dtype = pa.float32()
    return Schema(
        [
            *op.source.schema,
            Field(
                op.embedding_column_name,
                pa.large_list(inner_dtype),
                feature_type.embedding(),
            ),
        ]
    )


def _make_schema_for_unnest_list(op: UnnestList):
    schema = op.source.schema

    def gen_fields() -> Iterable[Field]:
        for field in schema:
            if field.name == op.list_column_name:
                dtype = field.dtype
                if not isinstance(dtype, pa.LargeListType):
                    raise result.InvalidArgumentError(
                        "unnest cannot be done on a non-list column"
                    )

                dtype = cast(
                    "pa.LargeListType[pa.DataType]",
                    dtype,
                )

                yield from (
                    Field(column_name, dtype=dtype.value_type, ftype=field.ftype)
                    for column_name in op.column_names
                )
            else:
                yield field

    return Schema(list(gen_fields()))


def _make_schema_for_describe_columns(op: DescribeColumns):
    schema = op.source.schema
    arrow_schema = pl.DataFrame(schema=schema.to_polars()).describe().to_arrow().schema
    fields = [
        Field(
            op.statistic_column_name,
            pa.large_string(),
            feature_type.text(),
        ),
        *(
            Field(
                field.name,
                field.type,
                schema[field.name].ftype,
            )
            for field in list(arrow_schema)[1:]
        ),
    ]
    return Schema(fields)


class Schema(Sequence[Field]):
    """List of fields describing data types and feature types of a table."""

    _fields: tuple[Field, ...]

    def __init__(self, fields: Iterable[Field]) -> None:
        self._fields = (*fields,)

    def __hash__(self) -> int:
        return hash(self._fields)

    def __eq__(self, other: object) -> bool:
        """Two schemas are equal if all of their fields match."""
        if isinstance(other, Schema):
            return self._fields == other._fields
        return False

    @overload
    def __getitem__(self, selection: str) -> Field: ...

    @overload
    def __getitem__(self, selection: int) -> Field: ...

    @overload
    def __getitem__(self, selection: slice) -> Sequence[Field]: ...

    def __getitem__(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, selection: int | str | slice
    ) -> Field | Sequence[Field]:
        """This operation is akin to pyarrow.Schema.field.

        The result is either the array addressed Field(s) or the first field with a
        matching name depending on the type of argument passed.
        """
        if isinstance(selection, str):
            for field in self._fields:
                if field.name == selection:
                    return field
            raise KeyError("no field with that name")
        return self._fields[selection]

    def __len__(self):
        """The number of fields in this schema."""
        return len(self._fields)

    def __str__(self) -> str:
        """Legible string representation of this schema."""
        return "\n".join(str(field) for field in self)

    @overload
    def get(self, column_name: str, default: Field) -> Field: ...

    @overload
    def get(self, column_name: str, default: None = ...) -> Field | None: ...

    def get(self, column_name: str, default: Field | None = None) -> Field | None:
        return next((f for f in self if f.name == column_name), default)

    def has_column(self, column_name: str) -> bool:
        return self.get(column_name) is not None

    @classmethod
    def from_arrow(
        cls,
        arrow_schema: pa.Schema,
        feature_types: Sequence[FeatureType | None] | None = None,
    ) -> Schema:
        if feature_types:
            if len(feature_types) != len(arrow_schema):
                raise result.InvalidArgumentError(
                    "length of feature_types must match schema"
                )
        else:
            feature_types = [None] * len(arrow_schema)
        return cls(
            fields=[
                Field.from_arrow(field, ftype)
                for field, ftype in zip(arrow_schema, feature_types, strict=True)
            ]
        )

    def to_arrow(self) -> pa.Schema:
        return pa.schema(field.to_arrow() for field in self)

    def to_polars(self) -> OrderedDict[str, pl.DataType]:
        table = pl.from_arrow(
            pa.schema(field.to_arrow() for field in self).empty_table()
        )
        if isinstance(table, pl.Series):
            table = table.to_frame()

        return table.schema

    def get_primary_key(self) -> Field | None:
        for field in self:
            match field.ftype:
                case feature_type.PrimaryKey():
                    return field
                case _:
                    pass
        return None

    def get_foreign_keys(self, source_id: eorm.SourceID) -> list[Field]:
        def generate_matching_fields():
            for field in self:
                match field.ftype:
                    case feature_type.ForeignKey(ref_id) if ref_id == source_id:
                        yield field
                    case _:
                        pass

        return list(generate_matching_fields())

    def get_embeddings(self) -> list[Field]:
        return [
            field for field in self if isinstance(field.ftype, feature_type.Embedding)
        ]

    @classmethod
    def from_ops(  # noqa: C901
        cls, ops: Op, in_memory_inputs: Mapping[str, pl.DataFrame] | None = None
    ) -> Schema:
        match ops:
            case InMemoryInput():
                if ops.arrow_schema:
                    feature_types = ops.feature_types
                    if not feature_types:
                        feature_types = [None for _ in ops.arrow_schema]
                    return Schema(
                        [
                            Field.from_arrow(dt, ft)
                            for dt, ft in zip(
                                ops.arrow_schema, feature_types, strict=True
                            )
                        ]
                    )

                in_memory_inputs = in_memory_inputs or {}
                input_df = in_memory_inputs.get(ops.input_name)
                if input_df is None:
                    raise result.InvalidArgumentError(
                        "in-memory input was missing", input_name=input_df
                    )
                return Schema.from_arrow(input_df.to_arrow().schema)
            case SelectFromStaging() | ReadFromParquet() | SelectFromVectorStaging():
                return Schema(
                    [
                        Field.from_arrow(afield, ftype)
                        for afield, ftype in zip(
                            ops.arrow_schema, ops.feature_types, strict=True
                        )
                    ]
                )
            case SelectColumns():
                return Schema([ops.source.schema[name] for name in ops.columns])
            case RenameColumns():

                def rename_column(field: Field) -> Field:
                    if field.name in ops.old_name_to_new:
                        return field.rename(ops.old_name_to_new[field.name])
                    return field

                return Schema(list(map(rename_column, ops.source.schema)))

            case UpdateFeatureTypes():

                def update_feature_type(field: Field) -> Field:
                    if field.name in ops.new_feature_types:
                        return Field(
                            field.name, field.dtype, ops.new_feature_types[field.name]
                        )
                    return field

                return Schema(list(map(update_feature_type, ops.source.schema)))

            case Join():
                left_schema = ops.left_source.schema
                right_schema = ops.right_source.schema
                left_names = {field.name for field in left_schema}
                return Schema(
                    list(
                        flatten(
                            (
                                (field for field in left_schema),
                                (
                                    field
                                    for field in right_schema
                                    if field.name not in left_names
                                    and field.name not in ops.right_join_columns
                                ),
                            )
                        )
                    )
                )

            case (
                LimitRows()
                | OffsetRows()
                | OrderBy()
                | FilterRows()
                | DistinctRows()
                | UpdateMetadata()
                | SetMetadata()
                | RemoveFromMetadata()
                | OutputCsv()
                | TruncateList()
                | AddDecisionTreeSummary()
                | SampleRows()
            ):
                return ops.source.schema

            case EmbeddingMetrics():
                return ops.table.schema

            case RollupByAggregation():
                schema = ops.source.schema
                new_fields = _generate_schema_for_rollup(
                    schema,
                    ops.aggregation_type,
                    ops.group_by_column_names,
                    ops.target_column_name,
                )
                return Schema(list(new_fields.values()))

            case Empty():
                return Schema([])

            case EmbedNode2vecFromEdgeLists():
                return _make_schema_from_node2vec_params(ops)

            case EmbeddingCoordinates():
                return _make_schema_for_embedding_coordinates(ops)

            case Concat():
                return _make_schema_for_concat(ops)

            case UnnestStruct():
                return _make_schema_for_unnest_struct(ops)

            case NestIntoStruct():
                return _make_schema_for_nest_into_struct(ops)

            case AddLiteralColumn():
                return _make_schema_for_add_literal_column(ops)

            case CombineColumns():
                return _make_schema_for_combine_columns(ops)

            case EmbedColumn():
                return _make_schema_for_embed_column(ops)

            case EncodeColumns():
                return _make_schema_for_encode_columns(ops)

            case AggregateColumns():
                return _make_schema_for_aggregate_columns(ops)

            case CorrelateColumns():
                return _make_schema_for_correlate_columns(ops)

            case HistogramColumn():
                return _make_schema_for_histogram_column(ops)

            case ConvertColumnToString():
                return Schema(
                    [
                        ops.source.schema[field.name]
                        if field.name != ops.column_name
                        else Field(
                            field.name,
                            dtype=pa.large_string(),
                            ftype=feature_type.text(),
                        )
                        for field in ops.source.schema
                    ]
                )

            case AddRowIndex():
                return Schema(
                    [
                        *ops.source.schema,
                        Field(
                            ops.row_index_column_name,
                            pa.uint64(),
                            feature_type.numerical(),
                        ),
                    ]
                )
            case Union():
                source = next(iter(ops.sources()), None)
                return source.schema if source else Schema([])

            case EmbedImageColumn():
                return _make_schema_for_embed_image_column(ops)
            case UnnestList():
                return _make_schema_for_unnest_list(ops)
            case DescribeColumns():
                return _make_schema_for_describe_columns(ops)


agg_mapping = {
    table_pb2.AGGREGATION_TYPE_COUNT: "count",
    table_pb2.AGGREGATION_TYPE_AVG: "avg",
    table_pb2.AGGREGATION_TYPE_MODE: "mode",
    table_pb2.AGGREGATION_TYPE_MIN: "min",
    table_pb2.AGGREGATION_TYPE_MAX: "max",
    table_pb2.AGGREGATION_TYPE_SUM: "sum",
}


def _generate_schema_for_rollup(
    schema: Schema,
    agg: table_pb2.AggregationType,
    group_by_column_names: Sequence[str],
    target_column_name: str,
) -> dict[str, Field]:
    new_fields: dict[str, Field] = {}
    group_by_str = "_".join(group_by_column_names)
    for field in schema:
        new_fields.update(
            {key: field for key in group_by_column_names if field.name == key}
        )
        if field.name == target_column_name:
            new_fields.update(
                {
                    f"{agg_mapping[agg]}_{target_column_name}_{group_by_str}": Field(
                        f"{agg_mapping[agg]}_{target_column_name}_{group_by_str}",
                        (
                            pa.uint32()
                            if agg_mapping[agg] == "count"
                            else (
                                pa.float32()
                                if agg_mapping[agg] == "avg"
                                else field.dtype
                            )
                        ),
                        (
                            feature_type.categorical()
                            if agg_mapping[agg] == "mode"
                            else feature_type.numerical()
                        ),
                    )
                }
            )
    return new_fields
