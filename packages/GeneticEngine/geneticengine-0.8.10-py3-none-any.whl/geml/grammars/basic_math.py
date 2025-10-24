from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from geml.grammars.sgp import Number


@dataclass
class SafeDiv(Number):
    """Safe Division object. If division fails because of a ZeroDivisionError,
    1 is returned.

    Args:
        left  (Number)
        right (Number)

    Returns when evaluated:
        left / right
    """

    left: Number
    right: Number

    def evaluate(self, **kwargs):
        d1 = self.left.evaluate(**kwargs)
        d2 = self.right.evaluate(**kwargs)
        if hasattr(d1, "dtype"):
            if d1.dtype == "O":
                d1 = d1.astype(float)
        if hasattr(d2, "dtype"):
            if d2.dtype == "O":
                d2 = d2.astype(float)
        try:
            with np.errstate(divide="ignore", invalid="ignore"):
                return np.where(abs(d2) < 0.001, np.ones_like(d1), d1 / d2)
        except ZeroDivisionError:
            # In this case we are trying to divide two constants, one of which is 0
            # Return a constant.
            return 1.0

    def __str__(self) -> str:
        return f"({self.left}/{self.right})"


@dataclass
class SafeSqrt(Number):
    """Safe Square Root object. If the number is negative, the square root of
    the positive counterpart of the number is returned.

    Args:
        number (Number)

    Returns when evaluated:
        np.sqrt(number)
    """

    number: Number

    def evaluate(self, **kwargs):
        v = self.number.evaluate(**kwargs)
        return np.sqrt(np.abs(v))

    def __str__(self) -> str:
        return f"np.sqrt(np.abs({self.number}))"


@dataclass
class Sin(Number):
    """Standard Sinus object.

    Args:
        number (Number)

    Returns when evaluated:
        np.sin(number)
    """

    number: Number

    def evaluate(self, **kwargs):
        v = self.number.evaluate(**kwargs)
        return np.sin(v)

    def __str__(self) -> str:
        return f"np.sin({self.number})"


@dataclass
class Tanh(Number):
    """Standard Hyperbolic Tangent object.

    Args:
        number (Number)

    Returns when evaluated:
        np.tanh(number)
    """

    number: Number

    def evaluate(self, **kwargs):
        v = self.number.evaluate(**kwargs)
        return np.tanh(v)

    def __str__(self) -> str:
        return f"np.tanh({self.number})"


@dataclass
class Exp(Number):
    """Standard Exponential object.

    Args:
        number (Number)

    Returns when evaluated:
        np.exp(number)
    """

    number: Number

    def evaluate(self, **kwargs):
        v = self.number.evaluate(**kwargs)
        return np.exp(v)

    def __str__(self) -> str:
        return f"np.exp({self.number})"


@dataclass
class SafeLog(Number):
    """Safe Logarithmic object. If the number is negative, the logarithm of the
    positive counterpart of the number + 1 is returned.

    Args:
        left  (Number)
        right (Number)

    Returns when evaluated:
        np.log(number)
    """

    number: Number

    def evaluate(self, **kwargs):
        v = self.number.evaluate(**kwargs)
        try:
            return np.log(1 + np.abs(v))
        except Exception:
            return 1

    def __str__(self) -> str:
        return f"np.log(1 + np.abs({self.number}))"
