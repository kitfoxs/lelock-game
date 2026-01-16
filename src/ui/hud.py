"""
Lelock HUD (Heads-Up Display)
Warm, cozy, friend-shaped UI for player status

Design Philosophy:
- "Bouba" shapes - everything rounded, friendly
- Warm color temperature (2700K-3000K feel)
- No red for warnings - use ui_warning (orange)
- Soft, bubbly interfaces like a warm blanket
"""

import pygame
from typing import Optional, Tuple
import os

# Import from parent directory
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color string to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


class HUD:
    """
    Heads-Up Display for Lelock.

    Shows:
    - Health bar (soft rounded corners)
    - Energy bar
    - Current tool/item indicator
    - Money display
    - Time of day indicator

    All visuals use warm, cozy aesthetics.
    """

    def __init__(self, player=None):
        """
        Initialize the HUD.

        Args:
            player: Player object with health, energy, money, etc.
                   Can be None for testing/standalone mode.
        """
        self.display_surface = pygame.display.get_surface()
        self.player = player

        # Convert colors from hex to RGB
        self.colors = {key: hex_to_rgb(val) for key, val in COLORS.items()}

        # Font setup (will use system font if custom not available)
        self.font_large = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)

        # HUD positioning (top-left corner, with padding)
        self.padding = 20
        self.bar_width = 200
        self.bar_height = 20
        self.bar_spacing = 8
        self.corner_radius = 10  # Bouba shapes - nice and rounded!

        # Animation state for gentle pulsing
        self.pulse_timer = 0
        self.pulse_speed = 2  # Slow, calming pulse

        # Tool/item display
        self.tool_icon_size = 48
        self.tool_bg_size = 64

        # Money display position (top-right)
        self.money_x = SCREEN_WIDTH - self.padding - 120
        self.money_y = self.padding

        # Time display position (top-center)
        self.time_x = SCREEN_WIDTH // 2
        self.time_y = self.padding

        # Default values if no player
        self._default_health = 100
        self._default_max_health = 100
        self._default_energy = 80
        self._default_max_energy = 100
        self._default_money = 500
        self._default_tool = "Hoe"
        self._default_time = "Morning"

    def _get_player_stat(self, stat: str, default):
        """Safely get a player stat or return default."""
        if self.player is None:
            return default
        return getattr(self.player, stat, default)

    def _draw_rounded_bar(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        fill_percent: float,
        fill_color: Tuple[int, int, int],
        bg_color: Tuple[int, int, int],
        border_color: Tuple[int, int, int],
        glow: bool = False
    ):
        """
        Draw a soft, rounded progress bar.

        Args:
            x, y: Top-left position
            width, height: Bar dimensions
            fill_percent: 0.0 to 1.0 fill amount
            fill_color: RGB tuple for the fill
            bg_color: RGB tuple for the background
            border_color: RGB tuple for the border
            glow: Whether to add a subtle glow effect
        """
        # Background (soft rounded rectangle)
        bg_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(
            self.display_surface,
            bg_color,
            bg_rect,
            border_radius=self.corner_radius
        )

        # Fill (also rounded, clips to prevent overflow)
        fill_width = max(self.corner_radius * 2, int(width * fill_percent))
        if fill_percent > 0:
            fill_rect = pygame.Rect(x, y, fill_width, height)
            pygame.draw.rect(
                self.display_surface,
                fill_color,
                fill_rect,
                border_radius=self.corner_radius
            )

        # Subtle glow effect when low (but not red - orange!)
        if glow and fill_percent < 0.25:
            import math
            pulse = abs(math.sin(self.pulse_timer * 0.05)) * 50
            glow_color = (
                min(255, fill_color[0] + int(pulse)),
                min(255, fill_color[1] + int(pulse * 0.5)),
                fill_color[2]
            )
            glow_rect = pygame.Rect(x - 2, y - 2, fill_width + 4, height + 4)
            glow_surface = pygame.Surface((fill_width + 4, height + 4), pygame.SRCALPHA)
            pygame.draw.rect(
                glow_surface,
                (*glow_color, 100),
                glow_surface.get_rect(),
                border_radius=self.corner_radius + 2
            )
            self.display_surface.blit(glow_surface, (x - 2, y - 2))

        # Border (soft, friendly)
        pygame.draw.rect(
            self.display_surface,
            border_color,
            bg_rect,
            width=2,
            border_radius=self.corner_radius
        )

    def _draw_health_bar(self):
        """Draw the health bar with warm, cozy aesthetics."""
        health = self._get_player_stat('health', self._default_health)
        max_health = self._get_player_stat('max_health', self._default_max_health)
        fill_percent = health / max_health if max_health > 0 else 0

        # Position
        x = self.padding
        y = self.padding

        # Label
        label = self.font_small.render("HP", True, self.colors['ui_text'])
        self.display_surface.blit(label, (x, y - 18))

        # Health uses a warm green (success color) - never red!
        fill_color = self.colors['ui_success']
        if fill_percent < 0.25:
            fill_color = self.colors['ui_warning']  # Orange, not red!

        self._draw_rounded_bar(
            x, y,
            self.bar_width, self.bar_height,
            fill_percent,
            fill_color,
            self.colors['ui_bg'],
            self.colors['ui_border'],
            glow=(fill_percent < 0.25)
        )

        # Health text overlay
        health_text = f"{int(health)}/{int(max_health)}"
        text_surf = self.font_small.render(health_text, True, self.colors['ui_text'])
        text_rect = text_surf.get_rect(center=(x + self.bar_width // 2, y + self.bar_height // 2))
        self.display_surface.blit(text_surf, text_rect)

    def _draw_energy_bar(self):
        """Draw the energy bar below health."""
        energy = self._get_player_stat('energy', self._default_energy)
        max_energy = self._get_player_stat('max_energy', self._default_max_energy)
        fill_percent = energy / max_energy if max_energy > 0 else 0

        # Position (below health bar)
        x = self.padding
        y = self.padding + self.bar_height + self.bar_spacing + 18  # +18 for label

        # Label
        label = self.font_small.render("Energy", True, self.colors['ui_text'])
        self.display_surface.blit(label, (x, y - 18))

        # Energy uses highlight color (warm gold)
        fill_color = self.colors['ui_highlight']
        if fill_percent < 0.25:
            fill_color = self.colors['ui_warning']

        self._draw_rounded_bar(
            x, y,
            self.bar_width, self.bar_height,
            fill_percent,
            fill_color,
            self.colors['ui_bg'],
            self.colors['ui_border'],
            glow=(fill_percent < 0.25)
        )

        # Energy text overlay
        energy_text = f"{int(energy)}/{int(max_energy)}"
        text_surf = self.font_small.render(energy_text, True, self.colors['ui_text'])
        text_rect = text_surf.get_rect(center=(x + self.bar_width // 2, y + self.bar_height // 2))
        self.display_surface.blit(text_surf, text_rect)

    def _draw_tool_indicator(self):
        """Draw the current tool/item indicator."""
        tool = self._get_player_stat('selected_tool', self._default_tool)

        # Position (below energy bar)
        x = self.padding
        y = self.padding + (self.bar_height + self.bar_spacing + 18) * 2 + 10

        # Background bubble (Bouba shape!)
        bg_rect = pygame.Rect(x, y, self.tool_bg_size, self.tool_bg_size)

        # Semi-transparent background
        bg_surface = pygame.Surface((self.tool_bg_size, self.tool_bg_size), pygame.SRCALPHA)
        pygame.draw.rect(
            bg_surface,
            (*self.colors['ui_bg'], 200),
            bg_surface.get_rect(),
            border_radius=12
        )
        self.display_surface.blit(bg_surface, (x, y))

        # Border
        pygame.draw.rect(
            self.display_surface,
            self.colors['ui_border'],
            bg_rect,
            width=2,
            border_radius=12
        )

        # Tool name (centered in the bubble)
        tool_text = self.font_small.render(tool[:4], True, self.colors['ui_text'])
        text_rect = tool_text.get_rect(center=(x + self.tool_bg_size // 2, y + self.tool_bg_size // 2))
        self.display_surface.blit(tool_text, text_rect)

        # Label below
        label = self.font_small.render("Tool", True, self.colors['ui_text'])
        self.display_surface.blit(label, (x + 10, y + self.tool_bg_size + 4))

    def _draw_money_display(self):
        """Draw the money display with a cute coin aesthetic."""
        money = self._get_player_stat('money', self._default_money)

        # Background bubble
        bg_width = 120
        bg_height = 40
        bg_rect = pygame.Rect(self.money_x, self.money_y, bg_width, bg_height)

        # Semi-transparent background
        bg_surface = pygame.Surface((bg_width, bg_height), pygame.SRCALPHA)
        pygame.draw.rect(
            bg_surface,
            (*self.colors['ui_bg'], 200),
            bg_surface.get_rect(),
            border_radius=self.corner_radius
        )
        self.display_surface.blit(bg_surface, (self.money_x, self.money_y))

        # Border
        pygame.draw.rect(
            self.display_surface,
            self.colors['ui_border'],
            bg_rect,
            width=2,
            border_radius=self.corner_radius
        )

        # Coin symbol (little circle)
        coin_x = self.money_x + 15
        coin_y = self.money_y + bg_height // 2
        pygame.draw.circle(
            self.display_surface,
            self.colors['ui_highlight'],
            (coin_x, coin_y),
            10
        )
        pygame.draw.circle(
            self.display_surface,
            self.colors['ui_border'],
            (coin_x, coin_y),
            10,
            width=2
        )

        # Money text
        money_text = f"{money:,}"
        text_surf = self.font_large.render(money_text, True, self.colors['ui_text'])
        text_rect = text_surf.get_rect(midleft=(coin_x + 18, coin_y))
        self.display_surface.blit(text_surf, text_rect)

    def _draw_time_indicator(self):
        """Draw the time of day indicator (placeholder)."""
        time_of_day = self._get_player_stat('time_of_day', self._default_time)

        # Background bubble (centered at top)
        bg_width = 140
        bg_height = 36
        x = self.time_x - bg_width // 2
        y = self.time_y

        bg_rect = pygame.Rect(x, y, bg_width, bg_height)

        # Semi-transparent background
        bg_surface = pygame.Surface((bg_width, bg_height), pygame.SRCALPHA)
        pygame.draw.rect(
            bg_surface,
            (*self.colors['ui_bg'], 200),
            bg_surface.get_rect(),
            border_radius=self.corner_radius
        )
        self.display_surface.blit(bg_surface, (x, y))

        # Border
        pygame.draw.rect(
            self.display_surface,
            self.colors['ui_border'],
            bg_rect,
            width=2,
            border_radius=self.corner_radius
        )

        # Time icon (sun/moon based on time)
        icon_x = x + 20
        icon_y = y + bg_height // 2

        if time_of_day in ["Morning", "Afternoon", "Day"]:
            # Sun icon (warm gold)
            pygame.draw.circle(
                self.display_surface,
                self.colors['ui_highlight'],
                (icon_x, icon_y),
                8
            )
        else:
            # Moon icon (soft blue-white)
            pygame.draw.circle(
                self.display_surface,
                self.colors['ui_text'],
                (icon_x, icon_y),
                8
            )

        # Time text
        text_surf = self.font_small.render(time_of_day, True, self.colors['ui_text'])
        text_rect = text_surf.get_rect(midleft=(icon_x + 15, icon_y))
        self.display_surface.blit(text_surf, text_rect)

    def update(self, dt: float = 0.016):
        """
        Update HUD animations.

        Args:
            dt: Delta time in seconds (default ~60fps)
        """
        self.pulse_timer += dt * 60  # Normalize to 60fps equivalent

    def draw(self):
        """Draw all HUD elements."""
        self._draw_health_bar()
        self._draw_energy_bar()
        self._draw_tool_indicator()
        self._draw_money_display()
        self._draw_time_indicator()

    def display(self):
        """Alias for draw() for compatibility with skeleton code."""
        self.draw()


# For testing standalone
if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Lelock HUD Test")

    clock = pygame.time.Clock()
    hud = HUD()

    # Test variables
    test_health = 75
    test_energy = 50

    running = True
    while running:
        dt = clock.tick(60) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                # Test health/energy changes
                elif event.key == pygame.K_UP:
                    hud._default_health = min(100, hud._default_health + 10)
                elif event.key == pygame.K_DOWN:
                    hud._default_health = max(0, hud._default_health - 10)
                elif event.key == pygame.K_LEFT:
                    hud._default_energy = max(0, hud._default_energy - 10)
                elif event.key == pygame.K_RIGHT:
                    hud._default_energy = min(100, hud._default_energy + 10)

        # Clear with background color
        screen.fill(hex_to_rgb(COLORS['background']))

        # Update and draw HUD
        hud.update(dt)
        hud.draw()

        # Instructions
        font = pygame.font.Font(None, 24)
        instructions = [
            "Arrow keys: Adjust health (up/down) and energy (left/right)",
            "ESC: Quit"
        ]
        for i, text in enumerate(instructions):
            surf = font.render(text, True, (255, 255, 255))
            screen.blit(surf, (20, SCREEN_HEIGHT - 60 + i * 25))

        pygame.display.flip()

    pygame.quit()
