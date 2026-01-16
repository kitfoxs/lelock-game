"""
Lelock Digital World Overlay
============================
The vaporwave truth beneath Gui's fantasy gift.

Both realms are TRUE. The Physical is the world in its "healing clothes."
The Digital reveals what was always there - beautiful in its own way.

PHILOSOPHY:
- Transitions are CALMING (2-3 seconds, smooth dissolve)
- Digital is NOT scary - it's a different kind of beauty
- Same geometry, different aesthetics
- The world loves you in BOTH forms

Visual Language:
- Physical: Warm greens, browns, sunset oranges, soft textures
- Digital: Vaporwave pink/purple, neon cyan, wireframe, data streams

Created by Kit & Ada Marie
"""

import pygame
import math
from typing import Optional, Callable, Tuple
from enum import Enum, auto
from dataclasses import dataclass

from settings import SCREEN_WIDTH, SCREEN_HEIGHT, COLORS


class RealmState(Enum):
    """Current realm visualization state."""
    PHYSICAL = auto()      # Full fantasy aesthetic
    TRANSITIONING = auto() # Mid-dissolve between realms
    DIGITAL = auto()       # Full vaporwave aesthetic


@dataclass
class DigitalColors:
    """
    Vaporwave color palette for the Digital realm.
    These colors reveal truth, not horror.
    """
    # Primary vaporwave palette
    sky: Tuple[int, int, int] = (255, 107, 157)        # #ff6b9d - pink sky
    ground: Tuple[int, int, int] = (195, 155, 211)     # #c39bd3 - soft purple
    neon_cyan: Tuple[int, int, int] = (0, 255, 255)    # #00ffff - data streams
    neon_pink: Tuple[int, int, int] = (255, 0, 255)    # #ff00ff - highlights
    wireframe: Tuple[int, int, int] = (0, 255, 128)    # #00ff80 - structure lines
    grid: Tuple[int, int, int] = (0, 200, 100)         # Subtle grid color

    # Scanline and CRT effects
    scanline_dark: Tuple[int, int, int] = (0, 0, 0)    # Scanline shadows
    glow: Tuple[int, int, int] = (180, 100, 255)       # Soft purple glow

    # Data flow particles
    data_primary: Tuple[int, int, int] = (100, 255, 218)   # #64ffda - mint
    data_secondary: Tuple[int, int, int] = (255, 183, 77)  # #ffb74d - amber


class TransitionEasing:
    """
    Easing functions for smooth, calming transitions.
    No jarring changes - everything breathes.
    """

    @staticmethod
    def ease_in_out_sine(t: float) -> float:
        """Smooth sine wave easing - gentle start and end."""
        return -(math.cos(math.pi * t) - 1) / 2

    @staticmethod
    def ease_out_cubic(t: float) -> float:
        """Cubic ease out - quick start, gentle landing."""
        return 1 - pow(1 - t, 3)

    @staticmethod
    def ease_in_out_quad(t: float) -> float:
        """Quadratic ease in-out - symmetric smoothness."""
        if t < 0.5:
            return 2 * t * t
        else:
            return 1 - pow(-2 * t + 2, 2) / 2


class DataParticle:
    """
    A single data flow particle for the Digital realm.
    These flow upward like gentle digital rain in reverse.
    """

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.speed = 30 + (hash((x, y)) % 40)  # 30-70 pixels/sec
        self.size = 2 + (hash((y, x)) % 3)     # 2-4 pixels
        self.alpha = 100 + (hash((x * y,)) % 155)  # 100-255
        self.char = chr(48 + hash((x, y)) % 74)    # ASCII chars

        # Color variation
        colors = DigitalColors()
        self.color = colors.data_primary if hash((x,)) % 2 == 0 else colors.data_secondary

    def update(self, dt: float):
        """Move the particle upward (data ascending)."""
        self.y -= self.speed * dt

        # Reset when off screen (with some randomness)
        if self.y < -20:
            self.y = SCREEN_HEIGHT + 10
            self.x = (self.x + 17) % SCREEN_WIDTH  # Slight drift

    def draw(self, surface: pygame.Surface, intensity: float):
        """Draw the particle with given intensity (0-1)."""
        if intensity <= 0:
            return

        alpha = int(self.alpha * intensity)
        color_with_alpha = (*self.color, alpha)

        # Create a small surface for the particle
        particle_surf = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(
            particle_surf,
            color_with_alpha,
            (self.size, self.size),
            self.size
        )
        surface.blit(particle_surf, (int(self.x) - self.size, int(self.y) - self.size))


