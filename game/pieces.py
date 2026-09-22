"""Tetromino piece definitions, rotation matrices, and piece shapes."""

from dataclasses import dataclass
from typing import Dict, List, Tuple

# 4 rotations for each tetromino (dx, dy) offsets relative to piece origin (x, y)
TETROMINO_SHAPES: Dict[str, List[List[Tuple[int, int]]]] = {
    "I": [
        [(0, 1), (1, 1), (2, 1), (3, 1)],  # 0: horizontal
        [(2, 0), (2, 1), (2, 2), (2, 3)],  # 1: vertical
        [(0, 2), (1, 2), (2, 2), (3, 2)],  # 2: horizontal shifted
        [(1, 0), (1, 1), (1, 2), (1, 3)],  # 3: vertical shifted
    ],
    "O": [
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)],
    ],
    "T": [
        [(1, 0), (0, 1), (1, 1), (2, 1)],  # 0: flat bottom, point up
        [(1, 0), (1, 1), (2, 1), (1, 2)],  # 1: flat left, point right
        [(0, 1), (1, 1), (2, 1), (1, 2)],  # 2: flat top, point down
        [(1, 0), (0, 1), (1, 1), (1, 2)],  # 3: flat right, point left
    ],
    "S": [
        [(1, 0), (2, 0), (0, 1), (1, 1)],
        [(1, 0), (1, 1), (2, 1), (2, 2)],
        [(1, 1), (2, 1), (0, 2), (1, 2)],
        [(0, 0), (0, 1), (1, 1), (1, 2)],
    ],
    "Z": [
        [(0, 0), (1, 0), (1, 1), (2, 1)],
        [(2, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 1), (1, 1), (1, 2), (2, 2)],
        [(1, 0), (0, 1), (1, 1), (0, 2)],
    ],
    "J": [
        [(0, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (2, 2)],
        [(1, 0), (1, 1), (0, 2), (1, 2)],
    ],
    "L": [
        [(2, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (1, 2), (2, 2)],
        [(0, 1), (1, 1), (2, 1), (0, 2)],
        [(0, 0), (1, 0), (1, 1), (1, 2)],
    ],
}

# Standard vibrant modern palette for Pygame UI
TETROMINO_COLORS: Dict[str, Tuple[int, int, int]] = {
    "I": (0, 230, 254),    # Cyan
    "O": (255, 213, 0),    # Yellow
    "T": (180, 70, 255),   # Purple
    "S": (76, 217, 100),   # Green
    "Z": (255, 59, 48),    # Red
    "J": (0, 122, 255),    # Blue
    "L": (255, 149, 0),    # Orange
}

# Numeric ID representation for each piece type (1-7, 0 = empty)
PIECE_TYPE_IDS: Dict[str, int] = {
    "I": 1,
    "O": 2,
    "T": 3,
    "S": 4,
    "Z": 5,
    "J": 6,
    "L": 7,
}

ALL_PIECE_TYPES: List[str] = ["I", "O", "T", "S", "Z", "J", "L"]


@dataclass
class Tetromino:
    """Represents an active falling piece on the board."""

    shape_type: str
    x: int
    y: int
    rotation: int = 0

    @property
    def color(self) -> Tuple[int, int, int]:
        return TETROMINO_COLORS[self.shape_type]

    @property
    def piece_id(self) -> int:
        return PIECE_TYPE_IDS[self.shape_type]

    def get_blocks(self, rotation: int | None = None, offset_x: int = 0, offset_y: int = 0) -> List[Tuple[int, int]]:
        """Returns the absolute coordinates [(x, y), ...] for this piece."""
        rot = (self.rotation if rotation is None else rotation) % 4
        offsets = TETROMINO_SHAPES[self.shape_type][rot]
        px = self.x + offset_x
        py = self.y + offset_y
        return [(px + dx, py + dy) for dx, dy in offsets]

    def copy(self) -> "Tetromino":
        return Tetromino(
            shape_type=self.shape_type,
            x=self.x,
            y=self.y,
            rotation=self.rotation,
        )
