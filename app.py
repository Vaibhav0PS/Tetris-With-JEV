"""Main entry point for Tetris with autonomous Jev AI (TypeSafe).

Supports:
- Human Mode: Play using standard keyboard controls.
- Jev AI Mode: Jev observes game state, outputs typed actions, and engine executes.
- Heuristic AI Mode: Dellacherie surface heuristic player for comparison.
- Headless Comparison Benchmark: Headless comparison between Jev and Heuristic AI.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Optional

import pygame
from dotenv import load_dotenv

from game.actions import TetrisAction
from game.state import TetrisState
from game.tetris import TetrisGame
from ai.heuristic_player import HeuristicPlayer
from ai.jev_player import JevPlayer
from ai.schemas import DecisionResult
from ui.pygame_ui import TetrisUI

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("TetrisApp")


def parse_arguments() -> argparse.Namespace:
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Autonomous Tetris Game with TypeSafe Jev AI"
    )
    parser.add_argument(
        "--mode",
        choices=["human", "jev", "heuristic", "compare"],
        default=os.getenv("DEFAULT_MODE", "human").lower(),
        help="Initial game mode (default: human)",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run Jev AI in mock/offline mode (no TypeSafe API key needed)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=os.getenv("TYPESAFE_MODEL", "jev-latest"),
        help="Pinned TypeSafe Jev model name (default: jev-latest)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=int(os.getenv("AI_DECISION_INTERVAL_MS", "250")),
        help="AI decision interval in milliseconds (default: 250)",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in headless benchmark comparison mode without GUI",
    )
    parser.add_argument(
        "--games",
        type=int,
        default=3,
        help="Number of games to simulate in comparison mode (default: 3)",
    )
    return parser.parse_args()


def run_headless_comparison(
    num_games: int, model_name: str, mock_mode: bool
) -> None:
    """Runs a side-by-side benchmark comparison between Jev AI and Heuristic AI."""
    print("=" * 65)
    print("      TETRIS AI PERFORMANCE BENCHMARK & COMPARISON")
    print("=" * 65)
    print(f"Games per AI: {num_games} | Model: {model_name} | Mock: {mock_mode}")

    jev_player = JevPlayer(model_name=model_name, mock_mode=mock_mode)
    heuristic_player = HeuristicPlayer()

    def run_benchmark_for(name: str, player) -> dict:
        scores = []
        lines_list = []
        latencies = []
        decisions_list = []

        print(f"\nEvaluating {name} across {num_games} matches...")
        for g in range(num_games):
            game = TetrisGame(seed=100 + g)
            step_count = 0
            # Cap at 500 steps per game for benchmarking
            while not game.game_over and step_count < 500:
                state = game.get_state()
                dec = player.choose_action(state, game)
                if dec.latency_ms > 0:
                    latencies.append(dec.latency_ms)
                if game.is_valid_action(dec.action):
                    game.apply_action(dec.action)
                else:
                    game.apply_action(TetrisAction.SOFT_DROP)

                step_count += 1
                if step_count % 3 == 0:
                    game.tick()

            scores.append(game.score)
            lines_list.append(game.lines_cleared)
            decisions_list.append(step_count)
            print(f"  Game {g+1}/{num_games}: Score={game.score}, Lines={game.lines_cleared}, Moves={step_count}")

        avg_score = sum(scores) / len(scores) if scores else 0
        avg_lines = sum(lines_list) / len(lines_list) if lines_list else 0
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        return {
            "avg_score": avg_score,
            "avg_lines": avg_lines,
            "avg_latency": avg_latency,
            "total_decisions": sum(decisions_list),
        }

    jev_stats = run_benchmark_for("Jev AI", jev_player)
    heur_stats = run_benchmark_for("Heuristic AI", heuristic_player)

    print("\n" + "=" * 65)
    print("                   BENCHMARK RESULTS")
    print("=" * 65)
    print(f"{'Metric':<25} | {'Jev AI':<16} | {'Heuristic AI':<16}")
    print("-" * 65)
    print(f"{'Average Score':<25} | {jev_stats['avg_score']:<16.1f} | {heur_stats['avg_score']:<16.1f}")
    print(f"{'Average Lines Cleared':<25} | {jev_stats['avg_lines']:<16.1f} | {heur_stats['avg_lines']:<16.1f}")
    print(f"{'Avg Latency (ms)':<25} | {jev_stats['avg_latency']:<16.1f} | {heur_stats['avg_latency']:<16.1f}")
    print(f"{'Total Decisions':<25} | {jev_stats['total_decisions']:<16} | {heur_stats['total_decisions']:<16}")
    print("=" * 65)


def run_gui_game(args: argparse.Namespace) -> None:
    """Launches the Pygame GUI and runs the game loop with Human and AI modes."""
    game = TetrisGame()
    ui = TetrisUI(game)

    # Initialize AI Players
    jev_player = JevPlayer(model_name=args.model, mock_mode=args.mock)
    heuristic_player = HeuristicPlayer()

    current_mode = args.mode if args.mode in ["human", "jev", "heuristic"] else "human"
    ai_interval_ms = max(50, args.interval)

    # Thread pool for non-blocking asynchronous AI requests
    executor = ThreadPoolExecutor(max_workers=1)
    pending_ai_future: Optional[Future[DecisionResult]] = None

    last_gravity_time = time.perf_counter()
    last_ai_action_time = time.perf_counter()

    logger.info(f"Starting Tetris with initial mode: {current_mode.upper()}")
    logger.info("Press TAB or M to toggle between Human and Jev AI mode.")

    running = True
    while running:
        current_time = time.perf_counter()

        # ----------------------------------------------------
        # 1. Handle UI & Keyboard Events
        # ----------------------------------------------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

            elif event.type == pygame.KEYDOWN:
                # Global Hotkeys
                if event.key in (pygame.K_TAB, pygame.K_m):
                    # Toggle between Human and Jev AI
                    if current_mode == "human":
                        current_mode = "jev"
                    elif current_mode == "jev":
                        current_mode = "human"
                    else:
                        current_mode = "human"
                    logger.info(f"Mode switched to: {current_mode.upper()}")

                elif event.key == pygame.K_h:
                    # Switch to Heuristic AI
                    current_mode = "heuristic" if current_mode != "heuristic" else "jev"
                    logger.info(f"Mode switched to: {current_mode.upper()}")

                elif event.key == pygame.K_p:
                    ui.is_paused = not ui.is_paused
                    logger.info(f"Game {'Paused' if ui.is_paused else 'Resumed'}")

                elif event.key == pygame.K_r:
                    game.reset()
                    pending_ai_future = None
                    logger.info("Game Reset.")

                elif event.key == pygame.K_1:
                    ai_interval_ms = 500
                    logger.info("AI Speed set to SLOW (500ms)")

                elif event.key == pygame.K_2:
                    ai_interval_ms = 250
                    logger.info("AI Speed set to NORMAL (250ms)")

                elif event.key == pygame.K_3:
                    ai_interval_ms = 100
                    logger.info("AI Speed set to FAST (100ms)")

                # Human Gameplay Controls (only active in Human Mode)
                elif current_mode == "human" and not ui.is_paused and not game.game_over:
                    if event.key == pygame.K_LEFT:
                        game.apply_action(TetrisAction.LEFT)
                    elif event.key == pygame.K_RIGHT:
                        game.apply_action(TetrisAction.RIGHT)
                    elif event.key == pygame.K_UP:
                        game.apply_action(TetrisAction.ROTATE_CW)
                    elif event.key == pygame.K_z:
                        game.apply_action(TetrisAction.ROTATE_CCW)
                    elif event.key == pygame.K_DOWN:
                        game.apply_action(TetrisAction.SOFT_DROP)
                    elif event.key == pygame.K_SPACE:
                        game.apply_action(TetrisAction.HARD_DROP)
                    elif event.key in (pygame.K_c, pygame.K_LSHIFT, pygame.K_RSHIFT):
                        game.apply_action(TetrisAction.HOLD)

        if not running:
            break

        # ----------------------------------------------------
        # 2. Autonomous AI Loop (Jev AI & Heuristic AI)
        # ----------------------------------------------------
        if current_mode in ("jev", "heuristic") and not ui.is_paused and not game.game_over:
            # Check if pending decision is complete
            if pending_ai_future is not None:
                if pending_ai_future.done():
                    try:
                        decision = pending_ai_future.result()
                        # Deterministic safety verification before execution
                        if game.is_valid_action(decision.action):
                            game.apply_action(decision.action)
                        else:
                            # Fallback action
                            game.apply_action(TetrisAction.SOFT_DROP)

                        ui.set_telemetry(
                            decision=decision,
                            mode=current_mode,
                            interval_ms=ai_interval_ms,
                            model_name=args.model if current_mode == "jev" else "Heuristic",
                        )
                        last_ai_action_time = current_time
                    except Exception as err:
                        logger.error(f"Error executing AI decision: {err}")
                    finally:
                        pending_ai_future = None

            # Dispatch new decision if interval elapsed and no request in-flight
            interval_sec = ai_interval_ms / 1000.0
            if pending_ai_future is None and (current_time - last_ai_action_time) >= interval_sec:
                active_player = jev_player if current_mode == "jev" else heuristic_player
                current_state = game.get_state()
                # Submit decision task to background worker to prevent UI freezing
                pending_ai_future = executor.submit(active_player.choose_action, current_state, game)

        # ----------------------------------------------------
        # 3. Natural Gravity Ticks
        # ----------------------------------------------------
        if not ui.is_paused and not game.game_over:
            gravity_interval_sec = game.get_gravity_interval_ms() / 1000.0
            if current_time - last_gravity_time >= gravity_interval_sec:
                game.tick()
                last_gravity_time = current_time

        # ----------------------------------------------------
        # 4. Render UI
        # ----------------------------------------------------
        ui.mode = current_mode
        ui.ai_interval_ms = ai_interval_ms
        ui.render()

    executor.shutdown(wait=False)
    pygame.quit()
    sys.exit(0)


def main() -> None:
    """Application entry point."""
    load_dotenv()
    args = parse_arguments()

    if args.headless or args.mode == "compare":
        run_headless_comparison(
            num_games=args.games, model_name=args.model, mock_mode=args.mock
        )
    else:
        run_gui_game(args)


if __name__ == "__main__":
    main()
