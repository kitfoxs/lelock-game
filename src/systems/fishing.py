"""
Lelock Fishing System
L.E.L.O.C.K. - Life Emulation & Lucid Observation for Care & Keeping

A relaxing, cozy fishing experience at Crystal Lake and beyond.
This is meditation, not competition. No stress, just vibes.

"Cast your line, watch the ripples, feel the peace."
- Dad's First Fishing Lesson
"""

import pygame
import random
import math
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime
import pytz


# =============================================================================
# ENUMS & DATA STRUCTURES
# =============================================================================

class FishRarity(Enum):
    """Fish rarity tiers - affects spawn rates and catch difficulty."""
    COMMON = auto()      # 50% of catches
    UNCOMMON = auto()    # 30% of catches
    RARE = auto()        # 15% of catches
    LEGENDARY = auto()   # 4% of catches
    MYTHIC = auto()      # 1% of catches (Server Shark, Quantum Quinnat)


class FishingLocation(Enum):
    """Where you can fish in Lelock."""
    CRYSTAL_LAKE_SHALLOWS = auto()
    CRYSTAL_LAKE_DEEP = auto()
    RIVER = auto()
    HOT_SPRINGS = auto()
    SECLUDED_POOL = auto()
    OCEAN_EDGE = auto()


class Weather(Enum):
    """Weather conditions that affect fishing."""
    CLEAR = auto()
    CLOUDY = auto()
    RAIN = auto()
    STORM = auto()
    FOG = auto()
    SNOW = auto()


class TimeOfDay(Enum):
    """Time periods that affect fish availability."""
    DAWN = auto()       # 5-7 AM
    MORNING = auto()    # 7-12 PM
    NOON = auto()       # 12-1 PM (special window)
    AFTERNOON = auto()  # 1-5 PM
    EVENING = auto()    # 5-8 PM
    NIGHT = auto()      # 8 PM - 12 AM
    MIDNIGHT = auto()   # 12:00:00 AM exactly (Binary Barracuda window)
    LATE_NIGHT = auto() # 12-5 AM


class MoonPhase(Enum):
    """Moon phases - affects rare fish spawns."""
    NEW_MOON = auto()
    WAXING = auto()
    FULL_MOON = auto()  # Glimmerfin time!
    WANING = auto()


class FishingState(Enum):
    """Current state of the fishing minigame."""
    IDLE = auto()           # Not fishing
    CASTING = auto()        # Casting animation
    WAITING = auto()        # Bobber in water, waiting for bite
    FISH_APPROACHING = auto()  # Fish shadow visible, building anticipation
    BITE = auto()           # Fish is biting! Time to hook
    REELING = auto()        # Reeling in the catch
    CAUGHT = auto()         # Success! Show the fish
    ESCAPED = auto()        # Fish got away (very rare, very forgiving)


@dataclass
class Fish:
    """A fish species in Lelock."""
    name: str
    rarity: FishRarity
    description: str

    # Where and when to find it
    locations: List[FishingLocation]
    best_time: List[TimeOfDay]

    # Optional special conditions
    requires_full_moon: bool = False
    requires_midnight: bool = False
    weather_bonus: Optional[Weather] = None
    season_bonus: Optional[str] = None  # "spring", "summer", "fall", "winter"

    # Appearance
    base_color: Tuple[int, int, int] = (100, 150, 200)
    glow_color: Optional[Tuple[int, int, int]] = None
    size_range: Tuple[int, int] = (20, 40)  # min/max pixel size

    # Value and uses
    sell_price: int = 10
    energy_restore: int = 5
    special_effect: Optional[str] = None

    # Lore snippet shown on catch
    lore_snippet: str = ""

    # Special behaviors
    can_duplicate: bool = False  # Glitch-Carp!
    contains_treasure: bool = False  # Trojan Trout!
    is_deceptive: bool = False  # Phish!


@dataclass
class FishingRod:
    """A fishing rod with varying qualities."""
    name: str
    description: str

    # Stats
    cast_distance: int = 100  # How far the bobber goes
    bite_rate_bonus: float = 0.0  # Multiplier for bite chance
    catch_bonus: float = 0.0  # Easier timing window
    rare_bonus: float = 0.0  # Better chance at rare fish

    # Visual
    color: Tuple[int, int, int] = (139, 90, 43)  # Brown default
    glow: bool = False

    # Unlock requirements
    unlocked: bool = False
    unlock_description: str = ""


@dataclass
class Bait:
    """Bait that affects what you catch."""
    name: str
    description: str

    # Effects
    bite_rate_bonus: float = 0.1
    target_rarity: Optional[FishRarity] = None  # Attract specific rarity
    target_fish: Optional[str] = None  # Attract specific fish

    # Cost and availability
    price: int = 5
    quantity: int = 0


@dataclass
class FishingSession:
    """Tracks the current fishing session state."""
    state: FishingState = FishingState.IDLE

    # Current catch attempt
    current_fish: Optional[Fish] = None
    bite_timer: float = 0.0
    hook_window: float = 2.0  # Very forgiving - 2 seconds to react
    reeling_progress: float = 0.0

    # Animation state
    bobber_pos: pygame.Vector2 = field(default_factory=lambda: pygame.Vector2(0, 0))
    bobber_velocity: pygame.Vector2 = field(default_factory=lambda: pygame.Vector2(0, 0))
    cast_power: float = 0.0
    ripple_timer: float = 0.0
    fish_shadow_visible: bool = False

    # Celebration state
    catch_celebration_timer: float = 0.0
    particles: List[Dict[str, Any]] = field(default_factory=list)

    # Session stats
    fish_caught: int = 0
    biggest_catch: Optional[Fish] = None
    rarest_catch: Optional[Fish] = None

    # Dad bonding
    fishing_with_dad: bool = False
    dad_tip_timer: float = 0.0


# =============================================================================
# FISH DATABASE - All 18+ Species from Crystal Lake & Beyond
# =============================================================================

