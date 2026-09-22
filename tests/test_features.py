"""Unit tests for derived board metrics and feature extraction."""

import pytest
from game.board import Board
from ai.features import (
    get_aggregate_height,
    get_bumpiness,
    get_column_heights,
    get_completed_lines,
    get_holes_count,
    get_maximum_height,
    get_well_depth,
    get_blocked_cells,
)


def test_empty_board_features():
    board = Board(10, 20)
    assert get_column_heights(board) == [0] * 10
    assert get_aggregate_height(board) == 0
    assert get_maximum_height(board) == 0
    assert get_holes_count(board) == 0
    assert get_bumpiness(board) == 0
    assert get_completed_lines(board) == 0


def test_column_heights_and_aggregate():
    board = Board(10, 20)
    # Put a block at col 0, bottom row 19 -> height 1
    board.grid[19][0] = 1
    # Put a block at col 1, row 17 -> height 3 (since 20 - 17 = 3)
    board.grid[17][1] = 1

    heights = get_column_heights(board)
    assert heights[0] == 1
    assert heights[1] == 3
    assert heights[2] == 0
    assert get_aggregate_height(board) == 4
    assert get_maximum_height(board) == 3


def test_holes_count():
    board = Board(10, 20)
    # Column 0: block at row 17, empty at row 18, block at row 19 -> 1 hole at row 18
    board.grid[17][0] = 1
    board.grid[18][0] = 0
    board.grid[19][0] = 1

    # Column 1: block at row 16, empty at rows 17, 18, 19 -> 3 holes
    board.grid[16][1] = 1
    board.grid[17][1] = 0
    board.grid[18][1] = 0
    board.grid[19][1] = 0

    assert get_holes_count(board) == 4


def test_bumpiness():
    board = Board(4, 10)
    # Set column heights to: [2, 5, 3, 1]
    # Row 10 is bottom, so row 8 = height 2, row 5 = height 5, row 7 = height 3, row 9 = height 1
    board.grid[8][0] = 1
    board.grid[5][1] = 1
    board.grid[7][2] = 1
    board.grid[9][3] = 1

    # Bumpiness = |2 - 5| + |5 - 3| + |3 - 1| = 3 + 2 + 2 = 7
    assert get_bumpiness(board) == 7


def test_completed_lines():
    board = Board(10, 20)
    board.grid[19] = [1] * 10
    board.grid[18] = [1] * 10
    board.grid[17] = [1, 1, 0, 1, 1, 1, 1, 1, 1, 1]
    assert get_completed_lines(board) == 2


def test_well_depth():
    board = Board(5, 10)
    # Columns heights: [3, 0, 3, 2, 2]
    # Col 1 has height 0, walls on left (3) and right (3) -> well of depth min(3,3) - 0 = 3
    board.grid[7][0] = 1
    board.grid[7][2] = 1
    board.grid[8][3] = 1
    board.grid[8][4] = 1

    wells = get_well_depth(board)
    assert wells >= 3
