from buf.validate import validate_pb2 as _validate_pb2
from corvic_generated.status.v1 import event_pb2 as _event_pb2
from google.protobuf import descriptor_pb2 as _descriptor_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ResourceType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    RESOURCE_TYPE_UNSPECIFIED: _ClassVar[ResourceType]
    RESOURCE_TYPE_TABLE: _ClassVar[ResourceType]
    RESOURCE_TYPE_DIMENSION_TABLE: _ClassVar[ResourceType]
    RESOURCE_TYPE_FACT_TABLE: _ClassVar[ResourceType]
    RESOURCE_TYPE_PDF_DOCUMENT: _ClassVar[ResourceType]
RESOURCE_TYPE_UNSPECIFIED: ResourceType
RESOURCE_TYPE_TABLE: ResourceType
RESOURCE_TYPE_DIMENSION_TABLE: ResourceType
RESOURCE_TYPE_FACT_TABLE: ResourceType
RESOURCE_TYPE_PDF_DOCUMENT: ResourceType

class ResourceMetadata(_message.Message):
    __slots__ = ("name", "mime_type", "room_id", "original_path", "description", "pipeline_id", "type_hint", "size")
    NAME_FIELD_NUMBER: _ClassVar[int]
    MIME_TYPE_FIELD_NUMBER: _ClassVar[int]
    ROOM_ID_FIELD_NUMBER: _ClassVar[int]
    ORIGINAL_PATH_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    PIPELINE_ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_HINT_FIELD_NUMBER: _ClassVar[int]
    SIZE_FIELD_NUMBER: _ClassVar[int]
    name: str
    mime_type: str
    room_id: str
    original_path: str
    description: str
    pipeline_id: str
    type_hint: ResourceType
    size: int
    def __init__(self, name: _Optional[str] = ..., mime_type: _Optional[str] = ..., room_id: _Optional[str] = ..., original_path: _Optional[str] = ..., description: _Optional[str] = ..., pipeline_id: _Optional[str] = ..., type_hint: _Optional[_Union[ResourceType, str]] = ..., size: _Optional[int] = ...) -> None: ...

class ResourceEntry(_message.Message):
    __slots__ = ("id", "name", "mime_type", "md5", "room_id", "size", "original_path", "description", "pipeline_id", "url_depth", "url_width", "referenced_by_source_ids", "created_at", "recent_events", "ingest_recent_events")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    MIME_TYPE_FIELD_NUMBER: _ClassVar[int]
    MD5_FIELD_NUMBER: _ClassVar[int]
    ROOM_ID_FIELD_NUMBER: _ClassVar[int]
    SIZE_FIELD_NUMBER: _ClassVar[int]
    ORIGINAL_PATH_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    PIPELINE_ID_FIELD_NUMBER: _ClassVar[int]
    URL_DEPTH_FIELD_NUMBER: _ClassVar[int]
    URL_WIDTH_FIELD_NUMBER: _ClassVar[int]
    REFERENCED_BY_SOURCE_IDS_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    RECENT_EVENTS_FIELD_NUMBER: _ClassVar[int]
    INGEST_RECENT_EVENTS_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    mime_type: str
    md5: str
    room_id: str
    size: int
    original_path: str
    description: str
    pipeline_id: str
    url_depth: int
    url_width: int
    referenced_by_source_ids: _containers.RepeatedScalarFieldContainer[str]
    created_at: _timestamp_pb2.Timestamp
    recent_events: _containers.RepeatedCompositeFieldContainer[_event_pb2.Event]
    ingest_recent_events: _containers.RepeatedCompositeFieldContainer[_event_pb2.Event]
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ..., mime_type: _Optional[str] = ..., md5: _Optional[str] = ..., room_id: _Optional[str] = ..., size: _Optional[int] = ..., original_path: _Optional[str] = ..., description: _Optional[str] = ..., pipeline_id: _Optional[str] = ..., url_depth: _Optional[int] = ..., url_width: _Optional[int] = ..., referenced_by_source_ids: _Optional[_Iterable[str]] = ..., created_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., recent_events: _Optional[_Iterable[_Union[_event_pb2.Event, _Mapping]]] = ..., ingest_recent_events: _Optional[_Iterable[_Union[_event_pb2.Event, _Mapping]]] = ...) -> None: ...