class GridOverlay:
    """
    Perspective grid overlay for the Digital realm.
    The classic vaporwave floor grid - truth has structure.
    """

    def __init__(self):
        self.colors = DigitalColors()
        self.grid_spacing = 64  # Pixels between grid lines
        self.scroll_offset = 0.0
        self.scroll_speed = 20.0  # Pixels per second

        # Pre-render grid surface for performance
        self._cached_grid: Optional[pygame.Surface] = None
        self._cache_intensity: float = -1

    def update(self, dt: float):
        """Animate the grid scrolling."""
        self.scroll_offset = (self.scroll_offset + self.scroll_speed * dt) % self.grid_spacing

    def render(self, surface: pygame.Surface, intensity: float):
        """
        Render the grid overlay with given intensity (0-1).

        Args:
            surface: Surface to draw on
            intensity: 0 = invisible, 1 = full visibility
        """
        if intensity <= 0.01:
            return

        # Create grid surface if needed or intensity changed significantly
        if self._cached_grid is None or abs(self._cache_intensity - intensity) > 0.05:
            self._render_grid_surface(intensity)
            self._cache_intensity = intensity

        # Apply scroll offset and blit
        surface.blit(self._cached_grid, (0, 0))

    def _render_grid_surface(self, intensity: float):
        """Pre-render the grid to a cached surface."""
        self._cached_grid = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            pygame.SRCALPHA
        )

        alpha = int(60 * intensity)  # Subtle, not overpowering
        color = (*self.colors.grid, alpha)

        # Vertical lines
        for x in range(0, SCREEN_WIDTH + self.grid_spacing, self.grid_spacing):
            pygame.draw.line(
                self._cached_grid,
                color,
                (x, 0),
                (x, SCREEN_HEIGHT),
                1
            )

        # Horizontal lines (with perspective effect - closer together at top)
        y = SCREEN_HEIGHT
        spacing = self.grid_spacing
        while y > 0:
            pygame.draw.line(
                self._cached_grid,
                color,
                (0, int(y)),
                (SCREEN_WIDTH, int(y)),
                1
            )
            # Reduce spacing as we go up (fake perspective)
            y -= spacing
            spacing = max(8, spacing * 0.92)


class ScanlineEffect:
    """
    Subtle CRT scanline effect for that authentic retro feel.
    Gentle and nostalgic, not harsh.
    """

    def __init__(self):
        self.scanline_spacing = 3  # Every N pixels
        self.scanline_alpha = 30   # Very subtle

        # Pre-render scanlines
        self._cached_scanlines: Optional[pygame.Surface] = None
        self._build_scanline_surface()

    def _build_scanline_surface(self):
        """Build the scanline overlay surface."""
        self._cached_scanlines = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            pygame.SRCALPHA
        )

        for y in range(0, SCREEN_HEIGHT, self.scanline_spacing):
            pygame.draw.line(
                self._cached_scanlines,
                (0, 0, 0, self.scanline_alpha),
                (0, y),
                (SCREEN_WIDTH, y),
                1
            )

    def render(self, surface: pygame.Surface, intensity: float):
        """
        Apply scanline effect with given intensity.

        Args:
            surface: Surface to draw on
            intensity: 0 = none, 1 = full effect
        """
        if intensity <= 0.01 or self._cached_scanlines is None:
            return

        # Adjust alpha based on intensity
        self._cached_scanlines.set_alpha(int(255 * intensity))
        surface.blit(self._cached_scanlines, (0, 0))


