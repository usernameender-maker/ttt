import itertools
import unittest

from ievf.communication import hamming
from ievf.communication.dual_orientation import (
    compare_orientations, complement, distance, negative_align, negative_encode,
    positive_encode, reverse,
)


class ShortenedHammingTests(unittest.TestCase):
    def test_all_messages_encode_and_decode(self):
        for message in itertools.product((0, 1), repeat=2):
            word = hamming.encode(message)
            result = hamming.decode(word)
            self.assertEqual(result.message, message)
            self.assertEqual(result.status, "clean")

    def test_all_single_bit_errors_correct(self):
        for message in itertools.product((0, 1), repeat=2):
            codeword = hamming.encode(message)
            for position in range(5):
                received = list(codeword)
                received[position] ^= 1
                result = hamming.decode(received)
                self.assertEqual(result.corrected, codeword)
                self.assertEqual(result.message, message)
                self.assertEqual(result.status, "corrected_single_bit")

    def test_exhaustive_code_properties(self):
        result = hamming.verify_code()
        self.assertTrue(result["valid"])
        self.assertEqual(result["codeword_count"], 4)
        self.assertEqual(result["minimum_distance"], 3)

    def test_two_bit_detection_when_syndrome_does_not_alias(self):
        detected = 0
        for pair in itertools.combinations(range(5), 2):
            word = [0] * 5
            for position in pair:
                word[position] = 1
            decoded = hamming.decode(word)
            if decoded.status == "detected_uncorrectable":
                detected += 1
        self.assertGreater(detected, 0)

    def test_bad_width_and_nonbinary_input_rejected(self):
        with self.assertRaises(ValueError):
            hamming.encode("010")
        with self.assertRaises(ValueError):
            hamming.decode("0x000")


class DualOrientationTests(unittest.TestCase):
    def test_complement_reversal_and_combined_transforms(self):
        frame = "1011001"
        self.assertEqual(complement(complement(frame)), frame)
        self.assertEqual(reverse(reverse(frame)), frame)
        self.assertEqual(reverse(complement(frame)), complement(reverse(frame)))

    def test_negative_orientation_aligns(self):
        message = "10101"
        positive = positive_encode(message)
        negative = negative_encode(message)
        comparison = compare_orientations(positive, negative)
        self.assertEqual(negative_align(negative), positive)
        self.assertEqual(comparison.aligned_distance, 0)

    def test_isometries_preserve_hamming_distance_exhaustively(self):
        words = ["".join(bits) for bits in itertools.product("01", repeat=4)]
        for left in words:
            for right in words:
                d = distance(left, right)
                self.assertEqual(distance(complement(left), complement(right)), d)
                self.assertEqual(distance(reverse(left), reverse(right)), d)
                self.assertEqual(distance(reverse(complement(left)), reverse(complement(right))), d)

    def test_transformations_reject_invalid_frames(self):
        with self.assertRaises(ValueError):
            complement("101x")


if __name__ == "__main__":
    unittest.main()
