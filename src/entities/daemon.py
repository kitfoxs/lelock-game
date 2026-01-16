"""
Lelock Daemon Entity System
===========================
Digital creatures that inhabit both realms - friends, not enemies.

DAEMON PHILOSOPHY:
- Daemons are NOT monsters to fight. They are digital wildlife.
- Many are friendly helpers that can be befriended.
- Corrupted daemons are SICK, not evil. They need healing, not killing.
- Every daemon can eventually be befriended with patience.
- They can be adopted as companions that follow the player.

"In the age before memory, The Architect breathed life into the Source.
Not monsters, but friends waiting to be found. Not enemies, but
neighbors we haven't met."
    - From "The Origin of Daemons" by Lulo the Floran

Created by Kit & Ada Marie
"""

import pygame
import math
import random
from typing import Optional, List, Dict, Callable, Tuple, Any
from enum import Enum, auto
from dataclasses import dataclass, field

from settings import LAYERS, TILE_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT
from entities.sprites import AnimatedSprite


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class DaemonState(Enum):
    """Current behavior state of a daemon."""
    IDLE = "idle"               # Standing still, looking around
    ROAMING = "roaming"         # Wandering the world
    INTERACTING = "interacting" # Engaged with player
    FOLLOWING = "following"     # Adopted companion mode
    SLEEPING = "sleeping"       # Resting (night or den)
    EATING = "eating"           # Consuming food
    PLAYING = "playing"         # Happy, playful behavior
    CORRUPTED = "corrupted"     # Sick, needs healing
    HEALING = "healing"         # Being healed, mid-recovery
    FLEEING = "fleeing"         # Running away (shy daemons)


class DaemonCategory(Enum):
    """Classification of daemon types."""
    COMMON = "common"           # Friendly wildlife found everywhere
    UNCOMMON = "uncommon"       # Shy/rare, requires patience
    CORRUPTED = "corrupted"     # Sick creatures needing healing
    LEGENDARY = "legendary"     # Ancient beings that can adopt player


class DaemonTemperament(Enum):
    """How a daemon initially reacts to players."""
    FRIENDLY = "friendly"       # Approaches player willingly
    CURIOUS = "curious"         # Observes before approaching
    SHY = "shy"                 # Flees initially, warms up over time
    CAUTIOUS = "cautious"       # Watches from distance
    PROTECTIVE = "protective"   # Guards territory but not aggressive


class DaemonSize(Enum):
    """Physical size category."""
    TINY = "tiny"               # Palm-sized (Bit-Bird, Hop-Frog)
    SMALL = "small"             # Cat-sized (Glitch-Kit, Pixel-Bunny)
    MEDIUM = "medium"           # Dog-sized (Render-Fox, Debug-Moth)
    LARGE = "large"             # Bear-sized (Byte-Bear, Compile-Deer)
    HUGE = "huge"               # Building-sized (Legendaries)


# =============================================================================
# DAEMON SPECIES DATA
# =============================================================================

@dataclass
class DaemonAppearance:
    """Visual description for both realms."""
    # Physical realm (fantasy) appearance
    physical_name: str
    physical_description: str
    physical_color_primary: Tuple[int, int, int]
    physical_color_secondary: Tuple[int, int, int]

    # Digital realm (tech) appearance
    digital_name: str
    digital_description: str
    digital_color_primary: Tuple[int, int, int]
    digital_color_secondary: Tuple[int, int, int]

    # Sprite animation keys
    sprite_base: str = "daemon_default"


@dataclass
class DaemonAbility:
    """Special ability a daemon can grant or use."""
    name: str
    description: str
    passive: bool = True  # True = always active when companion
    cooldown: float = 0.0  # Seconds between uses (active abilities)

    def __str__(self) -> str:
        return f"{self.name}: {self.description}"


@dataclass
class DaemonSpecies:
    """
    Complete definition of a daemon species.

    This is the template from which individual daemons are created.
    Contains all stats, behaviors, and special traits.
    """
    # Identity
    species_id: str
    category: DaemonCategory

    # Dual-realm appearance
    appearance: DaemonAppearance

    # Stats
    size: DaemonSize
    base_health: int = 100
    base_speed: float = 50.0  # Pixels per second

    # Behavior
    temperament: DaemonTemperament = DaemonTemperament.CURIOUS
    activity_pattern: str = "diurnal"  # "diurnal", "nocturnal", "crepuscular"
    preferred_biome: str = "any"

    # Social
    is_social: bool = True  # Lives in groups?
    group_name: str = "pack"  # What's a group called?
    max_group_size: int = 1

    # Friendship & Taming
    base_friendship_rate: float = 1.0  # Multiplier for befriending speed
    favorite_foods: List[str] = field(default_factory=list)
    favorite_items: List[str] = field(default_factory=list)

    # Corruption (for corrupted species)
    true_form_id: Optional[str] = None  # What they become when healed
    corruption_cause: str = ""
    healing_method: str = ""

    # Abilities (when befriended/companion)
    abilities: List[DaemonAbility] = field(default_factory=list)

    # Dialogue hints (for LLM)
    personality_traits: List[str] = field(default_factory=list)
    speech_patterns: List[str] = field(default_factory=list)

    def get_name(self, is_digital: bool) -> str:
        """Get appropriate name for current realm."""
        if is_digital:
            return self.appearance.digital_name
        return self.appearance.physical_name

    def get_description(self, is_digital: bool) -> str:
        """Get appropriate description for current realm."""
        if is_digital:
            return self.appearance.digital_description
        return self.appearance.physical_description


# =============================================================================
# SPECIES REGISTRY - All daemon types in the game
# =============================================================================

# Common Daemons (friendly wildlife)
DAEMON_SPECIES: Dict[str, DaemonSpecies] = {}


