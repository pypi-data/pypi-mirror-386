from jitxcore._proto import enums_pb2 as _enums_pb2
from jitxcore._proto import file_info_pb2 as _file_info_pb2
from jitxcore._proto import shapes_pb2 as _shapes_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Symbol(_message.Message):
    __slots__ = ("info", "id", "name", "layers", "pins", "symbol_orientation", "altium_substitution")
    INFO_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    LAYERS_FIELD_NUMBER: _ClassVar[int]
    PINS_FIELD_NUMBER: _ClassVar[int]
    SYMBOL_ORIENTATION_FIELD_NUMBER: _ClassVar[int]
    ALTIUM_SUBSTITUTION_FIELD_NUMBER: _ClassVar[int]
    info: _file_info_pb2.FileInfo
    id: int
    name: str
    layers: _containers.RepeatedCompositeFieldContainer[SymbolLayer]
    pins: _containers.RepeatedCompositeFieldContainer[SymbolPin]
    symbol_orientation: SymbolOrientation
    altium_substitution: int
    def __init__(self, info: _Optional[_Union[_file_info_pb2.FileInfo, _Mapping]] = ..., id: _Optional[int] = ..., name: _Optional[str] = ..., layers: _Optional[_Iterable[_Union[SymbolLayer, _Mapping]]] = ..., pins: _Optional[_Iterable[_Union[SymbolPin, _Mapping]]] = ..., symbol_orientation: _Optional[_Union[SymbolOrientation, _Mapping]] = ..., altium_substitution: _Optional[int] = ...) -> None: ...

class SymbolLayer(_message.Message):
    __slots__ = ("name", "shape")
    NAME_FIELD_NUMBER: _ClassVar[int]
    SHAPE_FIELD_NUMBER: _ClassVar[int]
    name: str
    shape: _shapes_pb2.Shape
    def __init__(self, name: _Optional[str] = ..., shape: _Optional[_Union[_shapes_pb2.Shape, _Mapping]] = ...) -> None: ...

class SymbolPin(_message.Message):
    __slots__ = ("id", "ref", "point", "properties")
    ID_FIELD_NUMBER: _ClassVar[int]
    REF_FIELD_NUMBER: _ClassVar[int]
    POINT_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    id: int
    ref: str
    point: _shapes_pb2.Point
    properties: PinProperties
    def __init__(self, id: _Optional[int] = ..., ref: _Optional[str] = ..., point: _Optional[_Union[_shapes_pb2.Point, _Mapping]] = ..., properties: _Optional[_Union[PinProperties, _Mapping]] = ...) -> None: ...

class PinProperties(_message.Message):
    __slots__ = ("length", "dir", "number_size", "name_size")
    LENGTH_FIELD_NUMBER: _ClassVar[int]
    DIR_FIELD_NUMBER: _ClassVar[int]
    NUMBER_SIZE_FIELD_NUMBER: _ClassVar[int]
    NAME_SIZE_FIELD_NUMBER: _ClassVar[int]
    length: float
    dir: _enums_pb2.Dir
    number_size: float
    name_size: float
    def __init__(self, length: _Optional[float] = ..., dir: _Optional[_Union[_enums_pb2.Dir, str]] = ..., number_size: _Optional[float] = ..., name_size: _Optional[float] = ...) -> None: ...

class SymbolOrientation(_message.Message):
    __slots__ = ("any_rotation", "prefer_rotation")
    ANY_ROTATION_FIELD_NUMBER: _ClassVar[int]
    PREFER_ROTATION_FIELD_NUMBER: _ClassVar[int]
    any_rotation: AnyRotation
    prefer_rotation: PreferRotation
    def __init__(self, any_rotation: _Optional[_Union[AnyRotation, _Mapping]] = ..., prefer_rotation: _Optional[_Union[PreferRotation, _Mapping]] = ...) -> None: ...

class AnyRotation(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class PreferRotation(_message.Message):
    __slots__ = ("rotations",)
    ROTATIONS_FIELD_NUMBER: _ClassVar[int]
    rotations: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, rotations: _Optional[_Iterable[int]] = ...) -> None: ...
