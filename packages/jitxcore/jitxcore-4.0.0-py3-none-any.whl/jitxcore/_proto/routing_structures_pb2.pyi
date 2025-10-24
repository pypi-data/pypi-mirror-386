from jitxcore._proto import file_info_pb2 as _file_info_pb2
from jitxcore._proto import layers_pb2 as _layers_pb2
from jitxcore._proto import local_pb2 as _local_pb2
from jitxcore._proto import mapping_pb2 as _mapping_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class RefLayer(_message.Message):
    __slots__ = ("layer", "desired_width", "required_width")
    LAYER_FIELD_NUMBER: _ClassVar[int]
    DESIRED_WIDTH_FIELD_NUMBER: _ClassVar[int]
    REQUIRED_WIDTH_FIELD_NUMBER: _ClassVar[int]
    layer: _layers_pb2.LayerIndex
    desired_width: float
    required_width: float
    def __init__(self, layer: _Optional[_Union[_layers_pb2.LayerIndex, _Mapping]] = ..., desired_width: _Optional[float] = ..., required_width: _Optional[float] = ...) -> None: ...

class AddGeom(_message.Message):
    __slots__ = ("layer", "desired_width")
    LAYER_FIELD_NUMBER: _ClassVar[int]
    DESIRED_WIDTH_FIELD_NUMBER: _ClassVar[int]
    layer: _layers_pb2.LayerSpecifier
    desired_width: float
    def __init__(self, layer: _Optional[_Union[_layers_pb2.LayerSpecifier, _Mapping]] = ..., desired_width: _Optional[float] = ...) -> None: ...

class RefLayerNet(_message.Message):
    __slots__ = ("layer", "ref")
    LAYER_FIELD_NUMBER: _ClassVar[int]
    REF_FIELD_NUMBER: _ClassVar[int]
    layer: _layers_pb2.LayerIndex
    ref: _local_pb2.Local
    def __init__(self, layer: _Optional[_Union[_layers_pb2.LayerIndex, _Mapping]] = ..., ref: _Optional[_Union[_local_pb2.Local, _Mapping]] = ...) -> None: ...

class Structure(_message.Message):
    __slots__ = ("info", "path", "ref_layer_nets", "via_fence_nets", "routing_structure")
    INFO_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    REF_LAYER_NETS_FIELD_NUMBER: _ClassVar[int]
    VIA_FENCE_NETS_FIELD_NUMBER: _ClassVar[int]
    ROUTING_STRUCTURE_FIELD_NUMBER: _ClassVar[int]
    info: _file_info_pb2.FileInfo
    path: _mapping_pb2.IDMappingEntry
    ref_layer_nets: _containers.RepeatedCompositeFieldContainer[RefLayerNet]
    via_fence_nets: _containers.RepeatedCompositeFieldContainer[RefLayerNet]
    routing_structure: int
    def __init__(self, info: _Optional[_Union[_file_info_pb2.FileInfo, _Mapping]] = ..., path: _Optional[_Union[_mapping_pb2.IDMappingEntry, _Mapping]] = ..., ref_layer_nets: _Optional[_Iterable[_Union[RefLayerNet, _Mapping]]] = ..., via_fence_nets: _Optional[_Iterable[_Union[RefLayerNet, _Mapping]]] = ..., routing_structure: _Optional[int] = ...) -> None: ...

class DifferentialStructure(_message.Message):
    __slots__ = ("info", "path1", "path2", "ref_layer_nets", "via_fence_nets", "differential_routing_structure")
    INFO_FIELD_NUMBER: _ClassVar[int]
    PATH1_FIELD_NUMBER: _ClassVar[int]
    PATH2_FIELD_NUMBER: _ClassVar[int]
    REF_LAYER_NETS_FIELD_NUMBER: _ClassVar[int]
    VIA_FENCE_NETS_FIELD_NUMBER: _ClassVar[int]
    DIFFERENTIAL_ROUTING_STRUCTURE_FIELD_NUMBER: _ClassVar[int]
    info: _file_info_pb2.FileInfo
    path1: _mapping_pb2.IDMappingEntry
    path2: _mapping_pb2.IDMappingEntry
    ref_layer_nets: _containers.RepeatedCompositeFieldContainer[RefLayerNet]
    via_fence_nets: _containers.RepeatedCompositeFieldContainer[RefLayerNet]
    differential_routing_structure: int
    def __init__(self, info: _Optional[_Union[_file_info_pb2.FileInfo, _Mapping]] = ..., path1: _Optional[_Union[_mapping_pb2.IDMappingEntry, _Mapping]] = ..., path2: _Optional[_Union[_mapping_pb2.IDMappingEntry, _Mapping]] = ..., ref_layer_nets: _Optional[_Iterable[_Union[RefLayerNet, _Mapping]]] = ..., via_fence_nets: _Optional[_Iterable[_Union[RefLayerNet, _Mapping]]] = ..., differential_routing_structure: _Optional[int] = ...) -> None: ...
