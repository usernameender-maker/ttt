"""Complement/reversal orientation transforms for classical binary frames.

Bitwise complement and coordinate reversal are Hamming isometries: for each
coordinate, complement preserves equality/inequality, and a permutation only
reorders the terms in the distance sum. This does not imply a transformed
word can be decoded with an unchanged parity-check matrix; align to the
original coordinate orientation before decoding, or transform H accordingly.
"""

from __future__ import annotations

from dataclasses import dataclass


def _validate(frame: str) -> str:
    if not isinstance(frame, str) or any(bit not in "01" for bit in frame):
        raise ValueError("frame must be a binary string")
    return frame


def complement(frame: str) -> str:
    return _validate(frame).translate(str.maketrans("01", "10"))


def reverse(frame: str) -> str:
    return _validate(frame)[::-1]


def positive_encode(message: str) -> str:
    """Return an identity-orientation binary frame (classical bits only)."""
    return _validate(message)


def negative_encode(message: str) -> str:
    """Return the bitwise-complement orientation of a binary frame."""
    return complement(message)


def negative_align(frame: str, *, reverse_order: bool = False) -> str:
    """Convert negative orientation to positive; optionally undo reversal."""
    aligned = complement(frame)
    return reverse(aligned) if reverse_order else aligned


@dataclass(frozen=True)
class OrientationComparison:
    positive: str
    negative: str
    aligned_negative: str
    raw_distance: int
    aligned_distance: int


def compare_orientations(positive: str, negative: str) -> OrientationComparison:
    p = _validate(positive)
    n = _validate(negative)
    if len(p) != len(n):
        raise ValueError("orientation frames must have equal lengths")
    aligned = negative_align(n)
    return OrientationComparison(
        positive=p,
        negative=n,
        aligned_negative=aligned,
        raw_distance=sum(a != b for a, b in zip(p, n)),
        aligned_distance=sum(a != b for a, b in zip(p, aligned)),
    )


def distance(left: str, right: str) -> int:
    a, b = _validate(left), _validate(right)
    if len(a) != len(b):
        raise ValueError("frames must have equal lengths")
    return sum(x != y for x, y in zip(a, b))
