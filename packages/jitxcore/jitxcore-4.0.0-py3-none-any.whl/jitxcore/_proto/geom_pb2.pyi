from jitxcore._proto import file_info_pb2 as _file_info_pb2
from jitxcore._proto import layers_pb2 as _layers_pb2
from jitxcore._proto import mapping_pb2 as _mapping_pb2
from jitxcore._proto import shapes_pb2 as _shapes_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Geom(_message.Message):
    __slots__ = ("copper", "pour", "via")
    COPPER_FIELD_NUMBER: _ClassVar[int]
    POUR_FIELD_NUMBER: _ClassVar[int]
    VIA_FIELD_NUMBER: _ClassVar[int]
    copper: Copper
    pour: Pour
    via: ViaInstance
    def __init__(self, copper: _Optional[_Union[Copper, _Mapping]] = ..., pour: _Optional[_Union[Pour, _Mapping]] = ..., via: _Optional[_Union[ViaInstance, _Mapping]] = ...) -> None: ...

class Copper(_message.Message):
    __slots__ = ("info", "layer", "shape")
    INFO_FIELD_NUMBER: _ClassVar[int]
    LAYER_FIELD_NUMBER: _ClassVar[int]
    SHAPE_FIELD_NUMBER: _ClassVar[int]
    info: _file_info_pb2.FileInfo
    layer: _layers_pb2.LayerIndex
    shape: _shapes_pb2.Shape
    def __init__(self, info: _Optional[_Union[_file_info_pb2.FileInfo, _Mapping]] = ..., layer: _Optional[_Union[_layers_pb2.LayerIndex, _Mapping]] = ..., shape: _Optional[_Union[_shapes_pb2.Shape, _Mapping]] = ...) -> None: ...

class Pour(_message.Message):
    __slots__ = ("info", "layer", "shape", "isolate", "rank", "orphans")
    INFO_FIELD_NUMBER: _ClassVar[int]
    LAYER_FIELD_NUMBER: _ClassVar[int]
    SHAPE_FIELD_NUMBER: _ClassVar[int]
    ISOLATE_FIELD_NUMBER: _ClassVar[int]
    RANK_FIELD_NUMBER: _ClassVar[int]
    ORPHANS_FIELD_NUMBER: _ClassVar[int]
    info: _file_info_pb2.FileInfo
    layer: _layers_pb2.LayerIndex
    shape: _shapes_pb2.Shape
    isolate: float
    rank: int
    orphans: bool
    def __init__(self, info: _Optional[_Union[_file_info_pb2.FileInfo, _Mapping]] = ..., layer: _Optional[_Union[_layers_pb2.LayerIndex, _Mapping]] = ..., shape: _Optional[_Union[_shapes_pb2.Shape, _Mapping]] = ..., isolate: _Optional[float] = ..., rank: _Optional[int] = ..., orphans: bool = ...) -> None: ...

class ViaInstance(_message.Message):
    __slots__ = ("info", "via", "point", "properties")
    INFO_FIELD_NUMBER: _ClassVar[int]
    VIA_FIELD_NUMBER: _ClassVar[int]
    POINT_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    info: _file_info_pb2.FileInfo
    via: str
    point: _shapes_pb2.Point
    properties: _containers.RepeatedCompositeFieldContainer[_mapping_pb2.Property]
    def __init__(self, info: _Optional[_Union[_file_info_pb2.FileInfo, _Mapping]] = ..., via: _Optional[str] = ..., point: _Optional[_Union[_shapes_pb2.Point, _Mapping]] = ..., properties: _Optional[_Iterable[_Union[_mapping_pb2.Property, _Mapping]]] = ...) -> None: ...
