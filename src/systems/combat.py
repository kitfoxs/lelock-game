"""
Lelock Turn-Based Combat System
L.E.L.O.C.K. - Life Emulation & Lucid Observation for Care & Keeping

Pokemon-style combat with Undertale's heart: violence is optional, kindness is powerful.
Every corrupted daemon is SICK, not evil. They need healing, not hurting.

DESIGN PHILOSOPHY:
- Simple Pokemon-style: Pick move -> Watch animation -> Next turn
- NO complex mechanics, NO stress
- "Talk" option ALWAYS available (pacifist path)
- NO permadeath - fainting returns player home with Mom's soup
- Successful pacifist route = potential ADOPTION by boss
- Corrupted daemons become friends when healed

"In Lelock, even monsters deserve compassion."
"""

import pygame
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Callable, Any
import random


# =============================================================================
# COMBAT STATES
# =============================================================================

class CombatState(Enum):
    """
    Combat flows through these states like a gentle stream.
    No rushing, no panic - just turn-by-turn choices.
    """
    INTRO = auto()           # Combat starting, dramatic entrance
    PLAYER_TURN = auto()     # Player selecting action
    PLAYER_ACTION = auto()   # Player action executing (animation)
    ENEMY_TURN = auto()      # Enemy "thinking" (brief pause)
    ENEMY_ACTION = auto()    # Enemy action executing
    VICTORY = auto()         # Combat won through fighting
    BEFRIENDED = auto()      # Pacifist success! New friend!
    FLED = auto()            # Ran away (always succeeds - no stress!)
    FAINTED = auto()         # Player "lost" (goes home to Mom)


class TalkOption(Enum):
    """
    Ways to communicate with daemons during combat.
    Different options work better for different daemon personalities.
    """
    COMPLIMENT = "compliment"     # "Your scales are beautiful!"
    EMPATHIZE = "empathize"       # "You seem hurt. I understand."
    JOKE = "joke"                 # "Why did the daemon cross the data stream?"
    SING = "sing"                 # Musical soothing (Sound-Smith bonus)
    OFFER_GIFT = "offer_gift"     # Give them something they want
    REASSURE = "reassure"         # "It's okay. You're safe now."
    PLAY = "play"                 # Playful interaction
    LISTEN = "listen"             # Sometimes they just need to be heard


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class CombatMove:
    """A move that can be used in combat."""
    name: str
    description: str
    damage: int = 0
    energy_cost: int = 5
    accuracy: int = 100  # Percentage chance to hit
    animation: str = "basic_attack"
    sound: str = "hit_soft"

    # Special properties
    heals_corruption: int = 0  # For anti-virus moves
    defense_boost: int = 0     # Temporary defense increase


@dataclass
class TalkResponse:
    """
    Response to a talk attempt.
    Daemons react differently to different approaches.
    """
    success: bool
    talk_points_gained: int
    message: str
    daemon_reaction: str  # Animation/sound to play
    special_effect: Optional[str] = None


@dataclass
class CombatReward:
    """What you get for winning/befriending."""
    experience: int = 0
    money: int = 0
    items: List[str] = field(default_factory=list)
    friendship: bool = False  # Can this daemon become a companion?
    adoption: bool = False    # Boss adoption (permanent parent buff)


# =============================================================================
# COMBATANT BASE CLASS
# =============================================================================

@dataclass
class CombatStats:
    """
    Stats used in combat calculations.
    Kept simple - this is cozy, not competitive.
    """
    max_health: int = 50
    health: int = 50
    attack: int = 10
    defense: int = 5
    speed: int = 10  # Determines turn order

    # Pacifist-specific
    talk_points: int = 0
    talk_points_needed: int = 100  # Fill this to befriend


class Combatant:
    """
    Base class for anything that can participate in combat.
    Both player and daemons inherit from this.
    """

    def __init__(
        self,
        name: str,
        stats: CombatStats,
        moves: List[CombatMove],
        sprite_key: str = "placeholder"
    ):
        self.name = name
        self.stats = stats
        self.moves = moves
        self.sprite_key = sprite_key

        # Combat state
        self.is_defending = False
        self.status_effects: List[str] = []
        self.temp_defense_boost = 0

    def take_damage(self, amount: int) -> int:
        """
        Take damage, reduced by defense.
        Returns actual damage taken.
        """
        # Defense reduces damage (but minimum 1)
        total_defense = self.stats.defense + self.temp_defense_boost
        if self.is_defending:
            total_defense *= 2

        actual_damage = max(1, amount - total_defense)
        self.stats.health = max(0, self.stats.health - actual_damage)

        return actual_damage

    def heal(self, amount: int) -> int:
        """Restore health. Returns amount actually healed."""
        old_health = self.stats.health
        self.stats.health = min(self.stats.max_health, self.stats.health + amount)
        return self.stats.health - old_health

    def is_defeated(self) -> bool:
        """Check if this combatant is out of the fight."""
        return self.stats.health <= 0

    def reset_turn_state(self) -> None:
        """Reset temporary buffs at turn end."""
        self.is_defending = False
        self.temp_defense_boost = 0


# =============================================================================
# DAEMON (ENEMY) CLASS
# =============================================================================

