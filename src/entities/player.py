"""
Lelock Player Character
L.E.L.O.C.K. - Life Emulation & Lucid Observation for Care & Keeping

The player - a child in a cozy world that exists to care for them.
No death. No failure. Just growth and comfort.
"""

import pygame
from typing import Dict, List, Optional, Tuple, Callable
from pygame.math import Vector2

from settings import (
    LAYERS, PLAYER_SPEED, PLAYER_TOOL_OFFSET, CLASSES
)
from entities.sprites import AnimatedSprite


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


class Player(AnimatedSprite):
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
        # Initialize with placeholder animations (will be loaded properly later)
        # For now, create simple colored rectangles
        placeholder_animations = self._create_placeholder_animations()

        super().__init__(
            pos=pos,
            frames=placeholder_animations,
            groups=groups,
            z=LAYERS['main'],
            animation_speed=4.0
        )

        # Position tracking (float precision for smooth movement)
        self.pos = Vector2(self.rect.center)
        self.direction = Vector2(0, 0)
        self.speed = PLAYER_SPEED

        # Collision
        self.collision_sprites = collision_sprites
        self.interaction_sprites = interaction_sprites or pygame.sprite.Group()
        # Smaller hitbox than sprite for better feel
        self.hitbox = self.rect.copy().inflate(-self.rect.width * 0.5, -self.rect.height * 0.6)

        # Status tracking
        self.status = 'idle_down'
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
        self.tools = ['hoe', 'axe', 'water', 'fishing_rod']
        self.tool_index = 0
        self.current_tool = self.tools[self.tool_index]
        self.target_pos = Vector2(0, 0)

        # Seeds for planting
        self.seeds = ['copper_wheat', 'silicon_berries']
        self.seed_index = 0
        self.current_seed = self.seeds[self.seed_index]

        # -----------------------------
        # INVENTORY (basic for now)
        # -----------------------------
        self.inventory: Dict[str, int] = {
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
            'tool_use': Timer(350, self._on_tool_use_complete),
            'tool_switch': Timer(200),
            'seed_use': Timer(350, self._on_seed_use_complete),
            'seed_switch': Timer(200),
        }

    def _create_placeholder_animations(self) -> Dict[str, List[pygame.Surface]]:
        """Create simple placeholder animations until real assets are loaded."""
        animations = {}
        directions = ['down', 'up', 'left', 'right']

        # Colors for different states
        idle_color = (100, 150, 200)  # Soft blue
        walk_color = (120, 180, 220)  # Lighter blue
        tool_color = (200, 150, 100)  # Warm orange

        for direction in directions:
            # Idle animations (single frame)
            surf = pygame.Surface((32, 48), pygame.SRCALPHA)
            pygame.draw.ellipse(surf, idle_color, (4, 8, 24, 36))
            # Direction indicator
            indicator_pos = {
                'down': (16, 40),
                'up': (16, 12),
                'left': (6, 26),
                'right': (26, 26)
            }
            pygame.draw.circle(surf, (255, 255, 255), indicator_pos[direction], 4)
            animations[f'idle_{direction}'] = [surf]

            # Walk animations (simple 2-frame)
            walk_frames = []
            for i in range(2):
                surf = pygame.Surface((32, 48), pygame.SRCALPHA)
                offset = 2 if i == 0 else -2
                pygame.draw.ellipse(surf, walk_color, (4, 8 + offset, 24, 36))
                pygame.draw.circle(surf, (255, 255, 255), indicator_pos[direction], 4)
                walk_frames.append(surf)
            animations[f'walk_{direction}'] = walk_frames

            # Tool animations (placeholder)
            surf = pygame.Surface((32, 48), pygame.SRCALPHA)
            pygame.draw.ellipse(surf, tool_color, (4, 8, 24, 36))
            pygame.draw.circle(surf, (255, 200, 100), indicator_pos[direction], 4)
            animations[f'tool_{direction}'] = [surf]

        return animations

    # =========================================================================
    # INPUT HANDLING
    # =========================================================================

    def input(self) -> None:
        """Process keyboard input for movement and actions."""
        # Can't move while using tool, sleeping, or fainted
        if self.timers['tool_use'].active or self.sleeping or self.fainted:
            return

        keys = pygame.key.get_pressed()

        # Reset direction
        self.direction.x = 0
        self.direction.y = 0

        # Movement: WASD and Arrow Keys (8-directional)
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.direction.y = -1
            self.facing_direction = 'up'
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.direction.y = 1
            self.facing_direction = 'down'

        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.direction.x = -1
            self.facing_direction = 'left'
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.direction.x = 1
            self.facing_direction = 'right'

        # Tool use (Space)
        if keys[pygame.K_SPACE] and not self.timers['tool_use'].active:
            self._start_tool_use()

        # Tool switch (Q)
        if keys[pygame.K_q] and not self.timers['tool_switch'].active:
            self._switch_tool()

        # Seed use (Left Ctrl / E for planting)
        if keys[pygame.K_LCTRL] and not self.timers['seed_use'].active:
            self._start_seed_use()

        # Seed switch (E when not planting)
        if keys[pygame.K_e] and not self.timers['seed_switch'].active:
            self._switch_seed()

        # Interaction (Enter/Return)
        if keys[pygame.K_RETURN]:
            self._check_interaction()

    def _start_tool_use(self) -> None:
        """Begin using current tool."""
        self.timers['tool_use'].activate()
        self.direction = Vector2(0, 0)
        self.using_tool = True
        self.frame_index = 0

        # Calculate target position based on facing direction
        offset = PLAYER_TOOL_OFFSET.get(self.facing_direction, Vector2(0, 50))
        self.target_pos = Vector2(self.rect.center) + offset

        # Energy cost for tools (but NEVER prevent basic actions)
        self._use_energy(5)

    def _on_tool_use_complete(self) -> None:
        """Called when tool use timer expires."""
        self.using_tool = False
        # Actual tool effect would be triggered here
        # For now, just a placeholder

    def _start_seed_use(self) -> None:
        """Begin planting current seed."""
        if self.seed_inventory.get(self.current_seed, 0) > 0:
            self.timers['seed_use'].activate()
            self.direction = Vector2(0, 0)
            self.frame_index = 0

            offset = PLAYER_TOOL_OFFSET.get(self.facing_direction, Vector2(0, 50))
            self.target_pos = Vector2(self.rect.center) + offset

            self._use_energy(2)

    def _on_seed_use_complete(self) -> None:
        """Called when seed planting timer expires."""
        if self.seed_inventory.get(self.current_seed, 0) > 0:
            self.seed_inventory[self.current_seed] -= 1
            # Actual planting would be triggered here

    def _switch_tool(self) -> None:
        """Cycle to next tool."""
        self.timers['tool_switch'].activate()
        self.tool_index = (self.tool_index + 1) % len(self.tools)
        self.current_tool = self.tools[self.tool_index]

    def _switch_seed(self) -> None:
        """Cycle to next seed type."""
        self.timers['seed_switch'].activate()
        self.seed_index = (self.seed_index + 1) % len(self.seeds)
        self.current_seed = self.seeds[self.seed_index]

    def _check_interaction(self) -> None:
        """Check for interactable objects and interact."""
        collided = pygame.sprite.spritecollide(
            self, self.interaction_sprites, False
        )
        if collided:
            interaction = collided[0]
            # Handle different interaction types
            if hasattr(interaction, 'name'):
                if interaction.name == 'Bed':
                    self.sleep()
                elif interaction.name == 'Terminal':
                    pass  # Digital world toggle
                elif interaction.name == 'NPC':
                    pass  # Dialogue trigger

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
        self._collision('horizontal')

        # Vertical movement
        self.pos.y += self.direction.y * self.speed * dt
        self.hitbox.centery = round(self.pos.y)
        self.rect.centery = self.hitbox.centery
        self._collision('vertical')

    def _collision(self, direction: str) -> None:
        """Handle collision with world objects."""
        for sprite in self.collision_sprites.sprites():
            if not hasattr(sprite, 'hitbox'):
                continue

            if sprite.hitbox.colliderect(self.hitbox):
                if direction == 'horizontal':
                    if self.direction.x > 0:  # Moving right
                        self.hitbox.right = sprite.hitbox.left
                    elif self.direction.x < 0:  # Moving left
                        self.hitbox.left = sprite.hitbox.right
                    self.rect.centerx = self.hitbox.centerx
                    self.pos.x = self.hitbox.centerx

                elif direction == 'vertical':
                    if self.direction.y > 0:  # Moving down
                        self.hitbox.bottom = sprite.hitbox.top
                    elif self.direction.y < 0:  # Moving up
                        self.hitbox.top = sprite.hitbox.bottom
                    self.rect.centery = self.hitbox.centery
                    self.pos.y = self.hitbox.centery

    # =========================================================================
    # STATUS & ANIMATION
    # =========================================================================

    def get_status(self) -> None:
        """Determine current animation status based on state."""
        # Tool use takes priority
        if self.timers['tool_use'].active:
            self.status = f'tool_{self.facing_direction}'
            return

        # Walking vs idle
        if self.direction.magnitude() > 0:
            self.status = f'walk_{self.facing_direction}'
            self.is_moving = True
        else:
            self.status = f'idle_{self.facing_direction}'
            self.is_moving = False

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
        # Restore speed if energy is back up
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

        # Recover from fainted state
        if self.fainted and self.health > 0:
            self.fainted = False

    def faint(self) -> None:
        """
        Player faints - NOT death.
        Sets flag for game to handle (warp home, Mom's soup cutscene).
        """
        self.fainted = True
        self.direction = Vector2(0, 0)
        # Game will check this flag and trigger the "warp home" sequence
        # Player wakes up in bed, Mom brings soup, all is well

    def sleep(self) -> None:
        """
        Go to bed for the night.
        Triggers day transition and full restore.
        """
        self.sleeping = True
        self.direction = Vector2(0, 0)
        self.status = f'idle_{self.facing_direction}'
        # Game will check this flag and trigger sleep transition
        # Next morning: full health, full energy, gentle sunrise

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
        if item in self.inventory:
            self.inventory[item] += amount
        else:
            self.inventory[item] = amount

    # =========================================================================
    # TOOL SYSTEM
    # =========================================================================

    def use_tool(self) -> Optional[str]:
        """
        Execute the current tool action.
        Returns the tool name for external handling (soil, trees, etc.)
        """
        if self.timers['tool_use'].active:
            return self.current_tool
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
        # Don't update if fainted (game handles that state)
        if self.fainted:
            return

        self.input()
        self.get_status()
        self.update_timers()
        self.move(dt)
        self.animate(dt)
