"""IEVF core primitives.

This package currently provides a 16-bit state codec, canonical JSON,
content-addressed evidence records, and a hash-linked JSONL audit ledger.
It is a small prototype, not the complete IEVF research system.
"""

from .state import STATE_BITS, STATE_COUNT, decode_state, encode_state

__all__ = ["STATE_BITS", "STATE_COUNT", "decode_state", "encode_state"]
__version__ = "0.1.0"
