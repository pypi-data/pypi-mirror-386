"""Test suite for composite.py - Composite actions."""

import arcade

from actions.base import Action
from actions.composite import parallel, repeat, sequence
from actions.conditional import DelayUntil, duration


def create_test_sprite() -> arcade.Sprite:
    """Create a sprite with texture for testing."""
    sprite = arcade.Sprite(":resources:images/items/star.png")
    sprite.center_x = 100
    sprite.center_y = 100
    return sprite


class TestSequenceFunction:
    """Test suite for sequence() function."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_sequence_empty_initialization(self):
        """Test empty sequence initialization."""
        seq = sequence()
        assert len(seq.actions) == 0
        assert seq.current_action is None
        assert seq.current_index == 0

    def test_sequence_with_actions_initialization(self):
        """Test sequence initialization with actions."""

        action1 = DelayUntil(duration(0.1))
        action2 = DelayUntil(duration(0.1))
        seq = sequence(action1, action2)

        assert len(seq.actions) == 2
        assert seq.actions[0] == action1
        assert seq.actions[1] == action2
        assert seq.current_action is None
        assert seq.current_index == 0

    def test_sequence_empty_completes_immediately(self):
        """Test that empty sequence completes immediately."""
        sprite = create_test_sprite()
        seq = sequence()
        seq.target = sprite
        seq.start()

        assert seq.done

    def test_sequence_starts_first_action(self):
        """Test that sequence starts the first action."""

        sprite = create_test_sprite()
        action1 = DelayUntil(duration(0.1))
        action2 = DelayUntil(duration(0.1))
        seq = sequence(action1, action2)

        seq.target = sprite
        seq.start()

        assert seq.current_action == action1
        assert seq.current_index == 0

    def test_sequence_advances_to_next_action(self):
        """Test that sequence advances to next action when current completes."""

        sprite = create_test_sprite()
        action1 = DelayUntil(duration(0.05))
        action2 = DelayUntil(duration(0.05))
        seq = sequence(action1, action2)

        seq.target = sprite
        seq.start()

        # Update until first action completes
        seq.update(0.06)

        assert action1.done
        assert seq.current_action == action2
        assert seq.current_index == 1

    def test_sequence_completes_when_all_actions_done(self):
        """Test that sequence completes when all actions are done."""

        sprite = create_test_sprite()
        action1 = DelayUntil(duration(0.05))
        action2 = DelayUntil(duration(0.05))
        seq = sequence(action1, action2)

        seq.target = sprite
        seq.start()

        # Update until both actions complete
        seq.update(0.06)  # Complete first action
        seq.update(0.06)  # Complete second action

        assert action1.done
        assert action2.done
        assert seq.done
        assert seq.current_action is None

    def test_sequence_stop_stops_current_action(self):
        """Test that stopping sequence stops the current action."""

        sprite = create_test_sprite()
        action1 = DelayUntil(duration(1.0))  # Long duration so it won't complete
        action2 = DelayUntil(duration(0.1))
        seq = sequence(action1, action2)

        seq.target = sprite
        seq.start()
        seq.stop()

        assert action1.done  # Should be marked done by stop()

    def test_sequence_clone(self):
        """Test sequence cloning."""

        action1 = DelayUntil(duration(0.1))
        action2 = DelayUntil(duration(0.1))
        seq = sequence(action1, action2)

        cloned = seq.clone()

        assert cloned is not seq
        assert len(cloned.actions) == 2
        assert cloned.actions[0] is not action1
        assert cloned.actions[1] is not action2


class TestParallelFunction:
    """Test suite for parallel() function."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_parallel_empty_initialization(self):
        """Test empty parallel initialization."""
        par = parallel()
        assert len(par.actions) == 0

    def test_parallel_with_actions_initialization(self):
        """Test parallel initialization with actions."""

        action1 = DelayUntil(duration(0.1))
        action2 = DelayUntil(duration(0.1))
        par = parallel(action1, action2)

        assert len(par.actions) == 2
        assert par.actions[0] == action1
        assert par.actions[1] == action2

    def test_parallel_empty_completes_immediately(self):
        """Test that empty parallel completes immediately."""
        sprite = create_test_sprite()
        par = parallel()
        par.target = sprite
        par.start()

        assert par.done

    def test_parallel_starts_all_actions(self):
        """Test that parallel starts all actions simultaneously."""

        sprite = create_test_sprite()
        action1 = DelayUntil(duration(0.1))
        action2 = DelayUntil(duration(0.1))
        par = parallel(action1, action2)

        par.target = sprite
        par.start()

        # Both actions should be started (can't check internal state easily, but they should be running)
        assert not par.done  # Parallel shouldn't be done immediately

    def test_parallel_completes_when_all_actions_done(self):
        """Test that parallel completes when all actions are done."""

        sprite = create_test_sprite()
        action1 = DelayUntil(duration(0.05))
        action2 = DelayUntil(duration(0.1))  # Longer duration
        par = parallel(action1, action2)

        par.target = sprite
        par.start()

        # Update until first action completes
        par.update(0.06)
        assert action1.done
        assert not par.done  # Parallel not done until all actions done

        # Update until second action completes
        par.update(0.05)
        assert action2.done
        assert par.done

    def test_parallel_stops_all_actions(self):
        """Test that stopping parallel stops all actions."""

        sprite = create_test_sprite()
        action1 = DelayUntil(duration(1.0))  # Long duration
        action2 = DelayUntil(duration(1.0))  # Long duration
        par = parallel(action1, action2)

        par.target = sprite
        par.start()
        par.stop()

        assert action1.done  # Should be marked done by stop()
        assert action2.done  # Should be marked done by stop()

    def test_parallel_clone(self):
        """Test parallel cloning."""

        action1 = DelayUntil(duration(0.1))
        action2 = DelayUntil(duration(0.1))
        par = parallel(action1, action2)

        cloned = par.clone()

        assert cloned is not par
        assert len(cloned.actions) == 2
        assert cloned.actions[0] is not action1
        assert cloned.actions[1] is not action2