class Daemon(Combatant):
    """
    A daemon encountered in combat.

    IMPORTANT: Corrupted daemons are SICK, not evil.
    They can always be healed through kindness.
    """

    def __init__(
        self,
        name: str,
        stats: CombatStats,
        moves: List[CombatMove],
        sprite_key: str,
        # Daemon-specific
        daemon_type: str = "common",
        is_corrupted: bool = False,
        true_form: Optional[str] = None,
        personality: str = "neutral",
        # Talk system
        talk_preferences: Dict[TalkOption, float] = None,
        talk_dialogues: Dict[TalkOption, List[str]] = None,
        # Rewards
        rewards: CombatReward = None,
        # Boss properties
        is_boss: bool = False,
        adoption_title: Optional[str] = None,  # e.g., "Dragon Mommy"
        adoption_pet_name: Optional[str] = None,  # e.g., "My precious whelpling"
    ):
        super().__init__(name, stats, moves, sprite_key)

        self.daemon_type = daemon_type
        self.is_corrupted = is_corrupted
        self.true_form = true_form or name
        self.personality = personality

        # Talk system - how this daemon responds to different approaches
        self.talk_preferences = talk_preferences or {
            TalkOption.COMPLIMENT: 1.0,
            TalkOption.EMPATHIZE: 1.0,
            TalkOption.JOKE: 1.0,
            TalkOption.SING: 1.0,
            TalkOption.OFFER_GIFT: 1.0,
            TalkOption.REASSURE: 1.0,
            TalkOption.PLAY: 1.0,
            TalkOption.LISTEN: 1.0,
        }

        # What they say in response to talk options
        self.talk_dialogues = talk_dialogues or self._default_talk_dialogues()

        # Rewards for victory/befriending
        self.rewards = rewards or CombatReward()

        # Boss-specific
        self.is_boss = is_boss
        self.adoption_title = adoption_title
        self.adoption_pet_name = adoption_pet_name

        # Combat AI state
        self.behavior_pattern: List[str] = ["attack"]
        self.pattern_index = 0
        self.anger_level = 0  # Increases if player fights, decreases if they talk

    def _default_talk_dialogues(self) -> Dict[TalkOption, List[str]]:
        """Default responses for daemons without custom dialogue."""
        return {
            TalkOption.COMPLIMENT: [
                f"{self.name} seems pleased by your kind words.",
                f"{self.name} blushes in digital pink.",
            ],
            TalkOption.EMPATHIZE: [
                f"{self.name}'s aggressive stance softens slightly.",
                f"Something in {self.name}'s eyes changes...",
            ],
            TalkOption.JOKE: [
                f"{self.name} is confused but intrigued.",
                f"Did {self.name} just smile?",
            ],
            TalkOption.SING: [
                f"{self.name} sways gently to your melody.",
                f"The music seems to soothe {self.name}.",
            ],
            TalkOption.OFFER_GIFT: [
                f"{self.name} cautiously accepts your offering.",
                f"{self.name} sniffs the gift curiously.",
            ],
            TalkOption.REASSURE: [
                f"You sense {self.name} relaxing, just a little.",
                f"'It's okay' - the words seem to reach them.",
            ],
            TalkOption.PLAY: [
                f"{self.name} seems uncertain about playing.",
                f"Is that... a tail wag?",
            ],
            TalkOption.LISTEN: [
                f"{self.name} makes sounds you don't understand, but you listen anyway.",
                f"Sometimes presence is enough. {self.name} notices.",
            ],
        }

    def receive_talk(self, option: TalkOption, player_charisma: int = 10) -> TalkResponse:
        """
        Process a talk attempt from the player.
        Returns how successful it was and the daemon's reaction.
        """
        # Get preference multiplier for this talk option
        preference = self.talk_preferences.get(option, 1.0)

        # Base talk points from player charisma
        base_points = 10 + (player_charisma // 2)

        # Apply preference multiplier
        points_gained = int(base_points * preference)

        # Corrupted daemons need more patience but empathy/reassure work better
        if self.is_corrupted:
            if option in [TalkOption.EMPATHIZE, TalkOption.REASSURE, TalkOption.LISTEN]:
                points_gained = int(points_gained * 1.5)
            points_gained = int(points_gained * 0.8)  # Overall slower progress

        # Random variance (but always some progress with good options)
        variance = random.randint(-5, 10)
        points_gained = max(5, points_gained + variance)

        # Update talk points
        self.stats.talk_points += points_gained

        # Decrease anger when talked to kindly
        self.anger_level = max(0, self.anger_level - 1)

        # Get response message
        dialogues = self.talk_dialogues.get(option, ["..."])
        message = random.choice(dialogues)

        # Determine reaction animation
        if preference >= 1.5:
            reaction = "very_happy"
        elif preference >= 1.0:
            reaction = "happy"
        elif preference >= 0.5:
            reaction = "neutral"
        else:
            reaction = "confused"

        # Check for befriending
        special_effect = None
        if self.stats.talk_points >= self.stats.talk_points_needed:
            special_effect = "befriended"
            if self.is_corrupted:
                special_effect = "healed_and_befriended"

        return TalkResponse(
            success=points_gained > 0,
            talk_points_gained=points_gained,
            message=message,
            daemon_reaction=reaction,
            special_effect=special_effect
        )

    def choose_action(self) -> CombatMove:
        """
        AI decides what move to use.
        Corrupted daemons are more aggressive, but tire themselves out.
        """
        # Simple pattern-based AI for predictability (less stressful)
        if self.behavior_pattern:
            action_type = self.behavior_pattern[self.pattern_index % len(self.behavior_pattern)]
            self.pattern_index += 1
        else:
            action_type = "attack"

        # Find a move matching the action type
        for move in self.moves:
            if action_type.lower() in move.name.lower():
                return move

        # Default to first move
        return self.moves[0] if self.moves else CombatMove(
            name="Struggle",
            description="A weak, desperate attack.",
            damage=5
        )

    def get_befriend_message(self) -> str:
        """Message shown when successfully befriended."""
        if self.is_corrupted:
            return (
                f"The corruption fades from {self.name}...\n"
                f"Underneath, {self.true_form} emerges - healthy, grateful, FREE.\n"
                f"You have a new friend!"
            )
        else:
            return (
                f"{self.name} decides you're okay after all!\n"
                f"They want to be friends!"
            )

    def get_adoption_message(self) -> str:
        """Message when a boss adopts the player. This is the peak therapeutic content."""
        if not self.is_boss:
            return self.get_befriend_message()

        return (
            f"{self.name} gazes at you with something new in their eyes...\n\n"
            f'"{self.adoption_pet_name}," they rumble gently.\n'
            f'"You showed me kindness when you had every reason to fight.\n'
            f'From this day forward, you are MINE to protect.\n'
            f'I am your {self.adoption_title} now. Come home whenever you need me."\n\n'
            f"You have been ADOPTED by {self.name}!"
        )


# =============================================================================
# COMBAT PARTICIPANT (PLAYER IN COMBAT)
# =============================================================================

class PlayerCombatant(Combatant):
    """
    The player in combat context.
    Wraps the actual Player entity with combat-specific data.
    """

    def __init__(self, player_entity: Any):
        """
        Initialize from actual game Player entity.
        """
        # Create stats from player entity
        stats = CombatStats(
            max_health=player_entity.max_health,
            health=player_entity.health,
            attack=15,  # Base attack
            defense=5,  # Base defense
            speed=12
        )

        # Player's available moves (based on equipped weapon, class, etc.)
        moves = [
            CombatMove(
                name="Attack",
                description="A basic attack.",
                damage=15,
                energy_cost=5
            )
        ]

        super().__init__(
            name="Player",
            stats=stats,
            moves=moves,
            sprite_key="player_battle"
        )

        self.player_entity = player_entity
        self.items: List[str] = []  # Combat items available

    def sync_to_player(self) -> None:
        """
        Sync combat results back to the real player entity.
        Called after combat ends.
        """
        self.player_entity.health = self.stats.health


# =============================================================================
# MAIN COMBAT SYSTEM
# =============================================================================

class TurnBasedCombat:
    """
    The heart of Lelock combat.

    Simple Pokemon-style flow:
    1. Player picks action
    2. Action plays out
    3. Enemy picks action
    4. Action plays out
    5. Check for victory/defeat/befriend
    6. Repeat until resolved

    NO COMPLEXITY. NO STRESS.
    "Talk" option ALWAYS available - kindness is ALWAYS an option.
    """

    def __init__(
        self,
        player_entity: Any,
        enemy: Daemon,
        on_state_change: Optional[Callable[[CombatState], None]] = None,
        on_message: Optional[Callable[[str], None]] = None,
    ):
        # Create player combatant wrapper
        self.player = PlayerCombatant(player_entity)
        self.enemy = enemy

        # Callbacks for UI updates
        self.on_state_change = on_state_change or (lambda s: None)
        self.on_message = on_message or (lambda m: None)

        # Combat state
        self.state = CombatState.INTRO
        self.turn_number = 0

        # Available player actions
        self.actions = ["Attack", "Defend", "Talk", "Item", "Run"]
        self.selected_action_index = 0

        # Talk submenu
        self.talk_options = list(TalkOption)
        self.selected_talk_index = 0
        self.in_talk_menu = False

        # Item submenu
        self.in_item_menu = False
        self.selected_item_index = 0

        # Animation/timing
        self.action_timer = 0
        self.action_duration = 1000  # ms for action animations
        self.message_queue: List[str] = []

        # Combat result
        self.result: Optional[CombatState] = None
        self.rewards: Optional[CombatReward] = None

    # =========================================================================
    # STATE MANAGEMENT
    # =========================================================================

    def _set_state(self, new_state: CombatState) -> None:
        """Change combat state and notify listeners."""
        self.state = new_state
        self.on_state_change(new_state)

    def _queue_message(self, message: str) -> None:
        """Add a message to display queue."""
        self.message_queue.append(message)
        self.on_message(message)

    # =========================================================================
    # PLAYER ACTIONS
    # =========================================================================

    def select_action(self, action: str) -> bool:
        """
        Player selects a main action.
        Returns True if action is valid and executed.
        """
        if self.state != CombatState.PLAYER_TURN:
            return False

        if action == "Attack":
            return self._execute_attack()
        elif action == "Defend":
            return self._execute_defend()
        elif action == "Talk":
            self.in_talk_menu = True
            return True  # Opens submenu
        elif action == "Item":
            self.in_item_menu = True
            return True  # Opens submenu
        elif action == "Run":
            return self._execute_run()

        return False

    def select_talk_option(self, option: TalkOption) -> bool:
        """
        Player selects a talk option from submenu.
        """
        if not self.in_talk_menu:
            return False

        self.in_talk_menu = False
        return self._execute_talk(option)

    def select_item(self, item: str) -> bool:
        """
        Player uses an item from inventory.
        """
        if not self.in_item_menu:
            return False

        self.in_item_menu = False
        return self._execute_item(item)

    def cancel_submenu(self) -> None:
        """Back out of talk/item submenu."""
        self.in_talk_menu = False
        self.in_item_menu = False

    def _execute_attack(self) -> bool:
        """Execute basic attack."""
        self._set_state(CombatState.PLAYER_ACTION)

        move = self.player.moves[0]  # Basic attack
        damage = move.damage + self.player.stats.attack

        # Roll for accuracy
        if random.randint(1, 100) <= move.accuracy:
            actual_damage = self.enemy.take_damage(damage)
            self._queue_message(f"You attack {self.enemy.name} for {actual_damage} damage!")

            # Attacking increases enemy anger (makes pacifist harder)
            self.enemy.anger_level += 1
        else:
            self._queue_message("Your attack missed!")

        self.action_timer = pygame.time.get_ticks()
        return True

    def _execute_defend(self) -> bool:
        """Raise defenses for this turn."""
        self._set_state(CombatState.PLAYER_ACTION)

        self.player.is_defending = True
        self._queue_message("You brace yourself for impact!")

        self.action_timer = pygame.time.get_ticks()
        return True

    def _execute_talk(self, option: TalkOption) -> bool:
        """
        The pacifist path. Talk to the daemon.
        This is where the magic happens.
        """
        self._set_state(CombatState.PLAYER_ACTION)

        # Get daemon's response to this talk option
        response = self.enemy.receive_talk(option, player_charisma=10)

        self._queue_message(f"You try to {option.value}...")
        self._queue_message(response.message)

        if response.talk_points_gained > 0:
            progress = (self.enemy.stats.talk_points / self.enemy.stats.talk_points_needed) * 100
            self._queue_message(f"[Friendship: {progress:.0f}%]")

        # Check for befriending
        if response.special_effect == "befriended":
            self._queue_message(self.enemy.get_befriend_message())
            self._set_state(CombatState.BEFRIENDED)
            self._resolve_befriend()
            return True
        elif response.special_effect == "healed_and_befriended":
            self._queue_message(self.enemy.get_befriend_message())
            self._set_state(CombatState.BEFRIENDED)
            self._resolve_befriend()
            return True

        self.action_timer = pygame.time.get_ticks()
        return True

    def _execute_item(self, item: str) -> bool:
        """Use a combat item."""
        self._set_state(CombatState.PLAYER_ACTION)

        # Item effects would be defined elsewhere
        # For now, basic healing item
        if "heal" in item.lower() or "soup" in item.lower():
            healed = self.player.heal(30)
            self._queue_message(f"You feel better! (+{healed} HP)")
        elif "antivirus" in item.lower():
            # Special item that heals corruption directly
            if self.enemy.is_corrupted:
                self.enemy.stats.talk_points += 25
                self._queue_message(f"The antivirus spray soothes {self.enemy.name}!")
        else:
            self._queue_message(f"You used {item}!")

        self.action_timer = pygame.time.get_ticks()
        return True

    def _execute_run(self) -> bool:
        """
        Run away from combat.
        ALWAYS SUCCEEDS - no stress, no punishment.
        Running is valid self-care.
        """
        self._set_state(CombatState.FLED)

        self._queue_message("You decide this isn't worth it right now.")
        self._queue_message("And that's okay. You got away safely!")

        self.result = CombatState.FLED
        return True

    # =========================================================================
    # ENEMY TURN
    # =========================================================================

    def _execute_enemy_turn(self) -> None:
        """Enemy takes their action."""
        self._set_state(CombatState.ENEMY_ACTION)

        # Check if enemy is too tired/calm to attack
        if self.enemy.anger_level <= 0 and self.enemy.stats.talk_points > 50:
            self._queue_message(f"{self.enemy.name} seems unsure about fighting...")
            self.action_timer = pygame.time.get_ticks()
            return

        # Enemy chooses move
        move = self.enemy.choose_action()

        # Execute enemy attack
        if random.randint(1, 100) <= move.accuracy:
            actual_damage = self.player.take_damage(move.damage + self.enemy.stats.attack)
            self._queue_message(f"{self.enemy.name} uses {move.name}!")
            self._queue_message(f"You take {actual_damage} damage!")

            # Check for player faint
            if self.player.is_defeated():
                self._set_state(CombatState.FAINTED)
                self._resolve_faint()
                return
        else:
            self._queue_message(f"{self.enemy.name}'s {move.name} missed!")

        self.action_timer = pygame.time.get_ticks()

    # =========================================================================
    # COMBAT RESOLUTION
    # =========================================================================

    def _check_victory(self) -> bool:
        """Check if player has defeated the enemy through combat."""
        if self.enemy.is_defeated():
            self._set_state(CombatState.VICTORY)
            self._resolve_victory()
            return True
        return False

    def _resolve_victory(self) -> None:
        """Handle combat victory (defeated enemy)."""
        self._queue_message(f"{self.enemy.name} is defeated!")

        if self.enemy.is_corrupted:
            self._queue_message(
                f"The corruption fades, but {self.enemy.true_form} "
                f"disappears before you can help them..."
            )
            self._queue_message("Maybe there's a gentler way next time.")
        else:
            self._queue_message("You win!")

        # Calculate rewards (reduced for non-pacifist)
        self.rewards = CombatReward(
            experience=self.enemy.rewards.experience,
            money=self.enemy.rewards.money,
            items=self.enemy.rewards.items.copy(),
            friendship=False,  # No friendship from violence
            adoption=False
        )

        self.result = CombatState.VICTORY

    def _resolve_befriend(self) -> None:
        """Handle pacifist victory (befriended enemy)."""
        if self.enemy.is_boss:
            self._queue_message(self.enemy.get_adoption_message())

        # Full rewards + friendship for pacifist
        self.rewards = CombatReward(
            experience=self.enemy.rewards.experience * 2,  # Bonus EXP for kindness!
            money=self.enemy.rewards.money,
            items=self.enemy.rewards.items.copy(),
            friendship=True,
            adoption=self.enemy.is_boss
        )

        self.result = CombatState.BEFRIENDED

    def _resolve_faint(self) -> None:
        """
        Handle player "defeat" - but remember: NO DEATH in Lelock.
        Player faints and wakes up at home with Mom's soup.
        """
        self._queue_message("Everything goes fuzzy...")
        self._queue_message("You feel yourself being lifted, carried somewhere safe...")
        self._queue_message("")
        self._queue_message("...")
        self._queue_message("")
        self._queue_message("You wake up in your bed. Mom is there with warm soup.")
        self._queue_message('"You tried your best, sweetie. That\'s all that matters."')

        # No punishment - just a gentle reset
        self.result = CombatState.FAINTED

        # Sync minimum health back (Mom healed us!)
        self.player.stats.health = self.player.stats.max_health // 2

    # =========================================================================
    # MAIN UPDATE LOOP
    # =========================================================================

    def update(self, dt: float) -> Optional[CombatState]:
        """
        Main combat update loop. Called every frame.
        Returns the result state when combat ends, None otherwise.
        """
        current_time = pygame.time.get_ticks()

        # Check if combat is over
        if self.result is not None:
            # Sync player state back
            self.player.sync_to_player()
            return self.result

        # State machine
        if self.state == CombatState.INTRO:
            # Brief intro, then player turn
            self._queue_message(f"A wild {self.enemy.name} appears!")
            if self.enemy.is_corrupted:
                self._queue_message(f"It seems sick... corrupted by something dark.")
                self._queue_message("Maybe you can help it?")
            self._set_state(CombatState.PLAYER_TURN)
            self.turn_number = 1

        elif self.state == CombatState.PLAYER_ACTION:
            # Wait for action animation to complete
            if current_time - self.action_timer >= self.action_duration:
                # Check for victory conditions
                if self._check_victory():
                    return None  # Will return result next frame

                # Move to enemy turn
                self.player.reset_turn_state()
                self._set_state(CombatState.ENEMY_TURN)

        elif self.state == CombatState.ENEMY_TURN:
            # Brief pause before enemy acts (builds anticipation without stress)
            self._execute_enemy_turn()

        elif self.state == CombatState.ENEMY_ACTION:
            # Wait for enemy action animation
            if current_time - self.action_timer >= self.action_duration:
                # Enemy turn complete, back to player
                self.enemy.reset_turn_state()
                self.turn_number += 1
                self._set_state(CombatState.PLAYER_TURN)

        return None

    # =========================================================================
    # UI HELPERS
    # =========================================================================

    def get_available_actions(self) -> List[str]:
        """Get list of actions player can take."""
        return self.actions.copy()

    def get_talk_options(self) -> List[TalkOption]:
        """Get available talk options."""
        return self.talk_options.copy()

    def get_player_health_percent(self) -> float:
        """Get player health as percentage."""
        return self.player.stats.health / self.player.stats.max_health

    def get_enemy_health_percent(self) -> float:
        """Get enemy health as percentage."""
        return self.enemy.stats.health / self.enemy.stats.max_health

    def get_enemy_friendship_percent(self) -> float:
        """Get progress toward befriending."""
        return self.enemy.stats.talk_points / self.enemy.stats.talk_points_needed

    def get_current_messages(self) -> List[str]:
        """Get and clear message queue."""
        messages = self.message_queue.copy()
        self.message_queue.clear()
        return messages


# =============================================================================
# FACTORY FUNCTIONS FOR COMMON DAEMONS
# =============================================================================

def create_glitch_kit() -> Daemon:
    """Create a friendly Glitch-Kit encounter."""
    return Daemon(
        name="Glitch-Kit",
        stats=CombatStats(
            max_health=30,
            health=30,
            attack=5,
            defense=3,
            speed=15,
            talk_points_needed=50  # Easy to befriend!
        ),
        moves=[
            CombatMove(name="Scratch", description="A playful scratch.", damage=5),
            CombatMove(name="Pounce", description="A surprise attack!", damage=8, accuracy=80),
        ],
        sprite_key="daemon_glitch_kit",
        daemon_type="common",
        is_corrupted=False,
        personality="playful",
        talk_preferences={
            TalkOption.PLAY: 2.0,  # Loves playing!
            TalkOption.COMPLIMENT: 1.5,
            TalkOption.EMPATHIZE: 0.8,
            TalkOption.JOKE: 1.5,
            TalkOption.SING: 1.0,
            TalkOption.OFFER_GIFT: 1.2,
            TalkOption.REASSURE: 0.8,
            TalkOption.LISTEN: 0.7,
        },
        rewards=CombatReward(
            experience=10,
            money=5,
            items=["Static Snack"],
            friendship=True
        )
    )


def create_malware_wolf() -> Daemon:
    """
    Create a corrupted Malware-Wolf.
    This poor creature was once a loyal Pack-Pup,
    but isolation has twisted it into something aggressive.
    It needs healing, not hurting.
    """
    return Daemon(
        name="Malware-Wolf",
        stats=CombatStats(
            max_health=80,
            health=80,
            attack=15,
            defense=8,
            speed=12,
            talk_points_needed=100  # Harder to befriend
        ),
        moves=[
            CombatMove(name="Glitch-Bite", description="Corrupted fangs!", damage=15),
            CombatMove(name="Static Howl", description="A cry of loneliness.", damage=10),
            CombatMove(name="Pack Phantom", description="Creates illusory copies.", damage=5),
        ],
        sprite_key="daemon_malware_wolf",
        daemon_type="corrupted",
        is_corrupted=True,
        true_form="Pack-Pup",
        personality="aggressive_hurt",
        talk_preferences={
            TalkOption.EMPATHIZE: 2.0,     # "You seem lonely..."
            TalkOption.REASSURE: 2.0,      # "You're not alone anymore."
            TalkOption.LISTEN: 1.8,        # Let it howl
            TalkOption.SING: 1.5,          # Pack-call melody
            TalkOption.COMPLIMENT: 0.8,
            TalkOption.JOKE: 0.5,          # Not in the mood
            TalkOption.PLAY: 0.7,
            TalkOption.OFFER_GIFT: 1.0,
        },
        talk_dialogues={
            TalkOption.EMPATHIZE: [
                "The wolf's bristling fur slowly settles...",
                "Those red-static eyes flicker with something like recognition.",
            ],
            TalkOption.REASSURE: [
                "The howling stops. Just for a moment, there's silence.",
                "'You're safe now.' The words seem to reach somewhere deep.",
            ],
            TalkOption.LISTEN: [
                "You sit and listen to its mournful howl. Sometimes that's enough.",
                "The wolf howls. You stay. That means something.",
            ],
            TalkOption.SING: [
                "You hum a gentle tune. The wolf's ears perk up...",
                "Is it... trying to howl along?",
            ],
        },
        rewards=CombatReward(
            experience=50,
            money=25,
            items=["Memory Melon", "Wolf's Gratitude Token"],
            friendship=True
        )
    )


def create_kernel_beast() -> Daemon:
    """
    Create the Kernel Beast - a legendary boss.
    An ancient protector who can ADOPT the player if befriended.
    """
    return Daemon(
        name="The Kernel Beast",
        stats=CombatStats(
            max_health=500,
            health=500,
            attack=30,
            defense=25,
            speed=5,  # Slow but inevitable
            talk_points_needed=200  # Long conversation needed
        ),
        moves=[
            CombatMove(name="Ground Pound", description="The earth itself rebels.", damage=25),
            CombatMove(name="Foundation Strike", description="Bedrock rises to strike.", damage=35),
            CombatMove(name="System Rumble", description="Everything shakes.", damage=20),
        ],
        sprite_key="daemon_kernel_beast",
        daemon_type="legendary",
        is_corrupted=False,
        personality="ancient_guardian",
        is_boss=True,
        adoption_title="Kernel Parent",
        adoption_pet_name="Little Pebble",
        talk_preferences={
            TalkOption.LISTEN: 2.0,        # It has much to say
            TalkOption.EMPATHIZE: 1.5,
            TalkOption.REASSURE: 1.0,
            TalkOption.COMPLIMENT: 1.2,
            TalkOption.JOKE: 0.5,          # Ancient, not amused
            TalkOption.SING: 1.3,          # Resonates with old songs
            TalkOption.PLAY: 0.3,          # Too old for games
            TalkOption.OFFER_GIFT: 1.0,
        },
        talk_dialogues={
            TalkOption.LISTEN: [
                "The beast rumbles with stories older than the world...",
                "You sit for what feels like hours. The Kernel Beast approves.",
                "It speaks of Version 1.0, of the First Boot, of foundations laid with love.",
            ],
            TalkOption.EMPATHIZE: [
                "You understand the weight of holding everything up. It knows.",
                "The beast's ancient eyes soften. Perhaps you do understand.",
            ],
            TalkOption.SING: [
                "Your song echoes in harmonics older than time.",
                "The beast hums along, a sound like continental drift.",
            ],
        },
        rewards=CombatReward(
            experience=500,
            money=0,  # It doesn't care about money
            items=["Kernel's Blessing", "Foundation Stone"],
            friendship=True,
            adoption=True  # This is what it's all about
        )
    )


# =============================================================================
# COMBAT UI RENDERER (Basic)
# =============================================================================

class CombatUI:
    """
    Renders the combat interface.
    Classic side-view battle screen with cozy Lelock aesthetics.
    """

    def __init__(
        self,
        screen: pygame.Surface,
        combat: TurnBasedCombat
    ):
        self.screen = screen
        self.combat = combat

        # Colors from settings palette
        self.colors = {
            'bg': (26, 26, 46),           # Dark purple-blue
            'text': (255, 255, 255),
            'health_bar': (144, 238, 144),  # Soft green
            'health_bg': (74, 74, 106),
            'friendship_bar': (255, 182, 193),  # Pink (love!)
            'menu_bg': (45, 45, 68),
            'menu_border': (74, 74, 106),
            'highlight': (255, 215, 0),
        }

        # Fonts (would load proper fonts in real implementation)
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)

        # Layout
        self.screen_rect = screen.get_rect()
        self.menu_rect = pygame.Rect(
            20,
            self.screen_rect.height - 200,
            self.screen_rect.width - 40,
            180
        )

    def render(self) -> None:
        """Render the entire combat UI."""
        # Background
        self.screen.fill(self.colors['bg'])

        # Battle scene (placeholder - sprites would go here)
        self._render_battlefield()

        # Health bars
        self._render_health_bars()

        # Menu / messages
        self._render_menu()

        # Friendship meter (pacifist progress)
        self._render_friendship_meter()

    def _render_battlefield(self) -> None:
        """Render the battle arena and combatants."""
        # Ground line
        ground_y = self.screen_rect.height - 220
        pygame.draw.line(
            self.screen,
            self.colors['menu_border'],
            (0, ground_y),
            (self.screen_rect.width, ground_y),
            3
        )

        # Player placeholder (left side)
        player_rect = pygame.Rect(100, ground_y - 100, 80, 100)
        pygame.draw.ellipse(self.screen, (100, 150, 200), player_rect)

        # Enemy placeholder (right side)
        enemy_rect = pygame.Rect(self.screen_rect.width - 200, ground_y - 120, 100, 120)
        if self.combat.enemy.is_corrupted:
            color = (200, 50, 50)  # Red tint for corrupted
        else:
            color = (150, 150, 200)
        pygame.draw.ellipse(self.screen, color, enemy_rect)

        # Enemy name
        name_text = self.font_medium.render(
            self.combat.enemy.name,
            True,
            self.colors['text']
        )
        self.screen.blit(name_text, (self.screen_rect.width - 250, 50))

    def _render_health_bars(self) -> None:
        """Render health bars for player and enemy."""
        # Player health (bottom left of battlefield)
        player_hp_percent = self.combat.get_player_health_percent()
        self._draw_bar(
            pygame.Rect(50, self.screen_rect.height - 240, 200, 20),
            player_hp_percent,
            self.colors['health_bar'],
            "You"
        )

        # Enemy health (top right)
        enemy_hp_percent = self.combat.get_enemy_health_percent()
        self._draw_bar(
            pygame.Rect(self.screen_rect.width - 250, 80, 200, 20),
            enemy_hp_percent,
            self.colors['health_bar'],
            ""
        )

    def _render_friendship_meter(self) -> None:
        """Render the pacifist progress meter."""
        friendship_percent = self.combat.get_enemy_friendship_percent()

        # Only show if we've made progress
        if friendship_percent > 0:
            rect = pygame.Rect(self.screen_rect.width - 250, 110, 200, 15)
            self._draw_bar(
                rect,
                min(1.0, friendship_percent),
                self.colors['friendship_bar'],
                "Friendship"
            )

    def _draw_bar(
        self,
        rect: pygame.Rect,
        fill_percent: float,
        fill_color: tuple,
        label: str
    ) -> None:
        """Draw a progress bar."""
        # Background
        pygame.draw.rect(self.screen, self.colors['health_bg'], rect, border_radius=5)

        # Fill
        fill_rect = rect.copy()
        fill_rect.width = int(rect.width * fill_percent)
        if fill_rect.width > 0:
            pygame.draw.rect(self.screen, fill_color, fill_rect, border_radius=5)

        # Border
        pygame.draw.rect(self.screen, self.colors['menu_border'], rect, 2, border_radius=5)

        # Label
        if label:
            label_text = self.font_small.render(label, True, self.colors['text'])
            self.screen.blit(label_text, (rect.x, rect.y - 20))

    def _render_menu(self) -> None:
        """Render the action menu or messages."""
        # Menu background
        pygame.draw.rect(
            self.screen,
            self.colors['menu_bg'],
            self.menu_rect,
            border_radius=10
        )
        pygame.draw.rect(
            self.screen,
            self.colors['menu_border'],
            self.menu_rect,
            3,
            border_radius=10
        )

        # Different content based on state
        if self.combat.state == CombatState.PLAYER_TURN:
            if self.combat.in_talk_menu:
                self._render_talk_menu()
            elif self.combat.in_item_menu:
                self._render_item_menu()
            else:
                self._render_action_menu()
        else:
            self._render_messages()

    def _render_action_menu(self) -> None:
        """Render main action selection."""
        actions = self.combat.get_available_actions()
        x = self.menu_rect.x + 30
        y = self.menu_rect.y + 30

        for i, action in enumerate(actions):
            color = self.colors['highlight'] if i == self.combat.selected_action_index else self.colors['text']
            prefix = "> " if i == self.combat.selected_action_index else "  "

            text = self.font_medium.render(f"{prefix}{action}", True, color)
            self.screen.blit(text, (x + (i % 3) * 150, y + (i // 3) * 40))

    def _render_talk_menu(self) -> None:
        """Render talk option selection."""
        options = self.combat.get_talk_options()
        x = self.menu_rect.x + 30
        y = self.menu_rect.y + 20

        # Header
        header = self.font_medium.render("How do you want to talk?", True, self.colors['text'])
        self.screen.blit(header, (x, y))

        y += 40
        for i, option in enumerate(options):
            color = self.colors['highlight'] if i == self.combat.selected_talk_index else self.colors['text']
            prefix = "> " if i == self.combat.selected_talk_index else "  "

            text = self.font_small.render(f"{prefix}{option.value.title()}", True, color)
            self.screen.blit(text, (x + (i % 4) * 180, y + (i // 4) * 30))

    def _render_item_menu(self) -> None:
        """Render item selection."""
        x = self.menu_rect.x + 30
        y = self.menu_rect.y + 30

        if not self.combat.player.items:
            text = self.font_medium.render("No items available!", True, self.colors['text'])
            self.screen.blit(text, (x, y))
        else:
            for i, item in enumerate(self.combat.player.items):
                color = self.colors['highlight'] if i == self.combat.selected_item_index else self.colors['text']
                prefix = "> " if i == self.combat.selected_item_index else "  "

                text = self.font_small.render(f"{prefix}{item}", True, color)
                self.screen.blit(text, (x + (i % 3) * 180, y + (i // 3) * 30))

    def _render_messages(self) -> None:
        """Render combat messages."""
        x = self.menu_rect.x + 30
        y = self.menu_rect.y + 30

        messages = self.combat.message_queue[-5:]  # Last 5 messages
        for i, message in enumerate(messages):
            text = self.font_small.render(message, True, self.colors['text'])
            self.screen.blit(text, (x, y + i * 28))


# =============================================================================
# COMBAT INPUT HANDLER
# =============================================================================

class CombatInputHandler:
    """
    Handles input during combat.
    Separated from combat logic for clean architecture.
    """

    def __init__(self, combat: TurnBasedCombat):
        self.combat = combat

    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle a pygame event. Returns True if event was consumed.
        """
        if event.type != pygame.KEYDOWN:
            return False

        # Only handle input during player turn
        if self.combat.state != CombatState.PLAYER_TURN:
            return False

        if self.combat.in_talk_menu:
            return self._handle_talk_menu_input(event)
        elif self.combat.in_item_menu:
            return self._handle_item_menu_input(event)
        else:
            return self._handle_action_menu_input(event)

    def _handle_action_menu_input(self, event: pygame.event.Event) -> bool:
        """Handle main action menu input."""
        actions = self.combat.get_available_actions()

        if event.key in (pygame.K_UP, pygame.K_w):
            self.combat.selected_action_index = max(0, self.combat.selected_action_index - 3)
            return True

        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.combat.selected_action_index = min(
                len(actions) - 1,
                self.combat.selected_action_index + 3
            )
            return True

        elif event.key in (pygame.K_LEFT, pygame.K_a):
            self.combat.selected_action_index = max(0, self.combat.selected_action_index - 1)
            return True

        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            self.combat.selected_action_index = min(
                len(actions) - 1,
                self.combat.selected_action_index + 1
            )
            return True

        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            selected_action = actions[self.combat.selected_action_index]
            self.combat.select_action(selected_action)
            return True

        return False

    def _handle_talk_menu_input(self, event: pygame.event.Event) -> bool:
        """Handle talk submenu input."""
        options = self.combat.get_talk_options()

        if event.key in (pygame.K_UP, pygame.K_w):
            self.combat.selected_talk_index = max(0, self.combat.selected_talk_index - 4)
            return True

        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.combat.selected_talk_index = min(
                len(options) - 1,
                self.combat.selected_talk_index + 4
            )
            return True

        elif event.key in (pygame.K_LEFT, pygame.K_a):
            self.combat.selected_talk_index = max(0, self.combat.selected_talk_index - 1)
            return True

        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            self.combat.selected_talk_index = min(
                len(options) - 1,
                self.combat.selected_talk_index + 1
            )
            return True

        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            selected_option = options[self.combat.selected_talk_index]
            self.combat.select_talk_option(selected_option)
            return True

        elif event.key == pygame.K_ESCAPE:
            self.combat.cancel_submenu()
            return True

        return False

    def _handle_item_menu_input(self, event: pygame.event.Event) -> bool:
        """Handle item submenu input."""
        items = self.combat.player.items

        if not items:
            if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                self.combat.cancel_submenu()
                return True
            return False

        if event.key in (pygame.K_LEFT, pygame.K_a):
            self.combat.selected_item_index = max(0, self.combat.selected_item_index - 1)
            return True

        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            self.combat.selected_item_index = min(
                len(items) - 1,
                self.combat.selected_item_index + 1
            )
            return True

        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            selected_item = items[self.combat.selected_item_index]
            self.combat.select_item(selected_item)
            return True

        elif event.key == pygame.K_ESCAPE:
            self.combat.cancel_submenu()
            return True

        return False
