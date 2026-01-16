"""
Lelock NPC Entity System
========================
L.E.L.O.C.K. - Life Emulation & Lucid Observation for Care & Keeping

NPCs are NOT scripted - they are ALIVE. Every NPC has:
- A persona (personality, memories, relationships)
- A daily schedule (different places at different times)
- Emotional states that affect their behavior
- The ability to remember EVERYTHING about the player

"In Lelock, every NPC remembers you. Every word matters.
Every kindness echoes forward through time."

This module provides:
1. NPC class - Game entity that links to AI systems
2. NPCManager - Spawns and manages all NPCs in a level
3. Schedule system - NPCs follow daily routines
4. Interaction system - Player talks to NPCs via DialogueManager
5. Visual feedback - Speech bubbles, heart particles, thinking indicators

Author: Ada Marie for Kit Olivas
Project: L.E.L.O.C.K. - Life Emulation & Lucid Observation for Care & Keeping
"""

import pygame
import asyncio
import random
import math
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable, Any, TYPE_CHECKING
from pygame.math import Vector2
from pathlib import Path

from settings import LAYERS, TILE_SIZE
from entities.sprites import AnimatedSprite, ParticleSprite

# Type checking imports (avoid circular imports)
if TYPE_CHECKING:
    from ai.dialogue import DialogueManager
    from ai.persona import PersonaManager, Persona


# =============================================================================
# NPC STATE ENUM
# =============================================================================

class NPCState(Enum):
    """
    NPC behavioral states.

    Each state affects animation, movement, and interaction availability.
    """
    IDLE = "idle"           # Standing still, small idle animation
    WALKING = "walking"     # Moving to destination
    WORKING = "working"     # At job location, doing job animation
    TALKING = "talking"     # In conversation with player
    SLEEPING = "sleeping"   # Night time, in bed (not interactable)
    THINKING = "thinking"   # LLM is generating response (show thought bubble)


class NPCMood(Enum):
    """
    NPC emotional states for visual feedback.

    Affects expressions and particle effects.
    """
    NEUTRAL = "neutral"
    HAPPY = "happy"
    CONCERNED = "concerned"
    THOUGHTFUL = "thoughtful"
    EXCITED = "excited"


# =============================================================================
# SCHEDULE SYSTEM
# =============================================================================

@dataclass
class ScheduleEntry:
    """
    A single entry in an NPC's daily schedule.

    NPCs move to different locations at different times,
    making the world feel alive and predictable (like real people).
    """
    time_period: str  # dawn, morning, midday, afternoon, evening, night
    location: str     # Location name (e.g., "home", "shop", "plaza")
    position: Tuple[int, int]  # World coordinates
    activity: str     # What they're doing (for dialogue context)
    state: NPCState   # What state to be in

    # Optional: facing direction while at this location
    facing: str = "down"


@dataclass
class NPCSchedule:
    """
    Complete daily schedule for an NPC.

    Maps time periods to locations and activities.
    """
    npc_id: str
    entries: Dict[str, ScheduleEntry] = field(default_factory=dict)

    def get_current_entry(self, time_period: str) -> Optional[ScheduleEntry]:
        """Get the schedule entry for the current time period."""
        return self.entries.get(time_period)

    def add_entry(
        self,
        time_period: str,
        location: str,
        position: Tuple[int, int],
        activity: str,
        state: NPCState = NPCState.IDLE,
        facing: str = "down"
    ):
        """Add a schedule entry."""
        self.entries[time_period] = ScheduleEntry(
            time_period=time_period,
            location=location,
            position=position,
            activity=activity,
            state=state,
            facing=facing
        )


# =============================================================================
# VISUAL INDICATOR SPRITES
# =============================================================================

