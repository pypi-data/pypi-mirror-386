"""
Coordinate system transforms
============================

This module provides 2D transforms used in the JITX system to position objects
within the design tree.
"""

from __future__ import annotations
from typing import Literal, Self, overload
from collections.abc import Iterator
from math import radians, cos, sin, atan2, sqrt

from jitx.shapes import Shape, ShapeGeometry

type GridPoint = tuple[int, int]
"""Grid point coordinates as (x, y) integer tuple."""

type Point = tuple[float | int, float | int]
"""2D point coordinates as (x, y) tuple."""

type Vec3D = tuple[float | int, float | int, float | int]
"""3D vector as (x, y, z) tuple."""


class Transform:
    """Transform represents a translate * rotate * scale (TRS) transform in
    that order, so scale is applied first, then rotate, and finally translate.
    Note that non-unit scale will typically not carry over into component and
    circuit placement, and while it can be used to compute a placement before
    it's applied, the results may be unexpected, and should be avoided. Also
    note that because the transforms are internally stored as decomposed values,
    a non-uniform scale cannot be applied to another transform, as this would
    result in a shear.

    Constructing a transform directly is typically only needed in niche cases,
    and more often than not it is better to use member methods of various
    objects (in JITX typically called :py:meth:`~jitx.shapes.Shape.at`) to
    transform the object.

    Args:
        translate: Translation as (x, y).
        rotate: Optional rotation angle in degrees.
        scale: Optional scale factors as (x, y). If a single value is
            provided, then the same value is used for both x and y.
    """

    __slots__ = ("_translate", "_rotate", "_scale")

    _translate: Point
    """Translation as (x, y)."""
    _rotate: float
    """Rotation angle in degrees."""
    _scale: tuple[float, float]
    """Scale factors as (x_scale, y_scale)."""

    def __init__(
        self,
        translate: Point,
        rotate: float = 0,
        scale: float | tuple[float, float] = (1, 1),
    ):
        self._translate = translate
        self._rotate = rotate
        if not isinstance(scale, tuple):
            scale = (scale, scale)
        self._scale = scale

    def __repr__(self):
        return f"Transform({self._translate}, {self._rotate}, {self._scale})"

    def clone(self):
        return self.__class__(self._translate, self._rotate, self._scale)

    @property
    def trs(self):
        return self._translate, self._rotate, self._scale

    @property
    def translation(self) -> Point:
        """The transform's translation as (x, y)."""
        return self._translate

    @property
    def rotation(self) -> float:
        """The transform's rotation angle in degrees."""
        return self._rotate

    def __eq__(self, other):
        return (
            isinstance(other, Transform)
            and self._translate == other._translate
            and self._rotate == other._rotate
            and self._scale == other._scale
        )

    @overload
    def __mul__(self, other: Transform) -> Transform: ...
    @overload
    def __mul__(self, other: Point) -> Point: ...
    @overload
    def __mul__(self, other: Vec2D) -> Vec2D: ...
    @overload
    def __mul__[T: ShapeGeometry](self, other: Shape[T]) -> Shape[T]: ...

    def __mul__(
        self, other: Transform | Point | Shape | Vec2D
    ) -> Transform | Point | Shape | Vec2D:
        # translate * rotate * scale * object
        if isinstance(other, Transform):
            return self.__apply_to_transform(other)
        elif isinstance(other, tuple):
            if len(other) == 2:
                return self.__apply_to_point(other)
            else:
                return NotImplemented
        elif isinstance(other, Vec2D):
            return self.__apply_to_vec2d(other)
        elif isinstance(other, Shape):
            if not other.transform:
                return Shape(other.geometry, self.clone())
            else:
                return Shape(other.geometry, self.__apply_to_transform(other.transform))
        else:
            return NotImplemented

    def __imul__(self, other: Transform):
        xform = self.__apply_to_transform(other)
        self._translate = xform._translate
        self._rotate = xform._rotate
        self._scale = xform._scale

    def __apply_to_transform(self, xf: Transform) -> Transform:
        sx, sy = self._scale
        osx, osy = xf._scale
        r = xf._rotate
        if sx != sy and abs(sx) != abs(sy) and r != 0:
            raise ValueError(
                "Unable to apply a non-uniform scale to an existing transform"
            )
        if sx * sy < 0:
            r = -r
        return self.__class__(
            self.__apply_to_point(xf._translate),
            self._rotate + r,
            (sx * osx, sy * osy),
        )._post_mul(self, xf)

    def _post_mul(self, left: Transform, right: Transform):
        return right._post_rmul(self, left)

    def _post_rmul(self, result: Transform, left: Transform):
        return result

    def __apply_to_point(self, pt: Point) -> Point:
        x, y = pt
        tx, ty = self._translate
        r = self._rotate
        sx, sy = self._scale
        if r < 0:
            r += 360
        if r == 0:
            return (tx + sx * x, ty + sy * y)
        if r == 90:
            return (tx - sy * y, ty + sx * x)
        if r == 180:
            return (tx - sx * x, ty - sy * y)
        if r == 270:
            return (tx + sy * y, ty - sx * x)
        a = radians(r)
        cosa = cos(a)
        sina = sin(a)
        return (tx + sx * x * cosa - sy * y * sina, ty + sx * x * sina + sy * y * cosa)

    def __apply_to_vec2d(self, v: Vec2D) -> Point:
        # same as point, but without the translation
        x, y = v.x, v.y
        r = self._rotate
        sx, sy = self._scale
        if r < 0:
            r += 360
        if r == 0:
            return (sx * x, +sy * y)
        if r == 90:
            return (-sy * y, +sx * x)
        if r == 180:
            return (-sx * x, -sy * y)
        if r == 270:
            return (+sy * y, -sx * x)
        a = radians(r)
        cosa = cos(a)
        sina = sin(a)
        return (sx * x * cosa - sy * y * sina, sx * x * sina + sy * y * cosa)

    def inverse(self):
        x, y = self._translate
        r = self._rotate
        sx, sy = self._scale

        return (
            Transform.scale(1 / sx, 1 / sy)
            * Transform.rotate(-r)
            * Transform.translate(-x, -y)
        )

    def __invert__(self):
        return self.inverse()

    @overload
    def matrix2x3(
        self, *, row_major: Literal[False] = False, flat: Literal[False] = False
    ) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]: ...
    @overload
    def matrix2x3(
        self, *, row_major: Literal[True], flat: Literal[False] = False
    ) -> tuple[tuple[float, float, float], tuple[float, float, float]]: ...
    @overload
    def matrix2x3(
        self, *, row_major: bool = False, flat: Literal[True]
    ) -> tuple[float, float, float, float, float, float]: ...
    def matrix2x3(self, *, row_major=False, flat=False):
        tx, ty = self._translate
        alpha = radians(self._rotate)
        ca = cos(alpha)
        sa = sin(alpha)
        sx, sy = self._scale
        m11 = ca * sx
        m21 = sa * sx
        m12 = -sa * sy
        m22 = ca * sy
        m13 = tx
        m23 = ty
        if not row_major:
            if flat:
                # fmt: off
                return (
                    m11, m21,
                    m12, m22,
                    m13, m23,
                )
                # fmt: on
            else:
                # fmt: off
                return (
                    (m11, m21),
                    (m12, m22),
                    (m13, m23),
                )
                # fmt: on
        else:
            if flat:
                # fmt: off
                return (
                    m11, m12, m13,
                    m21, m22, m23,
                )
                # fmt: on
            else:
                # fmt: off
                return (
                    (m11, m12, m13),
                    (m21, m22, m23),
                )
                # fmt: on

    @overload
    def matrix3x3(
        self, *, row_major: bool = False, flat: Literal[False] = False
    ) -> tuple[
        tuple[float, float, float],
        tuple[float, float, float],
        tuple[float, float, float],
    ]: ...
    @overload
    def matrix3x3(
        self, *, row_major: bool = False, flat: Literal[True]
    ) -> tuple[float, float, float, float, float, float, float, float, float]: ...
    def matrix3x3(self, *, row_major=False, flat=False):
        m11, m21, m12, m22, m13, m23 = self.matrix2x3(flat=True)
        if not row_major:
            if flat:
                # fmt: off
                return (
                    m11, m21, 0.0,
                    m12, m22, 0.0,
                    m13, m23, 1.0,
                )
                # fmt: on
            else:
                # fmt: off
                return (
                    (m11, m21, 0.0),
                    (m12, m22, 0.0),
                    (m13, m23, 1.0),
                )
                # fmt: on
        else:
            if flat:
                # fmt: off
                return (
                    m11, m12, m13,
                    m21, m22, m23,
                    0.0, 0.0, 1.0,
                )
                # fmt: on
            else:
                # fmt: off
                return (
                    (m11, m12, m13),
                    (m21, m22, m23),
                    (0.0, 0.0, 1.0),
                )
                # fmt: on

    @overload
    @classmethod
    def translate(cls, x: float, y: float, /) -> Self: ...
    @overload
    @classmethod
    def translate(cls, vector: Point, /) -> Self: ...
    @classmethod
    def translate(cls, x: float | Point, y: float | None = None, /):
        if isinstance(x, tuple):
            return cls(x, 0, (1, 1))
        else:
            assert isinstance(y, float | int)
            return cls((x, y), 0, (1, 1))

    @classmethod
    def rotate(cls, angle: float):
        return cls((0, 0), angle, (1, 1))

    @overload
    @classmethod
    def scale(cls, x: float, y: float, /) -> Self: ...
    @overload
    @classmethod
    def scale(cls, uniform: float, /) -> Self: ...
    @classmethod
    def scale(cls, x: float, y: float | None = None, /):
        if y is None:
            y = x
        return cls((0, 0), 0, (x, y))

    @classmethod
    def identity(cls):
        return cls((0, 0), 0, (1, 1))


