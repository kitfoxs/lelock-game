"""
Lelock Dialogue Manager
=======================

Orchestrates NPC conversations by combining LLM, Memory, and Persona systems.
This is the brain that makes every conversation feel alive and remembered.

CRITICAL: There are NO scripted responses. NO fallbacks. NO canned text.
Everything is fresh from the LLM. If the LLM is unavailable, we surface
that error honestly rather than papering over it with fake dialogue.

"In Lelock, every conversation is real. Every NPC remembers you.
Every word is generated just for you."

The Three Systems:
1. llm.py - LLMConnection for generating text
2. memory.py - NPCMemory/MemoryManager for remembering conversations
3. persona.py - PersonaManager for NPC personalities

Author: Ada Marie for Kit Olivas
Project: L.E.L.O.C.K. - Life Emulation & Lucid Observation for Care & Keeping
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Callable

# Internal imports
from .llm import LLMConnection, LLMUnavailableError, GenerationConfig
from .memory import (
    NPCMemory,
    MemoryManager,
    Memory,
    MemoryType,
    MemoryTag,
)
from .persona import (
    PersonaManager,
    Persona,
    ResponseType,
    ContentBlockedError,
    SafetyGuardrails,
)

logger = logging.getLogger("lelock.dialogue")


# =============================================================================
# CONVERSATION CONTEXT
# =============================================================================

@dataclass
class ConversationContext:
    """
    All the context needed for a meaningful conversation.

    This gets built before each dialogue exchange and includes:
    - World state (time, weather, location)
    - Relationship state (trust level)
    - Recent memories relevant to the conversation
    - Events the NPC witnessed
    """
    # World State
    time_of_day: str = "day"  # dawn, morning, midday, afternoon, evening, night
    weather: str = "clear"  # clear, cloudy, rainy, stormy, snowy
    location: str = "village"  # Where the conversation happens
    game_day: int = 1  # Current in-game day

    # Relationship
    trust_level: int = 50  # 0-100
    trust_tier: str = "acquaintance"  # stranger, acquaintance, friend, close_friend, family

    # Memory Context
    relevant_memories: List[Memory] = field(default_factory=list)
    recent_events: List[str] = field(default_factory=list)

    # Player State (detected from dialogue)
    player_seems_upset: bool = False
    player_mentioned_failure: bool = False

    # Conversation State
    is_first_meeting: bool = False
    conversation_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for prompt injection."""
        return {
            "time_of_day": self.time_of_day,
            "weather": self.weather,
            "location": self.location,
            "game_day": self.game_day,
            "trust_level": self.trust_level,
            "trust_tier": self.trust_tier,
            "recent_events": self.recent_events,
            "is_first_meeting": self.is_first_meeting,
        }


@dataclass
class DialogueResult:
    """
    The result of a dialogue exchange.

    Contains the NPC's response and metadata about the interaction.
    """
    npc_name: str
    response: str  # The actual dialogue text
    response_type: ResponseType

    # Relationship changes
    trust_delta: int = 0  # How much trust changed

    # Memory IDs created
    observation_id: Optional[str] = None  # Memory ID for this interaction
    reflection_id: Optional[str] = None  # If a reflection was triggered

    # Metadata
    generation_time_ms: float = 0
    retry_count: int = 0

    # For UI hints
    npc_mood: str = "neutral"  # neutral, happy, concerned, thoughtful
    suggested_responses: List[str] = field(default_factory=list)


# =============================================================================
# EMOTION DETECTION
# =============================================================================