class TestOperatorOverloading:
    """Test suite for operator-based composition (+ for sequence, | for parallel)."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_plus_operator_creates_sequence(self):
        """Test that the '+' operator creates a sequential action."""

        sprite = create_test_sprite()
        action1 = DelayUntil(duration(0.05))
        action2 = DelayUntil(duration(0.05))

        # Use + operator to create sequence
        sequence_action = action1 + action2
        sequence_action.apply(sprite)

        # Should behave like a sequence - first action runs, then second
        Action.update_all(0.06)  # Complete first action
        assert action1.done

        Action.update_all(0.06)  # Complete second action
        assert action2.done

    def test_pipe_operator_creates_parallel(self):
        """Test that the '|' operator creates a parallel action."""

        sprite = create_test_sprite()
        action1 = DelayUntil(duration(0.05))
        action2 = DelayUntil(duration(0.1))  # Different duration

        # Use | operator to create parallel
        parallel_action = action1 | action2
        parallel_action.apply(sprite)

        # Should behave like a parallel - both run simultaneously
        Action.update_all(0.06)  # Complete first action
        assert action1.done
        assert not action2.done  # Second still running

        Action.update_all(0.05)  # Complete second action
        assert action2.done

    def test_mixed_operator_composition(self):
        """Test mixing + and | operators for complex compositions."""

        sprite = create_test_sprite()
        action1 = DelayUntil(duration(0.05))
        action2 = DelayUntil(duration(0.05))
        action3 = DelayUntil(duration(0.05))

        # Create a sequence where the second step is parallel actions
        complex_action = action1 + (action2 | action3)
        complex_action.apply(sprite)

        # First action should complete first
        Action.update_all(0.06)
        assert action1.done

        # After first action completes, parallel actions should run and complete
        Action.update_all(0.06)
        assert action2.done
        assert action3.done

    def test_operator_precedence_with_parentheses(self):
        """Test operator precedence with explicit parentheses."""

        sprite = create_test_sprite()
        action1 = DelayUntil(duration(0.05))
        action2 = DelayUntil(duration(0.05))
        action3 = DelayUntil(duration(0.05))

        # Test a + (b | c) - explicit parentheses
        composed = action1 + (action2 | action3)
        composed.apply(sprite)

        # First action completes
        Action.update_all(0.06)
        assert action1.done

        # Then parallel actions complete
        Action.update_all(0.06)
        assert action2.done
        assert action3.done


class TestNestedComposites:
    """Test suite for nested composite actions."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_sequence_of_parallels_with_operators(self):
        """Test sequence containing parallel actions using operators."""

        sprite = create_test_sprite()
        action1 = DelayUntil(duration(0.05))
        action2 = DelayUntil(duration(0.05))
        action3 = DelayUntil(duration(0.05))
        action4 = DelayUntil(duration(0.05))

        # Create sequence of parallels using operators
        composed = (action1 | action2) + (action3 | action4)
        composed.apply(sprite)

        # Update until first parallel completes
        Action.update_all(0.06)
        assert action1.done
        assert action2.done

        # Update until second parallel completes
        Action.update_all(0.06)
        assert action3.done
        assert action4.done

    def test_parallel_of_sequences_with_operators(self):
        """Test parallel containing sequence actions using operators."""

        sprite = create_test_sprite()
        action1 = DelayUntil(duration(0.05))
        action2 = DelayUntil(duration(0.05))
        action3 = DelayUntil(duration(0.05))
        action4 = DelayUntil(duration(0.05))

        # Create parallel of sequences using operators
        composed = (action1 + action2) | (action3 + action4)
        composed.apply(sprite)

        # Both sequences run in parallel, each taking 2 updates (0.05 + 0.05)
        Action.update_all(0.06)  # Complete first actions in each sequence
        Action.update_all(0.06)  # Complete second actions in each sequence

        # All actions should be done
        assert action1.done
        assert action2.done
        assert action3.done
        assert action4.done

    def test_traditional_vs_operator_equivalence(self):
        """Test that operator syntax produces equivalent results to function syntax."""

        sprite1 = create_test_sprite()
        sprite2 = create_test_sprite()

        # Traditional function approach
        action1_func = DelayUntil(duration(0.05))
        action2_func = DelayUntil(duration(0.05))
        traditional = sequence(action1_func, action2_func)
        traditional.apply(sprite1)

        # Operator approach
        action1_op = DelayUntil(duration(0.05))
        action2_op = DelayUntil(duration(0.05))
        operator_based = action1_op + action2_op
        operator_based.apply(sprite2)

        # Both should behave identically - complete first actions
        Action.update_all(0.06)
        assert action1_func.done == action1_op.done

        # Complete second actions
        Action.update_all(0.06)
        assert action2_func.done == action2_op.done