class ImmutableTransform(Transform):
    __frozen = False

    def __init__(
        self, translate: Point, rotate: float = 0, scale: tuple[float, float] = (1, 1)
    ):
        super().__init__(translate, rotate, scale)
        self.__frozen = True

    def __setattr__(self, attr, value):
        if self.__frozen:
            raise ValueError("Transform is immutable")
        super().__setattr__(attr, value)


IDENTITY = ImmutableTransform.identity()


class Vec2D:
    """A basic 2D vector class. Used internally for some calculations, not typically used in public APIs."""

    __slots__ = ("_x", "_y")

    _x: float
    _y: float

    def __init__(self, x: float, y: float):
        self._x = x
        self._y = y

    def __repr__(self):
        return f"Vec2D({self._x}, {self._y})"

    @overload
    def __add__(self, other: Vec2D) -> Vec2D: ...
    @overload
    def __add__(self, other: Point) -> Point: ...
    def __add__(self, other) -> Vec2D | Point:
        # vector + vector = vector
        # point + vector = point
        if isinstance(other, tuple):
            return (self._x + other[0], self._y + other[1])
        elif isinstance(other, Vec2D):
            return Vec2D(self._x + other._x, self._y + other._y)
        else:
            return NotImplemented

    @overload
    def __radd__(self, other: Vec2D) -> Vec2D: ...
    @overload
    def __radd__(self, other: Point) -> Point: ...
    def __radd__(self, other) -> Vec2D | Point:
        return self.__add__(other)

    def __sub__(self, other) -> Vec2D:
        # vector - vector = vector
        # vector - point is undefined
        # point - point = vector, but can't be implemented since point is a tuple
        if isinstance(other, Vec2D):
            return Vec2D(self._x - other._x, self._y - other._y)
        else:
            return NotImplemented

    @overload
    def __rsub__(self, other: Vec2D) -> Vec2D: ...
    @overload
    def __rsub__(self, other: Point) -> Point: ...
    def __rsub__(self, other) -> Vec2D | Point:
        # point - vector = (-vector) + point = point
        return (-self).__add__(other)

    def __mul__(self, other: float) -> Vec2D:
        return Vec2D(self._x * other, self._y * other)

    def __rmul__(self, other: float) -> Vec2D:
        return Vec2D(self._x * other, self._y * other)

    def __truediv__(self, other: float) -> Vec2D:
        return Vec2D(self._x / other, self._y / other)

    def __floordiv__(self, other: float) -> Vec2D:
        return Vec2D(self._x // other, self._y // other)

    def __neg__(self) -> Vec2D:
        return Vec2D(-self._x, -self._y)

    def __pos__(self) -> Vec2D:
        return Vec2D(+self._x, +self._y)

    def __abs__(self) -> float:
        return sqrt(self._x**2 + self._y**2)

    def __getitem__(self, index: Literal[0, 1]) -> float:
        if index == 0:
            return self._x
        elif index == 1:
            return self._y
        else:
            raise IndexError("Vec2D index out of range")

    def __iter__(self) -> Iterator[float]:
        return iter((self._x, self._y))

    def __eq__(self, other) -> bool:
        if not isinstance(other, Vec2D):
            return False
        return self._x == other._x and self._y == other._y

    def __lt__(self, other: Vec2D) -> bool:
        return self._x < other._x and self._y < other._y

    def __le__(self, other: Vec2D) -> bool:
        return self._x <= other._x and self._y <= other._y

    def __gt__(self, other: Vec2D) -> bool:
        return self._x > other._x and self._y > other._y

    def __ge__(self, other: Vec2D) -> bool:
        return self._x >= other._x and self._y >= other._y

    def __hash__(self) -> int:
        return hash((self._x, self._y))

    @property
    def x(self) -> float:
        return self._x

    @property
    def y(self):
        return self._y

    @property
    def xy(self) -> tuple[float, float]:
        return self._x, self._y

    @property
    def length(self) -> float:
        return abs(self)

    def normalized(self) -> Vec2D:
        return self / abs(self)

    def dot(self, other: Vec2D) -> float:
        return self.x * other.x + self.y * other.y

    def cross(self, other: Vec2D) -> float:
        """Compute the magnitude of the cross product."""
        return self._x * other._y - self._y * other._x

    def angle(self) -> float:
        """Compute the angle in radians counter-clockwise from the +X axis of this vector"""
        return atan2(self.y, self.x)


def transform_grid_point(xform: Transform, pt: GridPoint) -> GridPoint:
    """Transform a grid point by a transform."""
    x, y = xform * (pt[0], pt[1])
    # Raise error if x or y is not an integer value
    if not x.is_integer() or not y.is_integer():
        raise ValueError("Transform result is not a grid point")
    return (int(x), int(y))
