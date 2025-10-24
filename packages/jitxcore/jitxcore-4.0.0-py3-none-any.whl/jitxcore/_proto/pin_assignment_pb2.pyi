from jitxcore._proto import local_pb2 as _local_pb2
from jitxcore._proto import mapping_pb2 as _mapping_pb2
from jitxcore._proto import ports_pb2 as _ports_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Support(_message.Message):
    __slots__ = ("bundle", "options")
    BUNDLE_FIELD_NUMBER: _ClassVar[int]
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    bundle: int
    options: _containers.RepeatedCompositeFieldContainer[Option]
    def __init__(self, bundle: _Optional[int] = ..., options: _Optional[_Iterable[_Union[Option, _Mapping]]] = ...) -> None: ...

class Option(_message.Message):
    __slots__ = ("requires", "restricts", "properties", "entries")
    REQUIRES_FIELD_NUMBER: _ClassVar[int]
    RESTRICTS_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    ENTRIES_FIELD_NUMBER: _ClassVar[int]
    requires: _containers.RepeatedCompositeFieldContainer[Require]
    restricts: _containers.RepeatedCompositeFieldContainer[Restrict]
    properties: _containers.RepeatedCompositeFieldContainer[_mapping_pb2.Property]
    entries: _containers.RepeatedCompositeFieldContainer[_mapping_pb2.IDMappingEntry]
    def __init__(self, requires: _Optional[_Iterable[_Union[Require, _Mapping]]] = ..., restricts: _Optional[_Iterable[_Union[Restrict, _Mapping]]] = ..., properties: _Optional[_Iterable[_Union[_mapping_pb2.Property, _Mapping]]] = ..., entries: _Optional[_Iterable[_Union[_mapping_pb2.IDMappingEntry, _Mapping]]] = ...) -> None: ...

class Require(_message.Message):
    __slots__ = ("port", "instance")
    PORT_FIELD_NUMBER: _ClassVar[int]
    INSTANCE_FIELD_NUMBER: _ClassVar[int]
    port: _ports_pb2.Port
    instance: _local_pb2.Local
    def __init__(self, port: _Optional[_Union[_ports_pb2.Port, _Mapping]] = ..., instance: _Optional[_Union[_local_pb2.Local, _Mapping]] = ...) -> None: ...

class Restrict(_message.Message):
    __slots__ = ("index", "port", "permit")
    INDEX_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    PERMIT_FIELD_NUMBER: _ClassVar[int]
    index: int
    port: _local_pb2.Local
    permit: bool
    def __init__(self, index: _Optional[int] = ..., port: _Optional[_Union[_local_pb2.Local, _Mapping]] = ..., permit: bool = ...) -> None: ...

class RestrictEntry(_message.Message):
    __slots__ = ("affected",)
    AFFECTED_FIELD_NUMBER: _ClassVar[int]
    affected: _containers.RepeatedCompositeFieldContainer[_local_pb2.Local]
    def __init__(self, affected: _Optional[_Iterable[_Union[_local_pb2.Local, _Mapping]]] = ...) -> None: ...