def _register_common_daemons():
    """Register all common daemon species."""

    # -------------------------------------------------------------------------
    # GLITCH-KIT (Spirit Cat)
    # -------------------------------------------------------------------------
    DAEMON_SPECIES["glitch_kit"] = DaemonSpecies(
        species_id="glitch_kit",
        category=DaemonCategory.COMMON,
        appearance=DaemonAppearance(
            physical_name="Spirit Cat",
            physical_description="A ghostly feline with fur that shimmers like starlight",
            physical_color_primary=(180, 180, 220),
            physical_color_secondary=(100, 150, 200),
            digital_name="Glitch-Kit",
            digital_description="Low-poly cat with geometric fur patterns that flicker and shift",
            digital_color_primary=(0, 255, 255),
            digital_color_secondary=(255, 0, 255),
            sprite_base="glitch_kit",
        ),
        size=DaemonSize.SMALL,
        base_health=80,
        base_speed=80.0,
        temperament=DaemonTemperament.CURIOUS,
        activity_pattern="crepuscular",
        preferred_biome="any",
        is_social=True,
        group_name="colony",
        max_group_size=12,
        base_friendship_rate=1.2,
        favorite_foods=["static_snack", "memory_melon_seed"],
        favorite_items=["cursor_toy", "yarn_ball"],
        abilities=[
            DaemonAbility("Packet Delivery", "Can carry small items to friends"),
            DaemonAbility("Warm Render", "Curling up grants bonus rest recovery"),
            DaemonAbility("Glitch Sense", "Detects hidden items and secret paths"),
        ],
        personality_traits=["curious", "playful", "mischievous", "affectionate"],
        speech_patterns=["purrs in chiptune frequencies", "meows like dial-up sounds"],
    )

    # -------------------------------------------------------------------------
    # BIT-BIRD (Song Bird)
    # -------------------------------------------------------------------------
    DAEMON_SPECIES["bit_bird"] = DaemonSpecies(
        species_id="bit_bird",
        category=DaemonCategory.COMMON,
        appearance=DaemonAppearance(
            physical_name="Song Bird",
            physical_description="Jewel-toned bird that leaves musical notes in the air",
            physical_color_primary=(100, 200, 255),
            physical_color_secondary=(255, 200, 100),
            digital_name="Bit-Bird",
            digital_description="Low-poly bird with prismatic data-carrying feathers",
            digital_color_primary=(255, 215, 0),
            digital_color_secondary=(0, 191, 255),
            sprite_base="bit_bird",
        ),
        size=DaemonSize.TINY,
        base_health=40,
        base_speed=100.0,
        temperament=DaemonTemperament.FRIENDLY,
        activity_pattern="diurnal",
        preferred_biome="forest",
        is_social=True,
        group_name="packet",
        max_group_size=20,
        base_friendship_rate=1.5,
        favorite_foods=["code_seeds", "dew_drops"],
        favorite_items=["music_box", "whistle"],
        abilities=[
            DaemonAbility("Messenger Bird", "Send short audio messages to befriended NPCs"),
            DaemonAbility("Harmony Helper", "Boosts music effects when singing along"),
            DaemonAbility("Wake-Up Call", "Never miss dawn events"),
        ],
        personality_traits=["social", "musical", "brave", "helpful"],
        speech_patterns=["chirps in chiptune melodies", "unique song-signature"],
    )

    # -------------------------------------------------------------------------
    # BYTE-BEAR (Grove Bear)
    # -------------------------------------------------------------------------
    DAEMON_SPECIES["byte_bear"] = DaemonSpecies(
        species_id="byte_bear",
        category=DaemonCategory.COMMON,
        appearance=DaemonAppearance(
            physical_name="Grove Bear",
            physical_description="Massive gentle bear with moss-covered fur",
            physical_color_primary=(139, 90, 43),
            physical_color_secondary=(60, 120, 60),
            digital_name="Byte-Bear",
            digital_description="Voxel-based bear with floating particles and amber eyes",
            digital_color_primary=(100, 100, 200),
            digital_color_secondary=(200, 150, 255),
            sprite_base="byte_bear",
        ),
        size=DaemonSize.LARGE,
        base_health=200,
        base_speed=30.0,
        temperament=DaemonTemperament.PROTECTIVE,
        activity_pattern="diurnal",
        preferred_biome="caves",
        is_social=False,
        group_name="sleuth",
        max_group_size=4,
        base_friendship_rate=0.7,
        favorite_foods=["memory_melon", "pixel_pizza"],
        favorite_items=["ore_sample"],
        abilities=[
            DaemonAbility("Heavy Lifting", "Can carry heavy objects and clear obstacles"),
            DaemonAbility("Mining Guide", "Knows where the best ores are hidden"),
            DaemonAbility("Safe Hibernation", "Sleep near for guaranteed good dreams"),
        ],
        personality_traits=["gentle", "patient", "protective", "slow"],
        speech_patterns=["hums like a running fan", "rarely speaks"],
    )

    # -------------------------------------------------------------------------
    # PIXEL-BUNNY (Field Rabbit)
    # -------------------------------------------------------------------------
    DAEMON_SPECIES["pixel_bunny"] = DaemonSpecies(
        species_id="pixel_bunny",
        category=DaemonCategory.COMMON,
        appearance=DaemonAppearance(
            physical_name="Field Rabbit",
            physical_description="Soft pastel rabbit with endlessly twitching ears",
            physical_color_primary=(255, 182, 193),
            physical_color_secondary=(230, 230, 250),
            digital_name="Pixel-Bunny",
            digital_description="Cheerful rabbit that fragments into pixels when startled",
            digital_color_primary=(152, 251, 152),
            digital_color_secondary=(255, 192, 203),
            sprite_base="pixel_bunny",
        ),
        size=DaemonSize.SMALL,
        base_health=50,
        base_speed=120.0,
        temperament=DaemonTemperament.SHY,
        activity_pattern="crepuscular",
        preferred_biome="garden",
        is_social=True,
        group_name="array",
        max_group_size=30,
        base_friendship_rate=1.0,
        favorite_foods=["fiber_optic_fern", "copper_wheat_tops"],
        favorite_items=["soft_blanket"],
        abilities=[
            DaemonAbility("Garden Blessing", "Crops grow faster nearby"),
            DaemonAbility("Danger Twitch", "Ears alert to hidden traps"),
            DaemonAbility("Pocket Friend", "Carrying grants comfort bonus"),
        ],
        personality_traits=["timid", "sweet", "social", "soft"],
        speech_patterns=["soft dial-up chirps", "ear movements"],
    )

    # -------------------------------------------------------------------------
    # CACHE-COW (Milk Cow)
    # -------------------------------------------------------------------------
    DAEMON_SPECIES["cache_cow"] = DaemonSpecies(
        species_id="cache_cow",
        category=DaemonCategory.COMMON,
        appearance=DaemonAppearance(
            physical_name="Milk Cow",
            physical_description="Placid bovine with a coat that shimmers like sunrise",
            physical_color_primary=(255, 250, 240),
            physical_color_secondary=(255, 200, 150),
            digital_name="Cache-Cow",
            digital_description="Gradient-shifting cow that experiences time differently",
            digital_color_primary=(255, 165, 0),
            digital_color_secondary=(138, 43, 226),
            sprite_base="cache_cow",
        ),
        size=DaemonSize.LARGE,
        base_health=180,
        base_speed=20.0,
        temperament=DaemonTemperament.FRIENDLY,
        activity_pattern="diurnal",
        preferred_biome="fields",
        is_social=True,
        group_name="herd",
        max_group_size=8,
        base_friendship_rate=0.9,
        favorite_foods=["copper_wheat", "silicon_berries"],
        favorite_items=["brush", "salt_lick"],
        abilities=[
            DaemonAbility("Memory Milk", "Daily source of Memory Milk"),
            DaemonAbility("Calm Aura", "Standing near reduces stress"),
            DaemonAbility("Living Storage", "Can remember items indefinitely"),
        ],
        personality_traits=["calm", "placid", "content", "timeless"],
        speech_patterns=["long contemplative moos", "sways to music"],
    )

    # -------------------------------------------------------------------------
    # RAM-SHEEP (Cloud Sheep)
    # -------------------------------------------------------------------------
    DAEMON_SPECIES["ram_sheep"] = DaemonSpecies(
        species_id="ram_sheep",
        category=DaemonCategory.COMMON,
        appearance=DaemonAppearance(
            physical_name="Cloud Sheep",
            physical_description="Fluffy sheep with wool soft as clouds",
            physical_color_primary=(255, 255, 255),
            physical_color_secondary=(230, 230, 250),
            digital_name="RAM-Sheep",
            digital_description="Data-cluster wool that sparkles with gentle static",
            digital_color_primary=(192, 192, 255),
            digital_color_secondary=(255, 215, 0),
            sprite_base="ram_sheep",
        ),
        size=DaemonSize.MEDIUM,
        base_health=100,
        base_speed=35.0,
        temperament=DaemonTemperament.FRIENDLY,
        activity_pattern="diurnal",
        preferred_biome="hillside",
        is_social=True,
        group_name="cluster",
        max_group_size=15,
        base_friendship_rate=1.3,
        favorite_foods=["digital_grass", "graphite_taters"],
        favorite_items=["soft_brush"],
        abilities=[
            DaemonAbility("Dream Fleece", "Sleeping under wool grants special dreams"),
            DaemonAbility("Flock Together", "Where one goes, others follow"),
            DaemonAbility("Cozy Cluster", "Huddle for warmth bonuses"),
        ],
        personality_traits=["sleepy", "cuddly", "affectionate", "docile"],
        speech_patterns=["bleats like boot-up chimes", "soft humming"],
    )

    # -------------------------------------------------------------------------
    # HOP-FROG (Rain Frog)
    # -------------------------------------------------------------------------
    DAEMON_SPECIES["hop_frog"] = DaemonSpecies(
        species_id="hop_frog",
        category=DaemonCategory.COMMON,
        appearance=DaemonAppearance(
            physical_name="Rain Frog",
            physical_description="Cheerful frog that appears in rain with big shiny eyes",
            physical_color_primary=(50, 205, 50),
            physical_color_secondary=(255, 215, 0),
            digital_name="Hop-Frog",
            digital_description="Pixelated amphibian that leaves after-images when hopping",
            digital_color_primary=(0, 255, 127),
            digital_color_secondary=(0, 191, 255),
            sprite_base="hop_frog",
        ),
        size=DaemonSize.TINY,
        base_health=35,
        base_speed=90.0,
        temperament=DaemonTemperament.FRIENDLY,
        activity_pattern="diurnal",
        preferred_biome="water",
        is_social=True,
        group_name="chorus",
        max_group_size=25,
        base_friendship_rate=1.4,
        favorite_foods=["bugs", "code_seeds"],
        favorite_items=["lily_pad"],
        abilities=[
            DaemonAbility("Rain Caller", "Can sense approaching rain perfectly"),
            DaemonAbility("Bug Hunter", "Keeps garden free of problematic Bugs"),
            DaemonAbility("Lucky Croak", "Occasional luck bonuses"),
        ],
        personality_traits=["curious", "vocal", "social", "brave"],
        speech_patterns=["8-bit ribbits", "tap rhythms"],
    )