FISH_DATABASE: Dict[str, Fish] = {
    # -------------------------------------------------------------------------
    # COMMON FISH
    # -------------------------------------------------------------------------
    "data_bass": Fish(
        name="Data-Bass",
        rarity=FishRarity.COMMON,
        description="A robust, silver-scaled fish with faint grid patterns. Eyes glow soft blue.",
        locations=[FishingLocation.CRYSTAL_LAKE_SHALLOWS],
        best_time=[TimeOfDay.MORNING, TimeOfDay.DAWN],
        base_color=(180, 200, 220),
        size_range=(30, 50),
        sell_price=15,
        energy_restore=10,
        lore_snippet="Tastes like nostalgia - each person experiences their happiest memory.",
    ),

    "ping_perch": Fish(
        name="Ping Perch",
        rarity=FishRarity.COMMON,
        description="Small, quick fish that travel in synchronized schools.",
        locations=[FishingLocation.RIVER],
        best_time=[TimeOfDay.MORNING, TimeOfDay.AFTERNOON, TimeOfDay.EVENING],
        base_color=(150, 180, 160),
        size_range=(15, 25),
        sell_price=8,
        energy_restore=5,
        lore_snippet="They 'ping' each other with electrical signals. Catching one often means several.",
    ),

    "lag_fish": Fish(
        name="Lag Fish",
        rarity=FishRarity.COMMON,
        description="Moves in stuttering, jerky motions. Timeline seems delayed.",
        locations=[FishingLocation.CRYSTAL_LAKE_SHALLOWS, FishingLocation.RIVER],
        best_time=[TimeOfDay.AFTERNOON],  # "Peak hours"
        base_color=(160, 160, 180),
        size_range=(20, 35),
        sell_price=5,
        energy_restore=3,
        lore_snippet="Responds to inputs with a delay. Teaches patience to impatient anglers.",
        special_effect="patience_training",
    ),

    "codec_cod": Fish(
        name="Codec Cod",
        rarity=FishRarity.COMMON,
        description="Plump, white-fleshed fish with geometric scale patterns.",
        locations=[FishingLocation.CRYSTAL_LAKE_DEEP],
        best_time=[TimeOfDay.MORNING, TimeOfDay.EVENING],
        season_bonus="winter",
        base_color=(220, 220, 230),
        size_range=(35, 55),
        sell_price=12,
        energy_restore=12,
        lore_snippet="Simple and reliable. Makes excellent Fish and Chips.",
    ),

    # -------------------------------------------------------------------------
    # UNCOMMON FISH
    # -------------------------------------------------------------------------
    "glitch_carp": Fish(
        name="Glitch-Carp",
        rarity=FishRarity.UNCOMMON,
        description="Golden-orange carp with flickering scales. Sometimes lags behind its actual position.",
        locations=[FishingLocation.CRYSTAL_LAKE_DEEP],
        best_time=[TimeOfDay.NOON],
        base_color=(255, 180, 80),
        glow_color=(255, 200, 100),
        size_range=(40, 70),
        sell_price=25,
        energy_restore=12,
        can_duplicate=True,  # THE DOUBLE-CATCH!
        lore_snippet="The Double-Catch: sometimes duplicates at capture. Lucky or ominous?",
    ),

    "router_ray": Fish(
        name="Router Ray",
        rarity=FishRarity.UNCOMMON,
        description="Flat, diamond-shaped fish that buries in sand. Topside displays blinking lights.",
        locations=[FishingLocation.CRYSTAL_LAKE_DEEP],
        best_time=[TimeOfDay.EVENING],
        base_color=(100, 120, 140),
        glow_color=(50, 200, 50),
        size_range=(50, 80),
        sell_price=30,
        energy_restore=10,
        lore_snippet="Dried ray can be used as a compass - lights always point north.",
        special_effect="navigation_aid",
    ),

    "scroll_salmon": Fish(
        name="Scroll Salmon",
        rarity=FishRarity.UNCOMMON,
        description="Large pink-fleshed fish with scale patterns resembling ancient text.",
        locations=[FishingLocation.RIVER],
        best_time=[TimeOfDay.MORNING, TimeOfDay.DAWN],
        season_bonus="fall",
        base_color=(255, 150, 150),
        size_range=(45, 75),
        sell_price=35,
        energy_restore=20,
        lore_snippet="During the Salmon Run, patterns scroll the year's data back to the Archives.",
    ),

    "captcha_catfish": Fish(
        name="Captcha Catfish",
        rarity=FishRarity.UNCOMMON,
        description="Large whiskered fish with distorted, wavy patterns. Hard to identify at first.",
        locations=[FishingLocation.CRYSTAL_LAKE_DEEP, FishingLocation.RIVER],
        best_time=[TimeOfDay.AFTERNOON],
        weather_bonus=Weather.CLOUDY,
        base_color=(120, 100, 80),
        size_range=(55, 90),
        sell_price=28,
        energy_restore=15,
        lore_snippet="Catching one proves you're a genuine fisher, not a Bot.",
    ),

    "ethernet_eel": Fish(
        name="Ethernet Eel",
        rarity=FishRarity.UNCOMMON,
        description="Long serpentine fish resembling a braided cable. Mildly therapeutic electric charge.",
        locations=[FishingLocation.CRYSTAL_LAKE_DEEP],
        best_time=[TimeOfDay.NIGHT, TimeOfDay.LATE_NIGHT],
        base_color=(60, 80, 120),
        glow_color=(100, 150, 255),
        size_range=(80, 150),
        sell_price=40,
        energy_restore=10,
        lore_snippet="The mild shock is therapeutic for sore muscles.",
        special_effect="shock_therapy",
    ),

    "protocol_pike": Fish(
        name="Protocol Pike",
        rarity=FishRarity.UNCOMMON,
        description="Long, streamlined fish built for speed. Scales form arrow patterns.",
        locations=[FishingLocation.RIVER],
        best_time=[TimeOfDay.MORNING],
        base_color=(80, 120, 80),
        size_range=(60, 100),
        sell_price=32,
        energy_restore=15,
        lore_snippet="Key ingredient in Speed Potions. Grants +10 Movement Speed.",
        special_effect="speed_boost",
    ),

    # -------------------------------------------------------------------------
    # RARE FISH
    # -------------------------------------------------------------------------
    "glimmerfin": Fish(
        name="Glimmerfin",
        rarity=FishRarity.RARE,
        description="Ethereal, slender fish with scales that genuinely glow with internal light.",
        locations=[FishingLocation.CRYSTAL_LAKE_DEEP],
        best_time=[TimeOfDay.NIGHT],
        requires_full_moon=True,
        base_color=(200, 220, 255),
        glow_color=(150, 200, 255),
        size_range=(30, 50),
        sell_price=100,
        energy_restore=15,
        lore_snippet="Only rises during full moon, creating the famous 'Lake Light' phenomenon.",
        special_effect="player_glow",
    ),

    "firewall_fish": Fish(
        name="Firewall Fish",
        rarity=FishRarity.RARE,
        description="Red-orange fish covered in protective scales. Warm to the touch.",
        locations=[FishingLocation.HOT_SPRINGS],
        best_time=[TimeOfDay.AFTERNOON, TimeOfDay.EVENING],
        base_color=(255, 100, 50),
        glow_color=(255, 150, 50),
        size_range=(35, 55),
        sell_price=80,
        energy_restore=15,
        lore_snippet="Can survive temperatures that would cook other fish. +15 Fire Resistance.",
        special_effect="fire_resistance",
    ),

    "trojan_trout": Fish(
        name="Trojan Trout",
        rarity=FishRarity.RARE,
        description="Normal-looking trout that occasionally reveals tiny treasures inside.",
        locations=[FishingLocation.SECLUDED_POOL],
        best_time=[TimeOfDay.DAWN, TimeOfDay.EVENING],
        base_color=(120, 100, 80),
        size_range=(35, 50),
        sell_price=45,
        energy_restore=8,
        contains_treasure=True,  # SURPRISE!
        lore_snippet="Swallows shiny objects. Prized not for meat but for what's inside.",
    ),

    "phish": Fish(
        name="Phish",
        rarity=FishRarity.RARE,  # Rare because it's tricky
        description="Looks exactly like what you hoped to catch - too perfectly.",
        locations=[FishingLocation.CRYSTAL_LAKE_SHALLOWS, FishingLocation.RIVER],
        best_time=[TimeOfDay.MORNING, TimeOfDay.AFTERNOON],
        is_deceptive=True,
        base_color=(200, 180, 160),
        glow_color=(255, 215, 0),  # Too shiny!
        size_range=(40, 60),
        sell_price=5,  # Disappointing!
        energy_restore=2,
        lore_snippet="The universe's reminder that patience is required. Too good to be true.",
    ),

    # -------------------------------------------------------------------------
    # LEGENDARY FISH
    # -------------------------------------------------------------------------
    "binary_barracuda": Fish(
        name="Binary Barracuda",
        rarity=FishRarity.LEGENDARY,
        description="Massive sleek predator with light/dark alternating scales. Eyes display binary code.",
        locations=[FishingLocation.CRYSTAL_LAKE_DEEP],
        best_time=[TimeOfDay.MIDNIGHT],
        requires_midnight=True,  # EXACTLY 12:00:00 AM!
        base_color=(40, 40, 60),
        glow_color=(0, 255, 0),
        size_range=(100, 180),
        sell_price=500,  # Trophy only
        energy_restore=50,
        lore_snippet="Only bites at exactly 12:00:00 AM. Not a second before or after.",
        special_effect="all_stats_boost",
    ),

    "quantum_quinnat": Fish(
        name="Quantum Quinnat",
        rarity=FishRarity.LEGENDARY,
        description="Silvery fish that flickers between visibility. Looking at it causes it to shift.",
        locations=[FishingLocation.CRYSTAL_LAKE_DEEP, FishingLocation.RIVER, FishingLocation.SECLUDED_POOL],
        best_time=[TimeOfDay.DAWN, TimeOfDay.EVENING, TimeOfDay.NIGHT],
        base_color=(200, 200, 220),
        glow_color=(255, 255, 255),
        size_range=(50, 80),
        sell_price=400,
        energy_restore=30,
        lore_snippet="Exists in probability until caught. Some catch it only to have it vanish.",
        special_effect="quantum_existence",
    ),

    # -------------------------------------------------------------------------
    # MYTHIC FISH (Nearly Impossible)
    # -------------------------------------------------------------------------
    "server_shark": Fish(
        name="Server Shark",
        rarity=FishRarity.MYTHIC,
        description="Massive silhouette at the edge of the map, where water meets the Great Shell.",
        locations=[FishingLocation.OCEAN_EDGE],
        best_time=[TimeOfDay.MIDNIGHT, TimeOfDay.LATE_NIGHT],
        base_color=(30, 30, 50),
        glow_color=(255, 0, 0),
        size_range=(200, 400),  # HUGE
        sell_price=0,  # Cannot be sold - too legendary
        energy_restore=0,  # Cannot be eaten - too legendary
        lore_snippet="Guardian of boundaries. No one has caught one. Some say they ARE the Firewall.",
    ),
}


