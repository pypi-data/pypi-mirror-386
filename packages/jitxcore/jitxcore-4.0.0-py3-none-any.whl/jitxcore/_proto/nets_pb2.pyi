from jitxcore._proto import file_info_pb2 as _file_info_pb2
from jitxcore._proto import local_pb2 as _local_pb2
from jitxcore._proto import ports_pb2 as _ports_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Net(_message.Message):
    __slots__ = ("info", "name", "id", "type", "refs")
    INFO_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    REFS_FIELD_NUMBER: _ClassVar[int]
    info: _file_info_pb2.FileInfo
    name: str
    id: int
    type: _ports_pb2.PortType
    refs: _containers.RepeatedCompositeFieldContainer[_local_pb2.Local]
    def __init__(self, info: _Optional[_Union[_file_info_pb2.FileInfo, _Mapping]] = ..., name: _Optional[str] = ..., id: _Optional[int] = ..., type: _Optional[_Union[_ports_pb2.PortType, _Mapping]] = ..., refs: _Optional[_Iterable[_Union[_local_pb2.Local, _Mapping]]] = ...) -> None: ...
