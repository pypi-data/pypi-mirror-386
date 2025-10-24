from jitxcore._proto import local_pb2 as _local_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class DefMapping(_message.Message):
    __slots__ = ("id", "entries")
    ID_FIELD_NUMBER: _ClassVar[int]
    ENTRIES_FIELD_NUMBER: _ClassVar[int]
    id: int
    entries: _containers.RepeatedCompositeFieldContainer[IDMappingEntry]
    def __init__(self, id: _Optional[int] = ..., entries: _Optional[_Iterable[_Union[IDMappingEntry, _Mapping]]] = ...) -> None: ...

class IDMappingEntry(_message.Message):
    __slots__ = ("key", "value")
    KEY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    key: _local_pb2.Local
    value: _local_pb2.Local
    def __init__(self, key: _Optional[_Union[_local_pb2.Local, _Mapping]] = ..., value: _Optional[_Union[_local_pb2.Local, _Mapping]] = ...) -> None: ...

class IDProperty(_message.Message):
    __slots__ = ("local", "property")
    LOCAL_FIELD_NUMBER: _ClassVar[int]
    PROPERTY_FIELD_NUMBER: _ClassVar[int]
    local: _local_pb2.Local
    property: Property
    def __init__(self, local: _Optional[_Union[_local_pb2.Local, _Mapping]] = ..., property: _Optional[_Union[Property, _Mapping]] = ...) -> None: ...

class Property(_message.Message):
    __slots__ = ("key", "value")
    KEY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    key: str
    value: str
    def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
