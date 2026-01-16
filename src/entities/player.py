"""
Lelock Player Character
L.E.L.O.C.K. - Life Emulation & Lucid Observation for Care & Keeping

The player - a child in a cozy world that exists to care for them.
No death. No failure. Just growth and comfort.
"""

import os
import pygame
from typing import Dict, List, Optional, Tuple, Callable
from pygame.math import Vector2

from settings import (
    LAYERS, PLAYER_SPEED, PLAYER_TOOL_OFFSET, CLASSES
)


class Timer:
    """Simple cooldown timer for actions."""

    def __init__(self, duration_ms: int, callback: Optional[Callable] = None):
        self.duration = duration_ms
        self.callback = callback
        self.start_time = 0
        self.active = False

    def activate(self) -> None:
        """Start the timer."""
        self.active = True
        self.start_time = pygame.time.get_ticks()

    def deactivate(self) -> None:
        """Stop the timer."""
        self.active = False
        self.start_time = 0

    def update(self) -> None:
        """Check timer and fire callback if expired."""
        if self.active:
            current_time = pygame.time.get_ticks()
            if current_time - self.start_time >= self.duration:
                if self.callback:
                    self.callback()
                self.deactivate()


def import_folder(path: str) -> List[pygame.Surface]:
    """Import all images from a folder and return as list of surfaces."""
    surface_list = []

    if not os.path.exists(path):
        # Return a placeholder if folder doesn't exist
        placeholder = pygame.Surface((48, 64), pygame.SRCALPHA)
        pygame.draw.ellipse(placeholder, (100, 150, 200), (8, 12, 32, 48))
        return [placeholder]

    for _, __, img_files in os.walk(path):
        for image in sorted(img_files):  # Sort for consistent frame order
            if image.endswith(('.png', '.jpg', '.jpeg')):
                full_path = os.path.join(path, image)
                image_surf = pygame.image.load(full_path).convert_alpha()
                surface_list.append(image_surf)

    # Return placeholder if no images found
    if not surface_list:
        placeholder = pygame.Surface((48, 64), pygame.SRCALPHA)
        pygame.draw.ellipse(placeholder, (100, 150, 200), (8, 12, 32, 48))
        return [placeholder]

    return surface_list


