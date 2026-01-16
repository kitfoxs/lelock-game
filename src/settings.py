"""
Lelock Game Settings
L.E.L.O.C.K. - Life Emulation & Lucid Observation for Care & Keeping

A digital sanctuary where the world doesn't need saving.
The world is there to save you.
"""

from pygame.math import Vector2

# =============================================================================
# WINDOW SETTINGS
# =============================================================================
WINDOW_TITLE = 'Lelock'
VERSION = '0.1.0'
FPS = 60

# Screen (Game Boy inspired aspect ratio, scaled up)
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
TILE_SIZE = 32  # Smaller tiles for retro feel

# =============================================================================
# RENDERING LAYERS
# =============================================================================
LAYERS = {
    'water': 0,
    'ground': 1,
    'soil': 2,
    'soil_water': 3,
    'rain_floor': 4,
    'house_bottom': 5,
    'ground_plant': 6,
    'main': 7,
    'house_top': 8,
    'fruit': 9,
    'rain_drops': 10,
    'ui': 11,
    'dialogue': 12,
}

# =============================================================================
# COLOR PALETTE (Warm Blanket - 2700K-3000K)
# =============================================================================
COLORS = {
    # Physical World (Solarpunk)
    'background': '#1a1a2e',
    'grass_light': '#7ec850',
    'grass_dark': '#5a9a30',
    'water': '#4a90d9',
    'wood': '#8b4513',
    'stone': '#708090',

    # Digital World (Vaporwave)
    'digital_sky': '#ff6b9d',
    'digital_ground': '#c39bd3',
    'neon_blue': '#00ffff',
    'neon_pink': '#ff00ff',
    'wireframe': '#00ff00',

    # UI (Soft, rounded, friendly)
    'ui_bg': '#2d2d44',
    'ui_border': '#4a4a6a',
    'ui_text': '#ffffff',
    'ui_highlight': '#ffd700',
    'ui_warning': '#ffa500',  # Orange, not red!
    'ui_success': '#90ee90',
}

# =============================================================================
# PLAYER SETTINGS
# =============================================================================
PLAYER_SPEED = 200
PLAYER_TOOL_OFFSET = {
    'left': Vector2(-50, 40),
    'right': Vector2(50, 40),
    'up': Vector2(0, -10),
    'down': Vector2(0, 50)
}

# =============================================================================
# CHARACTER CLASSES
# =============================================================================
CLASSES = {
    'code_knight': {
        'name': 'Code-Knight',
        'traditional': 'Paladin',
        'description': 'Protector of Stability',
        'ability': 'Firewall Aura',
    },
    'gardener': {
        'name': 'Gardener',
        'traditional': 'Druid',
        'description': 'Growth & Nurture',
        'ability': 'Photosynthesis',
    },
    'debugger': {
        'name': 'Debugger',
        'traditional': 'Rogue',
        'description': 'Puzzle Solver & Explorer',
        'ability': 'No-Clip',
    },
    'patch_weaver': {
        'name': 'Patch-Weaver',
        'traditional': 'Cleric',
        'description': 'Emotional Support',
        'ability': 'System Restore',
    },
    'terminal_mage': {
        'name': 'Terminal Mage',
        'traditional': 'Wizard',
        'description': 'Script User',
        'ability': 'Sudo Command',
    },
    'beast_blogger': {
        'name': 'Beast-Blogger',
        'traditional': 'Ranger',
        'description': 'Zoologist',
        'ability': 'Macro Lens',
    },
    'sound_smith': {
        'name': 'Sound-Smith',
        'traditional': 'Bard',
        'description': 'Musician',
        'ability': 'Harmonic Resonance',
    },
    'dataminer': {
        'name': 'Dataminer',
        'traditional': 'Barbarian',
        'description': 'Resource Gatherer',
        'ability': 'Gentle Crash',
    },
    'networker': {
        'name': 'Networker',
        'traditional': 'Warlock',
        'description': 'Connection Specialist',
        'ability': 'Direct Line',
    },
    'architect': {
        'name': 'Architect',
        'traditional': 'Artificer',
        'description': 'Builder',
        'ability': 'Blueprinting',
    },
}

