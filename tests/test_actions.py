"""Unit tests for the deterministic safety layer and action validation."""

import pytest
from game.actions import TetrisAction
from game.tetris import TetrisGame


def test_action_validation_left_wall():
    game = TetrisGame(seed=1)
    # Move all the way to left wall
    while game.is_valid_action(TetrisAction.LEFT):
        game.apply_action(TetrisAction.LEFT)

    # Now LEFT should be invalid
    assert not game.is_valid_action(TetrisAction.LEFT)
    assert not game.apply_action(TetrisAction.LEFT)


def test_action_validation_right_wall():
    game = TetrisGame(seed=1)
    # Move all the way to right wall
    while game.is_valid_action(TetrisAction.RIGHT):
        game.apply_action(TetrisAction.RIGHT)

    # Now RIGHT should be invalid
    assert not game.is_valid_action(TetrisAction.RIGHT)
    assert not game.apply_action(TetrisAction.RIGHT)


def test_action_validation_when_game_over():
    game = TetrisGame(seed=1)
    game.game_over = True

    for act in [TetrisAction.LEFT, TetrisAction.RIGHT, TetrisAction.ROTATE_CW, TetrisAction.HARD_DROP]:
        assert not game.is_valid_action(act)
        assert not game.apply_action(act)