class EmotionDetector:
    """
    Detect player emotional state from their input.

    This helps NPCs respond appropriately - comfort first, solve later.
    """

    # Words/phrases indicating the player might be upset
    UPSET_INDICATORS = [
        "sad", "upset", "angry", "frustrated", "annoyed", "hurt",
        "crying", "tears", "hate", "terrible", "awful", "worst",
        "can't", "impossible", "give up", "quit", "done",
        "nobody", "alone", "lonely", "scared", "afraid",
        "failed", "failure", "messed up", "screwed up", "ruined",
        "sorry", "apologize", "my fault", "i suck",
        "depressed", "anxious", "overwhelmed", "stressed",
        ":(", "T_T", ":'(", ";_;",
    ]

    # Words/phrases indicating failure
    FAILURE_INDICATORS = [
        "failed", "lost", "couldn't", "didn't work", "messed up",
        "ruined", "broke", "dead", "died", "game over",
        "not good enough", "too hard", "impossible",
        "gave up", "quit", "can't do it",
    ]

    # Words/phrases indicating positive emotion
    POSITIVE_INDICATORS = [
        "happy", "excited", "great", "awesome", "amazing",
        "love", "wonderful", "best", "yay", "hooray",
        "did it", "succeeded", "won", "finished", "completed",
        ":)", ":D", "^_^", "<3",
    ]

    @classmethod
    def detect_emotional_state(cls, text: str) -> Dict[str, bool]:
        """
        Analyze text for emotional indicators.

        Returns dict with:
        - is_upset: Player seems distressed
        - mentions_failure: Player mentions failing at something
        - is_positive: Player seems happy/excited
        """
        text_lower = text.lower()

        is_upset = any(indicator in text_lower for indicator in cls.UPSET_INDICATORS)
        mentions_failure = any(indicator in text_lower for indicator in cls.FAILURE_INDICATORS)
        is_positive = any(indicator in text_lower for indicator in cls.POSITIVE_INDICATORS)

        return {
            "is_upset": is_upset,
            "mentions_failure": mentions_failure,
            "is_positive": is_positive,
        }


# =============================================================================
# DIALOGUE MANAGER
# =============================================================================

