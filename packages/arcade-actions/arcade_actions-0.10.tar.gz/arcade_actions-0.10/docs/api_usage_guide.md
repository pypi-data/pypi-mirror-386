# ArcadeActions API Usage Guide

## Overview

ArcadeActions provides a conditional action system that works directly with Arcade's native sprites and sprite lists. The framework uses **condition-based actions** rather than duration-based ones, enabling more flexible and declarative game behaviors.

## Recommended Usage Patterns

### Display Utilities

* **`center_window`** – center an `arcade.Window` on the primary monitor before it becomes visible (SDL2-first fallback to screeninfo). Example projects demonstrate usage.

### Pattern 1: Helper Functions for Simple, Immediate Actions

Helper functions like `move_until`, `rotate_until`, and `follow_path_until` are designed for simple, immediate application to sprites:

```python
from actions import move_until, rotate_until, cycle_textures_until, duration

# Simple, immediate actions - this is what helper functions are for
move_until(player_sprite, velocity=(5, 0), condition=lambda: player_sprite.center_x > 800)
rotate_until(enemy_swarm, velocity=1.5, condition=duration(5.0))
cycle_textures_until(power_up_sprite, textures=power_up_textures, frames_per_second=30.0)
```

### Pattern 2: Direct Classes with sequence() for Complex Compositions

For complex, multi-step sequences, use direct action classes with the `sequence()` and `parallel()` functions:

```python
from actions import Action, DelayUntil, FadeUntil, MoveUntil, RotateUntil, duration, sequence, parallel

# Complex sequences - use direct classes
complex_behavior = sequence(
    DelayUntil(duration(1.0)),
    MoveUntil(velocity=(100, 0), condition=duration(2.0)),
    parallel(
        RotateUntil(angular_velocity=180, condition=duration(1.0)),
        FadeUntil(fade_velocity=-50, condition=duration(1.5))
    )
)
complex_behavior.apply(sprite, tag="complex_movement")
```

### Why This Design?

**Helper functions** immediately apply actions when called, which conflicts with sequence construction. **Direct classes** create actions without applying them, allowing proper sequence composition.

```python
# ✅ CORRECT: Direct classes + sequence()
# This works perfectly because actions aren't applied until the sequence is
sequence(
    DelayUntil(duration(1.0)),
    MoveUntil(velocity=(5, 0), condition=duration(2.0))
).apply(sprite)

# ✅ ALSO CORRECT: Helper functions for immediate, simple actions
move_until(sprite, velocity=(5, 0), condition=duration(2.0))  # Applied immediately
```

## Core Design Principles

### 1. Velocity Semantics: Pixels Per Frame at 60 FPS
**CRITICAL:** ArcadeActions uses Arcade's native velocity semantics - values represent "pixels per frame at 60 FPS", NOT "pixels per second".

```python
# Correct: 5 means "5 pixels per frame" (equivalent to 300 pixels/second at 60 FPS)
move_action = MoveUntil(velocity=(5, 0), condition=cond)  # Moves 5 pixels per frame
rotate_action = RotateUntil(angular_velocity=3, condition=cond)   # Rotates 3 degrees per frame

# These values are applied directly to sprite.change_x, sprite.change_y, sprite.change_angle
# Arcade's internal update system handles the frame-rate timing
```

This maintains consistency with Arcade's native sprite system where `sprite.change_x = 5` moves the sprite 5 pixels per frame.

### 2. Global Action Management
All actions are managed globally - no manual action tracking needed:

```python
from actions import Action, duration, move_until

# Apply actions directly to any arcade.Sprite or arcade.SpriteList
move_until(sprite, velocity=(100, 0), condition=duration(2.0))

# Global update handles everything
def update(self, delta_time):
    Action.update_all(delta_time)  # Updates all active actions
```

### 3. Target Types: arcade.Sprite and arcade.SpriteList
All action functions accept either a single sprite or a sprite list as their target:

```python
# Single sprite target
player = arcade.Sprite(":resources:images/player.png")
move_until(player, velocity=(100, 0), condition=duration(2.0))

# Sprite list target (all sprites move together)
enemies = arcade.SpriteList()
for i in range(5):
    enemy = arcade.Sprite(":resources:images/enemy.png")
    enemies.append(enemy)
move_until(enemies, velocity=(0, -50), condition=duration(3.0))
```

### 4. Condition-Based Actions
Actions run until conditions are met, not for fixed durations:

```python
from actions import move_until, rotate_until, fade_until, follow_path_until

# Velocity-based movement until condition is met (pixels per frame at 60 FPS)
move_until(sprite, velocity=(5, -2), condition=lambda: sprite.center_y < 100)

# Path following with automatic rotation
path_points = [(100, 100), (200, 200), (300, 100)]
follow_path_until(
    sprite, path_points, velocity=2.5, condition=lambda: sprite.center_x > 400
)

rotate_until(sprite, angular_velocity=1.5, condition=lambda: sprite.angle >= 45)
fade_until(sprite, fade_velocity=-4, condition=lambda: sprite.alpha <= 50)
```

### 5. Clear Separation of Use Cases

| Use Case | Pattern | Example |
|----------|---------|---------|
| **Simple immediate actions** | Helper functions | `move_until(sprite, (5, 0), condition)` |
| **Complex sequences** | Direct classes + `sequence()` | `sequence(DelayUntil(...), MoveUntil(...))` |
| **Parallel effects** | Direct classes + `parallel()` | `parallel(MoveUntil(...), FadeUntil(...))` |

## Core Components

### Action Types

#### Conditional Actions (actions/conditional.py)
- **MoveUntil** - Velocity-based movement
- **FollowPathUntil** - Follow Bezier curve paths with optional sprite rotation to face movement direction
- **RotateUntil** - Angular velocity rotation
- **ScaleUntil** - Scale velocity changes
- **FadeUntil** - Alpha velocity changes
- **CycleTexturesUntil** - Cycle through a list of textures at specified frame rate
- **BlinkUntil** - Toggle sprite visibility with optional enter/exit callbacks
- **CallbackUntil** - Execute callback functions at specified intervals or every frame
- **DelayUntil** - Wait for condition
- **TweenUntil** - Direct property animation from start to end value

#### Composite Actions (actions/composite.py)
- **Sequential actions** - Run actions one after another (use `sequence()`)
- **Parallel actions** - Run actions in parallel (use `parallel()`)
- **Repeat actions** - Repeat an action indefinitely (use `repeat()`)

#### Boundary Handling (actions/conditional.py)
- **MoveUntil with bounds** - Built-in boundary detection with bounce/wrap behaviors

#### Formation Management (actions/formation.py)
- **Formation functions** - Grid, line, circle, diamond, V-formation, triangle, hexagonal grid, arc, concentric rings, cross, and arrow positioning patterns
  - Zero-allocation support: pass `sprites=` to arrange existing sprites without allocating
  - Contract: exactly one of `sprites` or creation inputs (`count` / `sprite_factory`) is required
  - Grid rule: when `sprites` is provided, `len(sprites)` must equal `rows * cols`

#### Movement Patterns (actions/pattern.py)
- **Movement pattern functions** - Zigzag, wave, spiral, figure-8, orbit, bounce, and patrol movement patterns
- **Condition helpers** - Time-based and sprite count conditions for use with conditional actions

#### Easing Effects (actions/easing.py)
- **Ease wrapper** - Apply smooth acceleration/deceleration curves to any conditional action
- **Built-in easing functions** - Use Arcade's ease_in, ease_out, ease_in_out curves
- **Custom easing support** - Create custom easing curves for specialized effects
- **Nested easing** - Combine multiple easing levels for complex animations
- **Completion callbacks** - Execute code when easing transitions complete

## Animation Approaches: Ease vs TweenUntil

ArcadeActions provides two distinct but complementary approaches for creating smooth animations. Understanding when to use each is crucial for effective game development.

### Ease: Smooth Transitions for Continuous Actions

**Purpose:** Ease wraps continuous actions (like `MoveUntil`, `FollowPathUntil`, `RotateUntil`) and modulates their intensity over time, creating smooth acceleration and deceleration effects.

**How it works:** The `ease()` helper function wraps an existing action and applies the eased effect to a target. After the easing duration completes, the wrapped action continues running at full intensity until its own condition is met.

**Key characteristics:**
- Wraps existing continuous actions
- Creates smooth start/stop transitions
- Wrapped action continues after easing completes
- Perfect for velocity-based animations
- Supports complex actions like curved path following

```python
from actions import ease, infinite, move_until, follow_path_until
from arcade import easing

# Example 1: Smooth missile launch
missile_movement = move_until(missile, velocity=(300, 0), condition=infinite)  # Continuous movement
ease(missile, missile_movement, duration=1.5, ease_function=easing.ease_out)

# Result: Missile smoothly accelerates to 300px/s over 1.5 seconds, then continues at that speed

# Example 2: Smooth curved path with rotation
path_points = [(100, 100), (200, 200), (400, 150), (500, 100)]
path_action = follow_path_until(
    enemy, path_points, velocity=250, condition=infinite
)
ease(enemy, path_action, duration=2.0, ease_function=easing.ease_in_out)
# Result: Enemy smoothly accelerates along curved path while rotating to face direction

# Example 3: Formation movement
formation_move = move_until(enemy_formation, velocity=(100, 0), condition=infinite)
ease(enemy_formation, formation_move, duration=1.0, ease_function=easing.ease_in)
# Result: Entire formation smoothly accelerates to marching speed
```

### TweenUntil: Direct Property Animation

**Purpose:** `tween_until` directly animates a specific sprite property from a start value to an end value over time, with optional easing curves for the interpolation itself.

**How it works:** Calculates intermediate values between start and end using linear interpolation and an optional easing function, then directly sets the property value each frame. The action completes when the end value is reached or the condition is met.

