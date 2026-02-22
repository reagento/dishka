from __future__ import annotations

import os
from pathlib import Path

from setuptools import Extension, setup
from setuptools.command.build_ext import build_ext


class OptionalBuildExt(build_ext):
    def run(self) -> None:
        try:
            super().run()
        except Exception:
            self.warn(
                "Building Cython extensions failed; "
                "falling back to pure Python implementation.",
            )

    def build_extension(self, ext: Extension) -> None:
        try:
            super().build_extension(ext)
        except Exception:
            self.warn(
                f"Building extension {ext.name!r} failed; "
                "falling back to pure Python implementation.",
            )


def _make_extensions() -> list[Extension]:
    extensions: list[Extension] = []
    pyx_path = Path("src/dishka/entities/_key_c.pyx")
    if pyx_path.exists():
        extensions.append(
            Extension(
                name="dishka.entities._key_c",
                sources=[str(pyx_path)],
            ),
        )

    # Opt-in aggressive mode: compile almost all dishka modules with Cython.
    # Usage (PowerShell):
    #   $env:DISHKA_CYTHONIZE_ALL = "1"
    #   pip install -e .
    if os.getenv("DISHKA_CYTHONIZE_ALL") == "1":
        src_root = Path("src/dishka")
        excluded_prefixes = (
            "dishka._adaptix.",
            "dishka._adaptix",
            "dishka.code_tools.",
        )
        excluded_modules: set[str] = set()
        for py_file in src_root.rglob("*.py"):
            module_rel = py_file.relative_to("src").with_suffix("")
            module_name = ".".join(module_rel.parts)
            if module_name in {"dishka._version"}:
                continue
            if module_name.startswith(excluded_prefixes):
                continue
            if module_name in excluded_modules:
                continue
            extensions.append(
                Extension(
                    name=module_name,
                    sources=[str(py_file)],
                ),
            )
    return extensions


def _maybe_cythonize(extensions: list[Extension]) -> list[Extension]:
    if not extensions:
        return []
    try:
        from Cython.Build import cythonize
    except Exception:
        return []
    return cythonize(
        extensions,
        compiler_directives={"language_level": "3"},
    )


setup(
    ext_modules=_maybe_cythonize(_make_extensions()),
    cmdclass={"build_ext": OptionalBuildExt},
)