class TestRepeatFunction:
    """Test suite for repeat() function."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_repeat_initialization(self):
        """Test repeat initialization."""

        action = DelayUntil(duration(0.1))
        rep = repeat(action)

        assert rep.action == action
        assert rep.current_action is None
        assert not rep.done

    def test_repeat_starts_first_iteration(self):
        """Test that repeat starts the first iteration of the action."""

        sprite = create_test_sprite()
        action = DelayUntil(duration(0.05))
        rep = repeat(action)

        rep.target = sprite
        rep.start()

        assert rep.current_action is not None
        assert rep.current_action is not action  # Should be a clone
        assert not rep.done

    def test_repeat_restarts_action_when_completed(self):
        """Test that repeat restarts the action when it completes."""

        sprite = create_test_sprite()
        action = DelayUntil(duration(0.05))
        rep = repeat(action)

        rep.target = sprite
        rep.start()

        # Get the first iteration
        first_iteration = rep.current_action

        # Update until first iteration completes
        rep.update(0.06)
        assert first_iteration.done

        # Should have started a new iteration
        assert rep.current_action is not first_iteration
        assert not rep.done

    def test_repeat_continues_indefinitely(self):
        """Test that repeat continues indefinitely."""

        sprite = create_test_sprite()
        action = DelayUntil(duration(0.05))
        rep = repeat(action)

        rep.target = sprite
        rep.start()

        # Run multiple iterations
        for i in range(5):
            current_action = rep.current_action
            assert not rep.done

            # Complete this iteration
            rep.update(0.06)
            assert current_action.done

            # Trigger start of next iteration (may be deferred one frame)
            if rep.current_action is None:
                rep.update(0.0)

            assert rep.current_action is not current_action

    def test_repeat_stop_stops_current_action(self):
        """Test that stopping repeat stops the current action."""

        sprite = create_test_sprite()
        action = DelayUntil(duration(1.0))  # Long duration
        rep = repeat(action)

        rep.target = sprite
        rep.start()
        rep.stop()

        assert rep.current_action.done
        assert rep.done

    def test_repeat_clone(self):
        """Test repeat cloning."""

        action = DelayUntil(duration(0.1))
        rep = repeat(action)

        cloned = rep.clone()

        assert cloned is not rep
        assert cloned.action is not action
        assert cloned.current_action is None

    def test_repeat_with_no_action(self):
        """Test repeat with no action (should complete immediately)."""
        sprite = create_test_sprite()
        rep = repeat(None)

        rep.target = sprite
        rep.start()

        assert rep.done

    def test_repeat_with_composite_action(self):
        """Test repeat with a composite action (sequence)."""

        sprite = create_test_sprite()
        action1 = DelayUntil(duration(0.05))
        action2 = DelayUntil(duration(0.05))
        seq = sequence(action1, action2)
        rep = repeat(seq)

        rep.target = sprite
        rep.start()

        # First iteration should start
        assert rep.current_action is not None
        assert rep.current_action is not seq  # Should be a clone
        assert not rep.done

        # Complete first iteration (both delays)
        rep.update(0.06)  # Complete first delay
        rep.update(0.06)  # Complete second delay, complete sequence

        # Ensure the repeat schedules a new iteration (might begin next frame)
        if rep.current_action is None:
            rep.update(0.0)

        assert rep.current_action is not None
        assert not rep.done

    def test_repeat_with_move_action(self):
        """Test repeat with a MoveUntil action."""
        from actions.conditional import MoveUntil

        sprite = create_test_sprite()

        # Move right for a short duration
        move_action = MoveUntil(velocity=(100, 0), condition=duration(0.05))
        rep = repeat(move_action)
        rep.apply(sprite, tag="test_repeat")

        # Update to complete first iteration
        Action.update_all(0.06)

        # Ensure a new iteration has started (may require zero-dt tick)
        if sprite.change_x == 0:
            Action.update_all(0.0)

        assert sprite.change_x == 100  # Velocity should be set by new iteration

        # Update again with partial duration - iteration should still be running
        Action.update_all(0.03)

        # Should still have velocity from repeat cycles
        assert sprite.change_x == 100


class TestRepeatIntegration:
    """Integration tests for repeat with other composite actions."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_repeat_in_sequence(self):
        """Test repeat action used within a sequence."""

        sprite = create_test_sprite()
        setup_action = DelayUntil(duration(0.05))
        repeating_action = DelayUntil(duration(0.05))

        # Create sequence: setup action + repeating action
        rep = repeat(repeating_action)
        seq = sequence(setup_action, rep)

        seq.apply(sprite)

        # First, setup action should run
        Action.update_all(0.06)  # Complete setup

        # Now repeat should start and run indefinitely
        # Since repeat never completes, sequence never completes
        Action.update_all(0.06)  # First repeat iteration
        Action.update_all(0.06)  # Second repeat iteration

        # Sequence should still be running the repeat
        actions = Action.get_actions_for_target(sprite)
        assert len(actions) == 1  # The sequence is still active

    def test_repeat_in_parallel(self):
        """Test repeat action used within a parallel."""

        sprite = create_test_sprite()
        finite_action = DelayUntil(duration(0.1))
        repeating_action = DelayUntil(duration(0.05))

        # Create parallel: finite action + repeating action
        rep = repeat(repeating_action)
        par = parallel(finite_action, rep)

        par.apply(sprite)

        # Both should start
        Action.update_all(0.06)  # First repeat cycle completes, finite still running
        Action.update_all(0.06)  # Finite action completes, second repeat cycle

        # Since repeat never completes, parallel never completes naturally
        actions = Action.get_actions_for_target(sprite)
        assert len(actions) == 1  # The parallel is still active

    def test_operator_overloading_with_repeat(self):
        """Test that repeat works with operator overloading (+, |)."""

        sprite = create_test_sprite()
        action1 = DelayUntil(duration(0.05))
        action2 = DelayUntil(duration(0.05))

        # Create complex composition using operators
        rep = repeat(action1)
        composed = action2 + rep  # Sequence: action2 then infinite repeat

        composed.apply(sprite)

        # Update to complete first action
        Action.update_all(0.06)

        # Now repeat should be running
        Action.update_all(0.06)  # First repeat iteration
        Action.update_all(0.06)  # Second repeat iteration

        # Should still be active
        actions = Action.get_actions_for_target(sprite)
        assert len(actions) == 1


