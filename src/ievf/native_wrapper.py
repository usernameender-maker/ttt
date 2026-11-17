"""Native extension wrapper with deterministic NumPy fallback.

This module intentionally fails fast when a native extension is required, but it
allows a safe fallback path for test and CI execution when no compiled backend is
present. The fallback is not a replacement for the native kernel; it is a
compatibility layer that preserves the repository's validation contract.
"""

from __future__ import annotations

import importlib
from typing import Any

import numpy as np


class NativeCore:
    """Thin wrapper around a compiled backend or a strict NumPy fallback."""

    def __init__(self, require_native: bool = False, *, backend: str | None = None) -> None:
        self.require_native = require_native
        self.use_native = False
        self.backend = backend
        self._native_module = None
        self._native_contract = None
        self.contraction_count = 0
        self._load_backend()

    def _load_backend(self) -> None:
        candidates = [
            self.backend,
            "ievf_native",
            "_ievf_native",
            "ievf._native",
        ]
        seen: set[str] = set()
        for name in candidates:
            if not name or name in seen:
                continue
            seen.add(name)
            try:
                mod = importlib.import_module(name)
            except ImportError:
                continue
            if hasattr(mod, "contract"):
                self._native_module = mod
                self._native_contract = mod.contract
                self.use_native = True
                return
        if self.require_native:
            raise RuntimeError(
                "Native tensor backend is required, but no compatible extension was found. "
                "Build the native module or set require_native=False for the NumPy fallback."
            )

    def contract(self, a: Any, b: Any) -> np.ndarray:
        if self._native_contract is not None:
            output = self._native_contract(a, b)
            self.contraction_count = int(a.shape[0] * a.shape[1] * b.shape[1])
            return np.asarray(output)

        if a.ndim != 2 or b.ndim != 2:
            raise ValueError("NativeCore fallback supports only rank-2 inputs.")

        self.contraction_count = int(a.shape[0] * a.shape[1] * b.shape[1])
        return a @ b
