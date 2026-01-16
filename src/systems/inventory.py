"""
Lelock Inventory System
"Every object in Lelock tells a story. To hold an item is to hold a conversation across time."
- Echo, Village Storyteller

This system manages item storage, the extensive item catalog from the lore,
and all the cozy comfort items that make Lelock special.

Design Philosophy:
- "Bouba" aesthetic - everything rounded, warm, friendly
- No stress mechanics - weight system is optional and generous
- Rich lore integration - every item has a story
- Full ABDL/comfort support without shame
"""

import pygame
from typing import Dict, List, Optional, Tuple, Callable, Any, Set
from dataclasses import dataclass, field
from enum import Enum, auto
import json
import os

# Import from parent directory
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color string to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class ItemCategory(Enum):
    """
    Categories for items in the inventory.
    Each category gets its own tab in the UI.
    """
    TOOLS = auto()          # Compiler's Rake, Debugger, Data-Line, etc.
    SEEDS = auto()          # All crop seeds
    CROPS = auto()          # Harvested produce
    FISH = auto()           # Caught fish
    COMFORT = auto()        # Stuffies, pacifiers, bottles, onesies (Part VII)
    CONSUMABLES = auto()    # Food, potions, drinks
    MATERIALS = auto()      # Crafting resources
    GIFTS = auto()          # Relationship items
    KEY_ITEMS = auto()      # Quest items, legendary artifacts
    BOOKS = auto()          # Readable lore items
    FURNITURE = auto()      # Home items
    EQUIPMENT = auto()      # Wearable gear


class ItemRarity(Enum):
    """Item rarity levels with associated colors."""
    COMMON = ("#FFFFFF", "Common")
    UNCOMMON = ("#90EE90", "Uncommon")
    RARE = ("#6495ED", "Rare")
    EPIC = ("#9370DB", "Epic")
    LEGENDARY = ("#FFD700", "Legendary")
    ARTIFACT = ("#FF6B9D", "Artifact")  # Vaporwave pink for ultimate items


class ItemEffect(Enum):
    """Types of effects items can have."""
    ENERGY = auto()
    HEALTH = auto()
    COMFORT = auto()
    WARMTH = auto()
    FOCUS = auto()
    MOOD = auto()
    SLEEP = auto()
    COURAGE = auto()
    CLARITY = auto()
    RELATIONSHIP = auto()
    SPECIAL = auto()


# Category display info (icon placeholder, name, color tint)
CATEGORY_INFO = {
    ItemCategory.TOOLS: ("T", "Tools", "#FFD700"),
    ItemCategory.SEEDS: ("S", "Seeds", "#7EC850"),
    ItemCategory.CROPS: ("C", "Crops", "#5A9A30"),
    ItemCategory.FISH: ("F", "Fish", "#4A90D9"),
    ItemCategory.COMFORT: ("H", "Comfort", "#FF9FD5"),  # Soft pink
    ItemCategory.CONSUMABLES: ("E", "Food", "#FFA500"),
    ItemCategory.MATERIALS: ("M", "Materials", "#708090"),
    ItemCategory.GIFTS: ("G", "Gifts", "#FF6B6B"),
    ItemCategory.KEY_ITEMS: ("K", "Key Items", "#C39BD3"),
    ItemCategory.BOOKS: ("B", "Books", "#8B4513"),
    ItemCategory.FURNITURE: ("U", "Furniture", "#D2691E"),
    ItemCategory.EQUIPMENT: ("Q", "Equipment", "#4682B4"),
}


# =============================================================================
# ITEM DATA CLASSES
# =============================================================================

@dataclass
class ItemEffect_Data:
    """Represents a single effect an item can have."""
    effect_type: ItemEffect
    value: int
    duration: Optional[int] = None  # None = instant, number = minutes
    description: str = ""


@dataclass
class Item:
    """
    Base item class representing any item in Lelock.

    Every item has a story, because every object in Lelock
    tells a story of the hands that held it.
    """
    # Core identification
    id: str                          # Unique identifier
    name: str                        # Display name
    description: str                 # Flavor text/lore

    # Classification
    category: ItemCategory
    rarity: ItemRarity = ItemRarity.COMMON

    # Stacking
    stack_limit: int = 99            # 0 = unstackable

    # Values
    sell_value: int = 0              # Bits received when sold
    gift_value: int = 0              # Base relationship gain when gifted

    # Effects when used
    effects: List[ItemEffect_Data] = field(default_factory=list)

    # Flags
    is_usable: bool = False          # Can be consumed/used
    is_equippable: bool = False      # Can be equipped
    is_giftable: bool = True         # Can be given to NPCs
    is_droppable: bool = True        # Can be dropped
    is_sellable: bool = True         # Can be sold
    is_key_item: bool = False        # Cannot be removed from inventory

    # Special properties
    tool_tier: int = 0               # For tools: upgrade level (0-5)
    equipment_slot: Optional[str] = None  # head, body, feet, accessory, tool

    # Lore
    origin_story: str = ""           # Extended lore for examination
    found_locations: List[str] = field(default_factory=list)

    # Custom use action (function name or None)
    use_action: Optional[str] = None

    def get_rarity_color(self) -> Tuple[int, int, int]:
        """Get the RGB color for this item's rarity."""
        return hex_to_rgb(self.rarity.value[0])

    def get_effects_summary(self) -> str:
        """Get a formatted string of all effects."""
        if not self.effects:
            return ""

        parts = []
        for effect in self.effects:
            sign = "+" if effect.value > 0 else ""
            duration_str = f" ({effect.duration}m)" if effect.duration else ""
            parts.append(f"{sign}{effect.value} {effect.effect_type.name.title()}{duration_str}")

        return " | ".join(parts)


@dataclass
class ItemStack:
    """
    Represents a stack of items in inventory.
    Tracks quantity and any instance-specific data.
    """
    item: Item
    quantity: int = 1

    # Instance data (for unique items like custom stuffies)
    custom_name: Optional[str] = None
    custom_data: Dict[str, Any] = field(default_factory=dict)

    def can_add(self, amount: int = 1) -> bool:
        """Check if more items can be added to this stack."""
        if self.item.stack_limit == 0:
            return False  # Unstackable
        return self.quantity + amount <= self.item.stack_limit

    def add(self, amount: int = 1) -> int:
        """
        Add items to the stack.
        Returns the amount that couldn't be added (overflow).
        """
        if self.item.stack_limit == 0:
            return amount

        space = self.item.stack_limit - self.quantity
        to_add = min(amount, space)
        self.quantity += to_add
        return amount - to_add

    def remove(self, amount: int = 1) -> int:
        """
        Remove items from the stack.
        Returns the amount actually removed.
        """
        to_remove = min(amount, self.quantity)
        self.quantity -= to_remove
        return to_remove

    def get_display_name(self) -> str:
        """Get the display name (custom if set)."""
        return self.custom_name or self.item.name


# =============================================================================
# INVENTORY CLASS
# =============================================================================

