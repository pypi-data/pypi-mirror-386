"""Table."""

from __future__ import annotations

import dataclasses
import functools
import uuid
from collections.abc import Iterable, Mapping, Sequence
from typing import (
    Any,
    Final,
    Literal,
    Protocol,
    Self,
    TypeAlias,
    TypeVar,
    cast,
)

import more_itertools
import polars as pl
import pyarrow as pa
import pyarrow.parquet as pq
import structlog
from google.protobuf import struct_pb2

from corvic import eorm, op_graph, result
from corvic.op_graph import Encoder, Schema
from corvic.system import (
    Client,
    DataMisplacedError,
    ExecutionContext,
    TableComputeContext,
)

MetadataValue: TypeAlias = (
    "None | bool | str | float | dict[str, MetadataValue] | list[MetadataValue]"
)


class TypedMetadata(Protocol):
    """Metadata types implement this to participate in the typed lookup protocol."""

    @classmethod
    def metadata_key(cls) -> str: ...

    @classmethod
    def from_value(cls, value: MetadataValue) -> Self: ...

    def to_value(self) -> MetadataValue: ...


_TM = TypeVar("_TM", bound=TypedMetadata)


_logger = structlog.get_logger()


@dataclasses.dataclass
class DataclassAsTypedMetadataMixin:
    """A TypedMetadata mixin for dataclasses.

    Inheriting from this mixin adds the methods necessary for implementing
    the TypedMetadata protocol. Each implementer must choose their own unique
    METADATA_KEY.

    NOTE: Removing fields, changing the name of fields, or adding new fields
    that do not have default values will cause exceptions when reading old
    serialized data.

    Example Usage:
    >>> @dataclass
    >>> ModuleSpecificMetadata(DataclassAsTypedMetadataMixin):
    >>>     @classmethod
    >>>     def metadata_key(cls):
    >>>         return "unique-metadata-name"
    >>>     string_value: str
    >>>     ...
    """

    @classmethod
    def from_value(cls, value: MetadataValue):
        if not isinstance(value, dict):
            raise result.InvalidArgumentError("expected dict value")

        return cls(**value)

    def to_value(self) -> MetadataValue:
        return dataclasses.asdict(self)


