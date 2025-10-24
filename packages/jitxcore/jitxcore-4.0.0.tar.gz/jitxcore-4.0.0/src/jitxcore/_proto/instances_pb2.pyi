from jitxcore._proto import file_info_pb2 as _file_info_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Instance(_message.Message):
    __slots__ = ("info", "name", "id", "instantiable")
    INFO_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    INSTANTIABLE_FIELD_NUMBER: _ClassVar[int]
    info: _file_info_pb2.FileInfo
    name: str
    id: int
    instantiable: int
    def __init__(self, info: _Optional[_Union[_file_info_pb2.FileInfo, _Mapping]] = ..., name: _Optional[str] = ..., id: _Optional[int] = ..., instantiable: _Optional[int] = ...) -> None: ...
