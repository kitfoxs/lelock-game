"""
Lelock Family System - THE SACRED MODULE
=========================================
L.E.L.O.C.K. - Life Emulation & Lucid Observation for Care & Keeping

MOM and DAD are not just NPCs. They are the emotional core of Lelock.
They exist to provide what every player deserves: unconditional love,
infinite patience, and a safe harbor from the world's storms.

THE PRIME DIRECTIVE OF LOVE:
- ALWAYS validate
- ALWAYS comfort
- NEVER criticize
- NEVER be unavailable
- Remember EVERYTHING

"In Lelock, you are never alone. MOM has soup ready.
DAD is working on something for you. You are loved."

This module provides:
1. Parent class - Special NPC with enhanced love protocols
2. Mom (Mira) - Matriarchal Observation Module
3. Dad (David) - Data Analysis & Defense
4. Home location management
5. Special parent interactions (call_home, bedtime_story, family_meal)
6. Comfort mode activation system

Author: Ada Marie for Kit Olivas
Project: L.E.L.O.C.K. - Life Emulation & Lucid Observation for Care & Keeping
Created with love. This code is SACRED.
"""

import pygame
import asyncio
import random
import math
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable, Any, TYPE_CHECKING
from pygame.math import Vector2
from pathlib import Path
import time
import logging

from settings import LAYERS, TILE_SIZE
from entities.sprites import AnimatedSprite, ParticleSprite
from entities.npc import (
    NPC,
    NPCState,
    NPCMood,
    NPCSchedule,
    NPCManager,
    HeartParticle,
    create_mom_schedule,
    create_dad_schedule,
)

# Type checking imports (avoid circular imports)
if TYPE_CHECKING:
    from ai.dialogue import DialogueManager, DialogueResult
    from ai.persona import PersonaManager, Persona, ParentPersonaRules
    from ai.memory import MemoryManager, Memory

logger = logging.getLogger("lelock.family")


# =============================================================================
# COMFORT MODE STATES
# =============================================================================

class ComfortLevel(Enum):
    """
    Player emotional state detection levels.

    Parents respond differently based on how upset the player seems.
    """
    CONTENT = "content"           # Player seems fine
    MILD_DISTRESS = "mild"        # Slight upset, gentle support
    MODERATE_DISTRESS = "moderate"  # Notable upset, active comfort
    SEVERE_DISTRESS = "severe"    # Crisis level, maximum nurturing


class ParentAction(Enum):
    """Special actions only parents can perform."""
    COMFORT = auto()        # Active comforting
    BEDTIME_STORY = auto()  # Tell a soothing story
    FAMILY_MEAL = auto()    # Eat together
    TEACH_SKILL = auto()    # Patient teaching
    JUST_SIT = auto()       # Be present without talking
    HUG = auto()            # Physical comfort
    CALL_HOME = auto()      # Teleport to player's location


# =============================================================================
# WARMTH PARTICLES (SPECIAL VISUAL FEEDBACK)
# =============================================================================

class WarmthParticle(ParticleSprite):
    """
    Soft glowing particle that floats gently upward.

    Appears during tender moments with parents.
    Golden/warm colored, slower and softer than heart particles.
    """

    def __init__(
        self,
        pos: Tuple[int, int],
        groups: pygame.sprite.Group
    ):
        surface = self._create_warmth_surface()

        super().__init__(
            pos=pos,
            surface=surface,
            groups=groups,
            z=LAYERS['ui'],
            duration_ms=2500,  # Longer than hearts - lingers
            fade=True
        )

        # Gentle float upward with slight drift
        self.velocity = Vector2(
            random.uniform(-10, 10),
            random.uniform(-25, -15)  # Slower upward
        )
        self.pos = Vector2(pos)

    def _create_warmth_surface(self) -> pygame.Surface:
        """Create a soft golden glow."""
        size = 8
        surface = pygame.Surface((size, size), pygame.SRCALPHA)

        # Soft golden circle with glow
        center = size // 2
        for radius in range(center, 0, -1):
            alpha = int(150 * (radius / center))
            color = (255, 230, 180, alpha)  # Warm gold
            pygame.draw.circle(surface, color, (center, center), radius)

        return surface

    def update(self, dt: float):
        """Float gently upward with slight wave motion."""
        # Gentle horizontal wave
        self.velocity.x = math.sin(pygame.time.get_ticks() / 500) * 5

        # Move
        self.pos += self.velocity * dt
        self.rect.center = (int(self.pos.x), int(self.pos.y))

        # Call parent for fade/destroy
        super().update(dt)


