"""
Toleranced values and interval arithmetic
=========================================

This module provides the Toleranced class for representing values
with tolerances and performing interval arithmetic operations.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Self, overload
from .interval import Interval


class Unspecified:
    """:meta private:"""

    def __repr__(self):
        return "Unspecified"


_UNSPECIFIED = Unspecified()


_Unspecified = Unspecified
del Unspecified


class Toleranced(Interval):
    """
    Interval Arithmetic Type for values with tolerances.

    Args:
        typ: Typical value (average/nominal)
        plus: Relative positive increment (max bound, or None for unbounded)
        minus: Relative negative increment (min bound, or None for unbounded),
            If this argument is unspecified, the range will be symmetric.
    """

    typ: float
    plus: float | None
    minus: float | None
    __used_percent: tuple[float, float] | None = None

    @overload
    def __init__(self, typ: float, plusminus: float | None, /): ...
    @overload
    def __init__(self, typ: float, plus: float | None, minus: float | None): ...

    def __init__(
        self,
        typ: float,
        plus: float | None,
        minus: float | None | _Unspecified = _UNSPECIFIED,
    ):
        if isinstance(minus, _Unspecified):
            minus = plus
        self.typ = typ
        self.plus = plus
        self.minus = minus

        assert self.plus is None or self.plus >= 0.0
        assert self.minus is None or self.minus >= 0.0

    def __str__(self):
        # Both bounds present
        typ = self.typ
        plus = self.plus
        minus = self.minus
        if plus == minus:
            if plus is None:
                return f"{typ} ± ∞"
            elif self.__used_percent:
                return f"{typ} ± {self.__used_percent[0]}%"
            return f"{typ} ± {plus}"
        # Only min bound present
        elif self.plus is None:
            return f"Toleranced({self.min_value} <= typ:{self.typ})"
        # Only max bound present
        elif self.minus is None:
            return f"Toleranced(typ:{self.typ} <= {self.max_value})"
        return f"Toleranced({self.min_value} <= {self.typ} <= {self.max_value})"

    def __repr__(self):
        return f"Toleranced({self.typ}, {self.plus}, {self.minus})"

    @property
    def max_value(self) -> float:
        if self.plus is not None:
            return self.typ + self.plus
        raise ValueError("plus must be specified to compute max_value")

    @property
    def min_value(self) -> float:
        if self.minus is not None:
            return self.typ - self.minus
        raise ValueError("minus must be specified to compute min_value")

    def center_value(self) -> float:
        return self.min_value + 0.5 * (self.max_value - self.min_value)

    # Return a value in percentage unit: 2 means 2%
    def plus_percent(self) -> float:
        if self.plus is None:
            raise ValueError("plus must be specified to compute tol+%(Toleranced)")
        if self.typ == 0.0:
            raise ValueError("typ() != 0.0 to compute tol+%(Toleranced)")
        return 100.0 * self.plus / self.typ

    # Return a value in percentage unit: 2 means 2%
    def minus_percent(self) -> float:
        if self.minus is None:
            raise ValueError("minus must be specified to compute tol-%(Toleranced)")
        if self.typ == 0.0:
            raise ValueError("typ() != 0.0 to compute tol-%(Toleranced)")
        return 100.0 * self.minus / self.typ

    def in_range(self, value: float | Toleranced) -> bool:
        if isinstance(value, Toleranced):
            return (
                value.min_value >= self.min_value and value.max_value <= self.max_value
            )
        elif isinstance(value, float | int):
            return self.min_value <= value <= self.max_value
        else:
            raise ValueError("in_range() requires a Toleranced or float value.")

    def range(self) -> float:
        return self.max_value - self.min_value

    def _full_tolerance(self):
        """Return True if typ, plus, and minus are all specified (not None). 0.0 is valid and means exact."""
        return self.plus is not None and self.minus is not None

    # Arithmetic operators
    def __add__(self, other: Toleranced | float) -> Toleranced:
        if isinstance(other, Toleranced):
            if (self.plus is None or self.minus is None) or (
                other.plus is None or other.minus is None
            ):
                raise ValueError(
                    "Toleranced() arithmetic operations require fully specified arguments (None is not allowed, 0.0 is valid)"
                )
            return Toleranced(
                self.typ + other.typ,
                self.plus + other.plus,
                self.minus + other.minus,
            )
        elif isinstance(other, int | float):
            return Toleranced(self.typ + other, self.plus, self.minus)
        return NotImplemented

    def __radd__(self, other: float) -> Toleranced:
        return self.__add__(other)

    def __sub__(self, other: Toleranced | float) -> Toleranced:
        if isinstance(other, Toleranced):
            if (self.plus is None or self.minus is None) or (
                other.plus is None or other.minus is None
            ):
                raise ValueError(
                    "Toleranced() arithmetic operations require fully specified arguments (None is not allowed, 0.0 is valid)"
                )
            return Toleranced(
                self.typ - other.typ,
                self.plus + other.minus,
                self.minus + other.plus,
            )
        elif isinstance(other, int | float):
            return Toleranced(self.typ - other, self.plus, self.minus)
        return NotImplemented

    def __rsub__(self, other: float) -> Toleranced:
        return Toleranced(other, 0.0, 0.0) - self

    def __mul__(self, other: float | Toleranced) -> Toleranced:
        if isinstance(other, Toleranced):
            if (self.plus is None or self.minus is None) or (
                other.plus is None or other.minus is None
            ):
                raise ValueError(
                    "Toleranced() arithmetic operations require fully specified arguments (None is not allowed, 0.0 is valid)"
                )
            typ = self.typ * other.typ
            variants = [
                self.min_value * other.min_value,
                self.min_value * other.max_value,
                self.max_value * other.min_value,
                self.max_value * other.max_value,
            ]
            plus = max(variants) - typ
            minus = typ - min(variants)
            return Toleranced(typ, plus, minus)
        elif isinstance(other, int | float):
            plus = abs(self.plus * other) if self.plus is not None else None
            minus = abs(self.minus * other) if self.minus is not None else None
            return Toleranced(self.typ * other, plus, minus)
        return NotImplemented

    def __rmul__(self, other: float) -> Toleranced:
        return self.__mul__(other)

    def __truediv__(self, other: Toleranced | float) -> Toleranced:
        if isinstance(other, Toleranced):
            if (self.plus is None or self.minus is None) or (
                other.plus is None or other.minus is None
            ):
                raise ValueError(
                    "Toleranced() arithmetic operations require fully specified arguments (None is not allowed, 0.0 is valid)"
                )
            if other.in_range(0.0):
                raise ZeroDivisionError("Cannot divide by zero for Toleranced values.")
            typ = 1.0 / other.typ
            inv = Toleranced(
                typ, 1.0 / other.min_value - typ, typ - 1.0 / other.max_value
            )
            return self * inv
        elif isinstance(other, int | float):
            if other == 0:
                raise ZeroDivisionError("Cannot divide by zero.")
            elif other < 0:
                raise ValueError("Cannot divide Toleranced by negative value.")
            plus = self.plus / other if self.plus is not None else None
            minus = self.minus / other if self.minus is not None else None
            return self.__class__(self.typ / other, plus, minus)
        return NotImplemented

    def __rtruediv__(self, other: float) -> Toleranced:
        return Toleranced.exact(other) / self

    def apply(self, f: Callable[[float], float]) -> Self:
        tv = f(self.typ)
        minv = f(self.min_value)
        maxv = f(self.max_value)
        return self.min_typ_max(minv, tv, maxv)

    # Helper constructors

    @classmethod
    def min_typ_max(
        cls, min_val: float | None, typ_val: float | None, max_val: float | None
    ) -> Self:
        """
        Create a Toleranced value from min, typ, and max values.
        At least two must be specified.
        """
        if typ_val is not None and min_val is not None and max_val is not None:
            if typ_val < min_val or max_val < typ_val:
                raise ValueError("min-typ-max() should be [min] <= [typ] <= [max]")
            return cls(typ_val, max_val - typ_val, typ_val - min_val)
        elif min_val is not None and max_val is not None:
            if max_val < min_val:
                raise ValueError("min-typ-max() should have max >= min.")
            t = min_val + 0.5 * (max_val - min_val)
            return cls(t, max_val - t, t - min_val)
        elif typ_val is not None and min_val is not None:
            if typ_val < min_val:
                raise ValueError("min-typ-max() should have min <= typ")
            return cls(typ_val, None, typ_val - min_val)
        elif typ_val is not None and max_val is not None:
            if typ_val > max_val:
                raise ValueError("min-typ-max() should have typ <= max")
            return cls(typ_val, max_val - typ_val, None)
        else:
            raise ValueError(
                "min-typ-max() should have at least two of min, typ, max values"
            )

    @classmethod
    def min_max(cls, min_val: float, max_val: float) -> Self:
        """Toleranced defined by absolute min and max values."""
        return cls.min_typ_max(min_val, None, max_val)

    @classmethod
    def min_typ(cls, min_val: float, typ_val: float) -> Self:
        """Toleranced defined by an absolute minimum and typical value."""
        return cls.min_typ_max(min_val, typ_val, None)

    @classmethod
    def typ_max(cls, typ_val: float, max_val: float) -> Self:
        """Toleranced defined by an absolute maximum and typical value."""
        return cls.min_typ_max(None, typ_val, max_val)

    @classmethod
    def percent(
        cls, typ: float, plus: float, minus: float | _Unspecified = _UNSPECIFIED
    ) -> Self:
        """Create a Toleranced based on symmetric or assymetric percentages of
        the typical value. If the ``minus`` argument is unspecified, the range
        will be symmetric."""
        if isinstance(minus, _Unspecified):
            minus = plus
        if not (0.0 <= plus <= 100.0):
            raise ValueError("tol+ must be in range 0.0 <= tol+ <= 100.0")
        if not (0.0 <= minus <= 100.0):
            raise ValueError("tol- must be in range 0.0 <= tol- <= 100.0")
        abstyp = abs(typ)
        aplus = abstyp * plus / 100.0
        aminus = abstyp * minus / 100.0
        tol = cls(typ, aplus, aminus)
        tol.__used_percent = plus, minus
        return tol

    @classmethod
    def sym(cls, typ: float, plusminus: float) -> Self:
        """Create a Toleranced with symmetric bounds. Effectively an alias of the two-argument constructor."""
        return cls(typ, plusminus)

    @overload
    @classmethod
    def exact(cls, typ: float) -> Self: ...

    @overload
    @classmethod
    def exact(cls, typ: Toleranced) -> Toleranced: ...

    @classmethod
    def exact(cls, typ: float | Toleranced) -> Self | Toleranced:
        """Create a Toleranced with zero tol+ and tol- (exact value)."""
        if isinstance(typ, Toleranced):
            return typ
        return cls(typ, 0.0)
