from jitxcore._proto import design_rules_pb2 as _design_rules_pb2
from jitxcore._proto import enums_pb2 as _enums_pb2
from jitxcore._proto import file_info_pb2 as _file_info_pb2
from jitxcore._proto import instances_pb2 as _instances_pb2
from jitxcore._proto import geom_pb2 as _geom_pb2
from jitxcore._proto import layers_pb2 as _layers_pb2
from jitxcore._proto import local_pb2 as _local_pb2
from jitxcore._proto import mapping_pb2 as _mapping_pb2
from jitxcore._proto import nets_pb2 as _nets_pb2
from jitxcore._proto import pin_assignment_pb2 as _pin_assignment_pb2
from jitxcore._proto import ports_pb2 as _ports_pb2
from jitxcore._proto import routing_structures_pb2 as _routing_structures_pb2
from jitxcore._proto import shapes_pb2 as _shapes_pb2
from jitxcore._proto import signal_models_pb2 as _signal_models_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Module(_message.Message):
    __slots__ = ("info", "id", "name", "instances", "ports", "nets", "layers", "net_geoms", "instance_poses", "supports", "requires", "restricts", "short_traces", "reference_designators", "ref_labels", "value_labels", "schematic_groups", "same_schematic_groups", "schematic_group_order", "layout_groups", "same_layout_groups", "net_symbols", "pin_models", "topology_segments", "topology_defs", "differential_pairs", "constrain_timings", "constrain_insertion_losses", "constrain_timing_differences", "structures", "differential_structures", "no_connects", "apply_tags", "properties", "instance_statuses", "annotations")
    INFO_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    INSTANCES_FIELD_NUMBER: _ClassVar[int]
    PORTS_FIELD_NUMBER: _ClassVar[int]
    NETS_FIELD_NUMBER: _ClassVar[int]
    LAYERS_FIELD_NUMBER: _ClassVar[int]
    NET_GEOMS_FIELD_NUMBER: _ClassVar[int]
    INSTANCE_POSES_FIELD_NUMBER: _ClassVar[int]
    SUPPORTS_FIELD_NUMBER: _ClassVar[int]
    REQUIRES_FIELD_NUMBER: _ClassVar[int]
    RESTRICTS_FIELD_NUMBER: _ClassVar[int]
    SHORT_TRACES_FIELD_NUMBER: _ClassVar[int]
    REFERENCE_DESIGNATORS_FIELD_NUMBER: _ClassVar[int]
    REF_LABELS_FIELD_NUMBER: _ClassVar[int]
    VALUE_LABELS_FIELD_NUMBER: _ClassVar[int]
    SCHEMATIC_GROUPS_FIELD_NUMBER: _ClassVar[int]
    SAME_SCHEMATIC_GROUPS_FIELD_NUMBER: _ClassVar[int]
    SCHEMATIC_GROUP_ORDER_FIELD_NUMBER: _ClassVar[int]
    LAYOUT_GROUPS_FIELD_NUMBER: _ClassVar[int]
    SAME_LAYOUT_GROUPS_FIELD_NUMBER: _ClassVar[int]
    NET_SYMBOLS_FIELD_NUMBER: _ClassVar[int]
    PIN_MODELS_FIELD_NUMBER: _ClassVar[int]
    TOPOLOGY_SEGMENTS_FIELD_NUMBER: _ClassVar[int]
    TOPOLOGY_DEFS_FIELD_NUMBER: _ClassVar[int]
    DIFFERENTIAL_PAIRS_FIELD_NUMBER: _ClassVar[int]
    CONSTRAIN_TIMINGS_FIELD_NUMBER: _ClassVar[int]
    CONSTRAIN_INSERTION_LOSSES_FIELD_NUMBER: _ClassVar[int]
    CONSTRAIN_TIMING_DIFFERENCES_FIELD_NUMBER: _ClassVar[int]
    STRUCTURES_FIELD_NUMBER: _ClassVar[int]
    DIFFERENTIAL_STRUCTURES_FIELD_NUMBER: _ClassVar[int]
    NO_CONNECTS_FIELD_NUMBER: _ClassVar[int]
    APPLY_TAGS_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    INSTANCE_STATUSES_FIELD_NUMBER: _ClassVar[int]
    ANNOTATIONS_FIELD_NUMBER: _ClassVar[int]
    info: _file_info_pb2.FileInfo
    id: int
    name: str
    instances: _containers.RepeatedCompositeFieldContainer[_instances_pb2.Instance]
    ports: _containers.RepeatedCompositeFieldContainer[_ports_pb2.Port]
    nets: _containers.RepeatedCompositeFieldContainer[_nets_pb2.Net]
    layers: _containers.RepeatedCompositeFieldContainer[_layers_pb2.Layer]
    net_geoms: _containers.RepeatedCompositeFieldContainer[NetGeom]
    instance_poses: _containers.RepeatedCompositeFieldContainer[InstancePose]
    supports: _containers.RepeatedCompositeFieldContainer[_pin_assignment_pb2.Support]
    requires: _containers.RepeatedCompositeFieldContainer[_pin_assignment_pb2.Require]
    restricts: _containers.RepeatedCompositeFieldContainer[_pin_assignment_pb2.Restrict]
    short_traces: _containers.RepeatedCompositeFieldContainer[_mapping_pb2.IDMappingEntry]
    reference_designators: _containers.RepeatedCompositeFieldContainer[ReferenceDesignator]
    ref_labels: _containers.RepeatedCompositeFieldContainer[RefLabel]
    value_labels: _containers.RepeatedCompositeFieldContainer[ValueLabel]
    schematic_groups: _containers.RepeatedCompositeFieldContainer[SchematicGroup]
    same_schematic_groups: _containers.RepeatedCompositeFieldContainer[SameSchematicGroup]
    schematic_group_order: _containers.RepeatedCompositeFieldContainer[SchematicGroupOrder]
    layout_groups: _containers.RepeatedCompositeFieldContainer[LayoutGroup]
    same_layout_groups: _containers.RepeatedCompositeFieldContainer[SameLayoutGroup]
    net_symbols: _containers.RepeatedCompositeFieldContainer[NetSymbol]
    pin_models: _containers.RepeatedCompositeFieldContainer[_signal_models_pb2.PinModelStmt]
    topology_segments: _containers.RepeatedCompositeFieldContainer[_mapping_pb2.IDMappingEntry]
    topology_defs: _containers.RepeatedCompositeFieldContainer[TopologyDef]
    differential_pairs: _containers.RepeatedCompositeFieldContainer[_mapping_pb2.IDMappingEntry]
    constrain_timings: _containers.RepeatedCompositeFieldContainer[ConstrainTiming]
    constrain_insertion_losses: _containers.RepeatedCompositeFieldContainer[ConstrainInsertionLoss]
    constrain_timing_differences: _containers.RepeatedCompositeFieldContainer[ConstrainTimingDifference]
    structures: _containers.RepeatedCompositeFieldContainer[_routing_structures_pb2.Structure]
    differential_structures: _containers.RepeatedCompositeFieldContainer[_routing_structures_pb2.DifferentialStructure]
    no_connects: _containers.RepeatedCompositeFieldContainer[_local_pb2.Local]
    apply_tags: _containers.RepeatedCompositeFieldContainer[ApplyTag]
    properties: _containers.RepeatedCompositeFieldContainer[_mapping_pb2.IDProperty]
    instance_statuses: _containers.RepeatedCompositeFieldContainer[InstanceStatus]
    annotations: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, info: _Optional[_Union[_file_info_pb2.FileInfo, _Mapping]] = ..., id: _Optional[int] = ..., name: _Optional[str] = ..., instances: _Optional[_Iterable[_Union[_instances_pb2.Instance, _Mapping]]] = ..., ports: _Optional[_Iterable[_Union[_ports_pb2.Port, _Mapping]]] = ..., nets: _Optional[_Iterable[_Union[_nets_pb2.Net, _Mapping]]] = ..., layers: _Optional[_Iterable[_Union[_layers_pb2.Layer, _Mapping]]] = ..., net_geoms: _Optional[_Iterable[_Union[NetGeom, _Mapping]]] = ..., instance_poses: _Optional[_Iterable[_Union[InstancePose, _Mapping]]] = ..., supports: _Optional[_Iterable[_Union[_pin_assignment_pb2.Support, _Mapping]]] = ..., requires: _Optional[_Iterable[_Union[_pin_assignment_pb2.Require, _Mapping]]] = ..., restricts: _Optional[_Iterable[_Union[_pin_assignment_pb2.Restrict, _Mapping]]] = ..., short_traces: _Optional[_Iterable[_Union[_mapping_pb2.IDMappingEntry, _Mapping]]] = ..., reference_designators: _Optional[_Iterable[_Union[ReferenceDesignator, _Mapping]]] = ..., ref_labels: _Optional[_Iterable[_Union[RefLabel, _Mapping]]] = ..., value_labels: _Optional[_Iterable[_Union[ValueLabel, _Mapping]]] = ..., schematic_groups: _Optional[_Iterable[_Union[SchematicGroup, _Mapping]]] = ..., same_schematic_groups: _Optional[_Iterable[_Union[SameSchematicGroup, _Mapping]]] = ..., schematic_group_order: _Optional[_Iterable[_Union[SchematicGroupOrder, _Mapping]]] = ..., layout_groups: _Optional[_Iterable[_Union[LayoutGroup, _Mapping]]] = ..., same_layout_groups: _Optional[_Iterable[_Union[SameLayoutGroup, _Mapping]]] = ..., net_symbols: _Optional[_Iterable[_Union[NetSymbol, _Mapping]]] = ..., pin_models: _Optional[_Iterable[_Union[_signal_models_pb2.PinModelStmt, _Mapping]]] = ..., topology_segments: _Optional[_Iterable[_Union[_mapping_pb2.IDMappingEntry, _Mapping]]] = ..., topology_defs: _Optional[_Iterable[_Union[TopologyDef, _Mapping]]] = ..., differential_pairs: _Optional[_Iterable[_Union[_mapping_pb2.IDMappingEntry, _Mapping]]] = ..., constrain_timings: _Optional[_Iterable[_Union[ConstrainTiming, _Mapping]]] = ..., constrain_insertion_losses: _Optional[_Iterable[_Union[ConstrainInsertionLoss, _Mapping]]] = ..., constrain_timing_differences: _Optional[_Iterable[_Union[ConstrainTimingDifference, _Mapping]]] = ..., structures: _Optional[_Iterable[_Union[_routing_structures_pb2.Structure, _Mapping]]] = ..., differential_structures: _Optional[_Iterable[_Union[_routing_structures_pb2.DifferentialStructure, _Mapping]]] = ..., no_connects: _Optional[_Iterable[_Union[_local_pb2.Local, _Mapping]]] = ..., apply_tags: _Optional[_Iterable[_Union[ApplyTag, _Mapping]]] = ..., properties: _Optional[_Iterable[_Union[_mapping_pb2.IDProperty, _Mapping]]] = ..., instance_statuses: _Optional[_Iterable[_Union[InstanceStatus, _Mapping]]] = ..., annotations: _Optional[_Iterable[str]] = ...) -> None: ...

