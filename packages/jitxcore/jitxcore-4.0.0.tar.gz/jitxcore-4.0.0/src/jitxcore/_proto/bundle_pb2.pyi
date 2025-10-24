from jitxcore._proto import file_info_pb2 as _file_info_pb2
from jitxcore._proto import mapping_pb2 as _mapping_pb2
from jitxcore._proto import ports_pb2 as _ports_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Bundle(_message.Message):
    __slots__ = ("info", "id", "name", "ports", "differential_pairs")
    INFO_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    PORTS_FIELD_NUMBER: _ClassVar[int]
    DIFFERENTIAL_PAIRS_FIELD_NUMBER: _ClassVar[int]
    info: _file_info_pb2.FileInfo
    id: int
    name: str
    ports: _containers.RepeatedCompositeFieldContainer[_ports_pb2.Port]
    differential_pairs: _containers.RepeatedCompositeFieldContainer[_mapping_pb2.IDMappingEntry]
    def __init__(self, info: _Optional[_Union[_file_info_pb2.FileInfo, _Mapping]] = ..., id: _Optional[int] = ..., name: _Optional[str] = ..., ports: _Optional[_Iterable[_Union[_ports_pb2.Port, _Mapping]]] = ..., differential_pairs: _Optional[_Iterable[_Union[_mapping_pb2.IDMappingEntry, _Mapping]]] = ...) -> None: ...
