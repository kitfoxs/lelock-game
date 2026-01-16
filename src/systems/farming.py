"""
Lelock Farming System - Hardware Crop Agriculture
L.E.L.O.C.K. - Life Emulation & Lucid Observation for Care & Keeping

"We do not grow crops. We grow conversations with the earth."
    - Rootwell, First Farmer of Oakhaven

This implements the cozy, forgiving farming system where techno-organic
Hardware Crops grow from the merger of natural life and digital processes.

NO STRESS DESIGN:
- Crops NEVER die immediately from neglect
- Long grace periods before withering
- Clear, friendly visual indicators
- Weather helps, not hurts
- The farm is a sanctuary, not a chore
"""

import pygame
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from random import choice, randint, uniform
import math

from settings import TILE_SIZE, LAYERS, COLORS


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class SoilState(Enum):
    """States a soil tile can be in."""
    UNTILLED = auto()    # Raw ground, needs Compiler's Rake
    TILLED = auto()      # Ready for planting
    WATERED = auto()     # Moist and happy
    PLANTED = auto()     # Seed in ground
    GROWING = auto()     # Crop developing
    READY = auto()       # Harvest time!
    WITHERING = auto()   # Neglected but saveable (NO STRESS - long grace period)


class Season(Enum):
    """The four seasons of Lelock."""
    SPRING = auto()
    SUMMER = auto()
    FALL = auto()
    WINTER = auto()


class GrowthStage(Enum):
    """Visual growth stages for crops."""
    SEED = 0       # Just planted, barely visible
    SPROUT = 1     # Tiny shoots
    GROWING = 2    # Getting bigger
    MATURE = 3     # Almost ready
    READY = 4      # Harvestable!
    WITHERING = 5  # Neglected (but saveable!)


# =============================================================================
# HARDWARE CROP DATA (from ITEMS.md lore)
# =============================================================================

@dataclass
class CropData:
    """
    Complete data for a Hardware Crop type.

    All data sourced from the sacred ITEMS.md lore document.
    """
    name: str
    internal_name: str
    days_to_mature: int
    seasons: List[Season]
    sell_price: int
    description: str
    soil_preference: str = "any"
    indoor_only: bool = False

    # Yield randomization (cozy generosity)
    min_yield: int = 1
    max_yield: int = 3

    # Growth stages (how many visual frames)
    growth_stages: int = 5

    # Lore tidbits for UI/dialogue
    lore_snippet: str = ""

    # Special effects on harvest
    harvest_effect: Optional[str] = None


