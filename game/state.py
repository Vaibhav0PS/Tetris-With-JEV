"""Pydantic model representing the complete Tetris game state for Jev."""

from typing import List, Optional
from pydantic import BaseModel, Field


class TetrisState(BaseModel):
    """Compact structured representation of the Tetris board and gameplay status."""

    board: List[List[int]] = Field(
        description="20x10 binary matrix of board cells where 0=empty and 1=occupied."
    )
    current_piece: str = Field(description="Active falling piece type (I, O, T, S, Z, J, L).")
    current_x: int = Field(description="Current horizontal grid column of the active piece.")
    current_y: int = Field(description="Current vertical grid row of the active piece.")
    rotation: int = Field(description="Current orientation index (0 to 3).")
    next_piece: Optional[str] = Field(default=None, description="Upcoming piece waiting in queue.")
    hold_piece: Optional[str] = Field(default=None, description="Piece currently in the hold queue.")
    score: int = Field(default=0, description="Current game score.")
    level: int = Field(default=1, description="Current difficulty level.")
    lines_cleared: int = Field(default=0, description="Total number of lines cleared.")
    game_over: bool = Field(default=False, description="Whether the game has ended.")

    # High-level derived features to assist Jev AI decisions
    aggregate_height: int = Field(default=0, description="Sum of all column heights.")
    maximum_height: int = Field(default=0, description="Maximum height across all columns.")
    holes: int = Field(default=0, description="Number of covered empty holes.")
    bumpiness: int = Field(default=0, description="Variation between adjacent column heights.")
    completed_lines: int = Field(default=0, description="Number of completed full rows.")
    well_depth: int = Field(default=0, description="Sum of well depths.")
    column_heights: List[int] = Field(
        default_factory=list, description="List of heights for each of the 10 columns."
    )
