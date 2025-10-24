from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ViaStitchPattern(_message.Message):
    __slots__ = ("square", "triangular")
    SQUARE_FIELD_NUMBER: _ClassVar[int]
    TRIANGULAR_FIELD_NUMBER: _ClassVar[int]
    square: SquareViaStitchGrid
    triangular: TriangularViaStitchGrid
    def __init__(self, square: _Optional[_Union[SquareViaStitchGrid, _Mapping]] = ..., triangular: _Optional[_Union[TriangularViaStitchGrid, _Mapping]] = ...) -> None: ...

class SquareViaStitchGrid(_message.Message):
    __slots__ = ("pitch", "inset")
    PITCH_FIELD_NUMBER: _ClassVar[int]
    INSET_FIELD_NUMBER: _ClassVar[int]
    pitch: float
    inset: float
    def __init__(self, pitch: _Optional[float] = ..., inset: _Optional[float] = ...) -> None: ...

class TriangularViaStitchGrid(_message.Message):
    __slots__ = ("pitch", "inset")
    PITCH_FIELD_NUMBER: _ClassVar[int]
    INSET_FIELD_NUMBER: _ClassVar[int]
    pitch: float
    inset: float
    def __init__(self, pitch: _Optional[float] = ..., inset: _Optional[float] = ...) -> None: ...

class ViaFencePattern(_message.Message):
    __slots__ = ("pitch", "offset", "num_rows", "min_pitch", "max_pitch", "initial_offset", "input_shape_only")
    PITCH_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    NUM_ROWS_FIELD_NUMBER: _ClassVar[int]
    MIN_PITCH_FIELD_NUMBER: _ClassVar[int]
    MAX_PITCH_FIELD_NUMBER: _ClassVar[int]
    INITIAL_OFFSET_FIELD_NUMBER: _ClassVar[int]
    INPUT_SHAPE_ONLY_FIELD_NUMBER: _ClassVar[int]
    pitch: float
    offset: float
    num_rows: int
    min_pitch: float
    max_pitch: float
    initial_offset: float
    input_shape_only: bool
    def __init__(self, pitch: _Optional[float] = ..., offset: _Optional[float] = ..., num_rows: _Optional[int] = ..., min_pitch: _Optional[float] = ..., max_pitch: _Optional[float] = ..., initial_offset: _Optional[float] = ..., input_shape_only: bool = ...) -> None: ...

class StitchVia(_message.Message):
    __slots__ = ("definition", "pattern")
    DEFINITION_FIELD_NUMBER: _ClassVar[int]
    PATTERN_FIELD_NUMBER: _ClassVar[int]
    definition: str
    pattern: ViaStitchPattern
    def __init__(self, definition: _Optional[str] = ..., pattern: _Optional[_Union[ViaStitchPattern, _Mapping]] = ...) -> None: ...

class FenceVia(_message.Message):
    __slots__ = ("definition", "pattern")
    DEFINITION_FIELD_NUMBER: _ClassVar[int]
    PATTERN_FIELD_NUMBER: _ClassVar[int]
    definition: str
    pattern: ViaFencePattern
    def __init__(self, definition: _Optional[str] = ..., pattern: _Optional[_Union[ViaFencePattern, _Mapping]] = ...) -> None: ...
