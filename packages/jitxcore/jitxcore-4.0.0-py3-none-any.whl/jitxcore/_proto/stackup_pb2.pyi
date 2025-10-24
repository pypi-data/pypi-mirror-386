from jitxcore._proto import file_info_pb2 as _file_info_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Stackup(_message.Message):
    __slots__ = ("info", "id", "name", "layers")
    INFO_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    LAYERS_FIELD_NUMBER: _ClassVar[int]
    info: _file_info_pb2.FileInfo
    id: int
    name: str
    layers: _containers.RepeatedCompositeFieldContainer[StackupLayer]
    def __init__(self, info: _Optional[_Union[_file_info_pb2.FileInfo, _Mapping]] = ..., id: _Optional[int] = ..., name: _Optional[str] = ..., layers: _Optional[_Iterable[_Union[StackupLayer, _Mapping]]] = ...) -> None: ...

class StackupLayer(_message.Message):
    __slots__ = ("name", "thickness", "material")
    NAME_FIELD_NUMBER: _ClassVar[int]
    THICKNESS_FIELD_NUMBER: _ClassVar[int]
    MATERIAL_FIELD_NUMBER: _ClassVar[int]
    name: str
    thickness: float
    material: int
    def __init__(self, name: _Optional[str] = ..., thickness: _Optional[float] = ..., material: _Optional[int] = ...) -> None: ...
