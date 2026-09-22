"""Core Tetris game engine decoupled from any graphical user interface."""

import random
from typing import List, Optional, Tuple

from game.actions import TetrisAction
from game.board import Board, DEFAULT_HEIGHT, DEFAULT_WIDTH
from game.pieces import ALL_PIECE_TYPES, Tetromino
from game.state import TetrisState
from ai.features import (
    get_aggregate_height,
    get_bumpiness,
    get_column_heights,
    get_completed_lines,
    get_holes_count,
    get_maximum_height,
    get_well_depth,
)

# Standard line clear score multipliers
LINE_POINTS = {
    0: 0,
    1: 100,
    2: 300,
    3: 500,
    4: 800,
}


class TetrisGame:
    """Headless, deterministic Tetris engine supporting Human and AI play."""

    def __init__(
        self,
        width: int = DEFAULT_WIDTH,
        height: int = DEFAULT_HEIGHT,
        seed: Optional[int] = None,
    ):
        self.width = width
        self.height = height
        self._rng = random.Random(seed)

        self.board = Board(width=self.width, height=self.height)
        self.score: int = 0
        self.level: int = 1
        self.lines_cleared: int = 0
        self.game_over: bool = False
        self.can_hold: bool = True

        self.bag: List[str] = []
        self.current_piece: Tetromino = self._spawn_initial_piece()
        self.next_piece_type: str = self._peek_next_piece()
        self.hold_piece_type: Optional[str] = None

    def _refill_bag(self) -> None:
        """Refills the piece bag using the standard 7-bag randomizer."""
        pieces = ALL_PIECE_TYPES.copy()
        self._rng.shuffle(pieces)
        self.bag.extend(pieces)

    def _get_next_piece_from_bag(self) -> str:
        """Pulls the next piece from the 7-bag."""
        if not self.bag:
            self._refill_bag()
        return self.bag.pop(0)

    def _peek_next_piece(self) -> str:
        """Peeks at the next piece waiting in the queue without consuming it."""
        if not self.bag:
            self._refill_bag()
        return self.bag[0]

    def _create_tetromino(self, piece_type: str) -> Tetromino:
        """Instantiates a piece centered at the top spawn position."""
        # I piece is 4 wide, spawns centered horizontally at x=3
        # O piece is 2 wide, spawns centered horizontally at x=4
        # Others spawn at x=3
        spawn_x = 4 if piece_type == "O" else 3
        spawn_y = 0
        return Tetromino(shape_type=piece_type, x=spawn_x, y=spawn_y, rotation=0)

    def _spawn_initial_piece(self) -> Tetromino:
        """Spawns the first piece for the game."""
        piece_type = self._get_next_piece_from_bag()
        return self._create_tetromino(piece_type)

    def _spawn_piece(self, piece_type: str) -> None:
        """Spawns a new active piece and checks for top-out game over."""
        self.current_piece = self._create_tetromino(piece_type)
        self.next_piece_type = self._peek_next_piece()
        self.can_hold = True

        if not self.board.is_valid_position(self.current_piece):
            self.game_over = True

    def _try_rotation(self, new_rotation: int) -> bool:
        """
        Attempts to rotate the active piece, testing basic position and standard wall-kicks.
        Returns True if rotation was applied.
        """
        kicks: List[Tuple[int, int]] = [(0, 0), (-1, 0), (1, 0), (-2, 0), (2, 0), (0, -1)]
        for kx, ky in kicks:
            if self.board.is_valid_position(
                self.current_piece, offset_x=kx, offset_y=ky, rotation=new_rotation
            ):
                self.current_piece.rotation = new_rotation
                self.current_piece.x += kx
                self.current_piece.y += ky
                return True
        return False

    def is_valid_action(self, action: TetrisAction) -> bool:
        """
        Deterministic safety check: verifies whether an action is legal
        in the current engine state without modifying the state.
        """
        if self.game_over:
            return False

        if action == TetrisAction.NOOP:
            return True

        if action == TetrisAction.LEFT:
            return self.board.is_valid_position(self.current_piece, offset_x=-1)

        if action == TetrisAction.RIGHT:
            return self.board.is_valid_position(self.current_piece, offset_x=1)

        if action == TetrisAction.ROTATE_CW:
            target_rot = (self.current_piece.rotation + 1) % 4
            kicks: List[Tuple[int, int]] = [(0, 0), (-1, 0), (1, 0), (-2, 0), (2, 0), (0, -1)]
            return any(
                self.board.is_valid_position(
                    self.current_piece, offset_x=kx, offset_y=ky, rotation=target_rot
                )
                for kx, ky in kicks
            )

        if action == TetrisAction.ROTATE_CCW:
            target_rot = (self.current_piece.rotation - 1) % 4
            kicks: List[Tuple[int, int]] = [(0, 0), (-1, 0), (1, 0), (-2, 0), (2, 0), (0, -1)]
            return any(
                self.board.is_valid_position(
                    self.current_piece, offset_x=kx, offset_y=ky, rotation=target_rot
                )
                for kx, ky in kicks
            )

        if action == TetrisAction.SOFT_DROP:
            # Valid if it can move down at least 1 row, or if it can lock
            return True

        if action == TetrisAction.HARD_DROP:
            return True

        if action == TetrisAction.HOLD:
            return self.can_hold

        return False

    def apply_action(self, action: TetrisAction) -> bool:
        """
        Applies a validated action to the game.
        Returns True if successfully executed, False if rejected.
        """
        if not self.is_valid_action(action):
            return False

        if action == TetrisAction.NOOP:
            return True

        if action == TetrisAction.LEFT:
            self.current_piece.x -= 1
            return True

        if action == TetrisAction.RIGHT:
            self.current_piece.x += 1
            return True

        if action == TetrisAction.ROTATE_CW:
            target_rot = (self.current_piece.rotation + 1) % 4
            return self._try_rotation(target_rot)

        if action == TetrisAction.ROTATE_CCW:
            target_rot = (self.current_piece.rotation - 1) % 4
            return self._try_rotation(target_rot)

        if action == TetrisAction.SOFT_DROP:
            if self.board.is_valid_position(self.current_piece, offset_y=1):
                self.current_piece.y += 1
                self.score += 1
                return True
            else:
                self._lock_active_piece()
                return True

        if action == TetrisAction.HARD_DROP:
            drop_dist = self.board.get_drop_distance(self.current_piece)
            self.current_piece.y += drop_dist
            self.score += drop_dist * 2
            self._lock_active_piece()
            return True

        if action == TetrisAction.HOLD:
            if not self.can_hold:
                return False
            self.can_hold = False
            cur_type = self.current_piece.shape_type
            if self.hold_piece_type is None:
                self.hold_piece_type = cur_type
                next_type = self._get_next_piece_from_bag()
                self._spawn_piece(next_type)
            else:
                swap_type = self.hold_piece_type
                self.hold_piece_type = cur_type
                self._spawn_piece(swap_type)
            # Re-disallow hold until next piece locks
            self.can_hold = False
            return True

        return False

    def tick(self) -> bool:
        """
        Executes one natural gravity step.
        Returns True if piece fell, or False if piece locked or game ended.
        """
        if self.game_over:
            return False

        if self.board.is_valid_position(self.current_piece, offset_y=1):
            self.current_piece.y += 1
            return True
        else:
            self._lock_active_piece()
            return False

    def _lock_active_piece(self) -> None:
        """Locks the active piece onto the board, tallies lines and score, and spawns the next piece."""
        self.board.lock_piece(self.current_piece)
        cleared = self.board.clear_lines()
        if cleared > 0:
            self.lines_cleared += cleared
            self.score += LINE_POINTS.get(cleared, cleared * 200) * self.level
            self.level = 1 + (self.lines_cleared // 10)

        next_type = self._get_next_piece_from_bag()
        self._spawn_piece(next_type)

    def get_gravity_interval_ms(self) -> int:
        """Calculates natural drop interval based on the current level."""
        return max(100, int(800 * (0.85 ** (self.level - 1))))

    def get_ghost_y(self) -> int:
        """Returns the y-coordinate of the ghost piece (projected landing position)."""
        return self.current_piece.y + self.board.get_drop_distance(self.current_piece)

    def get_state(self) -> TetrisState:
        """
        Extracts a clean, serializable Pydantic TetrisState model
        representing the current board and gameplay metrics.
        """
        binary_board = self.board.to_binary_matrix()
        return TetrisState(
            board=binary_board,
            current_piece=self.current_piece.shape_type,
            current_x=self.current_piece.x,
            current_y=self.current_piece.y,
            rotation=self.current_piece.rotation,
            next_piece=self.next_piece_type,
            hold_piece=self.hold_piece_type,
            score=self.score,
            level=self.level,
            lines_cleared=self.lines_cleared,
            game_over=self.game_over,
            aggregate_height=get_aggregate_height(self.board),
            maximum_height=get_maximum_height(self.board),
            holes=get_holes_count(self.board),
            bumpiness=get_bumpiness(self.board),
            completed_lines=get_completed_lines(self.board),
            well_depth=get_well_depth(self.board),
            column_heights=get_column_heights(self.board),
        )

    def reset(self, seed: Optional[int] = None) -> None:
        """Resets the game state for a new match."""
        if seed is not None:
            self._rng = random.Random(seed)
        self.board = Board(width=self.width, height=self.height)
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.game_over = False
        self.can_hold = True
        self.bag.clear()
        self.hold_piece_type = None
        self.current_piece = self._spawn_initial_piece()
        self.next_piece_type = self._peek_next_piece()
