import unittest
from unittest.mock import patch

try:
    import numpy as np
except ImportError as exc:
    raise unittest.SkipTest("native contract tests require the optional NumPy dependency") from exc

from ievf.native_wrapper import NativeCore

# The repository's default wheel and unit-test workflow intentionally do not
# include native build requirements. Skip here when the extension was not built;
# native CI separately builds/imports it before test discovery, so this cannot
# turn a native CI build failure into a pass.
try:
    NativeCore(require_native=True)
except RuntimeError as exc:
    raise unittest.SkipTest(f"native extension not built: {exc}") from exc


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

    def test_inputs_are_converted_to_float64(self):
        a = np.array([[1, 2], [3, 4]], dtype=np.int32)
        b = np.array([[2], [1]], dtype=np.float32)
        actual = self.core.contract(a, b)
        self.assertEqual(actual.dtype, np.float64)
        np.testing.assert_allclose(actual, a @ b)

    def test_empty_matrix_dimensions(self):
        actual = self.core.contract(np.empty((0, 3)), np.empty((3, 2)))
        self.assertEqual(actual.shape, (0, 2))
        empty_inner = self.core.contract(np.empty((2, 0)), np.empty((0, 4)))
        self.assertEqual(empty_inner.shape, (2, 4))
        np.testing.assert_array_equal(empty_inner, np.zeros((2, 4)))

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

    def test_strict_native_mode_fails_closed(self):
        with patch("ievf.native_wrapper._tve1_native", None):
            with self.assertRaisesRegex(RuntimeError, "native extension is unavailable"):
                NativeCore(require_native=True)
            with self.assertRaisesRegex(RuntimeError, "Fallback is disabled"):
                NativeCore(allow_fallback=False)

    def test_fallback_is_available_only_when_explicitly_permitted(self):
        with patch("ievf.native_wrapper._tve1_native", None):
            core = NativeCore(allow_fallback=True)
            actual = core.contract(np.array([[2.0]]), np.array([[3.0]]))
            np.testing.assert_array_equal(actual, np.array([[6.0]]))
            self.assertEqual(core.contraction_count, 1)


if __name__ == "__main__":
    unittest.main()