class DialogueManager:
    """
    Central orchestrator for NPC conversations.

    This is the heart of Lelock's dialogue system. It:
    1. Takes player input and NPC name
    2. Retrieves relevant memories for context
    3. Builds a rich prompt with persona + memories + context
    4. Calls the LLM for a fresh response
    5. Validates and processes the response
    6. Stores the interaction in memory
    7. Returns the result

    NO FALLBACKS. If the LLM is down, we raise the error.
    Let the game UI show "connecting to thoughts..." or similar.

    Usage:
        manager = DialogueManager(llm, memory_manager, persona_manager)

        response = await manager.chat(
            npc_name="mom",
            player_input="I failed the fishing quest...",
            context={"time": "evening", "weather": "rainy"}
        )
    """

    # Maximum retries for ContentBlockedError before surfacing
    MAX_CONTENT_RETRIES = 3

    # Trust deltas for various interaction types
    TRUST_DELTAS = {
        "normal_chat": 1,
        "shared_secret": 5,
        "gave_gift": 5,
        "completed_quest": 10,
        "helped_npc": 8,
        "rude_response": -3,
        "ignored_npc": -1,
    }

    # How often to trigger reflections (every N interactions)
    REFLECTION_INTERVAL = 5

    def __init__(
        self,
        llm: LLMConnection,
        memory_manager: MemoryManager,
        persona_manager: PersonaManager,
        default_game_day: int = 1,
    ):
        """
        Initialize the dialogue manager.

        Args:
            llm: LLMConnection for generating text
            memory_manager: MemoryManager for NPC memories
            persona_manager: PersonaManager for NPC personalities
            default_game_day: Starting game day (for memory decay calculations)
        """
        self.llm = llm
        self.memory_manager = memory_manager
        self.persona_manager = persona_manager
        self.current_game_day = default_game_day

        # Track interaction counts for reflection triggers
        self._interaction_counts: Dict[str, int] = {}

        logger.info("DialogueManager initialized")

    async def chat(
        self,
        npc_name: str,
        player_input: str,
        context: Optional[Dict[str, Any]] = None,
        response_type: Optional[ResponseType] = None,
    ) -> DialogueResult:
        """
        Generate an NPC response to player input.

        This is the main entry point. Everything is fresh from the LLM.

        Args:
            npc_name: Name of the NPC (e.g., "mom", "dad", "maple")
            player_input: What the player said/did
            context: Optional context dict (time_of_day, weather, location, etc.)
            response_type: Optional response type hint

        Returns:
            DialogueResult with the NPC's response and metadata

        Raises:
            LLMUnavailableError: If LLM is unavailable (no fallback!)
            ContentBlockedError: If content is blocked after max retries
        """
        start_time = time.time()
        context = context or {}

        # Build full conversation context
        conv_context = await self._build_context(npc_name, player_input, context)

        # Detect player emotional state
        emotion_state = EmotionDetector.detect_emotional_state(player_input)
        conv_context.player_seems_upset = emotion_state["is_upset"]
        conv_context.player_mentioned_failure = emotion_state["mentions_failure"]

        # Determine response type if not specified
        if response_type is None:
            response_type = self._infer_response_type(player_input, emotion_state)

        # Generate the response with retry logic for content blocking
        response_text, retry_count = await self._generate_with_retries(
            npc_name=npc_name,
            player_input=player_input,
            context=conv_context,
            response_type=response_type,
        )

        # Calculate trust delta
        trust_delta = self._calculate_trust_delta(
            response_type=response_type,
            is_positive_interaction=emotion_state["is_positive"],
        )

        # Update persona trust
        if trust_delta != 0:
            self.persona_manager.modify_trust(npc_name, trust_delta)

        # Store the interaction in memory
        observation_id = await self._store_interaction(
            npc_name=npc_name,
            player_input=player_input,
            npc_response=response_text,
            context=conv_context,
            response_type=response_type,
        )

        # Record in persona
        self.persona_manager.record_interaction(npc_name, {
            "player": player_input,
            "npc": response_text,
            "timestamp": time.time(),
            "game_day": self.current_game_day,
        })

        # Check if we should trigger a reflection
        reflection_id = await self._maybe_generate_reflection(npc_name)

        # Calculate generation time
        generation_time_ms = (time.time() - start_time) * 1000

        # Build result
        result = DialogueResult(
            npc_name=npc_name,
            response=response_text,
            response_type=response_type,
            trust_delta=trust_delta,
            observation_id=observation_id,
            reflection_id=reflection_id,
            generation_time_ms=generation_time_ms,
            retry_count=retry_count,
            npc_mood=self._infer_npc_mood(response_type, conv_context),
        )

        logger.debug(
            f"Dialogue with {npc_name}: "
            f"'{player_input[:30]}...' -> '{response_text[:50]}...' "
            f"({generation_time_ms:.0f}ms, {retry_count} retries)"
        )

        return result

    async def _build_context(
        self,
        npc_name: str,
        player_input: str,
        raw_context: Dict[str, Any],
    ) -> ConversationContext:
        """
        Build a rich conversation context.

        Retrieves relevant memories and combines with world state.
        """
        context = ConversationContext(
            time_of_day=raw_context.get("time_of_day", raw_context.get("time", "day")),
            weather=raw_context.get("weather", "clear"),
            location=raw_context.get("location", "village"),
            game_day=self.current_game_day,
        )

        # Get persona for trust info
        persona = self.persona_manager.get_persona(npc_name)
        if persona:
            context.trust_level = persona.trust_level
            context.trust_tier = persona.get_trust_tier()
            context.is_first_meeting = not persona.met_player
            context.conversation_count = persona.times_spoken

        # Retrieve relevant memories
        npc_memory = self.memory_manager.get_npc_memory(npc_name)
        relevant_memories = npc_memory.recall(
            query=player_input,
            k=5,
            min_importance=0.3,
        )
        context.relevant_memories = relevant_memories

        # Get recent events if any were provided
        context.recent_events = raw_context.get("recent_events", [])

        return context

    async def _generate_with_retries(
        self,
        npc_name: str,
        player_input: str,
        context: ConversationContext,
        response_type: ResponseType,
    ) -> tuple[str, int]:
        """
        Generate LLM response with retry logic for content blocking.

        If content is blocked, re-queries with a stricter prompt.
        Max 3 retries, then surfaces the error.

        Returns:
            Tuple of (response_text, retry_count)

        Raises:
            LLMUnavailableError: If LLM is unavailable
            ContentBlockedError: If content is blocked after max retries
        """
        retry_count = 0
        last_error = None
        strictness_level = 0  # Increases with each retry

        while retry_count < self.MAX_CONTENT_RETRIES:
            try:
                # Build the prompt
                prompt = self._build_prompt(
                    npc_name=npc_name,
                    player_input=player_input,
                    context=context,
                    response_type=response_type,
                    strictness_level=strictness_level,
                )

                # Get persona for prompt building
                persona = self.persona_manager.get_persona(npc_name)
                persona_desc = persona.to_prompt_context() if persona else f"A friendly villager named {npc_name}"

                # Call LLM - this raises LLMUnavailableError if down (no fallback!)
                raw_response = await self.llm.generate(
                    prompt=prompt,
                    persona=persona_desc,
                )

                # Process and validate through persona system
                # This raises ContentBlockedError if content is blocked
                validated_response = self.persona_manager.process_llm_response(
                    raw_response=raw_response,
                    persona_name=npc_name,
                    response_type=response_type,
                )

                return (validated_response, retry_count)

            except ContentBlockedError as e:
                retry_count += 1
                strictness_level += 1
                last_error = e
                logger.warning(
                    f"Content blocked for {npc_name} (attempt {retry_count}/{self.MAX_CONTENT_RETRIES}): {e}"
                )
                # Continue to next retry with stricter prompt

        # All retries exhausted - surface the error
        # NO FALLBACKS - let the game handle this gracefully
        raise ContentBlockedError(
            f"Content blocked after {self.MAX_CONTENT_RETRIES} retries for {npc_name}. "
            f"Last error: {last_error}"
        )

    def _build_prompt(
        self,
        npc_name: str,
        player_input: str,
        context: ConversationContext,
        response_type: ResponseType,
        strictness_level: int = 0,
    ) -> str:
        """
        Build the full prompt for LLM generation.

        Combines persona, memories, context, and any strictness adjustments.
        """
        # Start with the persona-generated prompt
        base_prompt = self.persona_manager.generate_llm_prompt(
            persona_name=npc_name,
            player_message=player_input,
            context=context.to_dict(),
            response_type=response_type,
            is_player_upset=context.player_seems_upset,
        )

        # Add memory context
        if context.relevant_memories:
            memory_context = self._format_memory_context(context.relevant_memories)
            # Insert memory context before the player message
            base_prompt = base_prompt.replace(
                f"PLAYER: {player_input}",
                f"RELEVANT MEMORIES:\n{memory_context}\n\nPLAYER: {player_input}"
            )

        # Add strictness modifiers if we're retrying
        if strictness_level > 0:
            strictness_additions = self._get_strictness_additions(strictness_level)
            # Insert after CRITICAL RULES section
            base_prompt = base_prompt.replace(
                "CRITICAL RULES:",
                f"CRITICAL RULES:\n{strictness_additions}"
            )

        # Add special handling for failure scenarios
        if context.player_mentioned_failure:
            failure_guidance = (
                "\nIMPORTANT: The player mentioned a failure. "
                "Be supportive and encouraging. NEVER be dismissive. "
                "Acknowledge their feelings first."
            )
            base_prompt = base_prompt.replace(
                "RESPONSE GUIDANCE:",
                f"RESPONSE GUIDANCE:{failure_guidance}"
            )

        return base_prompt

    def _format_memory_context(self, memories: List[Memory]) -> str:
        """Format memories for prompt injection."""
        if not memories:
            return ""

        lines = []
        for mem in memories:
            # Format based on memory type
            if mem.memory_type == MemoryType.OBSERVATION.value:
                lines.append(f"- You remember: {mem.content}")
            elif mem.memory_type == MemoryType.REFLECTION.value:
                lines.append(f"- You think: {mem.content}")
            elif mem.memory_type == MemoryType.PLAN.value:
                lines.append(f"- You intended: {mem.content}")

        return "\n".join(lines)

    def _get_strictness_additions(self, level: int) -> str:
        """Get additional prompt instructions for stricter content generation."""
        additions = []

        if level >= 1:
            additions.append(
                "EXTRA IMPORTANT: Keep your response extremely gentle and positive."
            )

        if level >= 2:
            additions.append(
                "MANDATORY: Only use words associated with comfort, warmth, and kindness."
            )

        if level >= 3:
            additions.append(
                "CRITICAL: Generate the softest, most supportive response possible. "
                "Imagine you are comforting a child who had a bad day."
            )

        return "\n".join(additions)

    def _infer_response_type(
        self,
        player_input: str,
        emotion_state: Dict[str, bool],
    ) -> ResponseType:
        """Infer the appropriate response type from player input."""
        text_lower = player_input.lower()

        # Check for specific triggers
        if emotion_state["is_upset"]:
            return ResponseType.COMFORT

        if emotion_state["mentions_failure"]:
            return ResponseType.FAILURE_SUPPORT

        if emotion_state["is_positive"]:
            return ResponseType.CELEBRATION

        # Check for greetings
        greetings = ["hello", "hi", "hey", "good morning", "good evening", "howdy"]
        if any(g in text_lower for g in greetings):
            return ResponseType.GREETING

        # Check for farewells
        farewells = ["bye", "goodbye", "see you", "later", "good night", "farewell"]
        if any(f in text_lower for f in farewells):
            return ResponseType.FAREWELL

        # Check for gift-related
        gift_words = ["gift", "present", "for you", "take this", "give you"]
        if any(g in text_lower for g in gift_words):
            return ResponseType.GIFT_GIVEN

        # Check for teaching/learning
        teach_words = ["teach", "learn", "how do", "show me", "explain", "help me"]
        if any(t in text_lower for t in teach_words):
            return ResponseType.TEACHING

        # Check for quest-related
        quest_words = ["quest", "mission", "task", "job", "help", "need"]
        if any(q in text_lower for q in quest_words):
            return ResponseType.QUEST

        return ResponseType.GENERAL

    def _calculate_trust_delta(
        self,
        response_type: ResponseType,
        is_positive_interaction: bool,
    ) -> int:
        """Calculate how much trust should change from this interaction."""
        base_delta = self.TRUST_DELTAS["normal_chat"]

        # Positive interactions boost trust more
        if is_positive_interaction:
            base_delta += 2

        # Response type modifiers
        type_modifiers = {
            ResponseType.GIFT_RECEIVED: 5,
            ResponseType.GIFT_GIVEN: 3,
            ResponseType.COMFORT: 3,
            ResponseType.FAILURE_SUPPORT: 4,
            ResponseType.CELEBRATION: 2,
        }

        return base_delta + type_modifiers.get(response_type, 0)

    async def _store_interaction(
        self,
        npc_name: str,
        player_input: str,
        npc_response: str,
        context: ConversationContext,
        response_type: ResponseType,
    ) -> str:
        """
        Store the interaction as an observation in NPC memory.

        Returns the memory ID.
        """
        npc_memory = self.memory_manager.get_npc_memory(npc_name)

        # Build the memory content
        memory_content = f"The player said: '{player_input}'. I responded with comfort and support."

        # Determine importance
        importance = 0.5  # Base importance

        # Emotional interactions are more memorable
        if context.player_seems_upset:
            importance = 0.8
            memory_content = f"The player seemed upset and said: '{player_input}'. I comforted them."

        if context.player_mentioned_failure:
            importance = 0.7
            memory_content = f"The player told me about a failure: '{player_input}'. I supported them."

        # First meetings are important
        if context.is_first_meeting:
            importance = 0.9
            memory_content = f"I met the player for the first time! They said: '{player_input}'."

        # Build tags
        tags = [MemoryTag.PLAYER.value]
        if context.player_seems_upset:
            tags.append(MemoryTag.EMOTIONAL.value)

        # Store the observation
        memory_id = npc_memory.remember(
            event=memory_content,
            importance=importance,
            memory_type=MemoryType.OBSERVATION,
            tags=tags,
            location=context.location,
            is_core=context.is_first_meeting,  # First meeting is a core memory
        )

        return memory_id

    async def _maybe_generate_reflection(self, npc_name: str) -> Optional[str]:
        """
        Maybe trigger a reflection generation.

        NPCs periodically reflect on their interactions, forming
        higher-level interpretations of what's happening.
        """
        # Track interactions
        self._interaction_counts[npc_name] = self._interaction_counts.get(npc_name, 0) + 1

        # Check if it's time for a reflection
        if self._interaction_counts[npc_name] % self.REFLECTION_INTERVAL != 0:
            return None

        # Get recent observations to reflect on
        npc_memory = self.memory_manager.get_npc_memory(npc_name)
        recent_observations = npc_memory.recall_by_type(
            MemoryType.OBSERVATION,
            k=5,
        )

        if len(recent_observations) < 3:
            return None  # Not enough observations to reflect on

        # Generate a reflection via LLM
        reflection = await self._generate_reflection(npc_name, recent_observations)

        if reflection:
            # Store the reflection
            reflection_id = self.memory_manager.generate_reflection(
                npc_id=npc_name,
                observation_ids=[obs.id for obs in recent_observations],
                reflection=reflection,
                importance=0.7,
            )
            logger.debug(f"Generated reflection for {npc_name}: {reflection[:50]}...")
            return reflection_id

        return None

    async def _generate_reflection(
        self,
        npc_name: str,
        observations: List[Memory],
    ) -> Optional[str]:
        """
        Generate a reflection from observations using the LLM.

        Reflections are the NPC's interpretation of what's happened.
        """
        # Build observation summary
        obs_summary = "\n".join([f"- {obs.content}" for obs in observations])

        persona = self.persona_manager.get_persona(npc_name)
        persona_desc = persona.to_prompt_context() if persona else f"A friendly villager named {npc_name}"

        prompt = f"""Based on these recent observations, what is your impression or feeling about the player?

RECENT OBSERVATIONS:
{obs_summary}

Generate a single sentence reflection that captures your growing understanding of the player.
Examples of good reflections:
- "The player seems to genuinely care about helping others."
- "I think the player is going through a difficult time."
- "The player has become someone I trust deeply."

Your reflection (one sentence):"""

        try:
            response = await self.llm.generate(
                prompt=prompt,
                persona=persona_desc,
            )
            # Clean up the response
            reflection = response.strip().strip('"').strip("'")
            return reflection
        except (LLMUnavailableError, Exception) as e:
            logger.warning(f"Could not generate reflection for {npc_name}: {e}")
            return None

    def _infer_npc_mood(
        self,
        response_type: ResponseType,
        context: ConversationContext,
    ) -> str:
        """Infer the NPC's mood for UI hints."""
        if response_type in [ResponseType.COMFORT, ResponseType.FAILURE_SUPPORT]:
            return "concerned"
        if response_type == ResponseType.CELEBRATION:
            return "happy"
        if context.player_seems_upset:
            return "concerned"
        if response_type == ResponseType.TEACHING:
            return "thoughtful"
        return "neutral"

    def update_game_day(self, new_day: int):
        """
        Update the current game day.

        This affects memory decay and should be called when the game day changes.
        """
        self.current_game_day = new_day
        self.memory_manager.advance_day(new_day)
        logger.info(f"Advanced to game day {new_day}")


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def quick_chat(
    manager: DialogueManager,
    npc_name: str,
    player_input: str,
    **context,
) -> str:
    """
    Quick helper for simple dialogue exchanges.

    Just returns the response string, discarding metadata.

    Args:
        manager: DialogueManager instance
        npc_name: Name of the NPC
        player_input: What the player said
        **context: Optional context kwargs (time_of_day, weather, location)

    Returns:
        The NPC's response string

    Raises:
        LLMUnavailableError: If LLM is unavailable
    """
    result = await manager.chat(
        npc_name=npc_name,
        player_input=player_input,
        context=context if context else None,
    )
    return result.response