**Key characteristics:**
- Direct property manipulation (center_x, center_y, angle, scale, alpha, etc.)
- Precise A-to-B animations
- Built-in easing support for the interpolation curve
- Action completes when animation finishes
- Perfect for UI animations and precise movements

```python
from actions import duration,tween_until
from arcade import easing

# Example 1: UI panel slide-in
tween_until(ui_panel, start_value=-200, end_value=100, property_name="center_x", condition=duration(0.8), ease_function=easing.ease_out)
# Result: Panel slides from x=-200 to x=100 with smooth deceleration, then stops

# Example 2: Health bar animation
tween_until(health_bar, start_value=current_health, end_value=new_health, property_name="width", condition=duration(0.5))
# Result: Health bar width changes smoothly from current to new value

# Example 3: Button feedback animation
tween_until(button_sprite, start_value=1.0, end_value=1.2, property_name="scale", duration(0.1), ease_function=easing.ease_out)
# Result: Button scales from normal size to 120% over 0.1 seconds, then stops

# Example 4: Fade transition
tween_until(sprite, start_value=255, end_value=0, property_name="alpha", duration(1.0), ease_function=easing.ease_in)
# Result: Sprite fades from opaque to transparent over 1 second
```

### When to Use Which?

| Scenario | Choose | Reason |
|----------|--------|--------|
| **Missile/projectile launch** | `ease` | Need smooth acceleration to cruise speed, then constant velocity |
| **UI element slide-in** | `tween_until` | Need precise positioning from off-screen to final location |
| **Enemy formation movement** | `ease` | Formation should smoothly reach marching speed and continue |
| **Health/progress bar updates** | `tween_until` | Need exact value changes with smooth visual transition |
| **Curved path following** | `ease` | Complex path requires smooth acceleration along the curve |
| **Button press feedback** | `tween_until` | Need precise scale/position changes for UI responsiveness |
| **Vehicle acceleration** | `ease` | Realistic acceleration to top speed, then constant motion |
| **Fade in/out effects** | `tween_until` | Precise alpha value control with smooth transitions |
| **Camera smooth following** | `ease` | Smooth acceleration when starting to follow target |
| **Menu animations** | `tween_until` | Precise positioning and scaling for UI elements |

### Combining Both Approaches

You can use both techniques together for complex animations:

```python
# Sequential combination: precise positioning followed by smooth movement
from actions import TweenUntil, MoveUntil, duration, ease, sequence

def create_guard_behavior(guard_sprite):
    # Step 1: Precise positioning
    position_setup = TweenUntil(start_value=0, end_value=100, property_name="center_x", condition=duration(0.5))
    
    # Step 2: Smooth patrol movement  
    patrol_move = MoveUntil((50, 0), condition=infinite)
    
    # Create sequence
    behavior_sequence = sequence(position_setup, patrol_move)
    behavior_sequence.apply(guard_sprite, tag="guard_behavior")
    
    # Add easing to the patrol movement after positioning
    # Note: This requires more complex timing - simpler to use separate actions
    ease(guard_sprite, patrol_move, duration=1.0)
```

### Advanced Easing Patterns

```python
from actions import ease, fade_until, infinite, move_until, rotate_until
from arcade import easing

# Multiple concurrent eased effects
move_action = move_until(sprite, velocity=(200, 100), condition=infinite)
rotate_action = rotate_until(sprite, angular_velocity=360, condition=infinite)
fade_action = fade_until(sprite, fade_velocity=-100, condition=infinite)

# Apply different easing curves to each effect
ease(sprite, move_action, duration=2.0, ease_function=easing.ease_in_out)
ease(sprite, rotate_action, duration=1.5, ease_function=easing.ease_in)
ease(sprite, fade_action, duration=3.0, ease_function=easing.ease_out)
```

## Usage Patterns

### Pattern 1: Individual Sprite Control
For player characters, single enemies, individual UI elements:

```python
import arcade
from actions import duration, move_until, rotate_until

# Create any arcade.Sprite
player = arcade.Sprite(":resources:images/player.png")

# Apply simple actions directly using helper functions
move_until(player, velocity=(100, 0), condition=duration(2.0))
rotate_until(player, angular_velocity=180, condition=duration(0.5))
```

### Pattern 2: Group Coordination
For enemy formations, bullet patterns, coordinated behaviors:

```python
# Create standard arcade.SpriteList
enemies = arcade.SpriteList()
for i in range(10):
    enemy = arcade.Sprite(":resources:images/enemy.png")
    enemies.append(enemy)

# Apply actions to entire group
move_until(enemies, velocity=(0, -50), condition=duration(3.0))

# All sprites in the list move together
```

### Pattern 3: Complex Sequential Behaviors
For multi-step animations and complex game scenarios:

```python
from actions import Action, DelayUntil, MoveUntil, RotateUntil, FadeUntil, duration, sequence, parallel

# Create complex behavior using direct classes
def create_enemy_attack_sequence(enemy_sprite):
    attack_sequence = sequence(
        DelayUntil(duration(1.0)),                               # Wait 1 second
        MoveUntil(velocity=(0, -100), condition=duration(2.0)),  # Move down
        parallel(                                                # Simultaneously:
            RotateUntil(angular_velocity=360, condition=duration(1.0)),  #   Spin
            FadeUntil(fade_velocity=-50, condition=duration(1.5))  #   Fade out
        ),
        MoveUntil(velocity=(200, 0), condition=duration(1.0))  # Move sideways
    )
    attack_sequence.apply(enemy_sprite, tag="attack_sequence")

# Apply to multiple enemies
for enemy in enemy_list:
    create_enemy_attack_sequence(enemy)
```

### Pattern 4: Formation Management
For complex game scenarios with formation positioning:

```python
from actions import (
    arrange_grid, arrange_circle, arrange_diamond, arrange_triangle, 
    arrange_hexagonal_grid, arrange_arc, arrange_concentric_rings, 
    arrange_cross, arrange_arrow
)
from functools import partial

# Define how each enemy sprite should be built
enemy_factory = partial(arcade.Sprite, ":resources:images/enemy.png")

# Classic grid formation
enemies = arrange_grid(
    rows=3,
    cols=5,
    start_x=200,
    start_y=400,
    spacing_x=80,
    spacing_y=60,
    sprite_factory=enemy_factory,
)

# Zero-allocation: arrange an existing list without creating new sprites
pooled = [arcade.Sprite(":resources:images/enemy.png") for _ in range(12)]
arrange_grid(sprites=pooled, rows=3, cols=4, start_x=200, start_y=300)

# Contract reminders
# - Provide exactly one of `sprites` or creation inputs (`count` / `sprite_factory`)
# - For grids, len(sprites) must equal rows * cols

# Triangle formation for attack patterns
attack_formation = arrange_triangle(
    count=10, apex_x=400, apex_y=500, row_spacing=50, lateral_spacing=60
)

# Hexagonal grid for defensive formations
defensive_grid = arrange_hexagonal_grid(
    rows=4, cols=6, start_x=100, start_y=400, spacing=50
)

# Arc formation for firing patterns
firing_arc = arrange_arc(
    count=8, center_x=400, center_y=300, radius=120, start_angle=45, end_angle=135
)

# Concentric rings for boss battle patterns
boss_pattern = arrange_concentric_rings(
    radii=[80, 140, 200], sprites_per_ring=[6, 12, 18], center_x=400, center_y=300
)

# Cross formation for power-ups or obstacles
power_up_cross = arrange_cross(
    count=9, center_x=400, center_y=300, arm_length=100, spacing=40
)

# Arrow formation for escort patterns
escort_arrow = arrange_arrow(
    count=7, tip_x=400, tip_y=500, rows=3, spacing_along=50, spacing_outward=40
)

# Apply simple movement to any formation
move_until(enemies, velocity=(0, -50), condition=duration(3.0), tag="formation_move")
```

### Pattern 5: Movement Patterns
For creating complex movement behaviors using pattern functions:

```python
from actions import (
    create_zigzag_pattern, create_wave_pattern, create_spiral_pattern,
    create_figure_eight_pattern, create_orbit_pattern, create_bounce_pattern,
    create_patrol_pattern, time_elapsed, sprite_count
)

# Enemy with zigzag attack pattern
zigzag_movement = create_zigzag_pattern(
    width=100, height=50, speed=150, segments=6
)
zigzag_movement.apply(enemy_sprite)

# Boss with smooth wave movement
wave_movement = create_wave_pattern(
    amplitude=75, frequency=2, length=600, speed=120
)
wave_movement.apply(boss_sprite)

# Enemy with repeating wave pattern (forward then backward)
from actions import repeat, sequence

forward_wave = create_wave_pattern(
    amplitude=15, frequency=1, length=50, speed=100, reverse=False
)
backward_wave = create_wave_pattern(
    amplitude=15, frequency=1, length=50, speed=100, reverse=True
)
repeating_wave = repeat(sequence(forward_wave, backward_wave))
repeating_wave.apply(enemy_sprite)

# Guard with patrol pattern
patrol_movement = create_patrol_pattern(
    start_pos=(100, 200), end_pos=(500, 200), speed=80
)
patrol_movement.apply(guard_sprite)
```

### Pattern 6: Path Following with Rotation
For smooth curved movement with automatic sprite rotation:

