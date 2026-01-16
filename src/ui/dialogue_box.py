"""
Lelock Dialogue Box UI
======================

Renders NPC conversations with the "Bouba" aesthetic - rounded, soft, friend-shaped.
This is where words become warmth.

Design Philosophy:
- Classic RPG dialogue box at bottom of screen
- NPC portrait on left, name plate above text
- Typewriter effect with soft ticks
- Warm cream/parchment background
- Rounded corners, soft shadows, gentle glow
- All transitions are smooth (no jarring cuts)

States:
- HIDDEN: Not visible
- APPEARING: Sliding up animation
- TYPING: Text appearing character by character
- WAITING: Full text shown, waiting for input
- DISAPPEARING: Sliding down animation
- INPUT: Player typing their response
- THINKING: Waiting for LLM response

"In Lelock, every conversation feels like a warm hug."

Author: Ada Marie for Kit Olivas
Project: L.E.L.O.C.K. - Life Emulation & Lucid Observation for Care & Keeping
"""

import pygame
import math
import time
from enum import Enum, auto
from typing import Optional, Tuple, List, Callable, Dict, Any
from dataclasses import dataclass, field
import os
import sys

# Import from parent directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT, LAYERS


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color string to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between a and b by t (0-1)."""
    return a + (b - a) * max(0, min(1, t))


def ease_out_cubic(t: float) -> float:
    """Cubic ease-out for smooth deceleration."""
    return 1 - pow(1 - t, 3)


def ease_in_out_cubic(t: float) -> float:
    """Cubic ease-in-out for smooth start and end."""
    if t < 0.5:
        return 4 * t * t * t
    return 1 - pow(-2 * t + 2, 3) / 2


# =============================================================================
# DIALOGUE BOX STATE
# =============================================================================

class DialogueState(Enum):
    """States for the dialogue box state machine."""
    HIDDEN = auto()
    APPEARING = auto()
    TYPING = auto()
    WAITING = auto()
    INPUT = auto()
    THINKING = auto()
    DISAPPEARING = auto()


@dataclass
class DialogueConfig:
    """Configuration for dialogue box appearance and behavior."""
    # Dimensions
    box_width: int = SCREEN_WIDTH - 80  # Leave margin on sides
    box_height: int = 180
    box_margin_bottom: int = 20
    corner_radius: int = 20

    # Portrait
    portrait_size: int = 120
    portrait_margin: int = 15
    portrait_corner_radius: int = 15

    # Text
    font_size: int = 24
    font_size_small: int = 18
    font_size_name: int = 28
    text_margin: int = 20
    line_spacing: int = 8

    # Typewriter
    chars_per_second: float = 40.0
    skip_to_end_enabled: bool = True

    # Animation
    appear_duration: float = 0.3  # seconds
    disappear_duration: float = 0.2

    # Colors (warm palette - 2700K-3000K feel)
    bg_color: str = '#f5e6d3'  # Warm cream/parchment
    border_color: str = '#8b7355'  # Soft brown
    text_color: str = '#4a3728'  # Dark warm brown
    name_color: str = '#5d4037'  # Slightly lighter brown
    shadow_color: str = '#2d2d44'  # From UI palette
    glow_color: str = '#ffd700'  # Warm gold highlight
    input_bg_color: str = '#fff8e7'  # Lighter cream for input
    thinking_color: str = '#9e8b7d'  # Muted brown for "thinking..."

    # Accessibility
    high_contrast_mode: bool = False
    large_font_mode: bool = False


# =============================================================================
# PORTRAIT FRAME
# =============================================================================

class PortraitFrame:
    """
    Renders the NPC portrait with a cozy rounded frame.

    Features soft shadow, warm border, and gentle glow on speaking.
    """

    def __init__(self, config: DialogueConfig):
        self.config = config
        self.colors = {
            'bg': hex_to_rgb(config.bg_color),
            'border': hex_to_rgb(config.border_color),
            'shadow': hex_to_rgb(config.shadow_color),
            'glow': hex_to_rgb(config.glow_color),
        }

        # Animation state
        self.glow_intensity = 0.0
        self.glow_target = 0.0
        self.glow_speed = 5.0

        # Current portrait surface
        self.portrait_surface: Optional[pygame.Surface] = None
        self.npc_name: str = ""

    def set_portrait(self, portrait: Optional[pygame.Surface], npc_name: str = ""):
        """Set the current NPC portrait."""
        self.npc_name = npc_name

        if portrait is None:
            # Create placeholder
            self.portrait_surface = self._create_placeholder(npc_name)
        else:
            # Scale portrait to fit
            size = self.config.portrait_size - self.config.portrait_margin * 2
            self.portrait_surface = pygame.transform.smoothscale(
                portrait, (size, size)
            )

    def _create_placeholder(self, name: str) -> pygame.Surface:
        """Create a placeholder portrait with initials."""
        size = self.config.portrait_size - self.config.portrait_margin * 2
        surface = pygame.Surface((size, size), pygame.SRCALPHA)

        # Background circle
        pygame.draw.circle(
            surface,
            self.colors['border'],
            (size // 2, size // 2),
            size // 2
        )

        # Inner circle (lighter)
        inner_color = tuple(min(255, c + 40) for c in self.colors['border'])
        pygame.draw.circle(
            surface,
            inner_color,
            (size // 2, size // 2),
            size // 2 - 4
        )

        # Draw initials
        if name:
            font = pygame.font.Font(None, 48)
            initials = name[0].upper() if name else "?"
            text = font.render(initials, True, self.colors['bg'])
            text_rect = text.get_rect(center=(size // 2, size // 2))
            surface.blit(text, text_rect)

        return surface

    def set_speaking(self, is_speaking: bool):
        """Set whether the NPC is currently speaking (affects glow)."""
        self.glow_target = 1.0 if is_speaking else 0.0

    def update(self, dt: float):
        """Update glow animation."""
        # Smooth glow transition
        if self.glow_intensity < self.glow_target:
            self.glow_intensity = min(
                self.glow_target,
                self.glow_intensity + self.glow_speed * dt
            )
        else:
            self.glow_intensity = max(
                self.glow_target,
                self.glow_intensity - self.glow_speed * dt
            )

    def draw(self, surface: pygame.Surface, x: int, y: int):
        """Draw the portrait frame at the given position."""
        size = self.config.portrait_size
        radius = self.config.portrait_corner_radius

        # Draw soft shadow
        shadow_offset = 4
        shadow_surface = pygame.Surface((size + 10, size + 10), pygame.SRCALPHA)
        pygame.draw.rect(
            shadow_surface,
            (*self.colors['shadow'], 60),
            shadow_surface.get_rect(),
            border_radius=radius + 2
        )
        surface.blit(shadow_surface, (x - 3 + shadow_offset, y - 3 + shadow_offset))

        # Draw glow if speaking
        if self.glow_intensity > 0:
            glow_alpha = int(self.glow_intensity * 80)
            glow_size = size + 10
            glow_surface = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
            pygame.draw.rect(
                glow_surface,
                (*self.colors['glow'], glow_alpha),
                glow_surface.get_rect(),
                border_radius=radius + 4
            )
            surface.blit(glow_surface, (x - 5, y - 5))

        # Draw frame background
        frame_rect = pygame.Rect(x, y, size, size)
        pygame.draw.rect(
            surface,
            self.colors['bg'],
            frame_rect,
            border_radius=radius
        )

        # Draw portrait
        if self.portrait_surface:
            margin = self.config.portrait_margin
            surface.blit(self.portrait_surface, (x + margin, y + margin))

        # Draw border
        border_color = self.colors['border']
        if self.glow_intensity > 0:
            # Lerp toward glow color when speaking
            border_color = tuple(
                int(lerp(border_color[i], self.colors['glow'][i], self.glow_intensity * 0.5))
                for i in range(3)
            )
        pygame.draw.rect(
            surface,
            border_color,
            frame_rect,
            width=3,
            border_radius=radius
        )


# =============================================================================
# NAME PLATE
# =============================================================================

class NamePlate:
    """
    Renders the NPC name above the dialogue box.

    Soft rounded rectangle with the character's name.
    """

    def __init__(self, config: DialogueConfig):
        self.config = config
        self.colors = {
            'bg': hex_to_rgb(config.bg_color),
            'border': hex_to_rgb(config.border_color),
            'text': hex_to_rgb(config.name_color),
        }
        self.font = pygame.font.Font(None, config.font_size_name)
        self.name = ""
        self._cached_surface: Optional[pygame.Surface] = None

    def set_name(self, name: str):
        """Set the name to display."""
        if name != self.name:
            self.name = name
            self._cached_surface = None

    def draw(self, surface: pygame.Surface, x: int, y: int):
        """Draw the name plate at the given position."""
        if not self.name:
            return

        # Create cached surface if needed
        if self._cached_surface is None:
            self._create_surface()

        if self._cached_surface:
            surface.blit(self._cached_surface, (x, y))

    def _create_surface(self):
        """Create the name plate surface."""
        # Render text to get size
        text_surface = self.font.render(self.name, True, self.colors['text'])
        text_rect = text_surface.get_rect()

        # Calculate plate size
        padding_h = 20
        padding_v = 8
        plate_width = text_rect.width + padding_h * 2
        plate_height = text_rect.height + padding_v * 2
        radius = 10

        # Create surface
        self._cached_surface = pygame.Surface(
            (plate_width, plate_height),
            pygame.SRCALPHA
        )

        # Draw background
        pygame.draw.rect(
            self._cached_surface,
            (*self.colors['bg'], 240),
            self._cached_surface.get_rect(),
            border_radius=radius
        )

        # Draw border
        pygame.draw.rect(
            self._cached_surface,
            self.colors['border'],
            self._cached_surface.get_rect(),
            width=2,
            border_radius=radius
        )

        # Draw text
        text_x = (plate_width - text_rect.width) // 2
        text_y = (plate_height - text_rect.height) // 2
        self._cached_surface.blit(text_surface, (text_x, text_y))

    def get_width(self) -> int:
        """Get the width of the name plate."""
        if self._cached_surface:
            return self._cached_surface.get_width()
        return 0


# =============================================================================
# TEXT RENDERER
# =============================================================================

class TypewriterText:
    """
    Renders text with a typewriter effect.

    Characters appear one at a time with configurable speed.
    Supports word wrapping and multiple lines.
    """

    def __init__(self, config: DialogueConfig):
        self.config = config

        # Font setup
        font_size = config.font_size
        if config.large_font_mode:
            font_size = int(font_size * 1.3)
        self.font = pygame.font.Font(None, font_size)

        # Colors
        self.text_color = hex_to_rgb(config.text_color)
        if config.high_contrast_mode:
            self.text_color = (0, 0, 0)  # Pure black for high contrast

        # Text state
        self.full_text = ""
        self.visible_chars = 0
        self.char_timer = 0.0
        self.is_complete = False

        # Wrapped lines cache
        self._lines: List[str] = []
        self._max_width = 0

        # Sound callback
        self.on_char_typed: Optional[Callable[[], None]] = None

    def set_text(self, text: str, max_width: int):
        """Set the text to display with typewriter effect."""
        self.full_text = text
        self._max_width = max_width
        self.visible_chars = 0
        self.char_timer = 0.0
        self.is_complete = False

        # Word wrap
        self._lines = self._wrap_text(text, max_width)

    def _wrap_text(self, text: str, max_width: int) -> List[str]:
        """Wrap text to fit within max_width."""
        words = text.split(' ')
        lines = []
        current_line = ""

        for word in words:
            test_line = f"{current_line} {word}".strip()
            test_width = self.font.size(test_line)[0]

            if test_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return lines

    def skip_to_end(self):
        """Skip to the end of the text (show all at once)."""
        self.visible_chars = len(self.full_text)
        self.is_complete = True

    def update(self, dt: float):
        """Update the typewriter effect."""
        if self.is_complete:
            return

        # Advance character timer
        self.char_timer += dt
        chars_to_add = int(self.char_timer * self.config.chars_per_second)

        if chars_to_add > 0:
            old_chars = self.visible_chars
            self.visible_chars = min(
                self.visible_chars + chars_to_add,
                len(self.full_text)
            )
            self.char_timer -= chars_to_add / self.config.chars_per_second

            # Trigger sound for each new character
            if self.on_char_typed and self.visible_chars > old_chars:
                # Only play sound for non-space characters
                for i in range(old_chars, self.visible_chars):
                    if i < len(self.full_text) and self.full_text[i] not in ' \n':
                        self.on_char_typed()
                        break  # One sound per update to avoid spam

            # Check if complete
            if self.visible_chars >= len(self.full_text):
                self.is_complete = True

    def draw(self, surface: pygame.Surface, x: int, y: int):
        """Draw the visible text."""
        if not self._lines:
            return

        # Build visible text by counting characters across lines
        chars_remaining = self.visible_chars
        line_y = y

        for line in self._lines:
            if chars_remaining <= 0:
                break

            # Determine how much of this line to show
            visible_line = line[:chars_remaining]
            chars_remaining -= len(line) + 1  # +1 for the space/newline

            # Render line
            text_surface = self.font.render(visible_line, True, self.text_color)
            surface.blit(text_surface, (x, line_y))

            line_y += self.font.get_height() + self.config.line_spacing

    def get_height(self) -> int:
        """Get the total height of the wrapped text."""
        if not self._lines:
            return 0
        line_height = self.font.get_height() + self.config.line_spacing
        return len(self._lines) * line_height - self.config.line_spacing


# =============================================================================
# INPUT FIELD
# =============================================================================

class InputField:
    """
    Text input field for player responses.

    Soft, warm styling with blinking cursor.
    """

    def __init__(self, config: DialogueConfig):
        self.config = config

        # Font
        font_size = config.font_size
        if config.large_font_mode:
            font_size = int(font_size * 1.3)
        self.font = pygame.font.Font(None, font_size)

        # Colors
        self.colors = {
            'bg': hex_to_rgb(config.input_bg_color),
            'border': hex_to_rgb(config.border_color),
            'text': hex_to_rgb(config.text_color),
            'cursor': hex_to_rgb(config.text_color),
            'placeholder': hex_to_rgb(config.thinking_color),
        }

        # State
        self.text = ""
        self.placeholder = "Type your response..."
        self.is_active = False
        self.cursor_visible = True
        self.cursor_timer = 0.0
        self.cursor_blink_rate = 0.5  # seconds

        # Dimensions
        self.width = 0
        self.height = 40

        # Callbacks
        self.on_submit: Optional[Callable[[str], None]] = None

    def set_active(self, active: bool):
        """Set whether the input field is active."""
        self.is_active = active
        if active:
            self.cursor_visible = True
            self.cursor_timer = 0.0

    def clear(self):
        """Clear the input text."""
        self.text = ""

    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle input events.

        Returns True if the event was consumed.
        """
        if not self.is_active:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if self.text.strip() and self.on_submit:
                    self.on_submit(self.text.strip())
                    self.clear()
                return True
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
                return True
            elif event.unicode and event.unicode.isprintable():
                self.text += event.unicode
                return True

        return False

    def update(self, dt: float):
        """Update cursor blink."""
        if not self.is_active:
            return

        self.cursor_timer += dt
        if self.cursor_timer >= self.cursor_blink_rate:
            self.cursor_timer = 0.0
            self.cursor_visible = not self.cursor_visible

    def draw(self, surface: pygame.Surface, x: int, y: int, width: int):
        """Draw the input field."""
        self.width = width
        radius = 10

        # Background
        rect = pygame.Rect(x, y, width, self.height)
        pygame.draw.rect(
            surface,
            self.colors['bg'],
            rect,
            border_radius=radius
        )

        # Border (highlighted when active)
        border_color = self.colors['border']
        border_width = 2
        if self.is_active:
            border_color = hex_to_rgb(self.config.glow_color)
            border_width = 3

        pygame.draw.rect(
            surface,
            border_color,
            rect,
            width=border_width,
            border_radius=radius
        )

        # Text or placeholder
        text_x = x + 12
        text_y = y + (self.height - self.font.get_height()) // 2

        if self.text:
            text_surface = self.font.render(self.text, True, self.colors['text'])
            surface.blit(text_surface, (text_x, text_y))

            # Cursor
            if self.is_active and self.cursor_visible:
                cursor_x = text_x + text_surface.get_width() + 2
                cursor_height = self.font.get_height()
                pygame.draw.line(
                    surface,
                    self.colors['cursor'],
                    (cursor_x, text_y),
                    (cursor_x, text_y + cursor_height),
                    width=2
                )
        else:
            # Placeholder
            placeholder_surface = self.font.render(
                self.placeholder,
                True,
                self.colors['placeholder']
            )
            surface.blit(placeholder_surface, (text_x, text_y))

            # Cursor at start when empty
            if self.is_active and self.cursor_visible:
                cursor_height = self.font.get_height()
                pygame.draw.line(
                    surface,
                    self.colors['cursor'],
                    (text_x, text_y),
                    (text_x, text_y + cursor_height),
                    width=2
                )