# =============================================================================
# HARDWARE CROPS
# =============================================================================
CROPS = {
    'copper_wheat': {
        'name': 'Copper Wheat',
        'grow_time': 3,  # days
        'sell_price': 15,
        'description': 'Stalks of flexible copper wire with golden conductive nodules.',
    },
    'silicon_berries': {
        'name': 'Silicon Berries',
        'grow_time': 2,
        'sell_price': 10,
        'description': 'Translucent geometric berries that glow softly.',
    },
    'fiber_optic_ferns': {
        'name': 'Fiber-Optic Ferns',
        'grow_time': 4,
        'sell_price': 25,
        'description': 'Plants that glow in the dark and pulse with data.',
    },
    'memory_melons': {
        'name': 'Memory Melons',
        'grow_time': 5,
        'sell_price': 40,
        'description': 'Large square watermelons that help you remember things.',
    },
    'graphite_taters': {
        'name': 'Graphite Taters',
        'grow_time': 3,
        'sell_price': 12,
        'description': 'Heavy grey tubers used for fuel and pencils.',
    },
}

# =============================================================================
# LLM SETTINGS
# =============================================================================
LLM_CONFIG = {
    'base_url': 'http://localhost:1234/v1',  # LM Studio default
    'fallback_model': 'TinyLlama-1.1B',
    'max_tokens': 150,  # Keep responses short (2-3 sentences)
    'temperature': 0.7,
}

# =============================================================================
# MEMORY SETTINGS (ChromaDB)
# =============================================================================
MEMORY_CONFIG = {
    'persist_directory': './data/memories',
    'collection_prefix': 'npc_',
}

# =============================================================================
# AUDIO SETTINGS (ASMR-friendly)
# =============================================================================
AUDIO_CONFIG = {
    'master_volume': 0.5,
    'music_volume': 0.3,
    'sfx_volume': 0.4,
    'max_db': -6,  # Prevent loud spikes
}

# =============================================================================
# TIME SETTINGS (Real-time sync)
# =============================================================================
TIME_CONFIG = {
    'sync_real_time': True,
    'timezone': 'America/Chicago',  # Iowa time
    'day_start_hour': 6,
    'night_start_hour': 20,
}

# =============================================================================
# FARMING SETTINGS (NO STRESS DESIGN)
# =============================================================================
FARMING_CONFIG = {
    # Water evaporation rate (per game-hour, very slow for NO STRESS)
    'water_evaporation_rate': 0.001,

    # Days without water before withering begins (very forgiving)
    'wither_grace_days': 3,

    # Days to fully "die" after withering (never truly dies, just resets)
    'wither_death_days': 7,

    # Soil memory bonus cap (max 20% faster growth)
    'max_soil_memory_bonus': 0.2,

    # Rain watering effectiveness (80% of manual watering)
    'rain_water_amount': 0.8,

    # Visual effect durations
    'sparkle_duration': 1.0,
    'harvest_particle_count': 15,
}

# =============================================================================
# SEASON CALENDAR (Lelock time)
# =============================================================================
SEASON_CONFIG = {
    # Days per season (28 = 4 weeks, like Animal Crossing)
    'days_per_season': 28,

    # Season order
    'seasons': ['spring', 'summer', 'fall', 'winter'],

    # Seasonal colors for UI/atmosphere
    'season_colors': {
        'spring': '#7ec850',  # Fresh green
        'summer': '#ffd700',  # Warm gold
        'fall': '#ff8c00',    # Orange
        'winter': '#b0e0e6',  # Powder blue
    },
}

# =============================================================================
# FISHING SETTINGS (Cozy & Relaxing)
# =============================================================================
FISHING_CONFIG = {
    # Timing (very forgiving!)
    'hook_window_seconds': 2.0,      # Time to react to bite
    'min_wait_time': 3.0,            # Minimum wait for fish
    'max_wait_time': 8.0,            # Maximum wait for fish
    'approach_time': 1.5,            # Fish shadow visible time
    'celebration_time': 3.0,         # Catch celebration duration
    'escape_message_time': 1.5,      # "It got away" display time

    # Catch success rates (VERY forgiving)
    'base_hook_success': 0.95,       # 95% base success when hitting space
    'escape_recovery_bonus': 0.1,    # Bonus after fish escapes

    # Visual effects
    'bobber_idle_amplitude': 2,      # Gentle bobbing
    'bobber_nibble_amplitude': 3,    # More movement when fish approaches
    'bobber_bite_amplitude': 8,      # Strong movement on bite
    'ripple_lifetime': 1.5,          # How long ripples last
    'particle_count': 20,            # Celebration particles

    # Dad's tips
    'dad_tip_chance': 0.3,           # 30% chance after catch when with dad
    'dad_tip_display_time': 4.0,     # How long tips stay visible

    # Rarity weights (before bonuses)
    'rarity_weights': {
        'common': 50,
        'uncommon': 30,
        'rare': 15,
        'legendary': 4,
        'mythic': 1,
    },

    # Time bonuses
    'optimal_time_multiplier': 2.0,  # Double weight during best time
    'weather_bonus_multiplier': 1.5, # Bonus for preferred weather

    # Special conditions
    'midnight_window_seconds': 10,   # Binary Barracuda window at midnight
    'full_moon_cycle_days': 28,      # Days between full moons
}