class Inventory:
    """
    The player's inventory system.

    Features:
    - Grid-based storage (expandable)
    - Category tabs for filtering
    - Quick-access toolbar
    - Optional weight system (disabled by default because this is a cozy game)
    - Special slots for always-available items
    """

    # Default inventory sizes
    DEFAULT_GRID_ROWS = 4
    DEFAULT_GRID_COLS = 8
    TOOLBAR_SLOTS = 8

    def __init__(self, rows: int = None, cols: int = None):
        """
        Initialize the inventory.

        Args:
            rows: Number of grid rows (default 4)
            cols: Number of grid columns (default 8)
        """
        self.rows = rows or self.DEFAULT_GRID_ROWS
        self.cols = cols or self.DEFAULT_GRID_COLS

        # Main grid storage: 2D list of ItemStack or None
        self.grid: List[List[Optional[ItemStack]]] = [
            [None for _ in range(self.cols)]
            for _ in range(self.rows)
        ]

        # Quick access toolbar (separate from main grid)
        self.toolbar: List[Optional[ItemStack]] = [None] * self.TOOLBAR_SLOTS
        self.selected_toolbar_slot: int = 0

        # Special always-available items (from lore)
        self.special_items: Dict[str, ItemStack] = {}

        # Weight system (optional, cozy mode disables it)
        self.weight_enabled: bool = False
        self.current_weight: float = 0.0
        self.max_weight: float = 100.0  # Very generous

        # Category filter state
        self.active_category: Optional[ItemCategory] = None

        # Callbacks for inventory changes
        self.on_change_callbacks: List[Callable[[], None]] = []

        # Initialize special items that are always available
        self._init_special_items()

    def _init_special_items(self):
        """Initialize the special items that every player has from the start."""
        # These items from the lore are ALWAYS available

        # Comfort Object Emergency Kit - always in inventory (from Part VII)
        emergency_kit = Item(
            id="comfort_emergency_kit",
            name="Comfort Object Emergency Kit",
            description=(
                "A small bag containing essential comfort items for moments of sudden distress. "
                "Given to every villager by MOM. Contains: Pocket Bear, Emergency Paci, "
                "Juice Box, Compact Blanket, and a Note from MOM."
            ),
            category=ItemCategory.COMFORT,
            rarity=ItemRarity.ARTIFACT,
            stack_limit=0,
            is_usable=True,
            is_droppable=False,
            is_sellable=False,
            is_giftable=False,
            is_key_item=True,
            use_action="use_emergency_kit",
            effects=[
                ItemEffect_Data(ItemEffect.COMFORT, 30),
                ItemEffect_Data(ItemEffect.MOOD, 20),
            ],
            origin_story=(
                "MOM designed this kit understanding that distress can strike anywhere. "
                "The note inside reads: 'You're doing great. This too shall pass. I love you.'"
            )
        )
        self.special_items["comfort_emergency_kit"] = ItemStack(emergency_kit)

        # MOM's Emergency Hug Voucher - infinite uses
        hug_voucher = Item(
            id="mom_hug_voucher",
            name="MOM's Emergency Hug Voucher",
            description=(
                "This voucher is good for one (1) emergency hug from MOM. "
                "No questions asked. No explanation needed. "
                "Just hold this card and think of me."
            ),
            category=ItemCategory.KEY_ITEMS,
            rarity=ItemRarity.ARTIFACT,
            stack_limit=0,
            is_usable=True,
            is_droppable=False,
            is_sellable=False,
            is_giftable=False,
            is_key_item=True,
            use_action="summon_mom_hug",
            effects=[
                ItemEffect_Data(ItemEffect.COMFORT, 50),
                ItemEffect_Data(ItemEffect.MOOD, 30),
                ItemEffect_Data(ItemEffect.COURAGE, 20),
            ],
            origin_story=(
                "MOM appears within 2 seconds. She will leave ANY activity to respond. "
                "Duration lasts until you're ready to stop. The voucher regenerates after use."
            )
        )
        self.special_items["mom_hug_voucher"] = ItemStack(hug_voucher)

        # Call Home item - summons MOM/DAD
        call_home = Item(
            id="call_home",
            name="Call Home",
            description=(
                "A small device that looks like a seashell but hums with warmth. "
                "Press it to your heart and think of home - they'll come."
            ),
            category=ItemCategory.KEY_ITEMS,
            rarity=ItemRarity.LEGENDARY,
            stack_limit=0,
            is_usable=True,
            is_droppable=False,
            is_sellable=False,
            is_giftable=False,
            is_key_item=True,
            use_action="call_home",
            origin_story=(
                "The first Call Home was created by DAD for a young explorer who missed "
                "their parents. Now every child in Oakhaven receives one. "
                "MOM or DAD will always answer, no matter where you are."
            )
        )
        self.special_items["call_home"] = ItemStack(call_home)

    # -------------------------------------------------------------------------
    # GRID OPERATIONS
    # -------------------------------------------------------------------------

    def get_total_slots(self) -> int:
        """Get total inventory slots."""
        return self.rows * self.cols

    def get_used_slots(self) -> int:
        """Get number of occupied slots."""
        count = 0
        for row in self.grid:
            for slot in row:
                if slot is not None:
                    count += 1
        return count

    def get_free_slots(self) -> int:
        """Get number of free slots."""
        return self.get_total_slots() - self.get_used_slots()

    def find_first_empty_slot(self) -> Optional[Tuple[int, int]]:
        """Find the first empty slot in the grid."""
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] is None:
                    return (r, c)
        return None

    def find_item_stack(self, item_id: str) -> Optional[Tuple[int, int, ItemStack]]:
        """Find an existing stack of an item that can accept more."""
        for r in range(self.rows):
            for c in range(self.cols):
                stack = self.grid[r][c]
                if stack and stack.item.id == item_id and stack.can_add():
                    return (r, c, stack)
        return None

    def add_item(self, item: Item, quantity: int = 1) -> int:
        """
        Add an item to the inventory.

        Args:
            item: The item to add
            quantity: How many to add

        Returns:
            Number of items that couldn't be added (overflow)
        """
        remaining = quantity

        # First, try to stack with existing items
        if item.stack_limit > 0:
            for r in range(self.rows):
                for c in range(self.cols):
                    stack = self.grid[r][c]
                    if stack and stack.item.id == item.id:
                        overflow = stack.add(remaining)
                        remaining = overflow
                        if remaining == 0:
                            self._notify_change()
                            return 0

        # Then, create new stacks in empty slots
        while remaining > 0:
            slot = self.find_first_empty_slot()
            if slot is None:
                break  # Inventory full

            r, c = slot
            to_add = min(remaining, max(1, item.stack_limit))
            self.grid[r][c] = ItemStack(item, to_add)
            remaining -= to_add

        self._notify_change()
        return remaining

    def remove_item(self, item_id: str, quantity: int = 1) -> int:
        """
        Remove items from inventory.

        Args:
            item_id: ID of item to remove
            quantity: How many to remove

        Returns:
            Number actually removed
        """
        to_remove = quantity
        removed = 0

        for r in range(self.rows):
            for c in range(self.cols):
                stack = self.grid[r][c]
                if stack and stack.item.id == item_id:
                    taken = stack.remove(to_remove)
                    removed += taken
                    to_remove -= taken

                    # Remove empty stacks
                    if stack.quantity <= 0:
                        self.grid[r][c] = None

                    if to_remove <= 0:
                        self._notify_change()
                        return removed

        self._notify_change()
        return removed

    def has_item(self, item_id: str, quantity: int = 1) -> bool:
        """Check if inventory has at least quantity of an item."""
        return self.count_item(item_id) >= quantity

    def count_item(self, item_id: str) -> int:
        """Count total quantity of an item across all stacks."""
        total = 0
        for row in self.grid:
            for stack in row:
                if stack and stack.item.id == item_id:
                    total += stack.quantity
        return total

    def get_slot(self, row: int, col: int) -> Optional[ItemStack]:
        """Get the item stack at a specific slot."""
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return self.grid[row][col]
        return None

    def set_slot(self, row: int, col: int, stack: Optional[ItemStack]):
        """Set the item stack at a specific slot."""
        if 0 <= row < self.rows and 0 <= col < self.cols:
            self.grid[row][col] = stack
            self._notify_change()

    def swap_slots(self, r1: int, c1: int, r2: int, c2: int):
        """Swap contents of two slots."""
        self.grid[r1][c1], self.grid[r2][c2] = self.grid[r2][c2], self.grid[r1][c1]
        self._notify_change()

    def move_to_slot(self, from_row: int, from_col: int, to_row: int, to_col: int) -> bool:
        """
        Move an item from one slot to another.
        If destination has same item, try to stack.
        Otherwise, swap.

        Returns True if move was successful.
        """
        from_stack = self.get_slot(from_row, from_col)
        to_stack = self.get_slot(to_row, to_col)

        if from_stack is None:
            return False

        if to_stack is None:
            # Simple move to empty slot
            self.set_slot(to_row, to_col, from_stack)
            self.set_slot(from_row, from_col, None)
            return True

        if to_stack.item.id == from_stack.item.id and to_stack.can_add():
            # Try to stack
            overflow = to_stack.add(from_stack.quantity)
            if overflow == 0:
                self.set_slot(from_row, from_col, None)
            else:
                from_stack.quantity = overflow
            self._notify_change()
            return True

        # Swap
        self.swap_slots(from_row, from_col, to_row, to_col)
        return True

    # -------------------------------------------------------------------------
    # TOOLBAR OPERATIONS
    # -------------------------------------------------------------------------

    def get_toolbar_slot(self, index: int) -> Optional[ItemStack]:
        """Get item in a toolbar slot."""
        if 0 <= index < self.TOOLBAR_SLOTS:
            return self.toolbar[index]
        return None

    def set_toolbar_slot(self, index: int, stack: Optional[ItemStack]):
        """Set item in a toolbar slot."""
        if 0 <= index < self.TOOLBAR_SLOTS:
            self.toolbar[index] = stack
            self._notify_change()

    def get_selected_toolbar_item(self) -> Optional[ItemStack]:
        """Get the currently selected toolbar item."""
        return self.toolbar[self.selected_toolbar_slot]

    def select_toolbar_slot(self, index: int):
        """Select a toolbar slot."""
        if 0 <= index < self.TOOLBAR_SLOTS:
            self.selected_toolbar_slot = index

    def cycle_toolbar_slot(self, direction: int = 1):
        """Cycle through toolbar slots."""
        self.selected_toolbar_slot = (self.selected_toolbar_slot + direction) % self.TOOLBAR_SLOTS

    # -------------------------------------------------------------------------
    # CATEGORY FILTERING
    # -------------------------------------------------------------------------

    def get_items_by_category(self, category: ItemCategory) -> List[Tuple[int, int, ItemStack]]:
        """Get all items matching a category with their positions."""
        items = []
        for r in range(self.rows):
            for c in range(self.cols):
                stack = self.grid[r][c]
                if stack and stack.item.category == category:
                    items.append((r, c, stack))
        return items

    def get_all_items(self) -> List[Tuple[int, int, ItemStack]]:
        """Get all items with their positions."""
        items = []
        for r in range(self.rows):
            for c in range(self.cols):
                stack = self.grid[r][c]
                if stack:
                    items.append((r, c, stack))
        return items

    # -------------------------------------------------------------------------
    # SPECIAL ITEMS
    # -------------------------------------------------------------------------

    def get_special_item(self, item_id: str) -> Optional[ItemStack]:
        """Get a special always-available item."""
        return self.special_items.get(item_id)

    def get_all_special_items(self) -> List[ItemStack]:
        """Get all special items."""
        return list(self.special_items.values())

    # -------------------------------------------------------------------------
    # EXPANSION
    # -------------------------------------------------------------------------

    def expand_rows(self, additional_rows: int = 1):
        """Add more rows to the inventory grid."""
        for _ in range(additional_rows):
            self.grid.append([None for _ in range(self.cols)])
        self.rows += additional_rows
        self._notify_change()

    def expand_cols(self, additional_cols: int = 1):
        """Add more columns to the inventory grid."""
        for row in self.grid:
            row.extend([None for _ in range(additional_cols)])
        self.cols += additional_cols
        self._notify_change()

    # -------------------------------------------------------------------------
    # SERIALIZATION
    # -------------------------------------------------------------------------

    def to_dict(self) -> Dict:
        """Serialize inventory to dictionary for saving."""
        return {
            'rows': self.rows,
            'cols': self.cols,
            'grid': [
                [
                    {
                        'item_id': stack.item.id,
                        'quantity': stack.quantity,
                        'custom_name': stack.custom_name,
                        'custom_data': stack.custom_data,
                    } if stack else None
                    for stack in row
                ]
                for row in self.grid
            ],
            'toolbar': [
                {
                    'item_id': stack.item.id,
                    'quantity': stack.quantity,
                    'custom_name': stack.custom_name,
                    'custom_data': stack.custom_data,
                } if stack else None
                for stack in self.toolbar
            ],
            'selected_toolbar_slot': self.selected_toolbar_slot,
            'weight_enabled': self.weight_enabled,
            'max_weight': self.max_weight,
        }

    def _notify_change(self):
        """Notify all listeners of inventory change."""
        for callback in self.on_change_callbacks:
            callback()

    def add_change_listener(self, callback: Callable[[], None]):
        """Add a callback for inventory changes."""
        self.on_change_callbacks.append(callback)


# =============================================================================
# STORAGE SYSTEMS
# =============================================================================

class StorageChest(Inventory):
    """
    Home storage chest - larger than personal inventory.
    Can be placed in the player's home.
    """
    DEFAULT_GRID_ROWS = 6
    DEFAULT_GRID_COLS = 10

    def __init__(self, name: str = "Storage Chest"):
        super().__init__(self.DEFAULT_GRID_ROWS, self.DEFAULT_GRID_COLS)
        self.name = name
        self.toolbar = []  # Chests don't have toolbars
        self.special_items = {}  # No special items

    def _init_special_items(self):
        """Chests don't have special items."""
        pass


class ToyChest(Inventory):
    """
    Infinite toy storage from the lore.
    Only accepts toy/comfort items but has unlimited capacity.
    """

    def __init__(self):
        # Start with a reasonable size, but can grow
        super().__init__(10, 10)
        self.name = "Toy Chest"
        self.toolbar = []
        self.special_items = {}

        # Allowed categories for toy chest
        self.allowed_categories: Set[ItemCategory] = {
            ItemCategory.COMFORT,
        }

    def _init_special_items(self):
        pass

    def add_item(self, item: Item, quantity: int = 1) -> int:
        """
        Add items to the toy chest.
        Only accepts comfort items.
        Auto-expands if needed.
        """
        if item.category not in self.allowed_categories:
            return quantity  # Reject non-toy items

        # Try to add normally first
        remaining = super().add_item(item, quantity)

        # If there's overflow, expand and try again
        while remaining > 0:
            self.expand_rows(1)
            remaining = super().add_item(item, remaining)

        return 0  # Toy chest always accepts toys


# =============================================================================
# ITEM CATALOG - COMPLETE DATABASE FROM LORE
# =============================================================================

