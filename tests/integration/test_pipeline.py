"""Integration tests chaining the core modules without the HTTP layer.

Only the Tesseract call itself is faked; detection, masking, solving and
overlay rendering all run for real.
"""

import numpy as np
import pytest

from src.core import ocr as ocr_module
from src.core.detector import SudokuDetector
from src.core.ocr import SudokuTesseract
from src.core.solver import SudokuSolver
from src.core.visualizer import SudokuVisualizer
from tests.helpers import is_valid_solution

pytestmark = pytest.mark.integration


@pytest.fixture
def fake_tesseract(monkeypatch: pytest.MonkeyPatch, puzzle_board: np.ndarray) -> None:
    """Makes pytesseract return the known puzzle, cell by cell."""
    outputs = iter(
        "" if digit == 0 else f"{digit}\n\x0c" for digit in puzzle_board.flatten()
    )
    monkeypatch.setattr(
        ocr_module.pytesseract, "image_to_string", lambda cell, config: next(outputs)
    )


def test_detect_recognize_solve_and_overlay(
    grid_image: np.ndarray,
    puzzle_board: np.ndarray,
    mask_path: str,
    fake_tesseract: None,
) -> None:
    original, _, _, thresh = SudokuDetector.preprocess_image(grid_image)
    contour = SudokuDetector.find_grid_contour(thresh)
    assert contour is not None

    warped, _ = SudokuDetector.perspective_transform(original, contour)
    cells, cell_size = SudokuDetector.extract_cells(warped)
    assert cells.shape[0] == 81

    engine = SudokuTesseract()
    processed = engine.process_cells(cells, mask_path)
    recognized = engine.recognize(processed)
    assert np.array_equal(recognized, puzzle_board)

    solved = SudokuSolver.solve(recognized)
    assert is_valid_solution(solved, puzzle_board)

    positions = np.where(recognized > 0, 0, 1)
    result = SudokuVisualizer.overlay_solution(
        grid_image, warped, solved, positions, contour, cell_size
    )

    assert result.shape == grid_image.shape
    assert np.any(result != grid_image)


def test_extracted_cells_survive_mask_preprocessing(
    grid_image: np.ndarray, mask_path: str
) -> None:
    original, _, _, thresh = SudokuDetector.preprocess_image(grid_image)
    contour = SudokuDetector.find_grid_contour(thresh)
    assert contour is not None
    warped, _ = SudokuDetector.perspective_transform(original, contour)
    cells, _ = SudokuDetector.extract_cells(warped)

    processed = SudokuTesseract().process_cells(cells, mask_path)

    assert len(processed) == 81
    for cell in processed:
        assert cell.shape == (28, 28)
        assert cell.dtype == np.uint8


def test_pipeline_detects_absence_of_a_grid() -> None:
    blank = np.full((200, 200, 3), 255, dtype=np.uint8)

    _, _, _, thresh = SudokuDetector.preprocess_image(blank)

    assert SudokuDetector.find_grid_contour(thresh) is None


def test_solver_rejects_a_misread_grid() -> None:
    # A clue that leaves a cell with no candidate is a typical OCR failure mode.
    misread = np.zeros((9, 9), dtype=int)
    misread[0, :8] = [1, 2, 3, 4, 5, 6, 7, 8]
    misread[1, 8] = 9

    with pytest.raises(ValueError, match="No solution exists"):
        SudokuSolver.solve(misread)
