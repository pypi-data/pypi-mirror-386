from jitxcore._proto import shapes_pb2 as _shapes_pb2
from jitxcore._proto import layers_pb2 as _layers_pb2
from jitxcore._proto import file_info_pb2 as _file_info_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Board(_message.Message):
    __slots__ = ("info", "id", "name", "boundary", "signal_boundary", "stackup", "layers", "vias")
    INFO_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    BOUNDARY_FIELD_NUMBER: _ClassVar[int]
    SIGNAL_BOUNDARY_FIELD_NUMBER: _ClassVar[int]
    STACKUP_FIELD_NUMBER: _ClassVar[int]
    LAYERS_FIELD_NUMBER: _ClassVar[int]
    VIAS_FIELD_NUMBER: _ClassVar[int]
    info: _file_info_pb2.FileInfo
    id: int
    name: str
    boundary: _shapes_pb2.Shape
    signal_boundary: _shapes_pb2.Shape
    stackup: int
    layers: _containers.RepeatedCompositeFieldContainer[_layers_pb2.Layer]
    vias: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, info: _Optional[_Union[_file_info_pb2.FileInfo, _Mapping]] = ..., id: _Optional[int] = ..., name: _Optional[str] = ..., boundary: _Optional[_Union[_shapes_pb2.Shape, _Mapping]] = ..., signal_boundary: _Optional[_Union[_shapes_pb2.Shape, _Mapping]] = ..., stackup: _Optional[int] = ..., layers: _Optional[_Iterable[_Union[_layers_pb2.Layer, _Mapping]]] = ..., vias: _Optional[_Iterable[int]] = ...) -> None: ...
