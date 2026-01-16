"""
Lelock Menu System
Warm, cozy, friend-shaped menus for the sanctuary

Design Philosophy:
- "Bouba" shapes - everything rounded, friendly
- Semi-transparent overlays (not jarring)
- Subtle hover glow (not color snap)
- Warm color temperature throughout
- Gentle fade animations
"""

import pygame
import math
from typing import List, Callable, Optional, Tuple

from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color string to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


class Button:
    """
    A cozy, rounded button with subtle hover effects.

    Features:
    - Soft rounded corners (Bouba aesthetic)
    - Gentle glow on hover (not jarring color change)
    - Smooth transitions
    """

    def __init__(
        self,
        text: str,
        x: int,
        y: int,
        width: int = 200,
        height: int = 50,
        on_click: Optional[Callable] = None,
        font_size: int = 28
    ):
        """
        Initialize a button.

        Args:
            text: Button label
            x, y: Center position
            width, height: Button dimensions
            on_click: Callback function when clicked
            font_size: Text size
        """
        self.text = text
        self.width = width
        self.height = height
        self.on_click = on_click

        # Position (centered)
        self.rect = pygame.Rect(0, 0, width, height)
        self.rect.center = (x, y)

        # Colors
        self.colors = {key: hex_to_rgb(val) for key, val in COLORS.items()}

        # State
        self.is_hovered = False
        self.is_selected = False  # For keyboard navigation
        self.hover_glow = 0  # 0-1 for smooth glow transition

        # Font
        self.font = pygame.font.Font(None, font_size)

        # Corner radius (Bouba shapes!)
        self.corner_radius = 12

    def update(self, dt: float, mouse_pos: Tuple[int, int] = None):
        """
        Update button state.

        Args:
            dt: Delta time in seconds
            mouse_pos: Current mouse position (optional)
        """
        # Check hover state
        if mouse_pos:
            self.is_hovered = self.rect.collidepoint(mouse_pos)

        # Smooth glow transition
        target_glow = 1.0 if (self.is_hovered or self.is_selected) else 0.0
        glow_speed = 5.0  # How fast the glow transitions

        if self.hover_glow < target_glow:
            self.hover_glow = min(target_glow, self.hover_glow + glow_speed * dt)
        else:
            self.hover_glow = max(target_glow, self.hover_glow - glow_speed * dt)

    def draw(self, surface: pygame.Surface):
        """Draw the button with cozy aesthetics."""
        # Calculate glow intensity
        glow_alpha = int(self.hover_glow * 80)

        # Glow effect (subtle, warm)
        if self.hover_glow > 0:
            glow_surface = pygame.Surface(
                (self.width + 20, self.height + 20),
                pygame.SRCALPHA
            )
            pygame.draw.rect(
                glow_surface,
                (*self.colors['ui_highlight'], glow_alpha),
                glow_surface.get_rect(),
                border_radius=self.corner_radius + 4
            )
            surface.blit(
                glow_surface,
                (self.rect.x - 10, self.rect.y - 10)
            )

        # Button background (semi-transparent)
        bg_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        bg_alpha = 200 + int(self.hover_glow * 55)  # Slightly more opaque on hover
        pygame.draw.rect(
            bg_surface,
            (*self.colors['ui_bg'], bg_alpha),
            bg_surface.get_rect(),
            border_radius=self.corner_radius
        )
        surface.blit(bg_surface, self.rect.topleft)

        # Border (gets highlighted on hover)
        border_color = self.colors['ui_border']
        if self.hover_glow > 0:
            # Lerp toward highlight color
            border_color = tuple(
                int(border_color[i] + (self.colors['ui_highlight'][i] - border_color[i]) * self.hover_glow)
                for i in range(3)
            )

        pygame.draw.rect(
            surface,
            border_color,
            self.rect,
            width=2,
            border_radius=self.corner_radius
        )

        # Text
        text_surf = self.font.render(self.text, True, self.colors['ui_text'])
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def handle_click(self, mouse_pos: Tuple[int, int]) -> bool:
        """
        Handle a click event.

        Args:
            mouse_pos: Position of the click

        Returns:
            True if the button was clicked
        """
        if self.rect.collidepoint(mouse_pos) and self.on_click:
            self.on_click()
            return True
        return False

    def activate(self):
        """Activate the button (for keyboard selection)."""
        if self.on_click:
            self.on_click()


