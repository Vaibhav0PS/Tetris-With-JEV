"""Unit tests for the Tetris board, collisions, and line clearing."""

import pytest
from game.board import Board
from game.pieces import Tetromino


def test_board_initialization():
    board = Board(width=10, height=20)
    assert board.width == 10
    assert board.height == 20
    assert len(board.grid) == 20
    assert len(board.grid[0]) == 10
    assert all(board.grid[r][c] == 0 for r in range(20) for c in range(10))


def test_board_boundaries():
    board = Board(10, 20)
    assert board.is_inside(0, 0)
    assert board.is_inside(9, 19)
    assert not board.is_inside(-1, 5)
    assert not board.is_inside(10, 5)
    assert not board.is_inside(5, 20)


def test_board_collision_with_walls():
    board = Board(10, 20)
    # Piece outside left wall
    piece_left = Tetromino(shape_type="I", x=-2, y=5, rotation=0)
    assert not board.is_valid_position(piece_left)

    # Piece outside right wall
    piece_right = Tetromino(shape_type="I", x=8, y=5, rotation=0)
    assert not board.is_valid_position(piece_right)

    # Piece within bounds
    piece_valid = Tetromino(shape_type="I", x=3, y=5, rotation=0)
    assert board.is_valid_position(piece_valid)


def test_board_locking_and_collision():
    board = Board(10, 20)
    piece = Tetromino(shape_type="O", x=4, y=18, rotation=0)
    assert board.is_valid_position(piece)
    board.lock_piece(piece)

    # Locked blocks should be non-zero
    for bx, by in piece.get_blocks():
        assert board.grid[by][bx] == piece.piece_id

    # Another piece cannot be placed overlapping the locked piece
    piece2 = Tetromino(shape_type="O", x=4, y=18, rotation=0)
    assert not board.is_valid_position(piece2)


def test_board_clear_lines():
    board = Board(10, 20)
    # Fill bottom row completely
    board.grid[19] = [1] * 10
    # Fill row 18 partially
    board.grid[18] = [1, 1, 0, 0, 1, 1, 1, 1, 1, 1]

    cleared = board.clear_lines()
    assert cleared == 1
    # Former row 18 should now be at row 19
    assert board.grid[19] == [1, 1, 0, 0, 1, 1, 1, 1, 1, 1]
    # Row 0 should be empty
    assert board.grid[0] == [0] * 10


def test_board_drop_distance():
    board = Board(10, 20)
    piece = Tetromino(shape_type="I", x=3, y=0, rotation=0)
    # Horizontal I piece has blocks at y=1: (3,1), (4,1), (5,1), (6,1)
    # Bottom row is 19. So it can drop 18 rows to reach y=19.
    dist = board.get_drop_distance(piece)
    assert dist == 18