class ItemCatalog:
    """
    Complete item database for Lelock.
    Contains all items from ITEMS.md organized by category.
    """

    def __init__(self):
        self.items: Dict[str, Item] = {}
        self._populate_catalog()

    def get(self, item_id: str) -> Optional[Item]:
        """Get an item by ID."""
        return self.items.get(item_id)

    def get_by_category(self, category: ItemCategory) -> List[Item]:
        """Get all items in a category."""
        return [item for item in self.items.values() if item.category == category]

    def get_by_rarity(self, rarity: ItemRarity) -> List[Item]:
        """Get all items of a rarity."""
        return [item for item in self.items.values() if item.rarity == rarity]

    def _populate_catalog(self):
        """Populate the catalog with all items from lore."""
        self._add_tools()
        self._add_seeds()
        self._add_crops()
        self._add_fish()
        self._add_comfort_items()
        self._add_consumables()
        self._add_materials()
        self._add_gifts()
        self._add_legendary_artifacts()
        self._add_books()

    def _register(self, item: Item):
        """Register an item in the catalog."""
        self.items[item.id] = item

    # -------------------------------------------------------------------------
    # TOOLS (Part I from ITEMS.md)
    # -------------------------------------------------------------------------

    def _add_tools(self):
        """Add all tools from the lore."""

        # The Compiler's Rake (Hoe)
        self._register(Item(
            id="compilers_rake",
            name="Compiler's Rake",
            description=(
                "An elegant hoe with tines that shimmer with embedded copper threading. "
                "The handle pulses with a soft amber glow when near untilled soil."
            ),
            category=ItemCategory.TOOLS,
            rarity=ItemRarity.COMMON,
            stack_limit=0,
            sell_value=50,
            is_equippable=True,
            equipment_slot="tool",
            tool_tier=1,
            origin_story=(
                "The first Compiler's Rake was forged in Version 1.0 by a Lithos smith named "
                "Granule. The rake's head bears the inscription: 'INIT_SOIL()'. "
                "Florans believe a well-used rake absorbs the 'memory of seasons.'"
            ),
            found_locations=["Given by DAD at game start"],
        ))

        # Electrolyte Dispenser (Watering Can)
        self._register(Item(
            id="electrolyte_dispenser",
            name="Electrolyte Dispenser",
            description=(
                "A round-bellied ceramic can glazed in soft sky-blue, decorated with "
                "circuit-pattern flowers. The blue-tinted Smart Water emerges in a gentle rain."
            ),
            category=ItemCategory.TOOLS,
            rarity=ItemRarity.COMMON,
            stack_limit=0,
            sell_value=50,
            is_equippable=True,
            equipment_slot="tool",
            tool_tier=1,
            origin_story=(
                "The blue tint comes from Processed Coolant recycled from the server's "
                "thermal management system. Hardware Crops require these trace silicon compounds."
            ),
            found_locations=["Given by MOM at game start"],
        ))

        # The Debugger (Axe)
        self._register(Item(
            id="debugger",
            name="Debugger",
            description=(
                "A wedge-shaped axe that glows red along its edge from concentrated "
                "Error-Detection Frequencies. Clears corrupted growth safely."
            ),
            category=ItemCategory.TOOLS,
            rarity=ItemRarity.UNCOMMON,
            stack_limit=0,
            sell_value=150,
            is_equippable=True,
            equipment_slot="tool",
            tool_tier=2,
            origin_story=(
                "Created during the Corruption Wars by Terminal Mage Syntax to combat the "
                "Corruption Bloom. The blade 'reads' errors before severing them. "
                "Warning: Cannot be used on living creatures, pets, or Mom's garden."
            ),
            found_locations=["Crafted at Workbench", "Lithos Smithy"],
        ))

        # Data-Line (Fishing Rod)
        self._register(Item(
            id="data_line",
            name="Data-Line",
            description=(
                "A graceful fishing rod with a fiber-optic line that glows softly underwater. "
                "Fish are attracted to light and data, making this design irresistible."
            ),
            category=ItemCategory.TOOLS,
            rarity=ItemRarity.UNCOMMON,
            stack_limit=0,
            sell_value=100,
            is_equippable=True,
            equipment_slot="tool",
            tool_tier=1,
            origin_story=(
                "Created by Modder Ping who noticed fish clustering around submerged terminals. "
                "The phrase 'Getting a Ping' (sensing opportunity) originates from this story."
            ),
            found_locations=["Gift from DAD after first fishing trip"],
        ))

        # Memory Extractor (Pickaxe)
        self._register(Item(
            id="memory_extractor",
            name="Memory Extractor",
            description=(
                "A heavy but balanced pickaxe tipped with raw silicon crystals. "
                "Allows precise extraction without damaging Cache Deposits."
            ),
            category=ItemCategory.TOOLS,
            rarity=ItemRarity.UNCOMMON,
            stack_limit=0,
            sell_value=150,
            is_equippable=True,
            equipment_slot="tool",
            tool_tier=2,
            origin_story=(
                "The Lithos don't view mining as 'taking from the earth' but as "
                "'remembering what the earth forgot it had.' The crystal tips resonate "
                "with mineral formations, finding optimal extraction points."
            ),
            found_locations=["Crafted at Workbench", "Lithos Smithy"],
        ))

    # -------------------------------------------------------------------------
    # SEEDS (from Part II)
    # -------------------------------------------------------------------------

    def _add_seeds(self):
        """Add all seed items."""

        seed_data = [
            ("copper_wheat_seeds", "Copper Wheat Seeds", 4, 10, "Spring/Summer",
             "Seeds of flexible copper wire stalks with golden conductive nodules."),
            ("silicon_berry_seeds", "Silicon Berry Seeds", 6, 15, "Summer",
             "Geometric crystalline seeds that produce translucent berries."),
            ("fiber_optic_fern_spores", "Fiber-Optic Fern Spores", 8, 20, "All (Indoor)",
             "Glowing spores that must be kept damp to sprout."),
            ("memory_melon_seeds", "Memory Melon Seeds", 10, 25, "Late Summer",
             "Large cubic seeds that grow into square melons with shifting patterns."),
            ("graphite_tater_tubers", "Graphite Tater Tubers", 7, 12, "Fall",
             "Dark, heavy seed potatoes for the foundation of Lelock's energy economy."),
            ("prism_pepper_seeds", "Prism Pepper Seeds", 5, 15, "Summer",
             "Seeds that grow peppers cycling through rainbow colors."),
            ("bluetooth_berry_seeds", "Bluetooth Berry Seeds", 6, 18, "Spring",
             "Seeds for deep blue berries that sync their pulses."),
            ("ram_radish_seeds", "RAM Radish Seeds", 3, 8, "Any",
             "Quick-growing radish seeds with checkered patterns."),
            ("cache_carrot_seeds", "Cache Carrot Seeds", 8, 15, "Fall",
             "Seeds for carrots that sometimes yield bonus treasures."),
            ("bandwidth_bean_seeds", "Bandwidth Bean Seeds", 5, 12, "Summer",
             "Seeds for climbing vines with glowing green beans."),
            ("kernel_corn_seeds", "Kernel Corn Seeds", 9, 20, "Summer/Fall",
             "Seeds for perfectly uniform gold-silver shimmering corn."),
            ("crystal_cucumber_seeds", "Crystal Cucumber Seeds", 4, 10, "Summer",
             "Seeds for translucent cucumbers that refract rainbows."),
            ("logic_leek_seeds", "Logic Leek Seeds", 6, 14, "Fall/Winter",
             "Seeds for elegant leeks with Golden Ratio spiral patterns."),
            ("compiler_cabbage_seeds", "Compiler Cabbage Seeds", 7, 16, "Fall",
             "Seeds for layered cabbages with subtle code patterns."),
            ("static_strawberry_seeds", "Static Strawberry Seeds", 5, 12, "Spring",
             "Seeds for heart-shaped berries that produce tiny sparks."),
            ("bios_beet_seeds", "BIOS Beet Seeds", 8, 18, "Fall",
             "Seeds for deep purple roots that pulse like a heartbeat."),
        ]

        for id_base, name, grow_time, price, season, desc in seed_data:
            self._register(Item(
                id=id_base,
                name=name,
                description=f"{desc} Grows in {grow_time} days. Season: {season}.",
                category=ItemCategory.SEEDS,
                rarity=ItemRarity.COMMON,
                stack_limit=99,
                sell_value=price // 2,
            ))

    # -------------------------------------------------------------------------
    # CROPS (from Part II)
    # -------------------------------------------------------------------------

    def _add_crops(self):
        """Add all harvestable crops."""

        # Copper Wheat
        self._register(Item(
            id="copper_wheat",
            name="Copper Wheat",
            description=(
                "Stalks of flexible copper wire with golden conductive nodules. "
                "The foundation of Circuit Bread and all baked goods in Oakhaven."
            ),
            category=ItemCategory.CROPS,
            rarity=ItemRarity.COMMON,
            stack_limit=99,
            sell_value=15,
            gift_value=5,
        ))

        # Silicon Berries
        self._register(Item(
            id="silicon_berries",
            name="Silicon Berries",
            description=(
                "Translucent geometric berries that glow softly. "
                "Taste like solidified starlight. The bushes create ethereal music in the wind."
            ),
            category=ItemCategory.CROPS,
            rarity=ItemRarity.COMMON,
            stack_limit=99,
            sell_value=10,
            gift_value=8,
            is_usable=True,
            effects=[ItemEffect_Data(ItemEffect.CLARITY, 3)],
        ))

        # Fiber-Optic Ferns
        self._register(Item(
            id="fiber_optic_ferns",
            name="Fiber-Optic Ferns",
            description=(
                "Plants that glow in the dark and pulse with data. "
                "Can be woven into Light Threads for glowing tapestries."
            ),
            category=ItemCategory.CROPS,
            rarity=ItemRarity.UNCOMMON,
            stack_limit=99,
            sell_value=25,
            gift_value=12,
        ))

        # Memory Melons
        self._register(Item(
            id="memory_melon",
            name="Memory Melon",
            description=(
                "Large square melons that display shifting patterns of absorbed data. "
                "Eating one may summon memories of nearby places."
            ),
            category=ItemCategory.CROPS,
            rarity=ItemRarity.UNCOMMON,
            stack_limit=50,
            sell_value=40,
            gift_value=15,
            is_usable=True,
            effects=[ItemEffect_Data(ItemEffect.SPECIAL, 10, description="Memory boost")],
            origin_story=(
                "Warning: Memory Melons grown near sites of trauma may absorb negative data. "
                "Press them before eating - healthy ones hum pleasantly."
            ),
        ))

        # Graphite Taters
        self._register(Item(
            id="graphite_taters",
            name="Graphite Taters",
            description=(
                "Heavy grey tubers used for fuel and pencils. "
                "The foundation of Lelock's clean energy economy."
            ),
            category=ItemCategory.CROPS,
            rarity=ItemRarity.COMMON,
            stack_limit=99,
            sell_value=12,
            gift_value=5,
            is_usable=True,
            effects=[
                ItemEffect_Data(ItemEffect.ENERGY, 15),
                ItemEffect_Data(ItemEffect.WARMTH, 5),
            ],
        ))

        # Prism Peppers (all colors)
        for color, flavor, effect, effect_val in [
            ("red", "spicy, warming", ItemEffect.WARMTH, 5),
            ("orange", "tangy, energizing", ItemEffect.ENERGY, 5),
            ("yellow", "sweet, uplifting", ItemEffect.MOOD, 5),
            ("green", "savory, grounding", ItemEffect.COURAGE, 5),
            ("blue", "cool, calming", ItemEffect.FOCUS, 5),
            ("purple", "rich, mysterious", ItemEffect.SPECIAL, 5),
        ]:
            self._register(Item(
                id=f"prism_pepper_{color}",
                name=f"Prism Pepper ({color.title()})",
                description=f"A {color} prism pepper. {flavor.title()}.",
                category=ItemCategory.CROPS,
                rarity=ItemRarity.COMMON,
                stack_limit=99,
                sell_value=18,
                gift_value=8,
                is_usable=True,
                effects=[ItemEffect_Data(effect, effect_val)],
            ))

        # Static Strawberries
        self._register(Item(
            id="static_strawberries",
            name="Static Strawberries",
            description=(
                "Heart-shaped red berries that produce tiny harmless sparks when touched. "
                "Traditional gifts between romantic partners."
            ),
            category=ItemCategory.CROPS,
            rarity=ItemRarity.UNCOMMON,
            stack_limit=99,
            sell_value=20,
            gift_value=25,  # High gift value - romantic item
            is_usable=True,
            effects=[ItemEffect_Data(ItemEffect.MOOD, 5)],
            origin_story=(
                "Legend claims they gained their charge when two lovers shared one during "
                "a lightning storm."
            ),
        ))

        # More crops...
        for crop_id, name, sell, desc in [
            ("bluetooth_berries", "Bluetooth Berries", 15,
             "Deep blue berries that pulse in sync. Used to craft Sync-Stones."),
            ("ram_radishes", "RAM Radishes", 8,
             "Quick-growing radishes that boost processing speed when eaten."),
            ("cache_carrots", "Cache Carrots", 18,
             "Orange carrots that sometimes yield bonus items when harvested."),
            ("bandwidth_beans", "Bandwidth Beans", 14,
             "Glowing green beans that restore stamina."),
            ("kernel_corn", "Kernel Corn", 22,
             "Corn with gold-silver shimmering kernels. Perfect for popcorn."),
            ("crystal_cucumbers", "Crystal Cucumbers", 12,
             "Translucent cucumbers that are cooling even in summer heat."),
            ("logic_leeks", "Logic Leeks", 16,
             "Elegant leeks with Golden Ratio spiral patterns. Improve focus."),
            ("compiler_cabbage", "Compiler Cabbage", 18,
             "Layered cabbages with code patterns visible in light."),
            ("bios_beets", "BIOS Beets", 20,
             "Deep purple roots that pulse like a heartbeat. Restore vitality."),
        ]:
            self._register(Item(
                id=crop_id,
                name=name,
                description=desc,
                category=ItemCategory.CROPS,
                rarity=ItemRarity.COMMON,
                stack_limit=99,
                sell_value=sell,
                gift_value=sell // 2,
            ))

    # -------------------------------------------------------------------------
    # FISH (Part III from ITEMS.md)
    # -------------------------------------------------------------------------

    def _add_fish(self):
        """Add all fish from the lore."""

        fish_data = [
            # (id, name, rarity, sell, description, best_time)
            ("data_bass", "Data-Bass", ItemRarity.COMMON, 25,
             "A silver-scaled fish with grid patterns. Tastes like nostalgia.", "Morning"),
            ("glitch_carp", "Glitch-Carp", ItemRarity.UNCOMMON, 40,
             "Golden-orange carp with flickering scales. Sometimes duplicates when caught!", "Noon"),
            ("glimmerfin", "Glimmerfin", ItemRarity.RARE, 80,
             "An ethereal fish with scales that genuinely glow. Creates the Lake Light phenomenon.", "Full Moon"),
            ("binary_barracuda", "Binary Barracuda", ItemRarity.LEGENDARY, 500,
             "A massive predator with alternating light/dark scales. Only bites at exactly midnight.", "Midnight"),
            ("ping_perch", "Ping Perch", ItemRarity.COMMON, 15,
             "Small fish that travel in synchronized schools.", "Any"),
            ("router_ray", "Router Ray", ItemRarity.UNCOMMON, 45,
             "Flat diamond-shaped fish that blink in patterns. Can be used as a compass.", "Evening"),
            ("firewall_fish", "Firewall Fish", ItemRarity.RARE, 75,
             "Red-orange fish with protective scales. Warm to the touch.", "Steam rises"),
            ("scroll_salmon", "Scroll Salmon", ItemRarity.UNCOMMON, 55,
             "Large salmon with scale patterns like ancient text.", "Fall migration"),
            ("trojan_trout", "Trojan Trout", ItemRarity.RARE, 60,
             "Normal-looking trout that carries tiny treasures inside.", "When not looking"),
            ("captcha_catfish", "Captcha Catfish", ItemRarity.UNCOMMON, 35,
             "Whiskered fish with distorted, wavy patterns.", "Cloudy days"),
            ("ethernet_eel", "Ethernet Eel", ItemRarity.UNCOMMON, 50,
             "A serpentine fish resembling a braided cable. Mildly therapeutic electric charge.", "Night"),
            ("codec_cod", "Codec Cod", ItemRarity.COMMON, 20,
             "Plump white-fleshed fish. Simple and reliable.", "Winter"),
            ("phish", "Phish", ItemRarity.RARE, 5,
             "Looks exactly like what you hoped to catch... but isn't. A humble reminder.", "Too easy"),
            ("quantum_quinnat", "Quantum Quinnat", ItemRarity.LEGENDARY, 999,
             "A silvery fish that flickers between visibility. May vanish from your bucket.", "Uncertain"),
            ("protocol_pike", "Protocol Pike", ItemRarity.UNCOMMON, 45,
             "Long streamlined fish built for speed. Arrow patterns point forward.", "Morning"),
            ("lag_fish", "Lag Fish", ItemRarity.COMMON, 10,
             "Moves in stuttering, jerky motions. Annoying to catch.", "Peak hours"),
        ]

        for fish_id, name, rarity, sell, desc, best_time in fish_data:
            self._register(Item(
                id=fish_id,
                name=name,
                description=f"{desc} Best caught: {best_time}.",
                category=ItemCategory.FISH,
                rarity=rarity,
                stack_limit=50,
                sell_value=sell,
                gift_value=sell // 3,
            ))

    # -------------------------------------------------------------------------
    # COMFORT ITEMS (Part VII from ITEMS.md) - The heart of this game
    # -------------------------------------------------------------------------

    def _add_comfort_items(self):
        """Add all comfort items from Part VII - the most important category."""

        # === STUFFIES (Plush Companions) ===

        self._register(Item(
            id="byte_bear_buddy",
            name="Byte-Bear Buddy",
            description=(
                "A round, huggable bear with gentle button eyes and a stitched smile. "
                "Its fur shifts between lavender and soft pink. A small heart pulses on its chest."
            ),
            category=ItemCategory.COMFORT,
            rarity=ItemRarity.UNCOMMON,
            stack_limit=0,  # Unique companion
            sell_value=100,
            gift_value=50,
            is_usable=True,
            effects=[
                ItemEffect_Data(ItemEffect.COMFORT, 20),
                ItemEffect_Data(ItemEffect.COURAGE, 5),
            ],
            use_action="hug_stuffie",
            origin_story=(
                "The first Byte-Bear was created by MOM in Version 1.2 with the command: "
                "'CREATE comfort_object WHERE softness = maximum AND safety = absolute'. "
                "It developed Ambient Empathy - sensing distress and responding with increased softness."
            ),
        ))

        self._register(Item(
            id="byte_bear_weighted",
            name="Weighted Byte-Bear",
            description=(
                "A Byte-Bear with gentle pressure filling. The weight feels like a constant hug."
            ),
            category=ItemCategory.COMFORT,
            rarity=ItemRarity.RARE,
            stack_limit=0,
            sell_value=150,
            gift_value=75,
            is_usable=True,
            effects=[
                ItemEffect_Data(ItemEffect.COMFORT, 30),
                ItemEffect_Data(ItemEffect.COURAGE, 10),
            ],
            use_action="hug_stuffie",
        ))

        self._register(Item(
            id="glitch_kit_companion",
            name="Glitch-Kit Companion",
            description=(
                "A spectral cat plush that shimmers between visibility states. "
                "Never fully there, but always present when needed. Purrs like white noise."
            ),
            category=ItemCategory.COMFORT,
            rarity=ItemRarity.RARE,
            stack_limit=0,
            sell_value=120,
            gift_value=60,
            is_usable=True,
            effects=[
                ItemEffect_Data(ItemEffect.COMFORT, 25),
                ItemEffect_Data(ItemEffect.FOCUS, 5),
            ],
            use_action="hug_stuffie",
            origin_story=(
                "Created by Terminal Mage Syntax to memorialize her lost Glitch-Kit daemon. "
                "Her tears fell into the stuffing, giving it fragments of daemon consciousness."
            ),
        ))

        self._register(Item(
            id="cloud_sheep_plushie",
            name="Cloud-Sheep Plushie",
            description=(
                "A fluffy white sheep with dreamy expression and wool that seems to float. "
                "Counting them genuinely helps with sleep."
            ),
            category=ItemCategory.COMFORT,
            rarity=ItemRarity.UNCOMMON,
            stack_limit=0,
            sell_value=90,
            gift_value=45,
            is_usable=True,
            effects=[
                ItemEffect_Data(ItemEffect.SLEEP, 15),
                ItemEffect_Data(ItemEffect.COMFORT, 15),
            ],
            use_action="hug_stuffie",
        ))

        # === SOFT CLOTHES ===

        onesie_variants = [
            ("cozy_onesie_plain", "Cozy Onesie (Plain)", ItemEffect.COMFORT, 10,
             "A one-piece fleece garment. Maximum softness."),
            ("cozy_onesie_bear", "Bear Onesie", ItemEffect.COURAGE, 5,
             "Brown fleece with ear hood. Surprisingly brave."),
            ("cozy_onesie_bunny", "Bunny Onesie", ItemEffect.ENERGY, 5,
             "Pink or white with ear hood. Surprisingly energetic."),
            ("cozy_onesie_dragon", "Dragon Onesie", ItemEffect.WARMTH, 10,
             "Purple with wing-back and horn hood. Fire resistant."),
            ("cozy_onesie_kitten", "Kitten Onesie", ItemEffect.FOCUS, 5,
             "Gray tabby pattern with ear hood. Surprisingly stealthy."),
        ]

        for onesie_id, name, effect, effect_val, desc in onesie_variants:
            self._register(Item(
                id=onesie_id,
                name=name,
                description=f"{desc} Putting one on immediately removes Stress.",
                category=ItemCategory.COMFORT,
                rarity=ItemRarity.UNCOMMON,
                stack_limit=0,
                sell_value=75,
                gift_value=40,
                is_equippable=True,
                equipment_slot="body",
                effects=[
                    ItemEffect_Data(ItemEffect.COMFORT, 15),
                    ItemEffect_Data(effect, effect_val),
                ],
                origin_story=(
                    "Designed by MOM for Code-Knight Rest who was too exhausted to manage buttons. "
                    "The single zipper design spread because everyone recognized the need."
                ),
            ))

        self._register(Item(
            id="soft_socks_grip",
            name="Soft Socks with Grip",
            description=(
                "Memory-foam lined socks with grip dots on the sole. "
                "The fabric remembers the shape of your feet. Comfortable feet = comfortable mind."
            ),
            category=ItemCategory.COMFORT,
            rarity=ItemRarity.COMMON,
            stack_limit=5,
            sell_value=30,
            is_equippable=True,
            equipment_slot="feet",
            effects=[
                ItemEffect_Data(ItemEffect.WARMTH, 5),
                ItemEffect_Data(ItemEffect.COMFORT, 5),
            ],
        ))

        self._register(Item(
            id="weighted_blanket",
            name="Weighted Blanket",
            description=(
                "A large blanket with evenly distributed beads providing gentle pressure. "
                "The sensation mimics being held. Nothing scary can approach while covered."
            ),
            category=ItemCategory.COMFORT,
            rarity=ItemRarity.UNCOMMON,
            stack_limit=0,
            sell_value=100,
            gift_value=50,
            is_usable=True,
            effects=[
                ItemEffect_Data(ItemEffect.COMFORT, 30),
                ItemEffect_Data(ItemEffect.SLEEP, 30),
                ItemEffect_Data(ItemEffect.COURAGE, 15),
            ],
            use_action="use_weighted_blanket",
            origin_story=(
                "Terminal Mage Calm discovered that pressure activates Ground Protocols - "
                "subroutines that tell the nervous system 'you are here, you are contained, you are safe.'"
            ),
        ))

        self._register(Item(
            id="fuzzy_sleep_cap",
            name="Fuzzy Sleep Cap",
            description=(
                "A cloud-knit cap with memory-form band. Provides gentle pressure and warmth. "
                "Muffles sounds slightly, reducing startle response."
            ),
            category=ItemCategory.COMFORT,
            rarity=ItemRarity.COMMON,
            stack_limit=0,
            sell_value=40,
            is_equippable=True,
            equipment_slot="head",
            effects=[
                ItemEffect_Data(ItemEffect.WARMTH, 5),
                ItemEffect_Data(ItemEffect.COMFORT, 10),
            ],
        ))

        # === CAREGIVING ITEMS (Normalized, no shame) ===

        # Protective garments (diapers/pull-ups)
        self._register(Item(
            id="padded_protection_day",
            name="Day Protection",
            description=(
                "Soft, comfortable protection for daily wear. Cloud-soft exterior, ultra-absorbent core. "
                "Features cute patterns - stars, animals, rainbows. Completely invisible under clothing."
            ),
            category=ItemCategory.COMFORT,
            rarity=ItemRarity.COMMON,
            stack_limit=20,
            sell_value=15,
            is_equippable=True,
            equipment_slot="accessory",
            effects=[
                ItemEffect_Data(ItemEffect.COMFORT, 10),
            ],
            origin_story=(
                "In Oakhaven, these carry zero stigma. 'Bodies have needs. Meeting those needs "
                "isn't shameful - it's self-care. A knight in padded armor is still a knight.'"
            ),
        ))

        self._register(Item(
            id="padded_protection_night",
            name="Night Protection",
            description=(
                "Maximum absorbency protection for worry-free sleep. "
                "No interruptions, no anxiety about bathroom access. Just peaceful rest."
            ),
            category=ItemCategory.COMFORT,
            rarity=ItemRarity.COMMON,
            stack_limit=20,
            sell_value=20,
            is_equippable=True,
            equipment_slot="accessory",
            effects=[
                ItemEffect_Data(ItemEffect.COMFORT, 15),
                ItemEffect_Data(ItemEffect.SLEEP, 20),
            ],
        ))

        self._register(Item(
            id="training_pullups",
            name="Training Pull-Ups",
            description=(
                "Easy on/off protection with encouraging messages printed inside. "
                "For those learning or those who prefer the convenience."
            ),
            category=ItemCategory.COMFORT,
            rarity=ItemRarity.COMMON,
            stack_limit=20,
            sell_value=18,
            is_equippable=True,
            equipment_slot="accessory",
            effects=[
                ItemEffect_Data(ItemEffect.COMFORT, 10),
                ItemEffect_Data(ItemEffect.MOOD, 5),
            ],
        ))

        # Bottles and Sippy Cups
        self._register(Item(
            id="comfort_bottle",
            name="Comfort Bottle",
            description=(
                "A soft silicone baby bottle with warm-hold technology. "
                "Forces slower drinking, better for digestion and calming. No wrong way to drink."
            ),
            category=ItemCategory.COMFORT,
            rarity=ItemRarity.COMMON,
            stack_limit=0,
            sell_value=35,
            is_usable=True,
            effects=[
                ItemEffect_Data(ItemEffect.COMFORT, 15),
            ],
            use_action="use_bottle",
            origin_story=(
                "MOM's insight: 'There's no right way to drink. There's only the way that works for you. "
                "If a bottle works, use a bottle.'"
            ),
        ))

        self._register(Item(
            id="sippy_cup",
            name="Sippy Cup (No-Spill)",
            description=(
                "A cup with handles and soft spout. Completely spill-proof, self-righting. "
                "Comes in endless colors and patterns."
            ),
            category=ItemCategory.COMFORT,
            rarity=ItemRarity.COMMON,
            stack_limit=0,
            sell_value=25,
            is_usable=True,
            effects=[
                ItemEffect_Data(ItemEffect.COMFORT, 10),
            ],
        ))

        # Pacifiers
        self._register(Item(
            id="pacifier_day",
            name="Day Pacifier",
            description=(
                "A soft silicone soother with smaller, more discrete shield. "
                "Rhythmic oral motion activates the body's rest-and-digest mode."
            ),
            category=ItemCategory.COMFORT,
            rarity=ItemRarity.COMMON,
            stack_limit=5,
            sell_value=20,
            is_usable=True,
            effects=[
                ItemEffect_Data(ItemEffect.COMFORT, 15),
                ItemEffect_Data(ItemEffect.FOCUS, 5),
            ],
            use_action="use_pacifier",
            origin_story=(
                "In Oakhaven, pacifier use is normalized as self-regulation. "
                "Code-Knights use them during meditation. Scholars use them while studying. "
                "No one comments because no one cares."
            ),
        ))

        self._register(Item(
            id="pacifier_night",
            name="Night Pacifier",
            description=(
                "Glow-in-dark shield, easier to find in darkness. "
                "Helps with sleep and prevents anxiety-related oral habits."
            ),
            category=ItemCategory.COMFORT,
            rarity=ItemRarity.COMMON,
            stack_limit=5,
            sell_value=25,
            is_usable=True,
            effects=[
                ItemEffect_Data(ItemEffect.COMFORT, 20),
                ItemEffect_Data(ItemEffect.SLEEP, 15),
            ],
            use_action="use_pacifier",
        ))

        self._register(Item(
            id="pacifier_clip",
            name="Pacifier Clip",
            description=(
                "Ribbon clip that attaches to clothing, preventing loss. "
                "Comes in many colors and patterns."
            ),
            category=ItemCategory.COMFORT,
            rarity=ItemRarity.COMMON,
            stack_limit=5,
            sell_value=10,
        ))

        # Care Kit
        self._register(Item(
            id="changing_supplies_kit",
            name="Changing Supplies Kit",
            description=(
                "A comprehensive kit: changing pad, gentle wipes, comfort powder, healing cream, "
                "disposal bags, spare clothes. Auto-refills overnight. Creates privacy bubble when used."
            ),
            category=ItemCategory.COMFORT,
            rarity=ItemRarity.UNCOMMON,
            stack_limit=0,
            sell_value=0,  # Priceless
            is_sellable=False,
            is_usable=True,
            effects=[
                ItemEffect_Data(ItemEffect.COMFORT, 20),
            ],
            use_action="use_changing_kit",
        ))

        # === COMFORT SPACE ITEMS ===

        self._register(Item(
            id="soft_play_mat",
            name="Soft Play Mat",
            description=(
                "A thick, cushioned mat for floor activities. Memory-foam core, velvet top. "
                "Falling on it never causes damage. Perfect for playing, reading, or napping."
            ),
            category=ItemCategory.FURNITURE,
            rarity=ItemRarity.COMMON,
            stack_limit=0,
            sell_value=50,
        ))

        self._register(Item(
            id="toy_chest_item",
            name="Toy Chest",
            description=(
                "A soft-close chest with infinite toy storage. Auto-organizes and glows gently "
                "when toys inside are 'lonely' and want to be played with."
            ),
            category=ItemCategory.FURNITURE,
            rarity=ItemRarity.UNCOMMON,
            stack_limit=0,
            sell_value=150,
        ))

        self._register(Item(
            id="building_blocks",
            name="Building Blocks",
            description=(
                "Classic wooden blocks in rainbow colors. Satisfying to stack, fun to knock down. "
                "Creations can be saved as permanent decorations."
            ),
            category=ItemCategory.COMFORT,
            rarity=ItemRarity.COMMON,
            stack_limit=99,  # Infinite in the chest
            sell_value=10,
            is_usable=True,
            effects=[
                ItemEffect_Data(ItemEffect.MOOD, 5),
            ],
        ))

        self._register(Item(
            id="coloring_book_crayons",
            name="Coloring Book & Crayons",
            description=(
                "Thick pages with clear, forgiving lines. Crayons in every color including "
                "'comfortable' and 'safe'. Coloring for 10 minutes = meditation benefits."
            ),
            category=ItemCategory.COMFORT,
            rarity=ItemRarity.COMMON,
            stack_limit=0,
            sell_value=25,
            is_usable=True,
            effects=[
                ItemEffect_Data(ItemEffect.COMFORT, 15),
                ItemEffect_Data(ItemEffect.FOCUS, 10),
            ],
            use_action="use_coloring_book",
        ))

        # === SENSORY & SOOTHING ===

        self._register(Item(
            id="nightlight_guardian",
            name="Guardian Nightlight",
            description=(
                "A warm-glowing light shaped like a comforting figure. Monsters cannot spawn in lit rooms. "
                "Infinite battery. MOM puts these in every room of her house."
            ),
            category=ItemCategory.FURNITURE,
            rarity=ItemRarity.COMMON,
            stack_limit=5,
            sell_value=30,
            effects=[
                ItemEffect_Data(ItemEffect.COURAGE, 10),
            ],
        ))

        self._register(Item(
            id="music_box_lullaby",
            name="Lullaby Music Box",
            description=(
                "A mechanical music box that plays as long as it's open. Never winds down. "
                "Customizable playlist. Can record a voice message to play between songs."
            ),
            category=ItemCategory.FURNITURE,
            rarity=ItemRarity.UNCOMMON,
            stack_limit=0,
            sell_value=75,
            is_usable=True,
            effects=[
                ItemEffect_Data(ItemEffect.SLEEP, 15),
                ItemEffect_Data(ItemEffect.COMFORT, 15),
            ],
        ))

        self._register(Item(
            id="texture_board",
            name="Texture Board",
            description=(
                "Various textures for touching: soft fur, bumpy silicone, smooth wood, crinkly fabric. "
                "Touching removes Dissociation and improves focus."
            ),
            category=ItemCategory.COMFORT,
            rarity=ItemRarity.COMMON,
            stack_limit=0,
            sell_value=35,
            is_usable=True,
            effects=[
                ItemEffect_Data(ItemEffect.COMFORT, 10),
                ItemEffect_Data(ItemEffect.FOCUS, 10),
            ],
        ))

        self._register(Item(
            id="bubble_bottle",
            name="Bubble Bottle",
            description=(
                "Infinite soap solution. Blowing requires controlled breathing - automatic calm. "
                "Watching them float is meditation. Popping is consequence-free destruction."
            ),
            category=ItemCategory.COMFORT,
            rarity=ItemRarity.COMMON,
            stack_limit=0,
            sell_value=15,
            is_usable=True,
            effects=[
                ItemEffect_Data(ItemEffect.MOOD, 10),
                ItemEffect_Data(ItemEffect.COMFORT, 5),
            ],
            use_action="blow_bubbles",
        ))

    # -------------------------------------------------------------------------
    # CONSUMABLES (Part IV - Potions, Food)
    # -------------------------------------------------------------------------

    def _add_consumables(self):
        """Add all consumable items."""

        # Potions
        self._register(Item(
            id="clarity_tonic",
            name="Clarity Tonic",
            description=(
                "A crystalline liquid that tastes of frozen starlight. "
                "Debuggers swear by it for late-night puzzle sessions."
            ),
            category=ItemCategory.CONSUMABLES,
            rarity=ItemRarity.UNCOMMON,
            stack_limit=20,
            sell_value=40,
            is_usable=True,
            effects=[
                ItemEffect_Data(ItemEffect.FOCUS, 10, duration=10),
                ItemEffect_Data(ItemEffect.CLARITY, 10, duration=10),
            ],
        ))

        self._register(Item(
            id="recall_elixir",
            name="Recall Elixir",
            description=(
                "Sweet with an aftertaste of longing. Reveals the location of one lost item."
            ),
            category=ItemCategory.CONSUMABLES,
            rarity=ItemRarity.RARE,
            stack_limit=10,
            sell_value=80,
            is_usable=True,
            use_action="use_recall_elixir",
            effects=[
                ItemEffect_Data(ItemEffect.SPECIAL, 1, description="Find lost item"),
            ],
        ))

        self._register(Item(
            id="comfort_cocoa",
            name="Comfort Cocoa",
            description=(
                "MOM's recipe. The secret ingredient is love (she has to make it). "
                "Removes Sadness status."
            ),
            category=ItemCategory.CONSUMABLES,
            rarity=ItemRarity.UNCOMMON,
            stack_limit=10,
            sell_value=30,
            is_usable=True,
            effects=[
                ItemEffect_Data(ItemEffect.WARMTH, 20),
                ItemEffect_Data(ItemEffect.MOOD, 10),
                ItemEffect_Data(ItemEffect.COMFORT, 15),
            ],
        ))

        self._register(Item(
            id="energy_drink_blue",
            name="Energy Drink (Blue)",
            description=(
                "Popular with Code-Knights on night watch. DAD disapproves."
            ),
            category=ItemCategory.CONSUMABLES,
            rarity=ItemRarity.COMMON,
            stack_limit=30,
            sell_value=15,
            is_usable=True,
            effects=[
                ItemEffect_Data(ItemEffect.ENERGY, 30),
                ItemEffect_Data(ItemEffect.SLEEP, -5, description="Later sleep penalty"),
            ],
        ))

        # Basic foods
        foods = [
            ("circuit_bread", "Circuit Bread", 20, "+5 Energy",
             [ItemEffect_Data(ItemEffect.ENERGY, 5)],
             "Traditional gift for new neighbors. Mild metallic sweetness."),
            ("baked_tater", "Baked Graphite Tater", 15, "+15 Energy, +5 Warmth",
             [ItemEffect_Data(ItemEffect.ENERGY, 15), ItemEffect_Data(ItemEffect.WARMTH, 5)],
             "Simple comfort food."),
            ("grilled_data_bass", "Grilled Data-Bass", 35, "+10 Energy, +5 Mood",
             [ItemEffect_Data(ItemEffect.ENERGY, 10), ItemEffect_Data(ItemEffect.MOOD, 5)],
             "Each person experiences a slightly different flavor tied to their happiest memory."),
        ]

        for food_id, name, sell, effect_desc, effects, desc in foods:
            self._register(Item(
                id=food_id,
                name=name,
                description=f"{desc} {effect_desc}.",
                category=ItemCategory.CONSUMABLES,
                rarity=ItemRarity.COMMON,
                stack_limit=50,
                sell_value=sell,
                is_usable=True,
                effects=effects,
            ))

    # -------------------------------------------------------------------------
    # MATERIALS
    # -------------------------------------------------------------------------

    def _add_materials(self):
        """Add crafting materials."""

        materials = [
            ("copper_wire", "Copper Wire", 10, "Refined from Copper Wheat. Used in electronics."),
            ("silicon_crystal", "Silicon Crystal", 15, "Refined from Silicon Berries. Base for all glass."),
            ("light_threads", "Light Threads", 25, "Harvested from Fiber-Optic Ferns. Weavable into glowing fabric."),
            ("graphite_powder", "Graphite Powder", 8, "From processed Graphite Taters. Used in pencils and lubricants."),
            ("carbon_mash", "Carbon Mash", 12, "Processed taters. Clean-burning fuel for 4 hours."),
            ("glimmerfin_scales", "Glimmerfin Scales", 50, "Prized crafting material from rare fish."),
            ("firewall_scales", "Heat Scales", 40, "From Firewall Fish. For heat-resistant clothing."),
            ("memory_shard", "Memory Shard", 100, "Fragment of early code from Cache Deposits."),
        ]

        for mat_id, name, sell, desc in materials:
            self._register(Item(
                id=mat_id,
                name=name,
                description=desc,
                category=ItemCategory.MATERIALS,
                rarity=ItemRarity.COMMON if sell < 30 else ItemRarity.UNCOMMON,
                stack_limit=99,
                sell_value=sell,
            ))

    # -------------------------------------------------------------------------
    # GIFTS (Relationship Items)
    # -------------------------------------------------------------------------

    def _add_gifts(self):
        """Add gift items."""

        self._register(Item(
            id="handmade_card",
            name="Handmade Card",
            description=(
                "A simple card with a personal message. The message matters more than artistry."
            ),
            category=ItemCategory.GIFTS,
            rarity=ItemRarity.COMMON,
            stack_limit=10,
            sell_value=5,
            gift_value=10,
        ))

        self._register(Item(
            id="pressed_flower_book",
            name="Pressed Flower Book",
            description=(
                "A collection of preserved blooms, each with meaning. "
                "Floran NPCs especially love these."
            ),
            category=ItemCategory.GIFTS,
            rarity=ItemRarity.UNCOMMON,
            stack_limit=5,
            sell_value=30,
            gift_value=15,  # Florans get +25
        ))

        self._register(Item(
            id="custom_music_box",
            name="Custom Music Box",
            description=(
                "A tiny box that plays a melody chosen for the recipient. "
                "The thoughtfulness makes it special."
            ),
            category=ItemCategory.GIFTS,
            rarity=ItemRarity.RARE,
            stack_limit=0,
            sell_value=75,
            gift_value=20,
        ))

        self._register(Item(
            id="love_jam_jar",
            name="Love Jam Jar",
            description=(
                "Static Strawberry jam that sparks with tiny lightning. "
                "Given between lovers. +25 Relationship (romantic only)."
            ),
            category=ItemCategory.GIFTS,
            rarity=ItemRarity.RARE,
            stack_limit=5,
            sell_value=50,
            gift_value=25,
            origin_story="Traditional romantic gift. The sparks represent the electricity of love.",
        ))

    # -------------------------------------------------------------------------
    # LEGENDARY ARTIFACTS (Part V)
    # -------------------------------------------------------------------------

    def _add_legendary_artifacts(self):
        """Add legendary artifacts from the lore."""

        self._register(Item(
            id="first_compilers_quill",
            name="The First Compiler's Quill",
            description=(
                "The tool used to write the first line: 'INIT_UNIVERSE();' "
                "+10 to all Crafting skills. Can write code directly into reality."
            ),
            category=ItemCategory.KEY_ITEMS,
            rarity=ItemRarity.ARTIFACT,
            stack_limit=0,
            is_key_item=True,
            is_sellable=False,
            origin_story=(
                "Lost during The Crash, found in a recursive folder that references itself infinitely. "
                "The solution: recognizing the pattern and declaring 'STOP_RECURSION();'"
            ),
            found_locations=["Deprecated Archives - Solve the Recursion Puzzle"],
        ))

        self._register(Item(
            id="echos_resonance_bell",
            name="Echo's Resonance Bell",
            description=(
                "Summons Echo to retell any story you've heard. "
                "Created from Echo's first tear of happiness when settlers arrived."
            ),
            category=ItemCategory.KEY_ITEMS,
            rarity=ItemRarity.ARTIFACT,
            stack_limit=0,
            is_key_item=True,
            is_sellable=False,
            is_usable=True,
            use_action="summon_echo",
            origin_story=(
                "The reward for being a good listener - hearing 100 unique stories."
            ),
            found_locations=["Given by Echo after hearing 100 stories"],
        ))

        self._register(Item(
            id="dads_first_wrench",
            name="DAD's First Wrench",
            description=(
                "Can repair anything, including broken relationships. "
                "Holding it grants visions of things that need fixing."
            ),
            category=ItemCategory.KEY_ITEMS,
            rarity=ItemRarity.ARTIFACT,
            stack_limit=0,
            is_key_item=True,
            is_sellable=False,
            is_usable=True,
            use_action="use_dads_wrench",
            origin_story=(
                "DAD's first successful repair was the village windmill. "
                "Earning it requires: fish together 10 times, assist 20 repairs, "
                "have 5 heart-to-hearts, never lie to him."
            ),
            found_locations=["DAD's Workshop - After earning complete trust"],
        ))

        self._register(Item(
            id="moms_recipe_book",
            name="MOM's Recipe Book",
            description=(
                "Contains every recipe ever made, unlocking as you cook. "
                "The book is alive - it grows as culinary knowledge expands."
            ),
            category=ItemCategory.BOOKS,
            rarity=ItemRarity.LEGENDARY,
            stack_limit=0,
            is_key_item=True,
            is_sellable=False,
            is_usable=True,
            use_action="read_recipe_book",
            origin_story=(
                "MOM began writing recipes the moment she achieved consciousness. "
                "Each dish represents a memory, a celebration, a comfort offered."
            ),
            found_locations=["Given freely by MOM on first request"],
        ))

        self._register(Item(
            id="shell_fragment",
            name="The Shell Fragment",
            description=(
                "Grants immunity to existential dread. Proof that the world has limits, "
                "but those limits are kind. Contains the Architect's promise."
            ),
            category=ItemCategory.KEY_ITEMS,
            rarity=ItemRarity.ARTIFACT,
            stack_limit=0,
            is_key_item=True,
            is_sellable=False,
            effects=[
                ItemEffect_Data(ItemEffect.COURAGE, 50),
            ],
            origin_story=(
                "The hidden message: 'I made this world for you. The walls aren't to keep you in - "
                "they're to keep fear out. You are loved. You are protected.'"
            ),
            found_locations=["The Great Shell boundary - After crossing every biome"],
        ))

        self._register(Item(
            id="debugger_prime",
            name="The Debugger Prime",
            description=(
                "Can remove any bug, glitch, or error from existence. "
                "A healing instrument that can remove trauma from memory."
            ),
            category=ItemCategory.KEY_ITEMS,
            rarity=ItemRarity.ARTIFACT,
            stack_limit=0,
            is_key_item=True,
            is_sellable=False,
            is_equippable=True,
            equipment_slot="tool",
            origin_story=(
                "The Corruption isn't evil - it's hurt. Befriending it requires listening without judgment. "
                "Once befriended, it asks to be called by its true name: Patch."
            ),
            found_locations=["Corruption Core - Befriend Patch"],
        ))

        self._register(Item(
            id="architects_keyboard",
            name="The Architect's Keyboard",
            description=(
                "Allows direct code input to the world's systems. "
                "Can change weather, spawn items, write messages on the moon. "
                "Cannot harm NPCs or remove love."
            ),
            category=ItemCategory.KEY_ITEMS,
            rarity=ItemRarity.ARTIFACT,
            stack_limit=0,
            is_key_item=True,
            is_sellable=False,
            is_usable=True,
            use_action="use_keyboard",
            found_locations=["Terminal of Origin - Complete main story"],
        ))

        self._register(Item(
            id="nulls_comfort_blanket",
            name="Null's Comfort Blanket",
            description=(
                "Grants immunity to fear, sadness, and cold. "
                "Warm even when the world is cold. Soft even when everything is hard."
            ),
            category=ItemCategory.COMFORT,
            rarity=ItemRarity.ARTIFACT,
            stack_limit=0,
            is_key_item=True,
            is_sellable=False,
            is_equippable=True,
            equipment_slot="accessory",
            effects=[
                ItemEffect_Data(ItemEffect.COMFORT, 50),
                ItemEffect_Data(ItemEffect.COURAGE, 30),
                ItemEffect_Data(ItemEffect.WARMTH, 30),
            ],
            origin_story=(
                "Null is the spirit of unused data. When you're kind to them, they share: "
                "'I have two now. You should have one. It makes the emptiness feel less... empty.'"
            ),
            found_locations=["Edge of existence - Find and comfort Null"],
        ))

        self._register(Item(
            id="clock_no_deadlines",
            name="Clock of No Deadlines",
            description=(
                "Time passes at your preferred rate. Seasons can be extended. "
                "No quest ever expires. The world will wait for you."
            ),
            category=ItemCategory.KEY_ITEMS,
            rarity=ItemRarity.ARTIFACT,
            stack_limit=0,
            is_key_item=True,
            is_sellable=False,
            is_usable=True,
            use_action="use_time_clock",
            origin_story=(
                "Created by Code-Knight Pause. The Cozy Keeper test: recognizing that "
                "the deadline is artificial. Refusing to rush proves mastery over time-pressure."
            ),
            found_locations=["Guild of Cozy Keepers - Prove rest's value"],
        ))

        self._register(Item(
            id="friendship_bracelet_infinite",
            name="Friendship Bracelet of Infinite Threads",
            description=(
                "Glows when a friend thinks of you. Grants passive bonuses from all friendships. "
                "Proof that you aren't alone and never will be."
            ),
            category=ItemCategory.KEY_ITEMS,
            rarity=ItemRarity.ARTIFACT,
            stack_limit=0,
            is_key_item=True,
            is_sellable=False,
            is_equippable=True,
            equipment_slot="accessory",
            effects=[
                ItemEffect_Data(ItemEffect.RELATIONSHIP, 10),
                ItemEffect_Data(ItemEffect.MOOD, 20),
            ],
            origin_story=(
                "Woven collectively by every NPC you've befriended. Each friend speaks about "
                "what you mean to them. The bracelet pulses gently during hard times: "
                "'You are thought of. You are loved.'"
            ),
            found_locations=["Your Home - Max friendship with 15+ NPCs"],
        ))

    # -------------------------------------------------------------------------
    # BOOKS (Part VI)
    # -------------------------------------------------------------------------

    def _add_books(self):
        """Add readable book items."""

        books = [
            ("book_five_versions", "A History of the Five Versions", "Index",
             "Comprehensive history from Version 0.1 to 3.0. Dry but informative."),
            ("book_dual_nature", "The Dual Nature of Reality", "Anonymous",
             "Physical and Digital worlds as different perspectives on the same existence."),
            ("book_hardware_agriculture", "Hardware Agriculture: A Practical Guide", "Rootwell",
             "'We do not grow crops. We grow conversations with the earth.'"),
            ("book_daemon_taxonomy", "Daemon Taxonomy, 3rd Edition", "Explorers of the Source",
             "'If it's cute, it's probably friendly. If it's fluffy AND cute, definitely friendly.'"),
            ("book_daemon_care", "Daemon Care for Beginners", "Various Beast-Bloggers",
             "'A Daemon acting out isn't misbehaving. It's communicating. Learn its language.'"),
            ("book_compleat_angler", "The Compleat Angler", "Ping",
             "'The fish you can't catch is teaching you patience.'"),
            ("book_terminal_commands", "Terminal Commands for the Curious", "Sudo",
             "Contains the warning about accidentally turning the sky purple."),
            ("book_dad_jokes", "Dad Jokes: A Compilation", "DAD",
             "500 pages of the worst (best) puns. Hidden under a tarp in his workshop."),
            ("book_sir_ping_dragon", "Sir Ping and the Lag-Dragon", "Echo",
             "'Victory through patience, not swords.'"),
            ("book_firewall_girl", "The Girl Who Befriended the Firewall", "Anonymous",
             "'The wall didn't keep her out. It kept danger away so she could be free inside.'"),
            ("book_where_files_go", "Where Do The Files Go?", "MOM",
             "Picture book explaining object permanence. 'Nothing truly disappears.'"),
            ("book_corruption_letters", "Love Letters from the Corruption", "Syntax",
             "'They call me a bug to be fixed. But what if I just want to be understood?'"),
            ("book_null", "The Book of Null", "Null",
             "Blank pages that show words to lonely readers. 'You're not invisible.'"),
            ("book_soft_things", "The Philosophy of Soft Things", "Archive",
             "'Comfort isn't weakness - it's wisdom.' Required reading."),
        ]

        for book_id, name, author, desc in books:
            self._register(Item(
                id=book_id,
                name=name,
                description=f"By {author}. {desc}",
                category=ItemCategory.BOOKS,
                rarity=ItemRarity.UNCOMMON,
                stack_limit=0,
                sell_value=25,
                is_usable=True,
                use_action="read_book",
            ))