class TestVelocityForwarding:
    """Test suite for velocity forwarding in composite actions."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_velocity_forwarding_to_children(self):
        """Test that CompositeActions forward velocity changes to child actions that support it."""
        from actions.conditional import MoveUntil, infinite

        sprite = create_test_sprite()

        # Test 1: Parallel forwarding
        move_action1 = MoveUntil((5, 0), infinite)
        delay_action1 = DelayUntil(duration(1.0))

        par = parallel(move_action1, delay_action1)
        par.apply(sprite, tag="velocity_test")

        # Verify initial velocity
        assert move_action1.current_velocity == (5, 0)

        # Test velocity forwarding
        par.set_current_velocity((10, 3))
        assert move_action1.current_velocity == (10, 3)

        Action.stop_all()  # Clear actions between tests

        # Test 2: Sequence forwarding (should forward to current action)
        move_action2 = MoveUntil((7, 1), infinite)
        delay_action2 = DelayUntil(duration(1.0))

        seq = sequence(move_action2, delay_action2)
        seq.apply(sprite, tag="sequence_velocity_test")

        # Should forward to the current (first) action
        seq.set_current_velocity((15, -2))
        assert move_action2.current_velocity == (15, -2)

        Action.stop_all()  # Clear actions between tests

        # Test 3: Repeat forwarding
        move_action3 = MoveUntil((8, 2), infinite)
        rep = repeat(move_action3)
        rep.apply(sprite, tag="repeat_velocity_test")

        # Start the repeat so it has a current action
        Action.update_all(0.001)

        # Should forward to the current iteration (which is a clone)
        rep.set_current_velocity((20, 5))

        # The cloned action should have the new velocity
        assert rep.current_action.current_velocity == (20, 5)

    def test_velocity_forwarding_base_class(self):
        """Test that base CompositeAction set_current_velocity does nothing."""
        from actions.base import CompositeAction

        # Create a direct instance of the base CompositeAction
        base_composite = CompositeAction()

        # This should not raise an error and should do nothing
        base_composite.set_current_velocity((100, 200))

        # Should complete immediately since base class has no functionality
        assert True  # Just testing that no exception was raised

    def test_velocity_forwarding_with_noop_velocity(self):
        """Test velocity forwarding gracefully handles actions using the default no-op setter."""
        from actions.conditional import DelayUntil, MoveUntil, infinite

        sprite = create_test_sprite()

        # Create a custom action that doesn't support velocity control
        class CustomAction(DelayUntil):
            """A custom action that explicitly doesn't have set_current_velocity."""

            def __init__(self):
                super().__init__(duration(1.0))

        move_action = MoveUntil((3, 4), infinite)
        custom_action = CustomAction()

        # Test parallel with action that raises AttributeError
        par = parallel(move_action, custom_action)
        par.apply(sprite, tag="error_test")

        # This should not raise an error despite custom_action not supporting velocity
        par.set_current_velocity((6, 8))

        # The move action should still get the new velocity
        assert move_action.current_velocity == (6, 8)

    def test_velocity_forwarding_sequence_no_current_action(self):
        """Test sequence velocity forwarding when there's no current action."""
        from actions.conditional import DelayUntil

        sprite = create_test_sprite()

        # Create a sequence but don't start it
        seq = sequence(DelayUntil(duration(0.1)))
        # Don't apply it to a sprite so current_action remains None

        # This should not raise an error
        seq.set_current_velocity((10, 20))

        # Should handle gracefully
        assert seq.current_action is None

    def test_velocity_forwarding_repeat_no_current_action(self):
        """Test repeat velocity forwarding when there's no current action."""
        from actions.conditional import DelayUntil

        sprite = create_test_sprite()

        # Create a repeat but don't start it
        rep = repeat(DelayUntil(duration(0.1)))
        # Don't apply it to a sprite so current_action remains None

        # This should not raise an error
        rep.set_current_velocity((30, 40))

        # Should handle gracefully
        assert rep.current_action is None

    def test_velocity_forwarding_empty_parallel(self):
        """Test velocity forwarding on empty parallel action."""
        sprite = create_test_sprite()

        # Create empty parallel
        par = parallel()
        par.apply(sprite, tag="empty_test")

        # This should not raise an error
        par.set_current_velocity((70, 80))

        # Should handle gracefully with empty actions list
        assert len(par.actions) == 0

    def test_velocity_forwarding_sequence_noop(self):
        """Test sequence velocity forwarding with actions relying on the default no-op setter."""
        from actions.conditional import DelayUntil

        sprite = create_test_sprite()

        # Create a custom action that raises AttributeError when set_current_velocity is called
        class ActionWithoutVelocity(DelayUntil):
            def __init__(self):
                super().__init__(duration(0.1))

        action_without_velocity = ActionWithoutVelocity()
        seq = sequence(action_without_velocity)
        seq.apply(sprite, tag="seq_error_test")

        # This should trigger the AttributeError handling in _Sequence.set_current_velocity
        seq.set_current_velocity((25, 35))

        # Should complete without error
        assert seq.current_action is action_without_velocity

    def test_velocity_forwarding_repeat_noop(self):
        """Test repeat velocity forwarding with actions relying on the default no-op setter."""
        from actions.conditional import DelayUntil

        sprite = create_test_sprite()

        # Create a custom action that raises AttributeError
        class ActionWithoutVelocity(DelayUntil):
            def __init__(self):
                super().__init__(duration(0.1))

        action_without_velocity = ActionWithoutVelocity()
        rep = repeat(action_without_velocity)
        rep.apply(sprite, tag="rep_error_test")

        # Start the repeat so it has a current action (clone)
        Action.update_all(0.001)

        # The cloned action should also not have set_current_velocity
        # This should trigger the AttributeError handling in _Repeat.set_current_velocity
        rep.set_current_velocity((45, 55))

        # Should complete without error
        assert rep.current_action is not None


