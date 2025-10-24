from jitxcore._proto import board_pb2 as _board_pb2
from jitxcore._proto import bundle_pb2 as _bundle_pb2
from jitxcore._proto import component_pb2 as _component_pb2
from jitxcore._proto import design_rules_pb2 as _design_rules_pb2
from jitxcore._proto import diff_routing_pb2 as _diff_routing_pb2
from jitxcore._proto import enums_pb2 as _enums_pb2
from jitxcore._proto import landpattern_pb2 as _landpattern_pb2
from jitxcore._proto import material_pb2 as _material_pb2
from jitxcore._proto import module_pb2 as _module_pb2
from jitxcore._proto import pad_pb2 as _pad_pb2
from jitxcore._proto import pin_assignment_pb2 as _pin_assignment_pb2
from jitxcore._proto import routing_pb2 as _routing_pb2
from jitxcore._proto import rules_pb2 as _rules_pb2
from jitxcore._proto import schematic_pb2 as _schematic_pb2
from jitxcore._proto import stackup_pb2 as _stackup_pb2
from jitxcore._proto import symbol_pb2 as _symbol_pb2
from jitxcore._proto import via_pb2 as _via_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Design(_message.Message):
    __slots__ = ("v1",)
    V1_FIELD_NUMBER: _ClassVar[int]
    v1: DesignV1
    def __init__(self, v1: _Optional[_Union[DesignV1, _Mapping]] = ...) -> None: ...

