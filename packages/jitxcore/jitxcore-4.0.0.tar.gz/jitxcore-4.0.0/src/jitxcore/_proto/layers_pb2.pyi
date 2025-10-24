from jitxcore._proto import shapes_pb2 as _shapes_pb2
from jitxcore._proto import enums_pb2 as _enums_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class LayerSpecifier(_message.Message):
    __slots__ = ("silkscreen", "cutout", "courtyard", "soldermask", "paste", "glue", "finish", "forbid_region", "forbid_copper", "forbid_via", "board_edge", "custom_layer")
    SILKSCREEN_FIELD_NUMBER: _ClassVar[int]
    CUTOUT_FIELD_NUMBER: _ClassVar[int]
    COURTYARD_FIELD_NUMBER: _ClassVar[int]
    SOLDERMASK_FIELD_NUMBER: _ClassVar[int]
    PASTE_FIELD_NUMBER: _ClassVar[int]
    GLUE_FIELD_NUMBER: _ClassVar[int]
    FINISH_FIELD_NUMBER: _ClassVar[int]
    FORBID_REGION_FIELD_NUMBER: _ClassVar[int]
    FORBID_COPPER_FIELD_NUMBER: _ClassVar[int]
    FORBID_VIA_FIELD_NUMBER: _ClassVar[int]
    BOARD_EDGE_FIELD_NUMBER: _ClassVar[int]
    CUSTOM_LAYER_FIELD_NUMBER: _ClassVar[int]
    silkscreen: Silkscreen
    cutout: Cutout
    courtyard: Courtyard
    soldermask: Soldermask
    paste: Paste
    glue: Glue
    finish: Finish
    forbid_region: ForbidRegion
    forbid_copper: ForbidCopper
    forbid_via: ForbidVia
    board_edge: BoardEdge
    custom_layer: CustomLayer
    def __init__(self, silkscreen: _Optional[_Union[Silkscreen, _Mapping]] = ..., cutout: _Optional[_Union[Cutout, _Mapping]] = ..., courtyard: _Optional[_Union[Courtyard, _Mapping]] = ..., soldermask: _Optional[_Union[Soldermask, _Mapping]] = ..., paste: _Optional[_Union[Paste, _Mapping]] = ..., glue: _Optional[_Union[Glue, _Mapping]] = ..., finish: _Optional[_Union[Finish, _Mapping]] = ..., forbid_region: _Optional[_Union[ForbidRegion, _Mapping]] = ..., forbid_copper: _Optional[_Union[ForbidCopper, _Mapping]] = ..., forbid_via: _Optional[_Union[ForbidVia, _Mapping]] = ..., board_edge: _Optional[_Union[BoardEdge, _Mapping]] = ..., custom_layer: _Optional[_Union[CustomLayer, _Mapping]] = ...) -> None: ...

class Silkscreen(_message.Message):
    __slots__ = ("name", "side")
    NAME_FIELD_NUMBER: _ClassVar[int]
    SIDE_FIELD_NUMBER: _ClassVar[int]
    name: str
    side: _enums_pb2.Side
    def __init__(self, name: _Optional[str] = ..., side: _Optional[_Union[_enums_pb2.Side, str]] = ...) -> None: ...

class Cutout(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Courtyard(_message.Message):
    __slots__ = ("side",)
    SIDE_FIELD_NUMBER: _ClassVar[int]
    side: _enums_pb2.Side
    def __init__(self, side: _Optional[_Union[_enums_pb2.Side, str]] = ...) -> None: ...

class Soldermask(_message.Message):
    __slots__ = ("side",)
    SIDE_FIELD_NUMBER: _ClassVar[int]
    side: _enums_pb2.Side
    def __init__(self, side: _Optional[_Union[_enums_pb2.Side, str]] = ...) -> None: ...

class Paste(_message.Message):
    __slots__ = ("side",)
    SIDE_FIELD_NUMBER: _ClassVar[int]
    side: _enums_pb2.Side
    def __init__(self, side: _Optional[_Union[_enums_pb2.Side, str]] = ...) -> None: ...

class Glue(_message.Message):
    __slots__ = ("side",)
    SIDE_FIELD_NUMBER: _ClassVar[int]
    side: _enums_pb2.Side
    def __init__(self, side: _Optional[_Union[_enums_pb2.Side, str]] = ...) -> None: ...

class Finish(_message.Message):
    __slots__ = ("side",)
    SIDE_FIELD_NUMBER: _ClassVar[int]
    side: _enums_pb2.Side
    def __init__(self, side: _Optional[_Union[_enums_pb2.Side, str]] = ...) -> None: ...

class ForbidRegion(_message.Message):
    __slots__ = ("forbid_pours", "forbid_vias", "forbid_routes", "start", "end")
    FORBID_POURS_FIELD_NUMBER: _ClassVar[int]
    FORBID_VIAS_FIELD_NUMBER: _ClassVar[int]
    FORBID_ROUTES_FIELD_NUMBER: _ClassVar[int]
    START_FIELD_NUMBER: _ClassVar[int]
    END_FIELD_NUMBER: _ClassVar[int]
    forbid_pours: bool
    forbid_vias: bool
    forbid_routes: bool
    start: LayerIndex
    end: LayerIndex
    def __init__(self, forbid_pours: bool = ..., forbid_vias: bool = ..., forbid_routes: bool = ..., start: _Optional[_Union[LayerIndex, _Mapping]] = ..., end: _Optional[_Union[LayerIndex, _Mapping]] = ...) -> None: ...

class ForbidCopper(_message.Message):
    __slots__ = ("start", "end")
    START_FIELD_NUMBER: _ClassVar[int]
    END_FIELD_NUMBER: _ClassVar[int]
    start: LayerIndex
    end: LayerIndex
    def __init__(self, start: _Optional[_Union[LayerIndex, _Mapping]] = ..., end: _Optional[_Union[LayerIndex, _Mapping]] = ...) -> None: ...

class ForbidVia(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class BoardEdge(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class CustomLayer(_message.Message):
    __slots__ = ("name", "side")
    NAME_FIELD_NUMBER: _ClassVar[int]
    SIDE_FIELD_NUMBER: _ClassVar[int]
    name: str
    side: _enums_pb2.Side
    def __init__(self, name: _Optional[str] = ..., side: _Optional[_Union[_enums_pb2.Side, str]] = ...) -> None: ...

class Layer(_message.Message):
    __slots__ = ("layer", "shape")
    LAYER_FIELD_NUMBER: _ClassVar[int]
    SHAPE_FIELD_NUMBER: _ClassVar[int]
    layer: LayerSpecifier
    shape: _shapes_pb2.Shape
    def __init__(self, layer: _Optional[_Union[LayerSpecifier, _Mapping]] = ..., shape: _Optional[_Union[_shapes_pb2.Shape, _Mapping]] = ...) -> None: ...

class LayerIndex(_message.Message):
    __slots__ = ("index", "side")
    INDEX_FIELD_NUMBER: _ClassVar[int]
    SIDE_FIELD_NUMBER: _ClassVar[int]
    index: int
    side: _enums_pb2.Side
    def __init__(self, index: _Optional[int] = ..., side: _Optional[_Union[_enums_pb2.Side, str]] = ...) -> None: ...