# =============================================================================
# THINKING INDICATOR
# =============================================================================

class ThinkingIndicator:
    """
    Shows "Thinking..." with animated dots while waiting for LLM.

    Provides visual feedback that something is happening.
    """

    def __init__(self, config: DialogueConfig):
        self.config = config
        self.font = pygame.font.Font(None, config.font_size_small)
        self.color = hex_to_rgb(config.thinking_color)

        # Animation
        self.dot_count = 0
        self.timer = 0.0
        self.dot_interval = 0.4  # seconds between dot changes
        self.max_dots = 3

    def update(self, dt: float):
        """Update dot animation."""
        self.timer += dt
        if self.timer >= self.dot_interval:
            self.timer = 0.0
            self.dot_count = (self.dot_count + 1) % (self.max_dots + 1)

    def draw(self, surface: pygame.Surface, x: int, y: int):
        """Draw the thinking indicator."""
        dots = "." * self.dot_count
        text = f"Thinking{dots}"
        text_surface = self.font.render(text, True, self.color)
        surface.blit(text_surface, (x, y))


# =============================================================================
# CONTINUE INDICATOR
# =============================================================================

class ContinueIndicator:
    """
    Animated indicator showing the player can continue.

    A gentle bouncing arrow or pulsing prompt.
    """

    def __init__(self, config: DialogueConfig):
        self.config = config
        self.font = pygame.font.Font(None, config.font_size_small)
        self.color = hex_to_rgb(config.border_color)
        self.highlight_color = hex_to_rgb(config.glow_color)

        # Animation
        self.timer = 0.0
        self.bounce_speed = 3.0
        self.bounce_height = 4

    def update(self, dt: float):
        """Update bounce animation."""
        self.timer += dt

    def draw(self, surface: pygame.Surface, x: int, y: int):
        """Draw the continue indicator."""
        # Bouncing offset
        offset = int(math.sin(self.timer * self.bounce_speed) * self.bounce_height)

        # Draw arrow or prompt
        # Using a simple triangle/arrow
        arrow_size = 8
        points = [
            (x, y + offset),
            (x + arrow_size, y + offset + arrow_size // 2),
            (x, y + offset + arrow_size)
        ]

        # Pulse color
        pulse = (math.sin(self.timer * 4) + 1) / 2
        color = tuple(
            int(lerp(self.color[i], self.highlight_color[i], pulse * 0.5))
            for i in range(3)
        )

        pygame.draw.polygon(surface, color, points)


# =============================================================================
# MAIN DIALOGUE BOX
# =============================================================================

class DialogueBox:
    """
    The complete dialogue box UI component.

    Orchestrates all sub-components:
    - Portrait frame
    - Name plate
    - Typewriter text
    - Input field
    - Thinking indicator
    - Continue indicator

    States are managed via a state machine for clean transitions.
    """

    def __init__(self, config: Optional[DialogueConfig] = None):
        """
        Initialize the dialogue box.

        Args:
            config: Optional configuration. Uses defaults if not provided.
        """
        self.config = config or DialogueConfig()
        self.display_surface = pygame.display.get_surface()

        # Colors
        self.colors = {
            'bg': hex_to_rgb(self.config.bg_color),
            'border': hex_to_rgb(self.config.border_color),
            'shadow': hex_to_rgb(self.config.shadow_color),
            'glow': hex_to_rgb(self.config.glow_color),
        }

        # Components
        self.portrait = PortraitFrame(self.config)
        self.name_plate = NamePlate(self.config)
        self.typewriter = TypewriterText(self.config)
        self.input_field = InputField(self.config)
        self.thinking = ThinkingIndicator(self.config)
        self.continue_indicator = ContinueIndicator(self.config)

        # State machine
        self.state = DialogueState.HIDDEN
        self.state_timer = 0.0

        # Animation
        self.slide_offset = 0  # Positive = below screen
        self.target_slide = 0

        # Current dialogue data
        self.current_npc_name = ""
        self.current_text = ""
        self.current_portrait: Optional[pygame.Surface] = None

        # Callbacks
        self.on_dialogue_complete: Optional[Callable[[], None]] = None
        self.on_player_input: Optional[Callable[[str], None]] = None
        self.on_char_sound: Optional[Callable[[], None]] = None

        # Wire up typewriter sound
        self.typewriter.on_char_typed = self._play_char_sound

        # Wire up input submission
        self.input_field.on_submit = self._handle_player_input

        # Accessibility: screen reader text
        self.screen_reader_text: List[str] = []

        # Calculate positions
        self._calculate_layout()

    def _calculate_layout(self):
        """Calculate component positions based on config."""
        # Box position (bottom of screen, centered)
        self.box_x = (SCREEN_WIDTH - self.config.box_width) // 2
        self.box_y = SCREEN_HEIGHT - self.config.box_height - self.config.box_margin_bottom

        # Portrait position (inside box, left side)
        self.portrait_x = self.box_x + 15
        self.portrait_y = self.box_y + (self.config.box_height - self.config.portrait_size) // 2

        # Text area position
        text_left = self.portrait_x + self.config.portrait_size + 20
        self.text_x = text_left
        self.text_y = self.box_y + 25
        self.text_width = self.box_x + self.config.box_width - text_left - 25

        # Name plate position (above box)
        self.name_x = text_left
        self.name_y = self.box_y - 35

        # Input field position (at bottom of text area)
        self.input_y = self.box_y + self.config.box_height - 55

        # Continue indicator position
        self.continue_x = self.box_x + self.config.box_width - 30
        self.continue_y = self.box_y + self.config.box_height - 25

    def show_dialogue(
        self,
        npc_name: str,
        text: str,
        portrait: Optional[pygame.Surface] = None,
        allow_input: bool = False,
    ):
        """
        Show dialogue from an NPC.

        Args:
            npc_name: The NPC's display name
            text: The dialogue text to show
            portrait: Optional portrait surface
            allow_input: Whether to show input field after text
        """
        self.current_npc_name = npc_name
        self.current_text = text
        self.current_portrait = portrait
        self._allow_input = allow_input

        # Set up components
        self.portrait.set_portrait(portrait, npc_name)
        self.name_plate.set_name(npc_name)
        self.typewriter.set_text(text, self.text_width)

        # Start appearing
        self._transition_to(DialogueState.APPEARING)

        # Accessibility
        self.screen_reader_text.append(f"{npc_name}: {text}")

    def show_thinking(self, npc_name: str, portrait: Optional[pygame.Surface] = None):
        """
        Show the thinking indicator while waiting for LLM.

        Args:
            npc_name: The NPC who is thinking
            portrait: Optional portrait surface
        """
        self.current_npc_name = npc_name
        self.portrait.set_portrait(portrait, npc_name)
        self.name_plate.set_name(npc_name)

        if self.state == DialogueState.HIDDEN:
            self._transition_to(DialogueState.APPEARING)
        else:
            self._transition_to(DialogueState.THINKING)

    def hide(self):
        """Hide the dialogue box with animation."""
        if self.state != DialogueState.HIDDEN:
            self._transition_to(DialogueState.DISAPPEARING)

    def skip(self):
        """Skip to end of current text or advance dialogue."""
        if self.state == DialogueState.TYPING:
            if self.config.skip_to_end_enabled:
                self.typewriter.skip_to_end()
                self._transition_to(DialogueState.WAITING)
        elif self.state == DialogueState.WAITING:
            if self._allow_input:
                self._transition_to(DialogueState.INPUT)
            else:
                if self.on_dialogue_complete:
                    self.on_dialogue_complete()
                else:
                    self.hide()

    def _transition_to(self, new_state: DialogueState):
        """Transition to a new state."""
        old_state = self.state
        self.state = new_state
        self.state_timer = 0.0

        # Handle state entry
        if new_state == DialogueState.APPEARING:
            self.slide_offset = self.config.box_height + 50
            self.target_slide = 0
            self.portrait.set_speaking(True)

        elif new_state == DialogueState.TYPING:
            self.portrait.set_speaking(True)

        elif new_state == DialogueState.WAITING:
            self.portrait.set_speaking(False)

        elif new_state == DialogueState.INPUT:
            self.portrait.set_speaking(False)
            self.input_field.set_active(True)
            self.input_field.clear()

        elif new_state == DialogueState.THINKING:
            self.portrait.set_speaking(False)

        elif new_state == DialogueState.DISAPPEARING:
            self.target_slide = self.config.box_height + 50
            self.portrait.set_speaking(False)
            self.input_field.set_active(False)

        elif new_state == DialogueState.HIDDEN:
            self.slide_offset = self.config.box_height + 50

    def _play_char_sound(self):
        """Play the character typing sound."""
        if self.on_char_sound:
            self.on_char_sound()

    def _handle_player_input(self, text: str):
        """Handle submitted player input."""
        if self.on_player_input:
            self.on_player_input(text)
            self._transition_to(DialogueState.THINKING)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle input events.

        Returns True if the event was consumed.
        """
        if self.state == DialogueState.HIDDEN:
            return False

        # Handle input field events
        if self.state == DialogueState.INPUT:
            if self.input_field.handle_event(event):
                return True

        # Handle skip/advance
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_z):
                if self.state != DialogueState.INPUT:
                    self.skip()
                    return True
            elif event.key == pygame.K_ESCAPE:
                if self.state == DialogueState.INPUT:
                    # Cancel input, go back to waiting
                    self._transition_to(DialogueState.WAITING)
                    return True

        # Handle mouse click to skip
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                if self.state in (DialogueState.TYPING, DialogueState.WAITING):
                    self.skip()
                    return True

        return False

    def update(self, dt: float):
        """Update the dialogue box state and animations."""
        if self.state == DialogueState.HIDDEN:
            return

        self.state_timer += dt

        # Update slide animation
        if self.slide_offset != self.target_slide:
            # Smooth slide
            diff = self.target_slide - self.slide_offset
            speed = abs(diff) * 8  # Faster when further
            if abs(diff) < 1:
                self.slide_offset = self.target_slide
            elif diff > 0:
                self.slide_offset = min(
                    self.target_slide,
                    self.slide_offset + speed * dt
                )
            else:
                self.slide_offset = max(
                    self.target_slide,
                    self.slide_offset - speed * dt
                )

        # State-specific updates
        if self.state == DialogueState.APPEARING:
            if self.slide_offset == 0:
                self._transition_to(DialogueState.TYPING)

        elif self.state == DialogueState.TYPING:
            self.typewriter.update(dt)
            if self.typewriter.is_complete:
                self._transition_to(DialogueState.WAITING)

        elif self.state == DialogueState.WAITING:
            self.continue_indicator.update(dt)

        elif self.state == DialogueState.INPUT:
            self.input_field.update(dt)

        elif self.state == DialogueState.THINKING:
            self.thinking.update(dt)

        elif self.state == DialogueState.DISAPPEARING:
            if self.slide_offset >= self.config.box_height + 50:
                self._transition_to(DialogueState.HIDDEN)

        # Always update portrait
        self.portrait.update(dt)

    def draw(self):
        """Draw the dialogue box and all components."""
        if self.state == DialogueState.HIDDEN:
            return

        # Apply slide offset to all positions
        offset_y = int(self.slide_offset)

        # Draw shadow
        shadow_rect = pygame.Rect(
            self.box_x + 5,
            self.box_y + 5 + offset_y,
            self.config.box_width,
            self.config.box_height
        )
        shadow_surface = pygame.Surface(
            (shadow_rect.width, shadow_rect.height),
            pygame.SRCALPHA
        )
        pygame.draw.rect(
            shadow_surface,
            (*self.colors['shadow'], 80),
            shadow_surface.get_rect(),
            border_radius=self.config.corner_radius
        )
        self.display_surface.blit(shadow_surface, shadow_rect.topleft)

        # Draw main box background
        box_rect = pygame.Rect(
            self.box_x,
            self.box_y + offset_y,
            self.config.box_width,
            self.config.box_height
        )
        pygame.draw.rect(
            self.display_surface,
            self.colors['bg'],
            box_rect,
            border_radius=self.config.corner_radius
        )

        # Draw border with subtle glow
        pygame.draw.rect(
            self.display_surface,
            self.colors['border'],
            box_rect,
            width=3,
            border_radius=self.config.corner_radius
        )

        # Draw name plate
        self.name_plate.draw(
            self.display_surface,
            self.name_x,
            self.name_y + offset_y
        )

        # Draw portrait
        self.portrait.draw(
            self.display_surface,
            self.portrait_x,
            self.portrait_y + offset_y
        )

        # Draw content based on state
        if self.state in (DialogueState.TYPING, DialogueState.WAITING):
            # Draw dialogue text
            self.typewriter.draw(
                self.display_surface,
                self.text_x,
                self.text_y + offset_y
            )

            # Draw continue indicator in waiting state
            if self.state == DialogueState.WAITING:
                self.continue_indicator.draw(
                    self.display_surface,
                    self.continue_x,
                    self.continue_y + offset_y
                )

        elif self.state == DialogueState.INPUT:
            # Draw the completed text above input
            self.typewriter.draw(
                self.display_surface,
                self.text_x,
                self.text_y + offset_y
            )

            # Draw input field
            self.input_field.draw(
                self.display_surface,
                self.text_x,
                self.input_y + offset_y,
                self.text_width
            )

        elif self.state == DialogueState.THINKING:
            # Draw thinking indicator
            self.thinking.draw(
                self.display_surface,
                self.text_x,
                self.text_y + offset_y + 20
            )

    def is_visible(self) -> bool:
        """Check if the dialogue box is currently visible."""
        return self.state != DialogueState.HIDDEN

    def is_waiting_for_input(self) -> bool:
        """Check if waiting for player input."""
        return self.state == DialogueState.INPUT

    def is_thinking(self) -> bool:
        """Check if showing thinking indicator."""
        return self.state == DialogueState.THINKING

    def get_screen_reader_text(self) -> List[str]:
        """Get accumulated screen reader text and clear it."""
        text = self.screen_reader_text.copy()
        self.screen_reader_text.clear()
        return text

    def set_accessibility_options(
        self,
        high_contrast: bool = False,
        large_font: bool = False
    ):
        """
        Update accessibility options.

        Args:
            high_contrast: Enable high contrast mode
            large_font: Enable larger font size
        """
        self.config.high_contrast_mode = high_contrast
        self.config.large_font_mode = large_font

        # Recreate text components with new settings
        self.typewriter = TypewriterText(self.config)
        self.typewriter.on_char_typed = self._play_char_sound

        self.input_field = InputField(self.config)
        self.input_field.on_submit = self._handle_player_input

        # If we have active text, re-set it
        if self.current_text:
            self.typewriter.set_text(self.current_text, self.text_width)


# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Lelock Dialogue Box Test")

    clock = pygame.time.Clock()

    # Create dialogue box
    dialogue = DialogueBox()

    # Test dialogues
    test_dialogues = [
        ("Mom", "Welcome home, little one! I've been waiting for you. How was your day exploring the village?"),
        ("Dad", "Hey there, champ! I heard you've been making friends. That's my kid! Always knew you had it in you."),
        ("Maple", "Oh! It's you again! I was just tending to the silicon berries. They're growing so well this season!"),
    ]
    current_dialogue_index = 0

    # Callbacks
    def on_complete():
        global current_dialogue_index
        current_dialogue_index = (current_dialogue_index + 1) % len(test_dialogues)
        name, text = test_dialogues[current_dialogue_index]
        dialogue.show_dialogue(name, text, allow_input=True)

    def on_input(text):
        print(f"Player said: {text}")
        # Simulate thinking, then show next dialogue
        dialogue.show_thinking(test_dialogues[current_dialogue_index][0])
        pygame.time.set_timer(pygame.USEREVENT + 1, 2000)  # Show response after 2s

    dialogue.on_dialogue_complete = on_complete
    dialogue.on_player_input = on_input

    # Start first dialogue
    name, text = test_dialogues[0]
    dialogue.show_dialogue(name, text, allow_input=True)

    running = True
    while running:
        dt = clock.tick(60) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_h:
                    # Test hide
                    dialogue.hide()
                elif event.key == pygame.K_s:
                    # Test show
                    name, text = test_dialogues[current_dialogue_index]
                    dialogue.show_dialogue(name, text, allow_input=True)
            elif event.type == pygame.USEREVENT + 1:
                # Timer fired - show response
                pygame.time.set_timer(pygame.USEREVENT + 1, 0)  # Cancel timer
                on_complete()

            dialogue.handle_event(event)

        # Update
        dialogue.update(dt)

        # Draw
        screen.fill(hex_to_rgb(COLORS['background']))

        # Draw some fake game content behind
        font = pygame.font.Font(None, 36)
        instructions = [
            "Dialogue Box Test",
            "",
            "SPACE/ENTER/CLICK: Advance dialogue",
            "H: Hide dialogue",
            "S: Show dialogue",
            "ESC: Quit",
            "",
            "When input is shown, type and press ENTER",
        ]
        for i, line in enumerate(instructions):
            text_surf = font.render(line, True, (200, 200, 200))
            screen.blit(text_surf, (50, 50 + i * 35))

        # Draw dialogue box
        dialogue.draw()

        pygame.display.flip()

    pygame.quit()


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Main class
    'DialogueBox',

    # Configuration
    'DialogueConfig',
    'DialogueState',

    # Components (for advanced use)
    'PortraitFrame',
    'NamePlate',
    'TypewriterText',
    'InputField',
    'ThinkingIndicator',
    'ContinueIndicator',

    # Helpers
    'hex_to_rgb',
]
