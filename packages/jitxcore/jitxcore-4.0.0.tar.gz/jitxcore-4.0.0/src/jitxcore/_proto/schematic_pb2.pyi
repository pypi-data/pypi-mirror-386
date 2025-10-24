from jitxcore._proto import file_info_pb2 as _file_info_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class SchematicTemplate(_message.Message):
    __slots__ = ("info", "id", "name", "table", "width", "height")
    INFO_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    TABLE_FIELD_NUMBER: _ClassVar[int]
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    HEIGHT_FIELD_NUMBER: _ClassVar[int]
    info: _file_info_pb2.FileInfo
    id: int
    name: str
    table: AuthorTable
    width: int
    height: int
    def __init__(self, info: _Optional[_Union[_file_info_pb2.FileInfo, _Mapping]] = ..., id: _Optional[int] = ..., name: _Optional[str] = ..., table: _Optional[_Union[AuthorTable, _Mapping]] = ..., width: _Optional[int] = ..., height: _Optional[int] = ...) -> None: ...

class AuthorTable(_message.Message):
    __slots__ = ("rows",)
    ROWS_FIELD_NUMBER: _ClassVar[int]
    rows: _containers.RepeatedCompositeFieldContainer[AuthorRow]
    def __init__(self, rows: _Optional[_Iterable[_Union[AuthorRow, _Mapping]]] = ...) -> None: ...

class AuthorRow(_message.Message):
    __slots__ = ("cells", "height")
    CELLS_FIELD_NUMBER: _ClassVar[int]
    HEIGHT_FIELD_NUMBER: _ClassVar[int]
    cells: _containers.RepeatedCompositeFieldContainer[AuthorCell]
    height: float
    def __init__(self, cells: _Optional[_Iterable[_Union[AuthorCell, _Mapping]]] = ..., height: _Optional[float] = ...) -> None: ...

class AuthorCell(_message.Message):
    __slots__ = ("data", "table")
    DATA_FIELD_NUMBER: _ClassVar[int]
    TABLE_FIELD_NUMBER: _ClassVar[int]
    data: DataCell
    table: TableCell
    def __init__(self, data: _Optional[_Union[DataCell, _Mapping]] = ..., table: _Optional[_Union[TableCell, _Mapping]] = ...) -> None: ...

class DataCell(_message.Message):
    __slots__ = ("value", "width")
    VALUE_FIELD_NUMBER: _ClassVar[int]
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    value: str
    width: float
    def __init__(self, value: _Optional[str] = ..., width: _Optional[float] = ...) -> None: ...

class TableCell(_message.Message):
    __slots__ = ("table", "width")
    TABLE_FIELD_NUMBER: _ClassVar[int]
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    table: AuthorTable
    width: float
    def __init__(self, table: _Optional[_Union[AuthorTable, _Mapping]] = ..., width: _Optional[float] = ...) -> None: ...
