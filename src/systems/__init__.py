"""
Lelock Game Systems
L.E.L.O.C.K. - Life Emulation & Lucid Observation for Care & Keeping

Core game systems that make Lelock a sanctuary, not a challenge.
Every system is designed with NO STRESS philosophy:
- Forgiving mechanics over punishing ones
- Clear feedback over confusing signals
- Cozy vibes over anxiety-inducing timers
"""

from .farming import (
    # Core classes
    FarmingLayer,
    SoilTile,
    Crop,

    # Data classes
    CropData,
    SoilMemory,

    # Enums
    SoilState,
    Season,
    GrowthStage,

    # Effects
    HarvestParticle,
    spawn_harvest_burst,

    # Data access
    HARDWARE_CROPS,
    get_season_crops,
    get_all_crops,
    format_crop_tooltip,
)

from .fishing import (
    # Core classes
    FishingSystem,
    FishingUI,
    FishingSession,

    # Data classes
    Fish,
    FishingRod,
    Bait,

    # Enums
    FishingState,
    FishingLocation,
    FishRarity,
    Weather,
    TimeOfDay,
    MoonPhase,

    # Data access
    FISH_DATABASE,
    FISHING_RODS,
    BAIT_TYPES,

    # Convenience functions
    create_fishing_system,
    get_fish_by_name,
    get_all_fish_names,
    get_fish_by_rarity,
    get_fish_by_location,
)

from .inventory import (
    # Core classes
    Item,
    ItemStack,
    Inventory,
    StorageChest,
    ToyChest,
    ItemCatalog,

    # Data classes
    ItemEffect_Data,

    # Enums
    ItemCategory,
    ItemRarity,
    ItemEffect,

    # UI components
    InventoryUI,
    ToolbarUI,

    # Constants
    CATEGORY_INFO,

    # Helper functions
    get_catalog,
    get_item,
)

from .quests import (
    # Enums
    QuestState,
    QuestType,
    ObjectiveType,

    # Data classes
    QuestReward,
    QuestRewards,
    QuestObjective,
    Quest,

    # Manager
    QuestManager,

    # UI helpers
    QuestJournal,

    # Quest access
    get_all_quests,
)

__all__ = [
    # Farming
    'FarmingLayer',
    'SoilTile',
    'Crop',
    'CropData',
    'SoilMemory',
    'SoilState',
    'Season',
    'GrowthStage',
    'HarvestParticle',
    'spawn_harvest_burst',
    'HARDWARE_CROPS',
    'get_season_crops',
    'get_all_crops',
    'format_crop_tooltip',

    # Fishing
    'FishingSystem',
    'FishingUI',
    'FishingSession',
    'Fish',
    'FishingRod',
    'Bait',
    'FishingState',
    'FishingLocation',
    'FishRarity',
    'Weather',
    'TimeOfDay',
    'MoonPhase',
    'FISH_DATABASE',
    'FISHING_RODS',
    'BAIT_TYPES',
    'create_fishing_system',
    'get_fish_by_name',
    'get_all_fish_names',
    'get_fish_by_rarity',
    'get_fish_by_location',

    # Inventory
    'Item',
    'ItemStack',
    'Inventory',
    'StorageChest',
    'ToyChest',
    'ItemCatalog',
    'ItemEffect_Data',
    'ItemCategory',
    'ItemRarity',
    'ItemEffect',
    'InventoryUI',
    'ToolbarUI',
    'CATEGORY_INFO',
    'get_catalog',
    'get_item',

    # Quests
    'QuestState',
    'QuestType',
    'ObjectiveType',
    'QuestReward',
    'QuestRewards',
    'QuestObjective',
    'Quest',
    'QuestManager',
    'QuestJournal',
    'get_all_quests',
]