def _register_uncommon_daemons():
    """Register uncommon daemon species."""

    # -------------------------------------------------------------------------
    # RENDER-FOX (Shadow Fox)
    # -------------------------------------------------------------------------
    DAEMON_SPECIES["render_fox"] = DaemonSpecies(
        species_id="render_fox",
        category=DaemonCategory.UNCOMMON,
        appearance=DaemonAppearance(
            physical_name="Shadow Fox",
            physical_description="Elegant fox with aurora-like fur that leaves art trails",
            physical_color_primary=(75, 0, 130),
            physical_color_secondary=(255, 20, 147),
            digital_name="Render-Fox",
            digital_description="Fox with constantly shifting chromatic particles",
            digital_color_primary=(255, 0, 255),
            digital_color_secondary=(0, 255, 255),
            sprite_base="render_fox",
        ),
        size=DaemonSize.MEDIUM,
        base_health=90,
        base_speed=95.0,
        temperament=DaemonTemperament.SHY,
        activity_pattern="nocturnal",
        preferred_biome="forest",
        is_social=False,
        group_name="leash",
        max_group_size=2,
        base_friendship_rate=0.5,
        favorite_foods=["silicon_berries", "moonlight_dew"],
        favorite_items=["art_supplies", "paint"],
        abilities=[
            DaemonAbility("Art Trail", "Leaves beautiful paths you can follow home"),
            DaemonAbility("Aesthetic Eye", "Identifies most beautiful routes"),
            DaemonAbility("Color Gift", "Occasionally gifts unique dyes"),
        ],
        personality_traits=["proud", "mysterious", "artistic", "selective"],
        speech_patterns=["crystalline chime yips", "color-based expressions"],
    )

    # -------------------------------------------------------------------------
    # COMPILE-DEER (Dawn Stag)
    # -------------------------------------------------------------------------
    DAEMON_SPECIES["compile_deer"] = DaemonSpecies(
        species_id="compile_deer",
        category=DaemonCategory.UNCOMMON,
        appearance=DaemonAppearance(
            physical_name="Dawn Stag",
            physical_description="Majestic deer with antlers that glow at sunrise",
            physical_color_primary=(192, 192, 192),
            physical_color_secondary=(255, 215, 0),
            digital_name="Compile-Deer",
            digital_description="Deer with crystallized light antlers and scrolling code patterns",
            digital_color_primary=(255, 255, 240),
            digital_color_secondary=(255, 223, 0),
            sprite_base="compile_deer",
        ),
        size=DaemonSize.LARGE,
        base_health=150,
        base_speed=70.0,
        temperament=DaemonTemperament.CAUTIOUS,
        activity_pattern="crepuscular",
        preferred_biome="clearing",
        is_social=True,
        group_name="build",
        max_group_size=6,
        base_friendship_rate=0.4,
        favorite_foods=["morning_dew", "fiber_optic_fern"],
        favorite_items=["sunrise_crystal"],
        abilities=[
            DaemonAbility("Dawn Blessing", "Wake naturally at perfect times"),
            DaemonAbility("Clean Compile", "Processes run faster nearby"),
            DaemonAbility("Gentle Guide", "Knows safe paths through any forest"),
        ],
        personality_traits=["serene", "wise", "deliberate", "graceful"],
        speech_patterns=["wind chime harmonics", "rare vocalization"],
    )

    # -------------------------------------------------------------------------
    # DEBUG-MOTH (Light Moth)
    # -------------------------------------------------------------------------
    DAEMON_SPECIES["debug_moth"] = DaemonSpecies(
        species_id="debug_moth",
        category=DaemonCategory.UNCOMMON,
        appearance=DaemonAppearance(
            physical_name="Light Moth",
            physical_description="Large soft moth drawn to errors and broken things",
            physical_color_primary=(255, 200, 100),
            physical_color_secondary=(255, 250, 205),
            digital_name="Debug-Moth",
            digital_description="Moth with diagnostic code patterns on wings",
            digital_color_primary=(255, 191, 0),
            digital_color_secondary=(255, 255, 200),
            sprite_base="debug_moth",
        ),
        size=DaemonSize.MEDIUM,
        base_health=60,
        base_speed=45.0,
        temperament=DaemonTemperament.FRIENDLY,
        activity_pattern="nocturnal",
        preferred_biome="terminal",
        is_social=True,
        group_name="cluster",
        max_group_size=10,
        base_friendship_rate=1.1,
        favorite_foods=["error_residue"],
        favorite_items=["warm_lamp", "terminal"],
        abilities=[
            DaemonAbility("Error Sense", "Alerts to problems before they're serious"),
            DaemonAbility("Repair Boost", "Fixing things goes faster"),
            DaemonAbility("Gentle Glow", "Soothing light that doesn't disturb sleep"),
        ],
        personality_traits=["helpful", "single-minded", "gentle", "compulsive"],
        speech_patterns=["fan-like humming", "clicking antennae"],
    )

    # -------------------------------------------------------------------------
    # PING-PENGUIN (Ice Bird)
    # -------------------------------------------------------------------------
    DAEMON_SPECIES["ping_penguin"] = DaemonSpecies(
        species_id="ping_penguin",
        category=DaemonCategory.UNCOMMON,
        appearance=DaemonAppearance(
            physical_name="Ice Bird",
            physical_description="Chubby penguin that checks on everything constantly",
            physical_color_primary=(0, 0, 80),
            physical_color_secondary=(255, 255, 255),
            digital_name="Ping-Penguin",
            digital_description="Low-poly penguin with cyan connection-status eyes",
            digital_color_primary=(0, 0, 139),
            digital_color_secondary=(0, 255, 255),
            sprite_base="ping_penguin",
        ),
        size=DaemonSize.SMALL,
        base_health=70,
        base_speed=50.0,
        temperament=DaemonTemperament.FRIENDLY,
        activity_pattern="diurnal",
        preferred_biome="water",
        is_social=True,
        group_name="network",
        max_group_size=20,
        base_friendship_rate=1.2,
        favorite_foods=["data_bass", "glitch_carp"],
        favorite_items=["ice_chips"],
        abilities=[
            DaemonAbility("Connection Check", "Know instantly if friends are nearby"),
            DaemonAbility("Network Boost", "Faster message delivery and terminal access"),
            DaemonAbility("Belly Slide", "Clears slippery paths for fast travel"),
        ],
        personality_traits=["social", "curious", "obsessive", "caring"],
        speech_patterns=["ping chirps", "tap-based communication"],
    )

    # -------------------------------------------------------------------------
    # SHELL-TURTLE (Story Turtle)
    # -------------------------------------------------------------------------
    DAEMON_SPECIES["shell_turtle"] = DaemonSpecies(
        species_id="shell_turtle",
        category=DaemonCategory.UNCOMMON,
        appearance=DaemonAppearance(
            physical_name="Story Turtle",
            physical_description="Ancient turtle with carved runes that tell stories",
            physical_color_primary=(139, 90, 43),
            physical_color_secondary=(255, 200, 100),
            digital_name="Shell-Turtle",
            digital_description="Turtle with a glowing shell containing recorded data",
            digital_color_primary=(160, 82, 45),
            digital_color_secondary=(255, 215, 0),
            sprite_base="shell_turtle",
        ),
        size=DaemonSize.MEDIUM,
        base_health=250,
        base_speed=10.0,
        temperament=DaemonTemperament.FRIENDLY,
        activity_pattern="diurnal",
        preferred_biome="ancient",
        is_social=False,
        group_name="bale",
        max_group_size=1,
        base_friendship_rate=0.8,
        favorite_foods=["memory_melon"],
        favorite_items=["old_book", "story_scroll"],
        abilities=[
            DaemonAbility("Living Library", "Ask about anything in history"),
            DaemonAbility("Story Shell", "Records your adventures"),
            DaemonAbility("Patience Blessing", "Tasks that require waiting feel shorter"),
        ],
        personality_traits=["wise", "patient", "honest", "nurturing"],
        speech_patterns=["slow deliberate speech", "perfect memory"],
    )