class Table:
    """Table that computed or loaded from storage when needed.

    Table objects are a little different in that they are constructed (e.g., in memory)
    before they are registered. A table that is not registered is an "anonymous" table.
    Anonymous tables have no ID (Table.id returns the empty string) and cannot be found
    by table client instances.
    """

    MAX_ROWS_PER_SLICE: Final = 4096

    _client: Client
    _op: Final[op_graph.Op]
    _staged: bool
    _in_memory_inputs: Mapping[str, pl.DataFrame]

    def __init__(
        self,
        client: Client,
        op: op_graph.Op,
        in_memory_inputs: Mapping[str, pl.DataFrame],
    ):
        self._client = client
        self._op = op
        self._staged = False
        self._in_memory_inputs = in_memory_inputs

    def __hash__(self):
        return hash(self._op)

    def __eq__(self, other: object):
        if not isinstance(other, type(self)):
            return False
        return self._op == other._op

    @property
    def client(self):
        return self._client

    @property
    def op_graph(self):
        return self._op

    @property
    def in_memory_inputs(self):
        return self._in_memory_inputs

    def _compute_num_rows(self, op: op_graph.Op) -> int | None:  # noqa: C901
        match op:
            case (
                op_graph.op.SelectFromStaging()
                | op_graph.op.ReadFromParquet()
                | op_graph.op.SelectFromVectorStaging()
            ):
                return op.expected_rows
            case op_graph.op.InMemoryInput():
                in_memory_inputs = self.in_memory_inputs or {}
                this_input = in_memory_inputs.get(op.input_name)
                if this_input is None:
                    return None
                return len(this_input)
            case (
                op_graph.op.SelectColumns()
                | op_graph.op.RenameColumns()
                | op_graph.op.UpdateMetadata()
                | op_graph.op.SetMetadata()
                | op_graph.op.RemoveFromMetadata()
                | op_graph.op.UpdateFeatureTypes()
                | op_graph.op.UnnestStruct()
                | op_graph.op.AddLiteralColumn()
                | op_graph.op.CombineColumns()
                | op_graph.op.EmbedColumn()
                | op_graph.op.EncodeColumns()
                | op_graph.op.NestIntoStruct()
                | op_graph.op.CorrelateColumns()
                | op_graph.op.HistogramColumn()
                | op_graph.op.ConvertColumnToString()
                | op_graph.op.AddRowIndex()
                | op_graph.op.OutputCsv()
                | op_graph.op.TruncateList()
                | op_graph.op.EmbedImageColumn()
                | op_graph.op.UnnestList()
                | op_graph.op.DescribeColumns()
            ):
                return self._compute_num_rows(op.source)
            case op_graph.op.LimitRows() | op_graph.op.SampleRows():
                source_rows = self._compute_num_rows(op.source)
                return (
                    min(op.num_rows, source_rows) if source_rows is not None else None
                )
            case op_graph.op.OffsetRows():
                source_rows = self._compute_num_rows(op.source)
                return (
                    max(source_rows - op.num_rows, 0)
                    if source_rows is not None
                    else None
                )
            case op_graph.op.Empty():
                return 0
            case op_graph.op.Concat():
                match op.how:
                    case (
                        "vertical"
                        | "vertical_relaxed"
                        | "diagonal"
                        | "diagonal_relaxed"
                    ):
                        source_row_counts = (
                            self._compute_num_rows(src) for src in op.sources()
                        )
                        rows = 0
                        for count in source_row_counts:
                            if count is None:
                                return None
                            rows += count
                        return rows
                    case "horizontal":
                        source_row_counts = (
                            self._compute_num_rows(src) for src in op.sources()
                        )
                        rows = 0
                        for count in source_row_counts:
                            if count is None:
                                return None
                            rows = max(count, rows)
                        return rows
                    case "align":
                        raise NotImplementedError()
            case op_graph.op.AggregateColumns():
                return 1
            case (
                op_graph.op.Join()
                | op_graph.op.RollupByAggregation()
                | op_graph.op.OrderBy()
                | op_graph.op.FilterRows()
                | op_graph.op.DistinctRows()
                | op_graph.op.EmbedNode2vecFromEdgeLists()
                | op_graph.op.EmbeddingMetrics()
                | op_graph.op.EmbeddingCoordinates()
                | op_graph.op.AddDecisionTreeSummary()
            ):
                return None
            case op_graph.op.Union():
                if op.distinct:
                    return None
                row_count = 0
                for src in op.sources():
                    src_row_count = self._compute_num_rows(src)
                    if src_row_count is None:
                        return None
                    row_count += src_row_count
                return row_count

    @classmethod
    def _compute_metadata(cls, op: op_graph.Op) -> dict[str, Any]:
        match op:
            case op_graph.op.SetMetadata():
                return dict(op.new_metadata)

            case op_graph.op.UpdateMetadata():
                source_metadata = cls._compute_metadata(op.source)
                source_metadata.update(op.metadata_updates)
                return source_metadata

            case op_graph.op.RemoveFromMetadata():
                source_metadata = cls._compute_metadata(op.source)
                for key in op.keys_to_remove:
                    source_metadata.pop(key, None)
                return source_metadata

            case op_graph.op.Join():
                source_metadata = cls._compute_metadata(op.right_source)
                # for join, left source takes precedence in terms
                # of column names, ditto that for metadata names
                source_metadata.update(cls._compute_metadata(op.left_source))
                return source_metadata

            case (
                op_graph.op.SelectColumns()
                | op_graph.op.RenameColumns()
                | op_graph.op.LimitRows()
                | op_graph.op.OffsetRows()
                | op_graph.op.OrderBy()
                | op_graph.op.FilterRows()
                | op_graph.op.UpdateFeatureTypes()
                | op_graph.op.RollupByAggregation()
                | op_graph.op.DistinctRows()
                | op_graph.op.EmbedNode2vecFromEdgeLists()
                | op_graph.op.SelectFromStaging()
                | op_graph.op.Empty()
                | op_graph.op.EmbeddingMetrics()
                | op_graph.op.EmbeddingCoordinates()
                | op_graph.op.ReadFromParquet()
                | op_graph.op.SelectFromVectorStaging()
                | op_graph.op.Concat()
                | op_graph.op.UnnestStruct()
                | op_graph.op.NestIntoStruct()
                | op_graph.op.AddLiteralColumn()
                | op_graph.op.CombineColumns()
                | op_graph.op.EmbedColumn()
                | op_graph.op.EncodeColumns()
                | op_graph.op.AggregateColumns()
                | op_graph.op.CorrelateColumns()
                | op_graph.op.HistogramColumn()
                | op_graph.op.ConvertColumnToString()
                | op_graph.op.AddRowIndex()
                | op_graph.op.OutputCsv()
                | op_graph.op.TruncateList()
                | op_graph.op.Union()
                | op_graph.op.EmbedImageColumn()
                | op_graph.op.AddDecisionTreeSummary()
                | op_graph.op.UnnestList()
                | op_graph.op.SampleRows()
                | op_graph.op.DescribeColumns()
                | op_graph.op.InMemoryInput()
            ):
                metadata = dict[str, Any]()
                for source in op.sources():
                    metadata.update(cls._compute_metadata(source))
                return metadata

    @functools.cached_property
    def num_rows(self):
        return self._compute_num_rows(self.op_graph)

    @functools.cached_property
    def schema(self) -> Schema:
        return self.op_graph.schema

    @functools.cached_property
    def metadata(self) -> Mapping[str, Any]:
        return self._compute_metadata(self.op_graph)

    @classmethod
    def from_ops(
        cls,
        client: Client,
        op: op_graph.Op,
        in_memory_inputs: Mapping[str, pl.DataFrame] | None = None,
    ):
        return cls(client, op=op, in_memory_inputs=in_memory_inputs or {})

    @classmethod
    def from_bytes(
        cls,
        client: Client,
        op: bytes,
        in_memory_inputs: Mapping[str, pl.DataFrame] | None = None,
    ):
        return cls.from_ops(client, op_graph.op.from_bytes(op), in_memory_inputs or {})

    @classmethod
    def from_parquet_file(  # noqa: C901
        cls,
        client: Client,
        url: str,
    ) -> result.Ok[Table] | DataMisplacedError | result.InvalidArgumentError:
        """Build a table from an arrow Table."""
        blob = client.storage_manager.blob_from_url(url)
        try:
            with blob.open("rb") as stream:
                metadata = pq.read_metadata(stream)
        except pa.ArrowInvalid as exc:
            return result.InvalidArgumentError(f"parsing parquet: {exc}")
        num_rows = metadata.num_rows
        arrow_schema = metadata.schema.to_arrow_schema()
        schema = Schema.from_arrow(arrow_schema)
        case_insensitive_schema = {column.name.upper() for column in schema}
        if len(schema) != len(case_insensitive_schema):
            return result.InvalidArgumentError(
                "column names are case insensitive and must be unique"
            )
        null_columns: list[str] = []
        kept_columns: list[str] = []
        for column in schema:
            if pa.types.is_null(column.dtype):
                null_columns.append(column.name)
            else:
                kept_columns.append(column.name)
        if len(null_columns) > 0:
            _logger.warning("dropped null columns", columns=null_columns)

        blob_name = client.storage_manager.blob_from_url(blob.url).name.removeprefix(
            client.storage_manager.tabular_prefix + "/"
        )

        match op_graph.from_staging(
            blob_names=[blob_name],
            arrow_schema=schema.to_arrow(),
            feature_types=[field.ftype for field in schema],
            expected_rows=num_rows,
        ):
            case result.Ok(op):
                pass
            case result.InvalidArgumentError() as error:
                return error
        if len(null_columns) > 0:
            match op.select_columns(kept_columns):
                case result.InvalidArgumentError() as error:
                    return error
                case result.Ok(op):
                    pass

        return result.Ok(cls.from_ops(client, op))

    def to_bytes(self):
        return self.op_graph.to_bytes()

    async def to_polars(
        self, room_id: eorm.RoomID, *, flatten_single_field: bool = False
    ) -> (
        result.Ok[Iterable[pl.DataFrame]]
        | result.InvalidArgumentError
        | result.UnavailableError
    ):
        """Stream over the view as a series of Polars DataFrames."""
        match await self.to_batches(room_id=room_id):
            case result.Ok(batch_reader):
                pass
            case err:
                return err
        empty_table = cast(
            pl.DataFrame, pl.from_arrow(self.schema.to_arrow().empty_table())
        )
        polars_schema = empty_table.schema

        def generator():
            some = False
            for batch in batch_reader:
                df_batch = cast(
                    pl.DataFrame,
                    pl.from_arrow(batch, rechunk=False, schema_overrides=polars_schema),
                ).select(key for key in polars_schema)

                some = True
                yield df_batch
            if not some:
                yield empty_table

        return result.Ok(generator())

    @classmethod
    def _get_staging_ops(
        cls, op: op_graph.Op
    ) -> Iterable[op_graph.op.SelectFromStaging]:
        match op:
            case op_graph.op.SelectFromStaging():
                return [op]
            case _:
                return more_itertools.flatten(map(cls._get_staging_ops, op.sources()))

    def head(
        self, num_rows: int = 10
    ) -> result.InvalidArgumentError | result.Ok[Table]:
        """Get the first `num_rows` rows of the table."""
        return self.op_graph.limit_rows(num_rows=num_rows).map(
            lambda op: Table(self.client, op, self.in_memory_inputs)
        )

    def sample_rows(
        self, num_rows: int = 10
    ) -> result.InvalidArgumentError | result.Ok[Table]:
        """Get a sample of `num_rows` rows of the table."""
        return self.op_graph.sample_rows(
            sample_strategy=op_graph.sample_strategy.uniform_random(), num_rows=num_rows
        ).map(lambda op: Table(self.client, op, self.in_memory_inputs))

    def distinct_rows(self) -> Table:
        return Table(
            self.client,
            self.op_graph.distinct_rows().unwrap_or_raise(),
            self.in_memory_inputs,
        )

    def order_by(self, columns: Sequence[str], *, desc: bool) -> Table:
        return Table(
            self.client,
            self.op_graph.order_by(columns=columns, desc=desc).unwrap_or_raise(),
            self.in_memory_inputs,
        )

    def update_feature_types(
        self, new_feature_types: Mapping[str, op_graph.FeatureType]
    ) -> Table:
        return Table(
            self.client,
            self.op_graph.update_feature_types(
                new_feature_types=new_feature_types
            ).unwrap_or_raise(),
            self.in_memory_inputs,
        )

    async def to_batches(
        self, room_id: eorm.RoomID
    ) -> (
        result.Ok[pa.RecordBatchReader]
        | result.InvalidArgumentError
        | result.UnavailableError
    ):
        """Convert every row to a dictionary of Python-native values."""
        context = ExecutionContext(
            room_id=room_id,
            tables_to_compute=[
                TableComputeContext(
                    self.op_graph,
                    output_url_prefix=self.client.storage_manager.make_tabular_blob(
                        room_id=room_id,
                        suffix=f"anonymous_tables-{uuid.uuid4()}.parquet",
                    ).url,
                )
            ],
        )
        return (await self.client.executor.execute(context)).map(
            lambda result: result.tables[0].to_batch_reader()
        )

    @staticmethod
    def _resolve_conflicting_column_names(
        left_schema: Schema,
        right_schema: Schema,
        conflict_suffix: str,
        right_join_columns: list[str] | str,
        right_op_graph: op_graph.Op,
    ) -> op_graph.Op:
        """Returns the new schema the right table op_graph.

        The new schema will be returned with any necessary renames applied.
        """
        if isinstance(right_join_columns, str):
            right_join_columns = [right_join_columns]
        new_fields = {field.name: field for field in left_schema}
        right_table_renames: dict[str, str] = {}
        for field in right_schema:
            if field.name in right_join_columns:
                continue
            if field.name in new_fields:
                new_field = field.rename(f"{field.name}{conflict_suffix}")
                new_fields[new_field.name] = new_field
                right_table_renames[field.name] = new_field.name
            else:
                new_fields[field.name] = field

        if right_table_renames:
            right_op_graph = right_op_graph.rename_columns(
                right_table_renames
            ).unwrap_or_raise()

        return right_op_graph

    def rename_columns(self, old_to_new: Mapping[str, str]) -> Table:
        old_to_new = {
            old_name: new_name
            for old_name, new_name in old_to_new.items()
            if old_name != new_name
        }
        if not old_to_new:
            return self

        return Table(
            self.client,
            self.op_graph.rename_columns(old_to_new).unwrap_or_raise(),
            self.in_memory_inputs,
        )

    def join(
        self,
        right_table: Table,
        *,
        left_on: str | list[str],
        right_on: str | list[str],
        how: Literal["inner", "left outer"] = "left outer",
        suffix: str | None = None,
    ) -> Table:
        """Join this Table with another.

        If suffix is not provided, other_table.name is appended to the name of columns
        in other_table that conflict with column names in this table.
        """
        suffix = suffix or "_right"
        right_log = self._resolve_conflicting_column_names(
            self.schema,
            right_table.schema,
            right_join_columns=right_on,
            conflict_suffix=suffix,
            right_op_graph=right_table.op_graph,
        )

        in_memory_inputs = {**self.in_memory_inputs, **right_table.in_memory_inputs}
        if len(in_memory_inputs) != len(self.in_memory_inputs) + len(
            right_table.in_memory_inputs
        ):
            raise result.InvalidArgumentError("in-memory input names conflict")

        return Table(
            self.client,
            op=self.op_graph.join(
                right_log,
                left_on=left_on,
                right_on=right_on,
                how=how,
            ).unwrap_or_raise(),
            in_memory_inputs=in_memory_inputs,
        )

    def has_typed_metadata(self, typed_metadata: type[TypedMetadata]) -> bool:
        return typed_metadata.metadata_key() in self.metadata

    def get_typed_metadata(self, typed_metadata: type[_TM]) -> _TM:
        if not self.has_typed_metadata(typed_metadata):
            raise result.NotFoundError("typed metadata key was not set")
        value = self.metadata[typed_metadata.metadata_key()]
        return typed_metadata.from_value(value)

    def update_typed_metadata(self, *typed_metadatas: TypedMetadata):
        return self.update_metadata(
            {
                typed_metadata.metadata_key(): typed_metadata.to_value()
                for typed_metadata in typed_metadatas
            }
        )

    def update_metadata(self, metadata_updates: Mapping[str, Any]):
        if not metadata_updates:
            return self
        return Table(
            self.client,
            op=self.op_graph.update_metadata(metadata_updates).unwrap_or_raise(),
            in_memory_inputs=self.in_memory_inputs,
        )

    def set_metadata(self, new_metadata: Mapping[str, Any]):
        """Drop the old metadata and overwrite it with new_metadata."""
        return Table(
            self.client,
            op=self.op_graph.set_metadata(new_metadata).unwrap_or_raise(),
            in_memory_inputs=self.in_memory_inputs,
        )

    def remove_from_metadata(self, keys_to_remove: Sequence[str]) -> Table:
        """Remove the listed keys from the metadata if they exist."""
        if isinstance(keys_to_remove, str):
            keys_to_remove = [keys_to_remove]
        keys_to_remove = [key for key in keys_to_remove if key in self.metadata]
        if not keys_to_remove:
            return self
        return Table(
            self.client,
            op=self.op_graph.remove_from_metadata(keys_to_remove).unwrap_or_raise(),
            in_memory_inputs=self.in_memory_inputs,
        )

    def select(self, columns_to_select: Sequence[str]) -> Table:
        """Return a table with only the columns listed."""
        return Table(
            self.client,
            op=self.op_graph.select_columns(
                columns=columns_to_select
            ).unwrap_or_raise(),
            in_memory_inputs=self.in_memory_inputs,
        )

    def without_columns(
        self,
        columns_to_remove: Iterable[str],
    ) -> Table:
        """Return a table without the columns listed."""
        raise NotImplementedError()

    def rollup(
        self,
        *,
        group_by: str | list[str],
        target: str,
        agg: Literal["count", "avg", "mode", "min", "max", "sum"],
    ) -> Table:
        """Apply a basic rollup.

        The new column's name is computed from the target's name and the computation
        applied.
        """
        return Table(
            self.client,
            op=self.op_graph.rollup_by_aggregation(
                group_by=group_by,
                target=target,
                aggregation=agg,
            ).unwrap_or_raise(),
            in_memory_inputs=self.in_memory_inputs,
        )

    def _ensure_filter_columns_exist(self, row_filter: op_graph.RowFilter):
        match row_filter:
            case op_graph.row_filter.CombineFilters():
                for filter_ in row_filter.row_filters:
                    self._ensure_filter_columns_exist(filter_)
            case op_graph.row_filter.CompareColumnToLiteral():
                if not self.schema.has_column(row_filter.column_name):
                    raise result.InvalidArgumentError(
                        "column does not exist",
                        column_name=row_filter.column_name,
                    )

    def filter_rows(self, row_filter: op_graph.RowFilter) -> Table:
        self._ensure_filter_columns_exist(row_filter)
        return Table(
            self.client,
            op=self.op_graph.filter_rows(row_filter).unwrap_or_raise(),
            in_memory_inputs=self.in_memory_inputs,
        )

    def embed_text(
        self,
        *,
        target: str,
        model_name: str,
    ) -> Table:
        """Produce a table with new embedding column.

        The new column's name is computed from the target's name and the
        computation applied.
        """
        raise NotImplementedError()

    def encode_columns(self, *, target: str, encoder: Encoder) -> Table:
        """Produce a table with new encoded column."""
        raise NotImplementedError()

    def add_literal(
        self,
        *,
        target: str,
        literal: struct_pb2.Value | float | str | bool,
        dtype: pa.DataType,
        ftype: op_graph.FeatureType | None = None,
    ) -> Table:
        new_op = self.op_graph.add_literal_column(
            target, literal=literal, dtype=dtype, ftype=ftype
        ).unwrap_or_raise()
        return Table(self.client, op=new_op, in_memory_inputs=self.in_memory_inputs)

    def add_row_index(
        self,
        *,
        target: str,
        offset: int = 0,
    ) -> Table:
        new_op = self.op_graph.add_row_index(target, offset=offset).unwrap_or_raise()
        return Table(self.client, op=new_op, in_memory_inputs=self.in_memory_inputs)

    def convert_column_to_string(self, column_name: str) -> Table:
        new_op = self.op_graph.convert_column_to_string(column_name).unwrap_or_raise()
        return Table(self.client, op=new_op, in_memory_inputs=self.in_memory_inputs)

    def output_csv(self, *, url: str, include_header: bool) -> Table:
        new_op = self.op_graph.output_csv(
            url=url, include_header=include_header
        ).unwrap_or_raise()
        return Table(self.client, op=new_op, in_memory_inputs=self.in_memory_inputs)

    def truncate_list(
        self,
        *,
        list_column_name: str,
        target_list_length: int,
        padding_value: float | str | bool,
    ) -> Table:
        new_op = self.op_graph.truncate_list(
            list_column_name=list_column_name,
            target_list_length=target_list_length,
            padding_value=padding_value,
        ).unwrap_or_raise()
        return Table(self.client, op=new_op, in_memory_inputs=self.in_memory_inputs)

    def describe(self) -> result.Ok[Table] | result.InvalidArgumentError:
        """Summary statistics for a Table."""
        column_names = [field.name for field in self.schema]
        return result.Ok(
            Table(
                self.client,
                op=self.op_graph.describe(column_names).unwrap_or_raise(),
                in_memory_inputs=self.in_memory_inputs,
            )
        )
