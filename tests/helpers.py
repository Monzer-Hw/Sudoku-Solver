"""Shared test helpers: synthetic Sudoku images and board utilities."""

import cv2
import numpy as np

CELL_SIZE = 54
MARGIN = 24


def render_grid_image(
    grid: np.ndarray | None = None,
    cell_size: int = CELL_SIZE,
    margin: int = MARGIN,
) -> np.ndarray:
    """
    Draws a synthetic 9x9 Sudoku grid as a BGR image.

    The grid is black-on-white with a thick outer border so that the detector
    picks it up as the largest four-point contour.

    :param grid: Optional 9x9 array of digits; zeros are left blank.
    :param cell_size: Side length in pixels of a single cell.
    :param margin: White padding around the grid.
    :return: BGR image containing the grid.
    """
    side = cell_size * 9
    size = side + margin * 2
    img = np.full((size, size, 3), 255, dtype=np.uint8)

    for i in range(10):
        offset = margin + i * cell_size
        thickness = 3 if i % 3 == 0 else 1
        cv2.line(img, (margin, offset), (margin + side, offset), (0, 0, 0), thickness)
        cv2.line(img, (offset, margin), (offset, margin + side), (0, 0, 0), thickness)

    if grid is not None:
        for row in range(9):
            for col in range(9):
                digit = int(grid[row][col])
                if digit == 0:
                    continue
                origin = (
                    margin + int((col + 0.32) * cell_size),
                    margin + int((row + 0.78) * cell_size),
                )
                cv2.putText(
                    img,
                    str(digit),
                    origin,
                    cv2.FONT_HERSHEY_SIMPLEX,
                    cell_size / 45,
                    (0, 0, 0),
                    2,
                    cv2.LINE_AA,
                )
    return img


def encode_png(image: np.ndarray) -> bytes:
    """Encodes a BGR image as PNG bytes."""
    success, buffer = cv2.imencode(".png", image)
    assert success, "failed to encode test image"
    return bytes(buffer.tobytes())


def is_valid_solution(solved: np.ndarray, puzzle: np.ndarray) -> bool:
    """
    Checks that `solved` is a complete Sudoku solution consistent with `puzzle`.

    :param solved: Candidate 9x9 solution.
    :param puzzle: Original 9x9 board with zeros for empty cells.
    :return: True when every row, column and 3x3 box holds digits 1-9 exactly
             once and all clues from `puzzle` are preserved.
    """
    expected = set(range(1, 10))

    for i in range(9):
        if set(solved[i, :].tolist()) != expected:
            return False
        if set(solved[:, i].tolist()) != expected:
            return False

    for row in range(0, 9, 3):
        for col in range(0, 9, 3):
            box = solved[row : row + 3, col : col + 3]
            if set(box.flatten().tolist()) != expected:
                return False

    clues = puzzle != 0
    return bool(np.array_equal(solved[clues], puzzle[clues]))