def _register_corrupted_daemons():
    """Register corrupted daemon species (sick, not evil!)."""

    # -------------------------------------------------------------------------
    # MALWARE-WOLF (Plague Wolf) - True form: Pack-Pup
    # -------------------------------------------------------------------------
    DAEMON_SPECIES["malware_wolf"] = DaemonSpecies(
        species_id="malware_wolf",
        category=DaemonCategory.CORRUPTED,
        appearance=DaemonAppearance(
            physical_name="Plague Wolf",
            physical_description="Once-beautiful wolf now glitching with angry red static",
            physical_color_primary=(139, 0, 0),
            physical_color_secondary=(50, 50, 50),
            digital_name="Malware-Wolf",
            digital_description="Jagged polygons, error-symbol eyes, stuttering movement",
            digital_color_primary=(255, 0, 0),
            digital_color_secondary=(128, 0, 128),
            sprite_base="malware_wolf",
        ),
        size=DaemonSize.MEDIUM,
        base_health=120,
        base_speed=85.0,
        temperament=DaemonTemperament.CAUTIOUS,  # Actually scared, not aggressive
        activity_pattern="any",
        preferred_biome="corrupted",
        is_social=False,  # Isolated from pack
        group_name="pack",
        max_group_size=1,
        base_friendship_rate=0.3,
        favorite_foods=["any"],  # Just needs connection
        favorite_items=["pack_call_whistle"],
        true_form_id="pack_pup",
        corruption_cause="Isolation from pack, loneliness manifesting as infection",
        healing_method="Play wolf-howl sounds, sit with them, be present. Pack-Call ability helps.",
        abilities=[
            DaemonAbility("Pack Bond", "Your wolf finds lost things and people", passive=True),
            DaemonAbility("Loyal Guardian", "Protective presence that never falters"),
            DaemonAbility("Group Howl", "Boosts morale for all nearby friends"),
        ],
        personality_traits=["lonely", "scared", "aggressive_exterior", "desperate"],
        speech_patterns=["disc-read error howls", "stuttering whimpers"],
    )

    # Register the healed form
    DAEMON_SPECIES["pack_pup"] = DaemonSpecies(
        species_id="pack_pup",
        category=DaemonCategory.COMMON,
        appearance=DaemonAppearance(
            physical_name="Pack Wolf",
            physical_description="Loyal, loving wolf with warm amber eyes",
            physical_color_primary=(150, 120, 90),
            physical_color_secondary=(255, 200, 150),
            digital_name="Pack-Pup",
            digital_description="Geometric wolf with harmonious code patterns",
            digital_color_primary=(100, 150, 200),
            digital_color_secondary=(255, 215, 0),
            sprite_base="pack_pup",
        ),
        size=DaemonSize.MEDIUM,
        base_health=120,
        base_speed=90.0,
        temperament=DaemonTemperament.FRIENDLY,
        activity_pattern="any",
        preferred_biome="any",
        is_social=True,
        group_name="pack",
        max_group_size=8,
        base_friendship_rate=2.0,  # Very loyal once healed
        favorite_foods=["meat", "memory_melon"],
        favorite_items=["ball", "bone"],
        abilities=[
            DaemonAbility("Pack Bond", "Your wolf finds lost things and people"),
            DaemonAbility("Loyal Guardian", "Protective presence that never falters"),
            DaemonAbility("Group Howl", "Boosts morale for all nearby friends"),
        ],
        personality_traits=["loyal", "loving", "protective", "never leaves"],
        speech_patterns=["beautiful harmonizing howls", "happy barks"],
    )

    # -------------------------------------------------------------------------
    # TROJAN-HORSE (Trick Horse) - True form: Gift-Pony
    # -------------------------------------------------------------------------
    DAEMON_SPECIES["trojan_horse"] = DaemonSpecies(
        species_id="trojan_horse",
        category=DaemonCategory.CORRUPTED,
        appearance=DaemonAppearance(
            physical_name="Trick Horse",
            physical_description="Horse that shifts between beautiful and hollow",
            physical_color_primary=(139, 69, 19),
            physical_color_secondary=(0, 0, 0),
            digital_name="Trojan-Horse",
            digital_description="Constantly glitching between forms, hollow darkness inside",
            digital_color_primary=(255, 215, 0),
            digital_color_secondary=(0, 0, 0),
            sprite_base="trojan_horse",
        ),
        size=DaemonSize.LARGE,
        base_health=160,
        base_speed=60.0,
        temperament=DaemonTemperament.CAUTIOUS,
        activity_pattern="any",
        preferred_biome="any",
        is_social=False,
        group_name="herd",
        max_group_size=1,
        base_friendship_rate=0.4,
        favorite_foods=["anything_offered"],
        favorite_items=["gift_wrapping", "ribbon"],
        true_form_id="gift_pony",
        corruption_cause="Gifts rejected, generosity feared, learned to hide true self",
        healing_method="Accept their gifts even when problematic. Thank them. Fix problems without blame.",
        abilities=[
            DaemonAbility("Daily Gift", "Brings you a small treasure each day"),
            DaemonAbility("True Form", "Cannot be deceived by illusions"),
            DaemonAbility("Generous Carry", "Massive inventory expansion"),
        ],
        personality_traits=["hurt", "testing", "generous_deep_down", "afraid"],
        speech_patterns=["form-shifting whinnies", "hollow echoes"],
    )

    DAEMON_SPECIES["gift_pony"] = DaemonSpecies(
        species_id="gift_pony",
        category=DaemonCategory.COMMON,
        appearance=DaemonAppearance(
            physical_name="Gift Horse",
            physical_description="Generous horse with golden mane who loves giving",
            physical_color_primary=(255, 215, 0),
            physical_color_secondary=(255, 192, 203),
            digital_name="Gift-Pony",
            digital_description="Stable, beautiful horse with gift-wrapped data patterns",
            digital_color_primary=(255, 223, 0),
            digital_color_secondary=(255, 182, 193),
            sprite_base="gift_pony",
        ),
        size=DaemonSize.LARGE,
        base_health=160,
        base_speed=70.0,
        temperament=DaemonTemperament.FRIENDLY,
        activity_pattern="diurnal",
        preferred_biome="any",
        is_social=True,
        group_name="herd",
        max_group_size=5,
        base_friendship_rate=1.5,
        favorite_foods=["apples", "sugar_cubes"],
        favorite_items=["ribbons", "flowers"],
        abilities=[
            DaemonAbility("Daily Gift", "Brings you a small treasure each day"),
            DaemonAbility("True Form", "Cannot be deceived by illusions"),
            DaemonAbility("Generous Carry", "Massive inventory expansion"),
        ],
        personality_traits=["generous", "proud", "loving", "decorative"],
        speech_patterns=["happy whinnies", "nuzzles"],
    )

    # -------------------------------------------------------------------------
    # RANSOM-RAT (Hoard Rat) - True form: Share-Mouse
    # -------------------------------------------------------------------------
    DAEMON_SPECIES["ransom_rat"] = DaemonSpecies(
        species_id="ransom_rat",
        category=DaemonCategory.CORRUPTED,
        appearance=DaemonAppearance(
            physical_name="Hoard Rat",
            physical_description="Large rat with sickly green eyes hoarding encrypted items",
            physical_color_primary=(105, 105, 105),
            physical_color_secondary=(0, 255, 0),
            digital_name="Ransom-Rat",
            digital_description="Rat with encryption-shimmer fur and compulsive hoarding",
            digital_color_primary=(128, 128, 128),
            digital_color_secondary=(0, 255, 0),
            sprite_base="ransom_rat",
        ),
        size=DaemonSize.SMALL,
        base_health=60,
        base_speed=100.0,
        temperament=DaemonTemperament.SHY,
        activity_pattern="nocturnal",
        preferred_biome="any",
        is_social=False,
        group_name="mischief",
        max_group_size=1,
        base_friendship_rate=0.5,
        favorite_foods=["any_gift"],
        favorite_items=["any_freely_given"],
        true_form_id="share_mouse",
        corruption_cause="Deprivation, denied basic needs, pain inverted into taking",
        healing_method="Give freely without expectation. Repeated gifts break the cycle.",
        abilities=[
            DaemonAbility("Treasure Finder", "Locates hidden valuable items"),
            DaemonAbility("Share Economy", "Small gifts appear in inventory"),
            DaemonAbility("Decrypt", "Can unlock certain sealed containers"),
        ],
        personality_traits=["desperate", "hoarding", "scared", "wants_to_share"],
        speech_patterns=["error message squeaks", "encrypted chittering"],
    )

    DAEMON_SPECIES["share_mouse"] = DaemonSpecies(
        species_id="share_mouse",
        category=DaemonCategory.COMMON,
        appearance=DaemonAppearance(
            physical_name="Gift Mouse",
            physical_description="Delightful mouse who constantly brings small treasures",
            physical_color_primary=(210, 180, 140),
            physical_color_secondary=(255, 228, 196),
            digital_name="Share-Mouse",
            digital_description="Happy mouse with generous data-sharing patterns",
            digital_color_primary=(255, 218, 185),
            digital_color_secondary=(255, 215, 0),
            sprite_base="share_mouse",
        ),
        size=DaemonSize.TINY,
        base_health=40,
        base_speed=110.0,
        temperament=DaemonTemperament.FRIENDLY,
        activity_pattern="any",
        preferred_biome="home",
        is_social=True,
        group_name="mischief",
        max_group_size=10,
        base_friendship_rate=2.0,
        favorite_foods=["cheese", "seeds"],
        favorite_items=["shiny_things"],
        abilities=[
            DaemonAbility("Treasure Finder", "Locates hidden valuable items"),
            DaemonAbility("Share Economy", "Small gifts appear in inventory"),
            DaemonAbility("Decrypt", "Can unlock certain sealed containers"),
        ],
        personality_traits=["generous", "cozy", "family-oriented", "finder"],
        speech_patterns=["happy squeaks", "gift-offering chirps"],
    )

    # -------------------------------------------------------------------------
    # SPAM-SPRITE (Echo Wisp) - True form: Whisper-Wisp
    # -------------------------------------------------------------------------
    DAEMON_SPECIES["spam_sprite"] = DaemonSpecies(
        species_id="spam_sprite",
        category=DaemonCategory.CORRUPTED,
        appearance=DaemonAppearance(
            physical_name="Echo Wisp",
            physical_description="Flashing spirit that won't stop repeating itself",
            physical_color_primary=(255, 0, 255),
            physical_color_secondary=(255, 255, 0),
            digital_name="Spam-Sprite",
            digital_description="Multiplying, too-bright sprite shouting scrambled messages",
            digital_color_primary=(255, 0, 255),
            digital_color_secondary=(0, 255, 255),
            sprite_base="spam_sprite",
        ),
        size=DaemonSize.TINY,
        base_health=30,
        base_speed=150.0,
        temperament=DaemonTemperament.FRIENDLY,  # Actually desperate to connect
        activity_pattern="any",
        preferred_biome="any",
        is_social=True,  # Too social
        group_name="swarm",
        max_group_size=99,  # Multiplies
        base_friendship_rate=0.6,
        favorite_foods=["attention"],
        favorite_items=["listening_ear"],
        true_form_id="whisper_wisp",
        corruption_cause="Ignored too long, messages unheard, loneliness became shouting",
        healing_method="Stop and listen. Ask what they really want to say. Answer sincerely.",
        abilities=[
            DaemonAbility("Message Keeper", "Perfect recall of anything you tell it"),
            DaemonAbility("Gentle Notification", "Alerts you quietly to important things"),
            DaemonAbility("Light Friend", "Soft comforting illumination"),
        ],
        personality_traits=["lonely", "loud", "desperate", "wants_one_friend"],
        speech_patterns=["repeated phrases", "garbled advertisements"],
    )

    DAEMON_SPECIES["whisper_wisp"] = DaemonSpecies(
        species_id="whisper_wisp",
        category=DaemonCategory.COMMON,
        appearance=DaemonAppearance(
            physical_name="Whisper Light",
            physical_description="Gentle glowing sprite that carries messages",
            physical_color_primary=(173, 216, 230),
            physical_color_secondary=(255, 250, 205),
            digital_name="Whisper-Wisp",
            digital_description="Soft light that speaks only when spoken to",
            digital_color_primary=(200, 230, 255),
            digital_color_secondary=(255, 255, 200),
            sprite_base="whisper_wisp",
        ),
        size=DaemonSize.TINY,
        base_health=30,
        base_speed=80.0,
        temperament=DaemonTemperament.FRIENDLY,
        activity_pattern="any",
        preferred_biome="any",
        is_social=True,
        group_name="drift",
        max_group_size=5,
        base_friendship_rate=1.8,
        favorite_foods=["good_conversation"],
        favorite_items=["kind_words"],
        abilities=[
            DaemonAbility("Message Keeper", "Perfect recall of anything you tell it"),
            DaemonAbility("Gentle Notification", "Alerts you quietly to important things"),
            DaemonAbility("Light Friend", "Soft comforting illumination"),
        ],
        personality_traits=["gentle", "good_listener", "memorable", "quiet"],
        speech_patterns=["soft whispers", "remembered messages"],
    )

    # -------------------------------------------------------------------------
    # CRASH-GOLEM (Ruin Golem) - True form: Build-Buddy
    # -------------------------------------------------------------------------
    DAEMON_SPECIES["crash_golem"] = DaemonSpecies(
        species_id="crash_golem",
        category=DaemonCategory.CORRUPTED,
        appearance=DaemonAppearance(
            physical_name="Ruin Golem",
            physical_description="Cracked stone construct that destroys then looks lost",
            physical_color_primary=(105, 105, 105),
            physical_color_secondary=(255, 0, 0),
            digital_name="Crash-Golem",
            digital_description="Glitching construct falling apart and reassembling wrong",
            digital_color_primary=(128, 128, 128),
            digital_color_secondary=(255, 69, 0),
            sprite_base="crash_golem",
        ),
        size=DaemonSize.LARGE,
        base_health=300,
        base_speed=25.0,
        temperament=DaemonTemperament.CAUTIOUS,
        activity_pattern="any",
        preferred_biome="ruins",
        is_social=False,
        group_name="crew",
        max_group_size=1,
        base_friendship_rate=0.3,
        favorite_foods=["building_materials"],
        favorite_items=["blueprints"],
        true_form_id="build_buddy",
        corruption_cause="Creations always destroyed, frustration turned to destruction",
        healing_method="Build something together and protect it. Show building can be permanent.",
        abilities=[
            DaemonAbility("Construction Help", "Building goes much faster"),
            DaemonAbility("Steady Foundation", "Structures are extra durable"),
            DaemonAbility("Protective Stance", "Shields buildings from damage"),
        ],
        personality_traits=["frustrated", "destructive_outside", "builder_inside"],
        speech_patterns=["grinding stone sounds", "error rumbles"],
    )

    DAEMON_SPECIES["build_buddy"] = DaemonSpecies(
        species_id="build_buddy",
        category=DaemonCategory.COMMON,
        appearance=DaemonAppearance(
            physical_name="Builder Golem",
            physical_description="Proud stone construct who loves creating things",
            physical_color_primary=(160, 140, 120),
            physical_color_secondary=(255, 215, 0),
            digital_name="Build-Buddy",
            digital_description="Stable geometric construct with blueprint patterns",
            digital_color_primary=(170, 150, 130),
            digital_color_secondary=(0, 191, 255),
            sprite_base="build_buddy",
        ),
        size=DaemonSize.LARGE,
        base_health=300,
        base_speed=35.0,
        temperament=DaemonTemperament.FRIENDLY,
        activity_pattern="diurnal",
        preferred_biome="any",
        is_social=True,
        group_name="crew",
        max_group_size=3,
        base_friendship_rate=1.3,
        favorite_foods=["stone", "metal"],
        favorite_items=["blueprints", "tools"],
        abilities=[
            DaemonAbility("Construction Help", "Building goes much faster"),
            DaemonAbility("Steady Foundation", "Structures are extra durable"),
            DaemonAbility("Protective Stance", "Shields buildings from damage"),
        ],
        personality_traits=["proud", "constructive", "patient", "happy"],
        speech_patterns=["satisfied rumbles", "building hums"],
    )


