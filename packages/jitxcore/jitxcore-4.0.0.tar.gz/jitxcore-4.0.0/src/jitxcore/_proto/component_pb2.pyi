from jitxcore._proto import file_info_pb2 as _file_info_pb2
from jitxcore._proto import local_pb2 as _local_pb2
from jitxcore._proto import mapping_pb2 as _mapping_pb2
from jitxcore._proto import pin_assignment_pb2 as _pin_assignment_pb2
from jitxcore._proto import ports_pb2 as _ports_pb2
from jitxcore._proto import signal_models_pb2 as _signal_models_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Component(_message.Message):
    __slots__ = ("info", "id", "name", "value", "mpn", "datasheet", "manufacturer", "reference_prefix", "ports", "landpattern_map", "symbol_map", "spice", "pin_models", "differential_pairs", "no_connects", "supports")
    INFO_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    MPN_FIELD_NUMBER: _ClassVar[int]
    DATASHEET_FIELD_NUMBER: _ClassVar[int]
    MANUFACTURER_FIELD_NUMBER: _ClassVar[int]
    REFERENCE_PREFIX_FIELD_NUMBER: _ClassVar[int]
    PORTS_FIELD_NUMBER: _ClassVar[int]
    LANDPATTERN_MAP_FIELD_NUMBER: _ClassVar[int]
    SYMBOL_MAP_FIELD_NUMBER: _ClassVar[int]
    SPICE_FIELD_NUMBER: _ClassVar[int]
    PIN_MODELS_FIELD_NUMBER: _ClassVar[int]
    DIFFERENTIAL_PAIRS_FIELD_NUMBER: _ClassVar[int]
    NO_CONNECTS_FIELD_NUMBER: _ClassVar[int]
    SUPPORTS_FIELD_NUMBER: _ClassVar[int]
    info: _file_info_pb2.FileInfo
    id: int
    name: str
    value: str
    mpn: str
    datasheet: str
    manufacturer: str
    reference_prefix: str
    ports: _containers.RepeatedCompositeFieldContainer[_ports_pb2.Port]
    landpattern_map: _mapping_pb2.DefMapping
    symbol_map: SymbolDefMapping
    spice: SpiceModel
    pin_models: _containers.RepeatedCompositeFieldContainer[_signal_models_pb2.PinModelStmt]
    differential_pairs: _containers.RepeatedCompositeFieldContainer[_mapping_pb2.IDMappingEntry]
    no_connects: _containers.RepeatedCompositeFieldContainer[_local_pb2.Local]
    supports: _containers.RepeatedCompositeFieldContainer[_pin_assignment_pb2.Support]
    def __init__(self, info: _Optional[_Union[_file_info_pb2.FileInfo, _Mapping]] = ..., id: _Optional[int] = ..., name: _Optional[str] = ..., value: _Optional[str] = ..., mpn: _Optional[str] = ..., datasheet: _Optional[str] = ..., manufacturer: _Optional[str] = ..., reference_prefix: _Optional[str] = ..., ports: _Optional[_Iterable[_Union[_ports_pb2.Port, _Mapping]]] = ..., landpattern_map: _Optional[_Union[_mapping_pb2.DefMapping, _Mapping]] = ..., symbol_map: _Optional[_Union[SymbolDefMapping, _Mapping]] = ..., spice: _Optional[_Union[SpiceModel, _Mapping]] = ..., pin_models: _Optional[_Iterable[_Union[_signal_models_pb2.PinModelStmt, _Mapping]]] = ..., differential_pairs: _Optional[_Iterable[_Union[_mapping_pb2.IDMappingEntry, _Mapping]]] = ..., no_connects: _Optional[_Iterable[_Union[_local_pb2.Local, _Mapping]]] = ..., supports: _Optional[_Iterable[_Union[_pin_assignment_pb2.Support, _Mapping]]] = ...) -> None: ...

class SymbolDefMapping(_message.Message):
    __slots__ = ("units",)
    UNITS_FIELD_NUMBER: _ClassVar[int]
    units: _containers.RepeatedCompositeFieldContainer[SymbolUnitDefMapping]
    def __init__(self, units: _Optional[_Iterable[_Union[SymbolUnitDefMapping, _Mapping]]] = ...) -> None: ...

class SymbolUnitDefMapping(_message.Message):
    __slots__ = ("unit", "mapping")
    UNIT_FIELD_NUMBER: _ClassVar[int]
    MAPPING_FIELD_NUMBER: _ClassVar[int]
    unit: int
    mapping: _mapping_pb2.DefMapping
    def __init__(self, unit: _Optional[int] = ..., mapping: _Optional[_Union[_mapping_pb2.DefMapping, _Mapping]] = ...) -> None: ...

class SpiceModel(_message.Message):
    __slots__ = ("snippets",)
    SNIPPETS_FIELD_NUMBER: _ClassVar[int]
    snippets: _containers.RepeatedCompositeFieldContainer[SpiceSnippet]
    def __init__(self, snippets: _Optional[_Iterable[_Union[SpiceSnippet, _Mapping]]] = ...) -> None: ...

class SpiceSnippet(_message.Message):
    __slots__ = ("items",)
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    items: _containers.RepeatedCompositeFieldContainer[SnippetItem]
    def __init__(self, items: _Optional[_Iterable[_Union[SnippetItem, _Mapping]]] = ...) -> None: ...

class SnippetItem(_message.Message):
    __slots__ = ("string", "local", "name")
    STRING_FIELD_NUMBER: _ClassVar[int]
    LOCAL_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    string: str
    local: _local_pb2.Local
    name: str
    def __init__(self, string: _Optional[str] = ..., local: _Optional[_Union[_local_pb2.Local, _Mapping]] = ..., name: _Optional[str] = ...) -> None: ...
