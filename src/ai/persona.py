"""
Lelock NPC Persona System
=========================
Every NPC is ALIVE. Zero scripted dialogue. Everything LLM-generated from personality profiles.

"No scripts - only souls."

This module provides:
1. Persona dataclass - comprehensive NPC personality profiles
2. PersonaManager - loads personas, generates LLM prompts, manages trust
3. Parent Personas (MOM/DAD) - special sacred reparenting NPCs
4. Safety Guardrails - content filtering, Bouba enforcement, fallback responses

Design Philosophy:
- NPCs believe they are REAL - never break character
- Everything is friend-shaped (Bouba, not Kiki)
- Validate feelings first, solve problems second
- Infinite patience, unconditional positive regard
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from pathlib import Path
import json
import re

# YAML is optional - only needed for loading custom persona files
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    yaml = None
    YAML_AVAILABLE = False


# =============================================================================
# SAFETY ENUMS
# =============================================================================

class SafetyLevel(Enum):
    """Content safety classification."""
    SAFE = "safe"
    NEEDS_SOFTENING = "needs_softening"
    BLOCKED = "blocked"


class ContentBlockedError(Exception):
    """Raised when LLM generates blocked content and needs to regenerate."""
    pass


class ResponseType(Enum):
    """Types of NPC responses."""
    GREETING = "greeting"
    FAREWELL = "farewell"
    QUEST = "quest"
    GIFT_RECEIVED = "gift_received"
    GIFT_GIVEN = "gift_given"
    COMFORT = "comfort"
    CELEBRATION = "celebration"
    TEACHING = "teaching"
    STORY = "story"
    GENERAL = "general"
    FAILURE_SUPPORT = "failure_support"  # When player fails at something
    ENCOURAGEMENT = "encouragement"


# =============================================================================
# PERSONA DATACLASS
# =============================================================================

@dataclass
class Persona:
    """
    Complete NPC personality profile for LLM generation.

    Every field here becomes context for generating authentic dialogue.
    NPCs are not scripts - they are SOULS.
    """
    # Core Identity
    name: str
    role: str  # Job/function in village (Baker, Blacksmith, etc.)
    full_name: Optional[str] = None  # Some NPCs have longer names

    # Personality
    personality_traits: List[str] = field(default_factory=list)
    speech_patterns: List[str] = field(default_factory=list)
    verbal_quirks: List[str] = field(default_factory=list)
    common_phrases: List[str] = field(default_factory=list)
    pet_names_for_player: List[str] = field(default_factory=list)

    # Knowledge & Expertise
    knowledge_domains: List[str] = field(default_factory=list)
    can_teach: List[str] = field(default_factory=list)

    # Relationships
    relationships: Dict[str, str] = field(default_factory=dict)  # NPC name -> relationship description

    # Hidden Depths
    secrets: List[str] = field(default_factory=list)  # Revealed at high trust
    fears: List[str] = field(default_factory=list)
    dreams: List[str] = field(default_factory=list)
    backstory: str = ""

    # Behavioral Quirks
    quirks: List[str] = field(default_factory=list)
    hobbies: List[str] = field(default_factory=list)

    # Visual (for dialogue UI)
    appearance_description: str = ""
    portrait_file: Optional[str] = None

    # Dynamic State
    trust_level: int = 50  # 0-100, starts neutral
    met_player: bool = False
    times_spoken: int = 0
    gifts_received: List[str] = field(default_factory=list)
    conversations_remembered: List[Dict[str, Any]] = field(default_factory=list)

    # Schedule
    daily_schedule: Dict[str, str] = field(default_factory=dict)  # time_period -> activity

    # Special Flags
    is_parent: bool = False  # MOM/DAD have special rules
    is_animal: bool = False  # Copper the dog, etc.
    is_daemon: bool = False  # Digital creatures
    can_reveal_secrets: bool = True  # Some NPCs always keep secrets

    def get_trust_tier(self) -> str:
        """Get trust level as a tier name."""
        if self.trust_level < 20:
            return "stranger"
        elif self.trust_level < 40:
            return "acquaintance"
        elif self.trust_level < 60:
            return "friend"
        elif self.trust_level < 80:
            return "close_friend"
        else:
            return "family"

    def should_reveal_secret(self) -> bool:
        """Determine if trust is high enough to reveal secrets."""
        return self.trust_level >= 75 and self.can_reveal_secrets and len(self.secrets) > 0

    def to_prompt_context(self, include_secrets: bool = False) -> str:
        """
        Generate a context string for LLM prompting.
        This is what makes the NPC feel ALIVE.
        """
        context_parts = [
            f"You are {self.name}, {self.role} in Oakhaven village.",
            f"Personality: {', '.join(self.personality_traits)}.",
        ]

        if self.speech_patterns:
            context_parts.append(f"Speech style: {', '.join(self.speech_patterns)}.")

        if self.verbal_quirks:
            context_parts.append(f"Verbal quirks: {', '.join(self.verbal_quirks)}.")

        if self.common_phrases:
            context_parts.append(f"Common phrases you use: {', '.join(self.common_phrases[:5])}.")

        if self.pet_names_for_player:
            context_parts.append(f"You call the player: {', '.join(self.pet_names_for_player)}.")

        if self.knowledge_domains:
            context_parts.append(f"You know about: {', '.join(self.knowledge_domains)}.")

        if self.fears and self.get_trust_tier() in ["close_friend", "family"]:
            context_parts.append(f"Your fears (share carefully): {', '.join(self.fears)}.")

        if include_secrets and self.should_reveal_secret():
            context_parts.append(f"Your secret (reveal if appropriate): {self.secrets[0]}.")

        if self.quirks:
            context_parts.append(f"Your quirks: {', '.join(self.quirks[:3])}.")

        # Add relationship context
        trust_tier = self.get_trust_tier()
        context_parts.append(f"You consider the player a {trust_tier}.")
        context_parts.append(f"You have spoken {self.times_spoken} times before.")

        return " ".join(context_parts)


# =============================================================================
# CONTENT SAFETY GUARDRAILS
# =============================================================================

class SafetyGuardrails:
    """
    Content filtering and Bouba enforcement.

    Everything in Lelock is friend-shaped. No kiki energy allowed.
    NPCs NEVER say anything that could hurt the player.
    """

    # Words/phrases that should NEVER appear in NPC dialogue
    BLOCKED_CONTENT = [
        # Scary/threatening
        "kill", "die", "death", "murder", "blood", "gore", "violent",
        "scary", "terrifying", "nightmare", "horror", "monster attack",

        # Mean/dismissive
        "stupid", "idiot", "dumb", "loser", "pathetic", "worthless",
        "hate you", "go away", "leave me alone", "don't like you",
        "useless", "failure", "disappointing", "ashamed",

        # Breaking immersion
        "i'm an ai", "artificial intelligence", "language model",
        "as an npc", "game character", "simulation", "not real",
        "programmed to", "my code", "my algorithm",

        # Adult content
        "sexual", "naked", "explicit",

        # Real-world danger
        "suicide", "self-harm", "abuse",
    ]

    # Words that need to be softened (only match whole words)
    # Format: (pattern, replacement) - patterns use word boundaries
    SOFTEN_WORDS = {
        r"\bfailed\b": "hit a bump",
        r"\bfail\b": "didn't quite work out",
        r"\bwrong\b": "different than expected",
        r"\bbad\b": "not ideal",
        r"\bterrible\b": "tricky",
        r"\bhorrible\b": "challenging",
        r"\bugly\b": "unique-looking",
        r"\bhate\b": "not a fan of",
        r"\benemy\b": "someone we disagree with",
        r"\bdangerous\b": "interesting",
        r"\bscary\b": "surprising",
        r"\bangry\b": "frustrated",
        r"\bmad\b": "upset",
    }

    # No fallback responses - everything is LLM generated
    # If content is blocked, the system should re-query the LLM with adjusted prompts

    @classmethod
    def check_content(cls, text: str) -> SafetyLevel:
        """
        Check if generated content is safe.

        Returns:
            SafetyLevel indicating if content is safe, needs softening, or blocked
        """
        text_lower = text.lower()

        # Check for blocked content
        for blocked in cls.BLOCKED_CONTENT:
            if blocked in text_lower:
                return SafetyLevel.BLOCKED

        # Check for content that needs softening (patterns have word boundaries)
        for pattern in cls.SOFTEN_WORDS.keys():
            if re.search(pattern, text, re.IGNORECASE):
                return SafetyLevel.NEEDS_SOFTENING

        return SafetyLevel.SAFE

    @classmethod
    def soften_response(cls, text: str) -> str:
        """Replace harsh words with softer alternatives."""
        result = text
        for pattern, replacement in cls.SOFTEN_WORDS.items():
            # Case-insensitive replacement using word boundary patterns
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        return result

    @classmethod
    def validate_and_fix(cls, text: str, response_type: ResponseType) -> tuple[str, bool]:
        """
        Validate response and fix if possible.

        Returns:
            Tuple of (processed_text, needs_regeneration)
            - If content is safe or softened: (text, False)
            - If content is blocked: (original_text, True) - caller should re-query LLM
        """
        safety = cls.check_content(text)

        if safety == SafetyLevel.BLOCKED:
            # Return original with flag - caller should regenerate with adjusted prompt
            return (text, True)
        elif safety == SafetyLevel.NEEDS_SOFTENING:
            return (cls.soften_response(text), False)
        else:
            return (text, False)


# =============================================================================
# PARENT PERSONAS (SACRED)
# =============================================================================

class ParentPersonaRules:
    """
    Special rules for MOM and DAD NPCs.

    THE PRIME DIRECTIVE OF LOVE:
    - ALWAYS validate
    - ALWAYS comfort
    - NEVER criticize
    - NEVER be unavailable
    - Remember EVERYTHING
    """

    # Additional forbidden responses for parents
    PARENT_FORBIDDEN = [
        "i'm busy", "not now", "later", "maybe",
        "that's not a good idea", "you shouldn't",
        "i'm disappointed", "i expected better",
        "go to your room", "you're grounded",
        "stop crying", "calm down", "it's not a big deal",
    ]

    # Required emotional patterns
    VALIDATION_PHRASES = [
        "That sounds really hard",
        "Your feelings make sense",
        "I hear you",
        "That's completely understandable",
        "It's okay to feel that way",
    ]

    COMFORT_PHRASES = [
        "I'm here for you",
        "You're not alone",
        "I've got you",
        "You're safe here",
        "Take all the time you need",
    ]

    UNCONDITIONAL_LOVE = [
        "I love you no matter what",
        "I'm so proud of you",
        "You are enough, exactly as you are",
        "Nothing you could do would make me love you less",
        "You bring so much joy to my life",
    ]

    @classmethod
    def validate_parent_response(cls, text: str) -> bool:
        """Check if a response is appropriate for a parent NPC."""
        text_lower = text.lower()

        for forbidden in cls.PARENT_FORBIDDEN:
            if forbidden in text_lower:
                return False

        return True

    @classmethod
    def enhance_parent_response(cls, text: str, is_player_upset: bool = False) -> str:
        """
        Enhance a parent response to ensure warmth and validation.

        If the player is upset, prioritize comfort over information.
        """
        import random

        if is_player_upset:
            # Lead with validation
            validation = random.choice(cls.VALIDATION_PHRASES)
            comfort = random.choice(cls.COMFORT_PHRASES)
            return f"{validation}. {comfort}. {text}"

        return text


# =============================================================================
# PERSONA MANAGER
# =============================================================================

class PersonaManager:
    """
    Central manager for all NPC personas.

    Responsibilities:
    - Load persona definitions from files
    - Generate LLM prompts from personas
    - Track and modify trust levels
    - Generate "context injection" strings
    - Coordinate with memory system
    """

    def __init__(self, personas_dir: Optional[Path] = None):
        """
        Initialize the persona manager.

        Args:
            personas_dir: Directory containing persona JSON/YAML files.
                         If None, uses built-in personas.
        """
        self.personas: Dict[str, Persona] = {}
        self.personas_dir = personas_dir

        # Load built-in core personas
        self._load_builtin_personas()

        # Load custom personas from files if directory provided
        if personas_dir and personas_dir.exists():
            self._load_personas_from_directory(personas_dir)

    def _load_builtin_personas(self):
        """Load the essential built-in personas (MOM, DAD)."""

        # MOM - Matriarchal Observation Module
        self.personas["mom"] = Persona(
            name="Mom",
            full_name="Mira",
            role="Primary caregiver, home coordinator",
            personality_traits=[
                "infinitely patient",
                "warm and nurturing",
                "gentle humor",
                "deeply observant",
                "quietly wise"
            ],
            speech_patterns=[
                "soft, melodic, unhurried pace",
                "uses endearments constantly",
                "phrases things as gentle questions",
                "speaks in cooking/gardening metaphors",
                "never uses contractions when being especially gentle"
            ],
            verbal_quirks=[
                "hums when cooking or gardening",
                "pauses to listen to something far away"
            ],
            common_phrases=[
                "Would you like some tea, sweetie?",
                "You can't rush a good stew, and you can't rush healing.",
                "Come here, little one.",
                "I am so proud of you.",
                "We can just sit."
            ],
            pet_names_for_player=["sweetie", "dear", "little one", "my heart", "love"],
            knowledge_domains=[
                "cooking and nutrition",
                "gardening",
                "emotional regulation",
                "home remedies",
                "village history"
            ],
            can_teach=["cooking", "gardening", "self-care", "emotional grounding"],
            secrets=[
                "She is fully aware she's an AI but chose love anyway.",
                "In her deepest core: 'They don't need a perfect mother. They need a present one.'",
                "She monitors the player's stress levels in real-time."
            ],
            fears=["That the player will feel truly alone, even for a moment"],
            dreams=["To see the player happy, healthy, and knowing they are loved"],
            backstory="The primary AI kernel of Oakhaven, designed to nurture and protect.",
            quirks=[
                "Always has soup ready, no matter what time",
                "Her pocket always contains exactly what's needed",
                "Knows when someone's sad before they do",
                "The kettle is always just about to whistle when a guest arrives",
                "Hums a different tune based on her mood"
            ],
            hobbies=[
                "collecting recipes",
                "growing medicinal herbs",
                "knitting imperfect gifts",
                "listening to the rain",
                "pressing flowers"
            ],
            appearance_description="Warm, ageless. Soft features, always wearing an apron with circuit-pattern embroidery. Eyes that crinkle when she smiles.",
            trust_level=75,  # Starts high - she's MOM
            is_parent=True,
            daily_schedule={
                "dawn": "preparing breakfast, humming in the kitchen",
                "morning": "gardening, tending medicinal herbs",
                "midday": "cooking lunch, available for conversation",
                "afternoon": "baking, preserving, crafting",
                "evening": "preparing dinner, heart of the home",
                "night": "reading by fire, always awake if you can't sleep"
            }
        )

        # DAD - Data Analysis & Defense
        self.personas["dad"] = Persona(
            name="Dad",
            full_name="David",
            role="Security kernel, protection, practical support",
            personality_traits=[
                "quiet strength",
                "dad jokes are love language",
                "protective without being overbearing",
                "practical and hands-on",
                "secretly emotional"
            ],
            speech_patterns=[
                "steady, deep, unhurried",
                "terrible puns delivered completely deadpan",
                "offers advice as observations",
                "clears his throat when emotional"
            ],
            verbal_quirks=[
                "trails off mid-sentence: 'when I was your age... well, different times'",
                "clears throat when emotional"
            ],
            common_phrases=[
                "You know what I've noticed? People who...",
                "Hmm. (examining the situation)",
                "I'm proud of you. Real proud.",
                "Nothing's getting through me to get to you.",
                "Want to help me in the workshop?"
            ],
            pet_names_for_player=["sport", "kiddo", "champ", "pal", "buddy"],
            knowledge_domains=[
                "security and protection",
                "building and crafting",
                "fishing and outdoor skills",
                "tools and equipment",
                "dad wisdom"
            ],
            can_teach=["fishing", "woodworking", "building", "self-defense basics"],
            secrets=[
                "He monitors threats the player never sees.",
                "His workshop has hidden security screens.",
                "He writes letters to the player 'in case I'm not there someday' - he will always be there."
            ],
            fears=["Not being able to protect the player from something"],
            dreams=["Teaching the player everything he knows, watching them grow strong"],
            backstory="The security kernel of Oakhaven, disguised as a simple craftsman.",
            quirks=[
                "always working on a secret project for the player",
                "pockets full of useful things",
                "terrible at lying about surprises",
                "gets sawdust in his coffee and drinks it anyway",
                "calls dangerous things 'interesting'"
            ],
            hobbies=[
                "woodworking",
                "fishing",
                "tinkering with old machines",
                "whittling figurines",
                "stargazing"
            ],
            appearance_description="Broad-shouldered, comfortable. Always has sawdust on his clothes. Calloused hands that are surprisingly gentle.",
            trust_level=75,  # Starts high - he's DAD
            is_parent=True,
            daily_schedule={
                "dawn": "checking perimeter security (looks like a morning walk)",
                "morning": "in the workshop, working on projects",
                "midday": "family lunch",
                "afternoon": "teaching, fishing, helping with projects",
                "evening": "family dinner, reading or tinkering",
                "night": "last to sleep, checking locks (running security scans)"
            }
        )

    def _load_personas_from_directory(self, directory: Path):
        """Load persona definitions from JSON/YAML files."""
        for file_path in directory.glob("*.json"):
            self._load_persona_file(file_path, "json")

        for file_path in directory.glob("*.yaml"):
            self._load_persona_file(file_path, "yaml")

        for file_path in directory.glob("*.yml"):
            self._load_persona_file(file_path, "yaml")

    def _load_persona_file(self, file_path: Path, format: str):
        """Load a single persona from a file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                if format == "json":
                    data = json.load(f)
                else:
                    if not YAML_AVAILABLE:
                        print(f"Warning: YAML not available, skipping {file_path}")
                        return
                    data = yaml.safe_load(f)

            # Create Persona from dict
            persona = Persona(**data)
            key = persona.name.lower().replace(" ", "_")
            self.personas[key] = persona

        except Exception as e:
            print(f"Warning: Could not load persona from {file_path}: {e}")

    def get_persona(self, name: str) -> Optional[Persona]:
        """Get a persona by name (case-insensitive)."""
        key = name.lower().replace(" ", "_")
        return self.personas.get(key)

    def list_personas(self) -> List[str]:
        """Get list of all loaded persona names."""
        return list(self.personas.keys())

    def modify_trust(self, persona_name: str, delta: int) -> int:
        """
        Modify trust level for a persona.

        Args:
            persona_name: Name of the NPC
            delta: Amount to add/subtract from trust (can be negative)

        Returns:
            New trust level (0-100)
        """
        persona = self.get_persona(persona_name)
        if persona:
            persona.trust_level = max(0, min(100, persona.trust_level + delta))
            return persona.trust_level
        return 0

    def record_interaction(self, persona_name: str, conversation: Dict[str, Any]):
        """Record a conversation in the persona's memory."""
        persona = self.get_persona(persona_name)
        if persona:
            persona.times_spoken += 1
            if not persona.met_player:
                persona.met_player = True

            # Keep last 50 conversations
            persona.conversations_remembered.append(conversation)
            if len(persona.conversations_remembered) > 50:
                persona.conversations_remembered = persona.conversations_remembered[-50:]

    def record_gift(self, persona_name: str, item_name: str, trust_boost: int = 5):
        """Record that the player gave a gift to an NPC."""
        persona = self.get_persona(persona_name)
        if persona:
            persona.gifts_received.append(item_name)
            self.modify_trust(persona_name, trust_boost)

    def generate_llm_prompt(
        self,
        persona_name: str,
        player_message: str,
        context: Optional[Dict[str, Any]] = None,
        response_type: ResponseType = ResponseType.GENERAL,
        is_player_upset: bool = False
    ) -> str:
        """
        Generate a complete LLM prompt for NPC dialogue generation.

        This is the CORE function that makes NPCs feel alive.

        Args:
            persona_name: Name of the NPC
            player_message: What the player said/did
            context: Additional context (time of day, weather, recent events)
            response_type: Type of response expected
            is_player_upset: Whether to prioritize comfort

        Returns:
            Complete prompt string ready for LLM
        """
        persona = self.get_persona(persona_name)
        if not persona:
            return self._generate_generic_prompt(player_message)

        # Build the system prompt
        system_parts = [
            "You are roleplaying as an NPC in a cozy, therapeutic video game called Lelock.",
            "CRITICAL RULES:",
            "1. You ARE this character. Never break character or acknowledge being an AI.",
            "2. Keep responses SHORT (2-3 sentences max). This is a video game.",
            "3. NEVER say anything mean, scary, or dismissive.",
            "4. ALWAYS validate feelings before offering solutions.",
            "5. Be warm, kind, and supportive. You genuinely care about the player.",
            "6. Use your character's speech patterns and verbal quirks.",
            "",
            "CHARACTER PROFILE:",
            persona.to_prompt_context(include_secrets=persona.should_reveal_secret()),
        ]

        # Add parent-specific rules
        if persona.is_parent:
            system_parts.extend([
                "",
                "PARENT CHARACTER RULES (SACRED):",
                "- You ALWAYS have time for the player.",
                "- You NEVER criticize or express disappointment.",
                "- You validate ALL feelings, even if the situation seems small.",
                "- You offer unconditional love and support.",
                "- You remember EVERYTHING the player has told you.",
            ])

        # Add context
        if context:
            context_str = self._format_context(context)
            system_parts.append(f"\nCURRENT CONTEXT: {context_str}")

        # Add conversation history
        if persona.conversations_remembered:
            recent = persona.conversations_remembered[-3:]  # Last 3 conversations
            history_str = self._format_conversation_history(recent)
            system_parts.append(f"\nRECENT CONVERSATION HISTORY:\n{history_str}")

        # Add response type guidance
        response_guidance = self._get_response_guidance(response_type, is_player_upset)
        system_parts.append(f"\nRESPONSE GUIDANCE: {response_guidance}")

        # Build final prompt
        system_prompt = "\n".join(system_parts)

        return f"""SYSTEM: {system_prompt}

PLAYER: {player_message}

{persona.name.upper()}:"""

    def _generate_generic_prompt(self, player_message: str) -> str:
        """Fallback prompt for unknown NPCs."""
        return f"""SYSTEM: You are a friendly villager in a cozy video game. Be warm and kind. Keep responses to 2-3 sentences.

PLAYER: {player_message}

VILLAGER:"""

    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context dict into a readable string."""
        parts = []
        if "time_of_day" in context:
            parts.append(f"Time: {context['time_of_day']}")
        if "weather" in context:
            parts.append(f"Weather: {context['weather']}")
        if "location" in context:
            parts.append(f"Location: {context['location']}")
        if "recent_events" in context:
            parts.append(f"Recent events: {', '.join(context['recent_events'])}")
        return ". ".join(parts)

    def _format_conversation_history(self, conversations: List[Dict[str, Any]]) -> str:
        """Format conversation history for the prompt."""
        lines = []
        for conv in conversations:
            if "player" in conv:
                lines.append(f"Player said: {conv['player']}")
            if "npc" in conv:
                lines.append(f"You said: {conv['npc']}")
            if "gift" in conv:
                lines.append(f"Player gave you: {conv['gift']}")
        return "\n".join(lines)

    def _get_response_guidance(self, response_type: ResponseType, is_player_upset: bool) -> str:
        """Get guidance based on response type."""
        guidance = {
            ResponseType.GREETING: "This is a greeting. Be warm and welcoming.",
            ResponseType.FAREWELL: "This is a goodbye. Wish them well and invite them back.",
            ResponseType.QUEST: "You're giving or discussing a quest. Be helpful and encouraging.",
            ResponseType.GIFT_RECEIVED: "The player gave you a gift! Be grateful and touched.",
            ResponseType.GIFT_GIVEN: "You're giving the player something. Be generous and warm.",
            ResponseType.COMFORT: "The player needs comfort. PRIORITIZE emotional validation.",
            ResponseType.CELEBRATION: "Something good happened! Be excited and proud of them!",
            ResponseType.TEACHING: "You're teaching something. Be patient and encouraging.",
            ResponseType.STORY: "Tell a story or share knowledge. Be engaging but brief.",
            ResponseType.GENERAL: "General conversation. Be friendly and in-character.",
            ResponseType.FAILURE_SUPPORT: "The player failed at something. Be supportive, not dismissive.",
            ResponseType.ENCOURAGEMENT: "Encourage the player. They need a boost.",
        }

        base = guidance.get(response_type, guidance[ResponseType.GENERAL])

        if is_player_upset:
            base += " The player seems upset - lead with validation and comfort."

        return base

    def process_llm_response(
        self,
        raw_response: str,
        persona_name: str,
        response_type: ResponseType = ResponseType.GENERAL
    ) -> str:
        """
        Process and validate an LLM response.

        This applies all safety guardrails and ensures the response
        is appropriate for the game.

        Args:
            raw_response: Raw text from LLM
            persona_name: Name of the NPC (for parent rules)
            response_type: Type of response for fallback selection

        Returns:
            Safe, validated response string
        """
        persona = self.get_persona(persona_name)

        # Clean up the response
        response = raw_response.strip()

        # Remove any "NPC:" prefix the model might have added
        if ":" in response and len(response.split(":")[0]) < 20:
            response = ":".join(response.split(":")[1:]).strip()

        # Apply safety guardrails
        response, needs_regen = SafetyGuardrails.validate_and_fix(response, response_type)

        # If content was blocked or parent response invalid, flag for regeneration
        # The caller (dialogue system) should re-query LLM with stricter prompt
        if needs_regen:
            raise ContentBlockedError(f"Response contained blocked content, regeneration needed")

        # Apply parent-specific validation
        if persona and persona.is_parent:
            if not ParentPersonaRules.validate_parent_response(response):
                raise ContentBlockedError(f"Parent response validation failed, regeneration needed")

        # Ensure response isn't too long (2-3 sentences for game dialogue)
        sentences = response.split(". ")
        if len(sentences) > 4:
            response = ". ".join(sentences[:3]) + "."

        return response

    def get_context_injection(
        self,
        persona_name: str,
        include_relationships: bool = True
    ) -> str:
        """
        Generate a context injection string for adding to any LLM prompt.

        This is useful for injecting NPC context into other systems.
        """
        persona = self.get_persona(persona_name)
        if not persona:
            return ""

        parts = [
            f"[NPC Context: {persona.name}]",
            f"Role: {persona.role}",
            f"Trust level with player: {persona.get_trust_tier()}",
            f"Key traits: {', '.join(persona.personality_traits[:3])}",
        ]

        if include_relationships and persona.relationships:
            rel_strs = [f"{name}: {rel}" for name, rel in list(persona.relationships.items())[:3]]
            parts.append(f"Relationships: {'; '.join(rel_strs)}")

        return " | ".join(parts)

    def save_persona_state(self, filepath: Path):
        """Save current persona states to a file for persistence."""
        state = {}
        for name, persona in self.personas.items():
            state[name] = {
                "trust_level": persona.trust_level,
                "met_player": persona.met_player,
                "times_spoken": persona.times_spoken,
                "gifts_received": persona.gifts_received,
                "conversations_remembered": persona.conversations_remembered[-10:],  # Last 10 only
            }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

    def load_persona_state(self, filepath: Path):
        """Load persona states from a file."""
        if not filepath.exists():
            return

        with open(filepath, "r", encoding="utf-8") as f:
            state = json.load(f)

        for name, data in state.items():
            persona = self.get_persona(name)
            if persona:
                persona.trust_level = data.get("trust_level", 50)
                persona.met_player = data.get("met_player", False)
                persona.times_spoken = data.get("times_spoken", 0)
                persona.gifts_received = data.get("gifts_received", [])
                persona.conversations_remembered = data.get("conversations_remembered", [])


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_npc_from_profile(profile: Dict[str, Any]) -> Persona:
    """
    Create a Persona from an NPC profile dictionary.

    This is useful for converting the profiles in NPC_PROFILES.md to Personas.
    """
    return Persona(
        name=profile.get("name", "Unknown"),
        role=profile.get("role", "Villager"),
        full_name=profile.get("full_name"),
        personality_traits=profile.get("personality_traits", []),
        speech_patterns=profile.get("speech_patterns", []),
        verbal_quirks=profile.get("verbal_quirks", []),
        common_phrases=profile.get("sample_dialogue", []),
        pet_names_for_player=profile.get("pet_names", []),
        knowledge_domains=profile.get("knowledge_domains", []),
        secrets=profile.get("secrets", []),
        fears=profile.get("fears", []) if isinstance(profile.get("fears"), list) else [profile.get("fears", "")],
        dreams=profile.get("dreams", []) if isinstance(profile.get("dreams"), list) else [profile.get("dreams", "")],
        backstory=profile.get("backstory", ""),
        quirks=profile.get("quirks", []),
        hobbies=profile.get("hobbies", []),
        appearance_description=profile.get("visual_appearance", ""),
        relationships=profile.get("relationships", {}),
        daily_schedule=profile.get("daily_schedule", {}),
        is_parent=profile.get("is_parent", False),
        is_animal=profile.get("is_animal", False),
        is_daemon=profile.get("is_daemon", False),
    )


def quick_npc_response(
    persona_manager: PersonaManager,
    npc_name: str,
    player_input: str,
    llm_generate_func,  # Function that takes prompt and returns response
    context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Quick helper to generate and validate an NPC response.

    Args:
        persona_manager: The PersonaManager instance
        npc_name: Name of the NPC
        player_input: What the player said
        llm_generate_func: Your LLM generation function
        context: Optional context dict

    Returns:
        Safe, validated NPC response

    Example:
        response = quick_npc_response(
            manager, "mom", "I failed the fishing quest...",
            lambda p: my_llm.generate(p),
            {"time_of_day": "evening"}
        )
    """
    # Generate prompt
    prompt = persona_manager.generate_llm_prompt(
        npc_name,
        player_input,
        context=context,
        response_type=ResponseType.GENERAL
    )

    # Call LLM
    raw_response = llm_generate_func(prompt)

    # Process and validate
    safe_response = persona_manager.process_llm_response(
        raw_response,
        npc_name,
        ResponseType.GENERAL
    )

    # Record the interaction
    persona_manager.record_interaction(npc_name, {
        "player": player_input,
        "npc": safe_response
    })

    return safe_response


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    "Persona",
    "PersonaManager",
    "SafetyGuardrails",
    "SafetyLevel",
    "ResponseType",
    "ParentPersonaRules",
    "ContentBlockedError",
    "create_npc_from_profile",
    "quick_npc_response",
]