class CreateUploadURLRequest(_message.Message):
    __slots__ = ("metadata", "origin")
    METADATA_FIELD_NUMBER: _ClassVar[int]
    ORIGIN_FIELD_NUMBER: _ClassVar[int]
    metadata: ResourceMetadata
    origin: str
    def __init__(self, metadata: _Optional[_Union[ResourceMetadata, _Mapping]] = ..., origin: _Optional[str] = ...) -> None: ...

class CreateUploadURLResponse(_message.Message):
    __slots__ = ("url", "token")
    URL_FIELD_NUMBER: _ClassVar[int]
    TOKEN_FIELD_NUMBER: _ClassVar[int]
    url: str
    token: str
    def __init__(self, url: _Optional[str] = ..., token: _Optional[str] = ...) -> None: ...

class UploadURLTokenPayload(_message.Message):
    __slots__ = ("metadata", "filename", "resource_id")
    METADATA_FIELD_NUMBER: _ClassVar[int]
    FILENAME_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    metadata: ResourceMetadata
    filename: str
    resource_id: str
    def __init__(self, metadata: _Optional[_Union[ResourceMetadata, _Mapping]] = ..., filename: _Optional[str] = ..., resource_id: _Optional[str] = ...) -> None: ...

class FinalizeUploadURLRequest(_message.Message):
    __slots__ = ("token", "mark_failure", "reason")
    TOKEN_FIELD_NUMBER: _ClassVar[int]
    MARK_FAILURE_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    token: str
    mark_failure: bool
    reason: str
    def __init__(self, token: _Optional[str] = ..., mark_failure: bool = ..., reason: _Optional[str] = ...) -> None: ...

class FinalizeUploadURLResponse(_message.Message):
    __slots__ = ("entry",)
    ENTRY_FIELD_NUMBER: _ClassVar[int]
    entry: ResourceEntry
    def __init__(self, entry: _Optional[_Union[ResourceEntry, _Mapping]] = ...) -> None: ...

class FetchAndFinalizeExternalURLRequest(_message.Message):
    __slots__ = ("room_id", "pipeline_id", "original_path", "url_depth", "url_width")
    ROOM_ID_FIELD_NUMBER: _ClassVar[int]
    PIPELINE_ID_FIELD_NUMBER: _ClassVar[int]
    ORIGINAL_PATH_FIELD_NUMBER: _ClassVar[int]
    URL_DEPTH_FIELD_NUMBER: _ClassVar[int]
    URL_WIDTH_FIELD_NUMBER: _ClassVar[int]
    room_id: str
    pipeline_id: str
    original_path: str
    url_depth: int
    url_width: int
    def __init__(self, room_id: _Optional[str] = ..., pipeline_id: _Optional[str] = ..., original_path: _Optional[str] = ..., url_depth: _Optional[int] = ..., url_width: _Optional[int] = ...) -> None: ...

class FetchAndFinalizeExternalURLResponse(_message.Message):
    __slots__ = ("entry",)
    ENTRY_FIELD_NUMBER: _ClassVar[int]
    entry: ResourceEntry
    def __init__(self, entry: _Optional[_Union[ResourceEntry, _Mapping]] = ...) -> None: ...

class DeleteResourceRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class DeleteResourceResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetResourceRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class GetResourceResponse(_message.Message):
    __slots__ = ("entry",)
    ENTRY_FIELD_NUMBER: _ClassVar[int]
    entry: ResourceEntry
    def __init__(self, entry: _Optional[_Union[ResourceEntry, _Mapping]] = ...) -> None: ...

