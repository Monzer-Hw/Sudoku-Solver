"""Unit tests for grid detection and image geometry."""

import numpy as np
import pytest

from src.core.detector import SudokuDetector
from tests.helpers import CELL_SIZE

pytestmark = pytest.mark.unit


class TestPreprocessImage:
    def test_returns_four_stages_with_matching_geometry(
        self, grid_image: np.ndarray
    ) -> None:
        original, gray, blur, thresh = SudokuDetector.preprocess_image(grid_image)

        assert original.shape == grid_image.shape
        assert gray.shape == blur.shape == thresh.shape == grid_image.shape[:2]

    def test_swaps_blue_and_red_channels(self) -> None:
        bgr = np.zeros((10, 10, 3), dtype=np.uint8)
        bgr[:, :, 0] = 10  # blue
        bgr[:, :, 2] = 200  # red

        original, _, _, _ = SudokuDetector.preprocess_image(bgr)

        assert original[0, 0, 0] == 200
        assert original[0, 0, 2] == 10

    def test_threshold_output_is_binary(self, grid_image: np.ndarray) -> None:
        _, _, _, thresh = SudokuDetector.preprocess_image(grid_image)
        assert set(np.unique(thresh).tolist()) <= {0, 255}


class TestFindGridContour:
    def test_finds_four_corner_points(self, grid_image: np.ndarray) -> None:
        _, _, _, thresh = SudokuDetector.preprocess_image(grid_image)

        contour = SudokuDetector.find_grid_contour(thresh)

        assert contour is not None
        assert contour.shape == (4, 2)

    def test_corners_span_the_drawn_grid(self, grid_image: np.ndarray) -> None:
        _, _, _, thresh = SudokuDetector.preprocess_image(grid_image)

        contour = SudokuDetector.find_grid_contour(thresh)

        assert contour is not None
        side = CELL_SIZE * 9
        width = contour[:, 0].max() - contour[:, 0].min()
        height = contour[:, 1].max() - contour[:, 1].min()
        assert width == pytest.approx(side, abs=10)
        assert height == pytest.approx(side, abs=10)

    def test_returns_none_when_no_grid_present(self) -> None:
        blank = np.zeros((200, 200), dtype=np.uint8)
        assert SudokuDetector.find_grid_contour(blank) is None

    def test_ignores_quadrilaterals_that_are_too_small(self) -> None:
        speck = np.zeros((300, 300), dtype=np.uint8)
        speck[10:18, 10:18] = 255

        assert SudokuDetector.find_grid_contour(speck) is None

    def test_ignores_thin_quadrilaterals(self) -> None:
        # Wide enough in area terms, but only 4 pixels tall: splitting it into
        # nine rows would yield empty cells.
        sliver = np.zeros((300, 300), dtype=np.uint8)
        sliver[100:104, 10:290] = 255

        assert SudokuDetector.find_grid_contour(sliver) is None

    def test_ignores_quadrilaterals_covering_too_little_of_the_image(self) -> None:
        # 40x40 square: wide enough per side, but only 0.16% of the image.
        speck = np.zeros((1000, 1000), dtype=np.uint8)
        speck[100:140, 100:140] = 255

        assert SudokuDetector.find_grid_contour(speck) is None
        assert SudokuDetector.find_grid_contour(speck, min_area_ratio=0.0) is not None

    def test_accepts_a_grid_covering_most_of_the_image(
        self, grid_image: np.ndarray
    ) -> None:
        _, _, _, thresh = SudokuDetector.preprocess_image(grid_image)

        assert SudokuDetector.find_grid_contour(thresh, min_area_ratio=0.5) is not None


class TestPerspectiveTransform:
    def test_produces_square_top_down_view(self, grid_image: np.ndarray) -> None:
        original, _, _, thresh = SudokuDetector.preprocess_image(grid_image)
        contour = SudokuDetector.find_grid_contour(thresh)
        assert contour is not None

        warped, matrix = SudokuDetector.perspective_transform(original, contour)

        assert matrix.shape == (3, 3)
        assert warped.shape[0] == pytest.approx(warped.shape[1], abs=2)
        assert warped.shape[0] == pytest.approx(CELL_SIZE * 9, abs=10)

    def test_orders_corners_clockwise_from_top_left(self) -> None:
        # Deliberately unordered corners of a 100x50 rectangle.
        points = np.array([[100, 50], [0, 0], [0, 50], [100, 0]])
        img = np.zeros((80, 160, 3), dtype=np.uint8)

        warped, _ = SudokuDetector.perspective_transform(img, points)

        assert (warped.shape[1], warped.shape[0]) == (100, 50)


class TestExtractCells:
    def test_returns_81_cells_of_28x28(self, grid_image: np.ndarray) -> None:
        original, _, _, thresh = SudokuDetector.preprocess_image(grid_image)
        contour = SudokuDetector.find_grid_contour(thresh)
        assert contour is not None
        warped, _ = SudokuDetector.perspective_transform(original, contour)

        cells, cell_size = SudokuDetector.extract_cells(warped)

        assert cells.shape[:3] == (81, 28, 28)
        assert cell_size == warped.shape[0] // 9

    def test_cell_order_is_row_major(self) -> None:
        # Encode each cell's index as its own grey level, then read it back.
        warped = np.zeros((90, 90, 3), dtype=np.uint8)
        for row in range(9):
            for col in range(9):
                warped[row * 10 : row * 10 + 10, col * 10 : col * 10 + 10] = (
                    row * 9 + col
                )

        cells, cell_size = SudokuDetector.extract_cells(warped)

        assert cell_size == 10
        assert [int(cell[14, 14, 0]) for cell in cells] == list(range(81))
