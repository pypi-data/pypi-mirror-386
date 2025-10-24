from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class FileInfo(_message.Message):
    __slots__ = ("index", "line", "column")
    INDEX_FIELD_NUMBER: _ClassVar[int]
    LINE_FIELD_NUMBER: _ClassVar[int]
    COLUMN_FIELD_NUMBER: _ClassVar[int]
    index: int
    line: int
    column: int
    def __init__(self, index: _Optional[int] = ..., line: _Optional[int] = ..., column: _Optional[int] = ...) -> None: ...
