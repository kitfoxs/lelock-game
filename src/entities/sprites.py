"""
Lelock Base Sprite Classes
L.E.L.O.C.K. - Life Emulation & Lucid Observation for Care & Keeping

Base sprite classes for all game objects.
Everything in the game world inherits from these.
"""

import pygame
from typing import List, Optional, Tuple, Union
from settings import LAYERS


class GenericSprite(pygame.sprite.Sprite):
    """
    Base sprite class for all static game objects.

    Every sprite in Lelock has:
    - A position and image
    - A z-layer for rendering order
    - A hitbox for collisions (separate from image rect)
    """

    def __init__(
        self,
        pos: Tuple[int, int],
        surface: pygame.Surface,
        groups: Union[pygame.sprite.Group, List[pygame.sprite.Group]],
        z: int = LAYERS['main']
    ):
        super().__init__(groups)

        self.image = surface
        self.rect = self.image.get_rect(topleft=pos)
        self.z = z

        # Hitbox is smaller than image rect for better collision feel
        # Default: 80% width, 25% height (bottom portion)
        self.hitbox = self.rect.copy().inflate(
            -self.rect.width * 0.2,
            -self.rect.height * 0.75
        )


class AnimatedSprite(GenericSprite):
    """
    Sprite with frame-based animation support.

    Cycles through frames based on delta time.
    Supports multiple animation states (e.g., 'idle_down', 'walk_up').
    """

    def __init__(
        self,
        pos: Tuple[int, int],
        frames: Union[List[pygame.Surface], dict],
        groups: Union[pygame.sprite.Group, List[pygame.sprite.Group]],
        z: int = LAYERS['main'],
        animation_speed: float = 4.0
    ):
        # Handle both single frame list and animation dict
        if isinstance(frames, dict):
            self.animations = frames
            self.status = list(frames.keys())[0]
            initial_frame = frames[self.status][0] if frames[self.status] else pygame.Surface((32, 32))
        else:
            self.animations = {'default': frames}
            self.status = 'default'
            initial_frame = frames[0] if frames else pygame.Surface((32, 32))

        super().__init__(pos, initial_frame, groups, z)

        self.frame_index = 0.0
        self.animation_speed = animation_speed

    def animate(self, dt: float) -> None:
        """Advance animation frame based on delta time."""
        current_animation = self.animations.get(self.status, [])

        if not current_animation:
            return

        self.frame_index += self.animation_speed * dt

        if self.frame_index >= len(current_animation):
            self.frame_index = 0.0

        self.image = current_animation[int(self.frame_index)]

    def set_animation(self, status: str, reset_frame: bool = False) -> None:
        """Change the current animation state."""
        if status in self.animations:
            if self.status != status or reset_frame:
                self.status = status
                if reset_frame:
                    self.frame_index = 0.0

    def update(self, dt: float) -> None:
        """Update animation each frame."""
        self.animate(dt)


class InteractionSprite(GenericSprite):
    """
    Invisible sprite marking interactable areas.

    Used for things like:
    - Bed (sleep interaction)
    - Doors (room transition)
    - NPCs (dialogue trigger)
    - Terminals (digital world access)
    """

    def __init__(
        self,
        pos: Tuple[int, int],
        size: Tuple[int, int],
        groups: Union[pygame.sprite.Group, List[pygame.sprite.Group]],
        name: str,
        interaction_type: str = 'generic'
    ):
        # Create invisible surface for the interaction zone
        surface = pygame.Surface(size, pygame.SRCALPHA)
        super().__init__(pos, surface, groups)

        # Interaction zone uses full rect as hitbox
        self.hitbox = self.rect.copy()

        # Metadata for interaction handling
        self.name = name
        self.interaction_type = interaction_type

        # Optional callback or data
        self.data = {}

    def set_data(self, key: str, value) -> None:
        """Store arbitrary data for interaction handling."""
        self.data[key] = value

    def get_data(self, key: str, default=None):
        """Retrieve stored data."""
        return self.data.get(key, default)


class ParticleSprite(GenericSprite):
    """
    Temporary visual effect sprite that auto-destroys.

    Used for:
    - Tool use effects
    - Item pickup sparkles
    - Transition effects
    """

    def __init__(
        self,
        pos: Tuple[int, int],
        surface: pygame.Surface,
        groups: Union[pygame.sprite.Group, List[pygame.sprite.Group]],
        z: int = LAYERS['main'],
        duration_ms: int = 200,
        fade: bool = True
    ):
        super().__init__(pos, surface, groups, z)

        self.start_time = pygame.time.get_ticks()
        self.duration = duration_ms
        self.fade = fade

        # Create white flash version for impact effect
        if fade:
            self.original_image = self.image.copy()
            mask_surf = pygame.mask.from_surface(self.image)
            self.image = mask_surf.to_surface()
            self.image.set_colorkey((0, 0, 0))

    def update(self, dt: float) -> None:
        """Check if particle should be destroyed."""
        elapsed = pygame.time.get_ticks() - self.start_time

        if elapsed >= self.duration:
            self.kill()
            return

        # Optional: fade out over time
        if self.fade and hasattr(self, 'original_image'):
            alpha = 255 * (1 - elapsed / self.duration)
            self.image.set_alpha(int(alpha))


class WaterSprite(AnimatedSprite):
    """
    Animated water tile with gentle wave motion.

    Separate class for water to ensure proper z-layer
    and potentially add reflection effects later.
    """

    def __init__(
        self,
        pos: Tuple[int, int],
        frames: List[pygame.Surface],
        groups: Union[pygame.sprite.Group, List[pygame.sprite.Group]]
    ):
        super().__init__(
            pos=pos,
            frames=frames,
            groups=groups,
            z=LAYERS['water'],
            animation_speed=5.0
        )

        # Water doesn't need collision
        self.hitbox = pygame.Rect(0, 0, 0, 0)


class CollisionSprite(GenericSprite):
    """
    Invisible collision-only sprite.

    Used for:
    - Wall boundaries
    - Furniture collision boxes
    - Invisible barriers
    """

    def __init__(
        self,
        pos: Tuple[int, int],
        size: Tuple[int, int],
        groups: Union[pygame.sprite.Group, List[pygame.sprite.Group]]
    ):
        # Create invisible surface
        surface = pygame.Surface(size, pygame.SRCALPHA)
        super().__init__(pos, surface, groups)

        # Full rect is the collision area
        self.hitbox = self.rect.copy()
