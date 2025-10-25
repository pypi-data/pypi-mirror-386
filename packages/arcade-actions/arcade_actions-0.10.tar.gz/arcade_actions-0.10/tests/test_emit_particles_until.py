import types

import pytest

from actions import Action
from actions.conditional import duration


class FakeEmitter:
    def __init__(self):
        self.center_x = 0.0
        self.center_y = 0.0
        self.angle = 0.0
        self.update_calls = 0
        self.destroy_calls = 0

    def update(self):
        self.update_calls += 1

    def destroy(self):
        self.destroy_calls += 1


def make_emitter_factory():
    def factory(_sprite):
        return FakeEmitter()

    return factory


class TestEmitParticlesUntil:
    def teardown_method(self):
        Action.stop_all()

    def test_emitter_per_sprite_center_anchor_and_rotation(self, test_sprite_list):
        from actions.conditional import EmitParticlesUntil

        # Assign distinct angles for follow_rotation verification
        for i, s in enumerate(test_sprite_list):
            s.angle = 10 * (i + 1)

        # Apply action with follow_rotation
        action = EmitParticlesUntil(
            emitter_factory=make_emitter_factory(),
            condition=duration(0.05),
            anchor="center",
            follow_rotation=True,
        )
        action.apply(test_sprite_list)

        # Drive updates
        Action.update_all(0.016)
        Action.update_all(0.016)

        # Validate emitters exist for each sprite and follow position/angle
        assert hasattr(action, "_emitters") and len(action._emitters) == len(test_sprite_list)

        for sprite in test_sprite_list:
            emitter = action._emitters[id(sprite)]
            assert pytest.approx(emitter.center_x) == sprite.center_x
            assert pytest.approx(emitter.center_y) == sprite.center_y
            assert pytest.approx(emitter.angle) == sprite.angle
            assert emitter.update_calls >= 1

        # After completion, emitters should be destroyed
        Action.update_all(0.06)
        for sprite in test_sprite_list:
            emitter = action._emitters_snapshot[id(sprite)]
            assert emitter.destroy_calls == 1
        assert action.done

    def test_custom_anchor_offset_tuple(self, test_sprite):
        from actions.conditional import EmitParticlesUntil

        test_sprite.center_x = 200
        test_sprite.center_y = 300

        offset = (5.0, -3.0)
        action = EmitParticlesUntil(
            emitter_factory=make_emitter_factory(),
            condition=duration(0.02),
            anchor=offset,
            follow_rotation=False,
        )
        action.apply(test_sprite)

        Action.update_all(0.016)

        emitter = next(iter(action._emitters.values()))
        assert pytest.approx(emitter.center_x) == test_sprite.center_x + offset[0]
        assert pytest.approx(emitter.center_y) == test_sprite.center_y + offset[1]


