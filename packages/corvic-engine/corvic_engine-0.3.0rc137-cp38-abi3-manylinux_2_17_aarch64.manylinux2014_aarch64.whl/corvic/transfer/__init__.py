"""Common machinery for using protocol buffers as transfer objects."""

from corvic.transfer._common_transformations import (
    UNCOMMITTED_ID_PREFIX,
    OrmIdT,
    generate_uncommitted_id_str,
    non_empty_timestamp_to_datetime,
    translate_nongenerated_orm_id,
    translate_orm_id,
)
from corvic.transfer._orm_backed_proto import (
    HasIdOrmBackedProto,
    HasProtoSelf,
    OrmBackedProto,
    OrmHasIdModel,
    OrmHasIdT,
    OrmModel,
    OrmT,
    ProtoHasIdModel,
    ProtoHasIdT,
    ProtoModel,
    ProtoT,
    UsesOrmID,
)

__all__ = [
    "UNCOMMITTED_ID_PREFIX",
    "HasIdOrmBackedProto",
    "HasProtoSelf",
    "OrmBackedProto",
    "OrmHasIdModel",
    "OrmHasIdT",
    "OrmIdT",
    "OrmModel",
    "OrmT",
    "ProtoHasIdModel",
    "ProtoHasIdT",
    "ProtoModel",
    "ProtoT",
    "UsesOrmID",
    "generate_uncommitted_id_str",
    "non_empty_timestamp_to_datetime",
    "translate_nongenerated_orm_id",
    "translate_orm_id",
]
