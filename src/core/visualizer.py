"""
Provides the SudokuVisualizer class for overlaying the Sudoku solution onto the original image.
"""

import cv2
import numpy as np


class SudokuVisualizer:
    """
    A class for creating a visual overlay of the Sudoku solution on the original image.
    """

    @staticmethod
    def overlay_solution(
        original_img: np.ndarray,
        warped_img: np.ndarray,
        solution_grid: np.ndarray,
        positions: np.ndarray,
        grid_contour: np.ndarray,
        cell_size: int,
    ) -> np.ndarray:
        """
        Overlays the solved digits on the original image.

        :param original_img: Original color image.
        :param warped_img: Warped (top-down) image of the Sudoku grid.
        :param solution_grid: 9x9 solved Sudoku grid.
        :param positions: Mask (1 for empty cells, 0 for pre-filled cells).
        :param grid_contour: Contour points of the Sudoku grid in the original image.
        :param cell_size: Size of each cell (affects text placement).
        :return: Image with the solution overlay.
        """
        font = cv2.FONT_HERSHEY_COMPLEX_SMALL
        scale = cell_size / 28
        color = (0, 255, 0)  # Green

        height, width = warped_img.shape[:2]
        solution_img = np.zeros_like(warped_img)

        # Only overlay digits in empty positions.
        solution_grid_masked = np.multiply(positions, solution_grid)
        for i in range(9):
            for j in range(9):
                if solution_grid_masked[i][j] != 0:
                    x = int((j + 0.3) * cell_size)
                    y = int((i + 0.8) * cell_size)
                    cv2.putText(
                        solution_img,
                        str(solution_grid_masked[i][j]),
                        (x, y),
                        font,
                        scale,
                        color,
                        1,
                        cv2.LINE_AA,
                    )

        # Compute inverse perspective transformation
        inv_M = cv2.getPerspectiveTransform(
            np.array(
                [[0, 0], [0, height], [width, height], [width, 0]], dtype="float32"
            ),
            grid_contour.astype("float32"),
        )
        inv_warped = cv2.warpPerspective(
            solution_img, inv_M, (original_img.shape[1], original_img.shape[0])
        )

        # Create a mask and combine the overlay with the original image.
        gray = cv2.cvtColor(inv_warped, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
        fg = cv2.bitwise_and(inv_warped, inv_warped, mask=mask)
        bg = cv2.bitwise_and(original_img, original_img, mask=cv2.bitwise_not(mask))
        result = cv2.add(bg, fg)

        return result