```python
from actions import duration, follow_path_until

# Basic path following without rotation
path_points = [(100, 100), (200, 150), (300, 100)]
follow_path_until(sprite, path_points, velocity=200, condition=duration(3.0))

# Path following with automatic rotation (sprite artwork points right)
follow_path_until(
    sprite, path_points, 
    velocity=200, 
    condition=duration(3.0),
    rotate_with_path=True,
)

# Path following with rotation offset for sprites pointing up
follow_path_until(
    sprite, path_points, 
    velocity=200, 
    condition=duration(3.0),
    rotate_with_path=True,
    rotation_offset=-90.0,  # Compensate for upward-pointing artwork
)

# Complex curved missile trajectory
missile_path = [(player.center_x, player.center_y),
                (target.center_x + 100, target.center_y + 50),  # Arc over target
                (target.center_x, target.center_y)]
follow_path_until(
    missile_sprite,
    missile_path, 
    velocity=300,
    condition=lambda: distance_to_target() < 20,  # Until close to target
    rotate_with_path=True,  # Missile points toward movement direction
)
```

### Pattern 7: Texture Cycling for Animation
For animating sprites by cycling through textures at specified frame rates:

```python
from actions import cycle_textures_until, infinite, duration

# Create a list of textures for animation
texture_list = []
for i in range(8):
    texture = arcade.load_texture(f"sprites/walk_frame_{i}.png")
    texture_list.append(texture)

# Simple infinite texture cycling
cycle_textures_until(
    player_sprite,
    textures=texture_list,
    frames_per_second=12.0,  # 12 frames per second animation
    condition=infinite
)

# Time-limited texture cycling (uses simulation time for consistent timing)
cycle_textures_until(
    power_up_sprite,
    textures=power_up_textures,
    frames_per_second=30.0,
    condition=duration(3.0),  # Animate for 3 seconds - uses simulation time
    direction=1,  # Forward animation
    tag="power_up_animation"
)

# Reverse texture cycling (for different animation directions)
cycle_textures_until(
    enemy_sprite,
    textures=enemy_walk_textures,
    frames_per_second=8.0,
    direction=-1,  # Backward cycling
    condition=lambda: enemy_sprite.center_x < 100  # Until reaching position
)

# Using with sequences for complex animations
from actions import sequence, DelayUntil

animation_sequence = sequence(
    # Phase 1: Spin up animation
    CycleTexturesUntil(
        textures=spin_up_textures,
        frames_per_second=24.0,
        direction=1,
        condition=duration(1.0)
    ),
    # Phase 2: Steady state animation
    CycleTexturesUntil(
        textures=steady_textures,
        frames_per_second=12.0,
        direction=1,
        condition=duration(5.0)
    ),
    # Phase 3: Spin down animation
    CycleTexturesUntil(
        textures=spin_down_textures,
        frames_per_second=24.0,
        direction=1,
        condition=duration(1.0)
    )
)
animation_sequence.apply(machinery_sprite, tag="machinery_startup")
```

**Key Features:**
- **Frame Rate Control**: Specify exactly how many texture changes per second
- **Direction Control**: Cycle forward (1) or backward (-1) through texture list
- **Condition-Based**: Stop cycling when any condition is met
- **Simulation Time Support**: `duration()` conditions use consistent timing independent of frame rate
- **Factor Scaling**: Use `set_factor()` to speed up/slow down both animation and duration timing
- **Automatic Wrapping**: Seamlessly loops through texture list
- **Works with Groups**: Apply same animation to entire sprite lists

**Duration and Timing:**
`CycleTexturesUntil` supports simulation time for consistent behavior:

```python
# Duration conditions use simulation time (frame-rate independent)
cycle_textures_until(
    sprite, 
    textures=animation_frames, 
    frames_per_second=24.0,
    condition=duration(3.0)  # Exactly 3 seconds, regardless of FPS
)

# Factor scaling affects both animation speed and duration
action = cycle_textures_until(sprite, textures=frames, condition=duration(2.0))
action.set_factor(2.0)  # 2x speed: animation plays faster AND completes in 1 second
action.set_factor(0.5)  # Half speed: animation plays slower AND takes 4 seconds
action.set_factor(0.0)  # Paused: both animation and duration timing stop
```

**Common Use Cases:**
- Character walk/run animations
- Power-up spinning effects
- Environmental animations (water, fire, etc.)
- UI element animations
- Machinery and rotating objects
- Particle-like effects

### Pattern 7.1: Visibility Blinking with Callbacks
For sprite blinking effects with collision detection management:

```python
from actions import blink_until, infinite, duration

# Basic blinking without callbacks
blink_until(
    invulnerable_player,
    seconds_until_change=0.25,  # Blink every 0.25 seconds
    condition=duration(3.0),    # Blink for 3 seconds total
    tag="invulnerability"
)

# Advanced: Collision detection management with callbacks
def enable_collisions(target):
    """Add target to collision detection when visible."""
    # For single sprite: target is the sprite
    # For SpriteList: target is the whole list - efficient!
    if hasattr(target, '__iter__'):  # SpriteList
        collision_sprites.extend(target)
    else:  # Single sprite
        if target not in collision_sprites:
            collision_sprites.append(target)

def disable_collisions(target):
    """Remove target from collision detection when invisible."""
    if hasattr(target, '__iter__'):  # SpriteList
        for sprite in target:
            if sprite in collision_sprites:
                collision_sprites.remove(sprite)
    else:  # Single sprite
        if target in collision_sprites:
            collision_sprites.remove(target)

# Individual sprite
blink_until(
    player_sprite,
    seconds_until_change=0.2,
    condition=infinite,
    on_blink_enter=enable_collisions,   # Called with player_sprite
    on_blink_exit=disable_collisions,   # Called with player_sprite
    tag="player_invulnerability"
)

# Formation blinking - callbacks called once per frame, not once per sprite!
blink_until(
    enemy_formation,  # SpriteList with 20 sprites
    seconds_until_change=0.25,
    condition=infinite,
    on_blink_enter=enable_collisions,   # Called once with enemy_formation
    on_blink_exit=disable_collisions,   # Called once with enemy_formation
    tag="formation_invulnerability"
)

# Power-up collection effect with status management
def on_powerup_visible(powerup):
    """Enable collection when power-up becomes visible."""
    powerup.can_be_collected = True
    powerup.alpha = 255  # Full opacity when visible

def on_powerup_hidden(powerup):
    """Disable collection when power-up becomes invisible."""
    powerup.can_be_collected = False
    
blink_until(
    collected_powerup,
    seconds_until_change=0.15,
    condition=duration(2.0),
    on_blink_enter=on_powerup_visible,
    on_blink_exit=on_powerup_hidden,
    tag="collection_effect"
)

# Enemy vulnerability periods
def make_vulnerable(enemy):
    """Enemy can take damage when visible."""
    enemy.vulnerable = True
    enemy.tint = arcade.color.WHITE

def make_invulnerable(enemy):
    """Enemy cannot take damage when invisible."""
    enemy.vulnerable = False

blink_until(
    boss_enemy,
    seconds_until_change=0.1,
    condition=lambda: boss_enemy.health <= 0,
    on_blink_enter=make_vulnerable,
    on_blink_exit=make_invulnerable,
    tag="boss_vulnerability"
)
```

**BlinkUntil Callback Features:**
- **Edge-triggered**: Callbacks fire only on visibility state changes, not continuously
- **Exception-safe**: Callback exceptions are caught and don't break blinking
- **Sprite list support**: Works with both individual sprites and sprite lists
- **Partial callbacks**: Can use only `on_blink_enter` or only `on_blink_exit`
- **Clone preservation**: Callback functions are preserved when cloning actions
- **Debug warnings**: Incorrect callback signatures show helpful one-time warnings when `ARCADEACTIONS_DEBUG=1`

**When to Use BlinkUntil Callbacks:**
- **Collision detection management**: Turn collision on/off based on visibility
- **Game state synchronization**: Update game state when sprites appear/disappear
- **Audio/visual effects**: Trigger sounds or particles on visibility changes
- **Performance optimization**: Enable/disable expensive operations based on visibility

**Callback Signatures:**
- `on_blink_enter(target)` - Called when target visibility changes to `True` (receives Sprite or SpriteList)
- `on_blink_exit(target)` - Called when target visibility changes to `False` (receives Sprite or SpriteList)

### When to Add Enter/Exit Callbacks

**Design Principle:** Only add `on_*_enter` and `on_*_exit` callbacks when the action has clear, binary state transitions that map to meaningful game events.

**Current implementations:**
- **MoveUntil** - `on_boundary_enter/exit` for boundary membership changes
- **BlinkUntil** - `on_blink_enter/exit` for visibility state changes

**Good candidates for future addition:**
- **FadeUntil** - `on_transparent_enter/exit` for alpha threshold crossings (0/255)
- **ScaleUntil** (with bounds) - `on_scale_min_enter/on_scale_max_enter` for scale limits
- **RotateUntil** (with angle limits) - `on_angle_min_enter/on_angle_max_enter` for angle constraints

**Avoid for:**
- **FollowPathUntil** - Continuous path following without clear state edges
- **DelayUntil** - Simple waiting without state transitions
- **CycleTexturesUntil** - Texture cycling is continuous, not binary

**Use composition instead for non-binary states:**
```python
# Instead of adding generic callbacks to every action
# Use conditions to detect state changes
def check_scale_threshold():
    if sprite.scale >= 2.0:
        return "max_scale_reached"
    return None

scale_until(sprite, scale_velocity=0.1, condition=check_scale_threshold, on_stop=handle_max_scale)
```

**Consistent API Pattern:** When adding callbacks, follow the established pattern:
- `on_[action]_enter(sprite, ...)` - Called when entering the state
- `on_[action]_exit(sprite, ...)` - Called when exiting the state
- Edge-triggered semantics (fire once per transition)
- Exception-safe execution

This pattern could be thoughtfully applied to other conditional actions where clear binary state transitions exist.

### Pattern 8: State Machines for Animation and Behavior