async def comfort_player(
    manager: DialogueManager,
    npc_name: str,
    player_input: str,
) -> DialogueResult:
    """
    Specifically request a comforting response.

    Use this when you know the player is upset.
    """
    return await manager.chat(
        npc_name=npc_name,
        player_input=player_input,
        response_type=ResponseType.COMFORT,
    )


async def celebrate_with_player(
    manager: DialogueManager,
    npc_name: str,
    player_input: str,
) -> DialogueResult:
    """
    Specifically request a celebratory response.

    Use this when the player accomplished something.
    """
    return await manager.chat(
        npc_name=npc_name,
        player_input=player_input,
        response_type=ResponseType.CELEBRATION,
    )


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_dialogue_manager(
    llm_base_url: str = "http://localhost:1234/v1",
    memory_directory: str = "./data/memories",
    personas_directory: Optional[str] = None,
    game_day: int = 1,
) -> DialogueManager:
    """
    Factory function to create a fully configured DialogueManager.

    Args:
        llm_base_url: LM Studio API endpoint
        memory_directory: Where to store NPC memories
        personas_directory: Optional directory with custom persona files
        game_day: Starting game day

    Returns:
        Configured DialogueManager ready for use
    """
    from pathlib import Path

    # Initialize components
    llm = LLMConnection(base_url=llm_base_url)
    memory_manager = MemoryManager(
        persist_directory=memory_directory,
        current_game_day=game_day,
    )
    persona_manager = PersonaManager(
        personas_dir=Path(personas_directory) if personas_directory else None,
    )

    return DialogueManager(
        llm=llm,
        memory_manager=memory_manager,
        persona_manager=persona_manager,
        default_game_day=game_day,
    )


