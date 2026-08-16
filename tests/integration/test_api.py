"""Integration tests for the FastAPI routes.

Tesseract is stubbed out here so these tests exercise routing, validation,
error mapping and the detector/solver/visualizer wiring without depending on
an OCR binary. The real OCR path is covered by the e2e suite.
"""

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from tests.helpers import encode_png

pytestmark = pytest.mark.integration

SOLVE_URL = "/sudoku/solve"
SOLVE_IMAGE_URL = "/sudoku/solve:image"


def upload(content: bytes, content_type: str = "image/png") -> dict:
    """Builds the multipart payload expected by the solve endpoints."""
    return {"file": ("grid.png", content, content_type)}


class TestBaseRoute:
    def test_reports_app_name_and_version(self, client: TestClient) -> None:
        response = client.get("/base/")

        assert response.status_code == 200
        assert response.json() == {"message": "Sudoku-Solver-API 0.1.0"}

    def test_openapi_schema_exposes_both_solve_routes(self, client: TestClient) -> None:
        paths = client.get("/openapi.json").json()["paths"]

        assert SOLVE_URL in paths
        assert SOLVE_IMAGE_URL in paths


class TestSolveJson:
    def test_returns_the_solved_grid(
        self,
        client: TestClient,
        stub_ocr,
        grid_image_png: bytes,
        solved_board: np.ndarray,
    ) -> None:
        stub_ocr()

        response = client.post(SOLVE_URL, files=upload(grid_image_png))

        assert response.status_code == 200
        body = response.json()
        assert body["solved"] is True
        assert body["grid"] == solved_board.tolist()

    @pytest.mark.parametrize("content_type", ["text/plain", "application/pdf"])
    def test_rejects_unsupported_content_types(
        self, client: TestClient, grid_image_png: bytes, content_type: str
    ) -> None:
        response = client.post(
            SOLVE_URL, files=upload(grid_image_png, content_type=content_type)
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "File type not supported"

    def test_rejects_undecodable_bytes(self, client: TestClient) -> None:
        response = client.post(SOLVE_URL, files=upload(b"this is not an image"))

        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid image"

    def test_returns_422_when_no_grid_is_detected(self, client: TestClient) -> None:
        blank = np.full((200, 200, 3), 255, dtype=np.uint8)

        response = client.post(SOLVE_URL, files=upload(encode_png(blank)))

        assert response.status_code == 422
        assert response.json()["detail"] == "Could not detect the Sudoku grid"

    def test_returns_422_when_the_recognised_grid_is_unsolvable(
        self,
        client: TestClient,
        stub_ocr,
        grid_image_png: bytes,
        unsolvable_board: np.ndarray,
    ) -> None:
        stub_ocr(unsolvable_board)

        response = client.post(SOLVE_URL, files=upload(grid_image_png))

        assert response.status_code == 422
        assert "No solution exists" in response.json()["detail"]

    def test_requires_a_file_field(self, client: TestClient) -> None:
        assert client.post(SOLVE_URL).status_code == 422

    def test_accepts_jpeg_uploads(
        self, client: TestClient, stub_ocr, grid_image: np.ndarray
    ) -> None:
        stub_ocr()
        success, buffer = cv2.imencode(".jpg", grid_image)
        assert success

        response = client.post(
            SOLVE_URL,
            files={"file": ("grid.jpg", buffer.tobytes(), "image/jpeg")},
        )

        assert response.status_code == 200


class TestSolveImage:
    def test_returns_a_decodable_png_of_the_original_size(
        self,
        client: TestClient,
        stub_ocr,
        grid_image: np.ndarray,
        grid_image_png: bytes,
    ) -> None:
        stub_ocr()

        response = client.post(SOLVE_IMAGE_URL, files=upload(grid_image_png))

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        decoded = cv2.imdecode(
            np.frombuffer(response.content, dtype=np.uint8), cv2.IMREAD_COLOR
        )
        assert decoded is not None
        assert decoded.shape == grid_image.shape

    def test_overlay_changes_the_uploaded_image(
        self,
        client: TestClient,
        stub_ocr,
        grid_image: np.ndarray,
        grid_image_png: bytes,
    ) -> None:
        stub_ocr()

        response = client.post(SOLVE_IMAGE_URL, files=upload(grid_image_png))

        decoded = cv2.imdecode(
            np.frombuffer(response.content, dtype=np.uint8), cv2.IMREAD_COLOR
        )
        assert np.any(decoded != grid_image)

    def test_rejects_unsupported_content_types(
        self, client: TestClient, grid_image_png: bytes
    ) -> None:
        response = client.post(
            SOLVE_IMAGE_URL, files=upload(grid_image_png, content_type="text/plain")
        )

        assert response.status_code == 400

    def test_rejects_undecodable_bytes(self, client: TestClient) -> None:
        response = client.post(SOLVE_IMAGE_URL, files=upload(b"nope"))

        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid image"

    def test_returns_422_when_no_grid_is_detected(self, client: TestClient) -> None:
        blank = np.full((200, 200, 3), 255, dtype=np.uint8)

        response = client.post(SOLVE_IMAGE_URL, files=upload(encode_png(blank)))

        assert response.status_code == 422

    def test_reports_encoding_failure_as_500(
        self,
        client: TestClient,
        stub_ocr,
        grid_image_png: bytes,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        stub_ocr()
        from src.api.routes import sudoku as sudoku_route

        monkeypatch.setattr(
            sudoku_route.cv2, "imencode", lambda ext, img: (False, np.array([]))
        )

        response = client.post(SOLVE_IMAGE_URL, files=upload(grid_image_png))

        assert response.status_code == 500
        assert response.json()["detail"] == "Failed to encode image"