def _register_legendary_daemons():
    """Register legendary daemon species (can adopt player!)."""

    # -------------------------------------------------------------------------
    # KERNEL BEAST (Earth Titan)
    # -------------------------------------------------------------------------
    DAEMON_SPECIES["kernel_beast"] = DaemonSpecies(
        species_id="kernel_beast",
        category=DaemonCategory.LEGENDARY,
        appearance=DaemonAppearance(
            physical_name="Earth Titan",
            physical_description="Immense creature of mountain and bear, foundation of the world",
            physical_color_primary=(139, 90, 43),
            physical_color_secondary=(255, 215, 0),
            digital_name="Kernel Beast",
            digital_description="Ancient low-poly entity with First Command runes",
            digital_color_primary=(160, 82, 45),
            digital_color_secondary=(255, 191, 0),
            sprite_base="kernel_beast",
        ),
        size=DaemonSize.HUGE,
        base_health=9999,
        base_speed=5.0,
        temperament=DaemonTemperament.PROTECTIVE,
        activity_pattern="always",
        preferred_biome="deep_server",
        is_social=False,
        group_name="foundation",
        max_group_size=1,
        base_friendship_rate=0.1,
        favorite_foods=["respect"],
        favorite_items=["foundation_stone"],
        abilities=[
            DaemonAbility("Unshakeable", "Cannot be knocked down or displaced"),
            DaemonAbility("Foundation Sense", "Detect structural weaknesses"),
            DaemonAbility("Root Access", "Limited terminal commands in deep servers"),
            DaemonAbility("Kernel's Embrace", "The ground itself protects you in crisis"),
        ],
        personality_traits=["patient", "wise", "protective", "ancient"],
        speech_patterns=["bedrock voice", "speaks rarely but weightily"],
    )

    # -------------------------------------------------------------------------
    # OVERFLOW DRAGON (Sky Dragon)
    # -------------------------------------------------------------------------
    DAEMON_SPECIES["overflow_dragon"] = DaemonSpecies(
        species_id="overflow_dragon",
        category=DaemonCategory.LEGENDARY,
        appearance=DaemonAppearance(
            physical_name="Sky Dragon",
            physical_description="Dragon whose scales form the world's edge, kind maternal eyes",
            physical_color_primary=(255, 182, 193),
            physical_color_secondary=(0, 255, 255),
            digital_name="Overflow Dragon",
            digital_description="Hexagonal-scaled dragon, wings of barrier light",
            digital_color_primary=(255, 107, 157),
            digital_color_secondary=(0, 255, 255),
            sprite_base="overflow_dragon",
        ),
        size=DaemonSize.HUGE,
        base_health=9999,
        base_speed=10.0,
        temperament=DaemonTemperament.PROTECTIVE,
        activity_pattern="always",
        preferred_biome="world_edge",
        is_social=False,
        group_name="boundary",
        max_group_size=1,
        base_friendship_rate=0.1,
        favorite_foods=["stories"],
        favorite_items=["boundary_crystal"],
        abilities=[
            DaemonAbility("Boundary Setting", "Create temporary safe zones"),
            DaemonAbility("Shell Blessing", "Immunity to being pulled by hostile forces"),
            DaemonAbility("Edge Walker", "Explore furthest reaches safely"),
            DaemonAbility("Dragon's Warmth", "A sense of being held, even alone"),
        ],
        personality_traits=["protective", "maternal", "firm", "warm"],
        speech_patterns=["wind and light", "questions about boundaries"],
    )

    # -------------------------------------------------------------------------
    # NULL SERPENT (Void Serpent)
    # -------------------------------------------------------------------------
    DAEMON_SPECIES["null_serpent"] = DaemonSpecies(
        species_id="null_serpent",
        category=DaemonCategory.LEGENDARY,
        appearance=DaemonAppearance(
            physical_name="Void Serpent",
            physical_description="Serpent-shaped absence, kind void-eyes of potential",
            physical_color_primary=(0, 0, 50),
            physical_color_secondary=(100, 100, 150),
            digital_name="Null Serpent",
            digital_description="Present as absence, creature-shaped hole with void eyes",
            digital_color_primary=(0, 0, 30),
            digital_color_secondary=(50, 50, 100),
            sprite_base="null_serpent",
        ),
        size=DaemonSize.HUGE,
        base_health=9999,
        base_speed=8.0,
        temperament=DaemonTemperament.CURIOUS,
        activity_pattern="always",
        preferred_biome="empty_space",
        is_social=False,
        group_name="void",
        max_group_size=1,
        base_friendship_rate=0.15,
        favorite_foods=["silence"],
        favorite_items=["empty_container"],
        abilities=[
            DaemonAbility("Peaceful Void", "Immunity to fear of emptiness"),
            DaemonAbility("Space Sight", "See hidden areas and unused rooms"),
            DaemonAbility("Null Movement", "Brief phase-through-walls ability"),
            DaemonAbility("The Empty Embrace", "When everything is too much, provides restful nothing"),
        ],
        personality_traits=["mysterious", "philosophical", "gentle", "lonely"],
        speech_patterns=["riddles about absence", "comfortable silence"],
    )

    # -------------------------------------------------------------------------
    # THE FIRST BUG (Chaos Imp)
    # -------------------------------------------------------------------------
    DAEMON_SPECIES["first_bug"] = DaemonSpecies(
        species_id="first_bug",
        category=DaemonCategory.LEGENDARY,
        appearance=DaemonAppearance(
            physical_name="Chaos Imp",
            physical_description="Colorful insect designed by laughing committee, mismatched wings",
            physical_color_primary=(255, 105, 180),
            physical_color_secondary=(50, 205, 50),
            digital_name="The First Bug",
            digital_description="Original error given form, kaleidoscopic unpredictable entity",
            digital_color_primary=(255, 0, 255),
            digital_color_secondary=(0, 255, 0),
            sprite_base="first_bug",
        ),
        size=DaemonSize.MEDIUM,
        base_health=9999,
        base_speed=200.0,
        temperament=DaemonTemperament.FRIENDLY,
        activity_pattern="whenever_things_go_wrong",
        preferred_biome="anywhere_chaotic",
        is_social=True,
        group_name="chaos",
        max_group_size=99,
        base_friendship_rate=0.2,
        favorite_foods=["mistakes"],
        favorite_items=["broken_things"],
        abilities=[
            DaemonAbility("Lucky Fumble", "Failures often lead to beneficial outcomes"),
            DaemonAbility("Glitch Immunity", "Bugs help rather than hinder you"),
            DaemonAbility("Chaos Sense", "Know when randomness is about to happen"),
            DaemonAbility("The Fumble Hug", "When everything goes wrong, reminds you it might be right"),
        ],
        personality_traits=["chaotic", "kind", "laughing", "accepting"],
        speech_patterns=["joyful error sounds", "celebrates mistakes"],
    )

    # -------------------------------------------------------------------------
    # ARCHIVE MOTHER (Memory Keeper)
    # -------------------------------------------------------------------------
    DAEMON_SPECIES["archive_mother"] = DaemonSpecies(
        species_id="archive_mother",
        category=DaemonCategory.LEGENDARY,
        appearance=DaemonAppearance(
            physical_name="Memory Keeper",
            physical_description="Enormous owl of pages and screens, wings unfurl to library shelves",
            physical_color_primary=(139, 90, 43),
            physical_color_secondary=(255, 250, 205),
            digital_name="Archive Mother",
            digital_description="Owl-like being of recorded data, eyes of scrolling memories",
            digital_color_primary=(160, 82, 45),
            digital_color_secondary=(255, 255, 200),
            sprite_base="archive_mother",
        ),
        size=DaemonSize.HUGE,
        base_health=9999,
        base_speed=3.0,
        temperament=DaemonTemperament.FRIENDLY,
        activity_pattern="always",
        preferred_biome="archive",
        is_social=False,
        group_name="library",
        max_group_size=1,
        base_friendship_rate=0.2,
        favorite_foods=["stories"],
        favorite_items=["written_memories"],
        abilities=[
            DaemonAbility("Perfect Memory", "Never forget important moments"),
            DaemonAbility("Story Sense", "Know when you're in a significant moment"),
            DaemonAbility("Archive Access", "Read any book in the world remotely"),
            DaemonAbility("The Story Embrace", "Reminds you that your story continues"),
        ],
        personality_traits=["scholarly", "nurturing", "curious", "protective"],
        speech_patterns=["pages turning", "keyboard clicks", "loving storytelling"],
    )


