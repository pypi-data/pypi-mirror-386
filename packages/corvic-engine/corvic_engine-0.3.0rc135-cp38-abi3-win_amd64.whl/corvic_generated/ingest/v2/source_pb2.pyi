from buf.validate import validate_pb2 as _validate_pb2
from corvic_generated.ingest.v2 import table_pb2 as _table_pb2
from corvic_generated.orm.v1 import table_pb2 as _table_pb2_1
from google.protobuf import descriptor_pb2 as _descriptor_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class SourceEntry(_message.Message):
    __slots__ = ("id", "name", "num_rows", "schema", "pipeline_id")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    NUM_ROWS_FIELD_NUMBER: _ClassVar[int]
    SCHEMA_FIELD_NUMBER: _ClassVar[int]
    PIPELINE_ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    num_rows: int
    schema: _table_pb2.TableSchema
    pipeline_id: str
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ..., num_rows: _Optional[int] = ..., schema: _Optional[_Union[_table_pb2.TableSchema, _Mapping]] = ..., pipeline_id: _Optional[str] = ...) -> None: ...

class DeleteSourceRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class DeleteSourceResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetSourceRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class GetSourceResponse(_message.Message):
    __slots__ = ("source_entry",)
    SOURCE_ENTRY_FIELD_NUMBER: _ClassVar[int]
    source_entry: SourceEntry
    def __init__(self, source_entry: _Optional[_Union[SourceEntry, _Mapping]] = ...) -> None: ...

class ListSourcesRequest(_message.Message):
    __slots__ = ("room_id", "resource_id")
    ROOM_ID_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    room_id: str
    resource_id: str
    def __init__(self, room_id: _Optional[str] = ..., resource_id: _Optional[str] = ...) -> None: ...

class ListSourcesResponse(_message.Message):
    __slots__ = ("entry",)
    ENTRY_FIELD_NUMBER: _ClassVar[int]
    entry: SourceEntry
    def __init__(self, entry: _Optional[_Union[SourceEntry, _Mapping]] = ...) -> None: ...

class ListSourcesPaginatedCursorPayload(_message.Message):
    __slots__ = ("create_time_of_last_entry",)
    CREATE_TIME_OF_LAST_ENTRY_FIELD_NUMBER: _ClassVar[int]
    create_time_of_last_entry: _timestamp_pb2.Timestamp
    def __init__(self, create_time_of_last_entry: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class ListSourcesPaginatedRequest(_message.Message):
    __slots__ = ("entries_per_page", "room_id", "cursor")
    ENTRIES_PER_PAGE_FIELD_NUMBER: _ClassVar[int]
    ROOM_ID_FIELD_NUMBER: _ClassVar[int]
    CURSOR_FIELD_NUMBER: _ClassVar[int]
    entries_per_page: int
    room_id: str
    cursor: str
    def __init__(self, entries_per_page: _Optional[int] = ..., room_id: _Optional[str] = ..., cursor: _Optional[str] = ...) -> None: ...

class ListSourcesPaginatedResponse(_message.Message):
    __slots__ = ("entry", "cursor")
    ENTRY_FIELD_NUMBER: _ClassVar[int]
    CURSOR_FIELD_NUMBER: _ClassVar[int]
    entry: _containers.RepeatedCompositeFieldContainer[SourceEntry]
    cursor: str
    def __init__(self, entry: _Optional[_Iterable[_Union[SourceEntry, _Mapping]]] = ..., cursor: _Optional[str] = ...) -> None: ...

class GetSourceHeadRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class GetSourceHeadResponse(_message.Message):
    __slots__ = ("entry", "head")
    ENTRY_FIELD_NUMBER: _ClassVar[int]
    HEAD_FIELD_NUMBER: _ClassVar[int]
    entry: SourceEntry
    head: _table_pb2.TableData
    def __init__(self, entry: _Optional[_Union[SourceEntry, _Mapping]] = ..., head: _Optional[_Union[_table_pb2.TableData, _Mapping]] = ...) -> None: ...

class SourceSchemaUpates(_message.Message):
    __slots__ = ("new_feature_types",)
    class NewFeatureTypesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: _table_pb2_1.FeatureType
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[_table_pb2_1.FeatureType, _Mapping]] = ...) -> None: ...
    NEW_FEATURE_TYPES_FIELD_NUMBER: _ClassVar[int]
    new_feature_types: _containers.MessageMap[str, _table_pb2_1.FeatureType]
    def __init__(self, new_feature_types: _Optional[_Mapping[str, _table_pb2_1.FeatureType]] = ...) -> None: ...

class SourceSchemaUpdates(_message.Message):
    __slots__ = ("new_feature_types",)
    class NewFeatureTypesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: _table_pb2_1.FeatureType
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[_table_pb2_1.FeatureType, _Mapping]] = ...) -> None: ...
    NEW_FEATURE_TYPES_FIELD_NUMBER: _ClassVar[int]
    new_feature_types: _containers.MessageMap[str, _table_pb2_1.FeatureType]
    def __init__(self, new_feature_types: _Optional[_Mapping[str, _table_pb2_1.FeatureType]] = ...) -> None: ...

class PatchSourceRequest(_message.Message):
    __slots__ = ("id", "source_schema_updates", "schema_updates")
    ID_FIELD_NUMBER: _ClassVar[int]
    SOURCE_SCHEMA_UPDATES_FIELD_NUMBER: _ClassVar[int]
    SCHEMA_UPDATES_FIELD_NUMBER: _ClassVar[int]
    id: str
    source_schema_updates: SourceSchemaUpates
    schema_updates: SourceSchemaUpdates
    def __init__(self, id: _Optional[str] = ..., source_schema_updates: _Optional[_Union[SourceSchemaUpates, _Mapping]] = ..., schema_updates: _Optional[_Union[SourceSchemaUpdates, _Mapping]] = ...) -> None: ...

class PatchSourceResponse(_message.Message):
    __slots__ = ("source_entry",)
    SOURCE_ENTRY_FIELD_NUMBER: _ClassVar[int]
    source_entry: SourceEntry
    def __init__(self, source_entry: _Optional[_Union[SourceEntry, _Mapping]] = ...) -> None: ...