class NetGeom(_message.Message):
    __slots__ = ("ref", "geom")
    REF_FIELD_NUMBER: _ClassVar[int]
    GEOM_FIELD_NUMBER: _ClassVar[int]
    ref: _local_pb2.Local
    geom: _geom_pb2.Geom
    def __init__(self, ref: _Optional[_Union[_local_pb2.Local, _Mapping]] = ..., geom: _Optional[_Union[_geom_pb2.Geom, _Mapping]] = ...) -> None: ...

class InstancePose(_message.Message):
    __slots__ = ("instance", "pose", "side", "anchor")
    INSTANCE_FIELD_NUMBER: _ClassVar[int]
    POSE_FIELD_NUMBER: _ClassVar[int]
    SIDE_FIELD_NUMBER: _ClassVar[int]
    ANCHOR_FIELD_NUMBER: _ClassVar[int]
    instance: _local_pb2.Local
    pose: _shapes_pb2.Pose
    side: _enums_pb2.Side
    anchor: _local_pb2.Local
    def __init__(self, instance: _Optional[_Union[_local_pb2.Local, _Mapping]] = ..., pose: _Optional[_Union[_shapes_pb2.Pose, _Mapping]] = ..., side: _Optional[_Union[_enums_pb2.Side, str]] = ..., anchor: _Optional[_Union[_local_pb2.Local, _Mapping]] = ...) -> None: ...

