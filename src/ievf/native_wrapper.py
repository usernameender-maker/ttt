"""Optional wrapper for the native 2-D matrix kernel.

NumPy is only required when this wrapper is used. If the extension is missing,
operations may use NumPy when ``allow_fallback=True``; callers and tests can
require native execution explicitly with ``require_native=True``.
"""

from __future__ import annotations

try:
    from . import _tve1_native
except ImportError as exc:
    _tve1_native = None
    _NATIVE_IMPORT_ERROR = exc
else:
    _NATIVE_IMPORT_ERROR = None


class NativeCore:
    """2-D matrix multiplication wrapper with explicit native/fallback mode."""

    def __init__(self, *, require_native: bool = False, allow_fallback: bool = True) -> None:
        if require_native and _tve1_native is None:
            raise RuntimeError("IEVF native extension is unavailable; run python build_native.py") from _NATIVE_IMPORT_ERROR
        self.use_native = _tve1_native is not None
        self.allow_fallback = allow_fallback
        self.contraction_count = 0

    def contract(self, tensor_a, tensor_b):
        """Multiply two 2-D arrays. Successful calls increment the counter."""
        try:
            import numpy as np
        except ImportError as exc:
            raise RuntimeError("NumPy is required to use NativeCore") from exc

        a = np.asarray(tensor_a, dtype=np.float64)
        b = np.asarray(tensor_b, dtype=np.float64)
        if a.ndim != 2 or b.ndim != 2:
            raise ValueError("contract accepts only 2-D arrays")
        if a.shape[1] != b.shape[0]:
            raise ValueError("inner matrix dimensions must match")

        if self.use_native:
            result = _tve1_native.contract_matrices(a, b)
        elif self.allow_fallback:
            result = a @ b
        else:
            raise RuntimeError("native extension is unavailable and fallback is disabled")
        self.contraction_count += 1
        return result
