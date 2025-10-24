from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Port(_message.Message):
    __slots__ = ("name", "id", "type")
    NAME_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    name: str
    id: int
    type: PortType
    def __init__(self, name: _Optional[str] = ..., id: _Optional[int] = ..., type: _Optional[_Union[PortType, _Mapping]] = ...) -> None: ...

class PortType(_message.Message):
    __slots__ = ("single", "bundle", "array")
    SINGLE_FIELD_NUMBER: _ClassVar[int]
    BUNDLE_FIELD_NUMBER: _ClassVar[int]
    ARRAY_FIELD_NUMBER: _ClassVar[int]
    single: PortSingle
    bundle: PortBundle
    array: PortArray
    def __init__(self, single: _Optional[_Union[PortSingle, _Mapping]] = ..., bundle: _Optional[_Union[PortBundle, _Mapping]] = ..., array: _Optional[_Union[PortArray, _Mapping]] = ...) -> None: ...

class PortSingle(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class PortBundle(_message.Message):
    __slots__ = ("bundle",)
    BUNDLE_FIELD_NUMBER: _ClassVar[int]
    bundle: int
    def __init__(self, bundle: _Optional[int] = ...) -> None: ...

class PortArrayEntry(_message.Message):
    __slots__ = ("index", "id")
    INDEX_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    index: int
    id: int
    def __init__(self, index: _Optional[int] = ..., id: _Optional[int] = ...) -> None: ...

class PortArray(_message.Message):
    __slots__ = ("type", "entries")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    ENTRIES_FIELD_NUMBER: _ClassVar[int]
    type: PortType
    entries: _containers.RepeatedCompositeFieldContainer[PortArrayEntry]
    def __init__(self, type: _Optional[_Union[PortType, _Mapping]] = ..., entries: _Optional[_Iterable[_Union[PortArrayEntry, _Mapping]]] = ...) -> None: ...
