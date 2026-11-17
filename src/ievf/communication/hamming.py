"""Shortened binary Hamming [5,2,3] code used in initial communication tests.

This is the shortening of a systematic [7,4,3] Hamming code obtained by
fixing two data coordinates to zero and removing those coordinates. A
minimum-distance-3 code corrects every single-bit error. It can detect a
double-bit error when the resulting syndrome is not a single-bit syndrome,
but some two-bit errors alias a single-bit syndrome and may be miscorrected.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

N = 5
K = 2

# Codeword (a, b, a xor b, a, b). Columns are distinct nonzero 3-bit vectors.
PARITY_CHECK_COLUMNS = (0b101, 0b011, 0b001, 0b100, 0b010)
CODEWORDS = tuple(
    tuple(bits)
    for bits in (
        (0, 0, 0, 0, 0),
        (1, 0, 1, 1, 0),
        (0, 1, 1, 0, 1),
        (1, 1, 0, 1, 1),
    )
)


def _bits(values: str | tuple[int, ...] | list[int], length: int) -> tuple[int, ...]:
    if isinstance(values, str):
        if any(c not in "01" for c in values):
            raise ValueError("bit string must contain only 0 and 1")
        result = tuple(int(c) for c in values)
    else:
        result = tuple(values)
        if any(type(bit) is not int or bit not in (0, 1) for bit in result):
            raise ValueError("bits must be integer 0 or 1 values")
    if len(result) != length:
        raise ValueError(f"expected exactly {length} bits")
    return result


def encode(message: str | tuple[int, int] | list[int]) -> tuple[int, ...]:
    """Encode a two-bit message into the [5,2,3] code."""
    a, b = _bits(message, K)
    return (a, b, a ^ b, a, b)


def syndrome(word: str | tuple[int, ...] | list[int]) -> int:
    """Return the 3-bit syndrome H r^T, with columns in transmitted order."""
    bits = _bits(word, N)
    result = 0
    for bit, column in zip(bits, PARITY_CHECK_COLUMNS):
        if bit:
            result ^= column
    return result


@dataclass(frozen=True)
class DecodeResult:
    received: tuple[int, ...]
    corrected: tuple[int, ...] | None
    message: tuple[int, int] | None
    syndrome: int
    status: str
    corrected_position: int | None = None


def decode(received: str | tuple[int, ...] | list[int]) -> DecodeResult:
    """Decode by syndrome correction, guaranteed for zero or one bit error.

    If the syndrome is not a column of H, the error is detected but not
    corrected. A multi-bit pattern can alias a single-bit syndrome; callers
    must not interpret a successful correction as proof that no such pattern
    occurred.
    """
    word = _bits(received, N)
    syn = syndrome(word)
    if syn == 0:
        corrected_word = word
        position = None
        status = "clean"
    else:
        try:
            position = PARITY_CHECK_COLUMNS.index(syn)
        except ValueError:
            return DecodeResult(word, None, None, syn, "detected_uncorrectable")
        mutable = list(word)
        mutable[position] ^= 1
        corrected_word = tuple(mutable)
        if syndrome(corrected_word) != 0:
            return DecodeResult(word, None, None, syn, "detected_uncorrectable")
        status = "corrected_single_bit"
    message = (corrected_word[0], corrected_word[1])
    if encode(message) != corrected_word:
        return DecodeResult(word, None, None, syn, "detected_uncorrectable")
    return DecodeResult(word, corrected_word, message, syn, status, position)


def hamming_distance(left: str | tuple[int, ...], right: str | tuple[int, ...]) -> int:
    a = _bits(left, len(left))
    b = _bits(right, len(right),)
    if len(a) != len(b):
        raise ValueError("words must have equal lengths")
    return sum(x != y for x, y in zip(a, b))


def minimum_distance(words: tuple[tuple[int, ...], ...] = CODEWORDS) -> int:
    return min(sum(a != b for a, b in zip(x, y)) for x, y in combinations(words, 2))


def verify_code() -> dict[str, int | bool]:
    """Exhaustively check the four codewords and their minimum distance."""
    encoded = tuple(encode((a, b)) for a in (0, 1) for b in (0, 1))
    return {
        "codeword_count": len(set(encoded)),
        "all_zero_syndrome": all(syndrome(word) == 0 for word in encoded),
        "minimum_distance": minimum_distance(encoded),
        "valid": len(set(encoded)) == 4 and minimum_distance(encoded) == 3,
    }