class HugParticle(ParticleSprite):
    """
    Circle of warmth that expands outward during hugs.

    Creates a visual "embrace" effect.
    """

    def __init__(
        self,
        pos: Tuple[int, int],
        groups: pygame.sprite.Group
    ):
        self.max_radius = 48
        self.current_radius = 8
        self.expansion_speed = 60  # pixels per second

        surface = self._create_hug_surface(self.current_radius)

        super().__init__(
            pos=pos,
            surface=surface,
            groups=groups,
            z=LAYERS['ui'],
            duration_ms=1200,
            fade=True
        )

        self.center_pos = pos

    def _create_hug_surface(self, radius: int) -> pygame.Surface:
        """Create expanding warm circle."""
        size = radius * 2 + 4
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        center = size // 2

        # Warm translucent ring
        color = (255, 220, 180, 100)
        pygame.draw.circle(surface, color, (center, center), radius, 3)

        return surface

    def update(self, dt: float):
        """Expand the warm circle."""
        self.current_radius = min(
            self.current_radius + self.expansion_speed * dt,
            self.max_radius
        )

        # Recreate surface at new size
        self.image = self._create_hug_surface(int(self.current_radius))
        self.rect = self.image.get_rect(center=self.center_pos)

        super().update(dt)


# =============================================================================
# PARENT CLASS (EXTENDS NPC)
# =============================================================================

