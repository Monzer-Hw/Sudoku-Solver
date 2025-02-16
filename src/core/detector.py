"""
Provides the SudokuDetector class for image preprocessing, grid detection,
perspective transformation, and cell extraction.
"""

import cv2
import numpy as np
from typing import Tuple, Optional


class SudokuDetector:
    """
    A class to preprocess an image and detect the Sudoku grid.
    """

    @staticmethod
    def preprocess_image(
        image: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Reads an image from the given path and applies preprocessing steps.

        :param image_path: Path to the input image.
        :return: Tuple of (original image, grayscale image, blurred image, thresholded image).
        """

        # Convert from BGR to RGB and create a copy of the original image.
        img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        original = img.copy()

        # Convert to grayscale, apply Gaussian blur, and adaptive thresholding.
        gray = cv2.cvtColor(original, cv2.COLOR_RGB2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        thresh = cv2.adaptiveThreshold(
            blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
        )
        return original, gray, blur, thresh

    @staticmethod
    def find_grid_contour(thresh_img: np.ndarray) -> Optional[np.ndarray]:
        """
        Finds the largest 4-point contour in the thresholded image assumed to be the Sudoku grid.

        :param thresh_img: Thresholded binary image.
        :return: An array of 4 points if found; otherwise, None.
        """
        contours, _ = cv2.findContours(
            thresh_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        contours = sorted(contours, key=cv2.contourArea, reverse=True)

        for cnt in contours:
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
            if len(approx) == 4:
                return approx.reshape(4, 2)
        return None

    @staticmethod
    def perspective_transform(
        img: np.ndarray, points: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Applies a perspective transformation to obtain a top-down view of the Sudoku grid.

        :param img: Original image.
        :param points: 4 points representing the grid contour.
        :return: A tuple (warped image, transformation matrix).
        """
        # Order points: top-left, top-right, bottom-right, bottom-left.
        rect = np.zeros((4, 2), dtype="float32")
        s = points.sum(axis=1)
        rect[0] = points[np.argmin(s)]
        rect[2] = points[np.argmax(s)]
        diff = np.diff(points, axis=1)
        rect[1] = points[np.argmin(diff)]
        rect[3] = points[np.argmax(diff)]

        (tl, tr, br, bl) = rect
        width = max(np.linalg.norm(tr - tl), np.linalg.norm(br - bl))
        height = max(np.linalg.norm(bl - tl), np.linalg.norm(br - tr))

        dst = np.array(
            [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]],
            dtype="float32",
        )

        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(img, M, (int(width), int(height)))
        return warped, M

    @staticmethod
    def extract_cells(warped_img: np.ndarray) -> Tuple[np.ndarray, int]:
        """
        Splits the warped Sudoku grid into 81 individual cell images.

        :param warped_img: Warped (top-down) image of the Sudoku grid.
        :return: A tuple of (array of cell images, original cell size).
        """
        cell_size = warped_img.shape[0] // 9

        rows = np.array_split(warped_img, 9, axis=0)
        cells = []
        for row in rows:
            cols = np.array_split(row, 9, axis=1)
            for cell in cols:
                cell = cv2.resize(cell, (28, 28))
                cells.append(cell)
        return np.array(cells), cell_size
