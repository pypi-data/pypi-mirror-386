from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from typing import ClassVar as _ClassVar

DESCRIPTOR: _descriptor.FileDescriptor

class Dir(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    UP: _ClassVar[Dir]
    DOWN: _ClassVar[Dir]
    LEFT: _ClassVar[Dir]
    RIGHT: _ClassVar[Dir]

class Side(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    TOP: _ClassVar[Side]
    BOTTOM: _ClassVar[Side]

class Anchor(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    N: _ClassVar[Anchor]
    S: _ClassVar[Anchor]
    E: _ClassVar[Anchor]
    W: _ClassVar[Anchor]
    NE: _ClassVar[Anchor]
    SE: _ClassVar[Anchor]
    SW: _ClassVar[Anchor]
    NW: _ClassVar[Anchor]
    C: _ClassVar[Anchor]

class PadType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SMD: _ClassVar[PadType]
    TH: _ClassVar[PadType]

class MaterialType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    CONDUCTOR: _ClassVar[MaterialType]
    DIELECTRIC: _ClassVar[MaterialType]

class ViaDrillType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    MECHANICAL_DRILL: _ClassVar[ViaDrillType]
    LASER_DRILL: _ClassVar[ViaDrillType]

class TentMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    TENT_TOP: _ClassVar[TentMode]
    TENT_BOTTOM: _ClassVar[TentMode]
    TENT_BOTH: _ClassVar[TentMode]
    TENT_NONE: _ClassVar[TentMode]

class ClearanceType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    MIN_COPPER_WIDTH: _ClassVar[ClearanceType]
    MIN_COPPER_COPPER_SPACE: _ClassVar[ClearanceType]
    MIN_COPPER_HOLE_SPACE: _ClassVar[ClearanceType]
    MIN_COPPER_EDGE_SPACE: _ClassVar[ClearanceType]
    MIN_ANNULAR_RING: _ClassVar[ClearanceType]
    MIN_DRILL_DIAMETER: _ClassVar[ClearanceType]
    MIN_SILKSCREEN_WIDTH: _ClassVar[ClearanceType]
    MIN_PITCH_LEADED: _ClassVar[ClearanceType]
    MIN_PITCH_BGA: _ClassVar[ClearanceType]
    MAX_BOARD_WIDTH: _ClassVar[ClearanceType]
    MAX_BOARD_HEIGHT: _ClassVar[ClearanceType]
    SOLDER_MASK_REGISTRATION: _ClassVar[ClearanceType]
    MIN_SILKSCREEN_TEXT_HEIGHT: _ClassVar[ClearanceType]
    MIN_SILK_SOLDER_MASK_SPACE: _ClassVar[ClearanceType]
    MIN_TH_PAD_EXPAND_OUTER: _ClassVar[ClearanceType]
    MIN_SOLDER_MASK_OPENING: _ClassVar[ClearanceType]
    MIN_SOLDER_MASK_BRIDGE: _ClassVar[ClearanceType]
    MIN_HOLE_TO_HOLE: _ClassVar[ClearanceType]
    MIN_PTH_PIN_SOLDER_CLEARANCE: _ClassVar[ClearanceType]

class Paper(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    ISO_A0: _ClassVar[Paper]
    ISO_A1: _ClassVar[Paper]
    ISO_A2: _ClassVar[Paper]
    ISO_A3: _ClassVar[Paper]
    ISO_A4: _ClassVar[Paper]
    ISO_A5: _ClassVar[Paper]
    ANSI_A: _ClassVar[Paper]
    ANSI_B: _ClassVar[Paper]
    ANSI_C: _ClassVar[Paper]
    ANSI_D: _ClassVar[Paper]
    ANSI_E: _ClassVar[Paper]

class ObjectTagType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    IsCopper: _ClassVar[ObjectTagType]
    IsTrace: _ClassVar[ObjectTagType]
    IsPour: _ClassVar[ObjectTagType]
    IsVia: _ClassVar[ObjectTagType]
    IsPad: _ClassVar[ObjectTagType]
    IsBoardEdge: _ClassVar[ObjectTagType]
    IsThroughHole: _ClassVar[ObjectTagType]
    IsNeckdown: _ClassVar[ObjectTagType]
    IsHole: _ClassVar[ObjectTagType]
UP: Dir
DOWN: Dir
LEFT: Dir
RIGHT: Dir
TOP: Side
BOTTOM: Side
N: Anchor
S: Anchor
E: Anchor
W: Anchor
NE: Anchor
SE: Anchor
SW: Anchor
NW: Anchor
C: Anchor
SMD: PadType
TH: PadType
CONDUCTOR: MaterialType
DIELECTRIC: MaterialType
MECHANICAL_DRILL: ViaDrillType
LASER_DRILL: ViaDrillType
TENT_TOP: TentMode
TENT_BOTTOM: TentMode
TENT_BOTH: TentMode
TENT_NONE: TentMode
MIN_COPPER_WIDTH: ClearanceType
MIN_COPPER_COPPER_SPACE: ClearanceType
MIN_COPPER_HOLE_SPACE: ClearanceType
MIN_COPPER_EDGE_SPACE: ClearanceType
MIN_ANNULAR_RING: ClearanceType
MIN_DRILL_DIAMETER: ClearanceType
MIN_SILKSCREEN_WIDTH: ClearanceType
MIN_PITCH_LEADED: ClearanceType
MIN_PITCH_BGA: ClearanceType
MAX_BOARD_WIDTH: ClearanceType
MAX_BOARD_HEIGHT: ClearanceType
SOLDER_MASK_REGISTRATION: ClearanceType
MIN_SILKSCREEN_TEXT_HEIGHT: ClearanceType
MIN_SILK_SOLDER_MASK_SPACE: ClearanceType
MIN_TH_PAD_EXPAND_OUTER: ClearanceType
MIN_SOLDER_MASK_OPENING: ClearanceType
MIN_SOLDER_MASK_BRIDGE: ClearanceType
MIN_HOLE_TO_HOLE: ClearanceType
MIN_PTH_PIN_SOLDER_CLEARANCE: ClearanceType
ISO_A0: Paper
ISO_A1: Paper
ISO_A2: Paper
ISO_A3: Paper
ISO_A4: Paper
ISO_A5: Paper
ANSI_A: Paper
ANSI_B: Paper
ANSI_C: Paper
ANSI_D: Paper
ANSI_E: Paper
IsCopper: ObjectTagType
IsTrace: ObjectTagType
IsPour: ObjectTagType
IsVia: ObjectTagType
IsPad: ObjectTagType
IsBoardEdge: ObjectTagType
IsThroughHole: ObjectTagType
IsNeckdown: ObjectTagType
IsHole: ObjectTagType