class TestCompositeReset:
    """Test suite for reset() functionality on composite actions."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_base_composite_action_reset(self):
        """Test that base CompositeAction.reset() resets flags."""
        from actions.base import CompositeAction

        # Create a minimal concrete subclass for testing
        class TestComposite(CompositeAction):
            def clone(self):
                return TestComposite()

        action = TestComposite()

        # Simulate completion
        action.done = True
        action._on_complete_called = True

        # Reset
        action.reset()

        # Verify base flags are reset
        assert action.done is False
        assert action._on_complete_called is False

    def test_sequence_reset_basic(self):
        """Test that sequence.reset() resets state and calls reset on child actions."""
        from actions.conditional import CycleTexturesUntil

        sprite = create_test_sprite()

        # Use CycleTexturesUntil which properly resets done flag
        textures = [arcade.Texture.create_empty(f"tex{i}", (10, 10)) for i in range(2)]
        action1 = CycleTexturesUntil(textures, frames_per_second=60, direction=1, condition=duration(0.05))
        action2 = CycleTexturesUntil(textures, frames_per_second=60, direction=1, condition=duration(0.05))
        seq = sequence(action1, action2)

        seq.apply(sprite, tag="test_reset")

        # Run until first action completes
        Action.update_all(0.06)

        assert action1.done
        assert seq.current_index == 1
        assert seq.current_action == action2

        # Reset
        seq.reset()

        # Verify sequence state is reset
        assert seq.current_index == 0
        assert seq.current_action is None
        assert seq.done is False
        assert seq._on_complete_called is False

        # Verify child actions were reset (reset() called on them)
        assert action1.done is False  # CycleTexturesUntil resets done
        assert action2.done is False

    def test_sequence_reset_after_completion(self):
        """Test that sequence can be reset after completion."""
        from actions.conditional import CycleTexturesUntil

        sprite = create_test_sprite()

        textures = [arcade.Texture.create_empty(f"tex{i}", (10, 10)) for i in range(2)]
        action1 = CycleTexturesUntil(textures, frames_per_second=60, direction=1, condition=duration(0.05))
        action2 = CycleTexturesUntil(textures, frames_per_second=60, direction=1, condition=duration(0.05))
        seq = sequence(action1, action2)

        seq.apply(sprite, tag="test_reset_reuse")

        # Complete the sequence
        Action.update_all(0.06)  # Complete first action
        Action.update_all(0.06)  # Complete second action

        assert seq.done
        assert action1.done
        assert action2.done

        # Reset
        seq.reset()

        # Verify state is reset
        assert seq.done is False
        assert seq.current_index == 0
        assert seq.current_action is None
        assert action1.done is False
        assert action2.done is False

    def test_parallel_reset_basic(self):
        """Test that parallel.reset() resets state and child actions."""
        from actions.conditional import CycleTexturesUntil

        sprite = create_test_sprite()

        textures = [arcade.Texture.create_empty(f"tex{i}", (10, 10)) for i in range(2)]
        action1 = CycleTexturesUntil(textures, frames_per_second=60, direction=1, condition=duration(0.05))
        action2 = CycleTexturesUntil(textures, frames_per_second=60, direction=1, condition=duration(0.1))
        par = parallel(action1, action2)

        par.apply(sprite, tag="test_parallel_reset")

        # Run until first action completes
        Action.update_all(0.06)

        assert action1.done
        assert not action2.done
        assert not par.done

        # Reset
        par.reset()

        # Verify parallel state is reset
        assert par.done is False
        assert par._on_complete_called is False

        # Verify child actions are reset
        assert action1.done is False
        assert action2.done is False

    def test_parallel_reset_after_completion(self):
        """Test that parallel can be reset after completion."""
        from actions.conditional import CycleTexturesUntil

        sprite = create_test_sprite()

        textures = [arcade.Texture.create_empty(f"tex{i}", (10, 10)) for i in range(2)]
        action1 = CycleTexturesUntil(textures, frames_per_second=60, direction=1, condition=duration(0.05))
        action2 = CycleTexturesUntil(textures, frames_per_second=60, direction=1, condition=duration(0.05))
        par = parallel(action1, action2)

        par.apply(sprite, tag="test_parallel_reuse")

        # Complete the parallel
        Action.update_all(0.06)

        assert par.done
        assert action1.done
        assert action2.done

        # Reset
        par.reset()

        # Verify state is reset
        assert par.done is False
        assert action1.done is False
        assert action2.done is False

    def test_repeat_reset_basic(self):
        """Test that repeat.reset() resets state and child action."""
        sprite = create_test_sprite()

        action = DelayUntil(duration(0.05))
        rep = repeat(action)

        rep.apply(sprite, tag="test_repeat_reset")

        # Run until first iteration completes
        Action.update_all(0.06)

        # First iteration should complete, but repeat continues
        assert rep.current_action is not None
        assert rep.current_action is not action  # It's a clone

        # Reset
        rep.reset()

        # Verify repeat state is reset
        assert rep.current_action is None
        assert rep.done is False
        assert rep._on_complete_called is False

    def test_repeat_reset_clears_current_action(self):
        """Test that repeat.reset() clears and resets the current cloned action."""
        from actions.conditional import CycleTexturesUntil

        sprite = create_test_sprite()

        textures = [arcade.Texture.create_empty(f"tex{i}", (10, 10)) for i in range(2)]
        action = CycleTexturesUntil(textures, frames_per_second=60, direction=1, condition=duration(0.05))
        rep = repeat(action)

        rep.apply(sprite, tag="test_repeat_current")

        # Run one iteration
        Action.update_all(0.06)

        # Verify there's a current action (it's a clone, not the original)
        assert rep.current_action is not None
        assert rep.current_action is not action  # It's a clone

        # Reset the repeat
        rep.reset()

        # Verify the repeat state is reset
        assert rep.current_action is None
        assert rep.done is False
        assert rep._on_complete_called is False

    def test_nested_sequence_reset(self):
        """Test that nested sequences reset properly."""
        from actions.conditional import CycleTexturesUntil

        sprite = create_test_sprite()

        textures = [arcade.Texture.create_empty(f"tex{i}", (10, 10)) for i in range(2)]
        action1 = CycleTexturesUntil(textures, frames_per_second=60, direction=1, condition=duration(0.05))
        action2 = CycleTexturesUntil(textures, frames_per_second=60, direction=1, condition=duration(0.05))
        inner_seq = sequence(action1, action2)

        action3 = CycleTexturesUntil(textures, frames_per_second=60, direction=1, condition=duration(0.05))
        outer_seq = sequence(inner_seq, action3)

        outer_seq.apply(sprite, tag="test_nested_reset")

        # Run until inner sequence completes
        Action.update_all(0.06)  # Complete action1
        Action.update_all(0.06)  # Complete action2, inner_seq done

        assert inner_seq.done
        assert action1.done
        assert action2.done

        # Reset outer sequence
        outer_seq.reset()

        # Verify inner sequence and its children are reset
        assert outer_seq.done is False
        assert inner_seq.done is False
        assert action1.done is False
        assert action2.done is False
        assert action3.done is False

    def test_parallel_with_sequences_reset(self):
        """Test that parallel containing sequences resets properly."""
        from actions.conditional import CycleTexturesUntil

        sprite = create_test_sprite()

        textures = [arcade.Texture.create_empty(f"tex{i}", (10, 10)) for i in range(2)]
        action1 = CycleTexturesUntil(textures, frames_per_second=60, direction=1, condition=duration(0.05))
        action2 = CycleTexturesUntil(textures, frames_per_second=60, direction=1, condition=duration(0.05))
        seq1 = sequence(action1, action2)

        action3 = CycleTexturesUntil(textures, frames_per_second=60, direction=1, condition=duration(0.05))
        seq2 = sequence(action3)

        par = parallel(seq1, seq2)
        par.apply(sprite, tag="test_parallel_seq_reset")

        # Run until both sequences complete
        Action.update_all(0.06)  # Complete action1 and action3
        Action.update_all(0.06)  # Complete action2, both sequences done

        assert par.done
        assert seq1.done
        assert seq2.done

        # Reset
        par.reset()

        # Verify everything is reset
        assert par.done is False
        assert seq1.done is False
        assert seq2.done is False
        assert action1.done is False
        assert action2.done is False
        assert action3.done is False

    def test_empty_sequence_reset(self):
        """Test that empty sequence reset works."""
        seq = sequence()

        # Empty sequence completes immediately
        sprite = create_test_sprite()
        seq.apply(sprite, tag="empty")

        assert seq.done

        # Reset
        seq.reset()

        # Verify it's reset
        assert seq.done is False
        assert seq._on_complete_called is False
        assert seq.current_index == 0
        assert seq.current_action is None

    def test_empty_parallel_reset(self):
        """Test that empty parallel reset works."""
        par = parallel()

        # Empty parallel completes immediately
        sprite = create_test_sprite()
        par.apply(sprite, tag="empty")

        assert par.done

        # Reset
        par.reset()

        # Verify it's reset
        assert par.done is False
        assert par._on_complete_called is False


class TestPriority1_EmptyCompositeRepresentation:
    """Test __repr__ methods for composite actions."""

    def test_sequence_repr(self):
        """Test sequence __repr__ method - covers line 108-109 in composite.py."""
        action1 = DelayUntil(duration(0.1))
        action2 = DelayUntil(duration(0.2))
        seq = sequence(action1, action2)

        repr_str = repr(seq)
        assert "_Sequence" in repr_str
        assert "actions=" in repr_str

    def test_parallel_repr(self):
        """Test parallel __repr__ method - covers line 189-190 in composite.py."""
        action1 = DelayUntil(duration(0.1))
        action2 = DelayUntil(duration(0.2))
        par = parallel(action1, action2)

        repr_str = repr(par)
        assert "_Parallel" in repr_str
        assert "actions=" in repr_str

    def test_repeat_repr(self):
        """Test repeat __repr__ method - covers line 287 in composite.py."""
        action = DelayUntil(duration(0.1))
        rep = repeat(action)

        repr_str = repr(rep)
        assert "_Repeat" in repr_str
        assert "action=" in repr_str


class TestPriority4_AttributeErrorHandling:
    """Test AttributeError handling in composite actions - covers lines 103-105, 282-284."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_sequence_set_current_velocity_attribute_error(self):
        """Test sequence handles AttributeError when action doesn't support velocity - line 103-105."""
        sprite = create_test_sprite()

        # DelayUntil doesn't support velocity control in meaningful way
        action = DelayUntil(duration(1.0))
        seq = sequence(action)
        seq.apply(sprite, tag="test")

        # This should not raise an error even though DelayUntil's set_current_velocity is a no-op
        seq.set_current_velocity((10, 20))

        # Should complete without error
        assert seq.current_action is action

    def test_repeat_set_current_velocity_attribute_error(self):
        """Test repeat handles AttributeError when action doesn't support velocity - line 282-284."""
        sprite = create_test_sprite()

        # DelayUntil doesn't support velocity control
        action = DelayUntil(duration(1.0))
        rep = repeat(action)
        rep.apply(sprite, tag="test")

        # Start the repeat so it has a current action
        Action.update_all(0.001)

        # This should not raise an error
        rep.set_current_velocity((30, 40))

        # Should handle gracefully
        assert rep.current_action is not None


