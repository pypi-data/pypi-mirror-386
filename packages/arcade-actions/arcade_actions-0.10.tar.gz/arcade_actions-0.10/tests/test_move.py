"""Test suite for boundary functionality in MoveUntil action."""

import arcade

from actions import move_until
from actions.base import Action
from actions.conditional import MoveUntil, infinite
from actions.pattern import time_elapsed


def create_test_sprite() -> arcade.Sprite:
    """Create a sprite with texture for testing."""
    sprite = arcade.Sprite(":resources:images/items/star.png")
    sprite.center_x = 100
    sprite.center_y = 100
    return sprite


class TestMoveUntilBoundaries:
    """Test suite for MoveUntil boundary functionality."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_move_until_with_bounce_boundaries(self):
        """Test MoveUntil with bouncing boundaries."""
        sprite = create_test_sprite()
        sprite.center_x = 799  # Very close to right boundary

        # Create bounds (left, bottom, right, top)
        bounds = (0, 0, 800, 600)

        # Move right - should hit boundary and bounce
        move_until(
            sprite,
            velocity=(100, 0),
            condition=time_elapsed(2.0),
            bounds=bounds,
            boundary_behavior="bounce",
            tag="movement",
        )

        # Update action to set velocity
        Action.update_all(0.1)
        # Move sprite to new position
        sprite.update()
        # Check boundaries on new position
        Action.update_all(0.001)

        # Should have hit boundary and bounced
        assert sprite.change_x < 0  # Moving left now
        assert sprite.center_x <= 800  # Kept in bounds

    def test_move_until_with_wrap_boundaries(self):
        """Test MoveUntil with wrapping boundaries."""
        sprite = create_test_sprite()
        sprite.center_x = 799  # Very close to right boundary

        bounds = (0, 0, 800, 600)

        # Move right - should wrap to left side
        move_until(
            sprite,
            velocity=(100, 0),
            condition=time_elapsed(2.0),
            bounds=bounds,
            boundary_behavior="wrap",
            tag="movement",
        )

        # Update action to set velocity
        Action.update_all(0.1)
        # Move sprite to new position
        sprite.update()
        # Check boundaries on new position
        Action.update_all(0.001)

        # Should have wrapped to left side
        assert sprite.center_x == 0  # Wrapped to left

    def test_move_until_with_boundary_callback(self):
        """Test MoveUntil boundary callback functionality."""
        sprite = create_test_sprite()
        sprite.center_x = 799  # Very close to right boundary

        boundary_hits = []

        def on_boundary_enter(hitting_sprite, axis, side):
            boundary_hits.append((hitting_sprite, axis, side))

        bounds = (0, 0, 800, 600)
        move_until(
            sprite,
            velocity=(100, 0),
            condition=time_elapsed(2.0),
            bounds=bounds,
            boundary_behavior="bounce",
            on_boundary_enter=on_boundary_enter,
            tag="movement",
        )

        # Update action to set velocity
        Action.update_all(0.1)
        # Move sprite to new position
        sprite.update()
        # Check boundaries on new position
        Action.update_all(0.001)

        # Should have called boundary enter callback once on X/right
        assert len(boundary_hits) >= 1
        assert boundary_hits[0][0] == sprite
        assert boundary_hits[0][1] == "x"
        assert boundary_hits[0][2] in ("right", "left", "top", "bottom")

    def test_move_until_vertical_boundaries(self):
        """Test MoveUntil with vertical boundary interactions."""
        sprite = create_test_sprite()
        sprite.center_y = 599  # Very close to top boundary

        bounds = (0, 0, 800, 600)

        # Move up - should hit top boundary and bounce
        move_until(
            sprite,
            velocity=(0, 100),
            condition=time_elapsed(2.0),
            bounds=bounds,
            boundary_behavior="bounce",
            tag="movement",
        )

        # Update action to set velocity
        Action.update_all(0.1)
        # Move sprite to new position
        sprite.update()
        # Check boundaries on new position
        Action.update_all(0.001)

        # Should have bounced (reversed Y velocity)
        assert sprite.change_y < 0  # Moving down now
        assert sprite.center_y <= 600  # Kept in bounds

    def test_move_until_no_boundaries(self):
        """Test MoveUntil without boundary checking."""
        sprite = create_test_sprite()
        initial_x = sprite.center_x

        # No bounds specified - should move normally
        move_until(sprite, velocity=(100, 0), condition=time_elapsed(1.0), tag="movement")

        Action.update_all(0.5)
        sprite.update()  # Apply velocity to position

        # Should move normally without boundary interference
        assert sprite.center_x > initial_x
        # MoveUntil uses pixels per frame at 60 FPS semantics
        assert sprite.change_x == 100  # Velocity unchanged

    def test_move_until_multiple_sprites_boundaries(self):
        """Test MoveUntil boundary checking with multiple sprites."""
        sprites = arcade.SpriteList()
        for i in range(3):
            sprite = create_test_sprite()
            sprite.center_x = 799 + i * 0.1  # All very close to right boundary
            sprites.append(sprite)

        bounds = (0, 0, 800, 600)

        move_until(
            sprites,
            velocity=(100, 0),
            condition=time_elapsed(2.0),
            bounds=bounds,
            boundary_behavior="bounce",
            tag="group_movement",
        )

        # Update action to set velocity
        Action.update_all(0.1)
        # Move sprites to new positions
        for sprite in sprites:
            sprite.update()
        # Check boundaries on new positions
        Action.update_all(0.001)

        # All sprites should have bounced
        for sprite in sprites:
            assert sprite.change_x < 0  # All moving left now
            assert sprite.center_x <= 800  # All kept in bounds

    def test_move_until_wrap_vertical_boundaries(self):
        """Test MoveUntil with vertical wrapping boundaries."""
        sprite = create_test_sprite()
        sprite.center_y = 599  # Very close to top boundary

        bounds = (0, 0, 800, 600)

        # Move up - should wrap to bottom
        move_until(
            sprite,
            velocity=(0, 100),
            condition=time_elapsed(2.0),
            bounds=bounds,
            boundary_behavior="wrap",
            tag="movement_wrap_y",
        )

        # Update action to set velocity and apply movement
        Action.update_all(0.1)
        sprite.update()
        # Run boundary processing
        Action.update_all(0.001)

        # Should have wrapped to bottom side
        assert sprite.center_y == 0

    def test_move_until_wrap_both_axes(self):
        """Test MoveUntil with wrapping on both axes simultaneously."""
        sprite = create_test_sprite()
        sprite.center_x = 799  # Near right
        sprite.center_y = 599  # Near top

        bounds = (0, 0, 800, 600)

        # Move diagonally up-right - should wrap to (left, bottom)
        move_until(
            sprite,
            velocity=(100, 100),
            condition=time_elapsed(2.0),
            bounds=bounds,
            boundary_behavior="wrap",
            tag="movement_wrap_xy",
        )

        # Update action to set velocity and apply movement
        Action.update_all(0.1)
        sprite.update()
        # Run boundary processing
        Action.update_all(0.001)

        # Should have wrapped on both axes
        assert sprite.center_x == 0
        assert sprite.center_y == 0

    def test_move_until_limit_debounce_x(self):
        """Limit behavior should fire one enter on approach and one exit on retreat (X)."""
        sprite = create_test_sprite()
        sprite.center_x = 799  # Near right boundary

        bounds = (0, 0, 800, 600)
        events: list[tuple[str, str, str]] = []

        def on_enter(s, axis, side):
            events.append(("enter", axis, side))

        def on_exit(s, axis, side):
            events.append(("exit", axis, side))

        action = move_until(
            sprite,
            velocity=(10, 0),
            condition=time_elapsed(2.0),
            bounds=bounds,
            boundary_behavior="limit",
            on_boundary_enter=on_enter,
            on_boundary_exit=on_exit,
            tag="limit_debounce_x",
        )

        # Apply initial velocity and movement toward boundary
        Action.update_all(0.05)
        sprite.update()
        Action.update_all(0.001)

        # Should have exactly one enter to right on X
        assert ("enter", "x", "right") in events
        assert events.count(("enter", "x", "right")) == 1

        # Continue pushing into the boundary for a few frames - no additional enters
        for _ in range(3):
            Action.update_all(0.016)
            sprite.update()
            Action.update_all(0.001)
        assert events.count(("enter", "x", "right")) == 1

        # Now retreat from the boundary by reversing velocity
        action.set_current_velocity((-10, 0))
        Action.update_all(0.016)
        sprite.update()
        Action.update_all(0.001)

        # Exactly one exit should be recorded
        assert events.count(("exit", "x", "right")) == 1

    def test_move_until_limit_debounce_y(self):
        """Limit behavior should fire one enter on approach and one exit on retreat (Y)."""
        sprite = create_test_sprite()
        sprite.center_y = 599  # Near top boundary

        bounds = (0, 0, 800, 600)
        events: list[tuple[str, str, str]] = []

        def on_enter(s, axis, side):
            events.append(("enter", axis, side))

        def on_exit(s, axis, side):
            events.append(("exit", axis, side))

        action = move_until(
            sprite,
            velocity=(0, 10),
            condition=time_elapsed(2.0),
            bounds=bounds,
            boundary_behavior="limit",
            on_boundary_enter=on_enter,
            on_boundary_exit=on_exit,
            tag="limit_debounce_y",
        )

        # Apply initial velocity and movement toward boundary
        Action.update_all(0.05)
        sprite.update()
        Action.update_all(0.001)

        # Should have exactly one enter to top on Y
        assert ("enter", "y", "top") in events
        assert events.count(("enter", "y", "top")) == 1

        # Continue pushing into the boundary for a few frames - no additional enters
        for _ in range(3):
            Action.update_all(0.016)
            sprite.update()
            Action.update_all(0.001)
        assert events.count(("enter", "y", "top")) == 1

        # Now retreat from the boundary by reversing velocity
        action.set_current_velocity((0, -10))
        Action.update_all(0.016)
        sprite.update()
        Action.update_all(0.001)

        # Exactly one exit should be recorded
        assert events.count(("exit", "y", "top")) == 1


class TestPriority3_BoundaryBehaviorMethods:
    """Test boundary behavior methods - covers lines 469-501 in conditional.py."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_wrap_behavior_left_to_right(self):
        """Test wrap boundary behavior when crossing left boundary - line 469-476."""
        sprite = create_test_sprite()
        sprite.center_x = 5  # Start just inside left boundary

        bounds = (0, 0, 800, 600)
        action = MoveUntil((-100, 0), infinite, bounds=bounds, boundary_behavior="wrap")
        action.apply(sprite, tag="move")

        # Update action to set velocity
        Action.update_all(0.1)
        # Move sprite to new position
        sprite.update()
        # Check boundaries on new position
        Action.update_all(0.001)

        # Should have wrapped to right side
        assert sprite.center_x >= 700  # Should be near right boundary (800)

    def test_wrap_behavior_right_to_left(self):
        """Test wrap boundary behavior when crossing right boundary."""
        sprite = create_test_sprite()
        sprite.center_x = 795  # Start near right boundary

        bounds = (0, 0, 800, 600)
        action = MoveUntil((100, 0), infinite, bounds=bounds, boundary_behavior="wrap")
        action.apply(sprite, tag="move")

        # Update action to set velocity
        Action.update_all(0.1)
        # Move sprite to new position
        sprite.update()
        # Check boundaries on new position
        Action.update_all(0.001)

        # Should have wrapped to left side
        assert sprite.center_x == 0  # Wrapped to left boundary

    def test_wrap_behavior_bottom_to_top(self):
        """Test wrap boundary behavior when crossing bottom boundary."""
        sprite = create_test_sprite()
        sprite.center_y = 5  # Start near bottom boundary

        bounds = (0, 0, 800, 600)
        action = MoveUntil((0, -100), infinite, bounds=bounds, boundary_behavior="wrap")
        action.apply(sprite, tag="move")

        # Update action to set velocity
        Action.update_all(0.1)
        # Move sprite to new position
        sprite.update()
        # Check boundaries on new position
        Action.update_all(0.001)

        # Should have wrapped to top side
        assert sprite.center_y >= 500  # Should be near top boundary (600)

    def test_wrap_behavior_top_to_bottom(self):
        """Test wrap boundary behavior when crossing top boundary."""
        sprite = create_test_sprite()
        sprite.center_y = 595  # Start near top boundary

        bounds = (0, 0, 800, 600)
        action = MoveUntil((0, 100), infinite, bounds=bounds, boundary_behavior="wrap")
        action.apply(sprite, tag="move")

        # Update action to set velocity
        Action.update_all(0.1)
        # Move sprite to new position
        sprite.update()
        # Check boundaries on new position
        Action.update_all(0.001)

        # Should have wrapped to bottom side
        assert sprite.center_y == 0  # Wrapped to bottom boundary

    def test_limit_behavior_left_boundary(self):
        """Test limit boundary behavior at left boundary - covers lines 480-501."""
        sprite = create_test_sprite()
        sprite.center_x = 50  # Start left of boundary

        bounds = (100, 0, 800, 600)
        action = MoveUntil((-5, 0), infinite, bounds=bounds, boundary_behavior="limit")
        action.apply(sprite, tag="move")

        # Update action - should immediately snap to boundary
        Action.update_all(1 / 60)

        # Should be clamped at boundary with zero velocity applied
        assert sprite.center_x == 100
        assert sprite.change_x == 0

    def test_limit_behavior_bottom_boundary(self):
        """Test limit boundary behavior at bottom boundary - covers lines 492-496."""
        sprite = create_test_sprite()
        sprite.center_y = 50  # Start below boundary

        bounds = (0, 100, 800, 600)
        action = MoveUntil((0, -5), infinite, bounds=bounds, boundary_behavior="limit")
        action.apply(sprite, tag="move")

        # Update action - should immediately snap to boundary
        Action.update_all(1 / 60)

        # Should be clamped at boundary with zero velocity applied
        assert sprite.center_y == 100
        assert sprite.change_y == 0

    def test_limit_behavior_top_boundary(self):
        """Test limit boundary behavior at top boundary - covers lines 497-501."""
        sprite = create_test_sprite()
        sprite.center_y = 650  # Start above boundary

        bounds = (0, 0, 800, 600)
        action = MoveUntil((0, 5), infinite, bounds=bounds, boundary_behavior="limit")
        action.apply(sprite, tag="move")

        # Should immediately snap to boundary
        Action.update_all(1 / 60)

        # Should be clamped at boundary with zero velocity
        assert sprite.center_y == 600
        assert sprite.change_y == 0


