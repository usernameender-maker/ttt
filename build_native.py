"""Build the optional IEVF C++ matrix kernel into src/ievf.

Requires CMake, a C++17 compiler with OpenMP, pybind11, and Python development
headers. The core Python package has no new mandatory runtime dependencies.
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
BUILD = ROOT / "build" / "native"


def main() -> int:
    try:
        cmake_dir = subprocess.check_output(
            [sys.executable, "-m", "pybind11", "--cmakedir"],
            cwd=ROOT,
            text=True,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        raise SystemExit("pybind11 and CMake must be installed to build the native module") from exc

    subprocess.run(
        [
            "cmake", "-S", str(ROOT / "native"), "-B", str(BUILD),
            f"-Dpybind11_DIR={cmake_dir}",
            f"-DIEVF_PYTHON_OUTPUT_DIR={ROOT / 'src' / 'ievf'}",
            "-DCMAKE_BUILD_TYPE=Release",
        ],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        ["cmake", "--build", str(BUILD), "--config", "Release"],
        cwd=ROOT,
        check=True,
    )

    env = os.environ.copy()
    src = str(ROOT / "src")
    env["PYTHONPATH"] = src + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    subprocess.run(
        [sys.executable, "-c", "import ievf._tve1_native as m; print(m.__file__)"] ,
        cwd=ROOT,
        env=env,
        check=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