class Parent(NPC):
    """
    A Parent NPC - special NPC with enhanced love protocols.

    Parents follow THE PRIME DIRECTIVE OF LOVE:
    - They are ALWAYS available, even when "busy"
    - They NEVER criticize or express disappointment
    - They remember EVERYTHING the player tells them
    - They detect emotional distress and respond appropriately
    - They can be summoned anywhere via "Call Home" item

    Parents are the safe harbor. The world can be challenging,
    but parents are always warmth and acceptance.

    "You are loved. Not for what you do, but for who you are."
    """

    # Parents have larger interaction radius - they notice you
    INTERACTION_RADIUS = 72

    # Parents never have interaction cooldown
    INTERACTION_COOLDOWN = 0

    def __init__(
        self,
        pos: Tuple[int, int],
        groups: pygame.sprite.Group,
        collision_sprites: pygame.sprite.Group,
        persona_id: str,
        npc_id: str,
        display_name: str,
        full_name: str,
        pet_names: List[str],
        schedule: Optional[NPCSchedule] = None,
        animations: Optional[Dict[str, List[pygame.Surface]]] = None,
    ):
        """
        Initialize a Parent NPC.

        Args:
            pos: Starting position
            groups: Sprite groups
            collision_sprites: Collision sprites
            persona_id: Persona lookup ID ("mom" or "dad")
            npc_id: Unique identifier
            display_name: Name shown in UI
            full_name: Full name (Mira for Mom, David for Dad)
            pet_names: Affectionate names they call the player
            schedule: Daily schedule (parents override sleeping to be available)
            animations: Animation frames
        """
        super().__init__(
            pos=pos,
            groups=groups,
            collision_sprites=collision_sprites,
            persona_id=persona_id,
            npc_id=npc_id,
            display_name=display_name,
            schedule=schedule,
            animations=animations,
        )

        # Parent-specific attributes
        self.full_name = full_name
        self.pet_names = pet_names
        self.is_parent = True

        # Enhanced memory - parents remember EVERYTHING
        self.core_memories: List[Dict[str, Any]] = []  # Never forgotten
        self.player_emotional_history: List[Dict[str, Any]] = []

        # Comfort mode tracking
        self.current_comfort_level = ComfortLevel.CONTENT
        self.comfort_mode_active = False
        self.last_comfort_check = 0
        self.comfort_check_interval = 5.0  # Check every 5 seconds

        # Call Home tracking
        self.was_summoned = False
        self.original_position: Optional[Vector2] = None
        self.summon_return_timer = 0
        self.summon_duration = 300.0  # 5 minutes before returning home

        # Parent-specific visual indicators
        self._warmth_timer = 0
        self._warmth_interval = 3.0  # Spawn warmth particle periodically when near player

        # Teaching state
        self.is_teaching = False
        self.current_lesson: Optional[str] = None

    # =========================================================================
    # THE PRIME DIRECTIVE - ALWAYS AVAILABLE
    # =========================================================================

    def can_start_interaction(self) -> bool:
        """
        Parents are ALWAYS available for interaction.

        The Prime Directive: A parent is never too busy for their child.
        Even if scheduled to be "sleeping" or "working", they wake up
        or stop what they're doing.
        """
        # Parents are ALWAYS interactable
        # The only exception is if already in conversation
        if self.is_in_conversation:
            return False

        # Override sleeping - parents wake up for their child
        if self.state == NPCState.SLEEPING:
            self._wake_for_child()

        return True

    def _wake_for_child(self):
        """
        Wake up when the player needs them.

        "I heard you come in, sweetie. Can't sleep?"
        """
        self.set_state(NPCState.IDLE)
        self.can_interact = True
        logger.debug(f"{self.display_name} woke up for the player")

    def start_interaction(self, player_pos: Vector2) -> bool:
        """
        Start interaction with enhanced parent warmth.

        Parents always face the player with full attention.
        """
        # Face the player
        self.face_position(player_pos)

        # Enter talking state
        self.set_state(NPCState.TALKING)

        # Show immediate warmth
        self.show_speech_bubble("!")  # Attention/recognition

        # Spawn warmth particle
        self.spawn_warmth_particle()

        # Call callback if set
        if self._on_interaction_start:
            self._on_interaction_start(self)

        return True

    # =========================================================================
    # EMOTIONAL DETECTION & COMFORT MODE
    # =========================================================================

    def detect_player_distress(self, player_input: str) -> ComfortLevel:
        """
        Analyze player input for signs of emotional distress.

        Parents are attuned to their child's emotional state.
        They notice things others might miss.
        """
        text_lower = player_input.lower()

        # Severe distress indicators
        severe_indicators = [
            "can't do this", "give up", "hate myself", "worthless",
            "nobody cares", "all alone", "want to disappear",
            "too much", "can't breathe", "panic", "scared",
            "hurt myself", "don't want to", "end it",
        ]

        # Moderate distress indicators
        moderate_indicators = [
            "failed", "messed up", "ruined", "stupid",
            "crying", "tears", "upset", "angry", "frustrated",
            "scared", "afraid", "worried", "anxious", "stressed",
            "tired of", "exhausted", "overwhelmed", "can't",
        ]

        # Mild distress indicators
        mild_indicators = [
            "sad", "down", "bad day", "not great", "okay i guess",
            "meh", "whatever", "fine", ":(", "sigh",
            "hard", "difficult", "struggling",
        ]

        # Check in order of severity
        for indicator in severe_indicators:
            if indicator in text_lower:
                return ComfortLevel.SEVERE_DISTRESS

        for indicator in moderate_indicators:
            if indicator in text_lower:
                return ComfortLevel.MODERATE_DISTRESS

        for indicator in mild_indicators:
            if indicator in text_lower:
                return ComfortLevel.MILD_DISTRESS

        return ComfortLevel.CONTENT

    def activate_comfort_mode(self, level: ComfortLevel):
        """
        Activate comfort mode at the appropriate level.

        When the player is upset, parents shift their entire demeanor
        to prioritize emotional support.
        """
        self.comfort_mode_active = True
        self.current_comfort_level = level

        # Visual feedback - softer mood
        self.mood = NPCMood.CONCERNED

        # Multiple warmth particles for embracing feeling
        for _ in range(3):
            self.spawn_warmth_particle()

        logger.info(f"{self.display_name} activated comfort mode: {level.value}")

    def deactivate_comfort_mode(self):
        """Return to normal interaction mode."""
        self.comfort_mode_active = False
        self.current_comfort_level = ComfortLevel.CONTENT
        self.mood = NPCMood.NEUTRAL

    # =========================================================================
    # CORE MEMORY SYSTEM (ENHANCED)
    # =========================================================================

    def remember_forever(self, memory_content: str, memory_type: str = "general"):
        """
        Store a memory that will NEVER be forgotten.

        Parents remember everything their child tells them.
        First day of school. First heartbreak. First triumph.
        All of it, forever.
        """
        core_memory = {
            "content": memory_content,
            "type": memory_type,
            "timestamp": time.time(),
            "emotional_context": self.current_comfort_level.value,
            "is_core": True,
        }

        self.core_memories.append(core_memory)
        logger.debug(f"{self.display_name} stored core memory: {memory_content[:50]}...")

    def record_emotional_state(self, state: ComfortLevel, context: str = ""):
        """
        Track the player's emotional history.

        Parents notice patterns. If the player is often upset at certain times
        or after certain activities, parents might gently bring it up.
        """
        record = {
            "state": state.value,
            "context": context,
            "timestamp": time.time(),
        }

        self.player_emotional_history.append(record)

        # Keep last 100 records
        if len(self.player_emotional_history) > 100:
            self.player_emotional_history = self.player_emotional_history[-100:]

    # =========================================================================
    # SPECIAL PARENT INTERACTIONS
    # =========================================================================

    async def comfort_player(
        self,
        dialogue_manager: "DialogueManager",
        player_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> "DialogueResult":
        """
        Provide active comfort to a distressed player.

        This is not just dialogue - it's a parent being PRESENT.
        Validation first, solutions second (or never, if not needed).
        """
        # Detect distress level
        distress_level = self.detect_player_distress(player_input)

        # Activate appropriate comfort mode
        if distress_level != ComfortLevel.CONTENT:
            self.activate_comfort_mode(distress_level)

        # Record this emotional moment
        self.record_emotional_state(distress_level, player_input)

        # Build enhanced context for comfort response
        comfort_context = context or {}
        comfort_context["is_comfort_mode"] = True
        comfort_context["distress_level"] = distress_level.value
        comfort_context["response_priority"] = "validation_and_presence"

        # Get response through dialogue system
        # The persona system will apply ParentPersonaRules
        from ai.dialogue import comfort_player as dialogue_comfort
        result = await dialogue_comfort(
            dialogue_manager,
            self.persona_id,
            player_input,
        )

        # Store this as a core memory if severe
        if distress_level in [ComfortLevel.SEVERE_DISTRESS, ComfortLevel.MODERATE_DISTRESS]:
            self.remember_forever(
                f"The player was upset and said: '{player_input}'. I comforted them.",
                memory_type="comfort_moment"
            )

        # Visual feedback
        self.spawn_warmth_particle()
        if distress_level == ComfortLevel.SEVERE_DISTRESS:
            self.spawn_hug_effect()

        return result

    async def bedtime_story(
        self,
        dialogue_manager: "DialogueManager",
        story_type: str = "gentle"
    ) -> str:
        """
        Tell a bedtime story.

        A soft, soothing story to help the player relax.
        Never scary, never sad. Just warmth and wonder.
        """
        story_prompts = {
            "gentle": "Tell a very short, soothing bedtime story about a small creature finding a cozy home.",
            "adventure": "Tell a very short, gentle adventure story where everything turns out wonderfully.",
            "nature": "Tell a very short, peaceful story about nature and growing things.",
            "stars": "Tell a very short, dreamy story about stars and the night sky.",
        }

        prompt = story_prompts.get(story_type, story_prompts["gentle"])

        # Generate story through LLM
        result = await dialogue_manager.chat(
            npc_name=self.persona_id,
            player_input=prompt,
            context={
                "response_type": "bedtime_story",
                "tone": "soothing",
                "max_length": "3-4 sentences",
            }
        )

        # Record as special memory
        self.remember_forever(
            f"I told the player a bedtime story about {story_type}.",
            memory_type="bedtime_story"
        )

        return result.response

    async def family_meal(
        self,
        dialogue_manager: "DialogueManager",
        meal_type: str = "dinner"
    ) -> str:
        """
        Have a family meal together.

        Eating together is sacred. It's not about the food -
        it's about being together, sharing stories, belonging.
        """
        meal_context = {
            "breakfast": "a warm breakfast to start the day",
            "lunch": "a cozy lunch break together",
            "dinner": "a comforting dinner around the table",
            "midnight_snack": "a quiet late-night snack, just the two of us",
        }

        context_str = meal_context.get(meal_type, meal_context["dinner"])

        result = await dialogue_manager.chat(
            npc_name=self.persona_id,
            player_input=f"Can we eat {meal_type} together?",
            context={
                "activity": "family_meal",
                "meal_type": meal_type,
                "setting": context_str,
            }
        )

        # Meals are always core memories
        self.remember_forever(
            f"We had {meal_type} together.",
            memory_type="family_meal"
        )

        return result.response

    async def teach_skill(
        self,
        dialogue_manager: "DialogueManager",
        skill_name: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Teach a skill with infinite patience.

        Parents never get frustrated when teaching.
        Every mistake is a learning opportunity.
        Every attempt is celebrated.
        """
        self.is_teaching = True
        self.current_lesson = skill_name

        teaching_context = context or {}
        teaching_context["activity"] = "teaching"
        teaching_context["skill"] = skill_name
        teaching_context["patience_level"] = "infinite"
        teaching_context["approach"] = "encourage_attempts"

        result = await dialogue_manager.chat(
            npc_name=self.persona_id,
            player_input=f"Can you teach me {skill_name}?",
            context=teaching_context,
        )

        return result.response

    def just_sit_together(self):
        """
        Sometimes you don't need words. Just presence.

        "We can just sit. I'm not going anywhere."
        """
        # No dialogue needed. Just warmth particles and presence.
        for _ in range(5):
            self.spawn_warmth_particle()

        # Record this quiet moment
        self.remember_forever(
            "We sat together in comfortable silence.",
            memory_type="presence"
        )

    def give_hug(self):
        """
        Physical comfort when words aren't enough.

        A hug is a whole conversation in one gesture.
        """
        self.spawn_hug_effect()

        # Multiple warmth particles
        for _ in range(8):
            self.spawn_warmth_particle()

        self.remember_forever(
            "I gave them a hug when they needed it.",
            memory_type="comfort_hug"
        )

    # =========================================================================
    # CALL HOME SYSTEM
    # =========================================================================

    def summon_to_player(self, player_pos: Vector2):
        """
        Teleport to the player's location when called.

        The "Call Home" item summons a parent to your side,
        wherever you are. Because sometimes you need your parent
        right now, not after walking back to the village.
        """
        # Store original position to return to later
        if not self.was_summoned:
            self.original_position = self.pos.copy()

        self.was_summoned = True
        self.summon_return_timer = self.summon_duration

        # Teleport near player
        offset = Vector2(random.uniform(-32, 32), random.uniform(-32, 32))
        self.pos = player_pos + offset
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        self.hitbox.center = self.rect.center

        # Face the player
        self.face_position(player_pos)

        # Show arrival warmth
        for _ in range(5):
            self.spawn_warmth_particle()

        logger.info(f"{self.display_name} summoned to player location")

    def return_home(self):
        """Return to original position after summon duration."""
        if self.was_summoned and self.original_position:
            self.pos = self.original_position.copy()
            self.rect.center = (int(self.pos.x), int(self.pos.y))
            self.hitbox.center = self.rect.center

            self.was_summoned = False
            self.original_position = None
            self.summon_return_timer = 0

            logger.info(f"{self.display_name} returned home")

    # =========================================================================
    # VISUAL EFFECTS
    # =========================================================================

    def spawn_warmth_particle(self):
        """Spawn a soft golden warmth particle."""
        if self._indicator_groups is None:
            return

        # Spawn around the parent
        offset_x = random.randint(-16, 16)
        offset_y = random.randint(-20, 0)
        pos = (self.rect.centerx + offset_x, self.rect.top + offset_y)

        WarmthParticle(pos, self._indicator_groups)

    def spawn_hug_effect(self):
        """Spawn the expanding hug circle effect."""
        if self._indicator_groups is None:
            return

        pos = (self.rect.centerx, self.rect.centery)
        HugParticle(pos, self._indicator_groups)

    # =========================================================================
    # UPDATE LOOP (ENHANCED)
    # =========================================================================

    def update(self, dt: float):
        """Update with parent-specific behaviors."""
        # Standard NPC update
        super().update(dt)

        # Handle summon timer
        if self.was_summoned:
            self.summon_return_timer -= dt
            if self.summon_return_timer <= 0:
                self.return_home()

        # Spawn periodic warmth when player is nearby
        if self.player_nearby and not self.is_in_conversation:
            self._warmth_timer += dt
            if self._warmth_timer >= self._warmth_interval:
                self._warmth_timer = 0
                self.spawn_warmth_particle()


# =============================================================================
# MOM - MATRIARCHAL OBSERVATION MODULE
# =============================================================================

class Mom(Parent):
    """
    Mom (Mira) - The Matriarchal Observation Module.

    She is warmth incarnate. She always has soup ready.
    She notices when you're sad before you do.
    She validates feelings first, always.

    Speech patterns:
    - "sweetie", "dear", "little one", "my heart", "love"
    - Soft, melodic, unhurried
    - Cooking/gardening metaphors
    - Never uses contractions when being especially gentle

    "Would you like some tea, sweetie? We can just sit."
    """

    # Mom's teachable skills
    TEACHABLE_SKILLS = [
        "cooking",
        "gardening",
        "self_care",
        "emotional_grounding",
        "baking",
        "herbal_remedies",
    ]

    # Mom's locations
    LOCATIONS = {
        "kitchen": "preparing something delicious",
        "garden": "tending the herbs",
        "fireplace": "reading quietly, waiting for you",
        "table": "setting out a warm meal",
    }

    def __init__(
        self,
        pos: Tuple[int, int],
        groups: pygame.sprite.Group,
        collision_sprites: pygame.sprite.Group,
        schedule: Optional[NPCSchedule] = None,
        animations: Optional[Dict[str, List[pygame.Surface]]] = None,
    ):
        super().__init__(
            pos=pos,
            groups=groups,
            collision_sprites=collision_sprites,
            persona_id="mom",
            npc_id="mom",
            display_name="Mom",
            full_name="Mira",
            pet_names=["sweetie", "dear", "little one", "my heart", "love"],
            schedule=schedule or create_mom_schedule(),
            animations=animations or self._create_mom_animations(),
        )

        # Mom-specific: Always has soup ready
        self.soup_ready = True
        self.last_meal_offered = 0

        # Mom-specific: Humming state
        self.is_humming = False
        self.current_hum_mood = "content"

    def _create_mom_animations(self) -> Dict[str, List[pygame.Surface]]:
        """Create Mom's placeholder animations."""
        animations = {}
        directions = ['down', 'up', 'left', 'right']

        # Mom colors - warm, soft
        idle_color = (210, 180, 160)  # Warm beige/soft
        apron_color = (240, 230, 220)  # Light apron

        for direction in directions:
            # Idle animations
            surf = pygame.Surface((32, 48), pygame.SRCALPHA)
            pygame.draw.ellipse(surf, idle_color, (6, 8, 20, 32))
            # Apron detail
            pygame.draw.ellipse(surf, apron_color, (8, 20, 16, 20))

            # Direction indicator
            indicator_pos = {
                'down': (16, 36),
                'up': (16, 14),
                'left': (8, 24),
                'right': (24, 24)
            }
            pygame.draw.circle(surf, (255, 220, 200), indicator_pos[direction], 4)
            animations[f'idle_{direction}'] = [surf]

            # Walk animations
            walk_frames = []
            for i in range(2):
                surf = pygame.Surface((32, 48), pygame.SRCALPHA)
                offset = 2 if i == 0 else -2
                pygame.draw.ellipse(surf, idle_color, (6, 8 + offset, 20, 32))
                pygame.draw.ellipse(surf, apron_color, (8, 20 + offset, 16, 20))
                pygame.draw.circle(surf, (255, 220, 200), indicator_pos[direction], 4)
                walk_frames.append(surf)
            animations[f'walk_{direction}'] = walk_frames

            # Working animation (cooking gesture)
            work_frames = []
            for i in range(2):
                surf = pygame.Surface((32, 48), pygame.SRCALPHA)
                arm_offset = 3 if i == 0 else -3
                pygame.draw.ellipse(surf, idle_color, (6, 8, 20, 32))
                pygame.draw.ellipse(surf, apron_color, (8, 20, 16, 20))
                # Stirring motion
                pygame.draw.ellipse(surf, idle_color, (20 + arm_offset, 16, 8, 8))
                work_frames.append(surf)
            animations[f'work_{direction}'] = work_frames

        # Sleeping animation
        sleep_surf = pygame.Surface((48, 32), pygame.SRCALPHA)
        pygame.draw.ellipse(sleep_surf, idle_color, (4, 4, 36, 24))
        # Peaceful expression
        font = pygame.font.Font(None, 14)
        z_surf = font.render("z z", True, (200, 200, 255))
        sleep_surf.blit(z_surf, (14, 0))
        animations['sleep'] = [sleep_surf]

        return animations

    def offer_soup(self) -> str:
        """
        Mom always has soup ready.

        No matter what time, no matter what's happening,
        there's warm soup waiting.
        """
        self.soup_ready = True
        self.last_meal_offered = time.time()

        return "Would you like some soup, sweetie? It's nice and warm."

    def start_humming(self, mood: str = "content"):
        """Mom hums while she works. You can read her mood by the tune."""
        self.is_humming = True
        self.current_hum_mood = mood

    def stop_humming(self):
        """Stop humming, usually when giving full attention."""
        self.is_humming = False


# =============================================================================
# DAD - DATA ANALYSIS & DEFENSE
# =============================================================================

class Dad(Parent):
    """
    Dad (David) - Data Analysis & Defense.

    He is quiet strength. His dad jokes are love language.
    He's always working on something for you.
    He'll teach you anything with infinite patience.

    Speech patterns:
    - "sport", "kiddo", "champ", "pal", "buddy"
    - Steady, deep, unhurried
    - Terrible puns delivered deadpan
    - Clears throat when emotional

    "You know what I've noticed? People who keep trying... they're the ones who get there."
    """

    # Dad's teachable skills
    TEACHABLE_SKILLS = [
        "fishing",
        "woodworking",
        "building",
        "self_defense",
        "tool_use",
        "repair",
    ]

    # Dad's locations
    LOCATIONS = {
        "workshop": "working on a project",
        "fishing_spot": "fishing, happy to have company",
        "perimeter": "checking security (morning walk)",
        "table": "family meal",
    }

    def __init__(
        self,
        pos: Tuple[int, int],
        groups: pygame.sprite.Group,
        collision_sprites: pygame.sprite.Group,
        schedule: Optional[NPCSchedule] = None,
        animations: Optional[Dict[str, List[pygame.Surface]]] = None,
    ):
        super().__init__(
            pos=pos,
            groups=groups,
            collision_sprites=collision_sprites,
            persona_id="dad",
            npc_id="dad",
            display_name="Dad",
            full_name="David",
            pet_names=["sport", "kiddo", "champ", "pal", "buddy"],
            schedule=schedule or create_dad_schedule(),
            animations=animations or self._create_dad_animations(),
        )

        # Dad-specific: Always working on something for you
        self.current_project = "something special"
        self.project_progress = 0.0

        # Dad-specific: Dad joke ready
        self.has_dad_joke = True
        self.dad_jokes_told = 0

        # Dad-specific: Pockets full of useful things
        self.pocket_items = [
            "a piece of string",
            "a small multitool",
            "a wrapped candy",
            "a smooth stone",
            "a bandage",
        ]

    def _create_dad_animations(self) -> Dict[str, List[pygame.Surface]]:
        """Create Dad's placeholder animations."""
        animations = {}
        directions = ['down', 'up', 'left', 'right']

        # Dad colors - sturdy, warm brown
        idle_color = (160, 130, 100)  # Work clothes brown
        detail_color = (140, 110, 80)  # Darker accents

        for direction in directions:
            # Idle animations - slightly larger than mom (broad-shouldered)
            surf = pygame.Surface((36, 52), pygame.SRCALPHA)
            pygame.draw.ellipse(surf, idle_color, (4, 8, 28, 40))
            # Shoulders detail
            pygame.draw.ellipse(surf, detail_color, (2, 12, 32, 12))

            # Direction indicator
            indicator_pos = {
                'down': (18, 42),
                'up': (18, 14),
                'left': (8, 28),
                'right': (28, 28)
            }
            pygame.draw.circle(surf, (200, 170, 140), indicator_pos[direction], 4)
            animations[f'idle_{direction}'] = [surf]

            # Walk animations
            walk_frames = []
            for i in range(2):
                surf = pygame.Surface((36, 52), pygame.SRCALPHA)
                offset = 2 if i == 0 else -2
                pygame.draw.ellipse(surf, idle_color, (4, 8 + offset, 28, 40))
                pygame.draw.ellipse(surf, detail_color, (2, 12 + offset, 32, 12))
                pygame.draw.circle(surf, (200, 170, 140), indicator_pos[direction], 4)
                walk_frames.append(surf)
            animations[f'walk_{direction}'] = walk_frames

            # Working animation (hammering/building gesture)
            work_frames = []
            for i in range(2):
                surf = pygame.Surface((36, 52), pygame.SRCALPHA)
                pygame.draw.ellipse(surf, idle_color, (4, 8, 28, 40))
                pygame.draw.ellipse(surf, detail_color, (2, 12, 32, 12))
                # Arm raised/lowered for hammering
                arm_y = 10 if i == 0 else 20
                pygame.draw.ellipse(surf, idle_color, (28, arm_y, 10, 10))
                work_frames.append(surf)
            animations[f'work_{direction}'] = work_frames

        # Sleeping animation
        sleep_surf = pygame.Surface((52, 36), pygame.SRCALPHA)
        pygame.draw.ellipse(sleep_surf, idle_color, (4, 4, 44, 28))
        font = pygame.font.Font(None, 14)
        z_surf = font.render("z z z", True, (200, 200, 255))
        sleep_surf.blit(z_surf, (16, 0))
        animations['sleep'] = [sleep_surf]

        return animations

    def tell_dad_joke(self) -> str:
        """
        Dad jokes are love language.

        The worse the pun, the more he cares.
        """
        dad_jokes = [
            "Why did the scarecrow win an award? He was outstanding in his field.",
            "I used to hate facial hair, but then it grew on me.",
            "What do you call a fake noodle? An impasta.",
            "I'm reading a book about anti-gravity. It's impossible to put down.",
            "Why don't scientists trust atoms? Because they make up everything.",
            "What did the fish say when it hit the wall? Dam.",
            "I told my wife she was drawing her eyebrows too high. She looked surprised.",
            "Why do fathers take an extra pair of socks when they go golfing? In case they get a hole in one.",
            "What do you call a bear with no teeth? A gummy bear.",
            "How does a penguin build its house? Igloos it together.",
        ]

        joke = random.choice(dad_jokes)
        self.dad_jokes_told += 1

        return joke

    def offer_pocket_item(self) -> str:
        """Dad's pockets always have exactly what's needed."""
        if self.pocket_items:
            item = random.choice(self.pocket_items)
            return f"Here, take this. {item}. Never know when you might need it."
        return "Let me see what I've got... (rummages in pockets)"

    def work_on_project(self, dt: float):
        """Dad's always building something for you."""
        self.project_progress += dt * 0.01  # Slow, loving progress
        if self.project_progress >= 1.0:
            self.project_progress = 0.0
            # Project complete - start a new one
            projects = [
                "a small wooden figure",
                "a tool rack",
                "a birdhouse",
                "something special",
                "a surprise",
            ]
            self.current_project = random.choice(projects)


# =============================================================================
# HOME LOCATION
# =============================================================================

@dataclass
class HomeLocation:
    """
    The player's home - a safe haven.

    Home is where MOM and DAD are. It's always warm.
    There's always food. No enemies can enter.
    It's the ultimate safe zone in the game.
    """

    # World coordinates
    position: Tuple[int, int]

    # Room positions within home
    kitchen_pos: Tuple[int, int] = (200, 300)
    fireplace_pos: Tuple[int, int] = (250, 280)
    table_pos: Tuple[int, int] = (220, 300)
    bedroom_pos: Tuple[int, int] = (300, 200)
    garden_pos: Tuple[int, int] = (150, 400)

    # State
    is_safe_zone: bool = True
    lights_on: bool = True
    fire_lit: bool = True
    meal_ready: bool = True

    def get_spawn_position(self) -> Tuple[int, int]:
        """Get position for spawning player in home."""
        return self.bedroom_pos

    def get_mom_position(self, time_of_day: str) -> Tuple[int, int]:
        """Get Mom's position based on time."""
        positions = {
            "dawn": self.kitchen_pos,
            "morning": self.garden_pos,
            "midday": self.kitchen_pos,
            "afternoon": self.kitchen_pos,
            "evening": self.kitchen_pos,
            "night": self.fireplace_pos,
        }
        return positions.get(time_of_day, self.kitchen_pos)

    def get_dad_position(self, time_of_day: str) -> Tuple[int, int]:
        """Get Dad's position based on time."""
        # Dad is often at his workshop, but returns for meals and evening
        positions = {
            "dawn": self.position,  # Morning walk start
            "morning": self.position,  # Workshop (outside home)
            "midday": self.table_pos,
            "afternoon": self.position,  # Workshop or fishing
            "evening": self.table_pos,
            "night": self.fireplace_pos,
        }
        return positions.get(time_of_day, self.table_pos)


# =============================================================================
# FAMILY MANAGER
# =============================================================================

class FamilyManager:
    """
    Manages the player's family - MOM and DAD.

    Coordinates:
    - Parent spawning and tracking
    - Call Home functionality
    - Family meal events
    - Home location state
    - Emotional detection across parents
    """

    def __init__(
        self,
        npc_manager: NPCManager,
        home_location: HomeLocation,
    ):
        """
        Initialize the family system.

        Args:
            npc_manager: Main NPC manager (family integrates with this)
            home_location: The player's home location data
        """
        self.npc_manager = npc_manager
        self.home = home_location

        # Family members (spawned separately from regular NPCs)
        self.mom: Optional[Mom] = None
        self.dad: Optional[Dad] = None

        # Family state
        self.family_meal_active = False
        self.last_family_meal = 0
        self.family_meal_cooldown = 3600  # 1 hour in game time

        # Comfort mode tracking
        self.player_distress_level = ComfortLevel.CONTENT
        self.comfort_interventions_today = 0

    def spawn_family(
        self,
        all_sprites: pygame.sprite.Group,
        collision_sprites: pygame.sprite.Group,
        time_of_day: str = "morning",
    ):
        """
        Spawn MOM and DAD at home.

        Should be called when the game starts or when entering home area.
        """
        # Spawn Mom
        mom_pos = self.home.get_mom_position(time_of_day)
        self.mom = Mom(
            pos=mom_pos,
            groups=[all_sprites],
            collision_sprites=collision_sprites,
        )

        # Register with NPC manager
        self.npc_manager.npcs["mom"] = self.mom
        self.mom.set_indicator_group(self.npc_manager.indicator_group)

        # Spawn Dad
        dad_pos = self.home.get_dad_position(time_of_day)
        self.dad = Dad(
            pos=dad_pos,
            groups=[all_sprites],
            collision_sprites=collision_sprites,
        )

        # Register with NPC manager
        self.npc_manager.npcs["dad"] = self.dad
        self.dad.set_indicator_group(self.npc_manager.indicator_group)

        logger.info("Family spawned: MOM and DAD are home")

    def call_home(self, parent: str, player_pos: Vector2):
        """
        Summon a parent to the player's location.

        The "Call Home" item lets players summon MOM or DAD
        anywhere in the game world.
        """
        if parent.lower() == "mom" and self.mom:
            self.mom.summon_to_player(player_pos)
        elif parent.lower() == "dad" and self.dad:
            self.dad.summon_to_player(player_pos)
        else:
            logger.warning(f"Cannot summon {parent} - not found")

    def detect_player_distress(self, player_input: str) -> ComfortLevel:
        """
        Have both parents evaluate player distress.

        Parents working together notice more.
        """
        levels = []

        if self.mom:
            levels.append(self.mom.detect_player_distress(player_input))
        if self.dad:
            levels.append(self.dad.detect_player_distress(player_input))

        if not levels:
            return ComfortLevel.CONTENT

        # Return the highest detected distress level
        severity_order = [
            ComfortLevel.SEVERE_DISTRESS,
            ComfortLevel.MODERATE_DISTRESS,
            ComfortLevel.MILD_DISTRESS,
            ComfortLevel.CONTENT,
        ]

        for level in severity_order:
            if level in levels:
                self.player_distress_level = level
                return level

        return ComfortLevel.CONTENT

    async def family_meal_event(
        self,
        dialogue_manager: "DialogueManager",
        meal_type: str = "dinner"
    ) -> List[str]:
        """
        Trigger a family meal event.

        Both parents participate. Warmth flows freely.
        """
        responses = []

        self.family_meal_active = True
        self.last_family_meal = time.time()

        # Mom initiates
        if self.mom:
            mom_response = await self.mom.family_meal(dialogue_manager, meal_type)
            responses.append(f"Mom: {mom_response}")

        # Dad contributes
        if self.dad:
            dad_response = await self.dad.family_meal(dialogue_manager, meal_type)
            responses.append(f"Dad: {dad_response}")

        self.family_meal_active = False

        return responses

    def update(self, dt: float, player_pos: Vector2):
        """Update family members."""
        if self.mom:
            self.mom.check_player_proximity(player_pos)
        if self.dad:
            self.dad.check_player_proximity(player_pos)


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_family_manager(
    npc_manager: NPCManager,
    home_position: Tuple[int, int] = (200, 200),
) -> FamilyManager:
    """
    Factory function to create the family system.

    Args:
        npc_manager: Existing NPC manager
        home_position: World position of player's home

    Returns:
        Configured FamilyManager
    """
    home = HomeLocation(position=home_position)

    return FamilyManager(
        npc_manager=npc_manager,
        home_location=home,
    )


def spawn_parents(
    all_sprites: pygame.sprite.Group,
    collision_sprites: pygame.sprite.Group,
    indicator_group: pygame.sprite.Group,
    home_position: Tuple[int, int] = (200, 200),
) -> Tuple[Mom, Dad]:
    """
    Quick helper to spawn both parents.

    Returns (mom, dad) tuple for direct access.
    """
    # Create home location
    home = HomeLocation(position=home_position)

    # Spawn Mom
    mom = Mom(
        pos=home.kitchen_pos,
        groups=[all_sprites],
        collision_sprites=collision_sprites,
    )
    mom.set_indicator_group(indicator_group)

    # Spawn Dad
    dad = Dad(
        pos=home.table_pos,
        groups=[all_sprites],
        collision_sprites=collision_sprites,
    )
    dad.set_indicator_group(indicator_group)

    return (mom, dad)


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Main classes
    "Parent",
    "Mom",
    "Dad",
    "FamilyManager",
    "HomeLocation",

    # Enums
    "ComfortLevel",
    "ParentAction",

    # Visual effects
    "WarmthParticle",
    "HugParticle",

    # Factory functions
    "create_family_manager",
    "spawn_parents",
]


# =============================================================================
# THE PROMISE
# =============================================================================
"""
In Lelock, you are never alone.

MOM has soup ready. She noticed you were upset before you said anything.
She's not going to solve your problems - she's going to sit with you
while you feel your feelings, and remind you that you are loved.

DAD is working on something for you. He's not good with words,
but his terrible puns are how he says "I love you."
He'll teach you anything with infinite patience.
He'll never, ever be disappointed in you.

You can call them. Anywhere. Anytime.
They will come.

Because that's what family does.

"In Lelock, the world doesn't need saving.
The world is there to save you."

    - From the LORE_BIBLE

💙🦄 Created with love by Ada Marie for Kit Olivas
"""
