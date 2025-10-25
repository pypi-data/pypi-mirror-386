from clavata.gateway.v1 import content_pb2 as _content_pb2
from clavata.shared.v1 import public_pb2 as _public_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class AddToContentLakeRequest(_message.Message):
    __slots__ = ("content_data",)
    CONTENT_DATA_FIELD_NUMBER: _ClassVar[int]
    content_data: _containers.RepeatedCompositeFieldContainer[_public_pb2.ContentData]
    def __init__(self, content_data: _Optional[_Iterable[_Union[_public_pb2.ContentData, _Mapping]]] = ...) -> None: ...

class ContentLakeEntry(_message.Message):
    __slots__ = ("content_hash", "object_store_url", "content_mode", "original_index")
    CONTENT_HASH_FIELD_NUMBER: _ClassVar[int]
    OBJECT_STORE_URL_FIELD_NUMBER: _ClassVar[int]
    CONTENT_MODE_FIELD_NUMBER: _ClassVar[int]
    ORIGINAL_INDEX_FIELD_NUMBER: _ClassVar[int]
    content_hash: str
    object_store_url: str
    content_mode: str
    original_index: int
    def __init__(self, content_hash: _Optional[str] = ..., object_store_url: _Optional[str] = ..., content_mode: _Optional[str] = ..., original_index: _Optional[int] = ...) -> None: ...

class AddToContentLakeResponse(_message.Message):
    __slots__ = ("content_lake_entries", "failed_content", "summary")
    CONTENT_LAKE_ENTRIES_FIELD_NUMBER: _ClassVar[int]
    FAILED_CONTENT_FIELD_NUMBER: _ClassVar[int]
    SUMMARY_FIELD_NUMBER: _ClassVar[int]
    content_lake_entries: _containers.RepeatedCompositeFieldContainer[ContentLakeEntry]
    failed_content: _containers.RepeatedCompositeFieldContainer[_content_pb2.FailedContent]
    summary: _content_pb2.BatchSummary
    def __init__(self, content_lake_entries: _Optional[_Iterable[_Union[ContentLakeEntry, _Mapping]]] = ..., failed_content: _Optional[_Iterable[_Union[_content_pb2.FailedContent, _Mapping]]] = ..., summary: _Optional[_Union[_content_pb2.BatchSummary, _Mapping]] = ...) -> None: ...
