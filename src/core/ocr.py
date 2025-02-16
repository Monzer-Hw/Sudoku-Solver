"""
Provides the SudokuTesseract class for processing Sudoku cell images
and recognizing digits using pytesseract.
"""

from typing import Optional

import cv2
import numpy as np
import pytesseract  # type: ignore

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


class SudokuTesseract:
    """
    A class for processing Sudoku cell images and recognizing digits using pytesseract.
    """

    def __init__(self, config="--psm 10 --oem 3 -c tessedit_char_whitelist=0123456789"):
        """
        Initializes the OCR engine with a configuration optimized for single-digit recognition.

        :param config: Pytesseract configuration string. The default is set to:
                --psm 10 (treat image as a single character),
                --oem 3 (default OCR Engine Mode), and restricts recognition to digits 0-9.
        """
        self.config = config

    def process_cells(self, cells: np.ndarray, mask_path: Optional[str] = None) -> list:
        """
        Processes a list of cell images to prepare them for OCR.

        This includes converting each cell to grayscale, thresholding, and optionally applying a mask.

        :param cells: NumPy array of cell images.
        :param mask_path: Optional path to a mask image to enhance digit visibility.
        :return: List of processed cell images.
        """
        processed_cells = []

        if mask_path is not None:
            mask = cv2.imread(mask_path, 0)
            if mask is None:
                raise FileNotFoundError(f"Mask image not found: {mask_path}")

        for cell in cells:
            cell = cv2.cvtColor(cell, cv2.COLOR_BGR2GRAY)
            _, cell = cv2.threshold(cell, 0, 255, cv2.THRESH_OTSU)
            resized_mask = cv2.resize(mask, (cell.shape[1], cell.shape[0]))
            cell = cv2.bitwise_or(cell, resized_mask)

            processed_cells.append(cell)

        return processed_cells

    def recognize(self, cells: list) -> np.ndarray:
        """
        Recognizes digits from the provided cell images using pytesseract.

        For each cell, pytesseract is used to extract a character. Non-digit
        results are treated as an empty cell (0).

        :param cells: List of preprocessed cell images.
        :return: A 9x9 NumPy array representing the recognized Sudoku grid.
        """
        result = []
        for cell in cells:
            text = pytesseract.image_to_string(cell, config=self.config)
            text = text.strip()
            if text.isdigit():
                digit = int(text)
            else:
                digit = 0
            result.append(digit)
        sudoku_grid = np.array(result).reshape(9, 9)
        return sudoku_grid
