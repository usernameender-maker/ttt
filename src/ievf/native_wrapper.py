"""Optional wrapper for the native 2-D matrix kernel.

NumPy is only required when this wrapper is used. Missing native support may
fall back to NumPy only when allowed; ``require_native=True`` is fail-closed.
"""

from __future__ import annotations

try:
    from . import _tve1_native
except (ImportError, OSError) as exc:
    # OSError also covers a present extension whose dependent runtime library
    # (for example the OpenMP runtime) cannot be loaded.
    _tve1_native = None
    _NATIVE_IMPORT_ERROR = exc
else:
    _NATIVE_IMPORT_ERROR = None


class NativeCore:
    """2-D matrix multiplication wrapper with explicit native/fallback mode."""

    def __init__(self, *, require_native: bool = False, allow_fallback: bool = True) -> None:
        if require_native and _tve1_native is None:
            raise RuntimeError(
                "IEVF native extension is unavailable; install native requirements and run python build_native.py"
            ) from _NATIVE_IMPORT_ERROR
        if _tve1_native is None and not allow_fallback:
            raise RuntimeError(
                "Fallback is disabled, but the native extension is unavailable."
            ) from _NATIVE_IMPORT_ERROR

        self.use_native = _tve1_native is not None
        self.allow_fallback = allow_fallback
        self.contraction_count = 0

    def contract(self, tensor_a, tensor_b):
        """Multiply two 2-D arrays; count only successful operations."""
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
            # This can occur only if module state is changed after construction.
            raise RuntimeError("native extension is unavailable and fallback is disabled") from _NATIVE_IMPORT_ERROR

        self.contraction_count += 1
        return result
