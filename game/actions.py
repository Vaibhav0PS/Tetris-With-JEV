"""Tetris action definitions."""

from enum import Enum


class TetrisAction(str, Enum):
    """Enumeration of possible discrete actions in Tetris."""

    LEFT = "left"
    RIGHT = "right"
    ROTATE_CW = "rotate_cw"
    ROTATE_CCW = "rotate_ccw"
    SOFT_DROP = "soft_drop"
    HARD_DROP = "hard_drop"
    HOLD = "hold"
    NOOP = "noop"
