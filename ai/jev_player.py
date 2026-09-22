"""Jev AI autonomous player integrating Pydantic AI with TypeSafe."""

from __future__ import annotations

import logging
import os
import time
from typing import TYPE_CHECKING, Optional

from dotenv import load_dotenv
from pydantic_ai import Agent

from game.actions import TetrisAction
from game.state import TetrisState

if TYPE_CHECKING:
    from game.tetris import TetrisGame
from ai.features import get_holes_count
from ai.heuristic_player import HeuristicPlayer
from ai.prompts import JEV_SYSTEM_INSTRUCTION, format_state_prompt
from ai.schemas import DecisionResult, JevDecision

# Load environment variables
load_dotenv()
os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

logger = logging.getLogger("JevAI")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class JevPlayer:
    """Autonomous agent player using Pydantic AI and TypeSafe Jev."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        mock_mode: bool = False,
    ):
        self.api_key = api_key or os.getenv("TYPESAFE_API_KEY", "").strip()
        self.model_name = model_name or os.getenv("TYPESAFE_MODEL", "jev-latest").strip()
        self.mock_mode = mock_mode or not bool(self.api_key)

        self.heuristic_fallback = HeuristicPlayer()
        self.agent: Optional[Agent] = None

        self._init_agent()

    def _init_agent(self) -> None:
        """Initializes the Pydantic AI agent with TypeSafe model or mock model."""
        if self.mock_mode:
            logger.info("Initializing Jev AI in MOCK / OFFLINE mode (no API key required).")
            # In mock mode, we use 'test' model with output_type=JevDecision
            self.agent = Agent("test", output_type=JevDecision, system_prompt=JEV_SYSTEM_INSTRUCTION)
        else:
            logger.info(f"Initializing Jev AI with TypeSafe model: '{self.model_name}'")
            # Set environment variable for TypeSafe provider
            os.environ["TYPESAFE_API_KEY"] = self.api_key
            try:
                self.agent = Agent(
                    f"typesafe:{self.model_name}",
                    output_type=JevDecision,
                    system_prompt=JEV_SYSTEM_INSTRUCTION,
                )
            except Exception as err:
                logger.error(f"Failed to initialize TypeSafe agent: {err}. Falling back to mock/offline mode.")
                self.mock_mode = True
                self.agent = Agent("test", output_type=JevDecision, system_prompt=JEV_SYSTEM_INSTRUCTION)

    def choose_action(
        self, state: TetrisState, game: Optional[TetrisGame] = None
    ) -> DecisionResult:
        """
        Observes the game state, asks Jev for the next typed action, validates legality,
        and applies fallback safety if required.
        """
        start_time = time.perf_counter()

        # If in mock mode, use high-grade heuristic with simulated latency & confidence
        if self.mock_mode:
            time.sleep(0.01)  # small simulation delay
            decision = self.heuristic_fallback.choose_action(state, game)
            latency_ms = (time.perf_counter() - start_time) * 1000
            self._log_decision(state, decision.action, decision.confidence, latency_ms, source="mock_jev")
            return DecisionResult(
                action=decision.action,
                confidence=decision.confidence,
                latency_ms=round(latency_ms, 2),
                source="mock_jev",
            )

        # Real Jev AI Call via Pydantic AI
        prompt = format_state_prompt(state)
        confidence: Optional[float] = None
        action: Optional[TetrisAction] = None
        error_msg: Optional[str] = None

        try:
            run_result = self.agent.run_sync(prompt)
            action = run_result.output.action

            # Extract confidence if exposed by TypeSafe provider details
            if run_result.response and run_result.response.provider_details:
                details = run_result.response.provider_details
                conf_data = details.get("confidence")
                if isinstance(conf_data, dict):
                    action_conf = conf_data.get("action")
                    if isinstance(action_conf, (float, int)):
                        confidence = round(float(action_conf), 3)
                elif isinstance(conf_data, (float, int)):
                    confidence = round(float(conf_data), 3)

        except Exception as err:
            error_msg = str(err)
            logger.warning(f"Jev API call error: {err}. Executing safe fallback.")

        latency_ms = (time.perf_counter() - start_time) * 1000

        # Deterministic Safety Validation
        if action is not None and (game is None or game.is_valid_action(action)):
            self._log_decision(state, action, confidence, latency_ms, source="jev")
            return DecisionResult(
                action=action,
                confidence=confidence,
                latency_ms=round(latency_ms, 2),
                source="jev",
            )

        # Fallback layer if action is illegal, timeout, or API failure
        fallback_res = self.heuristic_fallback.choose_action(state, game)
        self._log_decision(
            state,
            fallback_res.action,
            fallback_res.confidence,
            latency_ms,
            source="fallback",
            note=f"Rejected proposal: {action}" if action else error_msg,
        )
        return DecisionResult(
            action=fallback_res.action,
            confidence=fallback_res.confidence,
            latency_ms=round(latency_ms, 2),
            source="fallback",
            error_message=error_msg or f"Invalid action: {action}",
        )

    def _log_decision(
        self,
        state: TetrisState,
        action: TetrisAction,
        confidence: Optional[float],
        latency_ms: float,
        source: str,
        note: Optional[str] = None,
    ) -> None:
        """Formats and outputs structured decision logs."""
        conf_str = f"{confidence:.2f}" if confidence is not None else "N/A"
        holes = state.holes
        note_str = f" ({note})" if note else ""
        logger.info(
            f"[AI] piece={state.current_piece} pos=({state.current_x},{state.current_y}) "
            f"holes={holes} action={action.value} confidence={conf_str} "
            f"latency={latency_ms:.1f}ms score={state.score} lines={state.lines_cleared} "
            f"src={source}{note_str}"
        )
