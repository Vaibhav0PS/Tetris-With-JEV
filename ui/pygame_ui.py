"""Modern graphical interface for Tetris supporting Human and Jev AI play."""

import math
import time
from typing import Optional, Tuple
import pygame

from game.actions import TetrisAction
from game.board import Board
from game.pieces import TETROMINO_COLORS, TETROMINO_SHAPES, Tetromino
from game.state import TetrisState
from game.tetris import TetrisGame
from ai.schemas import DecisionResult

# UI Dimensions
CELL_SIZE = 30
BOARD_COLS = 10
BOARD_ROWS = 20
BOARD_WIDTH = BOARD_COLS * CELL_SIZE
BOARD_HEIGHT = BOARD_ROWS * CELL_SIZE

SIDEBAR_LEFT_WIDTH = 190
SIDEBAR_RIGHT_WIDTH = 340
SCREEN_WIDTH = SIDEBAR_LEFT_WIDTH + BOARD_WIDTH + SIDEBAR_RIGHT_WIDTH + 60
SCREEN_HEIGHT = BOARD_HEIGHT + 60

# Color Palette (Dark modern theme)
COLOR_BG = (16, 18, 27)
COLOR_PANEL_BG = (24, 27, 39)
COLOR_PANEL_BORDER = (45, 50, 72)
COLOR_GRID_BG = (12, 14, 22)
COLOR_GRID_LINE = (28, 32, 48)
COLOR_TEXT_WHITE = (240, 243, 246)
COLOR_TEXT_MUTED = (140, 146, 172)
COLOR_ACCENT_CYAN = (0, 220, 255)
COLOR_ACCENT_GREEN = (50, 220, 120)
COLOR_ACCENT_PURPLE = (180, 100, 255)
COLOR_ACCENT_RED = (255, 75, 75)
COLOR_ACCENT_AMBER = (255, 170, 30)


