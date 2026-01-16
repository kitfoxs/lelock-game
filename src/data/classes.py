"""
Lelock Character Class System
L.E.L.O.C.K. - Life Emulation & Lucid Observation for Care & Keeping

10 Character Classes with Dual Names (Fantasy/Tech)
Every class is valid. Every class is fun. No power gaming - just different playstyles.

Design Philosophy:
- Classes are ROLES, not power levels
- Every class enhances a specific playstyle
- No class gates content - all can do everything, some just excel
- Players can switch classes with effort
- Multi-classing planned for future
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from enum import Enum


# =============================================================================
# CORE STAT TYPES
# =============================================================================

class PrimaryStat(Enum):
    """The six primary stats a class can excel at."""
    STRENGTH = "strength"       # Physical power, building, mining
    DEXTERITY = "dexterity"    # Crafting precision, speed
    INTELLIGENCE = "intelligence"  # Magic power, terminal access
    WISDOM = "wisdom"           # Healing, perception, spiritual
    CHARISMA = "charisma"       # Social, daemon bonding, music
    LUCK = "luck"               # Finding rare items, random events
    DEFENSE = "defense"         # Damage reduction, protection
    NATURE = "nature"           # Farming, growth, weather


# =============================================================================
# CLASS ABILITY
# =============================================================================

@dataclass
class ClassAbility:
    """
    An ability granted by a character class.

    Abilities unlock at specific levels and provide unique gameplay options.
    Mana costs are kept low - we don't want resource stress.
    """
    name: str
    fantasy_name: str  # Name shown in Physical realm
    tech_name: str     # Name shown in Digital realm
    description: str
    mana_cost: int
    cooldown: float    # Seconds between uses
    level_required: int
    effect_type: str   # 'buff', 'heal', 'damage', 'utility', 'summon', 'passive'
    effect_value: float  # Numerical value of the effect

    # Optional scaling
    scales_with: Optional[str] = None  # Which stat affects power
    scaling_factor: float = 0.1  # How much stat affects result

    # Visual/audio
    animation: str = "default"
    sound_effect: str = "ability_activate"
    particle_color: str = "#ffffff"

    def get_display_name(self, realm: str = "physical") -> str:
        """Return name appropriate for current realm."""
        return self.fantasy_name if realm == "physical" else self.tech_name

    def calculate_effect(self, base_stat: int = 0) -> float:
        """Calculate actual effect value with stat scaling."""
        if self.scales_with and base_stat > 0:
            return self.effect_value + (base_stat * self.scaling_factor)
        return self.effect_value


# =============================================================================
# CHARACTER CLASS
# =============================================================================

@dataclass
class CharacterClass:
    """
    A character class with unique abilities and bonuses.

    Classes provide identity and specialization without gatekeeping.
    Every player can do everything - classes just make some things easier.
    """
    id: str
    fantasy_name: str
    tech_name: str
    description: str
    lore_description: str  # Longer flavor text
    primary_stat: PrimaryStat

    # Abilities (unlock over time)
    abilities: List[ClassAbility] = field(default_factory=list)

    # Passive bonuses (always active)
    passive_bonuses: Dict[str, float] = field(default_factory=dict)

    # Starting gear
    starting_items: List[str] = field(default_factory=list)
    starting_tools: List[str] = field(default_factory=list)

    # Unlock requirements (None = available at start)
    unlock_condition: Optional[str] = None
    unlock_description: Optional[str] = None

    # Visual identity
    color_primary: str = "#ffffff"
    color_secondary: str = "#888888"
    icon: str = "class_default"

    # Stat bonuses per level (applied when leveling up)
    level_stat_bonus: Dict[str, float] = field(default_factory=dict)

    def get_display_name(self, realm: str = "physical") -> str:
        """Return name appropriate for current realm."""
        return self.fantasy_name if realm == "physical" else self.tech_name

    def get_abilities_at_level(self, level: int) -> List[ClassAbility]:
        """Get all abilities unlocked at or before the given level."""
        return [a for a in self.abilities if a.level_required <= level]

    def get_passive_value(self, bonus_key: str, level: int = 1) -> float:
        """Get passive bonus value, scaled by level."""
        base = self.passive_bonuses.get(bonus_key, 0.0)
        # Passives scale slightly with level (5% per level after 1)
        return base * (1 + (level - 1) * 0.05)


# =============================================================================
# CLASS SYSTEM MANAGER
# =============================================================================

class ClassSystem:
    """
    Manages player class progression and switching.

    Key Features:
    - Track progress in multiple classes
    - Switching classes preserves progress
    - Multi-classing support (future)
    - Prestige system at level 20
    """

    MAX_LEVEL = 20
    XP_PER_LEVEL = [
        0,     # Level 1 (starting)
        100,   # Level 2
        250,   # Level 3
        450,   # Level 4
        700,   # Level 5
        1000,  # Level 6
        1400,  # Level 7
        1900,  # Level 8
        2500,  # Level 9
        3200,  # Level 10
        4000,  # Level 11
        4900,  # Level 12
        5900,  # Level 13
        7000,  # Level 14
        8200,  # Level 15
        9500,  # Level 16
        11000, # Level 17
        12700, # Level 18
        14600, # Level 19
        16700, # Level 20
    ]

    def __init__(self):
        self.classes: Dict[str, CharacterClass] = {}
        self.current_class: Optional[CharacterClass] = None
        self.class_levels: Dict[str, int] = {}
        self.class_xp: Dict[str, int] = {}
        self.prestige_levels: Dict[str, int] = {}
        self.unlocked_classes: List[str] = []

        # Initialize all classes
        self._init_all_classes()

    def _init_all_classes(self) -> None:
        """Initialize all 10 character classes."""
        all_classes = [
            self._create_knight(),
            self._create_gardener(),
            self._create_healer(),
            self._create_weaver(),
            self._create_mage(),
            self._create_beastmaster(),
            self._create_bard(),
            self._create_prospector(),
            self._create_diplomat(),
            self._create_builder(),
        ]

        for cls in all_classes:
            self.classes[cls.id] = cls
            self.class_levels[cls.id] = 1
            self.class_xp[cls.id] = 0
            self.prestige_levels[cls.id] = 0

        # Unlock starter classes (all of them in Lelock - no gatekeeping!)
        self.unlocked_classes = list(self.classes.keys())

    # =========================================================================
    # CLASS DEFINITIONS
    # =========================================================================

    def _create_knight(self) -> CharacterClass:
        """Knight / Code-Knight - Protector, front-line defender"""
        return CharacterClass(
            id="knight",
            fantasy_name="Knight",
            tech_name="Code-Knight",
            description="Protector of Stability",
            lore_description=(
                "Knights stand between corruption and innocence. In the Physical realm, "
                "they are armored warriors of honor. In the Digital realm, they are "
                "living firewalls - debugging threats before they can harm the system. "
                "A Knight never runs from danger; they run toward those who need protection."
            ),
            primary_stat=PrimaryStat.DEFENSE,
            abilities=[
                ClassAbility(
                    name="shield_block",
                    fantasy_name="Shield Block",
                    tech_name="Firewall",
                    description="Raise your shield to block incoming damage for 3 seconds.",
                    mana_cost=10,
                    cooldown=8.0,
                    level_required=1,
                    effect_type="buff",
                    effect_value=0.75,  # 75% damage reduction
                    scales_with="defense",
                    animation="shield_up",
                    particle_color="#gold"
                ),
                ClassAbility(
                    name="protect_ally",
                    fantasy_name="Guardian's Oath",
                    tech_name="Proxy Shield",
                    description="Redirect damage from a nearby ally to yourself for 5 seconds.",
                    mana_cost=15,
                    cooldown=15.0,
                    level_required=5,
                    effect_type="buff",
                    effect_value=1.0,  # 100% redirect
                    animation="protection_aura",
                    particle_color="#00ffff"
                ),
                ClassAbility(
                    name="debug_strike",
                    fantasy_name="Purifying Strike",
                    tech_name="Debug Strike",
                    description="Attack that removes corruption from the target.",
                    mana_cost=20,
                    cooldown=12.0,
                    level_required=8,
                    effect_type="damage",
                    effect_value=30,
                    scales_with="defense",
                    scaling_factor=0.5,
                    animation="holy_strike",
                    particle_color="#ffffff"
                ),
                ClassAbility(
                    name="rally_defense",
                    fantasy_name="Rally the Guard",
                    tech_name="Distribute Load",
                    description="Grant all nearby allies +30% defense for 10 seconds.",
                    mana_cost=25,
                    cooldown=30.0,
                    level_required=12,
                    effect_type="buff",
                    effect_value=0.30,
                    animation="rally_cry",
                    particle_color="#ffd700"
                ),
                ClassAbility(
                    name="unbreakable",
                    fantasy_name="Unbreakable Will",
                    tech_name="System Integrity",
                    description="Become immune to all damage for 5 seconds. Cannot attack during.",
                    mana_cost=40,
                    cooldown=60.0,
                    level_required=18,
                    effect_type="buff",
                    effect_value=1.0,  # 100% immunity
                    animation="golden_aura",
                    particle_color="#ffd700"
                ),
            ],
            passive_bonuses={
                "damage_reduction": 0.20,  # 20% damage reduction
                "ally_defense_aura": 0.10,  # +10% to allies nearby
                "corruption_resistance": 0.15,  # 15% corruption resistance
            },
            starting_items=["wooden_shield", "health_potion_x3"],
            starting_tools=["sword"],
            color_primary="#4169e1",  # Royal blue
            color_secondary="#ffd700",  # Gold
            icon="class_knight",
            level_stat_bonus={"defense": 3, "strength": 1},
        )

    def _create_gardener(self) -> CharacterClass:
        """Gardener / Gardener - Growth specialist (same name in both realms!)"""
        return CharacterClass(
            id="gardener",
            fantasy_name="Gardener",
            tech_name="Gardener",  # Intentionally the same!
            description="Growth & Nurture Specialist",
            lore_description=(
                "The only class with the same name in both realms, because growth is growth. "
                "Whether tending copper wheat or optimizing processing cycles, Gardeners "
                "understand that all things need patience, care, and time. They don't force "
                "growth - they create the conditions for it to flourish naturally."
            ),
            primary_stat=PrimaryStat.NATURE,
            abilities=[
                ClassAbility(
                    name="speed_grow",
                    fantasy_name="Blessing of Growth",
                    tech_name="Overclock Growth",
                    description="Target crop grows 50% faster for the next stage.",
                    mana_cost=8,
                    cooldown=30.0,
                    level_required=1,
                    effect_type="utility",
                    effect_value=0.50,  # 50% faster
                    scales_with="nature",
                    animation="green_sparkles",
                    particle_color="#7ec850"
                ),
                ClassAbility(
                    name="bountiful_harvest",
                    fantasy_name="Bountiful Harvest",
                    tech_name="Yield Optimization",
                    description="Next harvest from target plot gives double yield.",
                    mana_cost=15,
                    cooldown=120.0,
                    level_required=4,
                    effect_type="utility",
                    effect_value=2.0,  # 2x yield
                    animation="golden_growth",
                    particle_color="#ffd700"
                ),
                ClassAbility(
                    name="weather_prayer",
                    fantasy_name="Weather Prayer",
                    tech_name="Climate API Call",
                    description="Request rain or sunshine for the next 6 hours.",
                    mana_cost=20,
                    cooldown=360.0,  # 6 real minutes
                    level_required=7,
                    effect_type="utility",
                    effect_value=6.0,  # Hours
                    animation="sky_shimmer",
                    particle_color="#87ceeb"
                ),
                ClassAbility(
                    name="soil_memory",
                    fantasy_name="Earth Remembers",
                    tech_name="Cache Soil Data",
                    description="Mark a plot to remember the last crop. Same crop planted here grows 30% faster permanently.",
                    mana_cost=25,
                    cooldown=600.0,  # 10 minutes
                    level_required=10,
                    effect_type="utility",
                    effect_value=0.30,
                    animation="earth_glow",
                    particle_color="#8b4513"
                ),
                ClassAbility(
                    name="great_bloom",
                    fantasy_name="The Great Bloom",
                    tech_name="Mass Compilation",
                    description="All crops on the farm instantly advance one growth stage.",
                    mana_cost=50,
                    cooldown=1800.0,  # 30 minutes
                    level_required=15,
                    effect_type="utility",
                    effect_value=1.0,  # One stage
                    animation="farm_wide_bloom",
                    particle_color="#90ee90"
                ),
            ],
            passive_bonuses={
                "crop_yield": 0.30,  # 30% more crops
                "grow_speed": 0.20,  # 20% faster growth
                "seed_efficiency": 0.15,  # 15% chance to not consume seed
                "wilt_resistance": 0.50,  # 50% longer before crops wilt
            },
            starting_items=["copper_wheat_seeds_x10", "watering_can", "fertilizer_x5"],
            starting_tools=["hoe", "watering_can"],
            color_primary="#228b22",  # Forest green
            color_secondary="#8b4513",  # Saddle brown
            icon="class_gardener",
            level_stat_bonus={"nature": 3, "wisdom": 1},
        )

    def _create_healer(self) -> CharacterClass:
        """Healer / Debugger - Fixes corruption, heals allies and daemons"""
        return CharacterClass(
            id="healer",
            fantasy_name="Healer",
            tech_name="Debugger",
            description="Fixer of What's Broken",
            lore_description=(
                "Where others see sickness, Healers see code that needs patching. "
                "In the Physical realm, they tend wounds with herbs and gentle magic. "
                "In the Digital realm, they trace corruption to its source and write "
                "fixes that heal from the inside out. Every bug is just a creature "
                "that forgot how to be well."
            ),
            primary_stat=PrimaryStat.WISDOM,
            abilities=[
                ClassAbility(
                    name="patch_wounds",
                    fantasy_name="Gentle Touch",
                    tech_name="Patch v1.0",
                    description="Heal a target for 30 HP instantly.",
                    mana_cost=10,
                    cooldown=5.0,
                    level_required=1,
                    effect_type="heal",
                    effect_value=30,
                    scales_with="wisdom",
                    scaling_factor=1.0,
                    animation="healing_light",
                    particle_color="#90ee90"
                ),
                ClassAbility(
                    name="purify_corruption",
                    fantasy_name="Purification",
                    tech_name="Anti-Malware Scan",
                    description="Remove corruption from target creature or NPC.",
                    mana_cost=20,
                    cooldown=15.0,
                    level_required=5,
                    effect_type="utility",
                    effect_value=1.0,  # Full cleanse
                    animation="purify_burst",
                    particle_color="#ffffff"
                ),
                ClassAbility(
                    name="regeneration",
                    fantasy_name="Life Bloom",
                    tech_name="Auto-Repair Daemon",
                    description="Target regenerates 5 HP per second for 20 seconds.",
                    mana_cost=25,
                    cooldown=30.0,
                    level_required=8,
                    effect_type="heal",
                    effect_value=5.0,
                    scales_with="wisdom",
                    scaling_factor=0.2,
                    animation="green_motes",
                    particle_color="#32cd32"
                ),
                ClassAbility(
                    name="mass_heal",
                    fantasy_name="Circle of Renewal",
                    tech_name="Broadcast Patch",
                    description="Heal all allies in range for 50 HP.",
                    mana_cost=35,
                    cooldown=45.0,
                    level_required=12,
                    effect_type="heal",
                    effect_value=50,
                    scales_with="wisdom",
                    scaling_factor=0.8,
                    animation="healing_wave",
                    particle_color="#98fb98"
                ),
                ClassAbility(
                    name="system_restore",
                    fantasy_name="Miracle",
                    tech_name="System Restore",
                    description="Revive a fainted ally with 50% HP, or fully heal a corrupted daemon.",
                    mana_cost=50,
                    cooldown=180.0,  # 3 minutes
                    level_required=16,
                    effect_type="heal",
                    effect_value=0.50,
                    animation="resurrection_light",
                    particle_color="#ffd700"
                ),
            ],
            passive_bonuses={
                "healing_power": 0.50,  # 50% stronger heals
                "corruption_detection_range": 0.30,  # 30% larger detection range
                "mana_regen": 0.20,  # 20% faster mana regeneration
                "ally_recovery_speed": 0.25,  # Allies near you recover 25% faster
            },
            starting_items=["healing_herbs_x10", "bandages_x5", "corruption_detector"],
            starting_tools=["staff"],
            color_primary="#98fb98",  # Pale green
            color_secondary="#ffffff",  # White
            icon="class_healer",
            level_stat_bonus={"wisdom": 3, "charisma": 1},
        )

    def _create_weaver(self) -> CharacterClass:
        """Weaver / Patch-Weaver - Crafting and repair specialist"""
        return CharacterClass(
            id="weaver",
            fantasy_name="Weaver",
            tech_name="Patch-Weaver",
            description="Creator of Solutions",
            lore_description=(
                "Weavers see the threads that connect all things - in the Physical "
                "realm, these are the fibers of cloth and the grain of wood. In the "
                "Digital realm, they're lines of code waiting to be stitched into "
                "something new. A Weaver never throws anything away; everything can "
                "be repaired, repurposed, or reimagined."
            ),
            primary_stat=PrimaryStat.DEXTERITY,
            abilities=[
                ClassAbility(
                    name="quick_stitch",
                    fantasy_name="Quick Stitch",
                    tech_name="Hotfix",
                    description="Instantly repair a damaged item to 50% durability.",
                    mana_cost=8,
                    cooldown=10.0,
                    level_required=1,
                    effect_type="utility",
                    effect_value=0.50,
                    animation="thread_weave",
                    particle_color="#daa520"
                ),
                ClassAbility(
                    name="reinforce",
                    fantasy_name="Reinforce",
                    tech_name="Stability Patch",
                    description="Make target item unbreakable for 10 minutes.",
                    mana_cost=15,
                    cooldown=120.0,
                    level_required=4,
                    effect_type="buff",
                    effect_value=10.0,  # Minutes
                    animation="golden_thread",
                    particle_color="#ffd700"
                ),
                ClassAbility(
                    name="salvage",
                    fantasy_name="Unravel",
                    tech_name="Decompile",
                    description="Break down an item to recover 75% of its materials.",
                    mana_cost=12,
                    cooldown=30.0,
                    level_required=6,
                    effect_type="utility",
                    effect_value=0.75,
                    animation="unravel_threads",
                    particle_color="#c0c0c0"
                ),
                ClassAbility(
                    name="masterwork",
                    fantasy_name="Masterwork",
                    tech_name="Optimize Build",
                    description="Your next crafted item has +50% quality bonus.",
                    mana_cost=25,
                    cooldown=180.0,  # 3 minutes
                    level_required=10,
                    effect_type="buff",
                    effect_value=0.50,
                    animation="master_glow",
                    particle_color="#e6e6fa"
                ),
                ClassAbility(
                    name="create_from_nothing",
                    fantasy_name="Creation",
                    tech_name="Fabricate",
                    description="Create a basic item using only mana. Higher level = better items.",
                    mana_cost=40,
                    cooldown=300.0,  # 5 minutes
                    level_required=14,
                    effect_type="summon",
                    effect_value=1.0,
                    scales_with="dexterity",
                    animation="creation_burst",
                    particle_color="#ff69b4"
                ),
            ],
            passive_bonuses={
                "crafting_quality": 0.25,  # 25% better quality
                "material_cost": -0.30,  # 30% less materials needed
                "crafting_speed": 0.20,  # 20% faster crafting
                "repair_efficiency": 0.40,  # 40% more durability from repairs
            },
            starting_items=["thread_x20", "cloth_x10", "repair_kit"],
            starting_tools=["needle", "scissors"],
            color_primary="#dda0dd",  # Plum
            color_secondary="#4b0082",  # Indigo
            icon="class_weaver",
            level_stat_bonus={"dexterity": 3, "intelligence": 1},
        )

    def _create_mage(self) -> CharacterClass:
        """Mage / Terminal Mage - Direct code manipulation, spells"""
        return CharacterClass(
            id="mage",
            fantasy_name="Mage",
            tech_name="Terminal Mage",
            description="Script User & Code Wielder",
            lore_description=(
                "Terminal Mages speak the language of reality itself. Where others "
                "see magic spells, they see functions and parameters. Where others "
                "pray to gods, they query APIs. A skilled Terminal Mage can sudo "
                "reality into compliance - but with great root access comes great "
                "responsibility."
            ),
            primary_stat=PrimaryStat.INTELLIGENCE,
            abilities=[
                ClassAbility(
                    name="code_bolt",
                    fantasy_name="Arcane Bolt",
                    tech_name="Code Injection",
                    description="Fire a bolt of pure energy at target. Fast, reliable damage.",
                    mana_cost=8,
                    cooldown=2.0,
                    level_required=1,
                    effect_type="damage",
                    effect_value=25,
                    scales_with="intelligence",
                    scaling_factor=0.8,
                    animation="energy_bolt",
                    particle_color="#00ffff"
                ),
                ClassAbility(
                    name="system_call",
                    fantasy_name="Invoke Element",
                    tech_name="System Call",
                    description="Call upon an elemental force (fire/ice/lightning) for varied effects.",
                    mana_cost=15,
                    cooldown=8.0,
                    level_required=4,
                    effect_type="damage",
                    effect_value=40,
                    scales_with="intelligence",
                    scaling_factor=1.0,
                    animation="elemental_burst",
                    particle_color="#ff4500"
                ),
                ClassAbility(
                    name="analyze",
                    fantasy_name="True Sight",
                    tech_name="Debug Mode",
                    description="See hidden objects, reveal stats of creatures, detect corruption.",
                    mana_cost=12,
                    cooldown=20.0,
                    level_required=6,
                    effect_type="utility",
                    effect_value=30.0,  # Duration in seconds
                    animation="eye_glow",
                    particle_color="#9400d3"
                ),
                ClassAbility(
                    name="teleport",
                    fantasy_name="Blink",
                    tech_name="Fast Travel Protocol",
                    description="Instantly teleport a short distance in any direction.",
                    mana_cost=20,
                    cooldown=15.0,
                    level_required=9,
                    effect_type="utility",
                    effect_value=200,  # Pixels distance
                    animation="blink_effect",
                    particle_color="#ff00ff"
                ),
                ClassAbility(
                    name="root_access",
                    fantasy_name="Archmage's Word",
                    tech_name="Sudo Command",
                    description="Your next ability costs no mana and has double effect.",
                    mana_cost=30,
                    cooldown=120.0,
                    level_required=15,
                    effect_type="buff",
                    effect_value=2.0,  # Double effect
                    animation="sudo_aura",
                    particle_color="#ffd700"
                ),
            ],
            passive_bonuses={
                "mana_regen": 0.25,  # 25% faster mana regen
                "terminal_access": 1.0,  # Can use advanced terminal commands
                "spell_power": 0.15,  # 15% stronger spells
                "cooldown_reduction": 0.10,  # 10% faster cooldowns
            },
            starting_items=["mana_potion_x5", "spell_tome", "terminal_key"],
            starting_tools=["staff", "wand"],
            unlock_condition=None,  # Available from start
            color_primary="#9400d3",  # Dark violet
            color_secondary="#00ffff",  # Cyan
            icon="class_mage",
            level_stat_bonus={"intelligence": 3, "wisdom": 1},
        )

    def _create_beastmaster(self) -> CharacterClass:
        """Beastmaster / Beast-Blogger - Daemon taming and bonding"""
        return CharacterClass(
            id="beastmaster",
            fantasy_name="Beastmaster",
            tech_name="Beast-Blogger",
            description="Daemon Bond Specialist",
            lore_description=(
                "Beast-Bloggers document the lives of daemons, earning their trust "
                "through patience and understanding. In the Physical realm, they're "
                "animal whisperers who speak the language of creatures. In the Digital "
                "realm, they're daemon tamers who understand that every process has "
                "a personality. The best daemon partners aren't caught - they choose you."
            ),
            primary_stat=PrimaryStat.CHARISMA,
            abilities=[
                ClassAbility(
                    name="call_companion",
                    fantasy_name="Summon Friend",
                    tech_name="Spawn Daemon",
                    description="Call your bonded daemon companion to your side.",
                    mana_cost=5,
                    cooldown=10.0,
                    level_required=1,
                    effect_type="summon",
                    effect_value=1.0,
                    animation="summon_sparkle",
                    particle_color="#ff69b4"
                ),
                ClassAbility(
                    name="pack_bond",
                    fantasy_name="Pack Bond",
                    tech_name="Process Sync",
                    description="You and your daemon share health for 30 seconds.",
                    mana_cost=15,
                    cooldown=45.0,
                    level_required=4,
                    effect_type="buff",
                    effect_value=30.0,  # Duration
                    animation="bond_link",
                    particle_color="#ff1493"
                ),
                ClassAbility(
                    name="whisper_wild",
                    fantasy_name="Whisper to the Wild",
                    tech_name="Broadcast Friendly",
                    description="Wild daemons won't attack you for 5 minutes.",
                    mana_cost=20,
                    cooldown=300.0,  # 5 minutes
                    level_required=7,
                    effect_type="buff",
                    effect_value=300.0,  # Duration
                    animation="nature_whisper",
                    particle_color="#98fb98"
                ),
                ClassAbility(
                    name="beast_form",
                    fantasy_name="Spirit Merge",
                    tech_name="Process Fusion",
                    description="Temporarily become your daemon, gaining their abilities.",
                    mana_cost=30,
                    cooldown=120.0,
                    level_required=11,
                    effect_type="buff",
                    effect_value=60.0,  # Duration in seconds
                    animation="transformation",
                    particle_color="#ff00ff"
                ),
                ClassAbility(
                    name="alpha_call",
                    fantasy_name="Call of the Alpha",
                    tech_name="Root Daemon Summon",
                    description="Summon all your bonded daemons at once for a massive battle.",
                    mana_cost=50,
                    cooldown=300.0,  # 5 minutes
                    level_required=17,
                    effect_type="summon",
                    effect_value=5.0,  # Max daemons
                    animation="alpha_howl",
                    particle_color="#ffd700"
                ),
            ],
            passive_bonuses={
                "daemon_friendship_gain": 0.50,  # 50% faster friendship
                "companion_slots": 1,  # +1 companion slot
                "daemon_stat_boost": 0.20,  # Your daemons are 20% stronger
                "wild_encounter_rate": 0.25,  # 25% more daemon encounters
            },
            starting_items=["daemon_treat_x10", "capture_charm_x3", "creature_journal"],
            starting_tools=["net"],
            color_primary="#ff69b4",  # Hot pink
            color_secondary="#228b22",  # Forest green
            icon="class_beastmaster",
            level_stat_bonus={"charisma": 2, "nature": 2},
        )

    def _create_bard(self) -> CharacterClass:
        """Bard / Sound-Smith - Audio manipulation, buffs through music"""
        return CharacterClass(
            id="bard",
            fantasy_name="Bard",
            tech_name="Sound-Smith",
            description="Musician & Mood Manipulator",
            lore_description=(
                "Sound-Smiths know that reality vibrates at certain frequencies, and "
                "music is just organized vibration. In the Physical realm, they play "
                "instruments that soothe and inspire. In the Digital realm, they "
                "manipulate audio frequencies to buff allies and debuff corruption. "
                "A good song can heal what potions cannot."
            ),
            primary_stat=PrimaryStat.CHARISMA,
            abilities=[
                ClassAbility(
                    name="soothing_melody",
                    fantasy_name="Soothing Melody",
                    tech_name="Calm.wav",
                    description="Play a calming tune that restores 5 HP/sec to all nearby allies for 10s.",
                    mana_cost=12,
                    cooldown=20.0,
                    level_required=1,
                    effect_type="heal",
                    effect_value=5.0,
                    scales_with="charisma",
                    scaling_factor=0.3,
                    animation="music_notes",
                    particle_color="#87ceeb"
                ),
                ClassAbility(
                    name="battle_hymn",
                    fantasy_name="Battle Hymn",
                    tech_name="Overclock.mp3",
                    description="Inspiring music grants +25% damage to all allies for 15 seconds.",
                    mana_cost=18,
                    cooldown=30.0,
                    level_required=4,
                    effect_type="buff",
                    effect_value=0.25,
                    animation="war_drums",
                    particle_color="#ff4500"
                ),
                ClassAbility(
                    name="lullaby",
                    fantasy_name="Lullaby",
                    tech_name="Sleep.exe",
                    description="Put enemies to sleep for 8 seconds. Wakes on damage.",
                    mana_cost=20,
                    cooldown=25.0,
                    level_required=7,
                    effect_type="utility",
                    effect_value=8.0,
                    animation="dreamy_notes",
                    particle_color="#e6e6fa"
                ),
                ClassAbility(
                    name="discordant_note",
                    fantasy_name="Discordant Note",
                    tech_name="Malformed Packet",
                    description="Harsh sound that deals damage and confuses enemies.",
                    mana_cost=15,
                    cooldown=12.0,
                    level_required=9,
                    effect_type="damage",
                    effect_value=35,
                    scales_with="charisma",
                    scaling_factor=0.6,
                    animation="sound_wave",
                    particle_color="#ff00ff"
                ),
                ClassAbility(
                    name="symphony",
                    fantasy_name="Grand Symphony",
                    tech_name="Full Spectrum Broadcast",
                    description="Play all buffs simultaneously for 20 seconds.",
                    mana_cost=45,
                    cooldown=180.0,  # 3 minutes
                    level_required=15,
                    effect_type="buff",
                    effect_value=20.0,  # Duration
                    animation="grand_performance",
                    particle_color="#ffd700"
                ),
            ],
            passive_bonuses={
                "buff_duration": 0.30,  # 30% longer buffs
                "npc_mood_bonus": 0.25,  # NPCs like you 25% more
                "experience_gain": 0.10,  # 10% more XP from all sources
                "charm_resistance": 0.20,  # 20% resistance to charm effects
            },
            starting_items=["lute", "song_sheets_x5", "pitch_pipe"],
            starting_tools=["instrument"],
            color_primary="#da70d6",  # Orchid
            color_secondary="#ffd700",  # Gold
            icon="class_bard",
            level_stat_bonus={"charisma": 3, "luck": 1},
        )

    def _create_prospector(self) -> CharacterClass:
        """Prospector / Dataminer - Finding resources and secrets"""
        return CharacterClass(
            id="prospector",
            fantasy_name="Prospector",
            tech_name="Dataminer",
            description="Resource Finder & Secret Seeker",
            lore_description=(
                "Dataminers dig deep - into caves, into code, into the hidden corners "
                "of reality. In the Physical realm, they're miners and treasure hunters "
                "with an uncanny knack for finding ore. In the Digital realm, they "
                "extract valuable data that others overlook. Luck isn't random to them; "
                "it's a skill they've cultivated."
            ),
            primary_stat=PrimaryStat.LUCK,
            abilities=[
                ClassAbility(
                    name="ore_sense",
                    fantasy_name="Ore Sense",
                    tech_name="Resource Scanner",
                    description="Highlight all resources within 50 tiles for 30 seconds.",
                    mana_cost=10,
                    cooldown=45.0,
                    level_required=1,
                    effect_type="utility",
                    effect_value=50,  # Range in tiles
                    animation="pulse_scan",
                    particle_color="#ffd700"
                ),
                ClassAbility(
                    name="lucky_strike",
                    fantasy_name="Lucky Strike",
                    tech_name="RNG Manipulation",
                    description="Your next gathering action is guaranteed to be rare quality.",
                    mana_cost=15,
                    cooldown=60.0,
                    level_required=4,
                    effect_type="buff",
                    effect_value=1.0,  # Guaranteed rare
                    animation="lucky_sparkle",
                    particle_color="#00ff00"
                ),
                ClassAbility(
                    name="deep_dive",
                    fantasy_name="Deep Dive",
                    tech_name="Deep Query",
                    description="Find hidden caches, secret paths, and buried treasure nearby.",
                    mana_cost=20,
                    cooldown=120.0,
                    level_required=7,
                    effect_type="utility",
                    effect_value=100,  # Search range
                    animation="ground_pulse",
                    particle_color="#8b4513"
                ),
                ClassAbility(
                    name="appraise",
                    fantasy_name="Keen Eye",
                    tech_name="Value Analysis",
                    description="See the exact value and rarity of items. Reveals hidden properties.",
                    mana_cost=8,
                    cooldown=5.0,
                    level_required=5,
                    effect_type="utility",
                    effect_value=1.0,
                    animation="eye_flash",
                    particle_color="#ffffff"
                ),
                ClassAbility(
                    name="motherlode",
                    fantasy_name="Motherlode",
                    tech_name="Data Jackpot",
                    description="Your next mining node yields 5x resources.",
                    mana_cost=35,
                    cooldown=300.0,  # 5 minutes
                    level_required=13,
                    effect_type="buff",
                    effect_value=5.0,
                    animation="golden_explosion",
                    particle_color="#ffd700"
                ),
            ],
            passive_bonuses={
                "rare_find_chance": 0.40,  # 40% more rare finds
                "hidden_detection": 1.0,  # Can detect hidden items
                "mining_speed": 0.25,  # 25% faster mining
                "sell_price_bonus": 0.15,  # 15% better prices
            },
            starting_items=["pickaxe", "treasure_map", "lucky_coin"],
            starting_tools=["pickaxe", "shovel"],
            color_primary="#daa520",  # Goldenrod
            color_secondary="#8b4513",  # Saddle brown
            icon="class_prospector",
            level_stat_bonus={"luck": 3, "strength": 1},
        )

    def _create_diplomat(self) -> CharacterClass:
        """Diplomat / Networker - NPC relationships and quests"""
        return CharacterClass(
            id="diplomat",
            fantasy_name="Diplomat",
            tech_name="Networker",
            description="Connection Specialist",
            lore_description=(
                "Networkers understand that relationships are the real currency of "
                "any world. In the Physical realm, they're smooth-talking diplomats "
                "who can befriend anyone. In the Digital realm, they're masters of "
                "connection protocols, linking nodes that others can't reach. Every "
                "NPC remembers a Networker fondly."
            ),
            primary_stat=PrimaryStat.CHARISMA,
            abilities=[
                ClassAbility(
                    name="smooth_talk",
                    fantasy_name="Smooth Talk",
                    tech_name="Handshake Protocol",
                    description="Instantly gain 20 friendship with target NPC.",
                    mana_cost=10,
                    cooldown=30.0,
                    level_required=1,
                    effect_type="utility",
                    effect_value=20,
                    scales_with="charisma",
                    scaling_factor=0.5,
                    animation="charm_sparkle",
                    particle_color="#ff69b4"
                ),
                ClassAbility(
                    name="reputation_boost",
                    fantasy_name="Good Word",
                    tech_name="Reference Broadcast",
                    description="All NPCs in the area gain +10 friendship with you.",
                    mana_cost=20,
                    cooldown=120.0,
                    level_required=5,
                    effect_type="utility",
                    effect_value=10,
                    animation="reputation_wave",
                    particle_color="#ffd700"
                ),
                ClassAbility(
                    name="quest_finder",
                    fantasy_name="Hear Whispers",
                    tech_name="Query Opportunities",
                    description="NPCs reveal available quests and their rewards.",
                    mana_cost=15,
                    cooldown=60.0,
                    level_required=4,
                    effect_type="utility",
                    effect_value=1.0,
                    animation="question_marks",
                    particle_color="#87ceeb"
                ),
                ClassAbility(
                    name="haggle",
                    fantasy_name="Silver Tongue",
                    tech_name="Price Negotiation",
                    description="Get 30% better prices at shops for 5 minutes.",
                    mana_cost=12,
                    cooldown=180.0,  # 3 minutes
                    level_required=7,
                    effect_type="buff",
                    effect_value=0.30,
                    animation="coin_sparkle",
                    particle_color="#ffd700"
                ),
                ClassAbility(
                    name="trusted_friend",
                    fantasy_name="Trusted Friend",
                    tech_name="Root Trust",
                    description="Target NPC treats you as maximum friendship permanently.",
                    mana_cost=40,
                    cooldown=600.0,  # 10 minutes
                    level_required=14,
                    effect_type="utility",
                    effect_value=100,  # Max friendship
                    animation="heart_burst",
                    particle_color="#ff1493"
                ),
            ],
            passive_bonuses={
                "npc_friendship_gain": 0.30,  # 30% faster friendship
                "shop_prices": -0.15,  # 15% better prices
                "quest_rewards": 0.20,  # 20% better quest rewards
                "gossip_range": 0.50,  # 50% further gossip range
            },
            starting_items=["gift_basket", "business_cards_x10", "friendship_bracelet"],
            starting_tools=["quill"],
            color_primary="#4682b4",  # Steel blue
            color_secondary="#ffc0cb",  # Pink
            icon="class_diplomat",
            level_stat_bonus={"charisma": 3, "wisdom": 1},
        )

    def _create_builder(self) -> CharacterClass:
        """Builder / Architect - Construction and world modification"""
        return CharacterClass(
            id="builder",
            fantasy_name="Builder",
            tech_name="Architect",
            description="Constructor & World Shaper",
            lore_description=(
                "Architects don't just build things - they build the world itself. "
                "In the Physical realm, they're master craftsmen who raise barns and "
                "forge bridges. In the Digital realm, they compile new structures "
                "into existence. Every building in Oakhaven was placed by an Architect, "
                "and every one can be improved."
            ),
            primary_stat=PrimaryStat.STRENGTH,
            abilities=[
                ClassAbility(
                    name="quick_build",
                    fantasy_name="Rapid Construction",
                    tech_name="Compile Structure",
                    description="Build a basic structure instantly instead of over time.",
                    mana_cost=15,
                    cooldown=60.0,
                    level_required=1,
                    effect_type="utility",
                    effect_value=1.0,  # Instant
                    animation="hammer_sparks",
                    particle_color="#ffa500"
                ),
                ClassAbility(
                    name="reinforce_structure",
                    fantasy_name="Fortify",
                    tech_name="Error Correction",
                    description="Make a building immune to damage for 24 hours.",
                    mana_cost=20,
                    cooldown=300.0,  # 5 minutes
                    level_required=4,
                    effect_type="buff",
                    effect_value=24.0,  # Hours
                    animation="shield_overlay",
                    particle_color="#4169e1"
                ),
                ClassAbility(
                    name="blueprint_vision",
                    fantasy_name="Architect's Eye",
                    tech_name="Blueprint Mode",
                    description="See where buildings can be placed and preview results.",
                    mana_cost=8,
                    cooldown=5.0,
                    level_required=3,
                    effect_type="utility",
                    effect_value=60.0,  # Duration in seconds
                    animation="grid_overlay",
                    particle_color="#00ff00"
                ),
                ClassAbility(
                    name="salvage_building",
                    fantasy_name="Careful Demolition",
                    tech_name="Clean Uninstall",
                    description="Demolish a building and recover 100% of materials.",
                    mana_cost=25,
                    cooldown=180.0,  # 3 minutes
                    level_required=8,
                    effect_type="utility",
                    effect_value=1.0,  # 100% recovery
                    animation="controlled_collapse",
                    particle_color="#8b4513"
                ),
                ClassAbility(
                    name="grand_design",
                    fantasy_name="Grand Design",
                    tech_name="Macro Builder",
                    description="Place blueprints for up to 10 connected structures at once.",
                    mana_cost=40,
                    cooldown=300.0,  # 5 minutes
                    level_required=12,
                    effect_type="utility",
                    effect_value=10,  # Max structures
                    animation="master_blueprint",
                    particle_color="#ffd700"
                ),
            ],
            passive_bonuses={
                "build_time": -0.40,  # 40% faster building
                "structure_durability": 0.25,  # 25% more durable
                "material_efficiency": 0.20,  # 20% less materials needed
                "build_range": 0.30,  # 30% larger build radius
            },
            starting_items=["wooden_planks_x20", "nails_x50", "blueprint_basic"],
            starting_tools=["hammer", "saw"],
            color_primary="#cd853f",  # Peru (wood color)
            color_secondary="#808080",  # Gray (stone)
            icon="class_builder",
            level_stat_bonus={"strength": 3, "dexterity": 1},
        )

    # =========================================================================
    # CLASS MANAGEMENT
    # =========================================================================

    def select_starting_class(self, class_id: str) -> bool:
        """
        Select initial class for a new character.
        All classes are available from the start in Lelock.
        """
        if class_id not in self.classes:
            return False

        self.current_class = self.classes[class_id]
        return True

    def change_class(self, new_class_id: str) -> tuple[bool, str]:
        """
        Change to a different class.

        Returns:
            (success, message)
        """
        if new_class_id not in self.classes:
            return False, f"Unknown class: {new_class_id}"

        if new_class_id not in self.unlocked_classes:
            return False, f"Class not unlocked: {new_class_id}"

        if self.current_class and self.current_class.id == new_class_id:
            return False, "Already this class"

        # Store old class info
        old_class = self.current_class

        # Switch class
        self.current_class = self.classes[new_class_id]

        # Message
        if old_class:
            msg = f"Changed from {old_class.fantasy_name} to {self.current_class.fantasy_name}"
        else:
            msg = f"Became a {self.current_class.fantasy_name}"

        return True, msg

    def get_current_level(self) -> int:
        """Get level of current class."""
        if not self.current_class:
            return 1
        return self.class_levels.get(self.current_class.id, 1)

    def get_current_xp(self) -> int:
        """Get XP in current class."""
        if not self.current_class:
            return 0
        return self.class_xp.get(self.current_class.id, 0)

    def get_xp_for_next_level(self) -> int:
        """Get XP required for next level."""
        level = self.get_current_level()
        if level >= self.MAX_LEVEL:
            return 0  # Already max
        return self.XP_PER_LEVEL[level]  # Index matches next level requirement

    def add_xp(self, amount: int) -> tuple[int, bool]:
        """
        Add XP to current class.

        Returns:
            (new_total_xp, did_level_up)
        """
        if not self.current_class:
            return 0, False

        class_id = self.current_class.id
        current_level = self.class_levels[class_id]

        if current_level >= self.MAX_LEVEL:
            return self.class_xp[class_id], False

        self.class_xp[class_id] += amount

        # Check for level up
        leveled_up = False
        while (current_level < self.MAX_LEVEL and
               self.class_xp[class_id] >= self.XP_PER_LEVEL[current_level]):
            self.class_xp[class_id] -= self.XP_PER_LEVEL[current_level]
            self.class_levels[class_id] += 1
            current_level += 1
            leveled_up = True

        return self.class_xp[class_id], leveled_up

    def get_active_abilities(self) -> List[ClassAbility]:
        """Get abilities available at current level."""
        if not self.current_class:
            return []
        level = self.get_current_level()
        return self.current_class.get_abilities_at_level(level)

    def get_all_passives(self) -> Dict[str, float]:
        """Get all passive bonuses for current class at current level."""
        if not self.current_class:
            return {}

        level = self.get_current_level()
        passives = {}

        for key in self.current_class.passive_bonuses:
            passives[key] = self.current_class.get_passive_value(key, level)

        return passives

    def can_prestige(self) -> bool:
        """Check if current class can prestige (level 20)."""
        return self.get_current_level() >= self.MAX_LEVEL

    def prestige(self) -> tuple[bool, str]:
        """
        Prestige current class.
        Resets level to 1 but grants permanent bonuses.
        """
        if not self.current_class:
            return False, "No class selected"

        if not self.can_prestige():
            return False, "Must be level 20 to prestige"

        class_id = self.current_class.id
        self.prestige_levels[class_id] += 1
        self.class_levels[class_id] = 1
        self.class_xp[class_id] = 0

        prestige_count = self.prestige_levels[class_id]
        return True, f"Prestige {prestige_count}! Class reset with +{prestige_count * 5}% permanent bonus."

    def get_prestige_bonus(self, class_id: Optional[str] = None) -> float:
        """Get prestige bonus multiplier for a class."""
        if class_id is None:
            if not self.current_class:
                return 1.0
            class_id = self.current_class.id

        prestige = self.prestige_levels.get(class_id, 0)
        return 1.0 + (prestige * 0.05)  # 5% per prestige

    def get_class_info(self, class_id: str) -> Optional[CharacterClass]:
        """Get info about a specific class."""
        return self.classes.get(class_id)

    def get_all_classes(self) -> List[CharacterClass]:
        """Get list of all classes."""
        return list(self.classes.values())

    def get_unlocked_classes(self) -> List[CharacterClass]:
        """Get list of unlocked classes."""
        return [self.classes[cid] for cid in self.unlocked_classes]


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_class_system() -> ClassSystem:
    """Factory function to create a new class system."""
    return ClassSystem()


def get_class_by_id(class_id: str) -> Optional[CharacterClass]:
    """Quick lookup for class info without creating a full system."""
    system = ClassSystem()
    return system.get_class_info(class_id)


def get_all_class_ids() -> List[str]:
    """Get list of all class IDs."""
    return [
        "knight", "gardener", "healer", "weaver", "mage",
        "beastmaster", "bard", "prospector", "diplomat", "builder"
    ]


# =============================================================================
# MODULE CONSTANTS (for settings.py compatibility)
# =============================================================================

# Quick reference dict matching the existing CLASSES format in settings.py
CLASS_QUICK_REF = {
    'knight': {
        'name': 'Code-Knight',
        'traditional': 'Paladin',
        'description': 'Protector of Stability',
        'ability': 'Firewall Aura',
        'primary_stat': 'defense',
    },
    'gardener': {
        'name': 'Gardener',
        'traditional': 'Druid',
        'description': 'Growth & Nurture',
        'ability': 'Photosynthesis',
        'primary_stat': 'nature',
    },
    'healer': {
        'name': 'Debugger',
        'traditional': 'Cleric',
        'description': 'Fixer of What\'s Broken',
        'ability': 'System Restore',
        'primary_stat': 'wisdom',
    },
    'weaver': {
        'name': 'Patch-Weaver',
        'traditional': 'Artificer',
        'description': 'Creator of Solutions',
        'ability': 'Fabricate',
        'primary_stat': 'dexterity',
    },
    'mage': {
        'name': 'Terminal Mage',
        'traditional': 'Wizard',
        'description': 'Script User & Code Wielder',
        'ability': 'Sudo Command',
        'primary_stat': 'intelligence',
    },
    'beastmaster': {
        'name': 'Beast-Blogger',
        'traditional': 'Ranger',
        'description': 'Daemon Bond Specialist',
        'ability': 'Alpha Call',
        'primary_stat': 'charisma',
    },
    'bard': {
        'name': 'Sound-Smith',
        'traditional': 'Bard',
        'description': 'Musician & Mood Manipulator',
        'ability': 'Grand Symphony',
        'primary_stat': 'charisma',
    },
    'prospector': {
        'name': 'Dataminer',
        'traditional': 'Barbarian',
        'description': 'Resource Finder & Secret Seeker',
        'ability': 'Motherlode',
        'primary_stat': 'luck',
    },
    'diplomat': {
        'name': 'Networker',
        'traditional': 'Warlock',
        'description': 'Connection Specialist',
        'ability': 'Trusted Friend',
        'primary_stat': 'charisma',
    },
    'builder': {
        'name': 'Architect',
        'traditional': 'Fighter',
        'description': 'Constructor & World Shaper',
        'ability': 'Grand Design',
        'primary_stat': 'strength',
    },
}