class TestPriority2_SequenceEdgeCases:
    """Test Sequence edge cases - covers lines 49-52, 56-58 in composite.py."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_sequence_update_with_empty_actions(self):
        """Test sequence update when actions list is empty - lines 49-52."""
        sprite = create_test_sprite()
        seq = sequence()
        seq.apply(sprite, tag="empty")

        # Update should handle empty actions gracefully
        Action.update_all(1 / 60)

        assert seq.done

    def test_sequence_current_action_none_starts_next(self):
        """Test sequence starts next action when current is None - lines 56-58."""
        sprite = create_test_sprite()

        action1 = DelayUntil(duration(0.05))
        action2 = DelayUntil(duration(0.05))
        seq = sequence(action1, action2)

        seq.target = sprite
        seq.start()

        # Complete first action
        seq.update(0.06)

        # At this point current_action should transition
        assert action1.done
        # Second action should now be current
        assert seq.current_action == action2


class TestPriority3_ParallelEmptyHandling:
    """Test Parallel empty handling during update - covers lines 148-151 in composite.py."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_parallel_update_with_empty_actions(self):
        """Test parallel update when actions list is empty - lines 148-151."""
        sprite = create_test_sprite()
        par = parallel()
        par.apply(sprite, tag="empty")

        # Update should handle empty actions gracefully
        Action.update_all(1 / 60)

        assert par.done