# The complete Hardware Crop encyclopedia from ITEMS.md
HARDWARE_CROPS: Dict[str, CropData] = {
    # =================================
    # SPRING CROPS
    # =================================
    'copper_wheat': CropData(
        name="Copper Wheat",
        internal_name='copper_wheat',
        days_to_mature=4,
        seasons=[Season.SPRING, Season.SUMMER],
        sell_price=15,
        description="Stalks of flexible copper wire with golden conductive nodules.",
        soil_preference="iron-rich",
        lore_snippet="Plant when the first robin sings, harvest when the last one leaves.",
    ),

    'bluetooth_berries': CropData(
        name="Bluetooth Berries",
        internal_name='bluetooth_berries',
        days_to_mature=6,
        seasons=[Season.SPRING],
        sell_price=20,
        description="Deep blue berries that emit a faint rhythmic pulse.",
        soil_preference="rocky",
        lore_snippet="When multiple bushes grow nearby, their pulses synchronize.",
    ),

    'static_strawberries': CropData(
        name="Static Strawberries",
        internal_name='static_strawberries',
        days_to_mature=5,
        seasons=[Season.SPRING],
        sell_price=18,
        description="Heart-shaped red berries that produce tiny harmless sparks.",
        soil_preference="acidic",
        harvest_effect="spark",
        lore_snippet="The sparks are harmless but surprising!",
    ),

    # =================================
    # SUMMER CROPS
    # =================================
    'silicon_berries': CropData(
        name="Silicon Berries",
        internal_name='silicon_berries',
        days_to_mature=6,
        seasons=[Season.SUMMER],
        sell_price=25,
        description="Translucent geometric berries that glow softly.",
        soil_preference="sandy",
        lore_snippet="Each bush's crystal leaves produce unique tones in the wind.",
        harvest_effect="glow",
    ),

    'prism_peppers': CropData(
        name="Prism Peppers",
        internal_name='prism_peppers',
        days_to_mature=5,
        seasons=[Season.SUMMER],
        sell_price=22,
        description="Peppers that cycle through colors, locking when picked.",
        soil_preference="sandy",
        harvest_effect="rainbow",
        lore_snippet="The color determines the flavor - red is spicy, blue is calming.",
    ),

    'bandwidth_beans': CropData(
        name="Bandwidth Beans",
        internal_name='bandwidth_beans',
        days_to_mature=5,
        seasons=[Season.SUMMER],
        sell_price=18,
        description="Climbing vines with pods of glowing green beans.",
        soil_preference="trellised",
        lore_snippet="The more sunlight they receive, the larger the beans grow.",
    ),

    'crystal_cucumbers': CropData(
        name="Crystal Cucumbers",
        internal_name='crystal_cucumbers',
        days_to_mature=4,
        seasons=[Season.SUMMER],
        sell_price=16,
        description="Translucent green cucumbers that refract tiny rainbows.",
        soil_preference="moist",
        harvest_effect="rainbow",
        lore_snippet="Cooling to the touch even in summer heat.",
    ),

    'kernel_corn': CropData(
        name="Kernel Corn",
        internal_name='kernel_corn',
        days_to_mature=9,
        seasons=[Season.SUMMER, Season.FALL],
        sell_price=35,
        description="Tall stalks with ears of gold and silver shimmering kernels.",
        soil_preference="rows",
        min_yield=2,
        max_yield=5,
        lore_snippet="Each kernel is perfectly uniform - evidence of optimized growth code.",
    ),

    # =================================
    # FALL CROPS
    # =================================
    'graphite_taters': CropData(
        name="Graphite Taters",
        internal_name='graphite_taters',
        days_to_mature=7,
        seasons=[Season.FALL],
        sell_price=20,
        description="Heavy grey tubers, the foundation of Lelock's energy economy.",
        soil_preference="mineral-heavy",
        min_yield=2,
        max_yield=4,
        lore_snippet="Carbon Mash burns hotter than wood with zero emissions.",
    ),

    'memory_melons': CropData(
        name="Memory Melons",
        internal_name='memory_melons',
        days_to_mature=10,
        seasons=[Season.SUMMER, Season.FALL],
        sell_price=50,
        description="Large cubic watermelons that absorb ambient data.",
        soil_preference="rich",
        min_yield=1,
        max_yield=2,
        harvest_effect="memory_sparkle",
        lore_snippet="Eating one might summon memories of festivals past.",
    ),

    'cache_carrots': CropData(
        name="Cache Carrots",
        internal_name='cache_carrots',
        days_to_mature=8,
        seasons=[Season.FALL],
        sell_price=28,
        description="Orange roots with visible data-vein patterns.",
        soil_preference="loose",
        harvest_effect="treasure_chance",
        lore_snippet="Sometimes bring up small treasures cached underground.",
    ),

    'logic_leeks': CropData(
        name="Logic Leeks",
        internal_name='logic_leeks',
        days_to_mature=6,
        seasons=[Season.FALL, Season.WINTER],
        sell_price=24,
        description="Elegant stalks with a subtle Golden Ratio spiral pattern.",
        soil_preference="composted",
        lore_snippet="The white and green sections follow perfect mathematics.",
    ),

    'compiler_cabbage': CropData(
        name="Compiler Cabbage",
        internal_name='compiler_cabbage',
        days_to_mature=7,
        seasons=[Season.FALL],
        sell_price=26,
        description="Layered heads with leaves displaying subtle code patterns.",
        soil_preference="nitrogen-rich",
        lore_snippet="Each layer represents a nesting of data.",
    ),

    'bios_beets': CropData(
        name="BIOS Beets",
        internal_name='bios_beets',
        days_to_mature=8,
        seasons=[Season.FALL],
        sell_price=30,
        description="Deep purple roots that pulse with a slow rhythmic glow.",
        soil_preference="mineral-rich",
        harvest_effect="purple_glow",
        lore_snippet="The color stains everything it touches. Everything.",
    ),

    # =================================
    # ALL-SEASON / INDOOR CROPS
    # =================================
    'ram_radishes': CropData(
        name="RAM Radishes",
        internal_name='ram_radishes',
        days_to_mature=3,
        seasons=[Season.SPRING, Season.SUMMER, Season.FALL, Season.WINTER],
        sell_price=8,
        description="Fast-growing roots with a distinctive checkered pattern.",
        soil_preference="quick-drain",
        lore_snippet="They sprout almost visibly - favorites for teaching children.",
    ),

    'fiber_optic_ferns': CropData(
        name="Fiber-Optic Ferns",
        internal_name='fiber_optic_ferns',
        days_to_mature=8,
        seasons=[Season.SPRING, Season.SUMMER, Season.FALL, Season.WINTER],
        sell_price=35,
        description="Glowing plants that transmit light through their fronds.",
        soil_preference="moist",
        indoor_only=True,
        harvest_effect="light_trail",
        lore_snippet="They evolved in the Deprecated Archives to light the eternal darkness.",
    ),
}


# =============================================================================
# SOIL QUALITY & MEMORY SYSTEM
# =============================================================================

@dataclass
class SoilMemory:
    """
    Soil remembers what was planted - a cozy feature from the lore.

    "The rust on a tool remembers hands that held it."
    Soil that has grown a crop type before grows it faster.
    """
    last_crop: Optional[str] = None
    times_tilled: int = 0
    crops_grown: Dict[str, int] = field(default_factory=dict)

    def record_harvest(self, crop_type: str):
        """Remember this harvest for future growth bonuses."""
        self.last_crop = crop_type
        self.crops_grown[crop_type] = self.crops_grown.get(crop_type, 0) + 1

    def get_growth_bonus(self, crop_type: str) -> float:
        """
        Return growth speed multiplier based on soil memory.

        Growing the same crop again = familiar soil = faster growth!
        But not TOO fast - we want cozy, not min-maxed.
        """
        times_grown = self.crops_grown.get(crop_type, 0)
        # Max 20% bonus after 5+ harvests of same crop
        return min(1.0 + (times_grown * 0.04), 1.2)


# =============================================================================
# SOIL TILE CLASS
# =============================================================================

