from jitxcore._proto import enums_pb2 as _enums_pb2
from jitxcore._proto import file_info_pb2 as _file_info_pb2
from jitxcore._proto import layers_pb2 as _layers_pb2
from jitxcore._proto import signal_models_pb2 as _signal_models_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Via(_message.Message):
    __slots__ = ("info", "id", "name", "start", "stop", "diameter", "antipad_diameter", "nfp_diameter", "nfp_antipad_diameter", "diameters", "hole_diameter", "type", "filled", "tented", "via_in_pad", "backdrill", "structure_models")
    INFO_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    START_FIELD_NUMBER: _ClassVar[int]
    STOP_FIELD_NUMBER: _ClassVar[int]
    DIAMETER_FIELD_NUMBER: _ClassVar[int]
    ANTIPAD_DIAMETER_FIELD_NUMBER: _ClassVar[int]
    NFP_DIAMETER_FIELD_NUMBER: _ClassVar[int]
    NFP_ANTIPAD_DIAMETER_FIELD_NUMBER: _ClassVar[int]
    DIAMETERS_FIELD_NUMBER: _ClassVar[int]
    HOLE_DIAMETER_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    FILLED_FIELD_NUMBER: _ClassVar[int]
    TENTED_FIELD_NUMBER: _ClassVar[int]
    VIA_IN_PAD_FIELD_NUMBER: _ClassVar[int]
    BACKDRILL_FIELD_NUMBER: _ClassVar[int]
    STRUCTURE_MODELS_FIELD_NUMBER: _ClassVar[int]
    info: _file_info_pb2.FileInfo
    id: int
    name: str
    start: _layers_pb2.LayerIndex
    stop: _layers_pb2.LayerIndex
    diameter: float
    antipad_diameter: float
    nfp_diameter: float
    nfp_antipad_diameter: float
    diameters: _containers.RepeatedCompositeFieldContainer[ViaDiameter]
    hole_diameter: float
    type: _enums_pb2.ViaDrillType
    filled: bool
    tented: _enums_pb2.TentMode
    via_in_pad: bool
    backdrill: BackdrillSet
    structure_models: _containers.RepeatedCompositeFieldContainer[StructureModel]
    def __init__(self, info: _Optional[_Union[_file_info_pb2.FileInfo, _Mapping]] = ..., id: _Optional[int] = ..., name: _Optional[str] = ..., start: _Optional[_Union[_layers_pb2.LayerIndex, _Mapping]] = ..., stop: _Optional[_Union[_layers_pb2.LayerIndex, _Mapping]] = ..., diameter: _Optional[float] = ..., antipad_diameter: _Optional[float] = ..., nfp_diameter: _Optional[float] = ..., nfp_antipad_diameter: _Optional[float] = ..., diameters: _Optional[_Iterable[_Union[ViaDiameter, _Mapping]]] = ..., hole_diameter: _Optional[float] = ..., type: _Optional[_Union[_enums_pb2.ViaDrillType, str]] = ..., filled: bool = ..., tented: _Optional[_Union[_enums_pb2.TentMode, str]] = ..., via_in_pad: bool = ..., backdrill: _Optional[_Union[BackdrillSet, _Mapping]] = ..., structure_models: _Optional[_Iterable[_Union[StructureModel, _Mapping]]] = ...) -> None: ...

class BackdrillSet(_message.Message):
    __slots__ = ("top", "bottom")
    TOP_FIELD_NUMBER: _ClassVar[int]
    BOTTOM_FIELD_NUMBER: _ClassVar[int]
    top: Backdrill
    bottom: Backdrill
    def __init__(self, top: _Optional[_Union[Backdrill, _Mapping]] = ..., bottom: _Optional[_Union[Backdrill, _Mapping]] = ...) -> None: ...

class Backdrill(_message.Message):
    __slots__ = ("diameter", "startpad_diameter", "solder_mask_opening", "copper_clearance")
    DIAMETER_FIELD_NUMBER: _ClassVar[int]
    STARTPAD_DIAMETER_FIELD_NUMBER: _ClassVar[int]
    SOLDER_MASK_OPENING_FIELD_NUMBER: _ClassVar[int]
    COPPER_CLEARANCE_FIELD_NUMBER: _ClassVar[int]
    diameter: float
    startpad_diameter: float
    solder_mask_opening: float
    copper_clearance: float
    def __init__(self, diameter: _Optional[float] = ..., startpad_diameter: _Optional[float] = ..., solder_mask_opening: _Optional[float] = ..., copper_clearance: _Optional[float] = ...) -> None: ...

class StructureModel(_message.Message):
    __slots__ = ("entry", "exit", "model")
    ENTRY_FIELD_NUMBER: _ClassVar[int]
    EXIT_FIELD_NUMBER: _ClassVar[int]
    MODEL_FIELD_NUMBER: _ClassVar[int]
    entry: _layers_pb2.LayerIndex
    exit: _layers_pb2.LayerIndex
    model: _signal_models_pb2.PinModel
    def __init__(self, entry: _Optional[_Union[_layers_pb2.LayerIndex, _Mapping]] = ..., exit: _Optional[_Union[_layers_pb2.LayerIndex, _Mapping]] = ..., model: _Optional[_Union[_signal_models_pb2.PinModel, _Mapping]] = ...) -> None: ...

class ViaDiameter(_message.Message):
    __slots__ = ("pad", "antipad", "nfp", "nfp_antipad", "layers")
    PAD_FIELD_NUMBER: _ClassVar[int]
    ANTIPAD_FIELD_NUMBER: _ClassVar[int]
    NFP_FIELD_NUMBER: _ClassVar[int]
    NFP_ANTIPAD_FIELD_NUMBER: _ClassVar[int]
    LAYERS_FIELD_NUMBER: _ClassVar[int]
    pad: float
    antipad: float
    nfp: float
    nfp_antipad: float
    layers: _containers.RepeatedCompositeFieldContainer[_layers_pb2.LayerIndex]
    def __init__(self, pad: _Optional[float] = ..., antipad: _Optional[float] = ..., nfp: _Optional[float] = ..., nfp_antipad: _Optional[float] = ..., layers: _Optional[_Iterable[_Union[_layers_pb2.LayerIndex, _Mapping]]] = ...) -> None: ...
