"""Validated 16-bit state representation."""

STATE_BITS = 16
STATE_COUNT = 1 << STATE_BITS
MAX_STATE = STATE_COUNT - 1


def encode_state(value: int) -> bytes:
    """Encode an integer state as exactly two unsigned big-endian bytes."""
    if type(value) is not int:
        raise TypeError("state must be an integer")
    if not 0 <= value <= MAX_STATE:
        raise ValueError(f"state must be in range 0..{MAX_STATE}")
    return value.to_bytes(2, byteorder="big", signed=False)


def decode_state(data: bytes | bytearray | memoryview) -> int:
    """Decode exactly two bytes as an unsigned big-endian state."""
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError("state encoding must be bytes-like")
    encoded = bytes(data)
    if len(encoded) != 2:
        raise ValueError("state encoding must contain exactly two bytes")
    return int.from_bytes(encoded, byteorder="big", signed=False)