class TestEmitParticlesUntilErrorHandling:
    """Test EmitParticlesUntil error handling and edge cases."""

    def teardown_method(self):
        Action.stop_all()

    def test_on_stop_callback_exception(self, test_sprite):
        """Test EmitParticlesUntil handles on_stop callback exceptions."""
        from actions.conditional import EmitParticlesUntil

        def failing_callback():
            raise ValueError("Callback failed")

        action = EmitParticlesUntil(
            emitter_factory=make_emitter_factory(),
            condition=duration(0.01),  # Very short duration
            on_stop=failing_callback,
        )
        action.apply(test_sprite)

        # Should complete without crashing despite callback failure
        Action.update_all(0.02)
        assert action.done

    def test_missing_emitter_update(self, test_sprite):
        """Test update_effect handles missing emitter gracefully."""
        from actions.conditional import EmitParticlesUntil

        action = EmitParticlesUntil(
            emitter_factory=make_emitter_factory(),
            condition=duration(0.05),
        )
        action.apply(test_sprite)

        # Manually remove emitter from internal dict to simulate missing case
        sprite_id = id(test_sprite)
        del action._emitters[sprite_id]

        # Should not crash on update
        Action.update_all(0.016)
        assert not action.done

    def test_emitter_update_failure(self, test_sprite):
        """Test EmitParticlesUntil handles emitter update exceptions."""
        from actions.conditional import EmitParticlesUntil

        class FailingEmitter(FakeEmitter):
            def update(self):
                raise RuntimeError("Update failed")

        def failing_emitter_factory(sprite):
            return FailingEmitter()

        action = EmitParticlesUntil(
            emitter_factory=failing_emitter_factory,
            condition=duration(0.05),
        )
        action.apply(test_sprite)

        # Should not crash on emitter update failure
        Action.update_all(0.016)
        assert not action.done

    def test_emitter_destroy_failure(self, test_sprite):
        """Test EmitParticlesUntil handles emitter destroy exceptions."""
        from actions.conditional import EmitParticlesUntil

        class FailingEmitter(FakeEmitter):
            def destroy(self):
                raise RuntimeError("Destroy failed")

        def failing_emitter_factory(sprite):
            return FailingEmitter()

        action = EmitParticlesUntil(
            emitter_factory=failing_emitter_factory,
            condition=duration(0.01),  # Very short duration
            destroy_on_stop=True,
        )
        action.apply(test_sprite)

        # Should complete without crashing despite destroy failure
        Action.update_all(0.02)
        assert action.done

    def test_emitter_without_destroy_method(self, test_sprite):
        """Test EmitParticlesUntil handles emitters without destroy method."""
        from actions.conditional import EmitParticlesUntil

        class NoDestroyEmitter:
            """Emitter without destroy method."""

            def __init__(self):
                self.center_x = 0.0
                self.center_y = 0.0
                self.angle = 0.0
                self.update_calls = 0
                # No destroy method

            def update(self):
                self.update_calls += 1

        def no_destroy_factory(sprite):
            return NoDestroyEmitter()

        action = EmitParticlesUntil(
            emitter_factory=no_destroy_factory,
            condition=duration(0.01),  # Very short duration
            destroy_on_stop=True,
        )
        action.apply(test_sprite)

        # Should complete without crashing
        Action.update_all(0.02)
        assert action.done

    def test_emitter_without_update_method(self, test_sprite):
        """Test EmitParticlesUntil handles emitters without update method."""
        from actions.conditional import EmitParticlesUntil

        class NoUpdateEmitter:
            """Emitter without update method."""

            def __init__(self):
                self.center_x = 0.0
                self.center_y = 0.0
                self.angle = 0.0
                self.destroy_calls = 0
                # No update method

            def destroy(self):
                self.destroy_calls += 1

        def no_update_factory(sprite):
            return NoUpdateEmitter()

        action = EmitParticlesUntil(
            emitter_factory=no_update_factory,
            condition=duration(0.05),
        )
        action.apply(test_sprite)

        # Should not crash on update
        Action.update_all(0.016)
        assert not action.done

    def test_clone_method(self, test_sprite):
        """Test EmitParticlesUntil clone method."""
        from actions.conditional import EmitParticlesUntil

        original = EmitParticlesUntil(
            emitter_factory=make_emitter_factory(),
            condition=duration(0.05),
            anchor=(10.0, 20.0),
            follow_rotation=True,
            start_paused=True,
            destroy_on_stop=False,
        )

        cloned = original.clone()

        # Should have same configuration
        assert cloned._factory == original._factory
        assert cloned._anchor == original._anchor
        assert cloned._follow_rotation == original._follow_rotation
        assert cloned._start_paused == original._start_paused
        assert cloned._destroy_on_stop == original._destroy_on_stop
        assert cloned.condition != original.condition  # Different condition instance

    def test_destroy_on_stop_false(self, test_sprite):
        """Test EmitParticlesUntil with destroy_on_stop=False."""
        from actions.conditional import EmitParticlesUntil

        action = EmitParticlesUntil(
            emitter_factory=make_emitter_factory(),
            condition=duration(0.01),  # Very short duration
            destroy_on_stop=False,
        )
        action.apply(test_sprite)

        # Complete the action
        Action.update_all(0.02)
        assert action.done

        # Emitter should still exist in snapshot but not be destroyed
        emitter = next(iter(action._emitters_snapshot.values()))
        assert emitter.destroy_calls == 0