# =============================================================================
# FISHING RODS
# =============================================================================

FISHING_RODS: Dict[str, FishingRod] = {
    "starter_rod": FishingRod(
        name="Stick with String",
        description="A humble beginning. Dad helped you make this.",
        cast_distance=80,
        bite_rate_bonus=0.0,
        catch_bonus=0.0,
        rare_bonus=0.0,
        unlocked=True,
        unlock_description="Starting equipment",
    ),

    "data_line": FishingRod(
        name="Data-Line",
        description="Fiber-optic cable line that glows underwater. Fish can't resist.",
        cast_distance=120,
        bite_rate_bonus=0.2,
        catch_bonus=0.1,
        rare_bonus=0.1,
        color=(100, 150, 255),
        glow=True,
        unlocked=False,
        unlock_description="Gift from DAD after first fishing trip",
    ),

    "lunar_rod": FishingRod(
        name="Lunar Line",
        description="Blessed by moonlight. Blue glow attracts night fish.",
        cast_distance=140,
        bite_rate_bonus=0.3,
        catch_bonus=0.2,
        rare_bonus=0.25,
        color=(100, 150, 255),
        glow=True,
        unlocked=False,
        unlock_description="Catch 10 fish during full moon nights",
    ),

    "master_rod": FishingRod(
        name="The Architect's Line",
        description="Legendary rod said to be forged by the First Fisher.",
        cast_distance=200,
        bite_rate_bonus=0.5,
        catch_bonus=0.3,
        rare_bonus=0.4,
        color=(255, 215, 0),
        glow=True,
        unlocked=False,
        unlock_description="Catch every fish species at least once",
    ),
}


# =============================================================================
# BAIT TYPES
# =============================================================================

BAIT_TYPES: Dict[str, Bait] = {
    "basic_worm": Bait(
        name="Silicon Worm",
        description="Standard bait. Gets the job done.",
        bite_rate_bonus=0.1,
        price=5,
    ),

    "glowing_lure": Bait(
        name="Glowing Lure",
        description="Attracts fish from deeper waters.",
        bite_rate_bonus=0.2,
        target_rarity=FishRarity.UNCOMMON,
        price=15,
    ),

    "rare_bait": Bait(
        name="Memory Melon Chunks",
        description="Fish love the taste of nostalgia.",
        bite_rate_bonus=0.3,
        target_rarity=FishRarity.RARE,
        price=50,
    ),

    "legendary_lure": Bait(
        name="Binary Bait",
        description="Pulses with ones and zeros. Legendary fish notice.",
        bite_rate_bonus=0.4,
        target_rarity=FishRarity.LEGENDARY,
        price=200,
    ),
}


# =============================================================================
# FISHING SYSTEM - THE MAIN CLASS
# =============================================================================