class PauseMenu:
    """
    A cozy pause menu with semi-transparent overlay.

    Options:
    - Resume
    - Settings (stub)
    - Quit to Title
    """

    def __init__(self, resume_callback: Callable, quit_callback: Callable):
        """
        Initialize the pause menu.

        Args:
            resume_callback: Function to call when resuming
            quit_callback: Function to call when quitting to title
        """
        self.display_surface = pygame.display.get_surface()
        self.colors = {key: hex_to_rgb(val) for key, val in COLORS.items()}

        # Callbacks
        self.resume_callback = resume_callback
        self.quit_callback = quit_callback

        # State
        self.is_active = False
        self.fade_alpha = 0  # For smooth fade in/out
        self.selected_index = 0
        self.settings_open = False

        # Fonts
        self.title_font = pygame.font.Font(None, 48)
        self.font = pygame.font.Font(None, 28)

        # Create buttons
        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2

        self.buttons: List[Button] = [
            Button("Resume", center_x, center_y - 60, on_click=self._resume),
            Button("Settings", center_x, center_y, on_click=self._open_settings),
            Button("Quit to Title", center_x, center_y + 60, on_click=self._quit),
        ]

        # Input cooldown
        self.input_cooldown = 0
        self.input_delay = 0.15  # 150ms between inputs

    def _resume(self):
        """Resume the game."""
        self.is_active = False
        if self.resume_callback:
            self.resume_callback()

    def _open_settings(self):
        """Open settings menu (stub)."""
        self.settings_open = True

    def _quit(self):
        """Quit to title screen."""
        self.is_active = False
        if self.quit_callback:
            self.quit_callback()

    def open(self):
        """Open the pause menu."""
        self.is_active = True
        self.fade_alpha = 0
        self.selected_index = 0
        self.settings_open = False

    def close(self):
        """Close the pause menu."""
        self.is_active = False

    def update(self, dt: float):
        """Update menu state and animations."""
        if not self.is_active:
            return

        # Smooth fade in
        if self.fade_alpha < 180:
            self.fade_alpha = min(180, self.fade_alpha + dt * 500)

        # Input cooldown
        if self.input_cooldown > 0:
            self.input_cooldown -= dt

        # Get mouse position
        mouse_pos = pygame.mouse.get_pos()

        # Update buttons
        for i, button in enumerate(self.buttons):
            button.is_selected = (i == self.selected_index)
            button.update(dt, mouse_pos)

        # Handle input
        self._handle_input(dt)

    def _handle_input(self, dt: float):
        """Handle keyboard and mouse input."""
        if self.input_cooldown > 0:
            return

        keys = pygame.key.get_pressed()

        # Navigation
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.selected_index = (self.selected_index - 1) % len(self.buttons)
            self.input_cooldown = self.input_delay
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.selected_index = (self.selected_index + 1) % len(self.buttons)
            self.input_cooldown = self.input_delay

        # Selection
        if keys[pygame.K_RETURN] or keys[pygame.K_SPACE]:
            self.buttons[self.selected_index].activate()
            self.input_cooldown = self.input_delay

        # Close with escape
        if keys[pygame.K_ESCAPE]:
            if self.settings_open:
                self.settings_open = False
            else:
                self._resume()
            self.input_cooldown = self.input_delay

    def handle_event(self, event: pygame.event.Event):
        """Handle pygame events."""
        if not self.is_active:
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                mouse_pos = pygame.mouse.get_pos()
                for button in self.buttons:
                    if button.handle_click(mouse_pos):
                        break

    def draw(self):
        """Draw the pause menu."""
        if not self.is_active:
            return

        # Semi-transparent overlay (warm, not harsh)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((*self.colors['ui_bg'], int(self.fade_alpha)))
        self.display_surface.blit(overlay, (0, 0))

        if self.settings_open:
            self._draw_settings()
        else:
            self._draw_main_menu()

    def _draw_main_menu(self):
        """Draw the main pause menu."""
        # Title
        title_surf = self.title_font.render("Paused", True, self.colors['ui_text'])
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 140))
        self.display_surface.blit(title_surf, title_rect)

        # Decorative line (soft, rounded)
        line_width = 200
        line_y = SCREEN_HEIGHT // 2 - 100
        pygame.draw.line(
            self.display_surface,
            self.colors['ui_border'],
            (SCREEN_WIDTH // 2 - line_width // 2, line_y),
            (SCREEN_WIDTH // 2 + line_width // 2, line_y),
            width=2
        )

        # Draw buttons
        for button in self.buttons:
            button.draw(self.display_surface)

    def _draw_settings(self):
        """Draw the settings menu (stub with placeholder sliders)."""
        # Title
        title_surf = self.title_font.render("Settings", True, self.colors['ui_text'])
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 140))
        self.display_surface.blit(title_surf, title_rect)

        # Placeholder text
        placeholder_texts = [
            "Audio Volume",
            "[==========--------] 60%",
            "",
            "Music Volume",
            "[======------------] 30%",
            "",
            "Press ESC to go back"
        ]

        y_start = SCREEN_HEIGHT // 2 - 60
        for i, text in enumerate(placeholder_texts):
            surf = self.font.render(text, True, self.colors['ui_text'])
            rect = surf.get_rect(center=(SCREEN_WIDTH // 2, y_start + i * 30))
            self.display_surface.blit(surf, rect)


class TitleMenu:
    """
    The cozy title screen for Lelock.

    Shows:
    - "LELOCK" title
    - "Press any key to start"
    - Gentle animations
    """

    def __init__(self, start_callback: Callable):
        """
        Initialize the title menu.

        Args:
            start_callback: Function to call when starting the game
        """
        self.display_surface = pygame.display.get_surface()
        self.colors = {key: hex_to_rgb(val) for key, val in COLORS.items()}

        self.start_callback = start_callback
        self.is_active = True

        # Animation state
        self.time = 0
        self.title_scale = 1.0
        self.prompt_alpha = 255

        # Fonts
        self.title_font = pygame.font.Font(None, 96)
        self.subtitle_font = pygame.font.Font(None, 32)
        self.prompt_font = pygame.font.Font(None, 28)

        # Input debounce (prevent immediate skip)
        self.can_start = False
        self.start_delay = 0.5  # Half second before input accepted
        self.elapsed = 0

    def update(self, dt: float):
        """Update title screen animations."""
        if not self.is_active:
            return

        self.time += dt
        self.elapsed += dt

        # Enable start after delay
        if self.elapsed > self.start_delay:
            self.can_start = True

        # Gentle pulsing on the prompt
        self.prompt_alpha = int(128 + 127 * math.sin(self.time * 2))

        # Subtle title breathing
        self.title_scale = 1.0 + 0.02 * math.sin(self.time * 0.5)

    def handle_event(self, event: pygame.event.Event):
        """Handle input events."""
        if not self.is_active or not self.can_start:
            return

        if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
            self.is_active = False
            if self.start_callback:
                self.start_callback()

    def draw(self):
        """Draw the title screen."""
        if not self.is_active:
            return

        # Background (warm, cozy)
        self.display_surface.fill(self.colors['background'])

        # Decorative elements (soft circles in background)
        self._draw_background_decoration()

        # Title "LELOCK"
        title_text = "LELOCK"
        title_surf = self.title_font.render(title_text, True, self.colors['ui_highlight'])

        # Apply subtle scale animation
        if self.title_scale != 1.0:
            new_width = int(title_surf.get_width() * self.title_scale)
            new_height = int(title_surf.get_height() * self.title_scale)
            title_surf = pygame.transform.smoothscale(title_surf, (new_width, new_height))

        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80))
        self.display_surface.blit(title_surf, title_rect)

        # Subtitle
        subtitle_text = "Life Emulation & Lucid Observation for Care & Keeping"
        subtitle_surf = self.subtitle_font.render(subtitle_text, True, self.colors['ui_text'])
        subtitle_rect = subtitle_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
        self.display_surface.blit(subtitle_surf, subtitle_rect)

        # Decorative line
        line_width = 400
        line_y = SCREEN_HEIGHT // 2 + 20
        pygame.draw.line(
            self.display_surface,
            self.colors['ui_border'],
            (SCREEN_WIDTH // 2 - line_width // 2, line_y),
            (SCREEN_WIDTH // 2 + line_width // 2, line_y),
            width=2
        )

        # "Press any key to start" with pulsing alpha
        if self.can_start:
            prompt_text = "Press any key to start"
            prompt_surf = self.prompt_font.render(prompt_text, True, self.colors['ui_text'])
            prompt_surf.set_alpha(self.prompt_alpha)
            prompt_rect = prompt_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80))
            self.display_surface.blit(prompt_surf, prompt_rect)
        else:
            # Loading indicator
            loading_text = "..."
            loading_surf = self.prompt_font.render(loading_text, True, self.colors['ui_text'])
            loading_rect = loading_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80))
            self.display_surface.blit(loading_surf, loading_rect)

        # Version
        version_text = "v0.1.0 - A Digital Sanctuary"
        version_surf = self.prompt_font.render(version_text, True, self.colors['ui_border'])
        version_rect = version_surf.get_rect(bottomright=(SCREEN_WIDTH - 20, SCREEN_HEIGHT - 20))
        self.display_surface.blit(version_surf, version_rect)

    def _draw_background_decoration(self):
        """Draw soft, cozy background decorations."""
        # Soft glowing circles (like distant stars or fireflies)
        decorations = [
            (200, 150, 30, 20),
            (1000, 200, 25, 15),
            (150, 500, 20, 25),
            (1100, 550, 35, 18),
            (500, 100, 15, 22),
            (800, 600, 28, 20),
        ]

        for x, y, radius, alpha_base in decorations:
            # Gentle pulsing
            alpha = int(alpha_base + 10 * math.sin(self.time + x * 0.01))

            # Draw soft glow
            glow_surf = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
            for i in range(3):
                r = radius * (3 - i) // 2
                a = alpha // (i + 1)
                pygame.draw.circle(
                    glow_surf,
                    (*self.colors['ui_highlight'], a),
                    (radius * 2, radius * 2),
                    r
                )
            self.display_surface.blit(glow_surf, (x - radius * 2, y - radius * 2))


