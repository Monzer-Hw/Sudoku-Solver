"""Unit tests for the backtracking Sudoku solver."""

import numpy as np
import pytest

from src.core.solver import SudokuSolver
from tests.helpers import is_valid_solution

pytestmark = pytest.mark.unit


class TestIsValid:
    def test_rejects_number_already_in_row(self, puzzle_board: np.ndarray) -> None:
        # Row 0 already contains a 5 at column 0.
        assert SudokuSolver.is_valid(puzzle_board, 0, 2, 5) is False

    def test_rejects_number_already_in_column(self, puzzle_board: np.ndarray) -> None:
        # Column 0 already contains a 6 at row 1.
        assert SudokuSolver.is_valid(puzzle_board, 2, 0, 6) is False

    def test_rejects_number_already_in_box(self, puzzle_board: np.ndarray) -> None:
        # The top-left box already contains a 9 at (2, 1).
        assert SudokuSolver.is_valid(puzzle_board, 0, 2, 9) is False

    def test_accepts_number_with_no_conflict(self, puzzle_board: np.ndarray) -> None:
        assert SudokuSolver.is_valid(puzzle_board, 0, 2, 4) is True

    @pytest.mark.parametrize("num", range(1, 10))
    def test_empty_board_accepts_every_digit(self, num: int) -> None:
        assert SudokuSolver.is_valid(np.zeros((9, 9), dtype=int), 4, 4, num) is True


class TestExploreSolutions:
    def test_solves_board_in_place(self, puzzle_board: np.ndarray) -> None:
        board = puzzle_board.copy()
        assert SudokuSolver.explore_solutions(board) is True
        assert is_valid_solution(board, puzzle_board)

    def test_returns_true_for_already_complete_board(
        self, solved_board: np.ndarray
    ) -> None:
        board = solved_board.copy()
        assert SudokuSolver.explore_solutions(board) is True
        assert np.array_equal(board, solved_board)

    def test_returns_false_when_no_candidate_fits(
        self, unsolvable_board: np.ndarray
    ) -> None:
        assert SudokuSolver.explore_solutions(unsolvable_board.copy()) is False


class TestSolve:
    def test_returns_expected_solution(
        self, puzzle_board: np.ndarray, solved_board: np.ndarray
    ) -> None:
        assert np.array_equal(SudokuSolver.solve(puzzle_board), solved_board)

    def test_does_not_mutate_the_input_board(self, puzzle_board: np.ndarray) -> None:
        original = puzzle_board.copy()
        SudokuSolver.solve(puzzle_board)
        assert np.array_equal(puzzle_board, original)

    def test_solves_an_empty_board(self) -> None:
        empty = np.zeros((9, 9), dtype=int)
        assert is_valid_solution(SudokuSolver.solve(empty), empty)

    def test_raises_value_error_when_unsolvable(
        self, unsolvable_board: np.ndarray
    ) -> None:
        with pytest.raises(ValueError, match="No solution exists"):
            SudokuSolver.solve(unsolvable_board)
