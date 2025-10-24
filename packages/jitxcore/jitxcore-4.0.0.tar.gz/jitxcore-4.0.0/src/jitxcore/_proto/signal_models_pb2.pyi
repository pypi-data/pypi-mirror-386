from jitxcore._proto import file_info_pb2 as _file_info_pb2
from jitxcore._proto import local_pb2 as _local_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Toleranced(_message.Message):
    __slots__ = ("typ", "tol_plus", "tol_minus")
    TYP_FIELD_NUMBER: _ClassVar[int]
    TOL_PLUS_FIELD_NUMBER: _ClassVar[int]
    TOL_MINUS_FIELD_NUMBER: _ClassVar[int]
    typ: float
    tol_plus: float
    tol_minus: float
    def __init__(self, typ: _Optional[float] = ..., tol_plus: _Optional[float] = ..., tol_minus: _Optional[float] = ...) -> None: ...

class PinModel(_message.Message):
    __slots__ = ("delay", "loss")
    DELAY_FIELD_NUMBER: _ClassVar[int]
    LOSS_FIELD_NUMBER: _ClassVar[int]
    delay: Toleranced
    loss: Toleranced
    def __init__(self, delay: _Optional[_Union[Toleranced, _Mapping]] = ..., loss: _Optional[_Union[Toleranced, _Mapping]] = ...) -> None: ...

class PinModelStmt(_message.Message):
    __slots__ = ("info", "a", "b", "pin_model")
    INFO_FIELD_NUMBER: _ClassVar[int]
    A_FIELD_NUMBER: _ClassVar[int]
    B_FIELD_NUMBER: _ClassVar[int]
    PIN_MODEL_FIELD_NUMBER: _ClassVar[int]
    info: _file_info_pb2.FileInfo
    a: _local_pb2.Local
    b: _local_pb2.Local
    pin_model: PinModel
    def __init__(self, info: _Optional[_Union[_file_info_pb2.FileInfo, _Mapping]] = ..., a: _Optional[_Union[_local_pb2.Local, _Mapping]] = ..., b: _Optional[_Union[_local_pb2.Local, _Mapping]] = ..., pin_model: _Optional[_Union[PinModel, _Mapping]] = ...) -> None: ...

class TimingConstraint(_message.Message):
    __slots__ = ("min_delay", "max_delay")
    MIN_DELAY_FIELD_NUMBER: _ClassVar[int]
    MAX_DELAY_FIELD_NUMBER: _ClassVar[int]
    min_delay: float
    max_delay: float
    def __init__(self, min_delay: _Optional[float] = ..., max_delay: _Optional[float] = ...) -> None: ...

class InsertionLossConstraint(_message.Message):
    __slots__ = ("min_loss", "max_loss")
    MIN_LOSS_FIELD_NUMBER: _ClassVar[int]
    MAX_LOSS_FIELD_NUMBER: _ClassVar[int]
    min_loss: float
    max_loss: float
    def __init__(self, min_loss: _Optional[float] = ..., max_loss: _Optional[float] = ...) -> None: ...

class TimingDifferenceConstraint(_message.Message):
    __slots__ = ("min_delta", "max_delta")
    MIN_DELTA_FIELD_NUMBER: _ClassVar[int]
    MAX_DELTA_FIELD_NUMBER: _ClassVar[int]
    min_delta: float
    max_delta: float
    def __init__(self, min_delta: _Optional[float] = ..., max_delta: _Optional[float] = ...) -> None: ...
