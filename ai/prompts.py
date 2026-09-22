"""Prompts and state formatting for the Jev AI agent."""

from typing import Optional, Tuple
from game.board import Board
from game.state import TetrisState
from ai.heuristic_player import HeuristicPlayer

_heuristic = HeuristicPlayer()

JEV_SYSTEM_INSTRUCTION = """You are an autonomous AI agent controlling a live Tetris game.
Your task is to select the single best next action from the available actions.

Decision Objectives:
- Keep aggregate and maximum board heights as low as possible.
- Avoid creating holes or enclosed empty spaces.
- Minimize board surface bumpiness across columns.
- Complete and clear horizontal lines whenever possible.
- Steer pieces horizontally (left or right) to flat areas or valleys before dropping.
- NEVER hard_drop into the center columns if they are already tall.
- Use hard_drop ONLY when the piece has reached the target column and correct orientation.

You must output exactly one valid Tetris action.
You are not writing an explanation. You are directly controlling the game engine."""


def format_state_prompt(state: TetrisState) -> str:
    """
    Formats the TetrisState into a concise, high-signal text prompt for Jev.
    Includes active piece info, derived features, tactical guidance, and compact board view.
    """
    board = Board(len(state.board[0]), len(state.board))
    board.grid = [row[:] for row in state.board]
    placement = _heuristic.find_best_placement(board, state.current_piece)

    strategy_guidance = ""
    if placement is not None:
        target_rot, target_x, _ = placement
        if state.rotation != target_rot:
            strategy_guidance = (
                f"ORIENTATION: Current rotation {state.rotation} != target {target_rot}. "
                f"Action needed: ROTATE_CW to align piece flat."
            )
        elif state.current_x > target_x:
            strategy_guidance = (
                f"HORIZONTAL STEERING: Piece is at column {state.current_x}, but target valley is at column {target_x}. "
                f"Action needed: Move LEFT towards column {target_x}. Do NOT hard_drop here!"
            )
        elif state.current_x < target_x:
            strategy_guidance = (
                f"HORIZONTAL STEERING: Piece is at column {state.current_x}, but target valley is at column {target_x}. "
                f"Action needed: Move RIGHT towards column {target_x}. Do NOT hard_drop here!"
            )
        else:
            strategy_guidance = (
                f"TARGET REACHED: Piece is aligned at target column {state.current_x} with rotation {state.rotation}. "
                f"Action needed: HARD_DROP to lock securely."
            )

    # Only render rows from the highest occupied row down to row 19 to keep context compact
    highest_row = max(0, 20 - state.maximum_height - 2) if state.maximum_height > 0 else 18
    rendered_rows = []
    for r in range(highest_row, 20):
        row_str = " ".join("#" if cell != 0 else "." for cell in state.board[r])
        rendered_rows.append(f"R{r:02d}: {row_str}")

    board_view = "\n".join(rendered_rows) if rendered_rows else "All empty"

    return f"""TETRIS GAME STATE:
Active Piece: {state.current_piece} (col x={state.current_x}, row y={state.current_y}, rotation={state.rotation})
Next Piece: {state.next_piece or 'None'} | Hold: {state.hold_piece or 'None'}
Score: {state.score} | Level: {state.level} | Lines: {state.lines_cleared}

Surface Analysis:
- Aggregate Height: {state.aggregate_height} | Max Height: {state.maximum_height} | Holes: {state.holes}
- Column Heights: {state.column_heights}
- Tactical Advice: {strategy_guidance}

Board (active rows, #=block, .=empty):
{board_view}

Select the single best next action (left, right, rotate_cw, rotate_ccw, soft_drop, hard_drop, hold, noop)."""