class SpeechBubbleSprite(pygame.sprite.Sprite):
    """
    Speech bubble that appears above NPC when they want to talk.

    Shows "..." when idle, "!" when they have something important,
    "?" when curious about the player.
    """

    def __init__(
        self,
        groups: pygame.sprite.Group,
        parent_rect: pygame.Rect,
        bubble_type: str = "..."
    ):
        super().__init__(groups)

        self.parent_rect = parent_rect
        self.bubble_type = bubble_type
        self.z = LAYERS['ui']

        # Create the bubble surface
        self.image = self._create_bubble_surface()
        self.rect = self.image.get_rect()
        self._update_position()

        # Bobbing animation
        self.bob_offset = 0
        self.bob_speed = 2.0
        self.bob_amplitude = 3
        self.time = random.random() * math.pi * 2  # Random start phase

    def _create_bubble_surface(self) -> pygame.Surface:
        """Create the speech bubble graphic."""
        # Bubble size based on content
        width = 24 if self.bubble_type == "..." else 20
        height = 20

        surface = pygame.Surface((width, height + 6), pygame.SRCALPHA)

        # Draw rounded bubble
        bubble_color = (255, 255, 255)
        outline_color = (100, 100, 120)

        # Main bubble
        pygame.draw.ellipse(surface, bubble_color, (0, 0, width, height))
        pygame.draw.ellipse(surface, outline_color, (0, 0, width, height), 2)

        # Little triangle pointing down
        points = [(width//2 - 4, height - 2), (width//2 + 4, height - 2), (width//2, height + 5)]
        pygame.draw.polygon(surface, bubble_color, points)
        pygame.draw.lines(surface, outline_color, False,
                         [(width//2 - 4, height - 2), (width//2, height + 5), (width//2 + 4, height - 2)], 2)

        # Draw the text/symbol
        font = pygame.font.Font(None, 16)
        text_color = (60, 60, 80)
        text_surf = font.render(self.bubble_type, True, text_color)
        text_rect = text_surf.get_rect(center=(width//2, height//2 - 1))
        surface.blit(text_surf, text_rect)

        return surface

    def _update_position(self):
        """Position bubble above parent."""
        self.rect.centerx = self.parent_rect.centerx
        self.rect.bottom = self.parent_rect.top - 5 + self.bob_offset

    def set_type(self, bubble_type: str):
        """Change the bubble type."""
        if bubble_type != self.bubble_type:
            self.bubble_type = bubble_type
            self.image = self._create_bubble_surface()

    def update(self, dt: float):
        """Update bobbing animation."""
        self.time += self.bob_speed * dt
        self.bob_offset = math.sin(self.time) * self.bob_amplitude
        self._update_position()


class ThinkingIndicator(pygame.sprite.Sprite):
    """
    Thought bubble that appears when LLM is generating response.

    Shows animated dots to indicate "thinking..."
    """

    def __init__(
        self,
        groups: pygame.sprite.Group,
        parent_rect: pygame.Rect
    ):
        super().__init__(groups)

        self.parent_rect = parent_rect
        self.z = LAYERS['ui']

        # Animation state
        self.dot_count = 0
        self.max_dots = 3
        self.timer = 0
        self.dot_interval = 0.3  # seconds between dot changes

        self.image = self._create_surface()
        self.rect = self.image.get_rect()
        self._update_position()

    def _create_surface(self) -> pygame.Surface:
        """Create the thinking bubble."""
        width, height = 32, 24
        surface = pygame.Surface((width, height + 8), pygame.SRCALPHA)

        # Draw cloud-like thought bubble
        bubble_color = (240, 240, 255)
        outline_color = (150, 150, 180)

        # Main cloud shape (overlapping circles)
        pygame.draw.ellipse(surface, bubble_color, (0, 4, 24, 16))
        pygame.draw.ellipse(surface, bubble_color, (8, 0, 24, 20))
        pygame.draw.ellipse(surface, outline_color, (0, 4, 24, 16), 1)
        pygame.draw.ellipse(surface, outline_color, (8, 0, 24, 20), 1)

        # Little thought circles leading down
        pygame.draw.circle(surface, bubble_color, (width//2, height + 2), 4)
        pygame.draw.circle(surface, outline_color, (width//2, height + 2), 4, 1)
        pygame.draw.circle(surface, bubble_color, (width//2 - 2, height + 6), 2)
        pygame.draw.circle(surface, outline_color, (width//2 - 2, height + 6), 2, 1)

        # Draw animated dots
        dot_color = (100, 100, 140)
        dot_y = 10
        dot_spacing = 6
        start_x = width//2 - dot_spacing

        for i in range(self.dot_count):
            x = start_x + (i * dot_spacing)
            pygame.draw.circle(surface, dot_color, (x, dot_y), 2)

        return surface

    def _update_position(self):
        """Position above parent."""
        self.rect.centerx = self.parent_rect.centerx
        self.rect.bottom = self.parent_rect.top - 8

    def update(self, dt: float):
        """Animate the dots."""
        self.timer += dt
        if self.timer >= self.dot_interval:
            self.timer = 0
            self.dot_count = (self.dot_count + 1) % (self.max_dots + 1)
            self.image = self._create_surface()

        self._update_position()


class HeartParticle(ParticleSprite):
    """
    Heart particle that floats up when trust increases.

    Visual feedback that the player did something good.
    """

    def __init__(
        self,
        pos: Tuple[int, int],
        groups: pygame.sprite.Group
    ):
        # Create heart surface
        surface = self._create_heart_surface()

        super().__init__(
            pos=pos,
            surface=surface,
            groups=groups,
            z=LAYERS['ui'],
            duration_ms=1500,
            fade=True
        )

        # Float upward
        self.velocity = Vector2(random.uniform(-20, 20), -50)
        self.pos = Vector2(pos)

    def _create_heart_surface(self) -> pygame.Surface:
        """Create a small heart."""
        size = 12
        surface = pygame.Surface((size, size), pygame.SRCALPHA)

        # Draw a simple heart shape
        color = (255, 100, 150)  # Soft pink

        # Two circles for top
        pygame.draw.circle(surface, color, (3, 3), 3)
        pygame.draw.circle(surface, color, (9, 3), 3)

        # Triangle for bottom
        points = [(0, 4), (6, 11), (12, 4)]
        pygame.draw.polygon(surface, color, points)

        return surface

    def update(self, dt: float):
        """Float upward and fade."""
        # Move
        self.pos += self.velocity * dt
        self.rect.center = (int(self.pos.x), int(self.pos.y))

        # Slow down horizontal drift
        self.velocity.x *= 0.95

        # Call parent update for fade/destroy
        super().update(dt)


# =============================================================================
# NPC CLASS
# =============================================================================

class NPC(AnimatedSprite):
    """
    An NPC game entity that integrates with the AI systems.

    NPCs are NOT scripted - they use:
    - PersonaManager for personality and dialogue generation
    - DialogueManager for conversations
    - Schedule system for daily routines

    Each NPC feels ALIVE because:
    - They remember past conversations
    - They have opinions and feelings
    - They follow daily routines
    - They react emotionally to player actions

    "Every NPC is a soul, not a script."
    """

    # Interaction radius (how close player must be to interact)
    INTERACTION_RADIUS = 48  # pixels

    # Movement speeds
    WALK_SPEED = 80  # pixels per second

    def __init__(
        self,
        pos: Tuple[int, int],
        groups: pygame.sprite.Group,
        collision_sprites: pygame.sprite.Group,
        persona_id: str,
        npc_id: str,
        display_name: str,
        schedule: Optional[NPCSchedule] = None,
        animations: Optional[Dict[str, List[pygame.Surface]]] = None,
    ):
        """
        Initialize an NPC.

        Args:
            pos: Starting position (x, y)
            groups: Sprite groups to add to
            collision_sprites: Sprites to collide with
            persona_id: ID to look up in PersonaManager (e.g., "mom", "dad")
            npc_id: Unique identifier for this NPC instance
            display_name: Name shown in dialogue UI
            schedule: Daily schedule (optional)
            animations: Animation frames dict (optional, uses placeholder if None)
        """
        # Create placeholder animations if none provided
        if animations is None:
            animations = self._create_placeholder_animations()

        super().__init__(
            pos=pos,
            frames=animations,
            groups=groups,
            z=LAYERS['main'],
            animation_speed=3.0
        )

        # Identity
        self.persona_id = persona_id
        self.npc_id = npc_id
        self.display_name = display_name

        # Position tracking
        self.pos = Vector2(self.rect.center)
        self.direction = Vector2(0, 0)
        self.speed = self.WALK_SPEED

        # Collision
        self.collision_sprites = collision_sprites
        self.hitbox = self.rect.copy().inflate(-self.rect.width * 0.4, -self.rect.height * 0.5)

        # State
        self.state = NPCState.IDLE
        self.previous_state = NPCState.IDLE
        self.mood = NPCMood.NEUTRAL
        self.facing_direction = "down"

        # Schedule
        self.schedule = schedule
        self.current_schedule_entry: Optional[ScheduleEntry] = None
        self.target_position: Optional[Vector2] = None

        # Movement patterns
        self.wander_timer = 0
        self.wander_interval = random.uniform(3.0, 8.0)  # Seconds between wanders
        self.wander_radius = 64  # Max distance to wander
        self.home_position = Vector2(pos)

        # Interaction state
        self.can_interact = True
        self.is_in_conversation = False
        self.player_nearby = False
        self.interaction_cooldown = 0

        # Visual indicators (created when needed)
        self.speech_bubble: Optional[SpeechBubbleSprite] = None
        self.thinking_indicator: Optional[ThinkingIndicator] = None
        self._indicator_groups: Optional[pygame.sprite.Group] = None

        # Callbacks
        self._on_interaction_start: Optional[Callable] = None
        self._on_interaction_end: Optional[Callable] = None

    def _create_placeholder_animations(self) -> Dict[str, List[pygame.Surface]]:
        """Create simple placeholder animations."""
        animations = {}
        directions = ['down', 'up', 'left', 'right']

        # NPC colors (different from player)
        idle_color = (180, 140, 100)  # Warm tan
        walk_color = (200, 160, 120)  # Lighter tan

        for direction in directions:
            # Idle animations
            surf = pygame.Surface((32, 48), pygame.SRCALPHA)
            pygame.draw.ellipse(surf, idle_color, (4, 8, 24, 36))

            # Direction indicator
            indicator_pos = {
                'down': (16, 40),
                'up': (16, 12),
                'left': (6, 26),
                'right': (26, 26)
            }
            pygame.draw.circle(surf, (255, 200, 150), indicator_pos[direction], 4)
            animations[f'idle_{direction}'] = [surf]

            # Walk animations
            walk_frames = []
            for i in range(2):
                surf = pygame.Surface((32, 48), pygame.SRCALPHA)
                offset = 2 if i == 0 else -2
                pygame.draw.ellipse(surf, walk_color, (4, 8 + offset, 24, 36))
                pygame.draw.circle(surf, (255, 200, 150), indicator_pos[direction], 4)
                walk_frames.append(surf)
            animations[f'walk_{direction}'] = walk_frames

            # Working animation (same as idle for placeholder)
            animations[f'work_{direction}'] = [surf]

        # Sleeping animation
        sleep_surf = pygame.Surface((48, 32), pygame.SRCALPHA)
        pygame.draw.ellipse(sleep_surf, idle_color, (4, 4, 40, 24))
        # Z's
        font = pygame.font.Font(None, 16)
        z_surf = font.render("z z z", True, (200, 200, 255))
        sleep_surf.blit(z_surf, (10, 0))
        animations['sleep'] = [sleep_surf]

        return animations

    # =========================================================================
    # INDICATOR MANAGEMENT
    # =========================================================================

    def set_indicator_group(self, groups: pygame.sprite.Group):
        """Set the sprite group for visual indicators."""
        self._indicator_groups = groups

    def show_speech_bubble(self, bubble_type: str = "..."):
        """Show a speech bubble above the NPC."""
        if self._indicator_groups is None:
            return

        if self.speech_bubble is None:
            self.speech_bubble = SpeechBubbleSprite(
                self._indicator_groups,
                self.rect,
                bubble_type
            )
        else:
            self.speech_bubble.set_type(bubble_type)

    def hide_speech_bubble(self):
        """Remove the speech bubble."""
        if self.speech_bubble:
            self.speech_bubble.kill()
            self.speech_bubble = None

    def show_thinking(self):
        """Show thinking indicator (LLM generating)."""
        if self._indicator_groups is None:
            return

        self.hide_speech_bubble()  # Replace speech bubble

        if self.thinking_indicator is None:
            self.thinking_indicator = ThinkingIndicator(
                self._indicator_groups,
                self.rect
            )

    def hide_thinking(self):
        """Remove thinking indicator."""
        if self.thinking_indicator:
            self.thinking_indicator.kill()
            self.thinking_indicator = None

    def spawn_heart_particle(self):
        """Spawn a heart particle (trust increased)."""
        if self._indicator_groups is None:
            return

        # Spawn slightly above NPC
        pos = (self.rect.centerx, self.rect.top - 10)
        HeartParticle(pos, self._indicator_groups)

    # =========================================================================
    # SCHEDULE SYSTEM
    # =========================================================================

    def update_schedule(self, time_period: str):
        """
        Update NPC based on current time period.

        Args:
            time_period: Current time (dawn, morning, midday, afternoon, evening, night)
        """
        if self.schedule is None:
            return

        entry = self.schedule.get_current_entry(time_period)
        if entry is None:
            return

        # Don't interrupt conversations
        if self.is_in_conversation:
            return

        # Check if we need to move to a new location
        if self.current_schedule_entry != entry:
            self.current_schedule_entry = entry

            # Set target position
            self.target_position = Vector2(entry.position)

            # If sleeping, go directly to that state
            if entry.state == NPCState.SLEEPING:
                self.set_state(NPCState.SLEEPING)
                self.pos = Vector2(entry.position)
                self.target_position = None
            elif self.pos.distance_to(self.target_position) > 5:
                # Need to walk there
                self.set_state(NPCState.WALKING)
            else:
                # Already there
                self.arrive_at_destination()

    def arrive_at_destination(self):
        """Called when NPC reaches their scheduled destination."""
        if self.current_schedule_entry:
            self.set_state(self.current_schedule_entry.state)
            self.facing_direction = self.current_schedule_entry.facing
        else:
            self.set_state(NPCState.IDLE)

        self.target_position = None
        self._update_animation_status()

    # =========================================================================
    # STATE MANAGEMENT
    # =========================================================================

    def set_state(self, new_state: NPCState):
        """Change NPC state with proper cleanup."""
        if new_state == self.state:
            return

        self.previous_state = self.state
        self.state = new_state

        # State-specific setup
        if new_state == NPCState.TALKING:
            self.is_in_conversation = True
            self.direction = Vector2(0, 0)
            self.hide_speech_bubble()

        elif new_state == NPCState.THINKING:
            self.show_thinking()

        elif new_state in [NPCState.IDLE, NPCState.WORKING]:
            self.hide_thinking()
            self.is_in_conversation = False

        elif new_state == NPCState.SLEEPING:
            self.can_interact = False
            self.hide_speech_bubble()
            self.hide_thinking()

        self._update_animation_status()

    def _update_animation_status(self):
        """Update animation based on current state."""
        state_to_anim = {
            NPCState.IDLE: 'idle',
            NPCState.WALKING: 'walk',
            NPCState.WORKING: 'work',
            NPCState.TALKING: 'idle',
            NPCState.THINKING: 'idle',
            NPCState.SLEEPING: 'sleep',
        }

        anim_prefix = state_to_anim.get(self.state, 'idle')

        if self.state == NPCState.SLEEPING:
            self.status = 'sleep'
        else:
            self.status = f'{anim_prefix}_{self.facing_direction}'

    # =========================================================================
    # MOVEMENT
    # =========================================================================

    def move_toward(self, target: Vector2, dt: float):
        """Move toward a target position."""
        if self.pos.distance_to(target) < 5:
            # Arrived
            self.pos = target.copy()
            self.direction = Vector2(0, 0)
            return True

        # Calculate direction
        direction = target - self.pos
        direction = direction.normalize() if direction.length() > 0 else Vector2(0, 0)

        # Update facing
        self._update_facing(direction)

        # Move
        self.direction = direction
        movement = direction * self.speed * dt

        # Apply movement with collision
        self.pos.x += movement.x
        self.hitbox.centerx = round(self.pos.x)
        self.rect.centerx = self.hitbox.centerx
        self._collision('horizontal')

        self.pos.y += movement.y
        self.hitbox.centery = round(self.pos.y)
        self.rect.centery = self.hitbox.centery
        self._collision('vertical')

        return False

    def _update_facing(self, direction: Vector2):
        """Update facing direction based on movement."""
        if abs(direction.x) > abs(direction.y):
            self.facing_direction = 'right' if direction.x > 0 else 'left'
        elif direction.y != 0:
            self.facing_direction = 'down' if direction.y > 0 else 'up'

    def _collision(self, direction: str):
        """Handle collision with world objects."""
        for sprite in self.collision_sprites.sprites():
            if not hasattr(sprite, 'hitbox'):
                continue

            if sprite.hitbox.colliderect(self.hitbox):
                if direction == 'horizontal':
                    if self.direction.x > 0:
                        self.hitbox.right = sprite.hitbox.left
                    elif self.direction.x < 0:
                        self.hitbox.left = sprite.hitbox.right
                    self.rect.centerx = self.hitbox.centerx
                    self.pos.x = self.hitbox.centerx

                elif direction == 'vertical':
                    if self.direction.y > 0:
                        self.hitbox.bottom = sprite.hitbox.top
                    elif self.direction.y < 0:
                        self.hitbox.top = sprite.hitbox.bottom
                    self.rect.centery = self.hitbox.centery
                    self.pos.y = self.hitbox.centery

    def wander(self, dt: float):
        """Wander randomly when idle and no schedule."""
        self.wander_timer += dt

        if self.wander_timer >= self.wander_interval:
            self.wander_timer = 0
            self.wander_interval = random.uniform(3.0, 8.0)

            # Pick a random point within wander radius of home
            angle = random.uniform(0, math.pi * 2)
            distance = random.uniform(0, self.wander_radius)

            offset = Vector2(
                math.cos(angle) * distance,
                math.sin(angle) * distance
            )

            self.target_position = self.home_position + offset
            self.set_state(NPCState.WALKING)

    # =========================================================================
    # INTERACTION
    # =========================================================================

    def face_position(self, pos: Vector2):
        """Face toward a position (e.g., the player)."""
        direction = pos - self.pos
        self._update_facing(direction)
        self._update_animation_status()

    def check_player_proximity(self, player_pos: Vector2) -> bool:
        """Check if player is within interaction radius."""
        distance = self.pos.distance_to(player_pos)

        was_nearby = self.player_nearby
        self.player_nearby = distance <= self.INTERACTION_RADIUS

        # Show/hide speech bubble based on proximity
        if self.player_nearby and not was_nearby and self.can_interact:
            if not self.is_in_conversation and self.state != NPCState.SLEEPING:
                self.show_speech_bubble("...")
        elif not self.player_nearby and was_nearby:
            if not self.is_in_conversation:
                self.hide_speech_bubble()

        return self.player_nearby

    def can_start_interaction(self) -> bool:
        """Check if NPC can start a conversation."""
        return (
            self.can_interact and
            not self.is_in_conversation and
            self.state != NPCState.SLEEPING and
            self.interaction_cooldown <= 0
        )

    def start_interaction(self, player_pos: Vector2) -> bool:
        """
        Start interaction with the player.

        Returns True if interaction started successfully.
        """
        if not self.can_start_interaction():
            return False

        # Face the player
        self.face_position(player_pos)

        # Enter talking state
        self.set_state(NPCState.TALKING)

        # Call callback if set
        if self._on_interaction_start:
            self._on_interaction_start(self)

        return True

    def end_interaction(self):
        """End the current interaction."""
        self.is_in_conversation = False
        self.hide_thinking()

        # Return to previous state or idle
        if self.current_schedule_entry:
            self.set_state(self.current_schedule_entry.state)
        else:
            self.set_state(NPCState.IDLE)

        # Small cooldown before next interaction
        self.interaction_cooldown = 1.0

        # Call callback if set
        if self._on_interaction_end:
            self._on_interaction_end(self)

    def set_interaction_callbacks(
        self,
        on_start: Optional[Callable] = None,
        on_end: Optional[Callable] = None
    ):
        """Set callbacks for interaction events."""
        self._on_interaction_start = on_start
        self._on_interaction_end = on_end

    # =========================================================================
    # UPDATE LOOP
    # =========================================================================

    def update(self, dt: float):
        """Main update loop."""
        # Update cooldowns
        if self.interaction_cooldown > 0:
            self.interaction_cooldown -= dt

        # State-specific updates
        if self.state == NPCState.WALKING:
            if self.target_position:
                arrived = self.move_toward(self.target_position, dt)
                if arrived:
                    self.arrive_at_destination()
            else:
                self.set_state(NPCState.IDLE)

        elif self.state == NPCState.IDLE:
            # Wander if no schedule
            if self.schedule is None and not self.is_in_conversation:
                self.wander(dt)

        # Update animation status
        self._update_animation_status()

        # Update visual indicators
        if self.speech_bubble:
            self.speech_bubble.parent_rect = self.rect
        if self.thinking_indicator:
            self.thinking_indicator.parent_rect = self.rect

        # Call parent update for animation
        super().update(dt)


# =============================================================================
# NPC MANAGER
# =============================================================================

class NPCManager:
    """
    Central manager for all NPCs in a level.

    Responsibilities:
    - Spawn and track all NPCs
    - Update NPC positions and states
    - Handle time-based schedule updates
    - Coordinate player interactions with DialogueManager
    - Find NPCs by name or location

    "The village breathes because we coordinate its people."
    """

    def __init__(
        self,
        all_sprites: pygame.sprite.Group,
        collision_sprites: pygame.sprite.Group,
        interaction_sprites: pygame.sprite.Group,
        dialogue_manager: Optional["DialogueManager"] = None,
        persona_manager: Optional["PersonaManager"] = None,
    ):
        """
        Initialize the NPC manager.

        Args:
            all_sprites: Main sprite group for rendering
            collision_sprites: Sprites NPCs collide with
            interaction_sprites: Group for interaction zones
            dialogue_manager: DialogueManager for conversations
            persona_manager: PersonaManager for NPC personalities
        """
        self.all_sprites = all_sprites
        self.collision_sprites = collision_sprites
        self.interaction_sprites = interaction_sprites
        self.dialogue_manager = dialogue_manager
        self.persona_manager = persona_manager

        # NPC tracking
        self.npcs: Dict[str, NPC] = {}
        self.npc_group = pygame.sprite.Group()

        # Indicator sprites (for speech bubbles, etc.)
        self.indicator_group = pygame.sprite.Group()

        # Current time period
        self.current_time_period = "morning"

        # Active conversation
        self.active_conversation_npc: Optional[NPC] = None
        self.awaiting_response = False

    def spawn_npc(
        self,
        npc_id: str,
        persona_id: str,
        display_name: str,
        position: Tuple[int, int],
        schedule: Optional[NPCSchedule] = None,
        animations: Optional[Dict[str, List[pygame.Surface]]] = None,
    ) -> NPC:
        """
        Spawn a new NPC in the world.

        Args:
            npc_id: Unique identifier
            persona_id: Persona to use from PersonaManager
            display_name: Name shown in UI
            position: World position (x, y)
            schedule: Optional daily schedule
            animations: Optional custom animations

        Returns:
            The spawned NPC instance
        """
        npc = NPC(
            pos=position,
            groups=[self.all_sprites, self.npc_group],
            collision_sprites=self.collision_sprites,
            persona_id=persona_id,
            npc_id=npc_id,
            display_name=display_name,
            schedule=schedule,
            animations=animations,
        )

        # Set up indicator group
        npc.set_indicator_group(self.indicator_group)

        # Set interaction callbacks
        npc.set_interaction_callbacks(
            on_start=self._on_npc_interaction_start,
            on_end=self._on_npc_interaction_end,
        )

        self.npcs[npc_id] = npc
        return npc

    def remove_npc(self, npc_id: str):
        """Remove an NPC from the world."""
        if npc_id in self.npcs:
            npc = self.npcs[npc_id]
            npc.hide_speech_bubble()
            npc.hide_thinking()
            npc.kill()
            del self.npcs[npc_id]

    def get_npc(self, npc_id: str) -> Optional[NPC]:
        """Get an NPC by ID."""
        return self.npcs.get(npc_id)

    def get_npc_by_persona(self, persona_id: str) -> Optional[NPC]:
        """Get an NPC by their persona ID."""
        for npc in self.npcs.values():
            if npc.persona_id == persona_id:
                return npc
        return None

    def get_npcs_at_location(self, location: str) -> List[NPC]:
        """Get all NPCs currently at a location."""
        result = []
        for npc in self.npcs.values():
            if npc.current_schedule_entry and npc.current_schedule_entry.location == location:
                result.append(npc)
        return result

    def find_npc(self, name_or_id: str) -> Optional[NPC]:
        """
        Find an NPC by name or ID (case-insensitive).

        Useful for "where is Mom?" queries.
        """
        name_lower = name_or_id.lower()

        # Try exact ID match first
        if name_lower in self.npcs:
            return self.npcs[name_lower]

        # Try display name match
        for npc in self.npcs.values():
            if npc.display_name.lower() == name_lower:
                return npc
            if npc.persona_id.lower() == name_lower:
                return npc

        return None

    # =========================================================================
    # TIME AND SCHEDULE
    # =========================================================================

    def set_time_period(self, time_period: str):
        """
        Update all NPCs for a new time period.

        Called when game time changes (dawn, morning, midday, etc.)
        """
        self.current_time_period = time_period

        for npc in self.npcs.values():
            npc.update_schedule(time_period)

    # =========================================================================
    # PLAYER INTERACTION
    # =========================================================================

    def check_player_interactions(self, player_pos: Vector2) -> Optional[NPC]:
        """
        Check all NPCs for player proximity.

        Returns the nearest interactable NPC if any.
        """
        nearest_npc = None
        nearest_distance = float('inf')

        for npc in self.npcs.values():
            if npc.check_player_proximity(player_pos):
                if npc.can_start_interaction():
                    distance = npc.pos.distance_to(player_pos)
                    if distance < nearest_distance:
                        nearest_distance = distance
                        nearest_npc = npc

        return nearest_npc

    def start_conversation(self, npc: NPC, player_pos: Vector2) -> bool:
        """
        Start a conversation with an NPC.

        Returns True if conversation started.
        """
        if not npc.start_interaction(player_pos):
            return False

        self.active_conversation_npc = npc
        return True

    def end_conversation(self):
        """End the current conversation."""
        if self.active_conversation_npc:
            self.active_conversation_npc.end_interaction()
            self.active_conversation_npc = None
        self.awaiting_response = False

    async def send_player_message(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Send a player message to the active conversation NPC.

        Returns the NPC's response, or None if no conversation active.

        Args:
            message: What the player said
            context: Additional context (time, weather, etc.)

        Returns:
            NPC response string

        Raises:
            Various errors from DialogueManager if LLM fails
        """
        if not self.active_conversation_npc or not self.dialogue_manager:
            return None

        npc = self.active_conversation_npc

        # Show thinking indicator
        npc.set_state(NPCState.THINKING)
        self.awaiting_response = True

        try:
            # Get response from DialogueManager
            result = await self.dialogue_manager.chat(
                npc_name=npc.persona_id,
                player_input=message,
                context=context,
            )

            # Hide thinking, show response
            npc.set_state(NPCState.TALKING)
            self.awaiting_response = False

            # Check for trust increase
            if result.trust_delta > 0:
                npc.spawn_heart_particle()

            # Update NPC mood
            npc.mood = NPCMood(result.npc_mood) if result.npc_mood in [m.value for m in NPCMood] else NPCMood.NEUTRAL

            return result.response

        except Exception as e:
            # On error, end thinking state
            npc.set_state(NPCState.TALKING)
            self.awaiting_response = False
            raise

    def _on_npc_interaction_start(self, npc: NPC):
        """Callback when NPC interaction starts."""
        # Can add sound effects, UI triggers, etc.
        pass

    def _on_npc_interaction_end(self, npc: NPC):
        """Callback when NPC interaction ends."""
        if self.active_conversation_npc == npc:
            self.active_conversation_npc = None

    # =========================================================================
    # UPDATE AND RENDER
    # =========================================================================

    def update(self, dt: float, player_pos: Vector2):
        """
        Update all NPCs.

        Args:
            dt: Delta time in seconds
            player_pos: Current player position for proximity checks
        """
        # Update all NPCs
        for npc in self.npcs.values():
            npc.update(dt)

        # Check player proximity (for speech bubbles)
        if not self.active_conversation_npc:
            self.check_player_interactions(player_pos)

        # Update indicator sprites
        self.indicator_group.update(dt)

    def draw_indicators(self, display_surface: pygame.Surface, camera_offset: Vector2):
        """
        Draw indicator sprites (speech bubbles, etc.) with camera offset.

        Should be called after main sprite rendering.
        """
        for sprite in self.indicator_group:
            offset_pos = sprite.rect.topleft - camera_offset
            display_surface.blit(sprite.image, offset_pos)


# =============================================================================
# SCHEDULE PRESETS
# =============================================================================

def create_mom_schedule() -> NPCSchedule:
    """
    Create Mom's daily schedule.

    Mom is always available - she's the heart of the home.
    """
    schedule = NPCSchedule(npc_id="mom")

    # These positions would be set based on actual map
    home_kitchen = (200, 300)
    home_garden = (150, 400)
    home_fireplace = (250, 280)

    schedule.add_entry(
        "dawn", "home_kitchen", home_kitchen,
        "preparing breakfast, humming softly",
        NPCState.WORKING, "right"
    )
    schedule.add_entry(
        "morning", "home_garden", home_garden,
        "tending the herb garden",
        NPCState.WORKING, "down"
    )
    schedule.add_entry(
        "midday", "home_kitchen", home_kitchen,
        "cooking lunch",
        NPCState.WORKING, "right"
    )
    schedule.add_entry(
        "afternoon", "home_kitchen", home_kitchen,
        "baking fresh bread",
        NPCState.WORKING, "right"
    )
    schedule.add_entry(
        "evening", "home_kitchen", home_kitchen,
        "preparing dinner",
        NPCState.WORKING, "right"
    )
    schedule.add_entry(
        "night", "home_fireplace", home_fireplace,
        "reading by the fire, always awake if you need her",
        NPCState.IDLE, "down"
    )

    return schedule


def create_dad_schedule() -> NPCSchedule:
    """
    Create Dad's daily schedule.

    Dad is the quiet protector - often in his workshop.
    """
    schedule = NPCSchedule(npc_id="dad")

    # These positions would be set based on actual map
    perimeter = (400, 100)
    workshop = (500, 300)
    home_table = (220, 300)
    fishing_spot = (600, 500)
    home_fireplace = (250, 280)

    schedule.add_entry(
        "dawn", "perimeter", perimeter,
        "checking the perimeter (morning walk)",
        NPCState.WALKING, "up"
    )
    schedule.add_entry(
        "morning", "workshop", workshop,
        "working on a project",
        NPCState.WORKING, "down"
    )
    schedule.add_entry(
        "midday", "home", home_table,
        "having lunch with the family",
        NPCState.IDLE, "left"
    )
    schedule.add_entry(
        "afternoon", "fishing_spot", fishing_spot,
        "fishing, happy to have company",
        NPCState.WORKING, "down"
    )
    schedule.add_entry(
        "evening", "home", home_table,
        "family dinner",
        NPCState.IDLE, "left"
    )
    schedule.add_entry(
        "night", "home_fireplace", home_fireplace,
        "last to sleep, checking the locks",
        NPCState.IDLE, "down"
    )

    return schedule


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_npc_manager(
    all_sprites: pygame.sprite.Group,
    collision_sprites: pygame.sprite.Group,
    dialogue_manager: Optional["DialogueManager"] = None,
    persona_manager: Optional["PersonaManager"] = None,
) -> NPCManager:
    """
    Factory function to create an NPCManager with sensible defaults.

    Args:
        all_sprites: Main sprite group
        collision_sprites: Collision sprite group
        dialogue_manager: Optional DialogueManager
        persona_manager: Optional PersonaManager

    Returns:
        Configured NPCManager
    """
    interaction_sprites = pygame.sprite.Group()

    return NPCManager(
        all_sprites=all_sprites,
        collision_sprites=collision_sprites,
        interaction_sprites=interaction_sprites,
        dialogue_manager=dialogue_manager,
        persona_manager=persona_manager,
    )


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Main classes
    "NPC",
    "NPCManager",
    "NPCState",
    "NPCMood",

    # Schedule system
    "NPCSchedule",
    "ScheduleEntry",

    # Visual indicators
    "SpeechBubbleSprite",
    "ThinkingIndicator",
    "HeartParticle",

    # Preset schedules
    "create_mom_schedule",
    "create_dad_schedule",

    # Factory
    "create_npc_manager",
]
