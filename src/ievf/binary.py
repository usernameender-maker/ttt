"""IEVF Binary Core 1.0: canonical unsigned 16-bit state and reversible views.

This module defines representation only. It does not define universal meanings,
error correction, cryptographic authenticity, or physical communication claims.
"""

from __future__ import annotations

from dataclasses import dataclass

WIDTH = 16
MASK = (1 << WIDTH) - 1
STATE_COUNT = 1 << WIDTH
PROTOCOL_VERSION = 1


def require_u16(value: int) -> int:
    """Return a valid unsigned 16-bit integer; reject bool and coercions."""
    if type(value) is not int or not 0 <= value <= MASK:
        raise ValueError("state must be an unsigned 16-bit integer")
    return value


def complement(value: int) -> int:
    """Bitwise complement within 16 bits (equivalent to 65535 - value)."""
    return require_u16(value) ^ MASK


def reverse_bits(value: int) -> int:
    """Reverse the order of the 16 bits (bit 15 becomes bit 0)."""
    value = require_u16(value)
    result = 0
    for _ in range(WIDTH):
        result = (result << 1) | (value & 1)
        value >>= 1
    return result


def gray_encode(value: int) -> int:
    """Encode an unsigned state to reflected binary Gray code (not ECC)."""
    value = require_u16(value)
    return value ^ (value >> 1)


def gray_decode(value: int) -> int:
    """Invert reflected binary Gray encoding by cumulative XOR."""
    value = require_u16(value)
    result = value
    shift = 1
    while shift < WIDTH:
        result ^= result >> shift
        shift <<= 1
    return result & MASK


def to_signed(value: int) -> int:
    """Interpret the same 16-bit pattern as two's-complement signed integer."""
    value = require_u16(value)
    return value if value < (1 << (WIDTH - 1)) else value - STATE_COUNT


def from_signed(value: int) -> int:
    """Encode a signed two's-complement integer as its unsigned bit pattern."""
    if type(value) is not int or not -(1 << 15) <= value < (1 << 15):
        raise ValueError("signed value must be in [-32768, 32767]")
    return value & MASK


def twos_complement_negate(value: int) -> int:
    """Negate modulo 2^16; distinct from bitwise complement."""
    return (-require_u16(value)) & MASK


def hamming_distance(left: int, right: int) -> int:
    """Count differing bit positions in two unsigned 16-bit states."""
    return (require_u16(left) ^ require_u16(right)).bit_count()


def encode_bytes(value: int) -> bytes:
    """Serialize the canonical state as exactly two big-endian bytes."""
    return require_u16(value).to_bytes(2, byteorder="big", signed=False)


def decode_bytes(data: bytes) -> int:
    """Decode exactly two bytes as a canonical unsigned big-endian state."""
    if not isinstance(data, bytes) or len(data) != 2:
        raise ValueError("expected exactly two bytes")
    return int.from_bytes(data, byteorder="big", signed=False)


@dataclass(frozen=True)
class BinaryState:
    """Canonical word plus explicit semantic type and protocol version.

    ``state_type`` is a caller-defined namespace. The same value may mean
    different things under different types; no global interpretation is
    implied. Derived views never replace ``value``.
    """

    value: int
    state_type: str = "opaque"
    version: int = PROTOCOL_VERSION

    def __post_init__(self) -> None:
        require_u16(self.value)
        if not isinstance(self.state_type, str) or not self.state_type.strip():
            raise ValueError("state_type must be a non-empty string")
        if type(self.version) is not int or self.version != PROTOCOL_VERSION:
            raise ValueError("unsupported binary core version")

    @property
    def bits(self) -> str:
        return f"{self.value:016b}"

    @property
    def signed(self) -> int:
        return to_signed(self.value)

    @property
    def negative_orientation(self) -> int:
        return complement(self.value)

    @property
    def reversed_orientation(self) -> int:
        return reverse_bits(self.value)

    @property
    def gray(self) -> int:
        return gray_encode(self.value)

    @property
    def canonical_bytes(self) -> bytes:
        return encode_bytes(self.value)


def verify_exhaustively() -> dict[str, int | bool]:
    """Check every state and bijection/involution invariants deterministically."""
    seen_gray = bytearray(STATE_COUNT)
    for value in range(STATE_COUNT):
        comp = complement(value)
        reversed_value = reverse_bits(value)
        gray = gray_encode(value)
        if complement(comp) != value:
            raise AssertionError("complement involution failed")
        if reverse_bits(reversed_value) != value:
            raise AssertionError("reversal involution failed")
        if complement(reversed_value) != reverse_bits(comp):
            raise AssertionError("complement and reversal do not commute")
        if gray_decode(gray) != value:
            raise AssertionError("Gray round trip failed")
        if decode_bytes(encode_bytes(value)) != value:
            raise AssertionError("byte round trip failed")
        if from_signed(to_signed(value)) != value:
            raise AssertionError("signed interpretation round trip failed")
        if seen_gray[gray]:
            raise AssertionError("Gray encoding is not injective")
        seen_gray[gray] = 1
    return {
        "states_checked": STATE_COUNT,
        "distinct_gray_representations": sum(seen_gray),
        "complement_involution": True,
        "reversal_involution": True,
        "transform_commutation": True,
        "gray_bijection": True,
        "byte_round_trip": True,
        "signed_round_trip": True,
    }


__all__ = [
    "BinaryState", "MASK", "PROTOCOL_VERSION", "STATE_COUNT", "WIDTH",
    "complement", "decode_bytes", "encode_bytes", "from_signed",
    "gray_decode", "gray_encode", "hamming_distance", "require_u16",
    "reverse_bits", "to_signed", "twos_complement_negate", "verify_exhaustively",
]