class TetrisUI:
    """Renders the game board, telemetry panels, and handles user inputs."""

    def __init__(self, game: TetrisGame):
        self.game = game
        pygame.init()
        pygame.font.init()
        pygame.display.set_caption("Tetris Autonomous Jev AI (TypeSafe)")

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()

        # Fonts
        self.font_title = pygame.font.SysFont("Segoe UI, Arial", 22, bold=True)
        self.font_heading = pygame.font.SysFont("Segoe UI, Arial", 16, bold=True)
        self.font_body = pygame.font.SysFont("Segoe UI, Arial", 14)
        self.font_small = pygame.font.SysFont("Segoe UI, Arial", 12)
        self.font_mono = pygame.font.SysFont("Consolas, Courier", 13)

        # Offsets
        self.board_x = SIDEBAR_LEFT_WIDTH + 30
        self.board_y = 30

        # Animation states
        self.last_action_name: str = "NONE"
        self.last_confidence: Optional[float] = None
        self.last_latency_ms: float = 0.0
        self.last_source: str = "N/A"
        self.total_ai_decisions: int = 0
        self.mode: str = "human"  # 'human', 'jev', 'heuristic'
        self.is_paused: bool = False
        self.ai_interval_ms: int = 250
        self.model_name: str = "jev-2026-09"

    def set_telemetry(self, decision: DecisionResult, mode: str, interval_ms: int, model_name: str) -> None:
        """Updates real-time AI telemetry for the UI display."""
        self.last_action_name = decision.action.value.upper()
        self.last_confidence = decision.confidence
        self.last_latency_ms = decision.latency_ms
        self.last_source = decision.source
        self.total_ai_decisions += 1
        self.mode = mode
        self.ai_interval_ms = interval_ms
        self.model_name = model_name

    def draw_rounded_rect(
        self, surface: pygame.Surface, rect: pygame.Rect, color: Tuple[int, int, int], radius: int = 8
    ) -> None:
        """Draws a solid rounded rectangle."""
        pygame.draw.rect(surface, color, rect, border_radius=radius)

    def draw_panel(
        self,
        rect: pygame.Rect,
        title: Optional[str] = None,
        title_color: Tuple[int, int, int] = COLOR_ACCENT_CYAN,
    ) -> None:
        """Draws a themed card/panel with optional header."""
        self.draw_rounded_rect(self.screen, rect, COLOR_PANEL_BG, radius=8)
        pygame.draw.rect(self.screen, COLOR_PANEL_BORDER, rect, width=1, border_radius=8)

        if title:
            surf = self.font_heading.render(title, True, title_color)
            self.screen.blit(surf, (rect.x + 14, rect.y + 12))
            pygame.draw.line(
                self.screen,
                COLOR_PANEL_BORDER,
                (rect.x + 14, rect.y + 36),
                (rect.x + rect.width - 14, rect.y + 36),
                1,
            )

    def draw_piece_preview(
        self, rect: pygame.Rect, piece_type: Optional[str], label: str
    ) -> None:
        """Renders a mini-preview of a piece inside a panel."""
        self.draw_panel(rect, title=label)
        if not piece_type or piece_type not in TETROMINO_SHAPES:
            # Empty state
            txt = self.font_small.render("EMPTY", True, COLOR_TEXT_MUTED)
            self.screen.blit(
                txt,
                (rect.x + (rect.width - txt.get_width()) // 2, rect.y + 60),
            )
            return

        blocks = TETROMINO_SHAPES[piece_type][0]
        color = TETROMINO_COLORS[piece_type]
        mini_cell = 20

        # Center the piece
        min_x = min(x for x, y in blocks)
        max_x = max(x for x, y in blocks)
        min_y = min(y for x, y in blocks)
        max_y = max(y for x, y in blocks)

        p_width = (max_x - min_x + 1) * mini_cell
        p_height = (max_y - min_y + 1) * mini_cell
        start_x = rect.x + (rect.width - p_width) // 2 - min_x * mini_cell
        start_y = rect.y + 44 + (rect.height - 44 - p_height) // 2 - min_y * mini_cell

        for bx, by in blocks:
            cell_r = pygame.Rect(
                start_x + bx * mini_cell, start_y + by * mini_cell, mini_cell - 2, mini_cell - 2
            )
            pygame.draw.rect(self.screen, color, cell_r, border_radius=3)

    def draw_board(self) -> None:
        """Renders the main 10x20 grid, locked blocks, active piece, and ghost projection."""
        board_rect = pygame.Rect(self.board_x, self.board_y, BOARD_WIDTH, BOARD_HEIGHT)

        # Background
        pygame.draw.rect(self.screen, COLOR_GRID_BG, board_rect, border_radius=6)
        pygame.draw.rect(self.screen, COLOR_PANEL_BORDER, board_rect, width=2, border_radius=6)

        # Subtle grid lines
        for c in range(1, BOARD_COLS):
            x = self.board_x + c * CELL_SIZE
            pygame.draw.line(self.screen, COLOR_GRID_LINE, (x, self.board_y), (x, self.board_y + BOARD_HEIGHT))
        for r in range(1, BOARD_ROWS):
            y = self.board_y + r * CELL_SIZE
            pygame.draw.line(self.screen, COLOR_GRID_LINE, (self.board_x, y), (self.board_x + BOARD_WIDTH, y))

        # Locked blocks
        for r in range(BOARD_ROWS):
            for c in range(BOARD_COLS):
                val = self.game.board.grid[r][c]
                if val != 0:
                    # Look up piece color or default
                    color = list(TETROMINO_COLORS.values())[(val - 1) % len(TETROMINO_COLORS)]
                    self._draw_cell(c, r, color)

        # Ghost piece (projected landing position)
        if not self.game.game_over:
            ghost_y = self.game.get_ghost_y()
            ghost_blocks = self.game.current_piece.get_blocks(offset_y=ghost_y - self.game.current_piece.y)
            for gx, gy in ghost_blocks:
                if 0 <= gy < BOARD_ROWS and 0 <= gx < BOARD_COLS:
                    rect = pygame.Rect(
                        self.board_x + gx * CELL_SIZE + 2,
                        self.board_y + gy * CELL_SIZE + 2,
                        CELL_SIZE - 4,
                        CELL_SIZE - 4,
                    )
                    pygame.draw.rect(self.screen, (70, 75, 95), rect, width=2, border_radius=4)

            # Active falling piece
            piece_blocks = self.game.current_piece.get_blocks()
            color = self.game.current_piece.color
            for px, py in piece_blocks:
                if 0 <= py < BOARD_ROWS and 0 <= px < BOARD_COLS:
                    self._draw_cell(px, py, color, active=True)

        # Pause or Game Over overlay
        if self.game.game_over:
            self._draw_overlay("GAME OVER", "Press [R] to Restart", COLOR_ACCENT_RED)
        elif self.is_paused:
            self._draw_overlay("PAUSED", "Press [P] to Resume", COLOR_ACCENT_AMBER)

    def _draw_cell(self, col: int, row: int, color: Tuple[int, int, int], active: bool = False) -> None:
        """Renders an individual block with smooth borders and 3D bevel."""
        x = self.board_x + col * CELL_SIZE + 1
        y = self.board_y + row * CELL_SIZE + 1
        rect = pygame.Rect(x, y, CELL_SIZE - 2, CELL_SIZE - 2)

        # Main fill
        pygame.draw.rect(self.screen, color, rect, border_radius=4)

        # Highlight edge
        highlight_color = tuple(min(255, c + 50) for c in color)
        pygame.draw.line(self.screen, highlight_color, (x + 2, y + 2), (x + CELL_SIZE - 4, y + 2), 1)
        pygame.draw.line(self.screen, highlight_color, (x + 2, y + 2), (x + 2, y + CELL_SIZE - 4), 1)

    def _draw_overlay(self, title: str, subtitle: str, color: Tuple[int, int, int]) -> None:
        """Draws a semi-transparent modal message over the board."""
        overlay = pygame.Surface((BOARD_WIDTH, BOARD_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 12, 18, 210))
        self.screen.blit(overlay, (self.board_x, self.board_y))

        title_surf = self.font_title.render(title, True, color)
        sub_surf = self.font_body.render(subtitle, True, COLOR_TEXT_WHITE)

        cx = self.board_x + BOARD_WIDTH // 2
        cy = self.board_y + BOARD_HEIGHT // 2
        self.screen.blit(title_surf, (cx - title_surf.get_width() // 2, cy - 30))
        self.screen.blit(sub_surf, (cx - sub_surf.get_width() // 2, cy + 10))

    def draw_left_sidebar(self) -> None:
        """Draws the Hold box and controls reference."""
        # Hold Piece Box
        hold_rect = pygame.Rect(30, self.board_y, SIDEBAR_LEFT_WIDTH, 120)
        self.draw_piece_preview(hold_rect, self.game.hold_piece_type, "HOLD PIECE")

        # Controls Guide
        guide_rect = pygame.Rect(30, self.board_y + 140, SIDEBAR_LEFT_WIDTH, 460)
        self.draw_panel(guide_rect, title="CONTROLS", title_color=COLOR_TEXT_WHITE)

        controls_lines = [
            ("HUMAN CONTROLS", COLOR_ACCENT_GREEN),
            ("Left / Right", "Move"),
            ("Up Arrow", "Rotate CW"),
            ("Z Key", "Rotate CCW"),
            ("Down Arrow", "Soft Drop"),
            ("Spacebar", "Hard Drop"),
            ("C / Shift", "Hold Piece"),
            ("", None),
            ("MODE & SPEED", COLOR_ACCENT_CYAN),
            ("TAB / M", "Toggle AI/Human"),
            ("H Key", "Heuristic AI"),
            ("Key 1", "Slow (500ms)"),
            ("Key 2", "Normal (250ms)"),
            ("Key 3", "Fast (100ms)"),
            ("", None),
            ("SYSTEM", COLOR_ACCENT_PURPLE),
            ("P Key", "Pause Game"),
            ("R Key", "Restart Match"),
        ]

        curr_y = guide_rect.y + 45
        for item in controls_lines:
            if item[1] is None:
                curr_y += 6
                continue
            if isinstance(item[1], tuple):
                # Header
                txt = self.font_small.render(item[0], True, item[1])
                self.screen.blit(txt, (guide_rect.x + 14, curr_y))
                curr_y += 20
            else:
                k_txt = self.font_small.render(item[0], True, COLOR_TEXT_WHITE)
                v_txt = self.font_small.render(item[1], True, COLOR_TEXT_MUTED)
                self.screen.blit(k_txt, (guide_rect.x + 14, curr_y))
                self.screen.blit(v_txt, (guide_rect.x + guide_rect.width - v_txt.get_width() - 14, curr_y))
                curr_y += 18

    def draw_right_sidebar(self) -> None:
        """Draws Next Piece, Score & Level, and the Jev AI Telemetry Panel."""
        right_x = self.board_x + BOARD_WIDTH + 30

        # Next Piece Box
        next_rect = pygame.Rect(right_x, self.board_y, SIDEBAR_RIGHT_WIDTH, 120)
        self.draw_piece_preview(next_rect, self.game.next_piece_type, "NEXT PIECE")

        # Game Stats Panel (Score, Level, Lines)
        stats_rect = pygame.Rect(right_x, self.board_y + 135, SIDEBAR_RIGHT_WIDTH, 100)
        self.draw_panel(stats_rect, title="SCORE & PROGRESS")

        col1_x = stats_rect.x + 16
        col2_x = stats_rect.x + 120
        col3_x = stats_rect.x + 225
        base_y = stats_rect.y + 44

        def draw_stat(lbl: str, val: str, x: int, val_color: Tuple[int, int, int] = COLOR_TEXT_WHITE) -> None:
            l_surf = self.font_small.render(lbl, True, COLOR_TEXT_MUTED)
            v_surf = self.font_title.render(val, True, val_color)
            self.screen.blit(l_surf, (x, base_y))
            self.screen.blit(v_surf, (x, base_y + 18))

        draw_stat("SCORE", f"{self.game.score}", col1_x, COLOR_ACCENT_CYAN)
        draw_stat("LEVEL", f"{self.game.level}", col2_x, COLOR_ACCENT_AMBER)
        draw_stat("LINES", f"{self.game.lines_cleared}", col3_x, COLOR_ACCENT_GREEN)

        # Jev AI Telemetry Panel
        ai_panel_rect = pygame.Rect(right_x, self.board_y + 250, SIDEBAR_RIGHT_WIDTH, 350)
        self.draw_panel(ai_panel_rect, title="JEV AI TELEMETRY (TYPESAFE)", title_color=COLOR_ACCENT_CYAN)

        # Mode Badge
        if self.mode == "human":
            mode_badge_text = "MODE: HUMAN"
            mode_badge_color = COLOR_ACCENT_GREEN
        elif self.mode == "jev":
            mode_badge_text = "MODE: JEV AI (AUTONOMOUS)"
            mode_badge_color = COLOR_ACCENT_CYAN
        else:
            mode_badge_text = "MODE: HEURISTIC AI"
            mode_badge_color = COLOR_ACCENT_PURPLE

        badge_surf = self.font_heading.render(mode_badge_text, True, mode_badge_color)
        self.screen.blit(badge_surf, (ai_panel_rect.x + 16, ai_panel_rect.y + 45))

        # Telemetry metrics list
        conf_str = f"{self.last_confidence:.2f}" if self.last_confidence is not None else "N/A"
        latency_str = f"{self.last_latency_ms:.1f} ms" if self.last_latency_ms > 0 else "N/A"

        metrics = [
            ("Model", self.model_name),
            ("Decision Source", self.last_source.upper()),
            ("Last Action", self.last_action_name),
            ("Confidence", conf_str),
            ("Decision Latency", latency_str),
            ("AI Speed Interval", f"{self.ai_interval_ms} ms"),
            ("Total Decisions", str(self.total_ai_decisions)),
            ("Board Holes", str(self.game.get_state().holes)),
            ("Surface Bumpiness", str(self.game.get_state().bumpiness)),
            ("Aggregate Height", str(self.game.get_state().aggregate_height)),
        ]

        metric_y = ai_panel_rect.y + 75
        for label, val in metrics:
            l_surf = self.font_body.render(label + ":", True, COLOR_TEXT_MUTED)
            # Highlight specific fields
            val_col = COLOR_TEXT_WHITE
            if label == "Confidence" and self.last_confidence is not None:
                val_col = COLOR_ACCENT_GREEN if self.last_confidence >= 0.7 else COLOR_ACCENT_AMBER
            elif label == "Last Action":
                val_col = COLOR_ACCENT_CYAN
            elif label == "Decision Source" and val == "FALLBACK":
                val_col = COLOR_ACCENT_RED

            v_surf = self.font_mono.render(val, True, val_col)
            self.screen.blit(l_surf, (ai_panel_rect.x + 16, metric_y))
            self.screen.blit(v_surf, (ai_panel_rect.x + ai_panel_rect.width - v_surf.get_width() - 16, metric_y))
            metric_y += 24

    def render(self) -> None:
        """Main render loop pass."""
        self.screen.fill(COLOR_BG)
        self.draw_left_sidebar()
        self.draw_board()
        self.draw_right_sidebar()
        pygame.display.flip()
        self.clock.tick(60)  # 60 FPS