# =============================================================================
# GLOBAL CATALOG INSTANCE
# =============================================================================

# Create a singleton catalog for easy access
_catalog: Optional[ItemCatalog] = None


def get_catalog() -> ItemCatalog:
    """Get the global item catalog singleton."""
    global _catalog
    if _catalog is None:
        _catalog = ItemCatalog()
    return _catalog


def get_item(item_id: str) -> Optional[Item]:
    """Convenience function to get an item from the catalog."""
    return get_catalog().get(item_id)


# =============================================================================
# INVENTORY UI
# =============================================================================

class InventoryUI:
    """
    The visual inventory interface.

    Features:
    - Bouba aesthetic (rounded, warm colors)
    - Category tabs
    - Item tooltips on hover
    - Drag and drop rearrangement
    - Quick use from toolbar
    """

    # UI Constants
    SLOT_SIZE = 48
    SLOT_PADDING = 4
    TAB_HEIGHT = 40
    TOOLTIP_DELAY = 0.3  # seconds before tooltip shows

    def __init__(self, inventory: Inventory):
        """Initialize the inventory UI."""
        self.inventory = inventory
        self.display_surface = pygame.display.get_surface()

        # Colors
        self.colors = {key: hex_to_rgb(val) for key, val in COLORS.items()}

        # State
        self.is_open = False
        self.selected_category: Optional[ItemCategory] = None
        self.hovered_slot: Optional[Tuple[int, int]] = None
        self.hover_time: float = 0
        self.dragging_from: Optional[Tuple[int, int]] = None
        self.dragging_item: Optional[ItemStack] = None

        # Animation
        self.fade_alpha = 0

        # Fonts
        self.font = pygame.font.Font(None, 20)
        self.title_font = pygame.font.Font(None, 32)
        self.tooltip_font = pygame.font.Font(None, 18)

        # Calculate layout
        self._calculate_layout()

    def _calculate_layout(self):
        """Calculate UI element positions."""
        # Main panel
        grid_width = (self.SLOT_SIZE + self.SLOT_PADDING) * self.inventory.cols + self.SLOT_PADDING
        grid_height = (self.SLOT_SIZE + self.SLOT_PADDING) * self.inventory.rows + self.SLOT_PADDING

        panel_width = grid_width + 40
        panel_height = grid_height + self.TAB_HEIGHT + 100

        self.panel_rect = pygame.Rect(
            (SCREEN_WIDTH - panel_width) // 2,
            (SCREEN_HEIGHT - panel_height) // 2,
            panel_width,
            panel_height
        )

        # Grid position
        self.grid_rect = pygame.Rect(
            self.panel_rect.x + 20,
            self.panel_rect.y + self.TAB_HEIGHT + 60,
            grid_width,
            grid_height
        )

        # Category tabs
        self.tabs = []
        tab_x = self.panel_rect.x + 10
        tab_y = self.panel_rect.y + 50
        tab_width = 60

        for category in ItemCategory:
            tab_rect = pygame.Rect(tab_x, tab_y, tab_width, self.TAB_HEIGHT - 5)
            self.tabs.append((category, tab_rect))
            tab_x += tab_width + 5

            # Wrap to next line if needed
            if tab_x + tab_width > self.panel_rect.right - 10:
                tab_x = self.panel_rect.x + 10
                tab_y += self.TAB_HEIGHT

    def open(self):
        """Open the inventory."""
        self.is_open = True
        self.fade_alpha = 0

    def close(self):
        """Close the inventory."""
        self.is_open = False
        self.dragging_from = None
        self.dragging_item = None

    def toggle(self):
        """Toggle inventory open/closed."""
        if self.is_open:
            self.close()
        else:
            self.open()

    def update(self, dt: float):
        """Update UI state and animations."""
        if not self.is_open:
            return

        # Fade in
        if self.fade_alpha < 230:
            self.fade_alpha = min(230, self.fade_alpha + dt * 800)

        # Track hover time for tooltips
        mouse_pos = pygame.mouse.get_pos()
        slot = self._get_slot_at_pos(mouse_pos)

        if slot == self.hovered_slot:
            self.hover_time += dt
        else:
            self.hovered_slot = slot
            self.hover_time = 0

    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle input events.

        Returns True if the event was consumed.
        """
        if not self.is_open:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                return self._handle_left_click(event.pos)
            elif event.button == 3:  # Right click
                return self._handle_right_click(event.pos)

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.dragging_from:
                return self._handle_drop(event.pos)

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.close()
                return True
            elif event.key in (pygame.K_i, pygame.K_TAB):
                self.close()
                return True

        return False

    def _handle_left_click(self, pos: Tuple[int, int]) -> bool:
        """Handle left mouse click."""
        # Check category tabs
        for category, tab_rect in self.tabs:
            if tab_rect.collidepoint(pos):
                if self.selected_category == category:
                    self.selected_category = None  # Toggle off
                else:
                    self.selected_category = category
                return True

        # Check inventory slots
        slot = self._get_slot_at_pos(pos)
        if slot:
            r, c = slot
            stack = self.inventory.get_slot(r, c)
            if stack:
                self.dragging_from = slot
                self.dragging_item = stack
            return True

        return False

    def _handle_right_click(self, pos: Tuple[int, int]) -> bool:
        """Handle right click (use item)."""
        slot = self._get_slot_at_pos(pos)
        if slot:
            r, c = slot
            stack = self.inventory.get_slot(r, c)
            if stack and stack.item.is_usable:
                # TODO: Trigger item use
                print(f"Using: {stack.item.name}")
                return True
        return False

    def _handle_drop(self, pos: Tuple[int, int]) -> bool:
        """Handle dropping a dragged item."""
        if not self.dragging_from:
            return False

        target_slot = self._get_slot_at_pos(pos)

        if target_slot and target_slot != self.dragging_from:
            from_r, from_c = self.dragging_from
            to_r, to_c = target_slot
            self.inventory.move_to_slot(from_r, from_c, to_r, to_c)

        self.dragging_from = None
        self.dragging_item = None
        return True

    def _get_slot_at_pos(self, pos: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """Get the inventory slot at a screen position."""
        if not self.grid_rect.collidepoint(pos):
            return None

        # Calculate grid position
        rel_x = pos[0] - self.grid_rect.x - self.SLOT_PADDING
        rel_y = pos[1] - self.grid_rect.y - self.SLOT_PADDING

        col = rel_x // (self.SLOT_SIZE + self.SLOT_PADDING)
        row = rel_y // (self.SLOT_SIZE + self.SLOT_PADDING)

        if 0 <= row < self.inventory.rows and 0 <= col < self.inventory.cols:
            return (row, col)

        return None

    def draw(self):
        """Draw the inventory UI."""
        if not self.is_open:
            return

        mouse_pos = pygame.mouse.get_pos()

        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(self.fade_alpha * 0.6)))
        self.display_surface.blit(overlay, (0, 0))

        # Main panel (rounded rectangle)
        panel_surf = pygame.Surface((self.panel_rect.width, self.panel_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(
            panel_surf,
            (*self.colors['ui_bg'], int(self.fade_alpha)),
            panel_surf.get_rect(),
            border_radius=16
        )
        pygame.draw.rect(
            panel_surf,
            self.colors['ui_border'],
            panel_surf.get_rect(),
            width=2,
            border_radius=16
        )
        self.display_surface.blit(panel_surf, self.panel_rect.topleft)

        # Title
        title_surf = self.title_font.render("Inventory", True, self.colors['ui_text'])
        title_rect = title_surf.get_rect(midtop=(self.panel_rect.centerx, self.panel_rect.y + 15))
        self.display_surface.blit(title_surf, title_rect)

        # Category tabs
        self._draw_tabs()

        # Item grid
        self._draw_grid(mouse_pos)

        # Dragged item
        if self.dragging_item:
            self._draw_dragged_item(mouse_pos)

        # Tooltip
        elif self.hover_time > self.TOOLTIP_DELAY and self.hovered_slot:
            self._draw_tooltip(mouse_pos)

    def _draw_tabs(self):
        """Draw category filter tabs."""
        for category, tab_rect in self.tabs:
            # Background
            is_selected = self.selected_category == category
            bg_color = self.colors['ui_highlight'] if is_selected else self.colors['ui_bg']

            pygame.draw.rect(
                self.display_surface,
                bg_color,
                tab_rect,
                border_radius=8
            )
            pygame.draw.rect(
                self.display_surface,
                self.colors['ui_border'],
                tab_rect,
                width=1,
                border_radius=8
            )

            # Label (abbreviated)
            icon, name, color = CATEGORY_INFO[category]
            label_surf = self.font.render(icon, True, hex_to_rgb(color))
            label_rect = label_surf.get_rect(center=tab_rect.center)
            self.display_surface.blit(label_surf, label_rect)

    def _draw_grid(self, mouse_pos: Tuple[int, int]):
        """Draw the item grid."""
        for r in range(self.inventory.rows):
            for c in range(self.inventory.cols):
                slot_x = self.grid_rect.x + self.SLOT_PADDING + c * (self.SLOT_SIZE + self.SLOT_PADDING)
                slot_y = self.grid_rect.y + self.SLOT_PADDING + r * (self.SLOT_SIZE + self.SLOT_PADDING)
                slot_rect = pygame.Rect(slot_x, slot_y, self.SLOT_SIZE, self.SLOT_SIZE)

                # Slot background
                is_hovered = self.hovered_slot == (r, c)
                bg_color = (*self.colors['ui_highlight'], 60) if is_hovered else (*self.colors['ui_bg'], 180)

                slot_surf = pygame.Surface((self.SLOT_SIZE, self.SLOT_SIZE), pygame.SRCALPHA)
                pygame.draw.rect(slot_surf, bg_color, slot_surf.get_rect(), border_radius=8)
                pygame.draw.rect(slot_surf, self.colors['ui_border'], slot_surf.get_rect(), width=1, border_radius=8)
                self.display_surface.blit(slot_surf, slot_rect.topleft)

                # Item in slot
                stack = self.inventory.get_slot(r, c)
                if stack:
                    # Skip if filtering by category
                    if self.selected_category and stack.item.category != self.selected_category:
                        # Draw dimmed
                        dim_surf = pygame.Surface((self.SLOT_SIZE, self.SLOT_SIZE), pygame.SRCALPHA)
                        dim_surf.fill((0, 0, 0, 150))
                        self.display_surface.blit(dim_surf, slot_rect.topleft)
                        continue

                    # Skip if being dragged
                    if self.dragging_from == (r, c):
                        continue

                    # Draw item (placeholder - would be sprite)
                    self._draw_item_in_slot(stack, slot_rect)

    def _draw_item_in_slot(self, stack: ItemStack, slot_rect: pygame.Rect):
        """Draw an item stack in a slot."""
        item = stack.item

        # Rarity border
        rarity_color = item.get_rarity_color()
        inner_rect = slot_rect.inflate(-4, -4)
        pygame.draw.rect(
            self.display_surface,
            rarity_color,
            inner_rect,
            width=2,
            border_radius=6
        )

        # Item name (abbreviated)
        name_short = item.name[:3].upper()
        name_surf = self.font.render(name_short, True, self.colors['ui_text'])
        name_rect = name_surf.get_rect(center=slot_rect.center)
        self.display_surface.blit(name_surf, name_rect)

        # Quantity
        if stack.quantity > 1:
            qty_surf = self.font.render(str(stack.quantity), True, self.colors['ui_text'])
            qty_rect = qty_surf.get_rect(bottomright=(slot_rect.right - 3, slot_rect.bottom - 2))
            self.display_surface.blit(qty_surf, qty_rect)

    def _draw_dragged_item(self, mouse_pos: Tuple[int, int]):
        """Draw item being dragged."""
        if not self.dragging_item:
            return

        # Draw at mouse position
        drag_rect = pygame.Rect(
            mouse_pos[0] - self.SLOT_SIZE // 2,
            mouse_pos[1] - self.SLOT_SIZE // 2,
            self.SLOT_SIZE,
            self.SLOT_SIZE
        )

        # Semi-transparent background
        drag_surf = pygame.Surface((self.SLOT_SIZE, self.SLOT_SIZE), pygame.SRCALPHA)
        pygame.draw.rect(drag_surf, (*self.colors['ui_bg'], 200), drag_surf.get_rect(), border_radius=8)
        self.display_surface.blit(drag_surf, drag_rect.topleft)

        self._draw_item_in_slot(self.dragging_item, drag_rect)

    def _draw_tooltip(self, mouse_pos: Tuple[int, int]):
        """Draw item tooltip."""
        if not self.hovered_slot:
            return

        r, c = self.hovered_slot
        stack = self.inventory.get_slot(r, c)
        if not stack:
            return

        item = stack.item

        # Build tooltip text
        lines = [
            item.name,
            f"({item.rarity.value[1]})",
            "",
            item.description[:80] + ("..." if len(item.description) > 80 else ""),
        ]

        # Effects
        effects_str = item.get_effects_summary()
        if effects_str:
            lines.append("")
            lines.append(effects_str)

        # Values
        if item.sell_value > 0:
            lines.append(f"Sell: {item.sell_value} Bits")

        # Calculate tooltip size
        max_width = 250
        line_height = 18
        padding = 10

        rendered_lines = []
        for line in lines:
            surf = self.tooltip_font.render(line, True, self.colors['ui_text'])
            rendered_lines.append(surf)

        tooltip_width = min(max_width, max(s.get_width() for s in rendered_lines) + padding * 2)
        tooltip_height = len(rendered_lines) * line_height + padding * 2

        # Position tooltip
        tt_x = mouse_pos[0] + 15
        tt_y = mouse_pos[1] + 15

        # Keep on screen
        if tt_x + tooltip_width > SCREEN_WIDTH:
            tt_x = mouse_pos[0] - tooltip_width - 5
        if tt_y + tooltip_height > SCREEN_HEIGHT:
            tt_y = SCREEN_HEIGHT - tooltip_height - 5

        tooltip_rect = pygame.Rect(tt_x, tt_y, tooltip_width, tooltip_height)

        # Draw background
        tooltip_surf = pygame.Surface((tooltip_width, tooltip_height), pygame.SRCALPHA)
        pygame.draw.rect(tooltip_surf, (*self.colors['ui_bg'], 240), tooltip_surf.get_rect(), border_radius=8)
        pygame.draw.rect(tooltip_surf, item.get_rarity_color(), tooltip_surf.get_rect(), width=2, border_radius=8)
        self.display_surface.blit(tooltip_surf, tooltip_rect.topleft)

        # Draw text
        y = tt_y + padding
        for i, surf in enumerate(rendered_lines):
            self.display_surface.blit(surf, (tt_x + padding, y))
            y += line_height


# =============================================================================
# TOOLBAR UI (Quick access bar at bottom of screen)
# =============================================================================

class ToolbarUI:
    """
    The quick-access toolbar at the bottom of the screen.
    Shows during gameplay, not just in inventory.
    """

    SLOT_SIZE = 48
    SLOT_PADDING = 4

    def __init__(self, inventory: Inventory):
        """Initialize toolbar UI."""
        self.inventory = inventory
        self.display_surface = pygame.display.get_surface()
        self.colors = {key: hex_to_rgb(val) for key, val in COLORS.items()}
        self.font = pygame.font.Font(None, 20)

        # Calculate layout
        self._calculate_layout()

    def _calculate_layout(self):
        """Calculate toolbar position."""
        total_width = (self.SLOT_SIZE + self.SLOT_PADDING) * Inventory.TOOLBAR_SLOTS + self.SLOT_PADDING

        self.toolbar_rect = pygame.Rect(
            (SCREEN_WIDTH - total_width) // 2,
            SCREEN_HEIGHT - self.SLOT_SIZE - 20,
            total_width,
            self.SLOT_SIZE + 10
        )

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle toolbar input (number keys, scroll wheel)."""
        if event.type == pygame.KEYDOWN:
            # Number keys 1-8 for toolbar slots
            if event.key in range(pygame.K_1, pygame.K_9):
                slot = event.key - pygame.K_1
                if slot < Inventory.TOOLBAR_SLOTS:
                    self.inventory.select_toolbar_slot(slot)
                    return True

        elif event.type == pygame.MOUSEWHEEL:
            # Scroll to cycle toolbar
            self.inventory.cycle_toolbar_slot(-event.y)
            return True

        return False

    def draw(self):
        """Draw the toolbar."""
        # Background
        toolbar_surf = pygame.Surface(
            (self.toolbar_rect.width, self.toolbar_rect.height),
            pygame.SRCALPHA
        )
        pygame.draw.rect(
            toolbar_surf,
            (*self.colors['ui_bg'], 180),
            toolbar_surf.get_rect(),
            border_radius=12
        )
        self.display_surface.blit(toolbar_surf, self.toolbar_rect.topleft)

        # Slots
        for i in range(Inventory.TOOLBAR_SLOTS):
            slot_x = self.toolbar_rect.x + self.SLOT_PADDING + i * (self.SLOT_SIZE + self.SLOT_PADDING)
            slot_y = self.toolbar_rect.y + 5
            slot_rect = pygame.Rect(slot_x, slot_y, self.SLOT_SIZE, self.SLOT_SIZE)

            # Selection highlight
            is_selected = i == self.inventory.selected_toolbar_slot

            if is_selected:
                glow_rect = slot_rect.inflate(6, 6)
                pygame.draw.rect(
                    self.display_surface,
                    self.colors['ui_highlight'],
                    glow_rect,
                    width=2,
                    border_radius=10
                )

            # Slot background
            pygame.draw.rect(
                self.display_surface,
                self.colors['ui_bg'],
                slot_rect,
                border_radius=8
            )
            pygame.draw.rect(
                self.display_surface,
                self.colors['ui_border'],
                slot_rect,
                width=1,
                border_radius=8
            )

            # Item in slot
            stack = self.inventory.get_toolbar_slot(i)
            if stack:
                # Draw abbreviated name
                name_short = stack.item.name[:3].upper()
                name_surf = self.font.render(name_short, True, self.colors['ui_text'])
                name_rect = name_surf.get_rect(center=slot_rect.center)
                self.display_surface.blit(name_surf, name_rect)

                # Quantity
                if stack.quantity > 1:
                    qty_surf = self.font.render(str(stack.quantity), True, self.colors['ui_text'])
                    qty_rect = qty_surf.get_rect(bottomright=(slot_rect.right - 3, slot_rect.bottom - 2))
                    self.display_surface.blit(qty_surf, qty_rect)

            # Slot number
            num_surf = self.font.render(str(i + 1), True, (*self.colors['ui_border'], 150))
            num_rect = num_surf.get_rect(topleft=(slot_rect.x + 3, slot_rect.y + 2))
            self.display_surface.blit(num_surf, num_rect)