class Player(pygame.sprite.Sprite):
    """
    The player character in Lelock.

    Features:
    - 8-directional movement (WASD/Arrow keys)
    - Tool system for farming/interaction
    - Stats: health, energy, money
    - Class system (10 classes)
    - CANNOT DIE - only faints and goes home to Mom's soup

    The world exists to care for the player.
    This is a sanctuary.
    """

    def __init__(
        self,
        pos: Tuple[int, int],
        groups: pygame.sprite.Group,
        collision_sprites: pygame.sprite.Group,
        interaction_sprites: Optional[pygame.sprite.Group] = None,
        class_type: str = 'gardener'
    ):
        super().__init__(groups)

        # Load character sprites
        self.import_assets()

        # Animation state
        self.status = 'down'
        self.frame_index = 0

        # Setup image and rect from loaded animations
        self.image = self.animations[self.status][self.frame_index]
        self.rect = self.image.get_rect(center=pos)
        self.z = LAYERS['main']

        # Position tracking (float precision for smooth movement)
        self.pos = Vector2(self.rect.center)
        self.direction = Vector2(0, 0)
        self.speed = PLAYER_SPEED

        # Collision
        self.collision_sprites = collision_sprites
        self.interaction_sprites = interaction_sprites or pygame.sprite.Group()
        # Hitbox smaller than sprite for better feel (matches skeleton proportions)
        self.hitbox = self.rect.copy().inflate(-126, -70)

        # Status tracking
        self.facing_direction = 'down'
        self.is_moving = False
        self.using_tool = False
        self.sleeping = False

        # SAFETY: Player cannot die, only faint
        self.fainted = False

        # -----------------------------
        # PLAYER STATS
        # -----------------------------
        self.max_health = 100
        self.health = self.max_health

        self.max_energy = 100
        self.energy = self.max_energy

        self.money = 200  # Starting gold

        # -----------------------------
        # CLASS SYSTEM
        # -----------------------------
        self.class_type = class_type
        self.class_data = CLASSES.get(class_type, CLASSES['gardener'])

        # -----------------------------
        # TOOL SYSTEM
        # -----------------------------
        self.tools = ['hoe', 'axe', 'water']
        self.tool_index = 0
        self.selected_tool = self.tools[self.tool_index]
        self.target_pos = Vector2(0, 0)

        # Seeds for planting
        self.seeds = ['copper_wheat', 'silicon_berries']
        self.seed_index = 0
        self.selected_seed = self.seeds[self.seed_index]

        # -----------------------------
        # INVENTORY (basic for now)
        # -----------------------------
        self.item_inventory: Dict[str, int] = {
            'wood': 0,
            'stone': 0,
            'copper_wheat': 0,
            'silicon_berries': 0,
        }
        self.seed_inventory: Dict[str, int] = {
            'copper_wheat': 5,
            'silicon_berries': 5,
        }

        # -----------------------------
        # TIMERS (cooldowns)
        # -----------------------------
        self.timers = {
            'tool use': Timer(350, self._on_tool_use_complete),
            'tool switch': Timer(200),
            'seed use': Timer(350, self._on_seed_use_complete),
            'seed switch': Timer(200),
        }

    def import_assets(self) -> None:
        """Load all character animation sprites from disk."""
        # Animation dictionary matching skeleton's folder structure
        self.animations = {
            # Walking animations (direction only)
            'up': [], 'down': [], 'left': [], 'right': [],
            # Idle animations (direction_idle)
            'up_idle': [], 'down_idle': [], 'left_idle': [], 'right_idle': [],
            # Tool animations (direction_tool)
            'up_hoe': [], 'down_hoe': [], 'left_hoe': [], 'right_hoe': [],
            'up_axe': [], 'down_axe': [], 'left_axe': [], 'right_axe': [],
            'up_water': [], 'down_water': [], 'left_water': [], 'right_water': [],
        }

        # Get the path to graphics folder
        # From src/entities/player.py -> assets/graphics/character/
        current_dir = os.path.dirname(__file__)
        graphics_path = os.path.join(current_dir, '..', '..', 'assets', 'graphics', 'character')
        graphics_path = os.path.abspath(graphics_path)

        for animation in self.animations.keys():
            folder_path = os.path.join(graphics_path, animation)
            self.animations[animation] = import_folder(folder_path)

    def get_target_pos(self) -> None:
        """Calculate target position for tool use based on facing direction."""
        # Get base direction from status (e.g., 'down' from 'down_idle' or 'down_hoe')
        base_direction = self.status.split('_')[0]
        offset = PLAYER_TOOL_OFFSET.get(base_direction, Vector2(0, 50))
        self.target_pos = Vector2(self.rect.center) + offset

    # =========================================================================
    # INPUT HANDLING
    # =========================================================================

    def input(self) -> None:
        """Process keyboard input for movement and actions."""
        keys = pygame.key.get_pressed()

        # Can't move while using tool or sleeping
        if not self.timers['tool use'].active and not self.sleeping and not self.fainted:
            # Movement: WASD and Arrow Keys
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                self.direction.y = -1
                self.status = 'up'
            elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
                self.direction.y = 1
                self.status = 'down'
            else:
                self.direction.y = 0

            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                self.direction.x = -1
                self.status = 'left'
            elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                self.direction.x = 1
                self.status = 'right'
            else:
                self.direction.x = 0

            # Tool use (Space)
            if keys[pygame.K_SPACE]:
                self.timers['tool use'].activate()
                self.direction = Vector2(0, 0)
                self.frame_index = 0

            # Tool switch (Q)
            if keys[pygame.K_q] and not self.timers['tool switch'].active:
                self.timers['tool switch'].activate()
                self.tool_index = (self.tool_index + 1) % len(self.tools)
                self.selected_tool = self.tools[self.tool_index]

            # Seed use (Left Ctrl)
            if keys[pygame.K_LCTRL]:
                self.timers['seed use'].activate()
                self.direction = Vector2(0, 0)
                self.frame_index = 0

            # Seed switch (E)
            if keys[pygame.K_e] and not self.timers['seed switch'].active:
                self.timers['seed switch'].activate()
                self.seed_index = (self.seed_index + 1) % len(self.seeds)
                self.selected_seed = self.seeds[self.seed_index]

            # Interaction (Enter/Return)
            if keys[pygame.K_RETURN]:
                self._check_interaction()

    def _on_tool_use_complete(self) -> None:
        """Called when tool use timer expires."""
        self.using_tool = False
        # Actual tool effect would be triggered here via callback
        self._use_energy(5)

    def _on_seed_use_complete(self) -> None:
        """Called when seed planting timer expires."""
        if self.seed_inventory.get(self.selected_seed, 0) > 0:
            self.seed_inventory[self.selected_seed] -= 1
            self._use_energy(2)

    def _check_interaction(self) -> None:
        """Check for interactable objects and interact."""
        collided = pygame.sprite.spritecollide(
            self, self.interaction_sprites, False
        )
        if collided:
            interaction = collided[0]
            if hasattr(interaction, 'name'):
                if interaction.name == 'Bed':
                    self.status = 'left_idle'
                    self.sleeping = True
                elif interaction.name == 'Terminal':
                    pass  # Digital world toggle
                elif interaction.name == 'Trader':
                    pass  # Shop toggle

    # =========================================================================
    # STATUS & ANIMATION
    # =========================================================================

    def get_status(self) -> None:
        """Determine current animation status based on state."""
        # Add _idle suffix when not moving
        if self.direction.magnitude() == 0:
            self.status = self.status.split('_')[0] + '_idle'

        # Tool use overrides with tool name
        if self.timers['tool use'].active:
            self.status = self.status.split('_')[0] + '_' + self.selected_tool

    def animate(self, dt: float) -> None:
        """Advance animation frame based on delta time."""
        self.frame_index += 4 * dt

        if self.frame_index >= len(self.animations[self.status]):
            self.frame_index = 0

        self.image = self.animations[self.status][int(self.frame_index)]

    # =========================================================================
    # MOVEMENT & COLLISION
    # =========================================================================

    def move(self, dt: float) -> None:
        """Move player based on direction and handle collisions."""
        # Normalize diagonal movement
        if self.direction.magnitude() > 0:
            self.direction = self.direction.normalize()

        # Horizontal movement
        self.pos.x += self.direction.x * self.speed * dt
        self.hitbox.centerx = round(self.pos.x)
        self.rect.centerx = self.hitbox.centerx
        self.collision('horizontal')

        # Vertical movement
        self.pos.y += self.direction.y * self.speed * dt
        self.hitbox.centery = round(self.pos.y)
        self.rect.centery = round(self.pos.y)
        self.collision('vertical')

    def collision(self, direction: str) -> None:
        """Handle collision with world objects."""
        for sprite in self.collision_sprites.sprites():
            if hasattr(sprite, 'hitbox'):
                if sprite.hitbox.colliderect(self.hitbox):
                    if direction == 'horizontal':
                        if self.direction.x > 0:  # Moving right
                            self.hitbox.right = sprite.hitbox.left
                        if self.direction.x < 0:  # Moving left
                            self.hitbox.left = sprite.hitbox.right
                        self.rect.centerx = self.hitbox.centerx
                        self.pos.x = self.hitbox.centerx

                    if direction == 'vertical':
                        if self.direction.y > 0:  # Moving down
                            self.hitbox.bottom = sprite.hitbox.top
                        if self.direction.y < 0:  # Moving up
                            self.hitbox.top = sprite.hitbox.bottom
                        self.rect.centery = self.hitbox.centery
                        self.pos.y = self.hitbox.centery

    # =========================================================================
    # STATS & RESOURCES
    # =========================================================================

    def _use_energy(self, amount: int) -> None:
        """
        Consume energy for actions.
        Energy CAN reach 0, but NEVER prevents basic movement.
        Low energy just makes player slower.
        """
        self.energy = max(0, self.energy - amount)

        # Low energy penalty (but never stop movement entirely)
        if self.energy <= 20:
            self.speed = PLAYER_SPEED * 0.7
        else:
            self.speed = PLAYER_SPEED

    def restore_energy(self, amount: int) -> None:
        """Restore energy (from food, rest, etc.)."""
        self.energy = min(self.max_energy, self.energy + amount)
        if self.energy > 20:
            self.speed = PLAYER_SPEED

    def take_damage(self, amount: int) -> None:
        """
        Take damage. If health reaches 0, player FAINTS (not dies).
        The game will handle respawning at home with Mom's soup.
        """
        self.health = max(0, self.health - amount)

        if self.health <= 0:
            self.faint()

    def heal(self, amount: int) -> None:
        """Restore health."""
        self.health = min(self.max_health, self.health + amount)

        if self.fainted and self.health > 0:
            self.fainted = False

    def faint(self) -> None:
        """
        Player faints - NOT death.
        Sets flag for game to handle (warp home, Mom's soup cutscene).
        """
        self.fainted = True
        self.direction = Vector2(0, 0)

    def sleep(self) -> None:
        """
        Go to bed for the night.
        Triggers day transition and full restore.
        """
        self.sleeping = True
        self.direction = Vector2(0, 0)
        self.status = 'left_idle'

    def wake_up(self) -> None:
        """Called by game after sleep transition."""
        self.sleeping = False
        self.health = self.max_health
        self.energy = self.max_energy

    def add_money(self, amount: int) -> None:
        """Add money to player's wallet."""
        self.money += amount

    def spend_money(self, amount: int) -> bool:
        """Attempt to spend money. Returns True if successful."""
        if self.money >= amount:
            self.money -= amount
            return True
        return False

    def add_item(self, item: str, amount: int = 1) -> None:
        """Add item to inventory."""
        if item in self.item_inventory:
            self.item_inventory[item] += amount
        else:
            self.item_inventory[item] = amount

    # =========================================================================
    # TOOL SYSTEM
    # =========================================================================

    def use_tool(self) -> Optional[str]:
        """
        Execute the current tool action.
        Returns the tool name for external handling (soil, trees, etc.)
        """
        if self.timers['tool use'].active:
            return self.selected_tool
        return None

    def get_tool_target(self) -> Vector2:
        """Get the world position the tool is targeting."""
        return self.target_pos

    # =========================================================================
    # UPDATE LOOP
    # =========================================================================

    def update_timers(self) -> None:
        """Update all action timers."""
        for timer in self.timers.values():
            timer.update()

    def update(self, dt: float) -> None:
        """Main update loop - called every frame."""
        self.input()
        self.get_status()
        self.update_timers()
        self.get_target_pos()

        self.move(dt)
        self.animate(dt)