**Note:** ArcadeActions does not include a built-in StateMachine class. For state machine functionality, use the external [`python-statemachine`](https://github.com/fgmacedo/python-statemachine) library, which integrates seamlessly with ArcadeActions.

**Complete Example:** See `examples/pymunk_demo_platformer.py` for the canonical reference implementation demonstrating python-statemachine + ArcadeActions + PyMunk physics integration.

**Additional Reference:** The [amazon-warriors](https://github.com/bcorfman/amazon-warriors) project demonstrates advanced integration patterns for character animation states, AI behaviors, and game flow management.

### Best Practices: InputState with @dataclass

Use Python's `@dataclass` for clean input state containers (amazon-warriors pattern):

```python
from dataclasses import dataclass

@dataclass
class InputState:
    """Input state container (amazon-warriors pattern)."""
    left: bool = False
    right: bool = False
    up: bool = False
    down: bool = False
    shift: bool = False
    direction: int = 1  # 1 for right, -1 for left
    
    @property
    def moving(self) -> bool:
        return self.left or self.right
    
    @property
    def horizontal_input(self) -> int:
        """Returns -1 (left), 0 (none), or 1 (right)."""
        if self.left and not self.right:
            return -1
        elif self.right and not self.left:
            return 1
        return 0
    
    @property
    def vertical_input(self) -> int:
        """Returns -1 (down), 0 (none), or 1 (up)."""
        if self.up and not self.down:
            return 1
        elif self.down and not self.up:
            return -1
        return 0

# In your View (Arcade Window):
def on_key_press(self, key, modifiers):
    """DUMB View: just update state and trigger events."""
    if key in (arcade.key.LEFT, arcade.key.A):
        self.input_state.left = True
        self.input_state.direction = -1
    elif key in (arcade.key.RIGHT, arcade.key.D):
        self.input_state.right = True
        self.input_state.direction = 1
    elif key in (arcade.key.UP, arcade.key.W):
        self.input_state.up = True
        self.player.animation_state.jump_action()
    # Trigger movement transitions after updating input
    self.player.animation_state.movement()
```

**Key principles:**
- **@dataclass**: Eliminates boilerplate `__init__` while keeping type hints clear
- **Properties**: Derive complex state from simple fields (no manual methods)
- **No state flags**: Just data fields and computed properties
- **View is DUMB**: Only routes input, no physics or game logic

### State Machine + Physics Integration

For games combining character animation, physics simulation, and player input:

```python
from statemachine import State, StateMachine
from actions import Action, cycle_textures_until, infinite

class PlayerAnimationState(StateMachine):
    """SMART state machine: handles all logic."""
    
    idle = State(initial=True)
    walk = State()
    jump = State()
    fall = State()
    
    # Declarative transitions
    movement = (
        idle.to(walk, cond="moving and on_ground")
        | walk.to(idle, cond="not moving and on_ground")
    )
    
    jump_action = (
        idle.to(jump, cond="on_ground")
        | walk.to(jump, cond="on_ground")
    )
    
    physics_update = (
        jump.to(fall, cond="falling")
        | fall.to(idle, cond="on_ground and not moving")
        | fall.to(walk, cond="on_ground and moving")
    )
    
    def __init__(self, player, input_state, physics_engine):
        self.player = player
        self.input = input_state
        self.physics = physics_engine
        super().__init__()
        self.allow_event_without_transition = True
    
    # Guard conditions as properties
    @property
    def moving(self) -> bool:
        return self.input.moving
    
    @property
    def on_ground(self) -> bool:
        try:
            return self.physics.is_on_ground(self.player)
        except (KeyError, AttributeError):
            return False
    
    @property
    def falling(self) -> bool:
        return self.player.last_dy < -0.1
    
    # State enter callbacks: animation + physics
    def on_enter_walk(self):
        textures = [pair[0 if self.input.direction == 1 else 1] for pair in self.player.walk_textures]
        cycle_textures_until(self.player, textures=textures, frames_per_second=10.0, tag="animation")
    
    def on_enter_jump(self):
        self.player.texture = self.player.jump_texture_pair[0 if self.input.direction == 1 else 1]
        # Physics logic lives with state transitions!
        self.physics.apply_impulse(self.player, (0, 1800))
    
    def on_exit_walk(self):
        # Stop animation when leaving walk state
        Action.stop_actions_for_target(self.player, tag="animation")
    
    def apply_physics_forces(self):
        """Centralized physics force application (called from update loop)."""
        horizontal = self.input.horizontal_input
        
        if horizontal != 0:
            force = horizontal * 8000 if self.on_ground else horizontal * 900
            self.physics.apply_force(self.player, (force, 0))
            self.physics.set_friction(self.player, 0)
        else:
            self.physics.set_friction(self.player, 1.0)

# In your PlayerSprite:
class PlayerSprite(arcade.Sprite):
    def __init__(self, input_state, physics_engine):
        super().__init__()
        # ... load textures ...
        self.last_dy = 0.0
        self.animation_state = PlayerAnimationState(self, input_state, physics_engine)
    
    def pymunk_moved(self, physics_engine, dx, dy, d_angle):
        """Physics callback: track velocity and trigger state transitions."""
        self.last_dy = dy
        self.animation_state.movement()
        if not self.animation_state.current_state == self.animation_state.climb:
            self.animation_state.physics_update()

# In your game window:
def on_update(self, delta_time):
    # State machine applies all physics forces
    self.player.animation_state.apply_physics_forces()
    
    # Actions update + automatic kinematic sync
    Action.update_all(delta_time, physics_engine=self.physics_engine)
    self.physics_engine.step()
```

**Architecture principles:**
- **DUMB View (Window)**: Routes input to state machine, no logic
- **SMART State Machine**: Guards, transitions, physics forces, animation
- **Zero state flags**: State machine current_state is single source of truth
- **Dependency injection**: Pass InputState and physics_engine to state machine
- **Centralized physics**: All force application in `apply_physics_forces()` method
- **State-driven animation**: Use `cycle_textures_until` in enter callbacks, stop in exit callbacks

**Integration Pattern:**
- **python-statemachine**: Manages high-level game states and transitions
- **ArcadeActions**: Handles sprite animations, movements, and effects within each state
- **PyMunk Physics**: Handles forces, collisions, and realistic movement
- **Separation of concerns**: State machine controls which actions/forces are active; ArcadeActions and physics execute them

**When to use python-statemachine + physics:**
- Character animation states with physics (idle/walk/jump/fall/climb)
- Complex platformer mechanics (ladders, jumping, climbing)
- Physics-driven AI behaviors (patrol/chase/attack/flee with forces)
- Games requiring realistic physics simulation with state-based controls

**When to use ArcadeActions alone:**
- Use `sequence()` for: fixed multi-step animations, cutscenes, tutorials
- Use `parallel()` for: simultaneous effects, complex animations
- Use individual actions for: simple single-purpose behaviors
- Non-physics games: top-down shooters, puzzle games, simple arcade games

**Complete Example:** See `examples/pymunk_demo_platformer.py` for a full implementation showing all these patterns working together.

### Pattern 9: Boundary Interactions
For arcade-style movement with boundary detection:

```python
from actions import duration, infinite, move_until

# Individual sprite bouncing with enter/exit events
def on_bounce_enter(sprite, axis, side):
    print(f"Sprite hit {side} {axis} boundary")

def on_bounce_exit(sprite, axis, side):
    print(f"Sprite left {side} {axis} boundary")

bounds = (0, 0, 800, 600)  # left, bottom, right, top
move_until(
    sprite,
    velocity=(100, 50),
    condition=infinite,  
    bounds=bounds,
    boundary_behavior="bounce",
    on_boundary_enter=on_bounce_enter,
    on_boundary_exit=on_bounce_exit,
)

# Group bouncing (like Space Invaders) with edge-triggered callbacks
def formation_bounce_enter(sprite, axis, side):
    if axis == 'x':
        # Move entire formation down when hitting side boundaries
        move_until(enemies, (0, -30), duration(0.2))

move_until(
    enemies,
    velocity=(100, 0),
    condition=infinite,  
    bounds=bounds,
    boundary_behavior="bounce",
    on_boundary_enter=formation_bounce_enter,
    tag="formation_bounce"
)
```

### Boundary Callback API
The boundary system uses edge-triggered callbacks that fire when sprites enter or exit boundary regions:

#### Callback Signatures
- `on_boundary_enter(sprite, axis, side)` - Called when sprite first touches a boundary
- `on_boundary_exit(sprite, axis, side)` - Called when sprite moves away from a boundary

#### Parameters
- `sprite` - The sprite that triggered the boundary event
- `axis` - Either `"x"` (horizontal) or `"y"` (vertical) 
- `side` - Boundary side: `"left"`, `"right"`, `"top"`, or `"bottom"`

#### Edge-Triggered Behavior
Unlike the old `on_boundary` callback, these new callbacks are edge-triggered:
- `on_boundary_enter` fires only **once** when a sprite first contacts a boundary
- `on_boundary_exit` fires only **once** when a sprite moves away from a boundary
- This prevents callback spam and enables clean state management
- **Debug warnings**: Incorrect callback signatures show helpful one-time warnings when `ARCADEACTIONS_DEBUG=1`

#### Example: Speed Boost System
```python
class PlayerShip:
    def __init__(self):
        self.speed_factor = 1
        
    def on_right_boundary_enter(self, sprite, axis, side):
        if axis == "x" and side == "right":
            self.speed_factor = 2  # Double speed when pushing right
            self.update_tunnel_velocity()
            
    def on_right_boundary_exit(self, sprite, axis, side):
        if axis == "x" and side == "right":
            self.speed_factor = 1  # Normal speed when away from right edge
            self.update_tunnel_velocity()

# Apply boundary callbacks
move_until(
    player_ship,
    velocity_provider=player_ship.get_velocity,
    condition=infinite,
    bounds=(LEFT_BOUND, 0, RIGHT_BOUND, HEIGHT),
    boundary_behavior="limit",
    on_boundary_enter=player_ship.on_right_boundary_enter,
    on_boundary_exit=player_ship.on_right_boundary_exit,
)
```

## Shader and Particle Effects

### Pattern 10: Full-Screen Shader Effects with GlowUntil

`GlowUntil` provides a declarative wrapper around Arcade's Shadertoy system, simplifying full-screen shader effects:

```python
from arcade.experimental import Shadertoy
from actions import GlowUntil, duration

# Create shader factory
def make_glow_shader(size):
    return Shadertoy.create_from_file(size, "glow_shader.glsl")

# Apply glow effect for 5 seconds
GlowUntil(
    shadertoy_factory=make_glow_shader,
    condition=duration(5.0),
    on_stop=lambda: print("Glow effect ended")
).apply(sprite, tag="glow")

# In your on_draw():
# GlowUntil automatically calls shader.render()
```

**With Camera Offset and Uniforms:**

```python
def get_uniforms(shader, target):
    # Return dict of uniforms to set on the shader
    return {
        "lightPosition": (player.center_x, player.center_y),  # World coords
        "lightRadius": 200.0,
    }

def get_camera_pos():
    return (camera.position[0], camera.position[1])

GlowUntil(
    shadertoy_factory=make_glow_shader,
    condition=duration(3.0),
    uniforms_provider=get_uniforms,
    get_camera_bottom_left=get_camera_pos,  # Converts world → screen coords
    auto_resize=True,  # Handles window resize
).apply(sprite, tag="dynamic_glow")
```

**Helper Function:**

```python
from actions import glow_until

# Same as above, with automatic application
glow_until(
    sprite,
    shadertoy_factory=make_glow_shader,
    condition=duration(3.0),
    tag="quick_glow"
)
```

### Pattern 11: Per-Sprite Particle Emitters with EmitParticlesUntil

`EmitParticlesUntil` manages particle emitters that follow sprites with customizable anchors and rotation:

```python
from arcade import make_burst_emitter
from actions import EmitParticlesUntil, duration

# Factory receives the sprite and returns an emitter
def create_thrust_emitter(sprite):
    return make_burst_emitter(
        center_xy=(0, 0),  # Will be updated to sprite position
        filenames_and_textures=[":resources:images/pinball/pool_cue_ball.png"],
        particle_count=50,
        particle_speed=2.0,
        particle_lifetime_max=1.0,
    )

# Emit particles from sprite center for 2 seconds
EmitParticlesUntil(
    emitter_factory=create_thrust_emitter,
    condition=duration(2.0),
    anchor="center",  # Or (dx, dy) offset
    follow_rotation=True,  # Emitter.angle = sprite.angle
    destroy_on_stop=True,  # Clean up emitter when done
).apply(rocket, tag="thrust")
```

**For SpriteList (one emitter per sprite):**

```python
# When applied to SpriteList, creates one emitter per sprite
EmitParticlesUntil(
    emitter_factory=create_explosion_emitter,
    condition=duration(1.5),
    anchor="center",
).apply(enemy_ships, tag="explosions")

# Each sprite gets its own emitter that follows it
```

**Custom Anchor Offset:**

```python
# Emit from back of ship (offset from center)
EmitParticlesUntil(
    emitter_factory=create_thrust_emitter,
    condition=duration(2.0),
    anchor=(-20, 0),  # 20 pixels left of center
    follow_rotation=True,
).apply(rocket, tag="rear_thrust")
```

**Helper Function:**

```python
from actions import emit_particles_until

# Same as above, with automatic application
emit_particles_until(
    rocket,
    emitter_factory=create_thrust_emitter,
    condition=duration(2.0),
    anchor="center",
    follow_rotation=True,
    tag="quick_particles"
)
```

## Easing Effects

### Overview
The `ease()` helper function provides smooth acceleration and deceleration effects by modulating the intensity of any conditional action using easing curves. This creates natural-feeling animations that start slow, speed up, and slow down again.

### Basic Easing Usage

```python
from actions import duration, ease, move_until
from arcade import easing

# Wrap any conditional action with easing
move = move_until(sprite, velocity=(200, 0), condition=duration(3.0))
ease(sprite, move, duration=2.0, ease_function=easing.ease_in_out)

# The sprite will smoothly accelerate to full speed, then decelerate
```

### Easing Functions
Use Arcade's built-in easing functions for different effects:

```python
from arcade import easing
from actions import duration, ease, move_until

move = move_until(sprite, velocity=(200, 0), condition=duration(3.0))

# Slow start, fast finish
ease(sprite, move, duration=2.0, ease_function=easing.ease_in)

# Fast start, slow finish  
ease(sprite, move, duration=2.0, ease_function=easing.ease_out)

# Slow start, fast middle, slow finish (default)
ease(sprite, move, duration=2.0, ease_function=easing.ease_in_out)
```

### Easing with Path Following and Rotation
Create smooth curved movements with automatic sprite rotation:

```python
# Complex curved missile trajectory with easing
control_points = [(player.center_x, player.center_y),
                  (target.center_x + 100, target.center_y + 50),  # Arc over target
                  (target.center_x, target.center_y)]

missile_path = follow_path_until(
    missile_sprite,
    control_points, 
    velocity=300,
    condition=lambda: distance_to_target() < 20,
    rotate_with_path=True,  # Missile points toward movement direction
    rotation_offset=-90     # Compensate for upward-pointing artwork
)

# Add smooth acceleration/deceleration to the path following
ease(missile_sprite, missile_path, duration=1.5, ease_function=easing.ease_in_out)

# Missile will smoothly accelerate along the curved path while rotating to face direction
```

### Multiple Concurrent Eased Effects
Apply different easing to multiple effects simultaneously:

```python
from actions import ease, move_until, rotate_until, fade_until

# Create multiple effects with different easing curves
move = move_until(sprite, velocity=(200, 100), condition=infinite)
rotate = rotate_until(sprite, angular_velocity=360, condition=infinite)  # Full rotation
fade = fade_until(sprite, fade_velocity=-200, condition=infinite)     # Fade to transparent

# Apply different easing to each effect
ease(sprite, move, duration=2.0, ease_function=easing.ease_in_out)
ease(sprite, rotate, duration=1.5, ease_function=easing.ease_in)
ease(sprite, fade, duration=3.0, ease_function=easing.ease_out)

# Sprite moves, rotates, and fades with different easing curves
```

### Custom Easing Functions
Create your own easing curves:

```python
def bounce_ease(t):
    """Custom bouncing ease function."""
    if t < 0.5:
        return 2 * t * t
    else:
        return -1 + (4 - 2 * t) * t

move = move_until(sprite, velocity=(200, 0), condition=duration(3.0))
ease(sprite, move, duration=2.0, ease_function=bounce_ease)
```

## Action Management

### Tags and Organization
Use tags to organize and control different types of actions:

```python
# Apply different tagged actions
move_until(sprite, velocity=(100, 0), condition=duration(2.0), tag="movement")
fade_until(sprite, velocity=-10, condition=duration(1.5), tag="effects")
rotate_until(sprite, velocity=180, condition=duration(1.0), tag="combat")

# Stop specific tagged actions
Action.stop_actions_for_target(sprite, "effects")  # Stop just effects
Action.stop_actions_for_target(sprite)  # Stop all actions on sprite
```

### Global Control
The global Action system provides centralized management:

```python
# Update all actions globally
Action.update_all(delta_time)

# Global action queries
active_count = len(Action._active_actions)
movement_actions = Action.get_actions_for_target(sprite, "movement")

# Global cleanup
Action.stop_all()
```

### Configurable Debug Logging

ArcadeActions provides a powerful, fine-grained debug logging system with levels and per-Action filtering for focused, useful output without noise.

#### Debug Levels

- **Level 0**: No debug output (default)
- **Level 1**: Summary counts only when they change (minimal overhead)
  - Shows total active actions and per-class counts
  - Example: `[AA L1 summary] Total=5, MoveUntil=3, RotateUntil=2`
- **Level 2**: Lifecycle events (creation/removal) for observed actions
  - Filtered by action class unless `include_all=True`
  - Example: `[AA L2 MoveUntil] created target=Sprite tag='movement'`
- **Level 3+**: Verbose per-frame details for observed actions
  - Fine-grained internal state for debugging complex behaviors
  - Heavily filtered to prevent log spam

#### Programmatic API (Recommended)

```python
from actions import set_debug_options, observe_actions, clear_observed_actions

# Focused debugging: Level 2, only MoveUntil and CallbackUntil
set_debug_options(level=2, include=["MoveUntil", "CallbackUntil"])

# Or using class types
from actions import MoveUntil, CallbackUntil
set_debug_options(level=2, include=[MoveUntil, CallbackUntil])

# Incrementally add observed actions
observe_actions(MoveUntil)
observe_actions("CallbackUntil", "RotateUntil")

# Clear filters
clear_observed_actions()

# All actions at level 1 (summary only)
set_debug_options(level=1, include_all=True)

# Fine-grained tracing for MoveUntil only
set_debug_options(level=3, include=["MoveUntil"])

# Check current settings
from actions import get_debug_options
print(get_debug_options())
# {'level': 2, 'include_all': False, 'include': ['MoveUntil']}
```

#### Environment Variables (Optional)

```bash
# Set debug level (0-3+)
ARCADEACTIONS_DEBUG=2 uv run python your_app.py

# Observe all actions
ARCADEACTIONS_DEBUG=2 ARCADEACTIONS_DEBUG_ALL=1 uv run python your_app.py

# Observe specific action classes (comma-separated)
ARCADEACTIONS_DEBUG=2 ARCADEACTIONS_DEBUG_INCLUDE=MoveUntil,CallbackUntil uv run python your_app.py

# Boolean values also work (maps to level 1)
ARCADEACTIONS_DEBUG=true uv run python your_app.py
```

#### Usage Examples

**Example 1: Monitor all action activity (Level 1)**
```python
from actions import set_debug_options

# Minimal overhead - only logs when counts change
set_debug_options(level=1, include_all=True)
```

Output:
```
[AA L1 summary] Total=1, MoveUntil=1
[AA L1 summary] Total=3, MoveUntil=2, RotateUntil=1
```

**Example 2: Track specific action lifecycle (Level 2)**
```python
from actions import set_debug_options

# See when MoveUntil actions are created/removed
set_debug_options(level=2, include=["MoveUntil"])
```

Output:
```
[AA L1 summary] Total=1, MoveUntil=1
[AA L2 MoveUntil] created target=Sprite tag='movement'
[AA L2 MoveUntil] start() target=<Sprite> tag=movement
[AA L1 summary] Total=0
[AA L2 MoveUntil] removed target=Sprite tag='movement'
```

**Example 3: Deep debugging with verbose output (Level 3)**
```python
from actions import set_debug_options

# Internal state logging for MoveUntil only
set_debug_options(level=3, include=["MoveUntil"])
```

Output includes per-frame velocity updates, boundary checks, and internal state changes.

**Example 4: Incremental observation during development**
```python
from actions import observe_actions, set_debug_options

# Start with level 2
set_debug_options(level=2)

# Add actions as you need to observe them
observe_actions("MoveUntil")  # Track movement
# ... later in development ...
observe_actions("CallbackUntil")  # Also track callbacks
```

#### Callback Debug Warnings

At debug level 1 or higher, the framework provides helpful one-time warnings for common callback mistakes:

**Common callback signature errors:**
- `on_blink_enter(target)` and `on_blink_exit(target)` - require 1 parameter (receives Sprite or SpriteList)
- `on_boundary_enter(sprite, axis, side)` and `on_boundary_exit(sprite, axis, side)` - require 3 parameters  
- `on_stop(data)` or `on_stop()` - parameter count depends on condition return value

**Warning features:**
- **One-time only**: Each bad callback function warns once per process, preventing spam
- **Debug mode only**: No warnings when level is 0
- **Exception-safe**: Bad callbacks don't crash the game, they just fail silently in production
- **Helpful details**: Warning includes function name and specific TypeError details

**Example warning:**
```
RuntimeWarning: Callback 'bad_callback' failed with TypeError - 
check its parameter list matches the Action callback contract. 
Details: bad_callback() takes 0 positional arguments but 1 was given
```

#### Best Practices

1. **Start broad, then narrow**: Begin with level 1 + include_all to see overall activity, then focus on specific actions
2. **Use level 2 for most debugging**: Provides clear lifecycle events without overwhelming detail
3. **Reserve level 3+ for deep dives**: Only when you need internal state for specific problem actions
4. **Filter early**: Use `include` to focus on relevant actions - prevents noise and improves performance
5. **Disable in production**: Keep level at 0 in deployed games for best performance

## Complete Game Example

```python
import arcade
from actions import Action, DelayUntil, MoveUntil, arrange_grid, duration, sequence

class SpaceInvadersGame(arcade.Window):
    def __init__(self):
        super().__init__(800, 600, "Space Invaders")
        
        # Create enemy formation
        enemies = arcade.SpriteList()
        for row in range(5):
            for col in range(10):
                enemy = arcade.Sprite(":resources:images/enemy.png")
                enemy.center_x = 100 + col * 60
                enemy.center_y = 500 - row * 40
                enemies.append(enemy)
        
        # Store enemies for management
        self.enemies = enemies
        
        # Set up formation movement pattern
        self._setup_formation_movement()
    
    def _setup_formation_movement(self):
        # Create complex sequence using direct classes
        initial_sequence = sequence(
            DelayUntil(duration(2.0)),           # Wait 2 seconds
            MoveUntil(velocity=(50, 0), condition=duration(4.0))    # Move right
        )
        initial_sequence.apply(self.enemies, tag="initial_movement")
        
        # Set up boundary bouncing using new edge-triggered callbacks
        def on_formation_bounce_enter(sprite, axis, side):
            # Move formation down and reverse direction when hitting side boundaries
            if axis == 'x':
                move_until(self.enemies, velocity=(0, -30), condition=duration(0.3), tag="drop")
        
        bounds = (50, 0, 750, 600)  # left, bottom, right, top
        move_until(
            self.enemies,
            velocity=(50, 0), 
            condition=infinite,
            bounds=bounds,
            boundary_behavior="bounce",
            on_boundary_enter=on_formation_bounce_enter,
        )
    
    def on_update(self, delta_time):
        # Single global update handles all actions
        Action.update_all(delta_time)
```

## Best Practices

### 1. Choose the Right Pattern for the Use Case
```python
# ✅ Good: Helper functions for simple, immediate actions
move_until(sprite, velocity=(100, 0), condition=duration(2.0))

# ✅ Good: Direct classes + sequence() for complex behaviors
complex_behavior = sequence(
    DelayUntil(duration(1.0)),
    MoveUntil(velocity=(100, 0), condition=duration(2.0)),
    RotateUntil(angular_velocity=180, condition=duration(1.0))
)
complex_behavior.apply(sprite)

# ❌ Avoid: Mixing helper functions with operators
# (delay_until(sprite, duration(1.0)) + move_until(sprite, (100, 0), duration(2.0)))
```

### 2. Prefer Conditions Over Durations
```python
# Good: Condition-based
move_until(sprite, velocity=(100, 0), condition=lambda: sprite.center_x > 700)

# Avoid: Duration-based thinking
# move_for_time = MoveBy((500, 0), 5.0)  # Old paradigm
```

### 3. Use Formation Functions for Positioning
```python
# Good: Formation positioning
from actions import arrange_grid
arrange_grid(enemies, rows=3, cols=5)

# Avoid: Manual sprite positioning
# Manual calculation of sprite positions
```

### 4. Tag Your Actions
```python
# Good: Organized with tags
move_until(sprite, velocity=(100, 0), condition=duration(2.0), tag="movement")
fade_until(sprite, velocity=-10, condition=duration(1.5), tag="effects")

# Stop specific systems
Action.stop_actions_for_target(sprite, tag="effects")
```

### 5. Choose the Right Animation Approach
```python
# Good: Use Easing for continuous actions
move_action = move_until(sprite, velocity=(200, 0), condition=infinite)
ease(sprite, move_action, duration=1.5)

# Good: Use TweenUntil for precise property changes
tween_until(sprite, start_value=0, end_value=100, property_name="center_x", condition=duration(1.0))

# Avoid: Using the wrong approach for the use case
# Don't use TweenUntil for complex path following
# Don't use Easing for simple A-to-B property changes
```

## Common Patterns Summary

| Use Case | Pattern | Example |
|----------|---------|---------|
| Simple sprite actions | Helper functions | `move_until(sprite, velociy=(5, 0), condition=cond)` |
| Sprite group actions | Helper functions on SpriteList | `move_until(sprite_list, velocity=(5, 0), condition=cond)` |
| Complex sequences | Direct classes + `sequence()` | `sequence(DelayUntil(...), MoveUntil(...))` |
| Parallel behaviors | Direct classes + `parallel()` | `parallel(MoveUntil(...), FadeUntil(...))` |
| State machine integration | `python-statemachine` library | See [amazon-warriors](https://github.com/bcorfman/amazon-warriors) example |
| Formation positioning | Formation functions | `arrange_grid(enemies, rows=3, cols=5)` |
| Triangle formations | `arrange_triangle` | `arrange_triangle(count=10, apex_x=400, apex_y=500)` |
| Hexagonal grids | `arrange_hexagonal_grid` | `arrange_hexagonal_grid(rows=4, cols=6)` |
| Arc formations | `arrange_arc` | `arrange_arc(count=8, center_x=400, radius=120, start_angle=0, end_angle=180)` |
| Concentric patterns | `arrange_concentric_rings` | `arrange_concentric_rings(radii=[50, 100], sprites_per_ring=[6, 12])` |
| Cross patterns | `arrange_cross` | `arrange_cross(count=9, center_x=400, arm_length=100)` |
| Arrow formations | `arrange_arrow` | `arrange_arrow(count=7, tip_x=400, rows=3)` |
| Movement patterns | Pattern functions | `create_zigzag_pattern(100, 50, 150)` |
| Path following | `follow_path_until` helper | `follow_path_until(sprite, points, velocity=200, condition=cond)` |
| Texture animation | `cycle_textures_until` helper | `cycle_textures_until(sprite, textures=tex_list, frames_per_second=12)` |
| Visibility blinking | `blink_until` helper | `blink_until(sprite, seconds_until_change=0.25, condition=cond)` |
| Visibility callbacks | `blink_until` with callbacks | `blink_until(sprite, ..., on_blink_enter=enable_fn, on_blink_exit=disable_fn)` |
| Periodic callbacks | `callback_until` helper | `callback_until(sprite, callback=update_fn, condition=cond, seconds_between_calls=0.1)` |
| Shader/particle effects | `callback_until` for temporal control | `callback_until(sprite, lambda: emitter.update(), condition=cond)` |
| Boundary detection | `move_until` with bounds | `move_until(sprite, velocity=vel, condition=cond, bounds=b)` |
| Delayed execution | Direct classes in sequences | `sequence(DelayUntil(duration(1.0)), action)` |
| Smooth acceleration | `ease` helper | `ease(sprite, action, duration=2.0)` |
| Property animation | `tween_until` helper | `tween_until(sprite, start_val=start, end_val=end, "prop", duration(1.0))` |

The ArcadeActions framework provides a clean, declarative way to create complex game behaviors while leveraging Arcade's native sprite system!

## Optional Physics Integration (Arcade 3.x + PyMunk)

ArcadeActions can optionally route movement and rotation through `arcade.PymunkPhysicsEngine` when you provide an engine to the global update. This keeps the public API unchanged and preserves current behaviour when no engine is supplied.

### Automatic Kinematic Sync

**NEW:** When you pass `physics_engine` to `Action.update_all()`, ArcadeActions automatically syncs Arcade velocities (`change_x`/`change_y`) to Pymunk for all kinematic bodies. This eliminates manual `set_velocity()` boilerplate.

```python
def on_update(self, delta_time):
    # Actions update sprites (automatic kinematic sync when engine provided)
    Action.update_all(delta_time, physics_engine=self.physics_engine)
    
    # Physics engine advances simulation (explicit control)
    self.physics_engine.step()
```

**Why `step()` stays explicit:**
- Matches Arcade's standard API patterns
- Gives you explicit control over simulation timing
- Clear separation: actions update behaviors, physics steps simulation
- Enables advanced patterns (sub-stepping, conditional stepping, etc.)

### Key Integration Points

- Velocity semantics remain Arcade-native: pixels per frame at 60 FPS (no conversion).
- Without an engine: actions set `sprite.change_x/change_y/change_angle` directly (unchanged).
- With a `PymunkPhysicsEngine`:
  - `MoveUntil` routes velocity via `engine.set_velocity(sprite, (dx, dy))`
  - `RotateUntil` routes via `engine.set_angular_velocity(sprite, omega)`
  - **Kinematic bodies**: Automatically synced after all actions update (eliminates manual loops)
  - `FollowPathUntil` with `use_physics=True` uses steering impulses to follow paths naturally within physics simulation
- Other Arcade physics engines like `PhysicsEngineSimple/Platformer` already operate on `change_x/change_y`; you can continue using them as-is, with or without passing an engine.

### Example: Kinematic Moving Platforms

```python
import arcade
from actions import Action, move_until, infinite

# Set up physics
physics = arcade.PymunkPhysicsEngine(damping=1.0, gravity=(0, -1500))

# Load platforms from tilemap
tile_map = arcade.load_tilemap(":resources:/tiled_maps/pymunk_test_map.json", 0.5)
moving_platforms = tile_map.sprite_lists["Moving Platforms"]

# Add platforms as kinematic (user-controlled velocity)
physics.add_sprite_list(moving_platforms, body_type=arcade.PymunkPhysicsEngine.KINEMATIC)

# Apply MoveUntil with bounce to each platform
for sprite in moving_platforms:
    velocity = (sprite.change_x, sprite.change_y)  # From tilemap
    bounds = (
        sprite.boundary_left or float('-inf'),
        sprite.boundary_bottom or float('-inf'),
        sprite.boundary_right or float('inf'),
        sprite.boundary_top or float('inf'),
    )
    move_until(sprite, velocity=velocity, condition=infinite, boundary_behavior="bounce", bounds=bounds)

def on_update(delta_time):
    # MoveUntil updates change_x/change_y with bounce logic
    # Action.update_all automatically syncs to Pymunk kinematic velocities
    Action.update_all(delta_time, physics_engine=physics)
    physics.step()
```

**No manual velocity sync needed!** The kinematic sync happens automatically inside `Action.update_all()`.

### Example: Player with Physics Forces

```python
import arcade
from actions import Action, MoveUntil, infinite

window = arcade.Window(800, 600, "Physics Example")
player = arcade.Sprite(":resources:images/animated_characters/female_adventurer/femaleAdventurer_idle.png")

# Set up Pymunk physics engine
physics = arcade.PymunkPhysicsEngine(damping=1.0, gravity=(0, -200))
physics.add_sprite(player, mass=1.0, moment=arcade.PymunkPhysicsEngine.MOMENT_INF)

# Apply ArcadeActions movement (pixels per frame)
MoveUntil((5, 0), infinite).apply(player)

def on_update(delta_time):
    # Actions update, physics advances
    Action.update_all(delta_time, physics_engine=physics)
    physics.step()
```

### Example: Physics-Based Path Following

```python
import arcade
from actions import Action, FollowPathUntil, infinite

window = arcade.Window(800, 600, "Physics Path Following")
enemy = arcade.Sprite(":resources:images/enemies/slimeBlue.png")

# Set up Pymunk physics engine
physics = arcade.PymunkPhysicsEngine(damping=0.5, gravity=(0, 0))
physics.add_sprite(enemy, mass=2.0, moment=arcade.PymunkPhysicsEngine.MOMENT_INF)

# Physics-based path following with steering
path_points = [(100, 100), (300, 200), (500, 100), (300, 50)]
FollowPathUntil(
    control_points=path_points,
    velocity=150,  # Desired speed along path
    condition=infinite,
    use_physics=True,  # Enable physics steering
    steering_gain=5.0,  # Tunable responsiveness
    rotate_with_path=True,  # Rotate to face movement direction
).apply(enemy)

def on_update(delta_time):
    Action.update_all(delta_time, physics_engine=physics)
    physics.step()
```

### Notes on Physics Integration

- Boundary-limit logic within actions may clamp positions/velocities directly to keep behaviour simple and deterministic.
- Physics-based path following uses steering impulses, allowing natural interaction with other physics forces and collisions.
- The `steering_gain` parameter controls how aggressively the sprite steers toward the path (higher = more responsive, lower = smoother but may lag).
- Kinematic sync happens automatically for all sprites in the physics engine - no manual loops needed.
- If you don't pass a `physics_engine`, ArcadeActions behaves exactly as before.

## Runtime-checking-free patterns

Key conventions:

4. **Lint gate.**  `ruff` blocks any new `isinstance`, `hasattr`, or `getattr` usage during CI.

Stick to these patterns and you'll remain compliant with the project's "zero tolerance" design rule. 

### MoveUntil with Collision Detection and Data Passing

You can use MoveUntil for much more than just position checks. The condition function can return any data when a stop condition is met, and this data will be passed to the callback for efficient, zero-duplication event handling. This is especially powerful for collision detection:

```python
# Example: Move a bullet until it collides with an enemy or shield, or leaves the screen

def bullet_collision_check():
    enemy_hits = arcade.check_for_collision_with_list(bullet, enemy_list)
    shield_hits = arcade.check_for_collision_with_list(bullet, shield_list)
    off_screen = bullet.bottom > WINDOW_HEIGHT

    if enemy_hits or shield_hits or off_screen:
        return {
            "enemy_hits": enemy_hits,
            "shield_hits": shield_hits,
            "off_screen": off_screen
        }
    return None  # Continue moving

# The callback receives the collision data from the condition function

def handle_bullet_collision(collision_data):
    bullet.remove_from_sprite_lists()
    for enemy in collision_data["enemy_hits"]:
        enemy.remove_from_sprite_lists()
    for shield in collision_data["shield_hits"]:
        shield.remove_from_sprite_lists()
    if collision_data["off_screen"]:
        print("Bullet left the screen!")

move_until(bullet, velocity=(0, BULLET_SPEED), condition=bullet_collision_check, on_stop=handle_bullet_collision)
```

## Per-Axis Motion

ArcadeActions provides axis-specific movement actions that enable safe composition of orthogonal motion patterns. This is particularly useful for creating complex movement behaviors where different axes need different boundary behaviors or velocities.

### Axis-Specific Actions

**MoveXUntil** and **MoveYUntil** are specialized versions of MoveUntil that only affect their respective axes:

- **MoveXUntil**: Only modifies `sprite.change_x`, never touches `sprite.change_y`
- **MoveYUntil**: Only modifies `sprite.change_y`, never touches `sprite.change_x`

This allows you to compose orthogonal movements safely using `parallel()`:

```python
from actions import MoveXUntil, MoveYUntil, parallel, infinite

# X-axis scrolling with limit boundary behavior
scroll_x = MoveXUntil(
    velocity=(-3, 0),  # Only X velocity
    condition=infinite,
    bounds=(0, 0, 800, 600),
    boundary_behavior="limit"
)

# Y-axis bouncing with bounce boundary behavior  
bob_y = MoveYUntil(
    velocity=(0, 2),  # Only Y velocity
    condition=infinite,
    bounds=(0, 0, 800, 600),
    boundary_behavior="bounce"
)

# Compose both movements safely
parallel(scroll_x, bob_y).apply(sprite)
# Result: sprite.change_x = -3, sprite.change_y = 2
# X-axis limited at boundaries, Y-axis bounces
```

### Axis-Specific Helper Functions

For convenience, use the target-first helper functions:

```python
from actions import move_x_until, move_y_until, infinite

# X-axis movement only
scroll = move_x_until(
    target=sprite,
    dx=-4,
    condition=infinite,
    bounds=(0, 0, 800, 600),
    boundary_behavior="limit"
)

# Y-axis movement only
bob = move_y_until(
    target=sprite,
    dy=2,
    condition=infinite,
    bounds=(0, 0, 800, 600),
    boundary_behavior="bounce"
)

# Both movements are applied independently
# sprite.change_x = -4, sprite.change_y = 2
```

### Axis-Aware Pattern Factories

Pattern factories now support an `axis` parameter for creating axis-specific patterns:

```python
from actions import create_bounce_pattern, create_patrol_pattern

# X-axis only bouncing
bounce_x = create_bounce_pattern(
    velocity=(150, 0),  # Only X velocity matters
    bounds=(0, 0, 800, 600),
    axis="x"
)

# Y-axis only patrol
patrol_y = create_patrol_pattern(
    start_pos=(100, 200),
    end_pos=(100, 400),  # Vertical patrol
    speed=120,
    axis="y"
)

# Compose with other movements
move_x_until(sprite, dx=5, condition=infinite).apply(sprite)
patrol_y.apply(sprite)
# X-axis continues at 5 px/frame, Y-axis patrols vertically
```

### Velocity Semantics

All velocity values use Arcade's native "pixels per frame at 60 FPS" semantics:

- `move_x_until(sprite, dx=5, condition=infinite)` means 5 pixels per frame
- `move_y_until(sprite, dy=2, condition=infinite)` means 2 pixels per frame
- This maintains perfect consistency with Arcade's `sprite.change_x/change_y` system

### Common Use Cases

**Scrolling Background with Bouncing Elements:**
```python
# Background scrolls left, elements bounce vertically
scroll = move_x_until(background_sprites, dx=-2, condition=infinite)
bounce = move_y_until(element_sprites, dy=1, condition=infinite, 
                     bounds=(0, 0, 800, 600), boundary_behavior="bounce")
```

**Platformer Movement:**
```python
# Horizontal movement with gravity
move_horizontal = move_x_until(player, dx=3, condition=infinite)
apply_gravity = move_y_until(player, dy=-1, condition=infinite,
                           bounds=(0, 0, 800, 600), boundary_behavior="limit")
```

**Formation Movement:**
```python
# Formation moves as a unit horizontally, individual bobbing
formation_move = move_x_until(formation, dx=-1, condition=infinite)
for sprite in formation:
    bob = move_y_until(sprite, dy=0.5, condition=infinite,
                      bounds=(0, 0, 800, 600), boundary_behavior="bounce")
```

This approach ensures that orthogonal movements don't interfere with each other, making complex movement patterns predictable and composable.

This pattern ensures collision checks are only performed once per frame, and all relevant data is passed directly to the handler—no need for extra state or repeated queries. This is the recommended approach for efficient, event-driven collision handling in ArcadeActions.

## Important Implementation Notes

### infinite() Function

**CRITICAL:** The `infinite()` function implementation in `actions/conditional.py` should never be modified. The current implementation (`return False`) is intentional and correct for the project's usage patterns. Do not suggest changing it to return `lambda: False` or any other callable. This function works correctly with the existing codebase and should not be modified.

### SpritePool (experimental)

`actions.pools.SpritePool` enables zero-allocation gameplay by reusing sprites:

```python
from actions.pools import SpritePool
from actions import arrange_grid
import arcade

def make_enemy():
    return arcade.Sprite(":resources:images/enemies/bee.png", scale=0.5)

pool = SpritePool(make_enemy, max_size=300)
wave = pool.acquire(20)  # invisible, un-positioned sprites
arrange_grid(sprites=wave, rows=4, cols=5, start_x=100, start_y=400)
# ... gameplay ...
pool.release(wave)  # return hidden & detached
```

API:
- `acquire(n) -> list[Sprite]`
- `release(iterable[Sprite])`
- `assign(iterable[Sprite])` (load external sprites into the pool)


### Velocity System Consistency

**CRITICAL:** MoveUntil ALWAYS uses `sprite.change_x` and `sprite.change_y` (Arcade's built-in velocity system). NEVER use `sprite.velocity` - that's not how MoveUntil works. Be consistent - don't switch back and forth between approaches.

### Condition Function Usage

**CRITICAL:** ALWAYS use `infinite` instead of `lambda: False` for infinite/never-ending conditions. This is the standard pattern in the codebase.

## CallbackUntil Action

The `CallbackUntil` action executes a callback function at specified intervals or every frame until a condition is met. This is useful for periodic updates, state monitoring, or time-based effects.

### Basic Usage

```python
from actions import CallbackUntil, callback_until, duration, infinite

# Every frame callback
def update_color():
    sprite.color = (random.randint(0, 255), 0, 0)

CallbackUntil(
    callback=update_color,
    condition=duration(5.0)
).apply(sprite, tag="color_change")

# Or using the helper function
callback_until(sprite, callback=update_color, condition=duration(5.0))
```

### Interval-Based Callbacks

For performance-sensitive scenarios, use `seconds_between_calls` to limit callback frequency:

```python
# Call every 0.1 seconds instead of every frame
def periodic_check():
    if enemy_health <= 0:
        enemy.remove_from_sprite_lists()

CallbackUntil(
    callback=periodic_check,
    condition=infinite,
    seconds_between_calls=0.1
).apply(enemy, tag="health_check")

# Or using the helper
callback_until(
    enemy, 
    callback=periodic_check, 
    condition=infinite,
    seconds_between_calls=0.1
)
```

### Callback Signatures

Callbacks can accept zero or one parameter:

```python
# Zero-parameter callback
def update_score():
    game.score += 10

# One-parameter callback (receives the target)
def update_sprite_color(sprite):
    sprite.color = (255, 0, 0)

# Both work with CallbackUntil - it automatically detects the signature
CallbackUntil(callback=update_score, condition=duration(1.0)).apply(sprite)
CallbackUntil(callback=update_sprite_color, condition=duration(1.0)).apply(sprite)
```

### Factor Scaling

Use `set_factor()` to dynamically adjust callback timing:

```python
action = CallbackUntil(
    callback=update_animation,
    condition=infinite,
    seconds_between_calls=0.1
)
action.apply(sprite)

# Speed up callbacks (2x faster)
action.set_factor(2.0)  # Now calls every 0.05 seconds

# Pause callbacks
action.set_factor(0.0)  # Callbacks stop

# Resume at normal speed
action.set_factor(1.0)  # Back to every 0.1 seconds
```

### Shader and Particle Integration

`CallbackUntil` excels at managing temporal shader effects and particle systems, eliminating manual state tracking. The key pattern is to encapsulate state in objects that update themselves, similar to the laser_gates forcefield color cycling example:

```python
from actions import CallbackUntil, callback_until, duration, infinite

# Particle emitter management
thruster_emitter = arcade.Emitter(...)

def update_thruster():
    thruster_emitter.center_x = rocket.center_x
    thruster_emitter.center_y = rocket.center_y
    thruster_emitter.update()

# Emit particles while thrusting
CallbackUntil(
    callback=update_thruster,
    condition=lambda: not rocket.is_thrusting
).apply(rocket, tag="thruster")

# Dynamic shader uniform updates with state tracking
class ShieldEffect:
    def __init__(self):
        self.glow_intensity = 0.0
        self.time_elapsed = 0.0
        
    def update_glow(self):
        self.time_elapsed += 0.016  # Approximate frame time
        self.glow_intensity = 0.5 + 0.5 * math.sin(self.time_elapsed * 3)
        shield_shader.set_uniform('glow', self.glow_intensity)

shield_effect = ShieldEffect()

# Shield glow effect for 5 seconds
callback_until(
    player,
    callback=shield_effect.update_glow,
    condition=duration(5.0),
    tag="shield_glow"
)

# Conditional lighting effects
def update_raycast_shadows():
    light_layer.update()

callback_until(
    player,
    callback=update_raycast_shadows,
    condition=lambda: not lights_enabled,
    tag="dynamic_lighting"
)

# Pattern from laser_gates: Periodic state updates with encapsulated logic
class ColorCycler:
    def __init__(self, colors, sprites):
        self.colors = colors
        self.sprites = sprites
        self.current_index = 0
        
    def cycle_colors(self):
        """Update all sprites to the next color in sequence."""
        for sprite in self.sprites:
            sprite.color = self.colors[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.colors)

# Create color cycler for enemy formation
enemy_colors = [arcade.color.RED, arcade.color.BLUE, arcade.color.GREEN]
color_cycler = ColorCycler(enemy_colors, enemy_formation)

# Cycle colors every 0.1 seconds for 5 seconds
callback_until(
    enemy_formation,
    callback=color_cycler.cycle_colors,
    condition=duration(5.0),
    seconds_between_calls=0.1,
    tag="enemy_color_cycle"
)
```

**Benefits over manual management:**
- ✅ No state flags (`thruster_active`, `shield_glow_time`)
- ✅ Automatic lifecycle (start, run, cleanup)
- ✅ Declarative intent (update until condition)
- ✅ Composable with other actions
- ✅ Tag-based control for easy enable/disable

**Comparison:**

```python
# ❌ WITHOUT CallbackUntil - Manual state management
class MyGame:
    def __init__(self):
        self.thruster_active = False
        self.shield_glow_time = 0
        self.shield_active = False
        
    def on_update(self, delta_time):
        if self.player.is_thrusting:
            self.thruster_active = True
            self.thruster_emitter.update()
        else:
            self.thruster_active = False
            
        if self.shield_active:
            self.shield_glow_time += delta_time
            glow = 0.5 + 0.5 * math.sin(self.shield_glow_time * 3)
            self.shield_shader.set_uniform('glow', glow)
            if self.shield_glow_time > 5.0:
                self.shield_active = False
                self.shield_glow_time = 0

# ✅ WITH CallbackUntil - Declarative and clean
class MyGame:
    def __init__(self):
        self.shield_effect = ShieldEffect()
        
    def setup_effects(self):
        callback_until(
            self.player,
            callback=lambda: self.thruster_emitter.update(),
            condition=lambda: not self.player.is_thrusting,
            tag="thruster"
        )
        
        callback_until(
            self.player,
            callback=self.shield_effect.update_glow,
            condition=duration(5.0),
            tag="shield"
        )
    
    def on_update(self, delta_time):
        Action.update_all(delta_time)  # That's it!
```

### Best Practices

1. **Use intervals for performance**: Avoid per-frame callbacks for expensive operations
2. **Prefer conditions over infinite loops**: Use specific conditions when possible
3. **Handle exceptions gracefully**: Callback exceptions are caught automatically
4. **Tag your actions**: Use meaningful tags for easier management

```python
# Good: Performance-conscious with clear condition
callback_until(
    target=projectile,
    callback=check_collision,
    condition=lambda: projectile.center_y < 0,
    seconds_between_calls=0.02,
    tag="collision_check"
)

# Avoid: Expensive per-frame operations
# callback_until(target, expensive_operation, infinite)  # No interval!
```
