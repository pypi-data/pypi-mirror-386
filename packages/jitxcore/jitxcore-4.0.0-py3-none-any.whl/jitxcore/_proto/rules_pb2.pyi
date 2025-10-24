from jitxcore._proto import enums_pb2 as _enums_pb2
from jitxcore._proto import file_info_pb2 as _file_info_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Rules(_message.Message):
    __slots__ = ("info", "id", "name", "clearances")
    INFO_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    CLEARANCES_FIELD_NUMBER: _ClassVar[int]
    info: _file_info_pb2.FileInfo
    id: int
    name: str
    clearances: _containers.RepeatedCompositeFieldContainer[Clearance]
    def __init__(self, info: _Optional[_Union[_file_info_pb2.FileInfo, _Mapping]] = ..., id: _Optional[int] = ..., name: _Optional[str] = ..., clearances: _Optional[_Iterable[_Union[Clearance, _Mapping]]] = ...) -> None: ...

class Clearance(_message.Message):
    __slots__ = ("type", "value")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    type: _enums_pb2.ClearanceType
    value: float
    def __init__(self, type: _Optional[_Union[_enums_pb2.ClearanceType, str]] = ..., value: _Optional[float] = ...) -> None: ...