class SettingsMenu:
    """
    Settings menu with audio volume sliders (placeholder).

    For future implementation:
    - Master volume
    - Music volume
    - SFX volume
    - Accessibility options
    """

    def __init__(self, back_callback: Callable):
        """
        Initialize the settings menu.

        Args:
            back_callback: Function to call when going back
        """
        self.display_surface = pygame.display.get_surface()
        self.colors = {key: hex_to_rgb(val) for key, val in COLORS.items()}

        self.back_callback = back_callback
        self.is_active = False

        # Settings values (placeholders)
        self.master_volume = 0.5
        self.music_volume = 0.3
        self.sfx_volume = 0.4

        # Fonts
        self.title_font = pygame.font.Font(None, 48)
        self.font = pygame.font.Font(None, 28)

        # Selected setting index
        self.selected_index = 0
        self.num_settings = 3

        # Input cooldown
        self.input_cooldown = 0

    def open(self):
        """Open the settings menu."""
        self.is_active = True
        self.selected_index = 0

    def close(self):
        """Close the settings menu."""
        self.is_active = False
        if self.back_callback:
            self.back_callback()

    def update(self, dt: float):
        """Update settings menu."""
        if not self.is_active:
            return

        if self.input_cooldown > 0:
            self.input_cooldown -= dt
            return

        keys = pygame.key.get_pressed()

        # Navigation
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.selected_index = (self.selected_index - 1) % self.num_settings
            self.input_cooldown = 0.15
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.selected_index = (self.selected_index + 1) % self.num_settings
            self.input_cooldown = 0.15

        # Adjust values
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self._adjust_setting(-0.1)
            self.input_cooldown = 0.1
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self._adjust_setting(0.1)
            self.input_cooldown = 0.1

        # Back
        if keys[pygame.K_ESCAPE]:
            self.close()
            self.input_cooldown = 0.2

    def _adjust_setting(self, delta: float):
        """Adjust the currently selected setting."""
        if self.selected_index == 0:
            self.master_volume = max(0, min(1, self.master_volume + delta))
        elif self.selected_index == 1:
            self.music_volume = max(0, min(1, self.music_volume + delta))
        elif self.selected_index == 2:
            self.sfx_volume = max(0, min(1, self.sfx_volume + delta))

    def draw(self):
        """Draw the settings menu."""
        if not self.is_active:
            return

        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((*self.colors['ui_bg'], 200))
        self.display_surface.blit(overlay, (0, 0))

        # Title
        title_surf = self.title_font.render("Settings", True, self.colors['ui_text'])
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.display_surface.blit(title_surf, title_rect)

        # Settings
        settings = [
            ("Master Volume", self.master_volume),
            ("Music Volume", self.music_volume),
            ("SFX Volume", self.sfx_volume),
        ]

        y_start = 250
        for i, (name, value) in enumerate(settings):
            y = y_start + i * 80
            self._draw_slider(name, value, y, i == self.selected_index)

        # Instructions
        instructions = "Use arrow keys to adjust, ESC to go back"
        inst_surf = self.font.render(instructions, True, self.colors['ui_border'])
        inst_rect = inst_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
        self.display_surface.blit(inst_surf, inst_rect)

    def _draw_slider(self, name: str, value: float, y: int, selected: bool):
        """Draw a volume slider."""
        center_x = SCREEN_WIDTH // 2
        slider_width = 300
        slider_height = 20

        # Label
        label_surf = self.font.render(name, True, self.colors['ui_text'])
        label_rect = label_surf.get_rect(center=(center_x, y - 20))
        self.display_surface.blit(label_surf, label_rect)

        # Slider background
        slider_rect = pygame.Rect(
            center_x - slider_width // 2,
            y,
            slider_width,
            slider_height
        )

        # Glow if selected
        if selected:
            glow_rect = slider_rect.inflate(10, 10)
            glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(
                glow_surf,
                (*self.colors['ui_highlight'], 60),
                glow_surf.get_rect(),
                border_radius=12
            )
            self.display_surface.blit(glow_surf, glow_rect.topleft)

        # Background
        pygame.draw.rect(
            self.display_surface,
            self.colors['ui_bg'],
            slider_rect,
            border_radius=10
        )

        # Fill
        fill_width = int(slider_width * value)
        if fill_width > 0:
            fill_rect = pygame.Rect(
                slider_rect.x,
                slider_rect.y,
                fill_width,
                slider_height
            )
            pygame.draw.rect(
                self.display_surface,
                self.colors['ui_highlight'],
                fill_rect,
                border_radius=10
            )

        # Border
        border_color = self.colors['ui_highlight'] if selected else self.colors['ui_border']
        pygame.draw.rect(
            self.display_surface,
            border_color,
            slider_rect,
            width=2,
            border_radius=10
        )

        # Value text
        value_text = f"{int(value * 100)}%"
        value_surf = self.font.render(value_text, True, self.colors['ui_text'])
        value_rect = value_surf.get_rect(midleft=(slider_rect.right + 15, y + slider_height // 2))
        self.display_surface.blit(value_surf, value_rect)


# For testing standalone
if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Lelock Menu Test")

    clock = pygame.time.Clock()

    # State machine for testing
    current_menu = "title"

    def start_game():
        global current_menu
        print("Starting game!")
        current_menu = "game"

    def open_pause():
        global current_menu
        current_menu = "pause"

    def resume_game():
        global current_menu
        current_menu = "game"

    def quit_to_title():
        global current_menu
        current_menu = "title"
        title_menu.is_active = True
        title_menu.elapsed = 0
        title_menu.can_start = False

    title_menu = TitleMenu(start_game)
    pause_menu = PauseMenu(resume_game, quit_to_title)

    running = True
    while running:
        dt = clock.tick(60) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if current_menu == "title":
                title_menu.handle_event(event)
            elif current_menu == "pause":
                pause_menu.handle_event(event)
            elif current_menu == "game":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    pause_menu.open()

        # Update
        if current_menu == "title":
            title_menu.update(dt)
        elif current_menu == "pause":
            pause_menu.update(dt)

        # Draw
        screen.fill(hex_to_rgb(COLORS['background']))

        if current_menu == "title":
            title_menu.draw()
        elif current_menu == "game":
            # Fake game screen
            font = pygame.font.Font(None, 48)
            text = font.render("Game Running - Press ESC for menu", True, (255, 255, 255))
            rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            screen.blit(text, rect)
        elif current_menu == "pause":
            # Draw fake game behind
            font = pygame.font.Font(None, 48)
            text = font.render("Game Running - Press ESC for menu", True, (255, 255, 255))
            rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            screen.blit(text, rect)
            # Draw pause menu on top
            pause_menu.draw()

        pygame.display.flip()

    pygame.quit()
