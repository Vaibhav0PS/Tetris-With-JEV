"""Tetris Board representation, collision detection, and line clearing."""

from typing import List, Optional, Tuple
from game.pieces import Tetromino

DEFAULT_WIDTH = 10
DEFAULT_HEIGHT = 20


class Board:
    """Represents a 10x20 Tetris grid."""

    def __init__(self, width: int = DEFAULT_WIDTH, height: int = DEFAULT_HEIGHT):
        self.width = width
        self.height = height
        # 2D list of shape [height][width], row 0 is top, row (height-1) is bottom
        self.grid: List[List[int]] = [[0 for _ in range(self.width)] for _ in range(self.height)]

    def is_inside(self, x: int, y: int) -> bool:
        """Checks if (x, y) is within the horizontal boundaries and above floor."""
        return 0 <= x < self.width and y < self.height

    def is_cell_empty(self, x: int, y: int) -> bool:
        """Checks if a cell is free. Cells above board (y < 0) are considered empty."""
        if not (0 <= x < self.width):
            return False
        if y < 0:
            return True
        if y >= self.height:
            return False
        return self.grid[y][x] == 0

    def is_valid_position(
        self,
        piece: Tetromino,
        offset_x: int = 0,
        offset_y: int = 0,
        rotation: Optional[int] = None,
    ) -> bool:
        """Determines if a piece at the proposed position/rotation fits without collision."""
        blocks = piece.get_blocks(rotation=rotation, offset_x=offset_x, offset_y=offset_y)
        for bx, by in blocks:
            if not self.is_cell_empty(bx, by):
                return False
        return True

    def lock_piece(self, piece: Tetromino) -> None:
        """Locks a piece permanently onto the grid."""
        for bx, by in piece.get_blocks():
            if 0 <= by < self.height and 0 <= bx < self.width:
                self.grid[by][bx] = piece.piece_id

    def clear_lines(self) -> int:
        """Clears fully occupied lines and inserts empty lines at top. Returns lines cleared."""
        new_grid = [row for row in self.grid if any(cell == 0 for cell in row)]
        lines_cleared = self.height - len(new_grid)
        for _ in range(lines_cleared):
            new_grid.insert(0, [0 for _ in range(self.width)])
        self.grid = new_grid
        return lines_cleared

    def get_drop_distance(self, piece: Tetromino) -> int:
        """Calculates how many rows the piece can fall before hitting the floor or a locked piece."""
        dy = 0
        while self.is_valid_position(piece, offset_y=dy + 1):
            dy += 1
        return dy

    def to_binary_matrix(self) -> List[List[int]]:
        """Returns a 20x10 matrix where 0 = empty and 1 = occupied."""
        return [[1 if cell != 0 else 0 for cell in row] for row in self.grid]

    def copy(self) -> "Board":
        """Creates an independent deep copy of the board."""
        new_board = Board(width=self.width, height=self.height)
        new_board.grid = [row[:] for row in self.grid]
        return new_board