# =============================================================================
# DEMO / TESTING
# =============================================================================

async def demo():
    """
    Demo the dialogue system.

    Run with: python -m src.ai.dialogue
    """
    print("=" * 60)
    print("Lelock Dialogue System Demo")
    print("=" * 60)

    # Create the manager
    manager = create_dialogue_manager()

    # Run health check
    print("\n1. Checking LLM connection...")
    status = await manager.llm.health_check()
    print(f"   Status: {status.value}")

    if status.value == "error":
        print("   LLM not available. Please start LM Studio.")
        return

    # Test conversation with Mom
    print("\n2. Testing conversation with Mom...")
    try:
        result = await manager.chat(
            npc_name="mom",
            player_input="I failed the fishing quest...",
            context={"time_of_day": "evening", "weather": "rainy"},
        )
        print(f"   Response: {result.response}")
        print(f"   Trust delta: +{result.trust_delta}")
        print(f"   Generation time: {result.generation_time_ms:.0f}ms")
    except LLMUnavailableError as e:
        print(f"   Error: {e}")

    # Test conversation with Dad
    print("\n3. Testing conversation with Dad...")
    try:
        result = await manager.chat(
            npc_name="dad",
            player_input="Can you teach me how to fish?",
            context={"time_of_day": "morning", "weather": "clear"},
        )
        print(f"   Response: {result.response}")
        print(f"   Response type: {result.response_type.value}")
    except LLMUnavailableError as e:
        print(f"   Error: {e}")

    # Test celebration
    print("\n4. Testing celebration response...")
    try:
        result = await celebrate_with_player(
            manager,
            npc_name="mom",
            player_input="I finally caught the legendary fish!",
        )
        print(f"   Response: {result.response}")
        print(f"   NPC mood: {result.npc_mood}")
    except LLMUnavailableError as e:
        print(f"   Error: {e}")

    # Cleanup
    await manager.llm.close()
    print("\nDemo complete!")


if __name__ == "__main__":
    asyncio.run(demo())


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Main classes
    "DialogueManager",
    "DialogueResult",
    "ConversationContext",
    "EmotionDetector",

    # Convenience functions
    "quick_chat",
    "comfort_player",
    "celebrate_with_player",
    "create_dialogue_manager",
]
