from jitxcore._proto import enums_pb2 as _enums_pb2
from jitxcore._proto import layers_pb2 as _layers_pb2
from jitxcore._proto import via_patterns_pb2 as _via_patterns_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class DesignRule(_message.Message):
    __slots__ = ("name", "priority", "conditions", "effects")
    NAME_FIELD_NUMBER: _ClassVar[int]
    PRIORITY_FIELD_NUMBER: _ClassVar[int]
    CONDITIONS_FIELD_NUMBER: _ClassVar[int]
    EFFECTS_FIELD_NUMBER: _ClassVar[int]
    name: str
    priority: int
    conditions: _containers.RepeatedCompositeFieldContainer[BoolExpr]
    effects: _containers.RepeatedCompositeFieldContainer[ConstraintEffect]
    def __init__(self, name: _Optional[str] = ..., priority: _Optional[int] = ..., conditions: _Optional[_Iterable[_Union[BoolExpr, _Mapping]]] = ..., effects: _Optional[_Iterable[_Union[ConstraintEffect, _Mapping]]] = ...) -> None: ...

class ConstraintEffect(_message.Message):
    __slots__ = ("trace_width", "clearance", "stitch_via", "fence_via", "thermal_relief")
    TRACE_WIDTH_FIELD_NUMBER: _ClassVar[int]
    CLEARANCE_FIELD_NUMBER: _ClassVar[int]
    STITCH_VIA_FIELD_NUMBER: _ClassVar[int]
    FENCE_VIA_FIELD_NUMBER: _ClassVar[int]
    THERMAL_RELIEF_FIELD_NUMBER: _ClassVar[int]
    trace_width: TraceWidthEffect
    clearance: ClearanceEffect
    stitch_via: _via_patterns_pb2.StitchVia
    fence_via: _via_patterns_pb2.FenceVia
    thermal_relief: ThermalReliefEffect
    def __init__(self, trace_width: _Optional[_Union[TraceWidthEffect, _Mapping]] = ..., clearance: _Optional[_Union[ClearanceEffect, _Mapping]] = ..., stitch_via: _Optional[_Union[_via_patterns_pb2.StitchVia, _Mapping]] = ..., fence_via: _Optional[_Union[_via_patterns_pb2.FenceVia, _Mapping]] = ..., thermal_relief: _Optional[_Union[ThermalReliefEffect, _Mapping]] = ...) -> None: ...

class TraceWidthEffect(_message.Message):
    __slots__ = ("width",)
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    width: float
    def __init__(self, width: _Optional[float] = ...) -> None: ...

class ClearanceEffect(_message.Message):
    __slots__ = ("clearance",)
    CLEARANCE_FIELD_NUMBER: _ClassVar[int]
    clearance: float
    def __init__(self, clearance: _Optional[float] = ...) -> None: ...

class ThermalReliefEffect(_message.Message):
    __slots__ = ("gap_distance", "spoke_width", "num_spokes")
    GAP_DISTANCE_FIELD_NUMBER: _ClassVar[int]
    SPOKE_WIDTH_FIELD_NUMBER: _ClassVar[int]
    NUM_SPOKES_FIELD_NUMBER: _ClassVar[int]
    gap_distance: float
    spoke_width: float
    num_spokes: int
    def __init__(self, gap_distance: _Optional[float] = ..., spoke_width: _Optional[float] = ..., num_spokes: _Optional[int] = ...) -> None: ...

class Tag(_message.Message):
    __slots__ = ("builtin", "user")
    BUILTIN_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    builtin: BuiltinTag
    user: UserTag
    def __init__(self, builtin: _Optional[_Union[BuiltinTag, _Mapping]] = ..., user: _Optional[_Union[UserTag, _Mapping]] = ...) -> None: ...