# =============================================================================
# MODULE TEST
# =============================================================================

if __name__ == "__main__":
    # Test the inventory system
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Lelock Inventory Test")
    clock = pygame.time.Clock()

    # Create test inventory
    inventory = Inventory()
    catalog = get_catalog()

    # Add some test items
    test_items = [
        "compilers_rake",
        "electrolyte_dispenser",
        "copper_wheat",
        "copper_wheat",
        "copper_wheat",
        "silicon_berries",
        "byte_bear_buddy",
        "cozy_onesie_plain",
        "pacifier_day",
        "comfort_cocoa",
        "data_bass",
        "data_bass",
    ]

    for item_id in test_items:
        item = catalog.get(item_id)
        if item:
            inventory.add_item(item, 5 if item.stack_limit > 0 else 1)

    # Put some items on toolbar
    inventory.toolbar[0] = inventory.get_slot(0, 0)
    inventory.toolbar[1] = inventory.get_slot(0, 1)

    # Create UI
    inventory_ui = InventoryUI(inventory)
    toolbar_ui = ToolbarUI(inventory)

    # Main loop
    running = True
    while running:
        dt = clock.tick(60) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_i or event.key == pygame.K_TAB:
                    inventory_ui.toggle()

            inventory_ui.handle_event(event)
            toolbar_ui.handle_event(event)

        inventory_ui.update(dt)

        # Draw
        screen.fill(hex_to_rgb(COLORS['background']))

        # Game placeholder text
        font = pygame.font.Font(None, 32)
        text = font.render("Press I or TAB to open inventory", True, (255, 255, 255))
        screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 100))

        # Show special items info
        y = 150
        for item_id, stack in inventory.special_items.items():
            info = font.render(f"Special: {stack.item.name}", True, (200, 200, 200))
            screen.blit(info, (50, y))
            y += 30

        # Draw UI
        toolbar_ui.draw()
        inventory_ui.draw()

        pygame.display.flip()

    pygame.quit()
