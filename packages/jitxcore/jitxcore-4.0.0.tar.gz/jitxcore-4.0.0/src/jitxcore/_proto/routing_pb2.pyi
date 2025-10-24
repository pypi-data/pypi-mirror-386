from jitxcore._proto import file_info_pb2 as _file_info_pb2
from jitxcore._proto import layers_pb2 as _layers_pb2
from jitxcore._proto import routing_structures_pb2 as _routing_structures_pb2
from jitxcore._proto import via_patterns_pb2 as _via_patterns_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Routing(_message.Message):
    __slots__ = ("info", "id", "name", "layers")
    INFO_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    LAYERS_FIELD_NUMBER: _ClassVar[int]
    info: _file_info_pb2.FileInfo
    id: int
    name: str
    layers: _containers.RepeatedCompositeFieldContainer[RoutingLayer]
    def __init__(self, info: _Optional[_Union[_file_info_pb2.FileInfo, _Mapping]] = ..., id: _Optional[int] = ..., name: _Optional[str] = ..., layers: _Optional[_Iterable[_Union[RoutingLayer, _Mapping]]] = ...) -> None: ...

class RoutingLayer(_message.Message):
    __slots__ = ("layer", "trace_width", "velocity", "insertion_loss", "clearance", "neck_down", "ref_layers", "add_geoms", "fence")
    LAYER_FIELD_NUMBER: _ClassVar[int]
    TRACE_WIDTH_FIELD_NUMBER: _ClassVar[int]
    VELOCITY_FIELD_NUMBER: _ClassVar[int]
    INSERTION_LOSS_FIELD_NUMBER: _ClassVar[int]
    CLEARANCE_FIELD_NUMBER: _ClassVar[int]
    NECK_DOWN_FIELD_NUMBER: _ClassVar[int]
    REF_LAYERS_FIELD_NUMBER: _ClassVar[int]
    ADD_GEOMS_FIELD_NUMBER: _ClassVar[int]
    FENCE_FIELD_NUMBER: _ClassVar[int]
    layer: _layers_pb2.LayerIndex
    trace_width: float
    velocity: float
    insertion_loss: float
    clearance: float
    neck_down: NeckDown
    ref_layers: _containers.RepeatedCompositeFieldContainer[_routing_structures_pb2.RefLayer]
    add_geoms: _containers.RepeatedCompositeFieldContainer[_routing_structures_pb2.AddGeom]
    fence: _via_patterns_pb2.FenceVia
    def __init__(self, layer: _Optional[_Union[_layers_pb2.LayerIndex, _Mapping]] = ..., trace_width: _Optional[float] = ..., velocity: _Optional[float] = ..., insertion_loss: _Optional[float] = ..., clearance: _Optional[float] = ..., neck_down: _Optional[_Union[NeckDown, _Mapping]] = ..., ref_layers: _Optional[_Iterable[_Union[_routing_structures_pb2.RefLayer, _Mapping]]] = ..., add_geoms: _Optional[_Iterable[_Union[_routing_structures_pb2.AddGeom, _Mapping]]] = ..., fence: _Optional[_Union[_via_patterns_pb2.FenceVia, _Mapping]] = ...) -> None: ...

class NeckDown(_message.Message):
    __slots__ = ("trace_width", "clearance", "insertion_loss", "velocity")
    TRACE_WIDTH_FIELD_NUMBER: _ClassVar[int]
    CLEARANCE_FIELD_NUMBER: _ClassVar[int]
    INSERTION_LOSS_FIELD_NUMBER: _ClassVar[int]
    VELOCITY_FIELD_NUMBER: _ClassVar[int]
    trace_width: float
    clearance: float
    insertion_loss: float
    velocity: float
    def __init__(self, trace_width: _Optional[float] = ..., clearance: _Optional[float] = ..., insertion_loss: _Optional[float] = ..., velocity: _Optional[float] = ...) -> None: ...