class BuiltinTag(_message.Message):
    __slots__ = ("layer", "object")
    LAYER_FIELD_NUMBER: _ClassVar[int]
    OBJECT_FIELD_NUMBER: _ClassVar[int]
    layer: OnLayerTag
    object: ObjectTag
    def __init__(self, layer: _Optional[_Union[OnLayerTag, _Mapping]] = ..., object: _Optional[_Union[ObjectTag, _Mapping]] = ...) -> None: ...

class UserTag(_message.Message):
    __slots__ = ("name", "parents")
    NAME_FIELD_NUMBER: _ClassVar[int]
    PARENTS_FIELD_NUMBER: _ClassVar[int]
    name: str
    parents: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, name: _Optional[str] = ..., parents: _Optional[_Iterable[str]] = ...) -> None: ...

class OnLayerTag(_message.Message):
    __slots__ = ("layer",)
    LAYER_FIELD_NUMBER: _ClassVar[int]
    layer: _layers_pb2.LayerIndex
    def __init__(self, layer: _Optional[_Union[_layers_pb2.LayerIndex, _Mapping]] = ...) -> None: ...

class ObjectTag(_message.Message):
    __slots__ = ("type",)
    TYPE_FIELD_NUMBER: _ClassVar[int]
    type: _enums_pb2.ObjectTagType
    def __init__(self, type: _Optional[_Union[_enums_pb2.ObjectTagType, str]] = ...) -> None: ...

class BoolExpr(_message.Message):
    __slots__ = ("true_expr", "atom_expr", "not_expr", "or_expr", "and_expr")
    TRUE_EXPR_FIELD_NUMBER: _ClassVar[int]
    ATOM_EXPR_FIELD_NUMBER: _ClassVar[int]
    NOT_EXPR_FIELD_NUMBER: _ClassVar[int]
    OR_EXPR_FIELD_NUMBER: _ClassVar[int]
    AND_EXPR_FIELD_NUMBER: _ClassVar[int]
    true_expr: TrueExpr
    atom_expr: AtomExpr
    not_expr: NotExpr
    or_expr: OrExpr
    and_expr: AndExpr
    def __init__(self, true_expr: _Optional[_Union[TrueExpr, _Mapping]] = ..., atom_expr: _Optional[_Union[AtomExpr, _Mapping]] = ..., not_expr: _Optional[_Union[NotExpr, _Mapping]] = ..., or_expr: _Optional[_Union[OrExpr, _Mapping]] = ..., and_expr: _Optional[_Union[AndExpr, _Mapping]] = ...) -> None: ...

class TrueExpr(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class AtomExpr(_message.Message):
    __slots__ = ("atom",)
    ATOM_FIELD_NUMBER: _ClassVar[int]
    atom: Tag
    def __init__(self, atom: _Optional[_Union[Tag, _Mapping]] = ...) -> None: ...

class NotExpr(_message.Message):
    __slots__ = ("expr",)
    EXPR_FIELD_NUMBER: _ClassVar[int]
    expr: BoolExpr
    def __init__(self, expr: _Optional[_Union[BoolExpr, _Mapping]] = ...) -> None: ...

class OrExpr(_message.Message):
    __slots__ = ("left", "right")
    LEFT_FIELD_NUMBER: _ClassVar[int]
    RIGHT_FIELD_NUMBER: _ClassVar[int]
    left: BoolExpr
    right: BoolExpr
    def __init__(self, left: _Optional[_Union[BoolExpr, _Mapping]] = ..., right: _Optional[_Union[BoolExpr, _Mapping]] = ...) -> None: ...

class AndExpr(_message.Message):
    __slots__ = ("left", "right")
    LEFT_FIELD_NUMBER: _ClassVar[int]
    RIGHT_FIELD_NUMBER: _ClassVar[int]
    left: BoolExpr
    right: BoolExpr
    def __init__(self, left: _Optional[_Union[BoolExpr, _Mapping]] = ..., right: _Optional[_Union[BoolExpr, _Mapping]] = ...) -> None: ...