class ReferenceDesignator(_message.Message):
    __slots__ = ("instance", "reference")
    INSTANCE_FIELD_NUMBER: _ClassVar[int]
    REFERENCE_FIELD_NUMBER: _ClassVar[int]
    instance: _local_pb2.Local
    reference: str
    def __init__(self, instance: _Optional[_Union[_local_pb2.Local, _Mapping]] = ..., reference: _Optional[str] = ...) -> None: ...

class RefLabel(_message.Message):
    __slots__ = ("instance", "text")
    INSTANCE_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    instance: _local_pb2.Local
    text: str
    def __init__(self, instance: _Optional[_Union[_local_pb2.Local, _Mapping]] = ..., text: _Optional[str] = ...) -> None: ...

class ValueLabel(_message.Message):
    __slots__ = ("instance", "text")
    INSTANCE_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    instance: _local_pb2.Local
    text: str
    def __init__(self, instance: _Optional[_Union[_local_pb2.Local, _Mapping]] = ..., text: _Optional[str] = ...) -> None: ...

class SchematicGroup(_message.Message):
    __slots__ = ("instance", "unit", "group")
    INSTANCE_FIELD_NUMBER: _ClassVar[int]
    UNIT_FIELD_NUMBER: _ClassVar[int]
    GROUP_FIELD_NUMBER: _ClassVar[int]
    instance: _local_pb2.Local
    unit: int
    group: str
    def __init__(self, instance: _Optional[_Union[_local_pb2.Local, _Mapping]] = ..., unit: _Optional[int] = ..., group: _Optional[str] = ...) -> None: ...

