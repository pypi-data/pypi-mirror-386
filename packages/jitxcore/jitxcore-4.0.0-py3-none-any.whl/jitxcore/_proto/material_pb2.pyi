from jitxcore._proto import enums_pb2 as _enums_pb2
from jitxcore._proto import file_info_pb2 as _file_info_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Material(_message.Message):
    __slots__ = ("info", "id", "name", "material_name", "type", "roughness", "dielectric_coefficient", "loss_tangent")
    INFO_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    MATERIAL_NAME_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    ROUGHNESS_FIELD_NUMBER: _ClassVar[int]
    DIELECTRIC_COEFFICIENT_FIELD_NUMBER: _ClassVar[int]
    LOSS_TANGENT_FIELD_NUMBER: _ClassVar[int]
    info: _file_info_pb2.FileInfo
    id: int
    name: str
    material_name: str
    type: _enums_pb2.MaterialType
    roughness: float
    dielectric_coefficient: float
    loss_tangent: float
    def __init__(self, info: _Optional[_Union[_file_info_pb2.FileInfo, _Mapping]] = ..., id: _Optional[int] = ..., name: _Optional[str] = ..., material_name: _Optional[str] = ..., type: _Optional[_Union[_enums_pb2.MaterialType, str]] = ..., roughness: _Optional[float] = ..., dielectric_coefficient: _Optional[float] = ..., loss_tangent: _Optional[float] = ...) -> None: ...
