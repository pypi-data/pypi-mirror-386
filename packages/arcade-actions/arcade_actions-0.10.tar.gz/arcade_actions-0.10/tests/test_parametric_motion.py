"""Tests for ParametricMotionUntil relative motion and rotation."""

import arcade
import pytest

from actions.base import Action
from actions.conditional import ParametricMotionUntil, duration


def create_test_sprite() -> arcade.Sprite:
    """Create a sprite with texture for testing."""
    sprite = arcade.Sprite(":resources:images/items/star.png")
    sprite.center_x = 100
    sprite.center_y = 100
    return sprite


class TestParametricMotion:
    """Test suite for ParametricMotionUntil behavior."""

    def teardown_method(self):
        """Clean up actions between tests."""
        Action.stop_all()

    def test_basic_relative_motion(self):
        """Sprite should move by relative offsets over the action duration and complete."""
        sprite = arcade.Sprite(":resources:images/items/star.png")
        sprite.center_x = 100
        sprite.center_y = 100

        # Linear relative motion: dx = 100*t, dy = 50*t over 1.0s
        def offset_fn(t: float) -> tuple[float, float]:
            return 100.0 * t, 50.0 * t

        action = ParametricMotionUntil(
            offset_fn=offset_fn,
            condition=duration(1.0),
        )
        action.apply(sprite, tag="param_basic")

        # Simulate frames until done
        while not action.done:
            Action.update_all(1 / 60)

        # Final position should be origin + (100, 50)
        assert pytest.approx(sprite.center_x, rel=1e-3, abs=1e-3) == 200.0
        assert pytest.approx(sprite.center_y, rel=1e-3, abs=1e-3) == 150.0
        assert action.done

    def test_rotation_along_diagonal(self):
        """When rotate_with_path is enabled, angle should follow the motion direction."""
        sprite = arcade.Sprite(":resources:images/items/star.png")
        sprite.center_x = 0
        sprite.center_y = 0

        # 45-degree diagonal motion: dx = t, dy = t
        def offset_fn(t: float) -> tuple[float, float]:
            return t, t

        action = ParametricMotionUntil(
            offset_fn=offset_fn,
            condition=duration(0.5),
            rotate_with_path=True,
            rotation_offset=0.0,
        )
        action.apply(sprite, tag="param_rotate")

        # Run a few frames; angle should stabilize near 45 degrees
        for _ in range(10):
            Action.update_all(1 / 60)

        assert pytest.approx(sprite.angle, abs=1e-2) == 45.0

        # Complete the motion and ensure the angle remains valid
        while not action.done:
            Action.update_all(1 / 60)
        assert pytest.approx(sprite.angle, abs=1e-2) == 45.0

    def test_factor_scaling_affects_speed(self):
        """Scaling factor should slow down or speed up progress across frames."""
        sprite = arcade.Sprite(":resources:images/items/star.png")
        sprite.center_x = 10
        sprite.center_y = 20

        def offset_fn(t: float) -> tuple[float, float]:
            # Large displacement so differences are noticeable
            return 300.0 * t, 0.0

        action = ParametricMotionUntil(
            offset_fn=offset_fn,
            condition=duration(1.0),
        )
        action.apply(sprite, tag="param_factor")

        # Half speed
        action.set_factor(0.5)
        Action.update_all(0.5)  # half a second of sim time
        pos_half_speed = (sprite.center_x, sprite.center_y)

        # Reset and test full speed for comparison
        Action.stop_all()
        sprite.center_x = 10
        sprite.center_y = 20
        action2 = ParametricMotionUntil(offset_fn=offset_fn, condition=duration(1.0))
        action2.apply(sprite, tag="param_factor_full")
        action2.set_factor(1.0)
        Action.update_all(0.5)
        pos_full_speed = (sprite.center_x, sprite.center_y)

        # X displacement should be greater at full speed than at half speed
        assert pos_full_speed[0] - 10 > pos_half_speed[0] - 10

    def test_on_stop_called_once_with_none(self):
        """on_stop should be invoked once with None upon completion."""
        sprite = arcade.Sprite(":resources:images/items/star.png")
        sprite.center_x = 5
        sprite.center_y = 5

        def offset_fn(t: float) -> tuple[float, float]:
            return 50.0 * t, 0.0

        calls: list[object] = []

        def on_stop(arg=None):
            calls.append(arg)

        action = ParametricMotionUntil(
            offset_fn=offset_fn,
            condition=duration(0.2),
            on_stop=on_stop,
        )
        action.apply(sprite, tag="param_on_stop")

        # Run until completion
        while not action.done:
            Action.update_all(1 / 60)

        assert action.done
        assert len(calls) == 1
        assert calls[0] is None


class TestPriority5_ParametricMotionDebug:
    """Test ParametricMotionUntil debug mode - covers lines 1659-1664."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_parametric_motion_debug_mode_jump_detection(self, capsys):
        """Test debug mode detects large jumps and prints warning."""
        sprite = create_test_sprite()

        # Create offset function that causes a large jump
        def offset_fn(t):
            if t < 0.5:
                return (t * 10, 0)
            else:
                # Large jump at t=0.5 (500+ pixels)
                return (t * 10 + 500, 0)

        # Enable debug mode with low threshold AND rotation
        # (debug output only prints when rotate_with_path=True)
        action = ParametricMotionUntil(
            offset_fn,
            duration(1.0),
            debug=True,
            debug_threshold=100.0,  # 100 pixels threshold
            rotate_with_path=True,  # Required for debug output
        )
        action.apply(sprite, tag="motion")

        # Run until jump occurs
        for _ in range(35):  # Run past t=0.5
            Action.update_all(1 / 60)

        # Verify debug output was printed (lines 1736-1741)
        captured = capsys.readouterr()
        assert "[ParametricMotionUntil:jump]" in captured.out
        assert "Δ=" in captured.out  # Verify jump magnitude printed
        assert "thr=100.0" in captured.out  # Verify threshold printed

        # Action should still work despite the jump
        assert not action.done or action._elapsed >= 0.5