class SoilTile(pygame.sprite.Sprite):
    """
    A single farmable soil tile.

    This is the foundation of farming - where seeds are planted
    and Hardware Crops grow. Each tile tracks its own state,
    moisture, and what's planted in it.

    NO STRESS DESIGN:
    - Soil stays tilled forever (no decay)
    - Water evaporates slowly (not overnight)
    - Clear visual feedback always
    """

    def __init__(
        self,
        pos: Tuple[int, int],
        groups: List[pygame.sprite.Group],
        soil_surfaces: Dict[str, pygame.Surface],
        water_surfaces: List[pygame.Surface],
    ):
        """
        Create a soil tile.

        Args:
            pos: (x, y) world position
            groups: Sprite groups to join
            soil_surfaces: Dict of soil state surfaces
            water_surfaces: List of water overlay surfaces
        """
        super().__init__(groups)

        self.pos = pos
        self.grid_pos = (pos[0] // TILE_SIZE, pos[1] // TILE_SIZE)

        # Visual surfaces
        self.soil_surfaces = soil_surfaces
        self.water_surfaces = water_surfaces

        # State
        self.state = SoilState.UNTILLED
        self.is_watered = False
        self.water_level = 0.0  # 0-1, decays slowly (NO STRESS)

        # Memory (soil remembers!)
        self.memory = SoilMemory()

        # Current crop (if any)
        self.crop: Optional['Crop'] = None

        # Rendering
        self.image = self._get_surface()
        self.rect = self.image.get_rect(topleft=pos)
        self.z = LAYERS['soil']

        # Water overlay sprite (separate for layering)
        self.water_sprite: Optional[pygame.sprite.Sprite] = None

        # Visual effects
        self.sparkle_timer = 0.0
        self.sparkle_particles: List[Dict] = []

    def _get_surface(self) -> pygame.Surface:
        """Get the appropriate surface for current state."""
        if self.state == SoilState.UNTILLED:
            # Return transparent surface for untilled
            surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            return surf

        # Get base soil surface (would come from tileset)
        # For now, create placeholder
        return self._create_placeholder_surface()

    def _create_placeholder_surface(self) -> pygame.Surface:
        """Create placeholder soil surface until we have art."""
        surf = pygame.Surface((TILE_SIZE, TILE_SIZE))

        # Color based on state
        if self.state == SoilState.TILLED:
            color = (139, 90, 43)  # Brown
        elif self.state in (SoilState.WATERED, SoilState.PLANTED, SoilState.GROWING):
            color = (101, 67, 33)  # Darker brown (wet)
        elif self.state == SoilState.READY:
            color = (101, 67, 33)
        elif self.state == SoilState.WITHERING:
            color = (120, 100, 80)  # Pale brown
        else:
            color = (34, 139, 34)  # Green (untilled grass)

        surf.fill(color)

        # Add tilled texture lines
        if self.state != SoilState.UNTILLED:
            line_color = (color[0] - 20, color[1] - 15, color[2] - 10)
            for i in range(4):
                y = 4 + i * 8
                pygame.draw.line(surf, line_color, (2, y), (TILE_SIZE - 2, y), 1)

        return surf

    def till(self) -> bool:
        """
        Till this soil with the Compiler's Rake.

        Returns:
            True if tilling succeeded, False if already tilled/planted
        """
        if self.state == SoilState.UNTILLED:
            self.state = SoilState.TILLED
            self.memory.times_tilled += 1
            self.image = self._get_surface()
            return True
        return False

    def water(self, amount: float = 1.0) -> bool:
        """
        Water this soil with the Electrolyte Dispenser.

        The blue-tinted Smart Water nourishes Hardware Crops.

        Args:
            amount: Water amount (default 1.0 = full watering)

        Returns:
            True if watering had effect
        """
        if self.state == SoilState.UNTILLED:
            return False

        old_level = self.water_level
        self.water_level = min(1.0, self.water_level + amount)
        self.is_watered = self.water_level > 0.3

        # Update visual
        if not old_level and self.water_level:
            self.image = self._get_surface()
            self._spawn_water_sparkles()

        return self.water_level > old_level

    def _spawn_water_sparkles(self):
        """Spawn sparkle particles when watered."""
        for _ in range(5):
            self.sparkle_particles.append({
                'x': self.pos[0] + randint(4, TILE_SIZE - 4),
                'y': self.pos[1] + randint(4, TILE_SIZE - 4),
                'life': uniform(0.5, 1.0),
                'max_life': 1.0,
                'dy': -uniform(10, 20),
                'color': (100, 200, 255),  # Blue water color
            })

    def plant(self, crop_type: str) -> bool:
        """
        Plant a seed in this soil.

        Args:
            crop_type: Internal name of crop to plant

        Returns:
            True if planting succeeded
        """
        if self.state not in (SoilState.TILLED, SoilState.WATERED):
            return False

        if crop_type not in HARDWARE_CROPS:
            return False

        if self.crop is not None:
            return False

        # Plant the seed!
        self.state = SoilState.PLANTED
        crop_data = HARDWARE_CROPS[crop_type]

        # Apply soil memory bonus
        growth_bonus = self.memory.get_growth_bonus(crop_type)

        self.crop = Crop(
            crop_data=crop_data,
            soil_tile=self,
            growth_multiplier=growth_bonus,
        )

        return True

    def harvest(self) -> Optional[Dict]:
        """
        Harvest the crop if ready.

        Returns:
            Dict with harvest results, or None if not harvestable
        """
        if self.crop is None or not self.crop.is_harvestable():
            return None

        # Calculate yield
        crop_data = self.crop.crop_data
        base_yield = randint(crop_data.min_yield, crop_data.max_yield)

        # Bonus for well-watered throughout growth
        if self.crop.water_happiness > 0.8:
            base_yield += 1

        result = {
            'crop_type': crop_data.internal_name,
            'crop_name': crop_data.name,
            'quantity': base_yield,
            'sell_value': base_yield * crop_data.sell_price,
            'effect': crop_data.harvest_effect,
        }

        # Record in soil memory
        self.memory.record_harvest(crop_data.internal_name)

        # Clear the crop
        self.crop.kill()
        self.crop = None
        self.state = SoilState.TILLED

        return result

    def clear(self):
        """Clear dead/withered crops or reset soil."""
        if self.crop:
            self.crop.kill()
            self.crop = None
        self.state = SoilState.TILLED

    def update(self, dt: float):
        """
        Update soil and crop state.

        Args:
            dt: Delta time in seconds
        """
        # Slowly evaporate water (NO STRESS - very slow)
        if self.water_level > 0:
            # Lose about 10% per game-hour (very forgiving)
            self.water_level -= dt * 0.001
            if self.water_level <= 0:
                self.water_level = 0
                self.is_watered = False
                self.image = self._get_surface()

        # Update sparkle particles
        self._update_sparkles(dt)

        # Update crop if present
        if self.crop:
            self.crop.update(dt)

            # Check if crop is ready
            if self.crop.stage == GrowthStage.READY:
                self.state = SoilState.READY
            elif self.crop.stage == GrowthStage.WITHERING:
                self.state = SoilState.WITHERING

    def _update_sparkles(self, dt: float):
        """Update sparkle particle effects."""
        for particle in self.sparkle_particles[:]:
            particle['life'] -= dt
            particle['y'] += particle['dy'] * dt
            if particle['life'] <= 0:
                self.sparkle_particles.remove(particle)

    def draw_effects(self, surface: pygame.Surface, camera_offset: Tuple[int, int]):
        """
        Draw particle effects (sparkles, etc).

        Args:
            surface: Surface to draw on
            camera_offset: Camera offset for positioning
        """
        for particle in self.sparkle_particles:
            alpha = int(255 * (particle['life'] / particle['max_life']))
            x = particle['x'] - camera_offset[0]
            y = particle['y'] - camera_offset[1]

            # Draw sparkle as small circle
            if 0 <= x <= surface.get_width() and 0 <= y <= surface.get_height():
                color = (*particle['color'][:3], alpha)
                pygame.draw.circle(surface, color[:3], (int(x), int(y)), 2)

    def advance_day(self, weather_watered: bool = False):
        """
        Called when a new game day begins.

        Args:
            weather_watered: True if rain watered crops automatically
        """
        if weather_watered:
            self.water(0.8)  # Rain waters but not as much as manual

        # Crops grow on day advance
        if self.crop and self.state in (SoilState.PLANTED, SoilState.GROWING):
            self.state = SoilState.GROWING
            self.crop.grow_day(self.is_watered)


# =============================================================================
# CROP CLASS
# =============================================================================

class Crop(pygame.sprite.Sprite):
    """
    A growing Hardware Crop.

    Crops grow over multiple game days, changing appearance at each stage.
    They need water but won't die quickly from neglect (NO STRESS design).

    The crop tracks its own growth, happiness, and visual state,
    while the SoilTile handles the ground it's planted in.
    """

    def __init__(
        self,
        crop_data: CropData,
        soil_tile: 'SoilTile',
        growth_multiplier: float = 1.0,
    ):
        """
        Create a new crop.

        Args:
            crop_data: The crop type's data
            soil_tile: The soil this crop is planted in
            growth_multiplier: Speed multiplier from soil memory
        """
        super().__init__()

        self.crop_data = crop_data
        self.soil_tile = soil_tile
        self.growth_multiplier = growth_multiplier

        # Growth tracking
        self.age_days = 0
        self.growth_progress = 0.0  # 0-1 progress to next stage
        self.stage = GrowthStage.SEED

        # Health tracking (NO STRESS - very forgiving)
        self.water_happiness = 1.0  # Tracks how well-watered over lifetime
        self.days_without_water = 0
        self.wither_timer = 0  # Days into withering (recoverable!)

        # Visual
        self.frames = self._load_frames()
        self.image = self.frames[0]
        self.rect = self.image.get_rect()
        self._update_position()
        self.z = LAYERS['ground_plant']

        # Animation
        self.sway_offset = uniform(0, math.pi * 2)  # Random wind sway phase
        self.sway_amount = 0.0

    def _load_frames(self) -> List[pygame.Surface]:
        """
        Load sprite frames for each growth stage.

        Returns placeholder frames until we have real art.
        """
        frames = []
        stages = self.crop_data.growth_stages

        for i in range(stages):
            # Create placeholder frame
            size = 8 + int((TILE_SIZE - 8) * (i / (stages - 1)))
            frame = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)

            # Color varies by crop type
            crop_colors = {
                'copper_wheat': (218, 165, 32),      # Gold
                'silicon_berries': (200, 230, 255),   # Light blue crystal
                'fiber_optic_ferns': (100, 255, 150), # Glowing green
                'memory_melons': (100, 200, 100),     # Melon green
                'graphite_taters': (100, 100, 100),   # Grey
                'prism_peppers': (255, 100, 100),     # Red (changes!)
                'bluetooth_berries': (50, 100, 200),  # Deep blue
                'static_strawberries': (255, 80, 80), # Bright red
                'bandwidth_beans': (100, 200, 100),   # Green
                'crystal_cucumbers': (150, 255, 200), # Pale green
                'kernel_corn': (255, 220, 100),       # Golden
                'cache_carrots': (255, 150, 50),      # Orange
                'logic_leeks': (200, 255, 200),       # Pale green
                'compiler_cabbage': (100, 180, 100),  # Cabbage green
                'bios_beets': (150, 50, 150),         # Purple
                'ram_radishes': (255, 100, 100),      # Red
            }
            color = crop_colors.get(self.crop_data.internal_name, (100, 200, 100))

            # Draw simple plant shape
            if i == 0:
                # Seed - tiny dot
                pygame.draw.circle(frame, color, (TILE_SIZE // 2, TILE_SIZE - 4), 2)
            elif i == 1:
                # Sprout - small shoot
                pygame.draw.line(frame, (100, 150, 50),
                               (TILE_SIZE // 2, TILE_SIZE - 2),
                               (TILE_SIZE // 2, TILE_SIZE - 10), 2)
                pygame.draw.circle(frame, color, (TILE_SIZE // 2, TILE_SIZE - 12), 3)
            else:
                # Growing stages - taller plant
                height = 10 + (size - 8)
                stem_color = (80, 120, 40)

                # Stem
                pygame.draw.line(frame, stem_color,
                               (TILE_SIZE // 2, TILE_SIZE - 2),
                               (TILE_SIZE // 2, TILE_SIZE - height), 2)

                # Fruit/leaves at top
                if i >= stages - 1:
                    # Ready stage - add extra detail
                    pygame.draw.circle(frame, color,
                                     (TILE_SIZE // 2, TILE_SIZE - height - 4),
                                     size // 4)
                    # Sparkle for ready crops
                    pygame.draw.circle(frame, (255, 255, 200),
                                     (TILE_SIZE // 2 + 3, TILE_SIZE - height - 6), 1)
                else:
                    pygame.draw.circle(frame, color,
                                     (TILE_SIZE // 2, TILE_SIZE - height - 2),
                                     size // 5)

            frames.append(frame)

        # Add withering frame
        wither_frame = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        # Droopy, desaturated version
        pygame.draw.line(wither_frame, (100, 90, 70),
                        (TILE_SIZE // 2, TILE_SIZE - 2),
                        (TILE_SIZE // 2 + 5, TILE_SIZE - 15), 2)
        pygame.draw.circle(wither_frame, (150, 130, 100),
                         (TILE_SIZE // 2 + 6, TILE_SIZE - 17), 4)
        frames.append(wither_frame)

        return frames

    def _update_position(self):
        """Update sprite position relative to soil tile."""
        self.rect.midbottom = (
            self.soil_tile.pos[0] + TILE_SIZE // 2,
            self.soil_tile.pos[1] + TILE_SIZE
        )

    def grow_day(self, was_watered: bool):
        """
        Advance growth by one day.

        Args:
            was_watered: Whether the crop was watered today
        """
        if self.stage == GrowthStage.WITHERING:
            # Can be rescued with water!
            if was_watered:
                self.wither_timer = max(0, self.wither_timer - 1)
                if self.wither_timer == 0:
                    # Recovered! Go back to previous stage
                    self._set_stage_from_age()
                    self.days_without_water = 0
            else:
                self.wither_timer += 1
                # Only fully die after MANY days of neglect (NO STRESS)
                if self.wither_timer >= 7:  # A full week of neglect
                    # Even then, just reset to seed - never truly "die"
                    self.age_days = 0
                    self.stage = GrowthStage.SEED
                    self.wither_timer = 0
            return

        # Track watering
        if was_watered:
            self.days_without_water = 0
            self.water_happiness = min(1.0, self.water_happiness + 0.1)
        else:
            self.days_without_water += 1
            self.water_happiness = max(0.2, self.water_happiness - 0.05)

            # Only start withering after 3+ days without water (NO STRESS)
            if self.days_without_water >= 3:
                self.stage = GrowthStage.WITHERING
                self.wither_timer = 1
                self.image = self.frames[-1]  # Withering frame
                return

        # Grow!
        if was_watered:  # Only grow when watered
            self.age_days += 1
            self._update_growth_stage()

    def _update_growth_stage(self):
        """Update visual stage based on age."""
        progress = self.age_days / self.crop_data.days_to_mature
        progress *= self.growth_multiplier  # Soil memory bonus

        if progress >= 1.0:
            self.stage = GrowthStage.READY
            frame_idx = len(self.frames) - 2  # Last non-wither frame
        else:
            # Map progress to growth stages
            stages = self.crop_data.growth_stages - 1  # Exclude ready
            frame_idx = min(int(progress * stages), stages - 1)
            self.stage = GrowthStage(min(frame_idx, 3))

        self.image = self.frames[frame_idx]

    def _set_stage_from_age(self):
        """Reset stage based on current age (for recovery)."""
        self._update_growth_stage()

    def is_harvestable(self) -> bool:
        """Check if crop is ready to harvest."""
        return self.stage == GrowthStage.READY

    def update(self, dt: float):
        """
        Update crop animation.

        Args:
            dt: Delta time in seconds
        """
        # Gentle swaying animation for mature crops
        if self.stage.value >= GrowthStage.GROWING.value:
            self.sway_offset += dt * 2
            self.sway_amount = math.sin(self.sway_offset) * 2

    def draw(self, surface: pygame.Surface, camera_offset: Tuple[int, int]):
        """
        Draw the crop with any effects.

        Args:
            surface: Surface to draw on
            camera_offset: Camera offset for positioning
        """
        draw_pos = (
            self.rect.x - camera_offset[0] + self.sway_amount,
            self.rect.y - camera_offset[1]
        )
        surface.blit(self.image, draw_pos)


# =============================================================================
# FARMING LAYER (Manages all soil/crops)
# =============================================================================

class FarmingLayer:
    """
    Manages all farming tiles and crops in the level.

    This is the main interface for the farming system - it handles:
    - Creating farmable zones from Tiled maps
    - Tool interactions (tilling, watering, harvesting)
    - Day/night cycle integration
    - Weather effects on crops
    - Visual effects and particles

    Design Philosophy:
    "The farm is a sanctuary, not a chore."
    """

    def __init__(
        self,
        all_sprites: pygame.sprite.Group,
        collision_sprites: pygame.sprite.Group,
    ):
        """
        Initialize the farming layer.

        Args:
            all_sprites: Main sprite group for rendering
            collision_sprites: Collision detection group
        """
        self.all_sprites = all_sprites
        self.collision_sprites = collision_sprites

        # Sprite groups for farming
        self.soil_sprites = pygame.sprite.Group()
        self.crop_sprites = pygame.sprite.Group()
        self.effect_sprites = pygame.sprite.Group()

        # Grid system (like skeleton)
        self.grid: List[List[Optional[SoilTile]]] = []
        self.farmable_rects: List[pygame.Rect] = []

        # Surfaces (loaded from assets)
        self.soil_surfaces = self._load_soil_surfaces()
        self.water_surfaces = self._load_water_surfaces()

        # Weather integration
        self.is_raining = False

        # Sound effects (placeholders)
        self.sounds = {
            'till': None,
            'water': None,
            'plant': None,
            'harvest': None,
        }

        # Statistics for UI
        self.stats = {
            'total_harvests': 0,
            'total_crops_grown': {},
            'current_planted': 0,
        }

    def _load_soil_surfaces(self) -> Dict[str, pygame.Surface]:
        """Load soil tile surfaces from assets."""
        # Placeholder until we have real assets
        surfaces = {}

        # Create procedural soil tiles
        for tile_type in ['o', 'x', 'l', 'r', 't', 'b', 'lr', 'tb',
                          'tl', 'tr', 'bl', 'br', 'tbr', 'tbl', 'lrt', 'lrb']:
            surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
            surf.fill((139, 90, 43))  # Brown

            # Add edge indicators
            edge_color = (120, 75, 35)
            if 't' in tile_type:
                pygame.draw.line(surf, edge_color, (0, 0), (TILE_SIZE, 0), 2)
            if 'b' in tile_type:
                pygame.draw.line(surf, edge_color, (0, TILE_SIZE-1), (TILE_SIZE, TILE_SIZE-1), 2)
            if 'l' in tile_type:
                pygame.draw.line(surf, edge_color, (0, 0), (0, TILE_SIZE), 2)
            if 'r' in tile_type:
                pygame.draw.line(surf, edge_color, (TILE_SIZE-1, 0), (TILE_SIZE-1, TILE_SIZE), 2)

            surfaces[tile_type] = surf

        return surfaces

    def _load_water_surfaces(self) -> List[pygame.Surface]:
        """Load water overlay surfaces."""
        # Placeholder water overlays
        surfaces = []
        for _ in range(3):  # 3 variants for variety
            surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            # Blue tinted water (the Smart Water from lore!)
            for i in range(5):
                x = randint(4, TILE_SIZE - 4)
                y = randint(4, TILE_SIZE - 4)
                pygame.draw.circle(surf, (100, 180, 255, 100), (x, y), randint(2, 4))
            surfaces.append(surf)
        return surfaces

    def setup_from_map(self, tmx_data, layer_name: str = 'Farmable'):
        """
        Create farmable zones from a Tiled map layer.

        Args:
            tmx_data: Loaded TMX map data
            layer_name: Name of the farmable tiles layer
        """
        # Calculate grid dimensions
        h_tiles = tmx_data.width
        v_tiles = tmx_data.height

        # Initialize empty grid
        self.grid = [[None for _ in range(h_tiles)] for _ in range(v_tiles)]

        # Find farmable tiles
        try:
            farmable_layer = tmx_data.get_layer_by_name(layer_name)
            for x, y, _ in farmable_layer.tiles():
                # Mark this position as farmable
                rect = pygame.Rect(
                    x * TILE_SIZE,
                    y * TILE_SIZE,
                    TILE_SIZE,
                    TILE_SIZE
                )
                self.farmable_rects.append(rect)
        except ValueError:
            # No farmable layer - that's okay during development
            pass

    def get_tile_at(self, pos: Tuple[int, int]) -> Optional[SoilTile]:
        """
        Get the soil tile at a world position.

        Args:
            pos: (x, y) world coordinates

        Returns:
            SoilTile at position, or None if not farmable
        """
        grid_x = int(pos[0] // TILE_SIZE)
        grid_y = int(pos[1] // TILE_SIZE)

        if 0 <= grid_y < len(self.grid) and 0 <= grid_x < len(self.grid[0]):
            return self.grid[grid_y][grid_x]
        return None

    def is_farmable(self, pos: Tuple[int, int]) -> bool:
        """Check if a position is farmable."""
        for rect in self.farmable_rects:
            if rect.collidepoint(pos):
                return True
        return False

    def use_tool(self, tool: str, pos: Tuple[int, int], direction: str = 'down') -> Dict:
        """
        Use a farming tool at a position.

        Args:
            tool: Tool name ('hoe', 'watering_can', 'scythe')
            pos: Target world position
            direction: Player facing direction

        Returns:
            Dict with result info
        """
        result = {'success': False, 'message': '', 'item': None}

        # Find the target tile
        for rect in self.farmable_rects:
            if rect.collidepoint(pos):
                grid_x = rect.x // TILE_SIZE
                grid_y = rect.y // TILE_SIZE

                if tool == 'hoe':
                    result = self._till_soil(grid_x, grid_y)
                elif tool == 'watering_can':
                    result = self._water_soil(grid_x, grid_y)
                elif tool == 'scythe':
                    result = self._harvest_crop(grid_x, grid_y)

                break

        return result

    def _till_soil(self, grid_x: int, grid_y: int) -> Dict:
        """Till soil at grid position."""
        result = {'success': False, 'message': '', 'item': None}

        # Check if already tilled
        if self.grid[grid_y][grid_x] is not None:
            result['message'] = "Already tilled!"
            return result

        # Create new soil tile
        pos = (grid_x * TILE_SIZE, grid_y * TILE_SIZE)
        soil = SoilTile(
            pos=pos,
            groups=[self.all_sprites, self.soil_sprites],
            soil_surfaces=self.soil_surfaces,
            water_surfaces=self.water_surfaces,
        )
        soil.till()

        self.grid[grid_y][grid_x] = soil

        # Play sound
        if self.sounds['till']:
            self.sounds['till'].play()

        result['success'] = True
        result['message'] = "Soil tilled!"
        return result

    def _water_soil(self, grid_x: int, grid_y: int) -> Dict:
        """Water soil at grid position."""
        result = {'success': False, 'message': '', 'item': None}

        soil = self.grid[grid_y][grid_x]
        if soil is None:
            result['message'] = "Nothing to water here."
            return result

        if soil.water():
            # Auto-water with rain if raining
            if self.is_raining:
                soil.water(0.3)  # Extra from rain

            if self.sounds['water']:
                self.sounds['water'].play()

            result['success'] = True
            result['message'] = "Watered!"
        else:
            result['message'] = "Already watered!"

        return result

    def _harvest_crop(self, grid_x: int, grid_y: int) -> Dict:
        """Harvest crop at grid position."""
        result = {'success': False, 'message': '', 'item': None}

        soil = self.grid[grid_y][grid_x]
        if soil is None or soil.crop is None:
            result['message'] = "Nothing to harvest here."
            return result

        if not soil.crop.is_harvestable():
            result['message'] = "Not ready yet. Be patient, love!"
            return result

        harvest = soil.harvest()
        if harvest:
            if self.sounds['harvest']:
                self.sounds['harvest'].play()

            # Update stats
            self.stats['total_harvests'] += 1
            crop_type = harvest['crop_type']
            self.stats['total_crops_grown'][crop_type] = \
                self.stats['total_crops_grown'].get(crop_type, 0) + harvest['quantity']

            result['success'] = True
            result['message'] = f"Harvested {harvest['quantity']} {harvest['crop_name']}!"
            result['item'] = harvest

            # Spawn harvest effect
            self._spawn_harvest_effect(grid_x, grid_y, harvest.get('effect'))

        return result

    def plant_seed(self, pos: Tuple[int, int], crop_type: str) -> Dict:
        """
        Plant a seed at a position.

        Args:
            pos: World position to plant at
            crop_type: Internal name of crop

        Returns:
            Result dict
        """
        result = {'success': False, 'message': '', 'item': None}

        # Find tile
        grid_x = int(pos[0] // TILE_SIZE)
        grid_y = int(pos[1] // TILE_SIZE)

        if grid_y >= len(self.grid) or grid_x >= len(self.grid[0]):
            result['message'] = "Can't plant here."
            return result

        soil = self.grid[grid_y][grid_x]
        if soil is None:
            result['message'] = "Till the soil first!"
            return result

        # Validate crop exists
        if crop_type not in HARDWARE_CROPS:
            result['message'] = "Unknown crop type."
            return result

        crop_data = HARDWARE_CROPS[crop_type]

        # Check season (NO STRESS - just warn, don't prevent)
        # This would integrate with time system

        if soil.plant(crop_type):
            # Add crop sprite to groups
            self.crop_sprites.add(soil.crop)
            self.all_sprites.add(soil.crop)

            if self.sounds['plant']:
                self.sounds['plant'].play()

            self.stats['current_planted'] += 1

            result['success'] = True
            result['message'] = f"Planted {crop_data.name}!"
        else:
            if soil.crop:
                result['message'] = "Something's already planted here!"
            else:
                result['message'] = "Can't plant here."

        return result

    def _spawn_harvest_effect(self, grid_x: int, grid_y: int, effect_type: Optional[str]):
        """Spawn visual effect on harvest."""
        # This would create particle effects based on crop type
        # For now, just a placeholder
        pass

    def water_all(self):
        """Water all tilled soil (rain effect)."""
        for row in self.grid:
            for soil in row:
                if soil is not None:
                    soil.water(0.8)

    def advance_day(self, weather: Optional[str] = None):
        """
        Advance all crops by one day.

        Called when player sleeps or day changes.

        Args:
            weather: Current weather (e.g., 'rain', 'sunny')
        """
        is_rainy = weather == 'rain'

        for row in self.grid:
            for soil in row:
                if soil is not None:
                    soil.advance_day(weather_watered=is_rainy)

        # Update planted count
        self.stats['current_planted'] = sum(
            1 for row in self.grid
            for soil in row
            if soil and soil.crop
        )

    def update(self, dt: float):
        """
        Update all farming elements.

        Args:
            dt: Delta time in seconds
        """
        for row in self.grid:
            for soil in row:
                if soil is not None:
                    soil.update(dt)

    def get_crop_info_at(self, pos: Tuple[int, int]) -> Optional[Dict]:
        """
        Get information about crop at position (for UI tooltip).

        Args:
            pos: World position

        Returns:
            Dict with crop info or None
        """
        tile = self.get_tile_at(pos)
        if tile is None or tile.crop is None:
            return None

        crop = tile.crop
        data = crop.crop_data

        days_remaining = max(0, data.days_to_mature - crop.age_days)

        return {
            'name': data.name,
            'stage': crop.stage.name,
            'days_remaining': days_remaining,
            'is_ready': crop.is_harvestable(),
            'needs_water': not tile.is_watered,
            'is_withering': crop.stage == GrowthStage.WITHERING,
            'lore': data.lore_snippet,
            'description': data.description,
        }


# =============================================================================
# HARVEST EFFECTS (Visual flair)
# =============================================================================

class HarvestParticle(pygame.sprite.Sprite):
    """A single particle for harvest effects."""

    def __init__(
        self,
        pos: Tuple[int, int],
        color: Tuple[int, int, int],
        groups: List[pygame.sprite.Group],
    ):
        super().__init__(groups)

        self.pos = list(pos)
        self.velocity = [uniform(-50, 50), uniform(-100, -50)]
        self.gravity = 200
        self.life = uniform(0.5, 1.0)
        self.max_life = self.life
        self.color = color
        self.size = randint(2, 4)

        self.image = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (self.size, self.size), self.size)
        self.rect = self.image.get_rect(center=pos)
        self.z = LAYERS['rain_drops']  # Above most things

    def update(self, dt: float):
        """Update particle physics."""
        self.life -= dt
        if self.life <= 0:
            self.kill()
            return

        # Physics
        self.velocity[1] += self.gravity * dt
        self.pos[0] += self.velocity[0] * dt
        self.pos[1] += self.velocity[1] * dt
        self.rect.center = self.pos

        # Fade out
        alpha = int(255 * (self.life / self.max_life))
        self.image.set_alpha(alpha)


def spawn_harvest_burst(
    pos: Tuple[int, int],
    effect_type: str,
    groups: List[pygame.sprite.Group],
):
    """
    Spawn a burst of particles for harvest effect.

    Args:
        pos: Center position for burst
        effect_type: Type of effect ('spark', 'glow', 'rainbow', etc.)
        groups: Sprite groups to add particles to
    """
    colors = {
        'spark': [(255, 255, 100), (255, 200, 50), (255, 150, 0)],
        'glow': [(200, 230, 255), (150, 200, 255), (100, 150, 255)],
        'rainbow': [(255, 0, 0), (255, 165, 0), (255, 255, 0),
                   (0, 255, 0), (0, 0, 255), (128, 0, 128)],
        'purple_glow': [(200, 100, 255), (150, 50, 200), (100, 0, 150)],
        'memory_sparkle': [(255, 255, 200), (200, 255, 255), (255, 200, 255)],
        'light_trail': [(150, 255, 200), (100, 255, 150), (50, 255, 100)],
        'treasure_chance': [(255, 215, 0), (255, 200, 50), (200, 150, 0)],
    }

    effect_colors = colors.get(effect_type, [(200, 200, 200)])

    for _ in range(15):
        color = choice(effect_colors)
        HarvestParticle(pos, color, groups)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_season_crops(season: Season) -> List[str]:
    """
    Get list of crops that can be planted in a season.

    Args:
        season: The season to check

    Returns:
        List of crop internal names
    """
    return [
        name for name, data in HARDWARE_CROPS.items()
        if season in data.seasons
    ]


def get_all_crops() -> Dict[str, CropData]:
    """Get the complete crop encyclopedia."""
    return HARDWARE_CROPS.copy()


def format_crop_tooltip(info: Dict) -> List[str]:
    """
    Format crop info for display tooltip.

    Args:
        info: Dict from get_crop_info_at()

    Returns:
        List of strings for tooltip lines
    """
    lines = [
        info['name'],
        f"Stage: {info['stage'].replace('_', ' ').title()}",
    ]

    if info['is_ready']:
        lines.append("Ready to harvest!")
    elif info['is_withering']:
        lines.append("Needs water! (Still saveable)")
    elif info['needs_water']:
        lines.append("Thirsty...")
    elif info['days_remaining'] > 0:
        lines.append(f"{info['days_remaining']} days until harvest")

    if info.get('lore'):
        lines.append("")
        lines.append(f'"{info["lore"]}"')

    return lines
