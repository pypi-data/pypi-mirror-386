"""Op graphs that describe operations on tables."""

from corvic.op_graph import aggregation, sample_strategy
from corvic.op_graph import encoders as encoder
from corvic.op_graph import feature_types as feature_type
from corvic.op_graph import ops as op
from corvic.op_graph import row_filters as row_filter
from corvic.op_graph._schema import Field
from corvic.op_graph._transformations import replace_op_sources
from corvic.op_graph.errors import OpParseError
from corvic.op_graph.ops import Schema

# included as convenience here since it's part of the public interface
from corvic_generated.algorithm.graph.v1.graph_pb2 import Node2VecParameters
from corvic_generated.orm.v1.table_pb2 import ConcatList, ConcatString, JoinType

empty = op.empty
from_staging = op.from_staging
EdgeListTable = op.EdgeListTable
Op = op.Op
FeatureType = feature_type.FeatureType
Encoder = encoder.Encoder
RowFilter = row_filter.RowFilter
Aggregation = aggregation.Aggregation
SampleStrategy = sample_strategy.SampleStrategy

__all__ = [
    "Aggregation",
    "ConcatList",
    "ConcatString",
    "EdgeListTable",
    "Encoder",
    "FeatureType",
    "Field",
    "JoinType",
    "Node2VecParameters",
    "Op",
    "OpParseError",
    "SampleStrategy",
    "Schema",
    "aggregation",
    "empty",
    "encoder",
    "feature_type",
    "from_staging",
    "op",
    "replace_op_sources",
    "row_filter",
]
