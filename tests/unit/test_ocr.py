"""Unit tests for cell preprocessing and digit recognition."""

import numpy as np
import pytest

from src.core import ocr as ocr_module
from src.core.ocr import SudokuTesseract, configure_tesseract_cmd

pytestmark = pytest.mark.unit


@pytest.fixture
def cells() -> np.ndarray:
    """Four synthetic BGR cells with different brightness levels."""
    block = np.zeros((4, 28, 28, 3), dtype=np.uint8)
    for index in range(4):
        block[index, 8:20, 8:20] = 255 - index * 40
    return block


class TestConfigureTesseractCmd:
    def test_environment_variable_wins(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TESSERACT_CMD", "/custom/bin/tesseract")
        try:
            assert configure_tesseract_cmd() == "/custom/bin/tesseract"
        finally:
            monkeypatch.delenv("TESSERACT_CMD", raising=False)
            configure_tesseract_cmd()

    def test_falls_back_to_path_lookup(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("TESSERACT_CMD", raising=False)
        monkeypatch.setattr(ocr_module.shutil, "which", lambda _: "/usr/bin/tesseract")
        try:
            assert configure_tesseract_cmd() == "/usr/bin/tesseract"
        finally:
            monkeypatch.undo()
            configure_tesseract_cmd()


class TestProcessCells:
    def test_returns_binary_grayscale_cells_without_mask(
        self, cells: np.ndarray
    ) -> None:
        processed = SudokuTesseract().process_cells(cells)

        assert len(processed) == len(cells)
        for cell in processed:
            assert cell.shape == (28, 28)
            assert set(np.unique(cell).tolist()) <= {0, 255}

    def test_mask_is_applied_on_top_of_the_cell(
        self, cells: np.ndarray, mask_path: str
    ) -> None:
        engine = SudokuTesseract()

        plain = engine.process_cells(cells)
        masked = engine.process_cells(cells, mask_path)

        # bitwise_or with the mask can only add white pixels, never remove them.
        for before, after in zip(plain, masked, strict=True):
            assert np.all(after >= before)
        assert any(np.any(a != b) for a, b in zip(plain, masked, strict=True))

    def test_raises_when_mask_file_is_missing(self, cells: np.ndarray) -> None:
        with pytest.raises(FileNotFoundError, match="Mask image not found"):
            SudokuTesseract().process_cells(cells, "does/not/exist.png")


class TestRecognize:
    def test_builds_9x9_grid_from_ocr_output(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        expected = np.arange(81).reshape(9, 9) % 10
        outputs = iter(f" {value}\n" for value in expected.flatten())
        monkeypatch.setattr(
            ocr_module.pytesseract,
            "image_to_string",
            lambda cell, config: next(outputs),
        )

        grid = SudokuTesseract().recognize([np.zeros((28, 28), np.uint8)] * 81)

        assert grid.shape == (9, 9)
        assert np.array_equal(grid, expected)

    def test_non_digit_results_become_zero(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            ocr_module.pytesseract,
            "image_to_string",
            lambda cell, config: "|\n\x0c",
        )

        grid = SudokuTesseract().recognize([np.zeros((28, 28), np.uint8)] * 81)

        assert np.array_equal(grid, np.zeros((9, 9), dtype=int))

    def test_uses_the_configured_tesseract_options(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        seen: list[str] = []

        def fake_image_to_string(cell, config):
            seen.append(config)
            return "1"

        monkeypatch.setattr(
            ocr_module.pytesseract, "image_to_string", fake_image_to_string
        )

        SudokuTesseract(config="--psm 6").recognize([np.zeros((28, 28), np.uint8)] * 81)

        assert set(seen) == {"--psm 6"}