class FishingSystem:
    """
    The complete fishing minigame system for Lelock.

    Design Philosophy:
    - RELAXING, not challenging
    - Very forgiving timing windows
    - Fish rarely escape
    - Clear visual feedback
    - Dad can teach you (tutorial mode)

    This is meditation on a lake, not a competition.
    """

    def __init__(self, timezone: str = 'America/Chicago'):
        self.timezone = pytz.timezone(timezone)

        # Equipment
        self.current_rod: FishingRod = FISHING_RODS["starter_rod"]
        self.current_bait: Optional[Bait] = None
        self.unlocked_rods: List[str] = ["starter_rod"]

        # Session state
        self.session = FishingSession()

        # Location and conditions
        self.current_location = FishingLocation.CRYSTAL_LAKE_SHALLOWS
        self.current_weather = Weather.CLEAR
        self.moon_phase = MoonPhase.WAXING

        # Fish collection (for achievements)
        self.fish_caught_ever: Dict[str, int] = {}
        self.biggest_fish_ever: Dict[str, int] = {}  # name -> size

        # Dad's tips (tutorial system)
        self.dad_tips = [
            "Cast gently, little one. The fish feel your patience.",
            "Watch the bobber - when it dips, press Space!",
            "Don't worry if one gets away. There's always another.",
            "The best catches come when you're not trying too hard.",
            "I'm proud of you for being here with me.",
            "Some fish only come out at special times. That's okay - they'll wait.",
            "Remember: this isn't about catching fish. It's about being present.",
        ]
        self.dad_tip_index = 0

        # Sound placeholders (will be actual pygame sounds later)
        self.sounds: Dict[str, Any] = {}

        # Visual effects
        self.ripples: List[Dict[str, Any]] = []
        self.particles: List[Dict[str, Any]] = []

    # =========================================================================
    # TIME & CONDITIONS
    # =========================================================================

    def get_current_time_of_day(self) -> TimeOfDay:
        """Get the current time of day based on real time (Iowa time)."""
        now = datetime.now(self.timezone)
        hour = now.hour
        minute = now.minute
        second = now.second

        # Check for EXACT midnight (Binary Barracuda window)
        if hour == 0 and minute == 0 and second < 10:
            return TimeOfDay.MIDNIGHT

        if 5 <= hour < 7:
            return TimeOfDay.DAWN
        elif 7 <= hour < 12:
            return TimeOfDay.MORNING
        elif hour == 12:
            return TimeOfDay.NOON
        elif 13 <= hour < 17:
            return TimeOfDay.AFTERNOON
        elif 17 <= hour < 20:
            return TimeOfDay.EVENING
        elif 20 <= hour < 24:
            return TimeOfDay.NIGHT
        else:  # 0-5 AM (after midnight)
            return TimeOfDay.LATE_NIGHT

    def is_full_moon(self) -> bool:
        """Check if it's currently a full moon (for Glimmerfin)."""
        return self.moon_phase == MoonPhase.FULL_MOON

    def is_midnight(self) -> bool:
        """Check if it's exactly midnight (Binary Barracuda window)."""
        now = datetime.now(self.timezone)
        return now.hour == 0 and now.minute == 0 and now.second < 10

    # =========================================================================
    # FISH SELECTION
    # =========================================================================

    def get_available_fish(self) -> List[Fish]:
        """Get all fish available at current location/time/conditions."""
        available = []
        current_time = self.get_current_time_of_day()

        for fish_id, fish in FISH_DATABASE.items():
            # Check location
            if self.current_location not in fish.locations:
                continue

            # Check special conditions
            if fish.requires_full_moon and not self.is_full_moon():
                continue

            if fish.requires_midnight and not self.is_midnight():
                continue

            # Fish is available!
            available.append(fish)

        return available

    def select_random_fish(self) -> Optional[Fish]:
        """
        Select a random fish based on rarity and conditions.
        Very weighted toward common fish, but special conditions
        dramatically increase rare fish chances.
        """
        available = self.get_available_fish()

        if not available:
            return None

        # Calculate weights based on rarity
        weights = []
        current_time = self.get_current_time_of_day()

        for fish in available:
            # Base weight by rarity
            base_weight = {
                FishRarity.COMMON: 50,
                FishRarity.UNCOMMON: 30,
                FishRarity.RARE: 15,
                FishRarity.LEGENDARY: 4,
                FishRarity.MYTHIC: 1,
            }.get(fish.rarity, 10)

            # Bonus for optimal time
            if current_time in fish.best_time:
                base_weight *= 2.0

            # Bonus for weather
            if fish.weather_bonus == self.current_weather:
                base_weight *= 1.5

            # Rod bonuses
            if fish.rarity in [FishRarity.RARE, FishRarity.LEGENDARY, FishRarity.MYTHIC]:
                base_weight *= (1 + self.current_rod.rare_bonus)

            # Bait bonuses
            if self.current_bait:
                if self.current_bait.target_rarity == fish.rarity:
                    base_weight *= 2.0
                if self.current_bait.target_fish == fish.name:
                    base_weight *= 3.0

            weights.append(base_weight)

        # Weighted random selection
        total_weight = sum(weights)
        if total_weight <= 0:
            return random.choice(available) if available else None

        roll = random.uniform(0, total_weight)
        cumulative = 0

        for fish, weight in zip(available, weights):
            cumulative += weight
            if roll <= cumulative:
                return fish

        return available[-1] if available else None

    # =========================================================================
    # FISHING ACTIONS
    # =========================================================================

    def cast_line(self, power: float = 0.5) -> bool:
        """
        Cast the fishing line into the water.
        Power is 0.0-1.0, affects distance.

        Returns True if cast was successful.
        """
        if self.session.state != FishingState.IDLE:
            return False

        self.session.state = FishingState.CASTING
        self.session.cast_power = max(0.1, min(1.0, power))

        # Calculate bobber destination
        cast_distance = self.current_rod.cast_distance * self.session.cast_power

        # Start casting animation
        # (Actual animation handled by update loop)

        return True

    def start_waiting(self, bobber_x: float, bobber_y: float) -> None:
        """Called after cast animation completes. Begin waiting for bite."""
        self.session.state = FishingState.WAITING
        self.session.bobber_pos = pygame.Vector2(bobber_x, bobber_y)

        # Calculate time until fish approaches
        base_wait = random.uniform(3.0, 8.0)  # 3-8 seconds

        # Rod and bait bonuses reduce wait time
        wait_modifier = 1.0 - (self.current_rod.bite_rate_bonus * 0.5)
        if self.current_bait:
            wait_modifier -= self.current_bait.bite_rate_bonus * 0.3

        self.session.bite_timer = base_wait * max(0.3, wait_modifier)

        # Create initial ripple
        self._create_ripple(bobber_x, bobber_y, radius=20)

    def hook_fish(self) -> bool:
        """
        Attempt to hook a biting fish.
        Called when player presses action button during BITE state.

        Returns True if successfully hooked.
        """
        if self.session.state != FishingState.BITE:
            return False

        # VERY forgiving - almost always succeeds
        # Only fail if player is REALLY slow
        success_chance = 0.95 + (self.current_rod.catch_bonus * 0.05)

        if random.random() < success_chance:
            self.session.state = FishingState.REELING
            self.session.reeling_progress = 0.0
            return True
        else:
            # Fish escaped - but this is rare and okay!
            self.session.state = FishingState.ESCAPED
            self.session.catch_celebration_timer = 1.5  # Brief "aww" moment
            return False

    def reel_in(self, dt: float) -> Optional[Fish]:
        """
        Continue reeling in the fish.
        Called each frame during REELING state.

        Returns the caught fish when complete, None otherwise.
        """
        if self.session.state != FishingState.REELING:
            return None

        # Simple progress-based reeling (no skill required)
        # Just hold the button and watch!
        reel_speed = 0.4 + (self.current_rod.catch_bonus * 0.2)
        self.session.reeling_progress += reel_speed * dt

        if self.session.reeling_progress >= 1.0:
            # CAUGHT!
            fish = self.session.current_fish
            if fish:
                self._on_fish_caught(fish)
            return fish

        return None

    def cancel_fishing(self) -> None:
        """Cancel current fishing attempt and return to idle."""
        self.session.state = FishingState.IDLE
        self.session.current_fish = None
        self.session.bite_timer = 0
        self.session.reeling_progress = 0
        self.session.fish_shadow_visible = False

    # =========================================================================
    # INTERNAL FISHING LOGIC
    # =========================================================================

    def _on_fish_caught(self, fish: Fish) -> None:
        """Handle a successful catch."""
        self.session.state = FishingState.CAUGHT
        self.session.catch_celebration_timer = 3.0  # 3 seconds of celebration
        self.session.fish_caught += 1

        # Track in collection
        if fish.name in self.fish_caught_ever:
            self.fish_caught_ever[fish.name] += 1
        else:
            self.fish_caught_ever[fish.name] = 1

        # Handle special fish behaviors
        if fish.can_duplicate:
            # GLITCH-CARP DUPLICATION!
            if random.random() < 0.25:  # 25% chance
                self.fish_caught_ever[fish.name] += 1
                # TODO: Show "DOUBLE CATCH!" notification

        if fish.contains_treasure:
            # TROJAN TROUT TREASURE!
            self._generate_trojan_treasure()

        # Create celebration particles
        self._create_celebration_particles()

        # Dad tip time?
        if self.session.fishing_with_dad and random.random() < 0.3:
            self.session.dad_tip_timer = 2.0

    def _generate_trojan_treasure(self) -> Dict[str, Any]:
        """Generate treasure from a Trojan Trout."""
        treasures = [
            {"type": "coins", "amount": random.randint(10, 50)},
            {"type": "gem", "name": "Silicon Crystal", "value": 30},
            {"type": "item", "name": "Lost Locket", "value": 100},
            {"type": "coins", "amount": random.randint(5, 20)},
            {"type": "item", "name": "Old Key", "value": 50},
        ]
        return random.choice(treasures)

    # =========================================================================
    # UPDATE LOOP
    # =========================================================================

    def update(self, dt: float) -> Dict[str, Any]:
        """
        Main update loop for fishing system.
        Called every frame while fishing is active.

        Returns a dict with events that occurred this frame.
        """
        events = {
            "state_changed": False,
            "new_state": None,
            "fish_caught": None,
            "dad_tip": None,
            "double_catch": False,
            "treasure_found": None,
        }

        # Update based on current state
        if self.session.state == FishingState.CASTING:
            self._update_casting(dt)

        elif self.session.state == FishingState.WAITING:
            self._update_waiting(dt, events)

        elif self.session.state == FishingState.FISH_APPROACHING:
            self._update_fish_approaching(dt, events)

        elif self.session.state == FishingState.BITE:
            self._update_bite(dt, events)

        elif self.session.state == FishingState.REELING:
            pass  # Handled by reel_in() method

        elif self.session.state in [FishingState.CAUGHT, FishingState.ESCAPED]:
            self._update_celebration(dt, events)

        # Update visual effects
        self._update_ripples(dt)
        self._update_particles(dt)

        # Dad tips
        if self.session.dad_tip_timer > 0:
            self.session.dad_tip_timer -= dt
            if self.session.dad_tip_timer <= 0:
                events["dad_tip"] = self._get_dad_tip()

        return events

    def _update_casting(self, dt: float) -> None:
        """Update casting animation."""
        # Simple arc animation
        # After animation complete, transition to waiting
        pass  # Handled by animation system

    def _update_waiting(self, dt: float, events: Dict) -> None:
        """Update waiting state - countdown to fish approach."""
        self.session.bite_timer -= dt

        # Gentle bobber movement (relaxing)
        self._update_bobber_idle(dt)

        if self.session.bite_timer <= 0:
            # Fish is approaching!
            self.session.state = FishingState.FISH_APPROACHING
            self.session.current_fish = self.select_random_fish()
            self.session.fish_shadow_visible = True
            events["state_changed"] = True
            events["new_state"] = FishingState.FISH_APPROACHING

            # Time until bite
            self.session.bite_timer = random.uniform(1.5, 3.0)

    def _update_fish_approaching(self, dt: float, events: Dict) -> None:
        """Update fish approach - shadow visible, anticipation building."""
        self.session.bite_timer -= dt

        # More bobber movement
        self._update_bobber_nibble(dt)

        if self.session.bite_timer <= 0:
            # BITE!
            self.session.state = FishingState.BITE
            self.session.hook_window = 2.0  # 2 seconds to react (very forgiving!)
            events["state_changed"] = True
            events["new_state"] = FishingState.BITE

            # Visual feedback
            self._create_ripple(
                self.session.bobber_pos.x,
                self.session.bobber_pos.y,
                radius=30
            )

    def _update_bite(self, dt: float, events: Dict) -> None:
        """Update bite state - countdown to fish escape."""
        self.session.hook_window -= dt

        # Bobber going CRAZY (but still visible)
        self._update_bobber_bite(dt)

        if self.session.hook_window <= 0:
            # Fish got away - but this is VERY forgiving
            # Only happens if player completely ignores it
            self.session.state = FishingState.ESCAPED
            self.session.catch_celebration_timer = 1.5
            events["state_changed"] = True
            events["new_state"] = FishingState.ESCAPED

    def _update_celebration(self, dt: float, events: Dict) -> None:
        """Update celebration/escaped state."""
        self.session.catch_celebration_timer -= dt

        if self.session.catch_celebration_timer <= 0:
            # Return to idle
            self.session.state = FishingState.IDLE
            self.session.current_fish = None
            events["state_changed"] = True
            events["new_state"] = FishingState.IDLE

    # =========================================================================
    # BOBBER ANIMATIONS (Relaxing visual feedback)
    # =========================================================================

    def _update_bobber_idle(self, dt: float) -> None:
        """Gentle bobbing motion while waiting."""
        # Smooth sine wave
        self.session.ripple_timer += dt
        bob_y = math.sin(self.session.ripple_timer * 2) * 2
        self.session.bobber_velocity.y = bob_y

        # Occasional small ripple
        if random.random() < 0.01:  # 1% per frame
            self._create_ripple(
                self.session.bobber_pos.x,
                self.session.bobber_pos.y,
                radius=10
            )

    def _update_bobber_nibble(self, dt: float) -> None:
        """Slight nibbles as fish approaches."""
        self.session.ripple_timer += dt

        # More erratic movement
        bob_y = math.sin(self.session.ripple_timer * 4) * 3
        bob_x = math.sin(self.session.ripple_timer * 3) * 1.5
        self.session.bobber_velocity.y = bob_y
        self.session.bobber_velocity.x = bob_x

        # More frequent ripples
        if random.random() < 0.05:
            self._create_ripple(
                self.session.bobber_pos.x + random.uniform(-10, 10),
                self.session.bobber_pos.y + random.uniform(-10, 10),
                radius=15
            )

    def _update_bobber_bite(self, dt: float) -> None:
        """Bobber going under - FISH ON!"""
        self.session.ripple_timer += dt

        # Strong, obvious movement (easy to notice)
        bob_y = math.sin(self.session.ripple_timer * 8) * 8
        self.session.bobber_velocity.y = bob_y

        # Constant ripples
        if random.random() < 0.2:
            self._create_ripple(
                self.session.bobber_pos.x + random.uniform(-5, 5),
                self.session.bobber_pos.y + random.uniform(-5, 5),
                radius=25
            )

    # =========================================================================
    # VISUAL EFFECTS
    # =========================================================================

    def _create_ripple(self, x: float, y: float, radius: float = 20) -> None:
        """Create a ripple effect on the water."""
        self.ripples.append({
            "pos": pygame.Vector2(x, y),
            "radius": radius,
            "max_radius": radius * 3,
            "alpha": 255,
            "lifetime": 0,
            "max_lifetime": 1.5,
        })

    def _update_ripples(self, dt: float) -> None:
        """Update all ripple effects."""
        for ripple in self.ripples[:]:
            ripple["lifetime"] += dt
            progress = ripple["lifetime"] / ripple["max_lifetime"]

            # Expand and fade
            ripple["radius"] = ripple["max_radius"] * progress
            ripple["alpha"] = int(255 * (1 - progress))

            if ripple["lifetime"] >= ripple["max_lifetime"]:
                self.ripples.remove(ripple)

    def _create_celebration_particles(self) -> None:
        """Create celebration particles on successful catch."""
        colors = [
            (255, 215, 0),   # Gold
            (100, 200, 255), # Light blue
            (200, 255, 200), # Light green
            (255, 200, 255), # Light pink
        ]

        for _ in range(20):
            self.particles.append({
                "pos": pygame.Vector2(
                    self.session.bobber_pos.x + random.uniform(-20, 20),
                    self.session.bobber_pos.y + random.uniform(-20, 20)
                ),
                "velocity": pygame.Vector2(
                    random.uniform(-50, 50),
                    random.uniform(-100, -50)
                ),
                "color": random.choice(colors),
                "size": random.uniform(3, 8),
                "lifetime": 0,
                "max_lifetime": random.uniform(1.0, 2.0),
            })

    def _update_particles(self, dt: float) -> None:
        """Update celebration particles."""
        for particle in self.particles[:]:
            particle["lifetime"] += dt

            # Gravity
            particle["velocity"].y += 200 * dt

            # Move
            particle["pos"] += particle["velocity"] * dt

            # Fade
            particle["size"] *= 0.98

            if particle["lifetime"] >= particle["max_lifetime"]:
                self.particles.remove(particle)

    # =========================================================================
    # DAD'S TIPS (Tutorial System)
    # =========================================================================

    def _get_dad_tip(self) -> str:
        """Get the next Dad tip."""
        tip = self.dad_tips[self.dad_tip_index]
        self.dad_tip_index = (self.dad_tip_index + 1) % len(self.dad_tips)
        return tip

    def enable_dad_fishing(self, enable: bool = True) -> None:
        """Enable/disable fishing with Dad (tutorial mode)."""
        self.session.fishing_with_dad = enable
        if enable:
            self.session.dad_tip_timer = 1.0  # Initial tip soon

    # =========================================================================
    # EQUIPMENT MANAGEMENT
    # =========================================================================

    def equip_rod(self, rod_id: str) -> bool:
        """Equip a fishing rod by ID."""
        if rod_id not in FISHING_RODS:
            return False

        rod = FISHING_RODS[rod_id]
        if not rod.unlocked and rod_id not in self.unlocked_rods:
            return False

        self.current_rod = rod
        return True

    def unlock_rod(self, rod_id: str) -> bool:
        """Unlock a fishing rod."""
        if rod_id not in FISHING_RODS:
            return False

        if rod_id not in self.unlocked_rods:
            self.unlocked_rods.append(rod_id)
            FISHING_RODS[rod_id].unlocked = True
        return True

    def set_bait(self, bait_id: Optional[str]) -> bool:
        """Set current bait (or None for no bait)."""
        if bait_id is None:
            self.current_bait = None
            return True

        if bait_id not in BAIT_TYPES:
            return False

        self.current_bait = BAIT_TYPES[bait_id]
        return True

    def set_location(self, location: FishingLocation) -> None:
        """Set current fishing location."""
        self.current_location = location

    def set_weather(self, weather: Weather) -> None:
        """Set current weather conditions."""
        self.current_weather = weather

    def set_moon_phase(self, phase: MoonPhase) -> None:
        """Set current moon phase."""
        self.moon_phase = phase

    # =========================================================================
    # RENDERING (Called by game renderer)
    # =========================================================================

    def render(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        """
        Render fishing visuals.

        Args:
            surface: The pygame surface to render to
            camera_offset: Camera position offset for world coordinates
        """
        # Render ripples
        for ripple in self.ripples:
            pos = ripple["pos"] - camera_offset
            pygame.draw.circle(
                surface,
                (100, 150, 255, ripple["alpha"]),
                (int(pos.x), int(pos.y)),
                int(ripple["radius"]),
                2  # Ring only
            )

        # Render fish shadow (if approaching)
        if self.session.fish_shadow_visible and self.session.current_fish:
            self._render_fish_shadow(surface, camera_offset)

        # Render bobber
        if self.session.state in [
            FishingState.WAITING,
            FishingState.FISH_APPROACHING,
            FishingState.BITE,
            FishingState.REELING
        ]:
            self._render_bobber(surface, camera_offset)

        # Render particles
        for particle in self.particles:
            pos = particle["pos"] - camera_offset
            pygame.draw.circle(
                surface,
                particle["color"],
                (int(pos.x), int(pos.y)),
                int(particle["size"])
            )

        # Render caught fish display
        if self.session.state == FishingState.CAUGHT:
            self._render_caught_fish(surface, camera_offset)

    def _render_bobber(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        """Render the fishing bobber."""
        pos = self.session.bobber_pos - camera_offset + self.session.bobber_velocity

        # Red and white classic bobber
        pygame.draw.circle(surface, (255, 50, 50), (int(pos.x), int(pos.y)), 8)
        pygame.draw.circle(surface, (255, 255, 255), (int(pos.x), int(pos.y - 4)), 5)

        # Glow effect if rod has glow
        if self.current_rod.glow:
            glow_surf = pygame.Surface((40, 40), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*self.current_rod.color, 50), (20, 20), 15)
            surface.blit(glow_surf, (int(pos.x - 20), int(pos.y - 20)))

    def _render_fish_shadow(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        """Render fish shadow under water."""
        if not self.session.current_fish:
            return

        fish = self.session.current_fish
        pos = self.session.bobber_pos - camera_offset

        # Shadow offset (circling the bobber)
        shadow_offset = pygame.Vector2(
            math.sin(self.session.ripple_timer * 2) * 30,
            math.cos(self.session.ripple_timer * 2) * 15
        )

        shadow_pos = pos + shadow_offset + pygame.Vector2(0, 20)

        # Draw elliptical shadow
        size = random.randint(fish.size_range[0], fish.size_range[1])
        pygame.draw.ellipse(
            surface,
            (30, 50, 80, 100),  # Dark blue shadow
            (int(shadow_pos.x - size/2), int(shadow_pos.y - size/4), size, size//2)
        )

    def _render_caught_fish(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        """Render the caught fish celebration display."""
        if not self.session.current_fish:
            return

        fish = self.session.current_fish

        # Center of screen display
        center_x = surface.get_width() // 2
        center_y = surface.get_height() // 2

        # Fish display box
        box_rect = pygame.Rect(center_x - 150, center_y - 100, 300, 200)
        pygame.draw.rect(surface, (30, 30, 50), box_rect, border_radius=15)
        pygame.draw.rect(surface, (100, 150, 255), box_rect, 3, border_radius=15)

        # Fish silhouette (placeholder - will be actual sprite)
        size = random.randint(fish.size_range[0], fish.size_range[1])
        fish_rect = pygame.Rect(center_x - size//2, center_y - 60, size, size//2)
        pygame.draw.ellipse(surface, fish.base_color, fish_rect)

        # Glow effect for glowing fish
        if fish.glow_color:
            glow_rect = fish_rect.inflate(10, 10)
            pygame.draw.ellipse(surface, (*fish.glow_color, 50), glow_rect)

        # Text would go here (fish name, rarity, lore snippet)
        # Will be handled by UI system

    # =========================================================================
    # SAVE/LOAD
    # =========================================================================

    def get_save_data(self) -> Dict[str, Any]:
        """Get data to save to disk."""
        return {
            "unlocked_rods": self.unlocked_rods,
            "fish_caught_ever": self.fish_caught_ever,
            "biggest_fish_ever": self.biggest_fish_ever,
            "current_rod_id": next(
                (k for k, v in FISHING_RODS.items() if v == self.current_rod),
                "starter_rod"
            ),
        }

    def load_save_data(self, data: Dict[str, Any]) -> None:
        """Load data from disk."""
        self.unlocked_rods = data.get("unlocked_rods", ["starter_rod"])
        self.fish_caught_ever = data.get("fish_caught_ever", {})
        self.biggest_fish_ever = data.get("biggest_fish_ever", {})

        # Restore unlocked status
        for rod_id in self.unlocked_rods:
            if rod_id in FISHING_RODS:
                FISHING_RODS[rod_id].unlocked = True

        # Equip saved rod
        rod_id = data.get("current_rod_id", "starter_rod")
        self.equip_rod(rod_id)


# =============================================================================
# FISHING UI COMPONENT
# =============================================================================

class FishingUI:
    """
    UI overlay for fishing minigame.

    Displays:
    - Current state (casting, waiting, bite, etc.)
    - Progress bars (reeling)
    - Fish info on catch
    - Dad tips
    - Equipment info
    """

    def __init__(self, fishing_system: FishingSystem):
        self.fishing = fishing_system
        self.font_large: Optional[pygame.font.Font] = None
        self.font_medium: Optional[pygame.font.Font] = None
        self.font_small: Optional[pygame.font.Font] = None

        # Animation state
        self.bite_flash_timer = 0
        self.catch_celebration_scale = 1.0

    def init_fonts(self) -> None:
        """Initialize fonts (call after pygame.init)."""
        try:
            self.font_large = pygame.font.Font(None, 48)
            self.font_medium = pygame.font.Font(None, 32)
            self.font_small = pygame.font.Font(None, 24)
        except:
            pass

    def update(self, dt: float) -> None:
        """Update UI animations."""
        # Bite flash
        if self.fishing.session.state == FishingState.BITE:
            self.bite_flash_timer += dt * 8
        else:
            self.bite_flash_timer = 0

        # Catch celebration
        if self.fishing.session.state == FishingState.CAUGHT:
            self.catch_celebration_scale = 1.0 + math.sin(self.bite_flash_timer) * 0.1

    def render(self, surface: pygame.Surface) -> None:
        """Render fishing UI overlay."""
        state = self.fishing.session.state

        if state == FishingState.IDLE:
            self._render_idle_ui(surface)

        elif state == FishingState.WAITING:
            self._render_waiting_ui(surface)

        elif state == FishingState.FISH_APPROACHING:
            self._render_approaching_ui(surface)

        elif state == FishingState.BITE:
            self._render_bite_ui(surface)

        elif state == FishingState.REELING:
            self._render_reeling_ui(surface)

        elif state == FishingState.CAUGHT:
            self._render_caught_ui(surface)

        elif state == FishingState.ESCAPED:
            self._render_escaped_ui(surface)

        # Dad tips overlay
        if self.fishing.session.fishing_with_dad:
            self._render_dad_tip(surface)

    def _render_idle_ui(self, surface: pygame.Surface) -> None:
        """Render UI when not fishing."""
        if not self.font_small:
            return

        text = self.font_small.render(
            f"Press SPACE to cast ({self.fishing.current_rod.name})",
            True, (255, 255, 255)
        )
        pos = (surface.get_width() // 2 - text.get_width() // 2,
               surface.get_height() - 50)
        surface.blit(text, pos)

    def _render_waiting_ui(self, surface: pygame.Surface) -> None:
        """Render UI while waiting for bite."""
        if not self.font_small:
            return

        text = self.font_small.render(
            "Waiting... (watch the bobber)",
            True, (200, 220, 255)
        )
        pos = (surface.get_width() // 2 - text.get_width() // 2,
               surface.get_height() - 50)
        surface.blit(text, pos)

    def _render_approaching_ui(self, surface: pygame.Surface) -> None:
        """Render UI when fish is approaching."""
        if not self.font_medium:
            return

        text = self.font_medium.render(
            "Something's nibbling...",
            True, (255, 255, 200)
        )
        pos = (surface.get_width() // 2 - text.get_width() // 2,
               surface.get_height() - 60)
        surface.blit(text, pos)

    def _render_bite_ui(self, surface: pygame.Surface) -> None:
        """Render UI during bite - VERY OBVIOUS!"""
        if not self.font_large:
            return

        # Flashing "FISH ON!" text
        flash_alpha = int(abs(math.sin(self.bite_flash_timer)) * 255)

        text = self.font_large.render("FISH ON! Press SPACE!", True, (255, 255, 100))

        # Pulsing effect
        scale = 1.0 + math.sin(self.bite_flash_timer * 2) * 0.1
        scaled_text = pygame.transform.scale(
            text,
            (int(text.get_width() * scale), int(text.get_height() * scale))
        )

        pos = (surface.get_width() // 2 - scaled_text.get_width() // 2,
               surface.get_height() // 2 - 100)
        surface.blit(scaled_text, pos)

        # Timer bar (how much time left)
        bar_width = 200
        bar_height = 20
        bar_x = surface.get_width() // 2 - bar_width // 2
        bar_y = surface.get_height() // 2 - 50

        progress = self.fishing.session.hook_window / 2.0  # 2.0 is max window

        pygame.draw.rect(surface, (50, 50, 70), (bar_x, bar_y, bar_width, bar_height), border_radius=5)
        pygame.draw.rect(surface, (100, 255, 100),
                        (bar_x, bar_y, int(bar_width * progress), bar_height), border_radius=5)

    def _render_reeling_ui(self, surface: pygame.Surface) -> None:
        """Render UI while reeling in."""
        if not self.font_medium:
            return

        # Progress bar
        bar_width = 300
        bar_height = 25
        bar_x = surface.get_width() // 2 - bar_width // 2
        bar_y = surface.get_height() - 80

        progress = self.fishing.session.reeling_progress

        pygame.draw.rect(surface, (50, 50, 70), (bar_x, bar_y, bar_width, bar_height), border_radius=8)
        pygame.draw.rect(surface, (100, 200, 255),
                        (bar_x, bar_y, int(bar_width * progress), bar_height), border_radius=8)

        text = self.font_medium.render("Reeling in...", True, (200, 230, 255))
        pos = (surface.get_width() // 2 - text.get_width() // 2, bar_y - 35)
        surface.blit(text, pos)

    def _render_caught_ui(self, surface: pygame.Surface) -> None:
        """Render celebration UI on catch."""
        fish = self.fishing.session.current_fish
        if not fish or not self.font_large or not self.font_medium or not self.font_small:
            return

        center_x = surface.get_width() // 2
        center_y = surface.get_height() // 2

        # Background panel
        panel = pygame.Surface((400, 300), pygame.SRCALPHA)
        pygame.draw.rect(panel, (30, 30, 50, 230), (0, 0, 400, 300), border_radius=20)
        pygame.draw.rect(panel, (100, 150, 255), (0, 0, 400, 300), 4, border_radius=20)

        # Scale animation
        scaled_panel = pygame.transform.scale(
            panel,
            (int(400 * self.catch_celebration_scale),
             int(300 * self.catch_celebration_scale))
        )
        panel_pos = (center_x - scaled_panel.get_width() // 2,
                    center_y - scaled_panel.get_height() // 2)
        surface.blit(scaled_panel, panel_pos)

        # Fish name
        rarity_colors = {
            FishRarity.COMMON: (200, 200, 200),
            FishRarity.UNCOMMON: (100, 255, 100),
            FishRarity.RARE: (100, 150, 255),
            FishRarity.LEGENDARY: (255, 200, 50),
            FishRarity.MYTHIC: (255, 100, 255),
        }

        name_text = self.font_large.render(fish.name, True, rarity_colors.get(fish.rarity, (255, 255, 255)))
        surface.blit(name_text, (center_x - name_text.get_width() // 2, center_y - 80))

        # Rarity
        rarity_text = self.font_medium.render(fish.rarity.name, True, rarity_colors.get(fish.rarity, (255, 255, 255)))
        surface.blit(rarity_text, (center_x - rarity_text.get_width() // 2, center_y - 40))

        # Lore snippet
        if fish.lore_snippet:
            # Word wrap the lore snippet
            words = fish.lore_snippet.split()
            lines = []
            current_line = []

            for word in words:
                current_line.append(word)
                test_line = ' '.join(current_line)
                if self.font_small.size(test_line)[0] > 350:
                    current_line.pop()
                    lines.append(' '.join(current_line))
                    current_line = [word]
            if current_line:
                lines.append(' '.join(current_line))

            y_offset = center_y + 20
            for line in lines[:3]:  # Max 3 lines
                line_text = self.font_small.render(line, True, (200, 200, 220))
                surface.blit(line_text, (center_x - line_text.get_width() // 2, y_offset))
                y_offset += 25

    def _render_escaped_ui(self, surface: pygame.Surface) -> None:
        """Render UI when fish escapes (rare, gentle)."""
        if not self.font_medium:
            return

        text = self.font_medium.render("It got away... but that's okay!", True, (200, 200, 220))
        pos = (surface.get_width() // 2 - text.get_width() // 2,
               surface.get_height() // 2)
        surface.blit(text, pos)

        subtext = self.font_small.render("There's always another fish in the lake.", True, (150, 150, 170))
        sub_pos = (surface.get_width() // 2 - subtext.get_width() // 2,
                  surface.get_height() // 2 + 40)
        surface.blit(subtext, sub_pos)

    def _render_dad_tip(self, surface: pygame.Surface) -> None:
        """Render Dad's wisdom overlay."""
        if not self.font_medium or self.fishing.session.dad_tip_timer <= 0:
            return

        # Get current tip
        tip = self.fishing.dad_tips[self.fishing.dad_tip_index]

        # Speech bubble at top of screen
        bubble_width = min(500, len(tip) * 12 + 40)
        bubble_height = 80
        bubble_x = surface.get_width() // 2 - bubble_width // 2
        bubble_y = 20

        # Fade based on timer
        alpha = min(255, int(self.fishing.session.dad_tip_timer * 255))

        bubble = pygame.Surface((bubble_width, bubble_height), pygame.SRCALPHA)
        pygame.draw.rect(bubble, (60, 50, 40, alpha), (0, 0, bubble_width, bubble_height), border_radius=15)
        pygame.draw.rect(bubble, (139, 90, 43, alpha), (0, 0, bubble_width, bubble_height), 3, border_radius=15)
        surface.blit(bubble, (bubble_x, bubble_y))

        # "Dad:" label
        dad_label = self.font_small.render("Dad:", True, (200, 180, 150))
        surface.blit(dad_label, (bubble_x + 15, bubble_y + 10))

        # Tip text
        tip_text = self.font_small.render(tip, True, (255, 250, 240))
        surface.blit(tip_text, (bubble_x + 15, bubble_y + 35))


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_fishing_system(timezone: str = 'America/Chicago') -> Tuple[FishingSystem, FishingUI]:
    """
    Create a complete fishing system with UI.

    Returns:
        Tuple of (FishingSystem, FishingUI)
    """
    system = FishingSystem(timezone=timezone)
    ui = FishingUI(system)
    return system, ui


def get_fish_by_name(name: str) -> Optional[Fish]:
    """Get a fish by its name (case-insensitive)."""
    name_lower = name.lower().replace(" ", "_").replace("-", "_")

    for fish_id, fish in FISH_DATABASE.items():
        if fish_id == name_lower or fish.name.lower() == name.lower():
            return fish

    return None


def get_all_fish_names() -> List[str]:
    """Get a list of all fish names."""
    return [fish.name for fish in FISH_DATABASE.values()]


def get_fish_by_rarity(rarity: FishRarity) -> List[Fish]:
    """Get all fish of a specific rarity."""
    return [fish for fish in FISH_DATABASE.values() if fish.rarity == rarity]


def get_fish_by_location(location: FishingLocation) -> List[Fish]:
    """Get all fish available at a specific location."""
    return [fish for fish in FISH_DATABASE.values() if location in fish.locations]
