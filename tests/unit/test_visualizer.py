"""Unit tests for solution overlay rendering."""

import numpy as np
import pytest

from src.core.detector import SudokuDetector
from src.core.visualizer import SudokuVisualizer

pytestmark = pytest.mark.unit


@pytest.fixture
def geometry(grid_image: np.ndarray):
    """Warped grid, contour and cell size derived from the synthetic image."""
    original, _, _, thresh = SudokuDetector.preprocess_image(grid_image)
    contour = SudokuDetector.find_grid_contour(thresh)
    assert contour is not None
    warped, _ = SudokuDetector.perspective_transform(original, contour)
    _, cell_size = SudokuDetector.extract_cells(warped)
    return original, warped, contour, cell_size


def test_overlay_preserves_original_dimensions(
    geometry, solved_board: np.ndarray, puzzle_board: np.ndarray
) -> None:
    original, warped, contour, cell_size = geometry
    positions = np.where(puzzle_board > 0, 0, 1)

    result = SudokuVisualizer.overlay_solution(
        original, warped, solved_board, positions, contour, cell_size
    )

    assert result.shape == original.shape
    assert result.dtype == original.dtype


def test_overlay_draws_digits_into_empty_cells(
    geometry, solved_board: np.ndarray, puzzle_board: np.ndarray
) -> None:
    original, warped, contour, cell_size = geometry
    positions = np.where(puzzle_board > 0, 0, 1)

    result = SudokuVisualizer.overlay_solution(
        original, warped, solved_board, positions, contour, cell_size
    )

    assert np.any(result != original), "overlay produced no visible change"


def test_empty_position_mask_leaves_image_untouched(
    geometry, solved_board: np.ndarray
) -> None:
    original, warped, contour, cell_size = geometry
    positions = np.zeros((9, 9), dtype=int)

    result = SudokuVisualizer.overlay_solution(
        original, warped, solved_board, positions, contour, cell_size
    )

    assert np.array_equal(result, original)


def test_only_masked_cells_are_redrawn(geometry, solved_board: np.ndarray) -> None:
    original, warped, contour, cell_size = geometry
    only_first_cell = np.zeros((9, 9), dtype=int)
    only_first_cell[0, 0] = 1

    result = SudokuVisualizer.overlay_solution(
        original, warped, solved_board, only_first_cell, contour, cell_size
    )

    changed = np.argwhere(np.any(result != original, axis=2))
    assert changed.size > 0, "the single unmasked cell should have been drawn"
    # Every changed pixel must sit within the first cell-band of the grid.
    top_left = contour.min(axis=0)
    assert np.all(changed[:, 0] <= top_left[1] + 2 * cell_size)
    assert np.all(changed[:, 1] <= top_left[0] + 2 * cell_size)