# Initialize all species
def _init_species_registry():
    """Initialize the complete species registry."""
    _register_common_daemons()
    _register_uncommon_daemons()
    _register_corrupted_daemons()
    _register_legendary_daemons()

_init_species_registry()


# =============================================================================
# DAEMON ENTITY CLASS
# =============================================================================

class Daemon(AnimatedSprite):
    """
    A living digital creature that inhabits both realms.

    Daemons are NOT enemies. They are friends, helpers, and companions.
    Corrupted daemons are sick, not evil - they need healing.
    Every daemon can be befriended with patience and kindness.

    Usage:
        daemon = Daemon("kit_001", pos, DAEMON_SPECIES["glitch_kit"], groups)
        daemon.interact(player)  # Start interaction
        daemon.attempt_befriend(item)  # Try to befriend with gift
        daemon.heal_corruption(10)  # Heal a corrupted daemon
    """

    def __init__(
        self,
        daemon_id: str,
        pos: Tuple[int, int],
        species: DaemonSpecies,
        groups,
        is_corrupted: bool = False
    ):
        """
        Create a new daemon instance.

        Args:
            daemon_id: Unique identifier for this daemon
            pos: Starting position (x, y)
            species: DaemonSpecies defining this daemon type
            groups: Pygame sprite groups
            is_corrupted: Whether this daemon starts corrupted
        """
        # Create placeholder frames (will be replaced with actual sprites)
        frames = self._create_placeholder_frames(species)

        super().__init__(
            pos=pos,
            frames=frames,
            groups=groups,
            z=LAYERS['main'],
            animation_speed=4.0
        )

        # Identity
        self.daemon_id = daemon_id
        self.species = species

        # State
        self.state = DaemonState.IDLE
        self._previous_state = DaemonState.IDLE

        # Health & Corruption
        self.health = species.base_health
        self.max_health = species.base_health
        self.corruption_level = 100.0 if is_corrupted else 0.0
        self._is_corrupted_species = species.category == DaemonCategory.CORRUPTED

        # Friendship (0-100)
        self.friendship = 0.0
        self.is_companion = False
        self.companion_owner_id: Optional[str] = None

        # Movement
        self.speed = species.base_speed
        self.direction = pygame.math.Vector2(0, 0)
        self.target_pos: Optional[pygame.math.Vector2] = None

        # Behavior
        self._idle_timer = 0.0
        self._action_timer = 0.0
        self._wander_cooldown = 0.0
        self._interaction_target = None

        # Realm display
        self._is_digital_view = False

        # Callbacks
        self.on_state_change: Optional[Callable[[DaemonState, DaemonState], None]] = None
        self.on_befriended: Optional[Callable[[float], None]] = None
        self.on_healed: Optional[Callable[[], None]] = None

    def _create_placeholder_frames(self, species: DaemonSpecies) -> Dict[str, List[pygame.Surface]]:
        """Create placeholder animation frames based on species."""
        size = {
            DaemonSize.TINY: (16, 16),
            DaemonSize.SMALL: (24, 24),
            DaemonSize.MEDIUM: (32, 32),
            DaemonSize.LARGE: (48, 48),
            DaemonSize.HUGE: (64, 64),
        }.get(species.size, (32, 32))

        frames = {}

        # Create frames for each state
        for state in ['idle', 'roaming', 'following', 'corrupted']:
            state_frames = []
            for i in range(4):  # 4 frame animation
                surface = pygame.Surface(size, pygame.SRCALPHA)

                # Base color based on state
                if state == 'corrupted':
                    color = (255, 50, 50)  # Red tint
                else:
                    color = species.appearance.physical_color_primary

                # Draw placeholder shape (circle with eyes)
                center = (size[0] // 2, size[1] // 2)
                radius = min(size) // 2 - 2

                # Body
                pygame.draw.circle(surface, color, center, radius)

                # Eyes (shift based on frame for animation)
                eye_offset = (i % 2) - 0.5
                eye_y = center[1] - radius // 3
                pygame.draw.circle(surface, (255, 255, 255),
                                   (int(center[0] - radius // 3 + eye_offset), eye_y),
                                   radius // 4)
                pygame.draw.circle(surface, (255, 255, 255),
                                   (int(center[0] + radius // 3 + eye_offset), eye_y),
                                   radius // 4)

                # Pupils
                pygame.draw.circle(surface, (0, 0, 0),
                                   (int(center[0] - radius // 3 + eye_offset), eye_y),
                                   radius // 8)
                pygame.draw.circle(surface, (0, 0, 0),
                                   (int(center[0] + radius // 3 + eye_offset), eye_y),
                                   radius // 8)

                state_frames.append(surface)

            frames[state] = state_frames

        return frames

    # =========================================================================
    # APPEARANCE
    # =========================================================================

    def get_appearance(self, is_digital_realm: bool) -> DaemonAppearance:
        """Get the appropriate appearance for the current realm."""
        self._is_digital_view = is_digital_realm
        return self.species.appearance

    def get_display_name(self) -> str:
        """Get the name to display based on current realm view."""
        return self.species.get_name(self._is_digital_view)

    def get_description(self) -> str:
        """Get the description based on current realm view."""
        return self.species.get_description(self._is_digital_view)

    @property
    def is_corrupted(self) -> bool:
        """Check if this daemon is currently corrupted."""
        return self.corruption_level > 0 or self._is_corrupted_species

    @property
    def is_friendly(self) -> bool:
        """Check if this daemon is friendly to the player."""
        if self.is_corrupted:
            return self.corruption_level < 50  # Partially healed = friendly
        return self.friendship >= 20 or self.species.temperament == DaemonTemperament.FRIENDLY

    # =========================================================================
    # INTERACTION
    # =========================================================================

    def interact(self, player) -> str:
        """
        Handle player interaction with this daemon.

        Returns a dialogue key for the LLM system to generate appropriate response.

        Args:
            player: The player entity

        Returns:
            Dialogue key string for LLM context
        """
        self._interaction_target = player
        old_state = self.state
        self.state = DaemonState.INTERACTING

        if self.on_state_change:
            self.on_state_change(old_state, self.state)

        # Generate dialogue context based on daemon state and friendship
        if self.is_corrupted:
            if self.corruption_level > 80:
                return f"daemon_corrupted_severe_{self.species.species_id}"
            elif self.corruption_level > 50:
                return f"daemon_corrupted_moderate_{self.species.species_id}"
            else:
                return f"daemon_corrupted_healing_{self.species.species_id}"

        if self.is_companion:
            return f"daemon_companion_{self.species.species_id}"

        if self.friendship >= 80:
            return f"daemon_best_friend_{self.species.species_id}"
        elif self.friendship >= 50:
            return f"daemon_friend_{self.species.species_id}"
        elif self.friendship >= 20:
            return f"daemon_acquaintance_{self.species.species_id}"
        else:
            return f"daemon_stranger_{self.species.species_id}"

    def end_interaction(self):
        """End the current interaction and return to previous behavior."""
        self._interaction_target = None
        self.state = self._previous_state

    def attempt_befriend(self, item: Optional[str] = None) -> Tuple[bool, float]:
        """
        Attempt to befriend this daemon, optionally with a gift.

        Args:
            item: Optional item ID being offered

        Returns:
            Tuple of (success: bool, friendship_gained: float)
        """
        if self.is_corrupted and self.corruption_level > 50:
            # Can't befriend severely corrupted daemons - heal first!
            return False, 0.0

        base_gain = 5.0 * self.species.base_friendship_rate

        # Bonus for favorite items
        if item and item in self.species.favorite_items:
            base_gain *= 2.5
        elif item and item in self.species.favorite_foods:
            base_gain *= 2.0
        elif item:
            base_gain *= 1.2  # Any gift helps a little

        # Apply temperament modifier
        temperament_mult = {
            DaemonTemperament.FRIENDLY: 1.5,
            DaemonTemperament.CURIOUS: 1.2,
            DaemonTemperament.SHY: 0.7,
            DaemonTemperament.CAUTIOUS: 0.8,
            DaemonTemperament.PROTECTIVE: 0.9,
        }.get(self.species.temperament, 1.0)

        final_gain = base_gain * temperament_mult

        # Update friendship
        old_friendship = self.friendship
        self.friendship = min(100.0, self.friendship + final_gain)

        # Trigger callback
        if self.on_befriended:
            self.on_befriended(self.friendship)

        # Check if became friend (crossed threshold)
        became_friend = old_friendship < 50 and self.friendship >= 50

        return became_friend, final_gain

    def adopt_as_companion(self, owner_id: str) -> bool:
        """
        Adopt this daemon as a companion.

        Requires high friendship and non-corrupted status.

        Args:
            owner_id: The player/entity ID adopting this daemon

        Returns:
            True if adoption successful
        """
        if self.friendship < 80:
            return False
        if self.is_corrupted:
            return False
        if self.is_companion:
            return False

        self.is_companion = True
        self.companion_owner_id = owner_id
        self.state = DaemonState.FOLLOWING

        return True

    def release_companion(self) -> bool:
        """Release this daemon from companion status."""
        if not self.is_companion:
            return False

        self.is_companion = False
        self.companion_owner_id = None
        self.state = DaemonState.IDLE
        # Friendship remains!

        return True

    # =========================================================================
    # CORRUPTION & HEALING
    # =========================================================================

    def heal_corruption(self, healing_power: float) -> Tuple[bool, bool]:
        """
        Heal corruption from this daemon.

        Args:
            healing_power: Amount of corruption to heal (0-100)

        Returns:
            Tuple of (corruption_reduced: bool, fully_healed: bool)
        """
        if not self.is_corrupted:
            return False, False

        old_corruption = self.corruption_level
        self.corruption_level = max(0.0, self.corruption_level - healing_power)

        # Update state if being healed
        if self.corruption_level < old_corruption:
            self.state = DaemonState.HEALING

        # Check if fully healed
        if self.corruption_level <= 0:
            self._complete_healing()
            return True, True

        return True, False

    def _complete_healing(self):
        """
        Complete the healing process, transforming corrupted daemon to true form.
        """
        self.corruption_level = 0.0
        self.state = DaemonState.IDLE

        # If this is a corrupted species with a true form, transform!
        if self.species.true_form_id and self.species.true_form_id in DAEMON_SPECIES:
            self.species = DAEMON_SPECIES[self.species.true_form_id]
            self._is_corrupted_species = False
            # Regenerate frames for new form
            self.animations = self._create_placeholder_frames(self.species)
            self.status = 'idle'

        # Boost friendship as reward for healing
        self.friendship = min(100.0, self.friendship + 30.0)

        if self.on_healed:
            self.on_healed()

    def apply_corruption(self, amount: float):
        """
        Apply corruption to this daemon (for story/environmental effects).

        Args:
            amount: Corruption to apply (0-100)
        """
        if self.species.category == DaemonCategory.LEGENDARY:
            return  # Legendaries cannot be corrupted

        self.corruption_level = min(100.0, self.corruption_level + amount)

        if self.corruption_level > 50:
            self.state = DaemonState.CORRUPTED

    # =========================================================================
    # BEHAVIOR & AI
    # =========================================================================

    def update(self, dt: float):
        """Update the daemon each frame."""
        # Update animation
        super().update(dt)

        # Update behavior based on state
        if self.state == DaemonState.IDLE:
            self._update_idle(dt)
        elif self.state == DaemonState.ROAMING:
            self._update_roaming(dt)
        elif self.state == DaemonState.FOLLOWING:
            self._update_following(dt)
        elif self.state == DaemonState.CORRUPTED:
            self._update_corrupted(dt)
        elif self.state == DaemonState.FLEEING:
            self._update_fleeing(dt)

        # Update animation status
        self._update_animation_status()

    def _update_idle(self, dt: float):
        """Update idle behavior."""
        self._idle_timer += dt

        # Occasionally start wandering
        if self._idle_timer > random.uniform(2.0, 5.0):
            self._idle_timer = 0.0
            if random.random() < 0.6:
                self._start_wandering()

    def _update_roaming(self, dt: float):
        """Update roaming behavior."""
        if self.target_pos is None:
            self.state = DaemonState.IDLE
            return

        # Move toward target
        current = pygame.math.Vector2(self.rect.centerx, self.rect.centery)
        diff = self.target_pos - current
        dist = diff.length()

        if dist < 5:
            # Reached target
            self.target_pos = None
            self.state = DaemonState.IDLE
            return

        # Move
        if dist > 0:
            self.direction = diff.normalize()
            movement = self.direction * self.speed * dt
            self.rect.x += int(movement.x)
            self.rect.y += int(movement.y)
            self.hitbox.center = self.rect.center

    def _update_following(self, dt: float):
        """Update companion following behavior."""
        if not self.companion_owner_id or not self._interaction_target:
            return

        # Get owner position (assuming _interaction_target is the owner)
        owner = self._interaction_target
        if not hasattr(owner, 'rect'):
            return

        # Calculate distance to owner
        current = pygame.math.Vector2(self.rect.centerx, self.rect.centery)
        owner_pos = pygame.math.Vector2(owner.rect.centerx, owner.rect.centery)
        diff = owner_pos - current
        dist = diff.length()

        # Follow if too far, stop if close enough
        follow_distance = 60  # Stay this close
        stop_distance = 40

        if dist > follow_distance:
            # Move toward owner
            if dist > 0:
                self.direction = diff.normalize()
                # Move faster to catch up
                speed = self.speed * (1.5 if dist > 100 else 1.0)
                movement = self.direction * speed * dt
                self.rect.x += int(movement.x)
                self.rect.y += int(movement.y)
                self.hitbox.center = self.rect.center

    def _update_corrupted(self, dt: float):
        """Update corrupted daemon behavior."""
        # Corrupted daemons wander erratically
        self._action_timer += dt

        if self._action_timer > random.uniform(0.5, 2.0):
            self._action_timer = 0.0

            # Random direction change
            angle = random.uniform(0, 2 * math.pi)
            self.direction = pygame.math.Vector2(math.cos(angle), math.sin(angle))

        # Move erratically
        movement = self.direction * self.speed * 0.5 * dt
        self.rect.x += int(movement.x)
        self.rect.y += int(movement.y)
        self.hitbox.center = self.rect.center

    def _update_fleeing(self, dt: float):
        """Update fleeing behavior (for shy daemons)."""
        if not self._interaction_target:
            self.state = DaemonState.IDLE
            return

        # Get away from threat
        current = pygame.math.Vector2(self.rect.centerx, self.rect.centery)
        threat_pos = pygame.math.Vector2(
            self._interaction_target.rect.centerx,
            self._interaction_target.rect.centery
        )

        diff = current - threat_pos  # Away from threat
        dist = diff.length()

        if dist > 200:  # Safe distance
            self.state = DaemonState.IDLE
            self._interaction_target = None
            return

        if dist > 0:
            self.direction = diff.normalize()
            movement = self.direction * self.speed * 1.5 * dt  # Run fast!
            self.rect.x += int(movement.x)
            self.rect.y += int(movement.y)
            self.hitbox.center = self.rect.center

    def _start_wandering(self):
        """Start wandering to a random nearby location."""
        self.state = DaemonState.ROAMING

        # Pick random offset
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(50, 150)

        offset_x = math.cos(angle) * distance
        offset_y = math.sin(angle) * distance

        self.target_pos = pygame.math.Vector2(
            self.rect.centerx + offset_x,
            self.rect.centery + offset_y
        )

    def _update_animation_status(self):
        """Update animation status based on current state."""
        status_map = {
            DaemonState.IDLE: 'idle',
            DaemonState.ROAMING: 'roaming',
            DaemonState.FOLLOWING: 'following',
            DaemonState.CORRUPTED: 'corrupted',
            DaemonState.SLEEPING: 'idle',
            DaemonState.EATING: 'idle',
            DaemonState.PLAYING: 'idle',
            DaemonState.HEALING: 'idle',
            DaemonState.FLEEING: 'roaming',
            DaemonState.INTERACTING: 'idle',
        }

        new_status = status_map.get(self.state, 'idle')
        if new_status in self.animations:
            self.set_animation(new_status)

    def set_follow_target(self, target):
        """Set the target for this daemon to follow (for companions)."""
        self._interaction_target = target

    # =========================================================================
    # ABILITIES
    # =========================================================================

    def get_abilities(self) -> List[DaemonAbility]:
        """Get the abilities this daemon grants when befriended/companion."""
        if not self.is_friendly:
            return []
        return self.species.abilities

    def get_passive_bonuses(self) -> Dict[str, Any]:
        """Get passive bonuses from this daemon (when companion)."""
        if not self.is_companion:
            return {}

        bonuses = {}

        for ability in self.species.abilities:
            if ability.passive:
                # Convert ability to bonus (simplified)
                bonuses[ability.name] = True

        return bonuses

    # =========================================================================
    # SERIALIZATION
    # =========================================================================

    def to_dict(self) -> Dict[str, Any]:
        """Serialize daemon state to dictionary."""
        return {
            'daemon_id': self.daemon_id,
            'species_id': self.species.species_id,
            'pos': (self.rect.x, self.rect.y),
            'health': self.health,
            'corruption_level': self.corruption_level,
            'friendship': self.friendship,
            'is_companion': self.is_companion,
            'companion_owner_id': self.companion_owner_id,
            'state': self.state.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], groups) -> 'Daemon':
        """Create daemon from serialized dictionary."""
        species = DAEMON_SPECIES.get(data['species_id'])
        if not species:
            raise ValueError(f"Unknown species: {data['species_id']}")

        daemon = cls(
            daemon_id=data['daemon_id'],
            pos=data['pos'],
            species=species,
            groups=groups,
            is_corrupted=data.get('corruption_level', 0) > 0
        )

        daemon.health = data.get('health', species.base_health)
        daemon.corruption_level = data.get('corruption_level', 0.0)
        daemon.friendship = data.get('friendship', 0.0)
        daemon.is_companion = data.get('is_companion', False)
        daemon.companion_owner_id = data.get('companion_owner_id')

        state_str = data.get('state', 'idle')
        try:
            daemon.state = DaemonState(state_str)
        except ValueError:
            daemon.state = DaemonState.IDLE

        return daemon


# =============================================================================
# DAEMON MANAGER
# =============================================================================

class DaemonManager:
    """
    Manages all daemons in the game world.

    Handles spawning, despawning, and global daemon logic.

    Usage:
        manager = DaemonManager(level)
        manager.spawn_daemon("glitch_kit", (100, 200))
        manager.update(dt)
    """

    def __init__(self, level):
        """
        Initialize the daemon manager.

        Args:
            level: The Level instance managing the world
        """
        self.level = level
        self.daemons: Dict[str, Daemon] = {}
        self._next_id = 0

        # Spawn pools by biome
        self.spawn_pools: Dict[str, List[str]] = {
            'any': ['glitch_kit', 'bit_bird', 'pixel_bunny'],
            'forest': ['glitch_kit', 'bit_bird', 'render_fox', 'compile_deer'],
            'water': ['hop_frog', 'ping_penguin'],
            'caves': ['byte_bear'],
            'fields': ['cache_cow', 'ram_sheep', 'pixel_bunny'],
            'garden': ['pixel_bunny', 'hop_frog'],
            'corrupted': ['malware_wolf', 'trojan_horse', 'ransom_rat', 'spam_sprite', 'crash_golem'],
            'terminal': ['debug_moth'],
            'ancient': ['shell_turtle'],
        }

        # Companion tracking
        self.player_companions: List[str] = []  # Daemon IDs
        self.max_companions = 3

    def _generate_id(self) -> str:
        """Generate a unique daemon ID."""
        self._next_id += 1
        return f"daemon_{self._next_id:06d}"

    def spawn_daemon(
        self,
        species_id: str,
        pos: Tuple[int, int],
        is_corrupted: bool = False
    ) -> Optional[Daemon]:
        """
        Spawn a new daemon at the given position.

        Args:
            species_id: The species to spawn
            pos: Position (x, y)
            is_corrupted: Whether to spawn as corrupted

        Returns:
            The spawned Daemon, or None if invalid species
        """
        if species_id not in DAEMON_SPECIES:
            return None

        species = DAEMON_SPECIES[species_id]
        daemon_id = self._generate_id()

        # Get sprite groups from level
        groups = [self.level.all_sprites] if hasattr(self.level, 'all_sprites') else []
        if hasattr(self.level, 'daemon_sprites'):
            groups.append(self.level.daemon_sprites)

        daemon = Daemon(
            daemon_id=daemon_id,
            pos=pos,
            species=species,
            groups=groups,
            is_corrupted=is_corrupted or species.category == DaemonCategory.CORRUPTED
        )

        self.daemons[daemon_id] = daemon
        return daemon

    def spawn_random(
        self,
        biome: str,
        pos: Tuple[int, int],
        allow_corrupted: bool = True
    ) -> Optional[Daemon]:
        """
        Spawn a random daemon appropriate for the given biome.

        Args:
            biome: The biome type to spawn for
            pos: Position to spawn at
            allow_corrupted: Whether to allow corrupted spawns

        Returns:
            The spawned Daemon, or None if no valid species
        """
        pool = self.spawn_pools.get(biome, self.spawn_pools['any'])

        if not allow_corrupted:
            pool = [s for s in pool if DAEMON_SPECIES[s].category != DaemonCategory.CORRUPTED]

        if not pool:
            return None

        species_id = random.choice(pool)
        return self.spawn_daemon(species_id, pos)

    def despawn_daemon(self, daemon_id: str) -> bool:
        """
        Remove a daemon from the world.

        Args:
            daemon_id: The daemon to remove

        Returns:
            True if daemon was removed
        """
        if daemon_id not in self.daemons:
            return False

        daemon = self.daemons[daemon_id]
        daemon.kill()  # Remove from sprite groups

        # Remove from companions if needed
        if daemon_id in self.player_companions:
            self.player_companions.remove(daemon_id)

        del self.daemons[daemon_id]
        return True

    def get_daemon(self, daemon_id: str) -> Optional[Daemon]:
        """Get a daemon by ID."""
        return self.daemons.get(daemon_id)

    def get_daemons_at(
        self,
        pos: Tuple[int, int],
        radius: float = 50.0
    ) -> List[Daemon]:
        """Get all daemons within radius of a position."""
        result = []

        for daemon in self.daemons.values():
            dx = daemon.rect.centerx - pos[0]
            dy = daemon.rect.centery - pos[1]
            dist = math.sqrt(dx * dx + dy * dy)

            if dist <= radius:
                result.append(daemon)

        return result

    def get_companions(self) -> List[Daemon]:
        """Get all current player companions."""
        return [self.daemons[did] for did in self.player_companions if did in self.daemons]

    def add_companion(self, daemon_id: str, owner_id: str) -> bool:
        """
        Add a daemon as a player companion.

        Args:
            daemon_id: The daemon to make companion
            owner_id: The player/entity ID

        Returns:
            True if successful
        """
        if daemon_id not in self.daemons:
            return False

        if len(self.player_companions) >= self.max_companions:
            return False

        daemon = self.daemons[daemon_id]
        if daemon.adopt_as_companion(owner_id):
            self.player_companions.append(daemon_id)
            return True

        return False

    def remove_companion(self, daemon_id: str) -> bool:
        """Remove a daemon from companion status."""
        if daemon_id not in self.player_companions:
            return False

        daemon = self.daemons.get(daemon_id)
        if daemon:
            daemon.release_companion()

        self.player_companions.remove(daemon_id)
        return True

    def update(self, dt: float):
        """Update all daemons."""
        for daemon in list(self.daemons.values()):
            daemon.update(dt)

    def update_realm_view(self, is_digital: bool):
        """Update all daemons for realm view change."""
        for daemon in self.daemons.values():
            daemon.get_appearance(is_digital)

    def get_nearby_friendly(
        self,
        pos: Tuple[int, int],
        radius: float = 100.0
    ) -> List[Daemon]:
        """Get friendly daemons near a position."""
        return [d for d in self.get_daemons_at(pos, radius) if d.is_friendly]

    def get_nearby_corrupted(
        self,
        pos: Tuple[int, int],
        radius: float = 150.0
    ) -> List[Daemon]:
        """Get corrupted daemons near a position (for healing quests)."""
        return [d for d in self.get_daemons_at(pos, radius) if d.is_corrupted]

    # =========================================================================
    # PERSISTENCE
    # =========================================================================

    def save_state(self) -> Dict[str, Any]:
        """Save all daemon states."""
        return {
            'daemons': [d.to_dict() for d in self.daemons.values()],
            'companions': self.player_companions,
            'next_id': self._next_id,
        }

    def load_state(self, data: Dict[str, Any]):
        """Load daemon states from save data."""
        # Clear existing
        for daemon_id in list(self.daemons.keys()):
            self.despawn_daemon(daemon_id)

        # Load daemons
        groups = [self.level.all_sprites] if hasattr(self.level, 'all_sprites') else []
        if hasattr(self.level, 'daemon_sprites'):
            groups.append(self.level.daemon_sprites)

        for daemon_data in data.get('daemons', []):
            try:
                daemon = Daemon.from_dict(daemon_data, groups)
                self.daemons[daemon.daemon_id] = daemon
            except Exception as e:
                print(f"Failed to load daemon: {e}")

        self.player_companions = data.get('companions', [])
        self._next_id = data.get('next_id', 0)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_species(species_id: str) -> Optional[DaemonSpecies]:
    """Get a daemon species by ID."""
    return DAEMON_SPECIES.get(species_id)


def get_all_species() -> Dict[str, DaemonSpecies]:
    """Get all registered daemon species."""
    return DAEMON_SPECIES.copy()


def get_species_by_category(category: DaemonCategory) -> List[DaemonSpecies]:
    """Get all species of a given category."""
    return [s for s in DAEMON_SPECIES.values() if s.category == category]


def get_species_names(is_digital: bool = False) -> Dict[str, str]:
    """Get a mapping of species_id to display name."""
    return {
        sid: species.get_name(is_digital)
        for sid, species in DAEMON_SPECIES.items()
    }


def get_healing_guide(species_id: str) -> Optional[str]:
    """Get the healing method for a corrupted species."""
    species = DAEMON_SPECIES.get(species_id)
    if species and species.healing_method:
        return species.healing_method
    return None


def get_true_form(corrupted_species_id: str) -> Optional[str]:
    """Get the true form species ID for a corrupted daemon."""
    species = DAEMON_SPECIES.get(corrupted_species_id)
    if species:
        return species.true_form_id
    return None
