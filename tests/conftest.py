"""Shared fixtures for unit, integration and e2e tests."""

import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

from src.api.config import Settings, get_settings
from src.api.main import app
from tests.helpers import encode_png, render_grid_image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ASSETS_DIR = PROJECT_ROOT / "assets"

PUZZLE = [
    [5, 3, 0, 0, 7, 0, 0, 0, 0],
    [6, 0, 0, 1, 9, 5, 0, 0, 0],
    [0, 9, 8, 0, 0, 0, 0, 6, 0],
    [8, 0, 0, 0, 6, 0, 0, 0, 3],
    [4, 0, 0, 8, 0, 3, 0, 0, 1],
    [7, 0, 0, 0, 2, 0, 0, 0, 6],
    [0, 6, 0, 0, 0, 0, 2, 8, 0],
    [0, 0, 0, 4, 1, 9, 0, 0, 5],
    [0, 0, 0, 0, 8, 0, 0, 7, 9],
]

SOLUTION = [
    [5, 3, 4, 6, 7, 8, 9, 1, 2],
    [6, 7, 2, 1, 9, 5, 3, 4, 8],
    [1, 9, 8, 3, 4, 2, 5, 6, 7],
    [8, 5, 9, 7, 6, 1, 4, 2, 3],
    [4, 2, 6, 8, 5, 3, 7, 9, 1],
    [7, 1, 3, 9, 2, 4, 8, 5, 6],
    [9, 6, 1, 5, 3, 7, 2, 8, 4],
    [2, 8, 7, 4, 1, 9, 6, 3, 5],
    [3, 4, 5, 2, 8, 6, 1, 7, 9],
]


def tesseract_available() -> bool:
    """Returns True when a usable Tesseract binary is installed."""
    from src.core.ocr import configure_tesseract_cmd

    cmd = configure_tesseract_cmd()
    if shutil.which(cmd) is None and not Path(cmd).exists():
        return False
    try:
        subprocess.run([cmd, "--version"], capture_output=True, check=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return False
    return True


@pytest.fixture(autouse=True)
def settings_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Provides deterministic settings so tests never depend on a local .env."""
    monkeypatch.setenv("APP_NAME", "Sudoku-Solver-API")
    monkeypatch.setenv("APP_VERSION", "0.1.0")
    monkeypatch.setenv("FILE_ALLOWED_TYPES", '["image/png", "image/jpeg", "image/jpg"]')


@pytest.fixture
def settings(settings_env: None) -> Settings:
    """The Settings object built from the test environment."""
    return get_settings()


@pytest.fixture
def client() -> TestClient:
    """A FastAPI test client bound to the real application."""
    return TestClient(app)


@pytest.fixture
def puzzle_board() -> np.ndarray:
    """A solvable 9x9 puzzle with zeros for empty cells."""
    return np.array(PUZZLE, dtype=int)


@pytest.fixture
def solved_board() -> np.ndarray:
    """The unique solution of `puzzle_board`."""
    return np.array(SOLUTION, dtype=int)


@pytest.fixture
def unsolvable_board() -> np.ndarray:
    """A board whose only empty cell in row 0 has no legal candidate."""
    board = np.zeros((9, 9), dtype=int)
    board[0, :8] = [1, 2, 3, 4, 5, 6, 7, 8]
    board[1, 8] = 9
    return board


@pytest.fixture
def grid_image(puzzle_board: np.ndarray) -> np.ndarray:
    """A synthetic BGR image of the puzzle grid."""
    return render_grid_image(puzzle_board)


@pytest.fixture
def grid_image_png(grid_image: np.ndarray) -> bytes:
    """PNG bytes of the synthetic grid image."""
    return encode_png(grid_image)


@pytest.fixture
def mask_path() -> str:
    """Path to the OCR mask shipped with the project."""
    path = ASSETS_DIR / "mask.png"
    if not path.exists():
        pytest.skip(f"mask asset missing: {path}")
    return path.as_posix()


@pytest.fixture
def example_image_path() -> Path:
    """Path to a real example photo used by the e2e tests."""
    path = ASSETS_DIR / "examples" / "1.jpg"
    if not path.exists():
        pytest.skip(f"example asset missing: {path}")
    return path


@pytest.fixture
def stub_ocr(monkeypatch: pytest.MonkeyPatch, puzzle_board: np.ndarray):
    """
    Replaces Tesseract recognition with a fixed grid.

    Integration tests exercise routing, validation and the solver wiring without
    depending on an OCR binary being installed.
    """
    from src.core.ocr import SudokuTesseract

    def _install(grid: np.ndarray | None = None) -> np.ndarray:
        recognized = puzzle_board if grid is None else grid
        monkeypatch.setattr(
            SudokuTesseract,
            "recognize",
            lambda self, cells: recognized.copy(),
        )
        monkeypatch.setattr(
            SudokuTesseract,
            "process_cells",
            lambda self, cells, mask_path=None: list(cells),
        )
        return recognized

    return _install
