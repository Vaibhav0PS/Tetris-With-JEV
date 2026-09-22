"""Traditional Heuristic Tetris AI player based on surface evaluation."""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Tuple
from game.actions import TetrisAction
from game.board import Board
from game.pieces import Tetromino
from game.state import TetrisState

if TYPE_CHECKING:
    from game.tetris import TetrisGame
from ai.features import (
    get_aggregate_height,
    get_bumpiness,
    get_completed_lines,
    get_holes_count,
)
from ai.schemas import DecisionResult


class HeuristicPlayer:
    """
    Evaluates candidate landing positions using a weighted linear combination
    of standard Tetris heuristics (Dellacherie-style evaluation).
    """

    def __init__(
        self,
        weight_lines: float = 3.5,
        weight_height: float = -0.51,
        weight_holes: float = -3.5,
        weight_bumpiness: float = -0.35,
        weight_landing_height: float = -0.2,
    ):
        self.w_lines = weight_lines
        self.w_height = weight_height
        self.w_holes = weight_holes
        self.w_bumpiness = weight_bumpiness
        self.w_landing_height = weight_landing_height

    def evaluate_board(self, board: Board, lines_cleared: int, landing_height: int) -> float:
        """Computes heuristic score for a simulated resulting board."""
        agg_height = get_aggregate_height(board)
        holes = get_holes_count(board)
        bumpiness = get_bumpiness(board)

        return (
            self.w_lines * lines_cleared
            + self.w_height * agg_height
            + self.w_holes * holes
            + self.w_bumpiness * bumpiness
            + self.w_landing_height * landing_height
        )

    def find_best_placement(
        self, board: Board, piece_type: str
    ) -> Optional[Tuple[int, int, float]]:
        """
        Simulates all valid (rotation, x) placements for the piece type.
        Returns: (best_rotation, best_x, best_score)
        """
        best_score = float("-inf")
        best_placement: Optional[Tuple[int, int, float]] = None

        # Try all 4 rotations
        for rot in range(4):
            # Probe minimum and maximum horizontal coordinates
            probe_piece = Tetromino(shape_type=piece_type, x=0, y=0, rotation=rot)
            # Find leftmost and rightmost valid x for this rotation
            for target_x in range(-2, board.width + 2):
                test_piece = Tetromino(shape_type=piece_type, x=target_x, y=0, rotation=rot)
                # Check if piece fits within board columns at top
                if not board.is_valid_position(test_piece):
                    continue

                # Drop piece to floor
                drop_dist = board.get_drop_distance(test_piece)
                dropped_piece = Tetromino(
                    shape_type=piece_type, x=target_x, y=drop_dist, rotation=rot
                )

                # Simulate board after locking
                sim_board = board.copy()
                sim_board.lock_piece(dropped_piece)
                lines = sim_board.clear_lines()

                landing_height = board.height - (dropped_piece.y)
                score = self.evaluate_board(sim_board, lines, landing_height)

                if score > best_score:
                    best_score = score
                    best_placement = (rot, target_x, score)

        return best_placement

    def choose_action(
        self, state: TetrisState, game: Optional[TetrisGame] = None
    ) -> DecisionResult:
        """Determines the next step toward the optimal placement."""
        board = Board(len(state.board[0]), len(state.board))
        board.grid = [row[:] for row in state.board]

        placement = self.find_best_placement(board, state.current_piece)
        if placement is None:
            # Safe fallback if no placement found
            return DecisionResult(
                action=TetrisAction.SOFT_DROP,
                confidence=0.5,
                source="heuristic",
            )

        target_rot, target_x, _ = placement

        # Step 1: Align rotation
        if state.rotation != target_rot:
            # Decide CW or CCW
            rot_diff = (target_rot - state.rotation) % 4
            action = TetrisAction.ROTATE_CW if rot_diff <= 2 else TetrisAction.ROTATE_CCW
            # If game provided, verify validity
            if game is None or game.is_valid_action(action):
                return DecisionResult(action=action, confidence=0.95, source="heuristic")

        # Step 2: Align horizontal column
        if state.current_x < target_x:
            action = TetrisAction.RIGHT
            if game is None or game.is_valid_action(action):
                return DecisionResult(action=action, confidence=0.90, source="heuristic")
        elif state.current_x > target_x:
            action = TetrisAction.LEFT
            if game is None or game.is_valid_action(action):
                return DecisionResult(action=action, confidence=0.90, source="heuristic")

        # Step 3: Aligned! Execute drop
        action = TetrisAction.HARD_DROP
        if game is None or game.is_valid_action(action):
            return DecisionResult(action=action, confidence=0.99, source="heuristic")

        return DecisionResult(action=TetrisAction.SOFT_DROP, confidence=0.8, source="heuristic")