class SameSchematicGroup(_message.Message):
    __slots__ = ("instance", "instance_unit", "anchor", "anchor_unit")
    INSTANCE_FIELD_NUMBER: _ClassVar[int]
    INSTANCE_UNIT_FIELD_NUMBER: _ClassVar[int]
    ANCHOR_FIELD_NUMBER: _ClassVar[int]
    ANCHOR_UNIT_FIELD_NUMBER: _ClassVar[int]
    instance: _local_pb2.Local
    instance_unit: int
    anchor: _local_pb2.Local
    anchor_unit: int
    def __init__(self, instance: _Optional[_Union[_local_pb2.Local, _Mapping]] = ..., instance_unit: _Optional[int] = ..., anchor: _Optional[_Union[_local_pb2.Local, _Mapping]] = ..., anchor_unit: _Optional[int] = ...) -> None: ...

class SchematicGroupOrder(_message.Message):
    __slots__ = ("groups",)
    GROUPS_FIELD_NUMBER: _ClassVar[int]
    groups: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, groups: _Optional[_Iterable[str]] = ...) -> None: ...

class LayoutGroup(_message.Message):
    __slots__ = ("instance", "group")
    INSTANCE_FIELD_NUMBER: _ClassVar[int]
    GROUP_FIELD_NUMBER: _ClassVar[int]
    instance: _local_pb2.Local
    group: str
    def __init__(self, instance: _Optional[_Union[_local_pb2.Local, _Mapping]] = ..., group: _Optional[str] = ...) -> None: ...

class SameLayoutGroup(_message.Message):
    __slots__ = ("instance", "anchor")
    INSTANCE_FIELD_NUMBER: _ClassVar[int]
    ANCHOR_FIELD_NUMBER: _ClassVar[int]
    instance: _local_pb2.Local
    anchor: _local_pb2.Local
    def __init__(self, instance: _Optional[_Union[_local_pb2.Local, _Mapping]] = ..., anchor: _Optional[_Union[_local_pb2.Local, _Mapping]] = ...) -> None: ...

class NetSymbol(_message.Message):
    __slots__ = ("net", "symbol")
    NET_FIELD_NUMBER: _ClassVar[int]
    SYMBOL_FIELD_NUMBER: _ClassVar[int]
    net: _local_pb2.Local
    symbol: int
    def __init__(self, net: _Optional[_Union[_local_pb2.Local, _Mapping]] = ..., symbol: _Optional[int] = ...) -> None: ...