class ListResourcesRequest(_message.Message):
    __slots__ = ("room_id",)
    ROOM_ID_FIELD_NUMBER: _ClassVar[int]
    room_id: str
    def __init__(self, room_id: _Optional[str] = ...) -> None: ...

class ListResourcesResponse(_message.Message):
    __slots__ = ("entry",)
    ENTRY_FIELD_NUMBER: _ClassVar[int]
    entry: ResourceEntry
    def __init__(self, entry: _Optional[_Union[ResourceEntry, _Mapping]] = ...) -> None: ...

class ResourceList(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, id: _Optional[_Iterable[str]] = ...) -> None: ...

class WatchResourcesRequest(_message.Message):
    __slots__ = ("room_id", "ids")
    ROOM_ID_FIELD_NUMBER: _ClassVar[int]
    IDS_FIELD_NUMBER: _ClassVar[int]
    room_id: str
    ids: ResourceList
    def __init__(self, room_id: _Optional[str] = ..., ids: _Optional[_Union[ResourceList, _Mapping]] = ...) -> None: ...

class WatchResourcesResponse(_message.Message):
    __slots__ = ("updated_resource",)
    UPDATED_RESOURCE_FIELD_NUMBER: _ClassVar[int]
    updated_resource: ResourceEntry
    def __init__(self, updated_resource: _Optional[_Union[ResourceEntry, _Mapping]] = ...) -> None: ...

class ListResourcesPaginatedCursorPayload(_message.Message):
    __slots__ = ("create_time_of_last_entry", "room_id", "pipeline_id")
    CREATE_TIME_OF_LAST_ENTRY_FIELD_NUMBER: _ClassVar[int]
    ROOM_ID_FIELD_NUMBER: _ClassVar[int]
    PIPELINE_ID_FIELD_NUMBER: _ClassVar[int]
    create_time_of_last_entry: _timestamp_pb2.Timestamp
    room_id: str
    pipeline_id: str
    def __init__(self, create_time_of_last_entry: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., room_id: _Optional[str] = ..., pipeline_id: _Optional[str] = ...) -> None: ...

class ListResourcesPaginatedRequest(_message.Message):
    __slots__ = ("room_id", "pipeline_id", "entries_per_page", "cursor")
    ROOM_ID_FIELD_NUMBER: _ClassVar[int]
    PIPELINE_ID_FIELD_NUMBER: _ClassVar[int]
    ENTRIES_PER_PAGE_FIELD_NUMBER: _ClassVar[int]
    CURSOR_FIELD_NUMBER: _ClassVar[int]
    room_id: str
    pipeline_id: str
    entries_per_page: int
    cursor: str
    def __init__(self, room_id: _Optional[str] = ..., pipeline_id: _Optional[str] = ..., entries_per_page: _Optional[int] = ..., cursor: _Optional[str] = ...) -> None: ...

class ListResourcesPaginatedResponse(_message.Message):
    __slots__ = ("resource_entries", "cursor")
    RESOURCE_ENTRIES_FIELD_NUMBER: _ClassVar[int]
    CURSOR_FIELD_NUMBER: _ClassVar[int]
    resource_entries: _containers.RepeatedCompositeFieldContainer[ResourceEntry]
    cursor: str
    def __init__(self, resource_entries: _Optional[_Iterable[_Union[ResourceEntry, _Mapping]]] = ..., cursor: _Optional[str] = ...) -> None: ...

class CreateResourceDownloadURLRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class CreateResourceDownloadURLResponse(_message.Message):
    __slots__ = ("url",)
    URL_FIELD_NUMBER: _ClassVar[int]
    url: str
    def __init__(self, url: _Optional[str] = ...) -> None: ...

class CreateResourcePreviewURLRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class CreateResourcePreviewURLResponse(_message.Message):
    __slots__ = ("url",)
    URL_FIELD_NUMBER: _ClassVar[int]
    url: str
    def __init__(self, url: _Optional[str] = ...) -> None: ...
