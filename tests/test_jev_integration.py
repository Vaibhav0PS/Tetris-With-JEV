"""Integration tests for Jev AI autonomous loop and fallback safety."""

from unittest.mock import MagicMock
import pytest
from pydantic_ai.agent import AgentRunResult
from pydantic_ai.messages import ModelResponse

from game.actions import TetrisAction
from game.tetris import TetrisGame
from ai.jev_player import JevPlayer
from ai.schemas import JevDecision


def test_jev_player_mock_mode_e2e():
    """Verifies that JevPlayer in mock mode chooses actions and executes them seamlessly."""
    game = TetrisGame(seed=7)
    player = JevPlayer(mock_mode=True)

    # 1. Get state
    state = game.get_state()
    assert state.current_piece is not None

    # 2. Get Jev decision
    result = player.choose_action(state, game)
    assert result.action in TetrisAction
    assert result.source in ["mock_jev", "fallback"]

    # 3. Validate action
    assert game.is_valid_action(result.action)

    # 4. Execute action
    applied = game.apply_action(result.action)
    assert applied is True

    # 5. New state is generated
    new_state = game.get_state()
    assert new_state is not None


def test_jev_player_mocked_agent_call_with_confidence():
    """Mocks the Pydantic AI Agent to test structured response parsing and confidence extraction."""
    game = TetrisGame(seed=8)
    player = JevPlayer(api_key="fake_key_for_testing", model_name="jev-2026-09", mock_mode=False)

    # Mock the internal agent
    mock_agent = MagicMock()
    mock_run_result = MagicMock()
    mock_run_result.output = JevDecision(action=TetrisAction.ROTATE_CW)

    # Set up mock response with provider_details confidence
    mock_response = MagicMock(spec=ModelResponse)
    mock_response.provider_details = {
        "confidence": {"action": 0.88},
        "probabilities": {"action": {"rotate_cw": 0.88, "left": 0.05, "right": 0.07}},
    }
    mock_run_result.response = mock_response

    mock_agent.run_sync.return_value = mock_run_result
    player.agent = mock_agent

    state = game.get_state()
    decision = player.choose_action(state, game)

    assert decision.action == TetrisAction.ROTATE_CW
    assert decision.confidence == 0.88
    assert decision.source == "jev"
    assert game.is_valid_action(decision.action)
    assert game.apply_action(decision.action)


def test_jev_player_resilience_on_api_error():
    """Verifies fallback safety when the Jev API raises an exception (network/timeout/rate limit)."""
    game = TetrisGame(seed=9)
    player = JevPlayer(api_key="fake_key", mock_mode=False)

    # Mock agent raising an exception
    mock_agent = MagicMock()
    mock_agent.run_sync.side_effect = ConnectionError("Simulated network timeout connecting to api.typesafe.ai")
    player.agent = mock_agent

    state = game.get_state()
    decision = player.choose_action(state, game)

    # Must NOT crash! Must return a valid fallback action
    assert decision.action in TetrisAction
    assert decision.source == "fallback"
    assert "Simulated network timeout" in decision.error_message
    assert game.is_valid_action(decision.action)
    assert game.apply_action(decision.action)


def test_jev_player_deterministic_safety_layer():
    """Verifies that an illegal action proposed by Jev is rejected by the engine and intercepted."""
    game = TetrisGame(seed=10)
    player = JevPlayer(api_key="fake_key", mock_mode=False)

    # Move active piece all the way to the leftmost wall
    while game.is_valid_action(TetrisAction.LEFT):
        game.apply_action(TetrisAction.LEFT)

    # At this point, LEFT is an ILLEGAL action
    assert not game.is_valid_action(TetrisAction.LEFT)

    # Mock Jev returning the illegal action LEFT
    mock_agent = MagicMock()
    mock_run_result = MagicMock()
    mock_run_result.output = JevDecision(action=TetrisAction.LEFT)
    mock_run_result.response = None
    mock_agent.run_sync.return_value = mock_run_result
    player.agent = mock_agent

    state = game.get_state()
    decision = player.choose_action(state, game)

    # Decision should NOT be LEFT because engine rejects it; fallback must take over
    assert decision.action != TetrisAction.LEFT
    assert decision.source == "fallback"
    assert game.is_valid_action(decision.action)
    assert game.apply_action(decision.action)


def test_continuous_autonomous_loop():
    """Tests continuous 20-step autonomous loop: state -> Jev -> execute -> repeat."""
    game = TetrisGame(seed=99)
    player = JevPlayer(mock_mode=True)

    for step in range(20):
        if game.game_over:
            break
        state = game.get_state()
        decision = player.choose_action(state, game)
        assert game.is_valid_action(decision.action)
        game.apply_action(decision.action)

    assert not game.game_over
