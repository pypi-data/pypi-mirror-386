from jitxcore._proto import enums_pb2 as _enums_pb2
from jitxcore._proto import file_info_pb2 as _file_info_pb2
from jitxcore._proto import layers_pb2 as _layers_pb2
from jitxcore._proto import shapes_pb2 as _shapes_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Pad(_message.Message):
    __slots__ = ("info", "id", "name", "type", "shape", "nfp_shape", "shapes", "edge", "layers")
    INFO_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    SHAPE_FIELD_NUMBER: _ClassVar[int]
    NFP_SHAPE_FIELD_NUMBER: _ClassVar[int]
    SHAPES_FIELD_NUMBER: _ClassVar[int]
    EDGE_FIELD_NUMBER: _ClassVar[int]
    LAYERS_FIELD_NUMBER: _ClassVar[int]
    info: _file_info_pb2.FileInfo
    id: int
    name: str
    type: _enums_pb2.PadType
    shape: _shapes_pb2.Shape
    nfp_shape: _shapes_pb2.Shape
    shapes: _containers.RepeatedCompositeFieldContainer[PadShape]
    edge: bool
    layers: _containers.RepeatedCompositeFieldContainer[_layers_pb2.Layer]
    def __init__(self, info: _Optional[_Union[_file_info_pb2.FileInfo, _Mapping]] = ..., id: _Optional[int] = ..., name: _Optional[str] = ..., type: _Optional[_Union[_enums_pb2.PadType, str]] = ..., shape: _Optional[_Union[_shapes_pb2.Shape, _Mapping]] = ..., nfp_shape: _Optional[_Union[_shapes_pb2.Shape, _Mapping]] = ..., shapes: _Optional[_Iterable[_Union[PadShape, _Mapping]]] = ..., edge: bool = ..., layers: _Optional[_Iterable[_Union[_layers_pb2.Layer, _Mapping]]] = ...) -> None: ...

class PadShape(_message.Message):
    __slots__ = ("shape", "nfp", "layers")
    SHAPE_FIELD_NUMBER: _ClassVar[int]
    NFP_FIELD_NUMBER: _ClassVar[int]
    LAYERS_FIELD_NUMBER: _ClassVar[int]
    shape: _shapes_pb2.Shape
    nfp: _shapes_pb2.Shape
    layers: _containers.RepeatedCompositeFieldContainer[_layers_pb2.LayerIndex]
    def __init__(self, shape: _Optional[_Union[_shapes_pb2.Shape, _Mapping]] = ..., nfp: _Optional[_Union[_shapes_pb2.Shape, _Mapping]] = ..., layers: _Optional[_Iterable[_Union[_layers_pb2.LayerIndex, _Mapping]]] = ...) -> None: ...
