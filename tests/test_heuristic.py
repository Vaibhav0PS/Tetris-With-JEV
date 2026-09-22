"""Unit tests for the Heuristic AI player."""

import pytest
from game.actions import TetrisAction
from game.board import Board
from game.tetris import TetrisGame
from ai.heuristic_player import HeuristicPlayer


def test_heuristic_evaluates_board():
    hp = HeuristicPlayer()
    board = Board(10, 20)
    score1 = hp.evaluate_board(board, lines_cleared=0, landing_height=0)

    # A board with completed lines should score higher than a board with holes
    board_with_holes = Board(10, 20)
    board_with_holes.grid[17][0] = 1
    board_with_holes.grid[19][0] = 1  # hole at 18
    score_holes = hp.evaluate_board(board_with_holes, lines_cleared=0, landing_height=5)

    assert score1 > score_holes


def test_heuristic_player_chooses_valid_action():
    game = TetrisGame(seed=12)
    hp = HeuristicPlayer()

    state = game.get_state()
    decision = hp.choose_action(state, game)

    assert decision.action in TetrisAction
    assert game.is_valid_action(decision.action)
    assert game.apply_action(decision.action)


def test_heuristic_plays_multiple_steps():
    game = TetrisGame(seed=42)
    hp = HeuristicPlayer()

    # Let the heuristic play 30 actions
    for _ in range(30):
        if game.game_over:
            break
        state = game.get_state()
        decision = hp.choose_action(state, game)
        assert game.is_valid_action(decision.action)
        game.apply_action(decision.action)

    # Game should still be alive and piece moved/dropped
    assert not game.game_over
    assert game.score >= 0
