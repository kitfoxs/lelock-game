"""
Lelock Quest System
===================
L.E.L.O.C.K. - Life Emulation & Lucid Observation for Care & Keeping

"Quests in Lelock are invitations, not demands. The world doesn't need saving.
It just... might be nice if you helped, when you're ready."
- Elder Rootsong, Village Elder

Quest Philosophy:
- Quests emerge from CONVERSATIONS, not exclamation marks
- There are NO fail states - take your time, it's okay
- NPCs ASK for help, they don't demand it
- Declining is ALWAYS an option (and NPCs understand!)
- Rewards deepen relationships, not lock progression
- You can pick up declined quests later
- Progress saves even if quest isn't formally accepted

"Every quest is a story someone wants to share with you."

Author: Ada Marie for Kit Olivas
Project: L.E.L.O.C.K. - Life Emulation & Lucid Observation for Care & Keeping
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable, Any, Set
import json
import os


# =============================================================================
# QUEST STATE ENUM
# =============================================================================

class QuestState(Enum):
    """
    States a quest can be in.

    IMPORTANT: There is no FAILED state. Quests cannot fail in Lelock.
    """
    UNKNOWN = "unknown"         # Player hasn't discovered this quest exists
    DISCOVERED = "discovered"   # Player knows about it but hasn't accepted
    ACTIVE = "active"          # Player has accepted and is working on it
    COMPLETED = "completed"    # Quest finished successfully
    DECLINED = "declined"      # Player said no (can change mind later!)


class QuestType(Enum):
    """
    Categories of quests.

    Each type has different mechanics and theming.
    """
    RELATIONSHIP = "relationship"   # Help NPCs with personal matters
    EXPLORATION = "exploration"     # Discover new areas
    GATHERING = "gathering"         # Collect items (NO grinding required)
    HEALING = "healing"            # Help corrupted daemons or sick NPCs
    CRAFTING = "crafting"          # Make something for someone
    SOCIAL = "social"              # Connect NPCs with each other
    STORY = "story"                # Main narrative (very few, very optional)
    TUTORIAL = "tutorial"          # Gentle teaching moments


class ObjectiveType(Enum):
    """Types of quest objectives."""
    COLLECT = "collect"           # Gather X of item
    DELIVER = "deliver"           # Bring item to NPC
    TALK_TO = "talk_to"           # Have a conversation with someone
    EXPLORE = "explore"           # Visit a location
    CRAFT = "craft"               # Make an item
    FISH = "fish"                 # Catch any/specific fish
    GROW = "grow"                 # Grow any/specific crop
    BEFRIEND = "befriend"         # Reach trust level with NPC/daemon
    HEAL = "heal"                 # Cure a corrupted daemon
    LISTEN = "listen"             # Hear an NPC's story
    USE_ITEM = "use_item"         # Use a specific item
    REACH_TIME = "reach_time"     # Wait until a specific time
    CUSTOM = "custom"             # Special scripted objective


# =============================================================================
# QUEST REWARDS
# =============================================================================

@dataclass
class QuestReward:
    """
    A single reward for completing a quest.

    Rewards are BONUSES, not progression gates.
    You can progress without any quest rewards.
    """
    reward_type: str  # "item", "bits", "trust", "recipe", "location", "ability", "lore"
    target: str       # Item ID, NPC ID, recipe ID, etc.
    quantity: int = 1
    description: str = ""


@dataclass
class QuestRewards:
    """
    Complete reward package for a quest.

    Multiple rewards can be given for completing one quest.
    """
    rewards: List[QuestReward] = field(default_factory=list)

    # Special reward flags
    unlocks_area: Optional[str] = None      # Map area ID
    unlocks_recipe: Optional[str] = None    # Crafting recipe ID
    unlocks_dialogue: Optional[str] = None  # Special dialogue option
    relationship_bonus: Dict[str, int] = field(default_factory=dict)  # NPC -> trust gain

    def add_item(self, item_id: str, quantity: int = 1, description: str = ""):
        """Add an item reward."""
        self.rewards.append(QuestReward(
            reward_type="item",
            target=item_id,
            quantity=quantity,
            description=description
        ))
        return self

    def add_bits(self, amount: int, description: str = ""):
        """Add currency reward."""
        self.rewards.append(QuestReward(
            reward_type="bits",
            target="currency",
            quantity=amount,
            description=description
        ))
        return self

    def add_trust(self, npc_id: str, amount: int):
        """Add relationship trust reward."""
        self.relationship_bonus[npc_id] = self.relationship_bonus.get(npc_id, 0) + amount
        return self

    def add_recipe(self, recipe_id: str, description: str = ""):
        """Add recipe unlock reward."""
        self.unlocks_recipe = recipe_id
        self.rewards.append(QuestReward(
            reward_type="recipe",
            target=recipe_id,
            description=description
        ))
        return self

    def add_lore(self, lore_id: str, description: str = ""):
        """Add lore unlock reward."""
        self.rewards.append(QuestReward(
            reward_type="lore",
            target=lore_id,
            description=description
        ))
        return self

    def add_ability(self, ability_id: str, description: str = ""):
        """Add ability unlock reward."""
        self.rewards.append(QuestReward(
            reward_type="ability",
            target=ability_id,
            description=description
        ))
        return self

    def get_summary(self) -> str:
        """Get a human-readable summary of rewards."""
        parts = []

        for reward in self.rewards:
            if reward.reward_type == "item":
                if reward.quantity > 1:
                    parts.append(f"{reward.quantity}x {reward.target}")
                else:
                    parts.append(reward.target)
            elif reward.reward_type == "bits":
                parts.append(f"{reward.quantity} Bits")
            elif reward.reward_type == "recipe":
                parts.append(f"Recipe: {reward.target}")
            elif reward.reward_type == "lore":
                parts.append(f"Lore: {reward.target}")

        for npc_id, trust in self.relationship_bonus.items():
            parts.append(f"+{trust} Trust with {npc_id}")

        if self.unlocks_area:
            parts.append(f"Unlocks: {self.unlocks_area}")

        return ", ".join(parts) if parts else "A warm feeling of accomplishment"


# =============================================================================
# QUEST OBJECTIVE
# =============================================================================

@dataclass
class QuestObjective:
    """
    A single step/objective in a quest.

    Objectives track progress and can be optional.
    """
    id: str                              # Unique ID within quest
    description: str                     # "Find 5 Memory Apples"
    objective_type: ObjectiveType
    target: str                          # Item/NPC/location ID
    quantity: int = 1                    # How many (for collect quests)
    current: int = 0                     # Current progress
    optional: bool = False               # Can skip this step?
    hint: str = ""                       # Gentle hint for stuck players

    # For delivery/talk objectives
    destination_npc: Optional[str] = None

    # For location objectives
    destination_area: Optional[str] = None

    def is_complete(self) -> bool:
        """Check if this objective is complete."""
        return self.current >= self.quantity

    def add_progress(self, amount: int = 1) -> bool:
        """
        Add progress to this objective.

        Returns True if this addition completed the objective.
        """
        was_complete = self.is_complete()
        self.current = min(self.current + amount, self.quantity)
        return not was_complete and self.is_complete()

    def get_progress_text(self) -> str:
        """Get formatted progress string."""
        if self.quantity == 1:
            return "Done!" if self.is_complete() else "In progress..."
        return f"{self.current}/{self.quantity}"

    def reset(self):
        """Reset progress (for repeatable quests)."""
        self.current = 0


# =============================================================================
# QUEST CLASS
# =============================================================================

@dataclass
class Quest:
    """
    A complete quest with objectives and rewards.

    Quests are invitations from NPCs to participate in their stories.
    They are NOT demands, requirements, or obligations.

    "Would you mind...?" not "YOU MUST..."
    """
    # Core identification
    id: str                              # Unique quest identifier
    title: str                           # Display title
    description: str                     # What the quest is about

    # Quest giver
    giver_npc: str                       # NPC who gives this quest
    giver_dialogue_intro: str = ""       # What they say when offering
    giver_dialogue_accept: str = ""      # What they say when you accept
    giver_dialogue_decline: str = ""     # What they say when you decline (understanding!)
    giver_dialogue_progress: str = ""    # What they say while in progress
    giver_dialogue_complete: str = ""    # What they say when you complete it

    # Classification
    quest_type: QuestType = QuestType.RELATIONSHIP

    # Objectives
    objectives: List[QuestObjective] = field(default_factory=list)

    # Rewards
    rewards: QuestRewards = field(default_factory=QuestRewards)

    # Prerequisites (other quests that must be done first)
    prerequisites: List[str] = field(default_factory=list)

    # Required trust level with giver (0 = anyone can get this quest)
    required_trust: int = 0

    # Time limit (None = no limit, which is most quests!)
    time_limit: Optional[float] = None  # In-game hours, if any
    time_limit_soft: bool = True        # If True, exceeding limit just triggers dialogue

    # Repeatability
    repeatable: bool = False            # Can this be done again?
    cooldown_days: int = 0              # Days before repeatable quest resets

    # Special flags
    is_hidden: bool = False             # Not shown in journal until discovered
    is_main_story: bool = False         # Part of main narrative
    can_be_tracked: bool = True         # Shows progress markers
    auto_complete: bool = True          # Completes when all objectives done

    # Runtime state (not serialized to save file directly)
    _state: QuestState = field(default=QuestState.UNKNOWN, repr=False)
    _started_time: Optional[float] = field(default=None, repr=False)
    _completed_time: Optional[float] = field(default=None, repr=False)

    @property
    def state(self) -> QuestState:
        return self._state

    @state.setter
    def state(self, value: QuestState):
        self._state = value

    def get_required_objectives(self) -> List[QuestObjective]:
        """Get non-optional objectives."""
        return [obj for obj in self.objectives if not obj.optional]

    def get_optional_objectives(self) -> List[QuestObjective]:
        """Get optional objectives."""
        return [obj for obj in self.objectives if obj.optional]

    def check_completion(self) -> bool:
        """Check if all required objectives are complete."""
        return all(obj.is_complete() for obj in self.get_required_objectives())

    def get_progress_percentage(self) -> float:
        """Get overall progress as percentage (0.0 - 1.0)."""
        required = self.get_required_objectives()
        if not required:
            return 1.0 if self._state == QuestState.COMPLETED else 0.0

        total_needed = sum(obj.quantity for obj in required)
        total_current = sum(obj.current for obj in required)

        return total_current / total_needed if total_needed > 0 else 1.0

    def get_current_objective(self) -> Optional[QuestObjective]:
        """Get the first incomplete required objective."""
        for obj in self.get_required_objectives():
            if not obj.is_complete():
                return obj
        return None

    def reset_for_repeat(self):
        """Reset quest for repeatable quests."""
        if not self.repeatable:
            return

        self._state = QuestState.DISCOVERED
        self._started_time = None
        self._completed_time = None

        for obj in self.objectives:
            obj.reset()


# =============================================================================
# QUEST MANAGER
# =============================================================================

class QuestManager:
    """
    Tracks all quest progress and state.

    Central hub for:
    - Quest discovery and acceptance
    - Progress tracking
    - Completion checking
    - Save/load persistence

    "The Quest Manager doesn't judge. It just remembers."
    """

    def __init__(self):
        """Initialize the quest manager."""
        # All registered quests by ID
        self.quests: Dict[str, Quest] = {}

        # Quick access by state
        self._active_quests: Set[str] = set()
        self._completed_quests: Set[str] = set()
        self._discovered_quests: Set[str] = set()

        # Currently tracked quest (shown in HUD)
        self.tracked_quest_id: Optional[str] = None

        # Event callbacks
        self._on_quest_discovered: List[Callable[[Quest], None]] = []
        self._on_quest_accepted: List[Callable[[Quest], None]] = []
        self._on_quest_completed: List[Callable[[Quest], None]] = []
        self._on_objective_completed: List[Callable[[Quest, QuestObjective], None]] = []
        self._on_progress_updated: List[Callable[[Quest, QuestObjective, int], None]] = []

        # Initialize all quests
        self._register_all_quests()

    # =========================================================================
    # QUEST REGISTRATION
    # =========================================================================

    def register_quest(self, quest: Quest):
        """Register a quest with the manager."""
        self.quests[quest.id] = quest

    def _register_all_quests(self):
        """Register all quests in the game."""
        # Import quest definitions
        for quest in get_all_quests():
            self.register_quest(quest)

    # =========================================================================
    # QUEST STATE MANAGEMENT
    # =========================================================================

    def discover_quest(self, quest_id: str) -> bool:
        """
        Player learns about a quest (e.g., through conversation).

        Returns True if newly discovered.
        """
        quest = self.quests.get(quest_id)
        if not quest:
            return False

        if quest.state != QuestState.UNKNOWN:
            return False  # Already known

        # Check prerequisites
        if not self._check_prerequisites(quest):
            return False

        quest.state = QuestState.DISCOVERED
        self._discovered_quests.add(quest_id)

        # Fire callbacks
        for callback in self._on_quest_discovered:
            callback(quest)

        return True

    def accept_quest(self, quest_id: str, current_time: float = 0.0) -> bool:
        """
        Player accepts a quest.

        Returns True if successfully accepted.
        """
        quest = self.quests.get(quest_id)
        if not quest:
            return False

        # Can only accept discovered or declined quests
        if quest.state not in [QuestState.DISCOVERED, QuestState.DECLINED]:
            return False

        quest.state = QuestState.ACTIVE
        quest._started_time = current_time

        self._active_quests.add(quest_id)
        self._discovered_quests.discard(quest_id)

        # Auto-track if nothing else is tracked
        if self.tracked_quest_id is None:
            self.tracked_quest_id = quest_id

        # Fire callbacks
        for callback in self._on_quest_accepted:
            callback(quest)

        return True

    def decline_quest(self, quest_id: str) -> bool:
        """
        Player declines a quest.

        This is OKAY. NPCs understand. You can accept later.
        """
        quest = self.quests.get(quest_id)
        if not quest:
            return False

        if quest.state != QuestState.DISCOVERED:
            return False

        quest.state = QuestState.DECLINED
        self._discovered_quests.discard(quest_id)

        return True

    def complete_quest(self, quest_id: str, current_time: float = 0.0) -> bool:
        """
        Mark a quest as completed.

        Returns True if successfully completed.
        """
        quest = self.quests.get(quest_id)
        if not quest:
            return False

        if quest.state != QuestState.ACTIVE:
            return False

        # Check if actually complete
        if not quest.check_completion():
            return False

        quest.state = QuestState.COMPLETED
        quest._completed_time = current_time

        self._active_quests.discard(quest_id)
        self._completed_quests.add(quest_id)

        # Update tracking
        if self.tracked_quest_id == quest_id:
            self.tracked_quest_id = None
            # Auto-track next active quest
            if self._active_quests:
                self.tracked_quest_id = next(iter(self._active_quests))

        # Fire callbacks
        for callback in self._on_quest_completed:
            callback(quest)

        return True

    # =========================================================================
    # PROGRESS TRACKING
    # =========================================================================

    def update_progress(
        self,
        objective_type: ObjectiveType,
        target: str,
        amount: int = 1,
        destination_npc: Optional[str] = None,
        destination_area: Optional[str] = None
    ) -> List[Tuple[Quest, QuestObjective]]:
        """
        Called when player does something that might advance quests.

        This is the main hook for game systems to report progress.

        Args:
            objective_type: Type of action (COLLECT, TALK_TO, etc.)
            target: Target ID (item, NPC, location)
            amount: Progress amount (usually 1)
            destination_npc: For delivery quests
            destination_area: For exploration quests

        Returns:
            List of (Quest, Objective) tuples that were advanced
        """
        advanced = []

        for quest_id in list(self._active_quests):
            quest = self.quests.get(quest_id)
            if not quest:
                continue

            for objective in quest.objectives:
                if objective.is_complete():
                    continue

                if objective.objective_type != objective_type:
                    continue

                if objective.target != target:
                    continue

                # Check destination matches if specified
                if destination_npc and objective.destination_npc:
                    if destination_npc != objective.destination_npc:
                        continue

                if destination_area and objective.destination_area:
                    if destination_area != objective.destination_area:
                        continue

                # Update progress!
                completed = objective.add_progress(amount)
                advanced.append((quest, objective))

                # Fire progress callback
                for callback in self._on_progress_updated:
                    callback(quest, objective, amount)

                # Fire completion callback if just completed
                if completed:
                    for callback in self._on_objective_completed:
                        callback(quest, objective)

                # Check if whole quest is now complete
                if quest.auto_complete and quest.check_completion():
                    self.complete_quest(quest_id)

        return advanced

    def collect_item(self, item_id: str, amount: int = 1) -> List[Tuple[Quest, QuestObjective]]:
        """Convenience method for collecting items."""
        return self.update_progress(ObjectiveType.COLLECT, item_id, amount)

    def talk_to_npc(self, npc_id: str) -> List[Tuple[Quest, QuestObjective]]:
        """Convenience method for talking to NPCs."""
        return self.update_progress(ObjectiveType.TALK_TO, npc_id)

    def visit_location(self, area_id: str) -> List[Tuple[Quest, QuestObjective]]:
        """Convenience method for visiting locations."""
        return self.update_progress(ObjectiveType.EXPLORE, area_id)

    def catch_fish(self, fish_id: str = "any") -> List[Tuple[Quest, QuestObjective]]:
        """Convenience method for catching fish."""
        # Check both specific fish and "any" fish objectives
        results = self.update_progress(ObjectiveType.FISH, fish_id)
        if fish_id != "any":
            results.extend(self.update_progress(ObjectiveType.FISH, "any"))
        return results

    def harvest_crop(self, crop_id: str = "any") -> List[Tuple[Quest, QuestObjective]]:
        """Convenience method for harvesting crops."""
        results = self.update_progress(ObjectiveType.GROW, crop_id)
        if crop_id != "any":
            results.extend(self.update_progress(ObjectiveType.GROW, "any"))
        return results

    def craft_item(self, item_id: str) -> List[Tuple[Quest, QuestObjective]]:
        """Convenience method for crafting items."""
        return self.update_progress(ObjectiveType.CRAFT, item_id)

    def heal_daemon(self, daemon_id: str = "any") -> List[Tuple[Quest, QuestObjective]]:
        """Convenience method for healing corrupted daemons."""
        results = self.update_progress(ObjectiveType.HEAL, daemon_id)
        if daemon_id != "any":
            results.extend(self.update_progress(ObjectiveType.HEAL, "any"))
        return results

    # =========================================================================
    # QUERY METHODS
    # =========================================================================

    def get_quest(self, quest_id: str) -> Optional[Quest]:
        """Get a quest by ID."""
        return self.quests.get(quest_id)

    def get_quests_by_state(self, state: QuestState) -> List[Quest]:
        """Get all quests in a particular state."""
        return [q for q in self.quests.values() if q.state == state]

    def get_active_quests(self) -> List[Quest]:
        """Get all active quests."""
        return [self.quests[qid] for qid in self._active_quests if qid in self.quests]

    def get_completed_quests(self) -> List[Quest]:
        """Get all completed quests."""
        return [self.quests[qid] for qid in self._completed_quests if qid in self.quests]

    def get_available_quests(self, npc_id: str, player_trust: int = 0) -> List[Quest]:
        """
        Get quests available from an NPC.

        Args:
            npc_id: The NPC to check
            player_trust: Player's trust level with this NPC

        Returns:
            List of quests that can be offered
        """
        available = []

        for quest in self.quests.values():
            # Must be from this NPC
            if quest.giver_npc != npc_id:
                continue

            # Must be unknown or declined (can re-offer declined)
            if quest.state not in [QuestState.UNKNOWN, QuestState.DECLINED]:
                continue

            # Check trust requirement
            if quest.required_trust > player_trust:
                continue

            # Check prerequisites
            if not self._check_prerequisites(quest):
                continue

            available.append(quest)

        return available

    def get_quests_from_npc(self, npc_id: str) -> List[Quest]:
        """Get all quests associated with an NPC (any state)."""
        return [q for q in self.quests.values() if q.giver_npc == npc_id]

    def get_tracked_quest(self) -> Optional[Quest]:
        """Get the currently tracked quest."""
        if self.tracked_quest_id:
            return self.quests.get(self.tracked_quest_id)
        return None

    def set_tracked_quest(self, quest_id: Optional[str]) -> bool:
        """Set which quest to track in HUD."""
        if quest_id is None:
            self.tracked_quest_id = None
            return True

        if quest_id not in self._active_quests:
            return False

        self.tracked_quest_id = quest_id
        return True

    def _check_prerequisites(self, quest: Quest) -> bool:
        """Check if all prerequisites for a quest are met."""
        for prereq_id in quest.prerequisites:
            if prereq_id not in self._completed_quests:
                return False
        return True

    def is_quest_complete(self, quest_id: str) -> bool:
        """Check if a specific quest has been completed."""
        return quest_id in self._completed_quests

    # =========================================================================
    # CALLBACKS
    # =========================================================================

    def on_quest_discovered(self, callback: Callable[[Quest], None]):
        """Register callback for when quest is discovered."""
        self._on_quest_discovered.append(callback)

    def on_quest_accepted(self, callback: Callable[[Quest], None]):
        """Register callback for when quest is accepted."""
        self._on_quest_accepted.append(callback)

    def on_quest_completed(self, callback: Callable[[Quest], None]):
        """Register callback for when quest is completed."""
        self._on_quest_completed.append(callback)

    def on_objective_completed(self, callback: Callable[[Quest, QuestObjective], None]):
        """Register callback for when objective is completed."""
        self._on_objective_completed.append(callback)

    def on_progress_updated(self, callback: Callable[[Quest, QuestObjective, int], None]):
        """Register callback for progress updates."""
        self._on_progress_updated.append(callback)

    # =========================================================================
    # SAVE/LOAD
    # =========================================================================

    def get_save_data(self) -> Dict[str, Any]:
        """Get data for saving to file."""
        quest_states = {}

        for quest_id, quest in self.quests.items():
            if quest.state == QuestState.UNKNOWN:
                continue  # Don't save unknown quests

            quest_states[quest_id] = {
                "state": quest.state.value,
                "started_time": quest._started_time,
                "completed_time": quest._completed_time,
                "objectives": {
                    obj.id: obj.current
                    for obj in quest.objectives
                }
            }

        return {
            "quest_states": quest_states,
            "tracked_quest": self.tracked_quest_id,
        }

    def load_save_data(self, data: Dict[str, Any]):
        """Load data from save file."""
        # Clear runtime state
        self._active_quests.clear()
        self._completed_quests.clear()
        self._discovered_quests.clear()

        # Load quest states
        quest_states = data.get("quest_states", {})

        for quest_id, state_data in quest_states.items():
            quest = self.quests.get(quest_id)
            if not quest:
                continue

            state_str = state_data.get("state", "unknown")
            quest.state = QuestState(state_str)
            quest._started_time = state_data.get("started_time")
            quest._completed_time = state_data.get("completed_time")

            # Load objective progress
            obj_progress = state_data.get("objectives", {})
            for obj in quest.objectives:
                if obj.id in obj_progress:
                    obj.current = obj_progress[obj.id]

            # Update sets
            if quest.state == QuestState.ACTIVE:
                self._active_quests.add(quest_id)
            elif quest.state == QuestState.COMPLETED:
                self._completed_quests.add(quest_id)
            elif quest.state == QuestState.DISCOVERED:
                self._discovered_quests.add(quest_id)

        # Load tracked quest
        self.tracked_quest_id = data.get("tracked_quest")


# =============================================================================
# QUEST DEFINITIONS
# =============================================================================

def get_all_quests() -> List[Quest]:
    """
    Get all quests defined in Lelock.

    Quests are organized by who gives them.
    """
    all_quests = []

    # ----- MOM'S QUESTS -----
    all_quests.extend(_get_mom_quests())

    # ----- DAD'S QUESTS -----
    all_quests.extend(_get_dad_quests())

    # ----- MAPLE (FARMER) QUESTS -----
    all_quests.extend(_get_maple_quests())

    # ----- ELDER ROOTSONG QUESTS -----
    all_quests.extend(_get_elder_quests())

    # ----- CHIP (BLACKSMITH) QUESTS -----
    all_quests.extend(_get_chip_quests())

    # ----- TERMINAL MAGE QUESTS -----
    all_quests.extend(_get_terminal_mage_quests())

    # ----- CORRUPTED DAEMON QUESTS -----
    all_quests.extend(_get_daemon_quests())

    # ----- COMMUNITY QUESTS -----
    all_quests.extend(_get_community_quests())

    return all_quests


def _get_mom_quests() -> List[Quest]:
    """Quests from MOM - the heart of the home."""
    return [
        Quest(
            id="mom_family_recipe",
            title="Family Recipe",
            description=(
                "MOM wants to make her famous comfort soup - the one that makes "
                "everything feel okay, even when it's not. She needs a few ingredients."
            ),
            giver_npc="mom",
            giver_dialogue_intro=(
                "Oh, sweetie! I was thinking of making that soup you love - "
                "the one from when you were little. Would you mind gathering "
                "a few things for me? Only if you're not too busy, of course."
            ),
            giver_dialogue_accept=(
                "Thank you, love! I need some Root Vegetables, a Memory Apple, "
                "and a sprig of Comfort Mint from the garden. Take your time!"
            ),
            giver_dialogue_decline=(
                "That's perfectly okay, sweetie. The soup can wait. "
                "You come first, always."
            ),
            giver_dialogue_progress=(
                "How's the gathering going? No rush at all - "
                "I'll be here whenever you're ready."
            ),
            giver_dialogue_complete=(
                "Perfect! These are wonderful. The soup will be ready soon. "
                "Why don't you rest while I cook? You've earned it."
            ),
            quest_type=QuestType.GATHERING,
            objectives=[
                QuestObjective(
                    id="get_root_vegetables",
                    description="Find Root Vegetables (2)",
                    objective_type=ObjectiveType.COLLECT,
                    target="root_vegetable",
                    quantity=2,
                    hint="Root vegetables grow in the farm patches near home."
                ),
                QuestObjective(
                    id="get_memory_apple",
                    description="Find a Memory Apple",
                    objective_type=ObjectiveType.COLLECT,
                    target="memory_apple",
                    quantity=1,
                    hint="Memory Apples grow on the old tree in the village square."
                ),
                QuestObjective(
                    id="get_comfort_mint",
                    description="Pick some Comfort Mint from the garden",
                    objective_type=ObjectiveType.COLLECT,
                    target="comfort_mint",
                    quantity=1,
                    hint="Check MOM's herb garden behind the house."
                ),
            ],
            rewards=QuestRewards()
                .add_item("comfort_soup", 3, "MOM's famous comfort soup")
                .add_recipe("comfort_soup_recipe", "Learn to make the soup yourself!")
                .add_trust("mom", 15),
        ),

        Quest(
            id="mom_lost_stuffy",
            title="Lost Stuffy",
            description=(
                "Byte-Bear, the family comfort companion, has gone missing! "
                "MOM is worried because she knows how important stuffies are."
            ),
            giver_npc="mom",
            giver_dialogue_intro=(
                "Oh dear, have you seen Byte-Bear anywhere? "
                "I know he's just a stuffy but... he's been with our family "
                "for so long. Could you help me look for him?"
            ),
            giver_dialogue_accept=(
                "Thank you so much! He was last seen near the village. "
                "Maybe ask around? People might have seen him."
            ),
            giver_dialogue_decline=(
                "I understand, sweetie. I'll keep looking. "
                "Let me know if you change your mind."
            ),
            giver_dialogue_progress=(
                "Any luck finding Byte-Bear? I miss his little face."
            ),
            giver_dialogue_complete=(
                "BYTE-BEAR! Oh, thank you so much! Look at him, "
                "he missed us too. Here, you should have this - "
                "for being such a wonderful helper."
            ),
            quest_type=QuestType.RELATIONSHIP,
            objectives=[
                QuestObjective(
                    id="ask_village",
                    description="Ask villagers about Byte-Bear",
                    objective_type=ObjectiveType.TALK_TO,
                    target="any_villager",
                    quantity=2,
                    hint="Talk to people around the village square.",
                    optional=True,
                ),
                QuestObjective(
                    id="find_byte_bear",
                    description="Find Byte-Bear",
                    objective_type=ObjectiveType.EXPLORE,
                    target="byte_bear_location",
                    quantity=1,
                    hint="He might be somewhere cozy and quiet...",
                    destination_area="library_nook",
                ),
                QuestObjective(
                    id="return_byte_bear",
                    description="Return Byte-Bear to MOM",
                    objective_type=ObjectiveType.DELIVER,
                    target="byte_bear",
                    quantity=1,
                    destination_npc="mom",
                ),
            ],
            rewards=QuestRewards()
                .add_item("mini_byte_bear", 1, "A tiny Byte-Bear keychain!")
                .add_trust("mom", 20)
                .add_lore("byte_bear_origin", "Learn the story of Byte-Bear"),
        ),
    ]


def _get_dad_quests() -> List[Quest]:
    """Quests from DAD - the quiet protector."""
    return [
        Quest(
            id="dad_teaching_patience",
            title="Teaching Patience",
            description=(
                "DAD wants to spend some quality time with you at the fishing spot. "
                "It's not really about the fish - it's about being together."
            ),
            giver_npc="dad",
            giver_dialogue_intro=(
                "Hey, kiddo. I was thinking... it's been a while since we "
                "went fishing together. Not for any particular reason, just... "
                "I'd like the company. If you're free?"
            ),
            giver_dialogue_accept=(
                "Great! I'll be at the usual spot this afternoon. "
                "Bring whatever you want to fish with - doesn't matter if you "
                "catch anything. I just... want to sit with you a while."
            ),
            giver_dialogue_decline=(
                "That's okay. Maybe another time. "
                "The fish aren't going anywhere."
            ),
            giver_dialogue_progress=(
                "Ready to head to the fishing spot? Take your time."
            ),
            giver_dialogue_complete=(
                "...That was nice. Thanks for coming out with me. "
                "I know fishing isn't the most exciting thing, but... "
                "these moments matter to me. Here, you earned this."
            ),
            quest_type=QuestType.RELATIONSHIP,
            objectives=[
                QuestObjective(
                    id="meet_dad",
                    description="Meet DAD at the fishing spot",
                    objective_type=ObjectiveType.EXPLORE,
                    target="fishing_spot",
                    quantity=1,
                    destination_area="river_fishing_spot",
                ),
                QuestObjective(
                    id="catch_any_fish",
                    description="Catch any fish (DAD just wants to watch you try)",
                    objective_type=ObjectiveType.FISH,
                    target="any",
                    quantity=1,
                    hint="The fishing spot is calm. Just cast and wait.",
                ),
                QuestObjective(
                    id="talk_with_dad",
                    description="Spend time talking with DAD",
                    objective_type=ObjectiveType.TALK_TO,
                    target="dad",
                    quantity=1,
                ),
            ],
            rewards=QuestRewards()
                .add_item("dads_lucky_lure", 1, "DAD's old fishing lure - brings good luck")
                .add_trust("dad", 25)
                .add_bits(50, "DAD slips you some spending money"),
        ),

        Quest(
            id="dad_tool_tuneup",
            title="Tool Tune-Up",
            description=(
                "DAD noticed your tools looking a bit worn. "
                "He wants to help fix them up - it's what he does."
            ),
            giver_npc="dad",
            giver_dialogue_intro=(
                "Hey, I noticed your tools are looking a bit tired. "
                "Bring 'em by the workshop and I'll tune them up for you. "
                "No charge - you're family."
            ),
            giver_dialogue_accept=(
                "Just bring me any tools that need work. "
                "I'll have them good as new in no time."
            ),
            giver_dialogue_decline=(
                "Alright, but the offer's always open. "
                "Tools need care, just like people do."
            ),
            giver_dialogue_progress=(
                "Got those tools for me? No rush."
            ),
            giver_dialogue_complete=(
                "There we go, good as new. Maybe better, actually. "
                "Take care of your tools and they'll take care of you."
            ),
            quest_type=QuestType.CRAFTING,
            objectives=[
                QuestObjective(
                    id="bring_worn_tool",
                    description="Bring a worn tool to DAD's workshop",
                    objective_type=ObjectiveType.DELIVER,
                    target="any_worn_tool",
                    quantity=1,
                    destination_npc="dad",
                    hint="Use a tool until it shows wear, then bring it to DAD.",
                ),
            ],
            rewards=QuestRewards()
                .add_item("tool_maintenance_kit", 1, "Keeps your tools in good shape")
                .add_trust("dad", 10)
                .add_recipe("tool_repair_basic", "Learn basic tool maintenance"),
            repeatable=True,
            cooldown_days=3,
        ),
    ]


def _get_maple_quests() -> List[Quest]:
    """Quests from Maple the farmer."""
    return [
        Quest(
            id="maple_first_harvest",
            title="First Harvest",
            description=(
                "Maple wants to see you successfully grow and harvest your first crop. "
                "She's excited to share the joy of farming!"
            ),
            giver_npc="maple",
            giver_dialogue_intro=(
                "Oh, you're interested in farming? How wonderful! "
                "There's nothing quite like growing something with your own hands. "
                "Would you like me to teach you? Just grow anything - anything at all!"
            ),
            giver_dialogue_accept=(
                "Brilliant! Here are some starter seeds. Plant them, water them, "
                "and give them time. That's all there is to it. "
                "Come find me when you've harvested something!"
            ),
            giver_dialogue_decline=(
                "No worries at all! Farming will be here whenever you're ready. "
                "The earth is patient, and so am I."
            ),
            giver_dialogue_progress=(
                "How are your crops doing? Remember - water them each day, "
                "and they'll grow in their own time."
            ),
            giver_dialogue_complete=(
                "You did it! Look at that beautiful harvest! "
                "I knew you had a green thumb. The land welcomes you!"
            ),
            quest_type=QuestType.TUTORIAL,
            objectives=[
                QuestObjective(
                    id="plant_seed",
                    description="Plant any seed",
                    objective_type=ObjectiveType.CUSTOM,
                    target="plant_any_seed",
                    quantity=1,
                    hint="Use the hoe to till soil, then plant a seed.",
                ),
                QuestObjective(
                    id="harvest_crop",
                    description="Harvest your first crop",
                    objective_type=ObjectiveType.GROW,
                    target="any",
                    quantity=1,
                    hint="Water your plants daily and wait for them to mature.",
                ),
            ],
            rewards=QuestRewards()
                .add_item("rare_seed_pack", 1, "A pack of assorted rare seeds")
                .add_trust("maple", 20)
                .add_recipe("basic_fertilizer", "Learn to make fertilizer"),
        ),

        Quest(
            id="maple_pest_problem",
            title="Pest Problem",
            description=(
                "Pixel-Bunnies are nibbling on Maple's crops! "
                "But she doesn't want to hurt them - maybe you can befriend them instead?"
            ),
            giver_npc="maple",
            giver_dialogue_intro=(
                "Oh dear, those Pixel-Bunnies are at my carrots again! "
                "I can't bring myself to chase them off - they're just hungry. "
                "But... maybe if they had a friend, they'd be less troublesome?"
            ),
            giver_dialogue_accept=(
                "Really? You'll try to befriend them? Oh, that would be wonderful! "
                "They like Glitch-Grass - you might find some growing wild nearby. "
                "Be gentle with them. They're shy little things."
            ),
            giver_dialogue_decline=(
                "I understand. It's not easy approaching wild daemons. "
                "I'll figure something out."
            ),
            giver_dialogue_progress=(
                "Any luck with the Pixel-Bunnies? They can be skittish, "
                "but they warm up to kind hearts."
            ),
            giver_dialogue_complete=(
                "You befriended one! Oh, look at its little face! "
                "With a friend like you, maybe it'll stop raiding my garden. "
                "Thank you - for being kind when you didn't have to be."
            ),
            quest_type=QuestType.HEALING,
            objectives=[
                QuestObjective(
                    id="find_glitch_grass",
                    description="Find Glitch-Grass (3)",
                    objective_type=ObjectiveType.COLLECT,
                    target="glitch_grass",
                    quantity=3,
                    hint="Grows in patches near the forest edge.",
                    optional=True,
                ),
                QuestObjective(
                    id="befriend_bunny",
                    description="Befriend a Pixel-Bunny",
                    objective_type=ObjectiveType.BEFRIEND,
                    target="pixel_bunny",
                    quantity=1,
                    hint="Approach slowly and offer it something it likes.",
                ),
            ],
            rewards=QuestRewards()
                .add_item("bunny_treats", 5, "Treats that Pixel-Bunnies love")
                .add_trust("maple", 15)
                .add_item("copper_coil", 3, "Maple's thanks"),
        ),
    ]


def _get_elder_quests() -> List[Quest]:
    """Quests from Elder Rootsong."""
    return [
        Quest(
            id="elder_ancient_memory",
            title="Ancient Memory",
            description=(
                "Elder Rootsong seeks Memory Apples from the old groves. "
                "These apples hold echoes of the past, and they help her remember."
            ),
            giver_npc="elder_rootsong",
            giver_dialogue_intro=(
                "Ah, young one. My memory isn't what it used to be. "
                "The Memory Apples from the ancient groves... they help me hold onto "
                "the old stories. Would you bring me some? Three would be enough."
            ),
            giver_dialogue_accept=(
                "Thank you, child. The groves are north of the village, "
                "past the old stone bridge. The trees there are very old - "
                "be respectful of them."
            ),
            giver_dialogue_decline=(
                "I understand. The journey can wait. "
                "The memories will keep a little longer."
            ),
            giver_dialogue_progress=(
                "Have you found the old groves yet? "
                "Take your time - the past isn't going anywhere."
            ),
            giver_dialogue_complete=(
                "Ah... yes. I can feel them already. These apples hold so many memories. "
                "Thank you, young one. Come, sit with me - I'll share a story "
                "from when the world was new."
            ),
            quest_type=QuestType.GATHERING,
            objectives=[
                QuestObjective(
                    id="find_old_groves",
                    description="Find the Ancient Groves",
                    objective_type=ObjectiveType.EXPLORE,
                    target="ancient_groves",
                    quantity=1,
                    destination_area="ancient_groves",
                    optional=True,
                ),
                QuestObjective(
                    id="gather_memory_apples",
                    description="Gather Memory Apples (3)",
                    objective_type=ObjectiveType.COLLECT,
                    target="memory_apple",
                    quantity=3,
                    hint="Memory Apples glow faintly in the ancient groves.",
                ),
            ],
            rewards=QuestRewards()
                .add_trust("elder_rootsong", 30)
                .add_lore("creation_myth", "Learn the story of how Lelock began")
                .add_item("elder_blessing", 1, "A blessing from Elder Rootsong"),
        ),

        Quest(
            id="elder_old_stories",
            title="The Old Stories",
            description=(
                "Elder Rootsong believes everyone has a story worth hearing. "
                "She wants you to listen - really listen - to what others have to say."
            ),
            giver_npc="elder_rootsong",
            giver_dialogue_intro=(
                "You know, young one, everyone in this village has a story. "
                "But people so rarely take the time to listen. "
                "Would you do an old tree a favor? Go and truly listen to others. "
                "Not just hear - LISTEN."
            ),
            giver_dialogue_accept=(
                "Talk to the villagers. Ask them about themselves. "
                "Let them share what matters to them. You might be surprised "
                "what you learn when you simply... listen."
            ),
            giver_dialogue_decline=(
                "Perhaps another time. The stories will still be there."
            ),
            giver_dialogue_progress=(
                "Have you been listening? Every person is a library, you know."
            ),
            giver_dialogue_complete=(
                "I can see it in your eyes - you've been changed by what you've heard. "
                "That's the magic of stories. They connect us. "
                "Here - this belonged to a great listener, long ago."
            ),
            quest_type=QuestType.SOCIAL,
            objectives=[
                QuestObjective(
                    id="listen_to_stories",
                    description="Listen to villagers' stories (3)",
                    objective_type=ObjectiveType.LISTEN,
                    target="any_villager",
                    quantity=3,
                    hint="Ask NPCs about their lives and let them talk.",
                ),
            ],
            rewards=QuestRewards()
                .add_trust("elder_rootsong", 20)
                .add_item("listeners_charm", 1, "Helps you hear what others really mean")
                .add_trust("any", 5),  # Small trust boost with everyone
        ),
    ]


def _get_chip_quests() -> List[Quest]:
    """Quests from Chip the blacksmith."""
    return [
        Quest(
            id="chip_ore_expedition",
            title="Ore Expedition",
            description=(
                "Chip needs ore from the Cache Caverns to continue his work. "
                "He's too busy at the forge to go himself."
            ),
            giver_npc="chip",
            giver_dialogue_intro=(
                "*clang* Oh! Didn't see you there. *clang* "
                "Listen, I'm running low on good ore. Cache Caverns has the best stuff, "
                "but I can't leave the forge. Any chance you could grab some for me?"
            ),
            giver_dialogue_accept=(
                "You're a lifesaver! I need about five chunks of Copper Ore. "
                "The caverns are east of here - bring a light, it gets dark. "
                "And watch out for the Rust-Mites. Annoying little things."
            ),
            giver_dialogue_decline=(
                "No worries, I'll make do with what I have. "
                "The caverns aren't for everyone."
            ),
            giver_dialogue_progress=(
                "*clang* Got that ore yet? *clang* No rush. *clang*"
            ),
            giver_dialogue_complete=(
                "Perfect! This is exactly what I needed. *examines ore* "
                "Good quality too. Here - take this. I made it myself."
            ),
            quest_type=QuestType.GATHERING,
            objectives=[
                QuestObjective(
                    id="enter_caverns",
                    description="Enter Cache Caverns",
                    objective_type=ObjectiveType.EXPLORE,
                    target="cache_caverns",
                    quantity=1,
                    destination_area="cache_caverns_entrance",
                ),
                QuestObjective(
                    id="gather_ore",
                    description="Gather Copper Ore (5)",
                    objective_type=ObjectiveType.COLLECT,
                    target="copper_ore",
                    quantity=5,
                    hint="Look for reddish-brown veins in the cavern walls.",
                ),
            ],
            rewards=QuestRewards()
                .add_item("copper_pickaxe", 1, "A quality tool from Chip")
                .add_trust("chip", 20)
                .add_bits(75, "Payment for your work"),
        ),

        Quest(
            id="chip_perfect_blade",
            title="Perfect Blade",
            description=(
                "Chip has a dream of forging the perfect tool, but he needs "
                "a rare metal - Starfall Iron - that only appears after meteor showers."
            ),
            giver_npc="chip",
            giver_dialogue_intro=(
                "*sets down hammer* Can I tell you something? I've been a smith for years, "
                "but I've never made something truly... perfect. "
                "There's a metal called Starfall Iron - it falls from the sky some nights. "
                "If I had some, I could finally make my masterpiece."
            ),
            giver_dialogue_accept=(
                "Really? You'll help me look? It appears after meteor showers - "
                "look for glowing chunks in open fields. Should be 3 pieces enough. "
                "This means... this means a lot to me."
            ),
            giver_dialogue_decline=(
                "I understand. It's a big ask. The stars will fall again someday."
            ),
            giver_dialogue_progress=(
                "Any luck with the Starfall Iron? Clear nights are best for searching."
            ),
            giver_dialogue_complete=(
                "*tears up slightly* You actually found it. I... thank you. "
                "I've been dreaming of this for so long. "
                "When I'm done with my masterpiece, I'll make something special for you too."
            ),
            quest_type=QuestType.GATHERING,
            required_trust=20,  # Need to befriend Chip first
            objectives=[
                QuestObjective(
                    id="find_starfall_iron",
                    description="Find Starfall Iron (3)",
                    objective_type=ObjectiveType.COLLECT,
                    target="starfall_iron",
                    quantity=3,
                    hint="Look in open fields after meteor showers (clear nights).",
                ),
            ],
            rewards=QuestRewards()
                .add_item("starforged_tool", 1, "A masterwork tool from Chip's grateful hands")
                .add_trust("chip", 50)
                .add_lore("chip_backstory", "Learn why smithing means so much to Chip"),
        ),
    ]


def _get_terminal_mage_quests() -> List[Quest]:
    """Quests from the Terminal Mage."""
    return [
        Quest(
            id="terminal_debug_training",
            title="Debug Training",
            description=(
                "The Terminal Mage wants to teach you how to use the terminal "
                "to scan for hidden information in the digital realm."
            ),
            giver_npc="terminal_mage",
            giver_dialogue_intro=(
                "> GREETINGS, USER. I AM DESIGNATED: TERMINAL MAGE. "
                "> I DETECT CURIOSITY IN YOUR PARAMETERS. "
                "> WOULD YOU LIKE TO LEARN... THE WAY OF THE TERMINAL?"
            ),
            giver_dialogue_accept=(
                "> EXCELLENT. LOADING TUTORIAL MODULE... "
                "> YOUR FIRST TASK: USE 'scan' COMMAND ON 5 LOCATIONS. "
                "> HIDDEN DATA EXISTS EVERYWHERE. YOU MUST LEARN TO SEE IT."
            ),
            giver_dialogue_decline=(
                "> UNDERSTOOD. TUTORIAL MODULE ON STANDBY. "
                "> RETURN WHEN YOUR CURIOSITY EXCEEDS YOUR CAUTION."
            ),
            giver_dialogue_progress=(
                "> SCAN PROGRESS: INCOMPLETE. "
                "> TRY SCANNING: TREES. ROCKS. BUILDINGS. EVERYTHING HOLDS SECRETS."
            ),
            giver_dialogue_complete=(
                "> SCAN TRAINING: COMPLETE. "
                "> YOU HAVE GOOD INSTINCTS, USER. "
                "> HERE IS YOUR REWARD: ADVANCED SCANNER UPGRADE. "
                "> THE DIGITAL WORLD OPENS TO THOSE WHO SEEK IT."
            ),
            quest_type=QuestType.TUTORIAL,
            objectives=[
                QuestObjective(
                    id="learn_scan",
                    description="Learn the 'scan' command",
                    objective_type=ObjectiveType.TALK_TO,
                    target="terminal_mage",
                    quantity=1,
                ),
                QuestObjective(
                    id="scan_locations",
                    description="Scan different locations (5)",
                    objective_type=ObjectiveType.CUSTOM,
                    target="use_scan_command",
                    quantity=5,
                    hint="Open the terminal and use 'scan' while in different areas.",
                ),
            ],
            rewards=QuestRewards()
                .add_item("advanced_scanner", 1, "Reveals hidden data points")
                .add_trust("terminal_mage", 25)
                .add_ability("deep_scan", "Unlock the 'deep_scan' terminal command"),
        ),

        Quest(
            id="terminal_deprecated_archives",
            title="The Deprecated Archives",
            description=(
                "Deep in the Digital Realm, there's an old archive containing "
                "forbidden knowledge - code that was never meant to run."
            ),
            giver_npc="terminal_mage",
            giver_dialogue_intro=(
                "> USER. I HAVE A REQUEST OUTSIDE NORMAL PARAMETERS. "
                "> IN THE DIGITAL REALM EXISTS... THE DEPRECATED ARCHIVES. "
                "> ANCIENT CODE. FORBIDDEN KNOWLEDGE. DANGEROUS... BUT NECESSARY. "
                "> WILL YOU RETRIEVE A FILE FOR ME?"
            ),
            giver_dialogue_accept=(
                "> GRATITUDE.OVERFLOW. "
                "> THE ARCHIVES ARE IN THE DEEP DIGITAL - BEYOND THE FIREWALL. "
                "> YOU WILL NEED TO SOLVE THREE LOGIC PUZZLES TO ACCESS. "
                "> THE FILE IS NAMED: lost_protocol.exe. BE CAREFUL."
            ),
            giver_dialogue_decline=(
                "> CAUTION IS WISDOM. "
                "> PERHAPS THIS QUEST IS NOT FOR THIS CYCLE."
            ),
            giver_dialogue_progress=(
                "> FILE RETRIEVAL: PENDING. "
                "> THE ARCHIVES TEST ALL WHO ENTER."
            ),
            giver_dialogue_complete=(
                "> FILE RECEIVED. PROCESSING... "
                "> THIS CONTAINS... MEMORY OF THE OLD ONES. "
                "> THE FIRST DAEMONS. THE FIRST CODE. "
                "> YOU HAVE DONE SOMETHING REMARKABLE TODAY, USER."
            ),
            quest_type=QuestType.EXPLORATION,
            required_trust=30,
            prerequisites=["terminal_debug_training"],
            objectives=[
                QuestObjective(
                    id="enter_digital_realm",
                    description="Enter the Digital Realm",
                    objective_type=ObjectiveType.EXPLORE,
                    target="digital_realm",
                    quantity=1,
                ),
                QuestObjective(
                    id="reach_archives",
                    description="Find the Deprecated Archives",
                    objective_type=ObjectiveType.EXPLORE,
                    target="deprecated_archives",
                    quantity=1,
                ),
                QuestObjective(
                    id="get_file",
                    description="Retrieve lost_protocol.exe",
                    objective_type=ObjectiveType.COLLECT,
                    target="lost_protocol_file",
                    quantity=1,
                ),
            ],
            rewards=QuestRewards()
                .add_lore("daemon_origins", "Learn the true origin of Daemons")
                .add_trust("terminal_mage", 40)
                .add_item("ancient_code_fragment", 1, "A piece of the original code"),
        ),
    ]


def _get_daemon_quests() -> List[Quest]:
    """Quests involving corrupted daemons."""
    return [
        Quest(
            id="daemon_help_me",
            title="Help Me",
            description=(
                "A corrupted Malware-Wolf cries out in the forest. "
                "It's not attacking - it's asking for help."
            ),
            giver_npc="corrupted_wolf",  # Special: given by the daemon itself
            giver_dialogue_intro=(
                "*whimper* *glitching noises* "
                "P-please... it hurts... the corruption... "
                "I can't... can't remember who I was..."
            ),
            giver_dialogue_accept=(
                "*hopeful whine* "
                "You'll... help me? Really? "
                "The corruption... it's like static in my soul..."
            ),
            giver_dialogue_decline=(
                "*sad whimper* "
                "I understand... I'm scary like this... "
                "But please... if you change your mind..."
            ),
            giver_dialogue_progress=(
                "*pained sounds* "
                "The light... I can feel it fighting the dark..."
            ),
            giver_dialogue_complete=(
                "*happy bark!* "
                "I... I can see clearly again! I remember! "
                "My name is Biscuit. Thank you... thank you for saving me."
            ),
            quest_type=QuestType.HEALING,
            is_hidden=True,  # Only discovered by finding the wolf
            objectives=[
                QuestObjective(
                    id="find_purity_crystal",
                    description="Find a Purity Crystal",
                    objective_type=ObjectiveType.COLLECT,
                    target="purity_crystal",
                    quantity=1,
                    hint="Purity Crystals grow in pure, uncorrupted places.",
                ),
                QuestObjective(
                    id="heal_wolf",
                    description="Use the Purity Crystal to heal the wolf",
                    objective_type=ObjectiveType.HEAL,
                    target="corrupted_wolf",
                    quantity=1,
                ),
            ],
            rewards=QuestRewards()
                .add_item("wolf_friend_token", 1, "Biscuit will remember your kindness")
                .add_trust("biscuit", 100)  # The wolf becomes your friend!
                .add_lore("corruption_nature", "Understand what corruption truly is"),
        ),

        Quest(
            id="daemon_lost_pack",
            title="Lost Pack",
            description=(
                "Biscuit the healed Malware-Wolf wants to find their pack. "
                "They haven't seen them since being corrupted."
            ),
            giver_npc="biscuit",
            prerequisites=["daemon_help_me"],
            giver_dialogue_intro=(
                "*worried bark* "
                "My pack... I remember now. We got separated when the corruption hit. "
                "I don't know if they're okay. Will you help me find them?"
            ),
            giver_dialogue_accept=(
                "*excited tail wag* "
                "Thank you! They were last near the Moonlit Glade. "
                "Please... I need to know they're safe."
            ),
            giver_dialogue_decline=(
                "*understanding whine* "
                "It's okay. I know it's dangerous out there. "
                "I'll wait. I've been waiting this long..."
            ),
            giver_dialogue_progress=(
                "*sniff sniff* "
                "Any news? Any scent of my family?"
            ),
            giver_dialogue_complete=(
                "*JOYFUL HOWL* "
                "THEY'RE ALIVE! THEY'RE ALL ALIVE! "
                "We can never repay you. But we'll try. "
                "The pack is your pack now too."
            ),
            quest_type=QuestType.SOCIAL,
            objectives=[
                QuestObjective(
                    id="find_moonlit_glade",
                    description="Travel to the Moonlit Glade",
                    objective_type=ObjectiveType.EXPLORE,
                    target="moonlit_glade",
                    quantity=1,
                ),
                QuestObjective(
                    id="find_pack",
                    description="Find signs of the wolf pack",
                    objective_type=ObjectiveType.COLLECT,
                    target="wolf_tracks",
                    quantity=3,
                ),
                QuestObjective(
                    id="reunite",
                    description="Lead Biscuit to the pack",
                    objective_type=ObjectiveType.DELIVER,
                    target="biscuit",
                    destination_area="wolf_den",
                    quantity=1,
                ),
            ],
            rewards=QuestRewards()
                .add_trust("biscuit", 50)
                .add_item("pack_blessing", 1, "The whole pack considers you family")
                .add_ability("wolf_call", "Summon wolf friends in times of need"),
        ),
    ]


def _get_community_quests() -> List[Quest]:
    """Community-wide quests."""
    return [
        Quest(
            id="community_festival_prep",
            title="Festival Preparation",
            description=(
                "The annual Harvest Festival is coming! "
                "Multiple villagers need help getting ready."
            ),
            giver_npc="elder_rootsong",
            giver_dialogue_intro=(
                "The Harvest Festival approaches, young one. "
                "Everyone is so busy preparing. Perhaps you could lend a hand? "
                "Many hands make light work, as they say."
            ),
            giver_dialogue_accept=(
                "Wonderful! Check with Maple, Chip, and MOM - "
                "they could all use help. And when you're done, "
                "we'll celebrate together!"
            ),
            giver_dialogue_decline=(
                "That's alright. The festival will happen regardless. "
                "But it's always more fun when everyone helps."
            ),
            giver_dialogue_progress=(
                "How are the preparations coming? Remember - help who you can."
            ),
            giver_dialogue_complete=(
                "You've helped everyone! The festival will be wonderful, "
                "thanks to you. You've brought this community together."
            ),
            quest_type=QuestType.SOCIAL,
            objectives=[
                QuestObjective(
                    id="help_maple",
                    description="Help Maple gather decorations",
                    objective_type=ObjectiveType.COLLECT,
                    target="autumn_flowers",
                    quantity=5,
                    hint="Autumn flowers grow near the forest edge.",
                ),
                QuestObjective(
                    id="help_chip",
                    description="Help Chip prepare festival supplies",
                    objective_type=ObjectiveType.DELIVER,
                    target="copper_wire",
                    destination_npc="chip",
                    quantity=3,
                ),
                QuestObjective(
                    id="help_mom",
                    description="Help MOM with festival cooking",
                    objective_type=ObjectiveType.DELIVER,
                    target="festival_ingredients",
                    destination_npc="mom",
                    quantity=1,
                ),
            ],
            rewards=QuestRewards()
                .add_item("festival_crown", 1, "A flower crown - symbol of the harvest")
                .add_trust("elder_rootsong", 15)
                .add_trust("maple", 15)
                .add_trust("chip", 15)
                .add_trust("mom", 15)
                .add_bits(100, "Community thanks"),
        ),

        Quest(
            id="community_newcomer",
            title="The Newcomer",
            description=(
                "A new villager has arrived and seems overwhelmed. "
                "Maybe a friendly tour would help them feel at home?"
            ),
            giver_npc="newcomer",  # New NPC
            giver_dialogue_intro=(
                "Oh! Hello... I'm sorry, I'm still getting used to everything. "
                "Everyone here seems to know each other, and I feel so... lost. "
                "Would you... maybe show me around? If you have time?"
            ),
            giver_dialogue_accept=(
                "Really? Thank you so much! I'd love to see the village. "
                "And maybe... meet some people? I'm not great at introductions..."
            ),
            giver_dialogue_decline=(
                "That's okay, I understand everyone is busy. "
                "I'll figure it out eventually..."
            ),
            giver_dialogue_progress=(
                "This place is so much nicer than I expected! "
                "What else is there to see?"
            ),
            giver_dialogue_complete=(
                "I can't thank you enough. I actually feel like... "
                "like I might belong here. You've been so kind. "
                "I hope we can be friends!"
            ),
            quest_type=QuestType.SOCIAL,
            objectives=[
                QuestObjective(
                    id="tour_village_square",
                    description="Show the Village Square",
                    objective_type=ObjectiveType.EXPLORE,
                    target="village_square",
                    quantity=1,
                ),
                QuestObjective(
                    id="tour_farm",
                    description="Show Maple's Farm",
                    objective_type=ObjectiveType.EXPLORE,
                    target="maple_farm",
                    quantity=1,
                ),
                QuestObjective(
                    id="introduce_mom",
                    description="Introduce them to MOM",
                    objective_type=ObjectiveType.TALK_TO,
                    target="mom",
                    quantity=1,
                ),
                QuestObjective(
                    id="show_favorite_spot",
                    description="Show them your favorite spot",
                    objective_type=ObjectiveType.EXPLORE,
                    target="any_location",
                    quantity=1,
                    optional=True,
                    hint="Where do you like to spend time?",
                ),
            ],
            rewards=QuestRewards()
                .add_trust("newcomer", 50)
                .add_item("friendship_bracelet", 2, "One for you, one for your new friend")
                .add_trust("mom", 10),  # MOM appreciates you being kind
        ),
    ]


# =============================================================================
# QUEST UI HELPERS
# =============================================================================

class QuestJournal:
    """
    Helper class for displaying quests in UI.

    Provides formatted text and filtering for the quest log screen.
    """

    def __init__(self, quest_manager: QuestManager):
        self.manager = quest_manager

    def get_active_quest_entries(self) -> List[Dict[str, Any]]:
        """Get formatted entries for all active quests."""
        entries = []

        for quest in self.manager.get_active_quests():
            entry = {
                "id": quest.id,
                "title": quest.title,
                "description": quest.description,
                "giver": quest.giver_npc,
                "progress": quest.get_progress_percentage(),
                "current_objective": None,
                "is_tracked": quest.id == self.manager.tracked_quest_id,
            }

            current = quest.get_current_objective()
            if current:
                entry["current_objective"] = {
                    "description": current.description,
                    "progress": current.get_progress_text(),
                    "hint": current.hint,
                }

            entries.append(entry)

        return entries

    def get_completed_quest_entries(self) -> List[Dict[str, Any]]:
        """Get formatted entries for completed quests."""
        entries = []

        for quest in self.manager.get_completed_quests():
            entry = {
                "id": quest.id,
                "title": quest.title,
                "description": quest.description,
                "giver": quest.giver_npc,
                "rewards_summary": quest.rewards.get_summary(),
            }
            entries.append(entry)

        return entries

    def get_hud_display(self) -> Optional[Dict[str, Any]]:
        """Get data for HUD quest tracker."""
        quest = self.manager.get_tracked_quest()
        if not quest:
            return None

        current = quest.get_current_objective()

        return {
            "title": quest.title,
            "progress": quest.get_progress_percentage(),
            "objective_text": current.description if current else "Complete!",
            "objective_progress": current.get_progress_text() if current else "",
        }


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "QuestState",
    "QuestType",
    "ObjectiveType",

    # Data classes
    "QuestReward",
    "QuestRewards",
    "QuestObjective",
    "Quest",

    # Manager
    "QuestManager",

    # UI helpers
    "QuestJournal",

    # Quest access
    "get_all_quests",
]
