"""Unit tests for settings loading and response schemas."""

import pytest
from pydantic import ValidationError

from src.api.config import Settings, get_settings
from src.api.schemas.sudoku import SolveResponse

pytestmark = pytest.mark.unit


class TestSettings:
    def test_reads_values_from_the_environment(self) -> None:
        settings = get_settings()

        assert settings.APP_NAME == "Sudoku-Solver-API"
        assert settings.APP_VERSION == "0.1.0"
        assert "image/png" in settings.FILE_ALLOWED_TYPES

    def test_environment_overrides_are_picked_up(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("APP_NAME", "Renamed-API")

        assert get_settings().APP_NAME == "Renamed-API"

    def test_missing_required_field_raises(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path
    ) -> None:
        monkeypatch.delenv("APP_NAME", raising=False)
        # Run from a directory whose .env is empty so a developer's real file
        # cannot satisfy the missing field.
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".env").write_text("", encoding="utf-8")

        with pytest.raises(ValidationError):
            Settings()  # type: ignore[call-arg]  # values come from the environment


class TestSolveResponse:
    def test_accepts_a_9x9_grid(self, solved_board) -> None:
        response = SolveResponse(grid=solved_board.tolist(), solved=True)

        assert response.solved is True
        assert len(response.grid) == 9
        assert all(len(row) == 9 for row in response.grid)

    def test_rejects_non_integer_cells(self) -> None:
        with pytest.raises(ValidationError):
            SolveResponse(grid=[["a"] * 9] * 9, solved=True)  # type: ignore[list-item]

    def test_rejects_missing_solved_flag(self) -> None:
        with pytest.raises(ValidationError):
            SolveResponse(grid=[[0] * 9] * 9)  # type: ignore[call-arg]
