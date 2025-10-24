"""Tests for Pydantic models and custom properties."""

import pytest

from balatrobot.enums import State
from balatrobot.models import G


class TestGameState:
    """Test suite for G model."""

    def test_state_enum_property(self):
        """Test state_enum property converts integer to State enum correctly."""
        # Test with valid state value
        game_state = G(state=1, game=None, hand=None)
        assert game_state.state_enum == State.SELECTING_HAND

        # Test with different state values
        game_state = G(state=11, game=None, hand=None)
        assert game_state.state_enum == State.MENU

        game_state = G(state=5, game=None, hand=None)
        assert game_state.state_enum == State.SHOP

    def test_state_enum_property_with_invalid_state(self):
        """Test state_enum property with invalid state value raises ValueError."""
        game_state = G(state=999, game=None, hand=None)  # Invalid state

        with pytest.raises(ValueError):
            _ = game_state.state_enum