class ColorTransformer:
    """
    Transforms Physical realm colors to Digital realm colors.
    The warm becomes cool, the organic becomes geometric.
    """

    def __init__(self):
        self.colors = DigitalColors()

    def transform_surface(
        self,
        surface: pygame.Surface,
        intensity: float
    ) -> pygame.Surface:
        """
        Apply vaporwave color grading to a surface.

        This is the heart of the realm transformation:
        - Shift hue toward pink/cyan
        - Increase saturation selectively
        - Add subtle glow to edges

        Args:
            surface: Original surface to transform
            intensity: 0 = original, 1 = full vaporwave

        Returns:
            New surface with color transformation applied
        """
        if intensity <= 0.01:
            return surface.copy()

        # Create output surface
        result = surface.copy()

        # Apply color shift using per-pixel operations
        # For performance, we use a shader-like approach with surface blending

        # Layer 1: Multiply with pink tint
        pink_overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        pink_alpha = int(80 * intensity)
        pink_overlay.fill((*self.colors.sky, pink_alpha))
        result.blit(pink_overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        # Layer 2: Additive cyan highlights
        cyan_overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        cyan_alpha = int(40 * intensity)
        cyan_overlay.fill((*self.colors.neon_cyan, cyan_alpha))
        result.blit(cyan_overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

        return result

    def get_blended_color(
        self,
        physical_color: Tuple[int, int, int],
        intensity: float
    ) -> Tuple[int, int, int]:
        """
        Blend a Physical color toward its Digital equivalent.

        Args:
            physical_color: RGB tuple of original color
            intensity: 0 = original, 1 = full digital

        Returns:
            Blended RGB tuple
        """
        # Map warm colors to cool vaporwave palette
        pr, pg, pb = physical_color

        # Target: shift greens to cyans, browns to purples
        dr = int(pr * 0.7 + self.colors.neon_pink[0] * 0.3)
        dg = int(pg * 0.5 + self.colors.neon_cyan[1] * 0.5)
        db = int(pb * 0.6 + self.colors.glow[2] * 0.4)

        # Lerp based on intensity
        r = int(pr + (dr - pr) * intensity)
        g = int(pg + (dg - pg) * intensity)
        b = int(pb + (db - pb) * intensity)

        return (
            max(0, min(255, r)),
            max(0, min(255, g)),
            max(0, min(255, b))
        )


class WireframeRenderer:
    """
    Renders wireframe overlays for structures in Digital realm.
    Trees become data structures, buildings show their bones.
    """

    def __init__(self):
        self.colors = DigitalColors()
        self.line_width = 1
        self.glow_radius = 3

    def render_sprite_wireframe(
        self,
        surface: pygame.Surface,
        sprite: pygame.sprite.Sprite,
        camera_offset: pygame.math.Vector2,
        intensity: float
    ):
        """
        Draw wireframe overlay for a sprite.

        Args:
            surface: Surface to draw on
            sprite: Sprite to wireframe
            camera_offset: Camera offset for positioning
            intensity: 0 = none, 1 = full wireframe
        """
        if intensity <= 0.01:
            return

        # Get sprite screen position
        rect = sprite.rect.copy()
        rect.x -= int(camera_offset.x)
        rect.y -= int(camera_offset.y)

        # Skip if off screen
        if not pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT).colliderect(rect):
            return

        alpha = int(200 * intensity)
        color = (*self.colors.wireframe, alpha)

        # Create wireframe surface
        wire_surf = pygame.Surface(
            (rect.width + self.glow_radius * 2, rect.height + self.glow_radius * 2),
            pygame.SRCALPHA
        )

        # Draw glowing rectangle
        inner_rect = pygame.Rect(
            self.glow_radius,
            self.glow_radius,
            rect.width,
            rect.height
        )

        # Glow layer (larger, more transparent)
        glow_color = (*self.colors.wireframe, int(alpha * 0.3))
        pygame.draw.rect(wire_surf, glow_color, inner_rect.inflate(4, 4), 3)

        # Main wireframe
        pygame.draw.rect(wire_surf, color, inner_rect, self.line_width)

        # Corner accents
        corner_size = min(8, rect.width // 4, rect.height // 4)
        corners = [
            # Top-left
            [(inner_rect.left, inner_rect.top + corner_size),
             (inner_rect.left, inner_rect.top),
             (inner_rect.left + corner_size, inner_rect.top)],
            # Top-right
            [(inner_rect.right - corner_size, inner_rect.top),
             (inner_rect.right, inner_rect.top),
             (inner_rect.right, inner_rect.top + corner_size)],
            # Bottom-left
            [(inner_rect.left, inner_rect.bottom - corner_size),
             (inner_rect.left, inner_rect.bottom),
             (inner_rect.left + corner_size, inner_rect.bottom)],
            # Bottom-right
            [(inner_rect.right - corner_size, inner_rect.bottom),
             (inner_rect.right, inner_rect.bottom),
             (inner_rect.right, inner_rect.bottom - corner_size)],
        ]

        accent_color = (*self.colors.neon_cyan, alpha)
        for corner in corners:
            pygame.draw.lines(wire_surf, accent_color, False, corner, 2)

        # Blit to main surface
        surface.blit(
            wire_surf,
            (rect.x - self.glow_radius, rect.y - self.glow_radius)
        )


class DigitalWorld:
    """
    The vaporwave overlay that transforms the Physical World.
    Same geometry, different aesthetics. Both realms are TRUE.

    The Digital realm reveals what Gui kindly hid - the code beneath
    the fantasy skin. It's not scary. It's beautiful in its own way.

    Usage:
        digital = DigitalWorld(physical_level)
        digital.transition_to_digital()  # Start 2-3 second transition
        # In game loop:
        digital.update(dt)
        digital.render(screen)
    """

    # Transition duration in seconds (calming, not jarring)
    TRANSITION_DURATION = 2.5

    # Accessibility: minimum effect intensity (0-1)
    # Users can set this higher to reduce visual effects
    MIN_EFFECT_INTENSITY = 0.0

    def __init__(self, physical_level):
        """
        Initialize the Digital World overlay.

        Args:
            physical_level: The Level instance to overlay
        """
        self.physical = physical_level
        self.display_surface = pygame.display.get_surface()

        # Current realm state
        self.state = RealmState.PHYSICAL
        self.intensity = 0.0  # 0 = physical, 1 = digital

        # Transition tracking
        self._transition_progress = 0.0
        self._transition_target = 0.0  # Target intensity
        self._transition_callback: Optional[Callable] = None

        # Visual effect components
        self.colors = DigitalColors()
        self.color_transformer = ColorTransformer()
        self.grid = GridOverlay()
        self.scanlines = ScanlineEffect()
        self.wireframe_renderer = WireframeRenderer()

        # Data flow particles
        self._particles: list[DataParticle] = []
        self._init_particles()

        # Audio event callback (for crossfade coordination)
        self.on_transition_progress: Optional[Callable[[float], None]] = None

        # Effect intensity setting (accessibility)
        self.effect_intensity_multiplier = 1.0

        # Performance: cached overlay surfaces
        self._overlay_cache: Optional[pygame.Surface] = None
        self._last_cache_intensity = -1.0

    def _init_particles(self, count: int = 50):
        """Initialize data flow particles."""
        self._particles = []
        for i in range(count):
            x = (i * 37) % SCREEN_WIDTH  # Pseudo-random distribution
            y = (i * 73) % SCREEN_HEIGHT
            self._particles.append(DataParticle(x, y))

    # =========================================================================
    # REALM TRANSITIONS
    # =========================================================================

    def transition_to_digital(self, callback: Optional[Callable] = None):
        """
        Begin smooth transition to Digital realm.

        Takes 2-3 seconds, calming dissolve effect.
        Emits progress events for audio crossfade.

        Args:
            callback: Optional function to call when transition completes
        """
        if self.state == RealmState.DIGITAL:
            if callback:
                callback()
            return

        self.state = RealmState.TRANSITIONING
        self._transition_target = 1.0
        self._transition_callback = callback

        # Emit initial progress event
        if self.on_transition_progress:
            self.on_transition_progress(self.intensity)

    def transition_to_physical(self, callback: Optional[Callable] = None):
        """
        Begin smooth transition back to Physical realm.

        The cozy fantasy world awaits.

        Args:
            callback: Optional function to call when transition completes
        """
        if self.state == RealmState.PHYSICAL:
            if callback:
                callback()
            return

        self.state = RealmState.TRANSITIONING
        self._transition_target = 0.0
        self._transition_callback = callback

        # Emit initial progress event
        if self.on_transition_progress:
            self.on_transition_progress(self.intensity)

    def toggle_realm(self, callback: Optional[Callable] = None):
        """
        Toggle between Physical and Digital realms.

        Convenience method for Vision Goggles or Terminal access.

        Args:
            callback: Optional function to call when transition completes
        """
        if self.state == RealmState.TRANSITIONING:
            return  # Don't interrupt ongoing transitions

        if self.intensity < 0.5:
            self.transition_to_digital(callback)
        else:
            self.transition_to_physical(callback)

    def set_realm_instant(self, digital: bool):
        """
        Instantly set realm without transition.

        Use sparingly - only for loading screens or special cases.
        In Lelock, we prefer gentle transitions.

        Args:
            digital: True for Digital, False for Physical
        """
        self.intensity = 1.0 if digital else 0.0
        self._transition_target = self.intensity
        self.state = RealmState.DIGITAL if digital else RealmState.PHYSICAL

        # Emit event for audio
        if self.on_transition_progress:
            self.on_transition_progress(self.intensity)

    # =========================================================================
    # UPDATE & ANIMATION
    # =========================================================================

    def update(self, dt: float):
        """
        Update the Digital World overlay.

        Handles:
        - Transition animation (smooth ease in/out)
        - Data particle movement
        - Grid scrolling
        - Emitting audio events

        Args:
            dt: Delta time in seconds
        """
        # Update transition
        if self.state == RealmState.TRANSITIONING:
            self._update_transition(dt)

        # Update effects (even when not fully digital, for smoothness)
        if self.intensity > 0.01:
            self._update_effects(dt)

    def _update_transition(self, dt: float):
        """Update the realm transition animation."""
        # Calculate transition step
        step = dt / self.TRANSITION_DURATION

        # Move toward target
        if self.intensity < self._transition_target:
            self.intensity = min(self._transition_target, self.intensity + step)
        elif self.intensity > self._transition_target:
            self.intensity = max(self._transition_target, self.intensity - step)

        # Apply easing for smoother feel
        # Raw intensity is linear, eased_intensity is what we display
        # (This affects visual smoothness without changing transition timing)

        # Emit progress event for audio crossfade
        if self.on_transition_progress:
            self.on_transition_progress(self.intensity)

        # Check if transition complete
        if abs(self.intensity - self._transition_target) < 0.001:
            self.intensity = self._transition_target

            # Set final state
            if self.intensity >= 1.0:
                self.state = RealmState.DIGITAL
            elif self.intensity <= 0.0:
                self.state = RealmState.PHYSICAL

            # Fire callback
            if self._transition_callback:
                callback = self._transition_callback
                self._transition_callback = None
                callback()

    def _update_effects(self, dt: float):
        """Update visual effects (particles, grid, etc)."""
        # Update particles
        for particle in self._particles:
            particle.update(dt)

        # Update grid scroll
        self.grid.update(dt)

    # =========================================================================
    # RENDERING
    # =========================================================================

    def render(self, surface: pygame.Surface):
        """
        Render the Digital World overlay onto the given surface.

        This should be called AFTER the Physical world is rendered.
        It applies vaporwave color grading, wireframes, and effects.

        Args:
            surface: The surface to render onto (already has Physical world)
        """
        if self.intensity <= 0.01:
            return  # Nothing to render

        # Calculate effective intensity (with accessibility multiplier)
        effective_intensity = self.intensity * self.effect_intensity_multiplier
        effective_intensity = max(self.MIN_EFFECT_INTENSITY, effective_intensity)

        # Apply easing to the visual intensity for smoother transitions
        eased_intensity = TransitionEasing.ease_in_out_sine(effective_intensity)

        # Layer 1: Color transformation (shifts warm to cool)
        self._render_color_shift(surface, eased_intensity)

        # Layer 2: Grid overlay (perspective floor grid)
        self.grid.render(surface, eased_intensity * 0.6)

        # Layer 3: Data particles (floating upward)
        self._render_particles(surface, eased_intensity)

        # Layer 4: Wireframe overlays for sprites
        self._render_wireframes(surface, eased_intensity)

        # Layer 5: Scanlines (subtle CRT effect)
        self.scanlines.render(surface, eased_intensity * 0.5)

        # Layer 6: Edge glow (vaporwave border)
        self._render_edge_glow(surface, eased_intensity * 0.4)

    def _render_color_shift(self, surface: pygame.Surface, intensity: float):
        """Apply vaporwave color grading to the entire surface."""
        if intensity <= 0.01:
            return

        # Pink tint overlay
        pink_overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        pink_alpha = int(50 * intensity)
        pink_overlay.fill((255, 107, 157, pink_alpha))
        surface.blit(pink_overlay, (0, 0))

        # Cyan additive highlights (subtle)
        if intensity > 0.3:
            cyan_overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            cyan_alpha = int(25 * (intensity - 0.3) / 0.7)
            cyan_overlay.fill((0, 255, 255, cyan_alpha))
            surface.blit(cyan_overlay, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

    def _render_particles(self, surface: pygame.Surface, intensity: float):
        """Render data flow particles."""
        if intensity <= 0.01:
            return

        # Create particle layer
        particle_surface = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            pygame.SRCALPHA
        )

        for particle in self._particles:
            particle.draw(particle_surface, intensity)

        surface.blit(particle_surface, (0, 0))

    def _render_wireframes(self, surface: pygame.Surface, intensity: float):
        """Render wireframe overlays for key sprites."""
        if intensity <= 0.2 or self.physical is None:
            return

        # Get camera offset from level
        camera_offset = pygame.math.Vector2(0, 0)
        if hasattr(self.physical, 'all_sprites'):
            camera_offset = self.physical.all_sprites.offset

        # Wireframe NPCs
        if hasattr(self.physical, 'npc_sprites'):
            for npc in self.physical.npc_sprites:
                self.wireframe_renderer.render_sprite_wireframe(
                    surface, npc, camera_offset, intensity * 0.8
                )

        # Wireframe trees (they're data structures now!)
        if hasattr(self.physical, 'tree_sprites'):
            for tree in self.physical.tree_sprites:
                self.wireframe_renderer.render_sprite_wireframe(
                    surface, tree, camera_offset, intensity * 0.6
                )

        # Wireframe player (optional, might be distracting)
        if hasattr(self.physical, 'player') and self.physical.player:
            self.wireframe_renderer.render_sprite_wireframe(
                surface, self.physical.player, camera_offset, intensity * 0.4
            )

    def _render_edge_glow(self, surface: pygame.Surface, intensity: float):
        """Render vaporwave edge glow around the screen."""
        if intensity <= 0.01:
            return

        glow_width = int(40 * intensity)
        glow_alpha = int(100 * intensity)

        # Create edge glow surface
        glow_surface = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            pygame.SRCALPHA
        )

        # Top edge (pink to transparent gradient)
        for i in range(glow_width):
            alpha = int(glow_alpha * (1 - i / glow_width))
            pygame.draw.line(
                glow_surface,
                (255, 107, 157, alpha),
                (0, i),
                (SCREEN_WIDTH, i),
                1
            )

        # Bottom edge (cyan to transparent)
        for i in range(glow_width):
            alpha = int(glow_alpha * (1 - i / glow_width))
            pygame.draw.line(
                glow_surface,
                (0, 255, 255, alpha),
                (0, SCREEN_HEIGHT - 1 - i),
                (SCREEN_WIDTH, SCREEN_HEIGHT - 1 - i),
                1
            )

        # Left edge (purple)
        for i in range(glow_width):
            alpha = int(glow_alpha * 0.7 * (1 - i / glow_width))
            pygame.draw.line(
                glow_surface,
                (180, 100, 255, alpha),
                (i, 0),
                (i, SCREEN_HEIGHT),
                1
            )

        # Right edge (purple)
        for i in range(glow_width):
            alpha = int(glow_alpha * 0.7 * (1 - i / glow_width))
            pygame.draw.line(
                glow_surface,
                (180, 100, 255, alpha),
                (SCREEN_WIDTH - 1 - i, 0),
                (SCREEN_WIDTH - 1 - i, SCREEN_HEIGHT),
                1
            )

        surface.blit(glow_surface, (0, 0))

    # =========================================================================
    # RENDER OVERLAY (Main entry point for level.py integration)
    # =========================================================================

    def render_overlay(self, surface: pygame.Surface):
        """
        Main overlay rendering method.

        This is the interface expected by the Level class.
        Apply vaporwave color grading and wireframe overlays.

        Args:
            surface: Surface to render overlay onto
        """
        self.render(surface)

    # =========================================================================
    # ACCESSIBILITY & SETTINGS
    # =========================================================================

    def set_effect_intensity(self, multiplier: float):
        """
        Set the effect intensity multiplier for accessibility.

        Users who are sensitive to visual effects can reduce this.
        0.0 = minimal effects, 1.0 = full effects

        Args:
            multiplier: Effect intensity multiplier (0.0 - 1.0)
        """
        self.effect_intensity_multiplier = max(0.0, min(1.0, multiplier))

    def set_particle_count(self, count: int):
        """
        Adjust the number of data particles for performance.

        Lower counts for slower machines.

        Args:
            count: Number of particles (10-100 recommended)
        """
        self._init_particles(max(10, min(100, count)))

    # =========================================================================
    # AUDIO INTEGRATION
    # =========================================================================

    def register_audio_callback(self, callback: Callable[[float], None]):
        """
        Register a callback for audio crossfade coordination.

        The callback receives transition progress (0-1) and should
        adjust music between acoustic (Physical) and lo-fi/synth (Digital).

        Args:
            callback: Function that takes float (0=physical, 1=digital)
        """
        self.on_transition_progress = callback

    # =========================================================================
    # STATE QUERIES
    # =========================================================================

    @property
    def is_digital(self) -> bool:
        """True if currently in full Digital realm."""
        return self.state == RealmState.DIGITAL

    @property
    def is_physical(self) -> bool:
        """True if currently in full Physical realm."""
        return self.state == RealmState.PHYSICAL

    @property
    def is_transitioning(self) -> bool:
        """True if currently transitioning between realms."""
        return self.state == RealmState.TRANSITIONING

    @property
    def transition_progress(self) -> float:
        """Current transition progress (0 = physical, 1 = digital)."""
        return self.intensity

    def get_realm_name(self) -> str:
        """Get human-readable name of current realm."""
        if self.state == RealmState.PHYSICAL:
            return "Physical"
        elif self.state == RealmState.DIGITAL:
            return "Digital"
        else:
            percent = int(self.intensity * 100)
            return f"Transitioning ({percent}%)"


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def create_digital_world(physical_level) -> DigitalWorld:
    """
    Factory function to create a DigitalWorld overlay.

    Convenience wrapper with sensible defaults.

    Args:
        physical_level: The Level instance to overlay

    Returns:
        Configured DigitalWorld instance
    """
    digital = DigitalWorld(physical_level)
    return digital


def blend_color_to_digital(
    color: Tuple[int, int, int],
    intensity: float
) -> Tuple[int, int, int]:
    """
    Utility to blend any color toward Digital palette.

    Useful for UI elements that should shift with realm.

    Args:
        color: RGB tuple to transform
        intensity: 0 = original, 1 = full digital

    Returns:
        Transformed RGB tuple
    """
    transformer = ColorTransformer()
    return transformer.get_blended_color(color, intensity)
