"""
ArcadeActions - A declarative action system for Arcade games.

Actions available:
- Movement: MoveUntil with built-in boundary checking
- Rotation: RotateUntil
- Scaling: ScaleUntil
- Visual: FadeUntil, BlinkUntil
- Path: FollowPathUntil
- Timing: DelayUntil, duration, time_elapsed
- Easing: Ease wrapper for smooth acceleration/deceleration effects
- Interpolation: TweenUntil for direct property animation from start to end value
- Composition: sequence() and parallel() functions for combining actions
- Formation: arrange_line, arrange_grid, arrange_circle, arrange_v_formation, arrange_diamond,
            arrange_triangle, arrange_hexagonal_grid, arrange_arc, arrange_concentric_rings,
            arrange_cross, arrange_arrow functions
- Movement Patterns: create_zigzag_pattern, create_wave_pattern, create_spiral_pattern, etc.
- Condition helpers: sprite_count, time_elapsed
- Experimental: SpritePool for zero-allocation gameplay
"""

# Core classes
from .base import Action

# Composition functions
from .composite import parallel, repeat, sequence

# Conditional actions
from .conditional import (
    BlinkUntil,
    CallbackUntil,
    CycleTexturesUntil,
    DelayUntil,
    FadeUntil,
    FollowPathUntil,
    MoveUntil,
    RotateUntil,
    ScaleUntil,
    TweenUntil,
    duration,
    infinite,
)
from .config import (
    apply_environment_configuration,
    clear_observed_actions,
    get_debug_actions,
    get_debug_options,
    observe_actions,
    set_debug_actions,
    set_debug_options,
)

# Display utilities
from .display import center_window

# Easing wrappers
from .easing import (
    Ease,
)

# Formation arrangement functions
from .formation import (
    arrange_arc,
    arrange_arrow,
    arrange_circle,
    arrange_concentric_rings,
    arrange_cross,
    arrange_diamond,
    arrange_grid,
    arrange_hexagonal_grid,
    arrange_line,
    arrange_triangle,
    arrange_v_formation,
)

# Helper functions
from .helpers import (
    blink_until,
    callback_until,
    cycle_textures_until,
    delay_until,
    ease,
    fade_until,
    follow_path_until,
    move_by,
    move_to,
    move_until,
    rotate_until,
    scale_until,
    tween_until,
)

# Instant actions
from .instant import MoveBy, MoveTo

# Movement patterns and condition helpers
from .pattern import (
    create_bounce_pattern,
    create_figure_eight_pattern,
    create_formation_entry_from_sprites,
    create_orbit_pattern,
    create_patrol_pattern,
    create_spiral_pattern,
    create_wave_pattern,
    create_zigzag_pattern,
    sprite_count,
    time_elapsed,
)

# Experimental pools module
from .pools import SpritePool

__all__ = [
    # Core classes
    "Action",
    # Configuration
    "set_debug_actions",
    "get_debug_actions",
    "apply_environment_configuration",
    "set_debug_options",
    "get_debug_options",
    "observe_actions",
    "clear_observed_actions",
    # Conditional actions
    "MoveUntil",
    "RotateUntil",
    "ScaleUntil",
    "FadeUntil",
    "BlinkUntil",
    "CallbackUntil",
    "DelayUntil",
    "FollowPathUntil",
    "TweenUntil",
    "CycleTexturesUntil",
    "duration",
    "infinite",
    # Instant actions
    "MoveTo",
    "MoveBy",
    # Easing wrappers
    "Ease",
    # Composition functions
    "sequence",
    "parallel",
    "repeat",
    # Formation arrangement functions
    "arrange_arc",
    "arrange_arrow",
    "arrange_circle",
    "arrange_concentric_rings",
    "arrange_cross",
    "arrange_diamond",
    "arrange_grid",
    "arrange_hexagonal_grid",
    "arrange_line",
    "arrange_triangle",
    "arrange_v_formation",
    # Movement patterns
    "create_formation_entry_from_sprites",
    "create_zigzag_pattern",
    "create_wave_pattern",
    "create_spiral_pattern",
    "create_figure_eight_pattern",
    "create_orbit_pattern",
    "create_bounce_pattern",
    "create_patrol_pattern",
    # Condition helpers
    "time_elapsed",
    "sprite_count",
    # Helper functions
    "move_by",
    "move_to",
    "move_until",
    "rotate_until",
    "follow_path_until",
    "blink_until",
    "callback_until",
    "delay_until",
    "tween_until",
    "scale_until",
    "fade_until",
    "cycle_textures_until",
    "ease",
    # display
    "center_window",
    # experimental pools
    "SpritePool",
]

# Apply environment-driven configuration at import time so applications can
# enable debugging via ARCADEACTIONS_DEBUG without additional code changes.
# This remains opt-in and side-effect free beyond toggling debug output.
apply_environment_configuration()