class TestPriority4_RepeatEdgeCases:
    """Test Repeat edge cases - covers lines 235-238, 253-255 in composite.py."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_repeat_update_with_no_action(self):
        """Test repeat update when action is None - lines 235-238."""
        sprite = create_test_sprite()
        rep = repeat(None)
        rep.apply(sprite, tag="no_action")

        # Update should handle None action gracefully
        Action.update_all(1 / 60)

        assert rep.done

    def test_repeat_current_action_none_starts_clone(self):
        """Test repeat starts clone when current_action is None - lines 253-255."""
        sprite = create_test_sprite()

        action = DelayUntil(duration(0.05))
        rep = repeat(action)

        rep.target = sprite
        rep.start()

        # Current action should be set after start
        first_action = rep.current_action
        assert first_action is not None
        assert first_action is not action  # Should be a clone

        # Complete current action
        rep.update(0.06)

        # Should have started a new clone
        assert rep.current_action is not None
        assert rep.current_action is not first_action


class TestPriority10_CompositeEmptyHandling:
    """Additional composite action empty handling tests."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_sequence_repr_with_empty_actions(self):
        """Test sequence __repr__ with empty actions list."""
        seq = sequence()
        repr_str = repr(seq)
        assert "_Sequence" in repr_str
        assert "[]" in repr_str or "actions=" in repr_str

    def test_parallel_repr_with_empty_actions(self):
        """Test parallel __repr__ with empty actions list."""
        par = parallel()
        repr_str = repr(par)
        assert "_Parallel" in repr_str
        assert "[]" in repr_str or "actions=" in repr_str

    def test_repeat_repr_with_none_action(self):
        """Test repeat __repr__ with None action."""
        rep = repeat(None)
        repr_str = repr(rep)
        assert "_Repeat" in repr_str
        assert "None" in repr_str
