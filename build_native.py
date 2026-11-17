"""Build and verify the optional IEVF C++ matrix extension."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
NATIVE_DIR = ROOT / "native"
BUILD_DIR = ROOT / "build" / "native"
PACKAGE_DIR = ROOT / "src" / "ievf"


def main() -> int:
    try:
        cmake_dir = subprocess.check_output(
            [sys.executable, "-m", "pybind11", "--cmakedir"],
            cwd=ROOT,
            text=True,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        raise SystemExit(
            "pybind11 must be installed (for example: pip install '.[native]')"
        ) from exc

    subprocess.run(
        [
            "cmake", "-S", str(NATIVE_DIR), "-B", str(BUILD_DIR),
            f"-Dpybind11_DIR={cmake_dir}",
            f"-DIEVF_PYTHON_OUTPUT_DIR={PACKAGE_DIR}",
            "-DCMAKE_BUILD_TYPE=Release",
        ],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        ["cmake", "--build", str(BUILD_DIR), "--config", "Release"],
        cwd=ROOT,
        check=True,
    )

    # Import verifies ABI-suffixed module naming and load-time dependencies.
    env = os.environ.copy()
    src = str(ROOT / "src")
    env["PYTHONPATH"] = src + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    subprocess.run(
        [sys.executable, "-c", "import ievf._tve1_native as m; print(m.__file__)"],
        cwd=ROOT,
        env=env,
        check=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
