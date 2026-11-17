# IEVF Binary Core 1.0

The existing `ievf.state` codec remains unchanged and continues to serialize
unsigned values as two big-endian bytes. `ievf.binary` adds explicit views and
transformations without changing that API.

## Canonical contract

- A core word is an integer from 0 through 65,535 (exactly 16 bits).
- Bit 15 is most significant; serialization is exactly two big-endian bytes.
- Zero is an ordinary valid state. Invalid values raise errors; no numeric
  sentinel represents missing data.
- `BinaryState` couples the canonical value to an explicit semantic `state_type`
  and protocol `version`. The same bit pattern has no universal meaning across
  types. Derived views never replace its canonical `value`.
- Signed interpretation is a separate two's-complement view.
- Bitwise complement is `x xor 65535` (also `65535 - x`); signed negation is
  `(-x) mod 65536`, or complement plus one. They differ at zero.
- Reversal reverses the 16 bit positions. Gray encoding is a reversible code
  mapping, not an error-correcting code.
- XOR is bitwise addition modulo two; Hamming distance counts differing bits.

## Integrity boundary

Exhaustive verification enumerates all 65,536 inputs to test complement and
reversal involutions, their commutation, Gray round trips and uniqueness,
byte round trips, and signed-view round trips. These mathematical checks prove
properties of this implementation over its finite input domain. They do not
prove channel reliability, authenticity, cryptographic security, or physical
behavior. A checksum or digest elsewhere in the prototype similarly proves
integrity only relative to a trusted expected value.

Run the checks with:

```sh
python -m unittest discover -s tests -p 'test_binary_core.py' -v
```