class TopologyDef(_message.Message):
    __slots__ = ("info", "name", "path")
    INFO_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    info: _file_info_pb2.FileInfo
    name: str
    path: _mapping_pb2.IDMappingEntry
    def __init__(self, info: _Optional[_Union[_file_info_pb2.FileInfo, _Mapping]] = ..., name: _Optional[str] = ..., path: _Optional[_Union[_mapping_pb2.IDMappingEntry, _Mapping]] = ...) -> None: ...

class ConstrainTiming(_message.Message):
    __slots__ = ("info", "path", "constraint")
    INFO_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    CONSTRAINT_FIELD_NUMBER: _ClassVar[int]
    info: _file_info_pb2.FileInfo
    path: _mapping_pb2.IDMappingEntry
    constraint: _signal_models_pb2.TimingConstraint
    def __init__(self, info: _Optional[_Union[_file_info_pb2.FileInfo, _Mapping]] = ..., path: _Optional[_Union[_mapping_pb2.IDMappingEntry, _Mapping]] = ..., constraint: _Optional[_Union[_signal_models_pb2.TimingConstraint, _Mapping]] = ...) -> None: ...

class ConstrainInsertionLoss(_message.Message):
    __slots__ = ("info", "path", "constraint")
    INFO_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    CONSTRAINT_FIELD_NUMBER: _ClassVar[int]
    info: _file_info_pb2.FileInfo
    path: _mapping_pb2.IDMappingEntry
    constraint: _signal_models_pb2.InsertionLossConstraint
    def __init__(self, info: _Optional[_Union[_file_info_pb2.FileInfo, _Mapping]] = ..., path: _Optional[_Union[_mapping_pb2.IDMappingEntry, _Mapping]] = ..., constraint: _Optional[_Union[_signal_models_pb2.InsertionLossConstraint, _Mapping]] = ...) -> None: ...

class ConstrainTimingDifference(_message.Message):
    __slots__ = ("info", "path1", "path2", "constraint")
    INFO_FIELD_NUMBER: _ClassVar[int]
    PATH1_FIELD_NUMBER: _ClassVar[int]
    PATH2_FIELD_NUMBER: _ClassVar[int]
    CONSTRAINT_FIELD_NUMBER: _ClassVar[int]
    info: _file_info_pb2.FileInfo
    path1: _mapping_pb2.IDMappingEntry
    path2: _mapping_pb2.IDMappingEntry
    constraint: _signal_models_pb2.TimingDifferenceConstraint
    def __init__(self, info: _Optional[_Union[_file_info_pb2.FileInfo, _Mapping]] = ..., path1: _Optional[_Union[_mapping_pb2.IDMappingEntry, _Mapping]] = ..., path2: _Optional[_Union[_mapping_pb2.IDMappingEntry, _Mapping]] = ..., constraint: _Optional[_Union[_signal_models_pb2.TimingDifferenceConstraint, _Mapping]] = ...) -> None: ...

class ApplyTag(_message.Message):
    __slots__ = ("local", "tags")
    LOCAL_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    local: _local_pb2.Local
    tags: _containers.RepeatedCompositeFieldContainer[_design_rules_pb2.UserTag]
    def __init__(self, local: _Optional[_Union[_local_pb2.Local, _Mapping]] = ..., tags: _Optional[_Iterable[_Union[_design_rules_pb2.UserTag, _Mapping]]] = ...) -> None: ...

class InstanceStatus(_message.Message):
    __slots__ = ("instance", "in_bom", "soldered", "schematic_x_out")
    INSTANCE_FIELD_NUMBER: _ClassVar[int]
    IN_BOM_FIELD_NUMBER: _ClassVar[int]
    SOLDERED_FIELD_NUMBER: _ClassVar[int]
    SCHEMATIC_X_OUT_FIELD_NUMBER: _ClassVar[int]
    instance: _local_pb2.Local
    in_bom: bool
    soldered: bool
    schematic_x_out: bool
    def __init__(self, instance: _Optional[_Union[_local_pb2.Local, _Mapping]] = ..., in_bom: bool = ..., soldered: bool = ..., schematic_x_out: bool = ...) -> None: ...
