from jitxcore._proto import enums_pb2 as _enums_pb2
from jitxcore._proto import file_info_pb2 as _file_info_pb2
from jitxcore._proto import geom_pb2 as _geom_pb2
from jitxcore._proto import layers_pb2 as _layers_pb2
from jitxcore._proto import mapping_pb2 as _mapping_pb2
from jitxcore._proto import shapes_pb2 as _shapes_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Landpattern(_message.Message):
    __slots__ = ("info", "id", "name", "layers", "pads", "geoms", "model3ds")
    INFO_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    LAYERS_FIELD_NUMBER: _ClassVar[int]
    PADS_FIELD_NUMBER: _ClassVar[int]
    GEOMS_FIELD_NUMBER: _ClassVar[int]
    MODEL3DS_FIELD_NUMBER: _ClassVar[int]
    info: _file_info_pb2.FileInfo
    id: int
    name: str
    layers: _containers.RepeatedCompositeFieldContainer[_layers_pb2.Layer]
    pads: _containers.RepeatedCompositeFieldContainer[LandpatternPad]
    geoms: _containers.RepeatedCompositeFieldContainer[_geom_pb2.Geom]
    model3ds: _containers.RepeatedCompositeFieldContainer[Model3D]
    def __init__(self, info: _Optional[_Union[_file_info_pb2.FileInfo, _Mapping]] = ..., id: _Optional[int] = ..., name: _Optional[str] = ..., layers: _Optional[_Iterable[_Union[_layers_pb2.Layer, _Mapping]]] = ..., pads: _Optional[_Iterable[_Union[LandpatternPad, _Mapping]]] = ..., geoms: _Optional[_Iterable[_Union[_geom_pb2.Geom, _Mapping]]] = ..., model3ds: _Optional[_Iterable[_Union[Model3D, _Mapping]]] = ...) -> None: ...

class LandpatternPad(_message.Message):
    __slots__ = ("info", "id", "ref", "pad", "pose", "side")
    INFO_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    REF_FIELD_NUMBER: _ClassVar[int]
    PAD_FIELD_NUMBER: _ClassVar[int]
    POSE_FIELD_NUMBER: _ClassVar[int]
    SIDE_FIELD_NUMBER: _ClassVar[int]
    info: _file_info_pb2.FileInfo
    id: int
    ref: str
    pad: int
    pose: _shapes_pb2.Pose
    side: _enums_pb2.Side
    def __init__(self, info: _Optional[_Union[_file_info_pb2.FileInfo, _Mapping]] = ..., id: _Optional[int] = ..., ref: _Optional[str] = ..., pad: _Optional[int] = ..., pose: _Optional[_Union[_shapes_pb2.Pose, _Mapping]] = ..., side: _Optional[_Union[_enums_pb2.Side, str]] = ...) -> None: ...

class Model3D(_message.Message):
    __slots__ = ("filename", "position", "scale", "rotation", "properties")
    FILENAME_FIELD_NUMBER: _ClassVar[int]
    POSITION_FIELD_NUMBER: _ClassVar[int]
    SCALE_FIELD_NUMBER: _ClassVar[int]
    ROTATION_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    filename: str
    position: Vec3D
    scale: Vec3D
    rotation: Vec3D
    properties: _containers.RepeatedCompositeFieldContainer[_mapping_pb2.Property]
    def __init__(self, filename: _Optional[str] = ..., position: _Optional[_Union[Vec3D, _Mapping]] = ..., scale: _Optional[_Union[Vec3D, _Mapping]] = ..., rotation: _Optional[_Union[Vec3D, _Mapping]] = ..., properties: _Optional[_Iterable[_Union[_mapping_pb2.Property, _Mapping]]] = ...) -> None: ...

class Vec3D(_message.Message):
    __slots__ = ("x", "y", "z")
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    Z_FIELD_NUMBER: _ClassVar[int]
    x: float
    y: float
    z: float
    def __init__(self, x: _Optional[float] = ..., y: _Optional[float] = ..., z: _Optional[float] = ...) -> None: ...