class TestPriority1_VelocityProviderBoundaryCallbacks:
    """Test MoveUntil with velocity_provider and boundary callbacks - covers lines 238-248, 260-282."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_velocity_provider_boundary_enter_right(self):
        """Test velocity provider triggers boundary enter on right - lines 238-240."""
        sprite = create_test_sprite()
        sprite.center_x = 795

        enter_calls = []

        def on_enter(s, axis, side):
            enter_calls.append((axis, side))

        def velocity_provider():
            return (100, 0)

        bounds = (0, 0, 800, 600)
        action = MoveUntil(
            (100, 0),
            infinite,
            bounds=bounds,
            boundary_behavior="limit",
            velocity_provider=velocity_provider,
            on_boundary_enter=on_enter,
        )
        action.apply(sprite, tag="move")

        # One update should hit right boundary
        Action.update_all(1 / 60)

        assert len(enter_calls) > 0
        assert ("x", "right") in enter_calls

    def test_velocity_provider_boundary_enter_left(self):
        """Test velocity provider triggers boundary enter on left - lines 242-248."""
        sprite = create_test_sprite()
        sprite.center_x = 5

        enter_calls = []

        def on_enter(s, axis, side):
            enter_calls.append((axis, side))

        def velocity_provider():
            return (-100, 0)

        bounds = (0, 0, 800, 600)
        action = MoveUntil(
            (-100, 0),
            infinite,
            bounds=bounds,
            boundary_behavior="limit",
            velocity_provider=velocity_provider,
            on_boundary_enter=on_enter,
        )
        action.apply(sprite, tag="move")

        # One update should hit left boundary
        Action.update_all(1 / 60)

        assert len(enter_calls) > 0
        assert ("x", "left") in enter_calls

    def test_velocity_provider_boundary_enter_top(self):
        """Test velocity provider triggers boundary enter on top - lines 260-266."""
        sprite = create_test_sprite()
        sprite.center_y = 595

        enter_calls = []

        def on_enter(s, axis, side):
            enter_calls.append((axis, side))

        def velocity_provider():
            return (0, 100)

        bounds = (0, 0, 800, 600)
        action = MoveUntil(
            (0, 100),
            infinite,
            bounds=bounds,
            boundary_behavior="limit",
            velocity_provider=velocity_provider,
            on_boundary_enter=on_enter,
        )
        action.apply(sprite, tag="move")

        # One update should hit top boundary
        Action.update_all(1 / 60)

        assert len(enter_calls) > 0
        assert ("y", "top") in enter_calls

    def test_velocity_provider_boundary_enter_bottom(self):
        """Test velocity provider triggers boundary enter on bottom - lines 267-274."""
        sprite = create_test_sprite()
        sprite.center_y = 5

        enter_calls = []

        def on_enter(s, axis, side):
            enter_calls.append((axis, side))

        def velocity_provider():
            return (0, -100)

        bounds = (0, 0, 800, 600)
        action = MoveUntil(
            (0, -100),
            infinite,
            bounds=bounds,
            boundary_behavior="limit",
            velocity_provider=velocity_provider,
            on_boundary_enter=on_enter,
        )
        action.apply(sprite, tag="move")

        # One update should hit bottom boundary
        Action.update_all(1 / 60)

        assert len(enter_calls) > 0
        assert ("y", "bottom") in enter_calls

    def test_velocity_provider_boundary_exit_vertical(self):
        """Test velocity provider triggers boundary exit on vertical - lines 279-282."""
        sprite = create_test_sprite()
        sprite.center_y = 605  # Start beyond top boundary

        exit_calls = []
        enter_calls = []

        def on_enter(s, axis, side):
            enter_calls.append((axis, side))

        def on_exit(s, axis, side):
            exit_calls.append((axis, side))

        # First move down to enter boundary
        def velocity_provider():
            return (0, 100)

        bounds = (0, 0, 800, 600)
        action = MoveUntil(
            (0, 100),
            infinite,
            bounds=bounds,
            boundary_behavior="limit",
            velocity_provider=velocity_provider,
            on_boundary_enter=on_enter,
            on_boundary_exit=on_exit,
        )
        action.apply(sprite, tag="move")

        # First update - enter boundary
        Action.update_all(1 / 60)
        assert len(enter_calls) > 0

        # Change direction to exit boundary
        action.velocity_provider = lambda: (0, -100)

        # Next update - exit boundary
        Action.update_all(1 / 60)

        assert len(exit_calls) > 0
        assert ("y", "top") in exit_calls
