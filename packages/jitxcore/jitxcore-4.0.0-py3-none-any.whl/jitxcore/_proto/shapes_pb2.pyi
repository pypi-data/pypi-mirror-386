from jitxcore._proto import enums_pb2 as _enums_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Shape(_message.Message):
    __slots__ = ("polygon", "arc_polygon", "polyline", "arc_polyline", "circle", "empty_shape", "polygon_set", "text", "union")
    POLYGON_FIELD_NUMBER: _ClassVar[int]
    ARC_POLYGON_FIELD_NUMBER: _ClassVar[int]
    POLYLINE_FIELD_NUMBER: _ClassVar[int]
    ARC_POLYLINE_FIELD_NUMBER: _ClassVar[int]
    CIRCLE_FIELD_NUMBER: _ClassVar[int]
    EMPTY_SHAPE_FIELD_NUMBER: _ClassVar[int]
    POLYGON_SET_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    UNION_FIELD_NUMBER: _ClassVar[int]
    polygon: Polygon
    arc_polygon: ArcPolygon
    polyline: Polyline
    arc_polyline: ArcPolyline
    circle: Circle
    empty_shape: EmptyShape
    polygon_set: PolygonSet
    text: Text
    union: Union
    def __init__(self, polygon: _Optional[_Union[Polygon, _Mapping]] = ..., arc_polygon: _Optional[_Union[ArcPolygon, _Mapping]] = ..., polyline: _Optional[_Union[Polyline, _Mapping]] = ..., arc_polyline: _Optional[_Union[ArcPolyline, _Mapping]] = ..., circle: _Optional[_Union[Circle, _Mapping]] = ..., empty_shape: _Optional[_Union[EmptyShape, _Mapping]] = ..., polygon_set: _Optional[_Union[PolygonSet, _Mapping]] = ..., text: _Optional[_Union[Text, _Mapping]] = ..., union: _Optional[_Union[Union, _Mapping]] = ...) -> None: ...

class Point(_message.Message):
    __slots__ = ("x", "y")
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    x: float
    y: float
    def __init__(self, x: _Optional[float] = ..., y: _Optional[float] = ...) -> None: ...

class Arc(_message.Message):
    __slots__ = ("center", "radius", "start_angle", "angle")
    CENTER_FIELD_NUMBER: _ClassVar[int]
    RADIUS_FIELD_NUMBER: _ClassVar[int]
    START_ANGLE_FIELD_NUMBER: _ClassVar[int]
    ANGLE_FIELD_NUMBER: _ClassVar[int]
    center: Point
    radius: float
    start_angle: float
    angle: float
    def __init__(self, center: _Optional[_Union[Point, _Mapping]] = ..., radius: _Optional[float] = ..., start_angle: _Optional[float] = ..., angle: _Optional[float] = ...) -> None: ...

class Polygon(_message.Message):
    __slots__ = ("points",)
    POINTS_FIELD_NUMBER: _ClassVar[int]
    points: _containers.RepeatedCompositeFieldContainer[Point]
    def __init__(self, points: _Optional[_Iterable[_Union[Point, _Mapping]]] = ...) -> None: ...

class PolygonSet(_message.Message):
    __slots__ = ("components",)
    COMPONENTS_FIELD_NUMBER: _ClassVar[int]
    components: _containers.RepeatedCompositeFieldContainer[HolePolygon]
    def __init__(self, components: _Optional[_Iterable[_Union[HolePolygon, _Mapping]]] = ...) -> None: ...

class HolePolygon(_message.Message):
    __slots__ = ("outer", "inners")
    OUTER_FIELD_NUMBER: _ClassVar[int]
    INNERS_FIELD_NUMBER: _ClassVar[int]
    outer: Polygon
    inners: _containers.RepeatedCompositeFieldContainer[Polygon]
    def __init__(self, outer: _Optional[_Union[Polygon, _Mapping]] = ..., inners: _Optional[_Iterable[_Union[Polygon, _Mapping]]] = ...) -> None: ...

class Polyline(_message.Message):
    __slots__ = ("width", "points")
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    POINTS_FIELD_NUMBER: _ClassVar[int]
    width: float
    points: _containers.RepeatedCompositeFieldContainer[Point]
    def __init__(self, width: _Optional[float] = ..., points: _Optional[_Iterable[_Union[Point, _Mapping]]] = ...) -> None: ...

class ArcPolyline(_message.Message):
    __slots__ = ("width", "elements")
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    ELEMENTS_FIELD_NUMBER: _ClassVar[int]
    width: float
    elements: _containers.RepeatedCompositeFieldContainer[Element]
    def __init__(self, width: _Optional[float] = ..., elements: _Optional[_Iterable[_Union[Element, _Mapping]]] = ...) -> None: ...

class Circle(_message.Message):
    __slots__ = ("center", "radius")
    CENTER_FIELD_NUMBER: _ClassVar[int]
    RADIUS_FIELD_NUMBER: _ClassVar[int]
    center: Point
    radius: float
    def __init__(self, center: _Optional[_Union[Point, _Mapping]] = ..., radius: _Optional[float] = ...) -> None: ...

class Element(_message.Message):
    __slots__ = ("point", "arc")
    POINT_FIELD_NUMBER: _ClassVar[int]
    ARC_FIELD_NUMBER: _ClassVar[int]
    point: Point
    arc: Arc
    def __init__(self, point: _Optional[_Union[Point, _Mapping]] = ..., arc: _Optional[_Union[Arc, _Mapping]] = ...) -> None: ...

class ArcPolygon(_message.Message):
    __slots__ = ("elements",)
    ELEMENTS_FIELD_NUMBER: _ClassVar[int]
    elements: _containers.RepeatedCompositeFieldContainer[Element]
    def __init__(self, elements: _Optional[_Iterable[_Union[Element, _Mapping]]] = ...) -> None: ...

class EmptyShape(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Text(_message.Message):
    __slots__ = ("string", "size", "anchor", "pose")
    STRING_FIELD_NUMBER: _ClassVar[int]
    SIZE_FIELD_NUMBER: _ClassVar[int]
    ANCHOR_FIELD_NUMBER: _ClassVar[int]
    POSE_FIELD_NUMBER: _ClassVar[int]
    string: str
    size: float
    anchor: _enums_pb2.Anchor
    pose: Pose
    def __init__(self, string: _Optional[str] = ..., size: _Optional[float] = ..., anchor: _Optional[_Union[_enums_pb2.Anchor, str]] = ..., pose: _Optional[_Union[Pose, _Mapping]] = ...) -> None: ...

class Union(_message.Message):
    __slots__ = ("shapes",)
    SHAPES_FIELD_NUMBER: _ClassVar[int]
    shapes: _containers.RepeatedCompositeFieldContainer[Shape]
    def __init__(self, shapes: _Optional[_Iterable[_Union[Shape, _Mapping]]] = ...) -> None: ...

class Pose(_message.Message):
    __slots__ = ("center", "angle", "flipx")
    CENTER_FIELD_NUMBER: _ClassVar[int]
    ANGLE_FIELD_NUMBER: _ClassVar[int]
    FLIPX_FIELD_NUMBER: _ClassVar[int]
    center: Point
    angle: float
    flipx: bool
    def __init__(self, center: _Optional[_Union[Point, _Mapping]] = ..., angle: _Optional[float] = ..., flipx: bool = ...) -> None: ...
