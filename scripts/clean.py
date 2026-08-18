"""Remove caches and build artifacts. Driven by `just clean`.

Kept as a script rather than a shell one-liner so the recipe behaves the same on
Windows and POSIX shells.
"""

import shutil
from pathlib import Path

DIRECTORIES = (
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "dist",
    "htmlcov",
)
FILE_GLOBS = (".coverage", ".coverage.*", "coverage.xml")


def main() -> None:
    root = Path(__file__).resolve().parents[1]

    for name in DIRECTORIES:
        shutil.rmtree(root / name, ignore_errors=True)

    for cache in root.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)

    for pattern in FILE_GLOBS:
        for path in root.glob(pattern):
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
