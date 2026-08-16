"""End-to-end tests over the real HTTP API, real images and real Tesseract.

These are skipped automatically when no Tesseract binary is installed; CI
installs one so the suite runs there.
"""

from pathlib import Path

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from tests.conftest import tesseract_available
from tests.helpers import is_valid_solution

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        not tesseract_available(), reason="Tesseract OCR binary is not installed"
    ),
]

SOLVE_URL = "/sudoku/solve"
SOLVE_IMAGE_URL = "/sudoku/solve:image"


def jpeg_upload(path: Path) -> dict:
    """Builds a multipart payload from an example photo on disk."""
    return {"file": (path.name, path.read_bytes(), "image/jpeg")}


def test_solve_returns_a_complete_valid_solution(
    client: TestClient, example_image_path: Path
) -> None:
    response = client.post(SOLVE_URL, files=jpeg_upload(example_image_path))

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["solved"] is True

    grid = np.array(body["grid"], dtype=int)
    assert grid.shape == (9, 9)
    # A solution is self-consistent: every row, column and box holds 1-9 once.
    assert is_valid_solution(grid, np.zeros((9, 9), dtype=int))


def test_solve_image_returns_an_overlaid_png(
    client: TestClient, example_image_path: Path
) -> None:
    source = cv2.imread(example_image_path.as_posix())
    assert source is not None

    response = client.post(SOLVE_IMAGE_URL, files=jpeg_upload(example_image_path))

    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "image/png"

    decoded = cv2.imdecode(
        np.frombuffer(response.content, dtype=np.uint8), cv2.IMREAD_COLOR
    )
    assert decoded is not None
    assert decoded.shape == source.shape
    assert np.any(decoded != source), "no digits were drawn onto the photo"


def test_solve_is_deterministic_across_calls(
    client: TestClient, example_image_path: Path
) -> None:
    first = client.post(SOLVE_URL, files=jpeg_upload(example_image_path)).json()
    second = client.post(SOLVE_URL, files=jpeg_upload(example_image_path)).json()

    assert first == second


def test_photo_without_a_grid_is_rejected(client: TestClient) -> None:
    noise = np.random.default_rng(0).integers(0, 255, (300, 300, 3), dtype=np.uint8)
    success, buffer = cv2.imencode(".png", noise)
    assert success

    response = client.post(
        SOLVE_URL, files={"file": ("noise.png", buffer.tobytes(), "image/png")}
    )

    assert response.status_code == 422
