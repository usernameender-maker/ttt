import itertools
import unittest

from ievf.binary import (
    BinaryState, MASK, STATE_COUNT, complement, decode_bytes, encode_bytes,
    from_signed, gray_decode, gray_encode, hamming_distance, require_u16,
    reverse_bits, to_signed, twos_complement_negate, verify_exhaustively,
)


class BinaryCoreTests(unittest.TestCase):
    def test_strict_unsigned_and_serialization(self):
        for value in (0, 1, 0x1234, MASK):
            self.assertEqual(decode_bytes(encode_bytes(value)), value)
        for bad in (-1, STATE_COUNT, True, 1.0):
            with self.assertRaises(ValueError):
                require_u16(bad)
        for bad in (b"", b"\x00", b"\x00\x00\x00", bytearray(b"\x00\x00")):
            with self.assertRaises(ValueError):
                decode_bytes(bad)

    def test_complement_is_not_twos_complement_negation(self):
        for value in (0, 1, 2, 0x1234, MASK):
            self.assertEqual(complement(value), MASK - value)
            self.assertEqual(twos_complement_negate(value), (-value) & MASK)
        self.assertNotEqual(complement(0), twos_complement_negate(0))

    def test_signed_interpretation_round_trips_boundaries(self):
        for signed in (-32768, -1, 0, 1, 32767):
            self.assertEqual(to_signed(from_signed(signed)), signed)
        for invalid in (-32769, 32768, True):
            with self.assertRaises(ValueError):
                from_signed(invalid)

    def test_exhaustive_core_invariants(self):
        report = verify_exhaustively()
        self.assertEqual(report["states_checked"], 65536)
        self.assertEqual(report["distinct_gray_representations"], 65536)
        self.assertTrue(report["gray_bijection"])

    def test_hamming_distance_is_preserved_by_complement_and_reversal(self):
        samples = (0, 1, 0x1234, 0xAAAA, MASK)
        for left, right in itertools.product(samples, repeat=2):
            expected = hamming_distance(left, right)
            self.assertEqual(hamming_distance(complement(left), complement(right)), expected)
            self.assertEqual(hamming_distance(reverse_bits(left), reverse_bits(right)), expected)
            self.assertEqual(
                hamming_distance(complement(reverse_bits(left)), complement(reverse_bits(right))),
                expected,
            )

    def test_binary_state_keeps_canonical_value_and_type(self):
        state = BinaryState(0xB2C5, state_type="address")
        self.assertEqual(state.bits, "1011001011000101")
        self.assertEqual(state.canonical_bytes, b"\xb2\xc5")
        self.assertEqual(state.value, 0xB2C5)
        with self.assertRaises(ValueError):
            BinaryState(1, version=2)
        with self.assertRaises(ValueError):
            BinaryState(1, state_type=" ")


if __name__ == "__main__":
    unittest.main()
