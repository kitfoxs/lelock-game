"""
Lelock Camera System
Smooth, cozy camera following that creates safety and comfort.

The camera is the player's window into the Mandala of Safety.
All movement is gentle - no jarring snaps, no disorienting jumps.
"""

import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, LAYERS


class CameraGroup(pygame.sprite.Group):
    """
    Custom sprite group with camera offset and layer-based rendering.

    Design Philosophy:
    - Smooth lerp following (not instant snap) for comfort
    - Camera boundaries prevent showing void outside map
    - Layer-sorted rendering with Y-sorting within layers
    - The camera is like a gentle friend guiding your view
    """

    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()

        # Camera offset (where the camera is looking)
        self.offset = pygame.math.Vector2()

        # Target offset for smooth lerping
        self.target_offset = pygame.math.Vector2()

        # Lerp speed (lower = smoother but slower)
        # 5.0 feels cozy - not too snappy, not too floaty
        self.lerp_speed = 5.0

        # Map boundaries (set by level when map loads)
        self.map_width = 0
        self.map_height = 0
        self.boundaries_enabled = False

    def set_map_bounds(self, width: int, height: int):
        """
        Set the map boundaries to prevent camera from showing void.
        Called by Level after loading the Tiled map.

        Args:
            width: Map width in pixels
            height: Map height in pixels
        """
        self.map_width = width
        self.map_height = height
        self.boundaries_enabled = True

    def _clamp_offset(self, offset: pygame.math.Vector2) -> pygame.math.Vector2:
        """
        Clamp offset to keep camera within map boundaries.

        If map is smaller than screen, center it instead.
        No void, no emptiness - only the sanctuary.
        """
        if not self.boundaries_enabled:
            return offset

        clamped = pygame.math.Vector2(offset)

        # Horizontal clamping
        if self.map_width <= SCREEN_WIDTH:
            # Map fits in screen - center it
            clamped.x = (self.map_width - SCREEN_WIDTH) / 2
        else:
            # Clamp to map edges
            clamped.x = max(0, min(clamped.x, self.map_width - SCREEN_WIDTH))

        # Vertical clamping
        if self.map_height <= SCREEN_HEIGHT:
            # Map fits in screen - center it
            clamped.y = (self.map_height - SCREEN_HEIGHT) / 2
        else:
            # Clamp to map edges
            clamped.y = max(0, min(clamped.y, self.map_height - SCREEN_HEIGHT))

        return clamped

    def update_camera(self, target: pygame.sprite.Sprite, dt: float):
        """
        Smoothly update camera position to follow target.

        Uses linear interpolation for gentle, cozy movement.
        The camera doesn't chase - it accompanies.

        Args:
            target: Sprite to follow (usually player)
            dt: Delta time for frame-independent movement
        """
        # Calculate where camera should look (centered on target)
        self.target_offset.x = target.rect.centerx - SCREEN_WIDTH / 2
        self.target_offset.y = target.rect.centery - SCREEN_HEIGHT / 2

        # Apply boundary clamping to target
        self.target_offset = self._clamp_offset(self.target_offset)

        # Smooth lerp toward target
        # Formula: current + (target - current) * speed * dt
        lerp_factor = min(1.0, self.lerp_speed * dt)  # Clamp to prevent overshooting

        self.offset.x += (self.target_offset.x - self.offset.x) * lerp_factor
        self.offset.y += (self.target_offset.y - self.offset.y) * lerp_factor

        # Final boundary check (for safety)
        self.offset = self._clamp_offset(self.offset)

    def snap_to_target(self, target: pygame.sprite.Sprite):
        """
        Instantly snap camera to target (use sparingly).

        Only for level transitions or initial spawn.
        Even then, consider a fade transition to soften it.

        Args:
            target: Sprite to snap to
        """
        self.offset.x = target.rect.centerx - SCREEN_WIDTH / 2
        self.offset.y = target.rect.centery - SCREEN_HEIGHT / 2
        self.offset = self._clamp_offset(self.offset)
        self.target_offset = pygame.math.Vector2(self.offset)

    def custom_draw(self, player: pygame.sprite.Sprite, dt: float = None):
        """
        Draw all sprites with camera offset and layer sorting.

        Renders in layer order (water -> ground -> main -> ui).
        Within each layer, Y-sorts for proper depth (things lower on screen draw on top).

        Args:
            player: The player sprite (for camera following)
            dt: Delta time (optional, for camera smoothing)
        """
        # Update camera position (smooth follow)
        if dt is not None:
            self.update_camera(player, dt)
        else:
            # Fallback: instant follow if no dt provided
            self.target_offset.x = player.rect.centerx - SCREEN_WIDTH / 2
            self.target_offset.y = player.rect.centery - SCREEN_HEIGHT / 2
            self.offset = self._clamp_offset(self.target_offset)

        # Get all layer values and sort them
        layer_values = sorted(LAYERS.values())

        # Draw sprites layer by layer
        for layer in layer_values:
            # Get all sprites in this layer, sorted by Y position
            layer_sprites = [
                sprite for sprite in self.sprites()
                if hasattr(sprite, 'z') and sprite.z == layer
            ]

            # Y-sort within layer (lower Y = drawn first = appears behind)
            for sprite in sorted(layer_sprites, key=lambda s: s.rect.centery):
                # Calculate offset position
                offset_rect = sprite.rect.copy()
                offset_rect.center = (
                    sprite.rect.centerx - self.offset.x,
                    sprite.rect.centery - self.offset.y
                )

                # Only draw if on screen (basic culling for performance)
                if self._is_on_screen(offset_rect):
                    self.display_surface.blit(sprite.image, offset_rect)

    def _is_on_screen(self, rect: pygame.Rect) -> bool:
        """
        Check if a rect is visible on screen.

        Basic culling to skip drawing off-screen sprites.
        Small performance optimization for larger maps.
        """
        screen_rect = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        return rect.colliderect(screen_rect)

    def screen_to_world(self, screen_pos: tuple) -> pygame.math.Vector2:
        """
        Convert screen coordinates to world coordinates.

        Useful for mouse interactions, click detection, etc.

        Args:
            screen_pos: (x, y) position on screen

        Returns:
            Vector2 position in world space
        """
        return pygame.math.Vector2(
            screen_pos[0] + self.offset.x,
            screen_pos[1] + self.offset.y
        )

    def world_to_screen(self, world_pos: tuple) -> pygame.math.Vector2:
        """
        Convert world coordinates to screen coordinates.

        Useful for UI elements that need to point at world objects.

        Args:
            world_pos: (x, y) position in world

        Returns:
            Vector2 position on screen
        """
        return pygame.math.Vector2(
            world_pos[0] - self.offset.x,
            world_pos[1] - self.offset.y
        )
