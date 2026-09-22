"""Unit tests for Tetromino pieces and rotations."""

import pytest
from game.pieces import ALL_PIECE_TYPES, TETROMINO_SHAPES, Tetromino


def test_all_seven_pieces_exist():
    assert len(ALL_PIECE_TYPES) == 7
    for p in ["I", "O", "T", "S", "Z", "J", "L"]:
        assert p in ALL_PIECE_TYPES
        assert p in TETROMINO_SHAPES
        assert len(TETROMINO_SHAPES[p]) == 4  # 4 rotations each


def test_tetromino_blocks_calculation():
    piece = Tetromino(shape_type="O", x=4, y=0, rotation=0)
    blocks = piece.get_blocks()
    assert len(blocks) == 4
    # O piece offsets: (1,0), (2,0), (1,1), (2,1)
    assert (5, 0) in blocks
    assert (6, 0) in blocks
    assert (5, 1) in blocks
    assert (6, 1) in blocks


def test_tetromino_rotation():
    piece = Tetromino(shape_type="I", x=3, y=5, rotation=0)
    # Rotation 0 is horizontal: (0,1), (1,1), (2,1), (3,1)
    b0 = piece.get_blocks()
    assert (3, 6) in b0
    assert (4, 6) in b0
    assert (5, 6) in b0
    assert (6, 6) in b0

    # Rotation 1 is vertical: (2,0), (2,1), (2,2), (2,3)
    b1 = piece.get_blocks(rotation=1)
    assert (5, 5) in b1
    assert (5, 6) in b1
    assert (5, 7) in b1
    assert (5, 8) in b1


def test_tetromino_copy():
    piece = Tetromino(shape_type="T", x=2, y=3, rotation=1)
    copy_p = piece.copy()
    assert copy_p.shape_type == piece.shape_type
    assert copy_p.x == piece.x
    assert copy_p.y == piece.y
    assert copy_p.rotation == piece.rotation
    copy_p.x += 1
    assert piece.x == 2
