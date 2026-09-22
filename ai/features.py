"""Feature extraction functions for Tetris board states."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Union

if TYPE_CHECKING:
    from game.board import Board


def _extract_grid(board_data: Any) -> List[List[int]]:
    """Helper to extract grid rows from either a Board instance or a 2D list."""
    return board_data.grid if hasattr(board_data, "grid") else board_data


def get_column_heights(board_data: Union[Board, List[List[int]]]) -> List[int]:
    """
    Computes the height of each column on the board.
    Height is measured from the bottom row up to the highest occupied cell.
    """
    grid = _extract_grid(board_data)
    if not grid or not grid[0]:
        return []

    height = len(grid)
    width = len(grid[0])
    col_heights = [0] * width

    for c in range(width):
        for r in range(height):
            if grid[r][c] != 0:
                col_heights[c] = height - r
                break
    return col_heights


def get_aggregate_height(board_data: Union[Board, List[List[int]]]) -> int:
    """Calculates the sum of all column heights."""
    return sum(get_column_heights(board_data))


def get_maximum_height(board_data: Union[Board, List[List[int]]]) -> int:
    """Calculates the maximum column height across all columns."""
    heights = get_column_heights(board_data)
    return max(heights) if heights else 0


def get_holes_count(board_data: Union[Board, List[List[int]]]) -> int:
    """
    Counts the number of holes on the board.
    A hole is an empty cell that has at least one occupied cell directly or
    indirectly above it in the same column.
    """
    grid = _extract_grid(board_data)
    if not grid or not grid[0]:
        return 0

    height = len(grid)
    width = len(grid[0])
    holes = 0

    for c in range(width):
        found_block = False
        for r in range(height):
            if grid[r][c] != 0:
                found_block = True
            elif found_block and grid[r][c] == 0:
                holes += 1
    return holes


def get_bumpiness(board_data: Union[Board, List[List[int]]]) -> int:
    """
    Calculates the bumpiness of the board surface.
    Bumpiness is the sum of absolute differences between adjacent column heights.
    """
    heights = get_column_heights(board_data)
    if len(heights) < 2:
        return 0
    return sum(abs(heights[i] - heights[i + 1]) for i in range(len(heights) - 1))


def get_completed_lines(board_data: Union[Board, List[List[int]]]) -> int:
    """Counts the number of full horizontal lines waiting to be cleared."""
    grid = _extract_grid(board_data)
    return sum(1 for row in grid if all(cell != 0 for cell in row))


def get_well_depth(board_data: Union[Board, List[List[int]]]) -> int:
    """
    Calculates total well depth across the board.
    A well is a vertical valley between adjacent higher columns or board edges.
    """
    grid = _extract_grid(board_data)
    heights = get_column_heights(board_data)
    width = len(heights)
    if width == 0:
        return 0

    board_h = len(grid) if grid else 20
    total_well_depth = 0
    for c in range(width):
        left_h = heights[c - 1] if c > 0 else board_h
        right_h = heights[c + 1] if c < width - 1 else board_h
        wall_h = min(left_h, right_h)
        if wall_h > heights[c]:
            total_well_depth += (wall_h - heights[c])
    return total_well_depth


def get_blocked_cells(board_data: Union[Board, List[List[int]]]) -> int:
    """
    Counts how many occupied blocks are positioned above at least one hole in their column.
    """
    grid = _extract_grid(board_data)
    if not grid or not grid[0]:
        return 0

    height = len(grid)
    width = len(grid[0])
    blocked = 0

    for c in range(width):
        hole_found = False
        blocks_above_holes = 0
        for r in range(height - 1, -1, -1):
            if grid[r][c] == 0:
                hole_found = True
            elif hole_found and grid[r][c] != 0:
                blocks_above_holes += 1
        blocked += blocks_above_holes
    return blocked