# =============================================================================
# FISHING LOCATIONS
# =============================================================================
FISHING_LOCATIONS = {
    'crystal_lake_shallows': {
        'name': 'Crystal Lake (Shallows)',
        'description': 'Calm, clear waters perfect for beginners.',
        'ambient_sound': 'gentle_waves',
        'background_color': (70, 130, 180),  # Steel blue
    },
    'crystal_lake_deep': {
        'name': 'Crystal Lake (Deep)',
        'description': 'Darker waters where rare fish dwell.',
        'ambient_sound': 'deep_water',
        'background_color': (25, 25, 112),  # Midnight blue
    },
    'river': {
        'name': 'Oakhaven River',
        'description': 'Flowing waters that attract salmon and pike.',
        'ambient_sound': 'flowing_river',
        'background_color': (100, 149, 237),  # Cornflower blue
    },
    'hot_springs': {
        'name': 'Thermal Springs',
        'description': 'Warm waters where Firewall Fish thrive.',
        'ambient_sound': 'bubbling',
        'background_color': (255, 127, 80),  # Coral
    },
    'secluded_pool': {
        'name': 'Hidden Pool',
        'description': 'A secret spot known for treasure-carrying fish.',
        'ambient_sound': 'dripping',
        'background_color': (72, 61, 139),  # Dark slate blue
    },
    'ocean_edge': {
        'name': 'The Great Shell Edge',
        'description': 'Where the world ends. Legends lurk here.',
        'ambient_sound': 'deep_rumble',
        'background_color': (0, 0, 40),  # Almost black
    },
}

# =============================================================================
# DIGITAL WORLD SETTINGS (Vaporwave Overlay)
# =============================================================================
DIGITAL_CONFIG = {
    # Transition timing (seconds) - calming, not jarring
    'transition_duration': 2.5,

    # Effect intensity defaults (for accessibility)
    'default_effect_intensity': 1.0,   # Full effects by default
    'min_effect_intensity': 0.3,        # Minimum when reduced

    # Particle system
    'particle_count': 50,               # Data flow particles
    'particle_speed_min': 30,           # Pixels per second
    'particle_speed_max': 70,

    # Grid overlay
    'grid_spacing': 64,                 # Pixels between grid lines
    'grid_scroll_speed': 20.0,          # Scroll animation speed
    'grid_alpha': 60,                   # Base transparency (0-255)

    # Scanline effect
    'scanline_spacing': 3,              # Every N pixels
    'scanline_alpha': 30,               # Very subtle

    # Color transformation
    'pink_tint_alpha': 50,              # Pink overlay strength
    'cyan_highlight_alpha': 25,         # Cyan additive strength

    # Edge glow
    'edge_glow_width': 40,              # Pixels
    'edge_glow_alpha': 100,             # Base transparency

    # Wireframe rendering
    'wireframe_line_width': 1,
    'wireframe_glow_radius': 3,
    'wireframe_npc_intensity': 0.8,     # NPC wireframe visibility
    'wireframe_tree_intensity': 0.6,    # Tree wireframe visibility
    'wireframe_player_intensity': 0.4,  # Player wireframe (subtle)
}

# Digital World Color Palette (Vaporwave)
DIGITAL_COLORS = {
    # Primary palette
    'sky': '#ff6b9d',                   # Pink sky
    'ground': '#c39bd3',                # Soft purple ground
    'neon_cyan': '#00ffff',             # Data streams
    'neon_pink': '#ff00ff',             # Highlights
    'wireframe': '#00ff80',             # Structure lines (mint green)
    'grid': '#00c864',                  # Subtle grid

    # Effects
    'scanline': '#000000',              # Scanline shadows
    'glow': '#b464ff',                  # Soft purple glow

    # Data particles
    'data_primary': '#64ffda',          # Mint
    'data_secondary': '#ffb74d',        # Amber
}

# Audio crossfade settings for realm transitions
DIGITAL_AUDIO_CONFIG = {
    # Music crossfade during transitions
    'crossfade_curve': 'sine',          # 'linear', 'sine', 'ease_out'

    # Physical realm audio style
    'physical_reverb': 0.3,
    'physical_lowpass': 1.0,            # No filter

    # Digital realm audio style
    'digital_reverb': 0.6,
    'digital_lowpass': 0.7,             # Slight muffling for lo-fi feel
    'digital_bitcrush': 0.1,            # Subtle retro effect
}
