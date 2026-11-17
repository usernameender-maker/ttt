import unittest

import numpy as np

from ievf.native_wrapper import NativeCore


class NativeContractTests(unittest.TestCase):
    def setUp(self):
        self.core = NativeCore(require_native=True)

    def test_native_matches_numpy_for_matrix_product(self):
        rng = np.random.default_rng(20261117)
        a = rng.standard_normal((17, 9))
        b = rng.standard_normal((9, 13))
        actual = self.core.contract(a, b)
        np.testing.assert_allclose(actual, a @ b, rtol=1e-12, atol=1e-12)

    def test_non_contiguous_inputs_are_supported(self):
        a = np.arange(60.0).reshape(10, 6)[::2, :]
        b = np.arange(48.0).reshape(6, 8)[:, ::2]
        np.testing.assert_allclose(self.core.contract(a, b), a @ b, rtol=1e-12, atol=1e-12)

    def test_shape_contract_is_explicit(self):
        with self.assertRaisesRegex(ValueError, "2-D"):
            self.core.contract(np.ones((2, 2, 2)), np.ones((2, 2)))
        with self.assertRaisesRegex(ValueError, "inner"):
            self.core.contract(np.ones((2, 3)), np.ones((4, 2)))

    def test_count_tracks_successful_calls_only(self):
        initial = self.core.contraction_count
        self.core.contract(np.ones((2, 2)), np.ones((2, 2)))
        self.assertEqual(self.core.contraction_count, initial + 1)
        with self.assertRaises(ValueError):
            self.core.contract(np.ones((2, 3)), np.ones((4, 2)))
        self.assertEqual(self.core.contraction_count, initial + 1)


if __name__ == "__main__":
    unittest.main()
