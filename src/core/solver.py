"""
Provides the SudokuSolver class with methods to validate and solve a Sudoku puzzle.
"""

import numpy as np


class SudokuSolver:
    """
    A class that implements a backtracking algorithm to solve Sudoku puzzles.
    """

    @staticmethod
    def is_valid(board: np.ndarray, row: int, col: int, num: int) -> bool:
        """
        Determines whether placing 'num' in board[row][col] is valid.

        :param board: 9x9 Sudoku board.
        :param row: Row index.
        :param col: Column index.
        :param num: Number to validate.
        :return: True if valid, False otherwise.
        """
        if num in board[row]:
            return False
        if num in board[:, col]:
            return False

        start_row, start_col = row - row % 3, col - col % 3
        if num in board[start_row : start_row + 3, start_col : start_col + 3]:
            return False
        return True

    @staticmethod
    def explore_solutions(board: np.ndarray) -> bool:
        """
        Recursively solves the Sudoku board using backtracking.

        :param board: 9x9 Sudoku board.
        :return: True if a solution is found; False otherwise.
        """
        for row in range(9):
            for col in range(9):
                if board[row, col] == 0:
                    for num in range(1, 10):
                        if SudokuSolver.is_valid(board, row, col, num):
                            board[row, col] = num
                            if SudokuSolver.explore_solutions(board):
                                return True
                            board[row, col] = 0
                    return False
        return True

    @staticmethod
    def solve(board: np.ndarray) -> np.ndarray:
        """
        Solves the provided Sudoku puzzle.

        :param board: 9x9 Sudoku board with zeros for empty cells.
        :return: Solved Sudoku board.
        :raises ValueError: If no solution exists.
        """
        board_copy = board.copy()
        if SudokuSolver.explore_solutions(board_copy):
            return board_copy
        else:
            raise ValueError("No solution exists for the provided Sudoku puzzle.")