class DesignV1(_message.Message):
    __slots__ = ("boards", "ruless", "modules", "components", "stackups", "materials", "bundles", "landpatterns", "symbols", "pads", "vias", "routings", "differential_routings", "schematic_templates", "design_rules", "files", "name", "board", "rules", "module", "schematic_template", "schematic_page_markings", "schematic_title_page", "restricts", "paper", "filenames", "version")
    BOARDS_FIELD_NUMBER: _ClassVar[int]
    RULESS_FIELD_NUMBER: _ClassVar[int]
    MODULES_FIELD_NUMBER: _ClassVar[int]
    COMPONENTS_FIELD_NUMBER: _ClassVar[int]
    STACKUPS_FIELD_NUMBER: _ClassVar[int]
    MATERIALS_FIELD_NUMBER: _ClassVar[int]
    BUNDLES_FIELD_NUMBER: _ClassVar[int]
    LANDPATTERNS_FIELD_NUMBER: _ClassVar[int]
    SYMBOLS_FIELD_NUMBER: _ClassVar[int]
    PADS_FIELD_NUMBER: _ClassVar[int]
    VIAS_FIELD_NUMBER: _ClassVar[int]
    ROUTINGS_FIELD_NUMBER: _ClassVar[int]
    DIFFERENTIAL_ROUTINGS_FIELD_NUMBER: _ClassVar[int]
    SCHEMATIC_TEMPLATES_FIELD_NUMBER: _ClassVar[int]
    DESIGN_RULES_FIELD_NUMBER: _ClassVar[int]
    FILES_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    BOARD_FIELD_NUMBER: _ClassVar[int]
    RULES_FIELD_NUMBER: _ClassVar[int]
    MODULE_FIELD_NUMBER: _ClassVar[int]
    SCHEMATIC_TEMPLATE_FIELD_NUMBER: _ClassVar[int]
    SCHEMATIC_PAGE_MARKINGS_FIELD_NUMBER: _ClassVar[int]
    SCHEMATIC_TITLE_PAGE_FIELD_NUMBER: _ClassVar[int]
    RESTRICTS_FIELD_NUMBER: _ClassVar[int]
    PAPER_FIELD_NUMBER: _ClassVar[int]
    FILENAMES_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    boards: _containers.RepeatedCompositeFieldContainer[_board_pb2.Board]
    ruless: _containers.RepeatedCompositeFieldContainer[_rules_pb2.Rules]
    modules: _containers.RepeatedCompositeFieldContainer[_module_pb2.Module]
    components: _containers.RepeatedCompositeFieldContainer[_component_pb2.Component]
    stackups: _containers.RepeatedCompositeFieldContainer[_stackup_pb2.Stackup]
    materials: _containers.RepeatedCompositeFieldContainer[_material_pb2.Material]
    bundles: _containers.RepeatedCompositeFieldContainer[_bundle_pb2.Bundle]
    landpatterns: _containers.RepeatedCompositeFieldContainer[_landpattern_pb2.Landpattern]
    symbols: _containers.RepeatedCompositeFieldContainer[_symbol_pb2.Symbol]
    pads: _containers.RepeatedCompositeFieldContainer[_pad_pb2.Pad]
    vias: _containers.RepeatedCompositeFieldContainer[_via_pb2.Via]
    routings: _containers.RepeatedCompositeFieldContainer[_routing_pb2.Routing]
    differential_routings: _containers.RepeatedCompositeFieldContainer[_diff_routing_pb2.DifferentialRouting]
    schematic_templates: _containers.RepeatedCompositeFieldContainer[_schematic_pb2.SchematicTemplate]
    design_rules: _containers.RepeatedCompositeFieldContainer[_design_rules_pb2.DesignRule]
    files: _containers.RepeatedScalarFieldContainer[str]
    name: str
    board: int
    rules: int
    module: int
    schematic_template: int
    schematic_page_markings: _containers.RepeatedCompositeFieldContainer[SchematicPageMarking]
    schematic_title_page: str
    restricts: _containers.RepeatedCompositeFieldContainer[_pin_assignment_pb2.RestrictEntry]
    paper: _enums_pb2.Paper
    filenames: _containers.RepeatedScalarFieldContainer[str]
    version: int
    def __init__(self, boards: _Optional[_Iterable[_Union[_board_pb2.Board, _Mapping]]] = ..., ruless: _Optional[_Iterable[_Union[_rules_pb2.Rules, _Mapping]]] = ..., modules: _Optional[_Iterable[_Union[_module_pb2.Module, _Mapping]]] = ..., components: _Optional[_Iterable[_Union[_component_pb2.Component, _Mapping]]] = ..., stackups: _Optional[_Iterable[_Union[_stackup_pb2.Stackup, _Mapping]]] = ..., materials: _Optional[_Iterable[_Union[_material_pb2.Material, _Mapping]]] = ..., bundles: _Optional[_Iterable[_Union[_bundle_pb2.Bundle, _Mapping]]] = ..., landpatterns: _Optional[_Iterable[_Union[_landpattern_pb2.Landpattern, _Mapping]]] = ..., symbols: _Optional[_Iterable[_Union[_symbol_pb2.Symbol, _Mapping]]] = ..., pads: _Optional[_Iterable[_Union[_pad_pb2.Pad, _Mapping]]] = ..., vias: _Optional[_Iterable[_Union[_via_pb2.Via, _Mapping]]] = ..., routings: _Optional[_Iterable[_Union[_routing_pb2.Routing, _Mapping]]] = ..., differential_routings: _Optional[_Iterable[_Union[_diff_routing_pb2.DifferentialRouting, _Mapping]]] = ..., schematic_templates: _Optional[_Iterable[_Union[_schematic_pb2.SchematicTemplate, _Mapping]]] = ..., design_rules: _Optional[_Iterable[_Union[_design_rules_pb2.DesignRule, _Mapping]]] = ..., files: _Optional[_Iterable[str]] = ..., name: _Optional[str] = ..., board: _Optional[int] = ..., rules: _Optional[int] = ..., module: _Optional[int] = ..., schematic_template: _Optional[int] = ..., schematic_page_markings: _Optional[_Iterable[_Union[SchematicPageMarking, _Mapping]]] = ..., schematic_title_page: _Optional[str] = ..., restricts: _Optional[_Iterable[_Union[_pin_assignment_pb2.RestrictEntry, _Mapping]]] = ..., paper: _Optional[_Union[_enums_pb2.Paper, str]] = ..., filenames: _Optional[_Iterable[str]] = ..., version: _Optional[int] = ...) -> None: ...

class SchematicPageMarking(_message.Message):
    __slots__ = ("marking", "anchor")
    MARKING_FIELD_NUMBER: _ClassVar[int]
    ANCHOR_FIELD_NUMBER: _ClassVar[int]
    marking: str
    anchor: _enums_pb2.Anchor
    def __init__(self, marking: _Optional[str] = ..., anchor: _Optional[_Union[_enums_pb2.Anchor, str]] = ...) -> None: ...
