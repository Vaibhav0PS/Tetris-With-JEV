"""Unit tests for the TetrisGame engine, mechanics, scoring, and hold piece."""

import pytest
from game.actions import TetrisAction
from game.pieces import Tetromino
from game.tetris import TetrisGame


def test_game_initialization():
    game = TetrisGame(seed=42)
    assert not game.game_over
    assert game.score == 0
    assert game.level == 1
    assert game.lines_cleared == 0
    assert game.current_piece is not None
    assert game.next_piece_type in ["I", "O", "T", "S", "Z", "J", "L"]
    assert game.hold_piece_type is None
    assert game.can_hold is True


def test_movement_actions():
    game = TetrisGame(seed=10)
    init_x = game.current_piece.x
    assert game.apply_action(TetrisAction.LEFT)
    assert game.current_piece.x == init_x - 1

    assert game.apply_action(TetrisAction.RIGHT)
    assert game.current_piece.x == init_x


def test_rotation_actions():
    game = TetrisGame(seed=10)
    init_rot = game.current_piece.rotation
    assert game.apply_action(TetrisAction.ROTATE_CW)
    assert game.current_piece.rotation == (init_rot + 1) % 4

    assert game.apply_action(TetrisAction.ROTATE_CCW)
    assert game.current_piece.rotation == init_rot


def test_soft_drop_and_hard_drop():
    game = TetrisGame(seed=10)
    init_y = game.current_piece.y
    assert game.apply_action(TetrisAction.SOFT_DROP)
    assert game.current_piece.y == init_y + 1
    assert game.score == 1

    # Hard drop should lock the piece and spawn the next piece
    old_piece = game.current_piece.shape_type
    assert game.apply_action(TetrisAction.HARD_DROP)
    assert game.score > 1
    # Next piece is now active
    assert game.current_piece.y == 0


def test_hold_piece():
    game = TetrisGame(seed=123)
    first_piece = game.current_piece.shape_type
    assert game.can_hold is True

    # Hold first piece
    assert game.apply_action(TetrisAction.HOLD)
    assert game.hold_piece_type == first_piece
    assert game.can_hold is False

    # Cannot hold again immediately on the same piece
    assert not game.apply_action(TetrisAction.HOLD)

    # After hard dropping, can hold again
    game.apply_action(TetrisAction.HARD_DROP)
    assert game.can_hold is True


def test_line_clearing_and_scoring():
    game = TetrisGame(seed=99)
    # Prefill row 19 with 9 blocks (leaving column 5 empty)
    for c in range(10):
        if c != 5:
            game.board.grid[19][c] = 1

    # Place an I piece directly into col 5 or manipulate piece to fill row 19
    game.board.grid[19][5] = 1
    cleared = game.board.clear_lines()
    assert cleared == 1


def test_game_over_detection():
    game = TetrisGame(seed=5)
    # Stack blocks all the way to top
    for r in range(20):
        for c in range(10):
            game.board.grid[r][c] = 1

    # Next piece spawn will collide immediately
    game._spawn_piece("O")
    assert game.game_over is True


def test_state_serialization():
    game = TetrisGame(seed=42)
    state = game.get_state()
    assert len(state.board) == 20
    assert len(state.board[0]) == 10
    assert state.current_piece == game.current_piece.shape_type
    assert state.score == 0
    assert state.level == 1
    assert isinstance(state.aggregate_height, int)
    assert isinstance(state.holes, int)
