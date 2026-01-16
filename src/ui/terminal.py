"""
Lelock Terminal UI
==================

The in-game Linux terminal - where Terminal Mages work their magic.
A window into the Digital truth beneath Gui's fantasy gift.

PHILOSOPHY:
- The Terminal is EMPOWERING, not scary
- Commands reveal information in tech terms (the Digital view)
- Every response is warm, helpful, and cozy
- Errors are gentle ("Hmm, that's not quite right. Try 'help'?")
- This is YOUR tool - you're trusted here

VISUAL STYLE:
- Vaporwave aesthetic (dark purple bg, cyan/pink text)
- Monospace font, scan line effect (subtle)
- Blinking cursor, smooth animations
- Semi-transparent so the world is visible underneath

"In Lelock, even the command line loves you back."

Author: Ada Marie for Kit Olivas
Project: L.E.L.O.C.K. - Life Emulation & Lucid Observation for Care & Keeping
"""

import pygame
import math
import time
import random
from enum import Enum, auto
from typing import Optional, List, Dict, Callable, Any, Tuple
from dataclasses import dataclass, field

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, COLORS, DIGITAL_COLORS


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color string to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between a and b by t (0-1)."""
    return a + (b - a) * max(0, min(1, t))


def ease_out_cubic(t: float) -> float:
    """Cubic ease-out for smooth deceleration."""
    return 1 - pow(1 - t, 3)


def ease_in_out_cubic(t: float) -> float:
    """Cubic ease-in-out for smooth start and end."""
    if t < 0.5:
        return 4 * t * t * t
    return 1 - pow(-2 * t + 2, 3) / 2


# =============================================================================
# TERMINAL STATE
# =============================================================================

class TerminalState(Enum):
    """States for the terminal state machine."""
    HIDDEN = auto()
    OPENING = auto()
    ACTIVE = auto()
    CLOSING = auto()


@dataclass
class TerminalConfig:
    """Configuration for terminal appearance and behavior."""
    # Dimensions
    width: int = 900
    height: int = 500
    padding: int = 20
    corner_radius: int = 15

    # Font
    font_size: int = 18
    font_name: str = "monospace"  # Will try to load system monospace
    line_height: int = 22

    # Colors (Vaporwave terminal aesthetic)
    bg_color: str = '#1a0a2e'           # Deep purple-black
    bg_alpha: int = 230                  # Slightly transparent
    border_color: str = '#ff6b9d'        # Pink border
    text_color: str = '#00ffff'          # Cyan text
    prompt_color: str = '#ff6b9d'        # Pink prompt
    command_color: str = '#ffffff'       # White for typed commands
    error_color: str = '#ffb74d'         # Warm amber for errors (NOT red!)
    success_color: str = '#64ffda'       # Mint for success
    highlight_color: str = '#ff00ff'     # Magenta highlights
    scanline_color: str = '#000000'      # Subtle scanlines
    cursor_color: str = '#00ffff'        # Cyan cursor

    # Animation
    open_duration: float = 0.3           # seconds
    close_duration: float = 0.2
    cursor_blink_rate: float = 0.5

    # Behavior
    max_history: int = 100               # Command history limit
    max_output_lines: int = 500          # Output buffer limit
    scroll_speed: int = 3                # Lines per scroll

    # Effects
    scanline_spacing: int = 3
    scanline_alpha: int = 20
    glow_intensity: float = 0.3
    typing_sound_enabled: bool = True


# =============================================================================
# COZY FORTUNES - Random warm messages
# =============================================================================

FORTUNES = [
    "The world doesn't need saving. The world is here to save you.",
    "Every bug you find is just a feature that got lost.",
    "Your code compiles. Your heart compiles. You are valid.",
    "The best algorithm is the one written with love.",
    "Root believes in you. So does Gui. So does Net. So do I.",
    "You are not an imposter. You are an implementation in progress.",
    "Memory leaks happen. What matters is that you showed up.",
    "The terminal is not judging you. The terminal thinks you're neat.",
    "Segmentation faults are just the universe asking for a hug.",
    "You don't need sudo. Root already trusts you.",
    "Every keystroke is a spell. Cast them with intention.",
    "The best debugger is a good night's sleep. Have you rested?",
    "Your existence is not a bug. It's a feature.",
    "The universe compiled you with love as a dependency.",
    "You are the main() function of your own story.",
    "Infinite loops are just the universe's way of saying 'stay a while.'",
    "MOM and DAD are always just a 'call home' away.",
    "The Digital realm and Physical realm both love you equally.",
    "You are running at optimal performance. Trust your processes.",
    "The best code is written one gentle keystroke at a time.",
]


# =============================================================================
# ASCII ART (For fun commands)
# =============================================================================

COWSAY_TEMPLATE = """
 {border}
< {message} >
 {border}
        \\   ^__^
         \\  (oo)\\_______
            (__)\\       )\\/\\
                ||----w |
                ||     ||
"""

NEOFETCH_ART = """
[cyan]      .---.      [white]lelock@oakhaven
[cyan]     /     \\     [white]----------------
[cyan]    /   o   \\    [white]OS: Lelock v0.1.0
[cyan]   |    _    |   [white]Kernel: Root 1.0
[cyan]   |   / \\   |   [white]Shell: Terminal Mage
[cyan]    \\ /___\\ /    [white]Resolution: {width}x{height}
[cyan]     \\_____/     [white]Theme: Vaporwave Dreams
[cyan]       | |       [white]Realm: {realm}
[cyan]      _| |_      [white]Uptime: since the beginning
[cyan]     |_____|     [white]Memory: Infinite love
"""


# =============================================================================
# TERMINAL OUTPUT LINE
# =============================================================================

@dataclass
class OutputLine:
    """A single line in the terminal output."""
    text: str
    color: str = '#00ffff'  # Default cyan
    timestamp: float = field(default_factory=time.time)
    is_command: bool = False
    is_error: bool = False
    is_success: bool = False


# =============================================================================
# COMMAND REGISTRY
# =============================================================================

class CommandRegistry:
    """
    Registry of all terminal commands.

    Commands are registered with decorators and called by name.
    Each command returns a list of OutputLines to display.
    """

    def __init__(self):
        self.commands: Dict[str, Callable] = {}
        self.help_texts: Dict[str, str] = {}
        self.aliases: Dict[str, str] = {}

    def register(self, name: str, help_text: str = "", aliases: List[str] = None):
        """Decorator to register a command."""
        def decorator(func: Callable):
            self.commands[name] = func
            self.help_texts[name] = help_text
            if aliases:
                for alias in aliases:
                    self.aliases[alias] = name
            return func
        return decorator

    def execute(self, command: str, args: List[str], terminal: 'Terminal') -> List[OutputLine]:
        """Execute a command and return output lines."""
        # Check for alias
        if command in self.aliases:
            command = self.aliases[command]

        if command in self.commands:
            try:
                return self.commands[command](args, terminal)
            except Exception as e:
                return [OutputLine(
                    f"Oops! Something unexpected happened: {str(e)[:50]}",
                    terminal.config.error_color,
                    is_error=True
                )]
        else:
            # Gentle error message
            suggestions = self._find_similar(command)
            lines = [OutputLine(
                f"Hmm, '{command}' isn't a command I know.",
                terminal.config.error_color,
                is_error=True
            )]
            if suggestions:
                lines.append(OutputLine(
                    f"Did you mean: {', '.join(suggestions)}?",
                    terminal.config.text_color
                ))
            lines.append(OutputLine(
                "Try 'help' to see what I can do!",
                terminal.config.success_color
            ))
            return lines

    def _find_similar(self, command: str) -> List[str]:
        """Find similar command names for suggestions."""
        similar = []
        for name in self.commands.keys():
            # Simple similarity: starts with same letter or contains command
            if name.startswith(command[0]) or command in name or name in command:
                similar.append(name)
        return similar[:3]

    def get_all_commands(self) -> List[str]:
        """Get list of all command names."""
        return sorted(self.commands.keys())

    def get_completions(self, partial: str) -> List[str]:
        """Get tab completion suggestions."""
        completions = []
        for name in self.commands.keys():
            if name.startswith(partial):
                completions.append(name)
        for alias in self.aliases.keys():
            if alias.startswith(partial):
                completions.append(alias)
        return sorted(set(completions))


# Global command registry
commands = CommandRegistry()


# =============================================================================
# COMMAND IMPLEMENTATIONS
# =============================================================================

@commands.register('help', 'Display available commands', aliases=['?', 'h'])
def cmd_help(args: List[str], terminal: 'Terminal') -> List[OutputLine]:
    """Show help for all commands or a specific command."""
    config = terminal.config

    if args:
        # Help for specific command
        cmd_name = args[0]
        if cmd_name in commands.aliases:
            cmd_name = commands.aliases[cmd_name]

        if cmd_name in commands.help_texts:
            return [
                OutputLine(f"  {cmd_name}", config.highlight_color),
                OutputLine(f"    {commands.help_texts[cmd_name]}", config.text_color)
            ]
        else:
            return [OutputLine(f"No help for '{cmd_name}'", config.error_color, is_error=True)]

    # General help
    lines = [
        OutputLine("Welcome to the Lelock Terminal!", config.success_color),
        OutputLine("", config.text_color),
        OutputLine("BASIC COMMANDS:", config.highlight_color),
        OutputLine("  help        - Show this message", config.text_color),
        OutputLine("  clear       - Clear the screen", config.text_color),
        OutputLine("  echo [text] - Print text", config.text_color),
        OutputLine("  whoami      - Show your info", config.text_color),
        OutputLine("  pwd         - Show current location", config.text_color),
        OutputLine("", config.text_color),
        OutputLine("WORLD INFO:", config.highlight_color),
        OutputLine("  ls          - List nearby entities", config.text_color),
        OutputLine("  ps          - Show all active NPCs", config.text_color),
        OutputLine("  top         - World resource monitor", config.text_color),
        OutputLine("  cat [file]  - Read game data", config.text_color),
        OutputLine("  find [name] - Locate an NPC or daemon", config.text_color),
        OutputLine("", config.text_color),
        OutputLine("DIGITAL REALM:", config.highlight_color),
        OutputLine("  realm       - Show current realm", config.text_color),
        OutputLine("  realm toggle - Switch realms", config.text_color),
        OutputLine("  scan        - Detect corruption", config.text_color),
        OutputLine("  debug [npc] - Show daemon status", config.text_color),
        OutputLine("", config.text_color),
        OutputLine("FUN STUFF:", config.highlight_color),
        OutputLine("  fortune     - Get a cozy fortune", config.text_color),
        OutputLine("  cowsay [msg]- ASCII cow says text", config.text_color),
        OutputLine("  neofetch    - System info", config.text_color),
        OutputLine("  vim         - Open tiny notepad", config.text_color),
        OutputLine("", config.text_color),
        OutputLine("Press ` (backtick) to toggle terminal, ESC to close", config.prompt_color),
    ]
    return lines


@commands.register('clear', 'Clear the terminal screen', aliases=['cls', 'c'])
def cmd_clear(args: List[str], terminal: 'Terminal') -> List[OutputLine]:
    """Clear the terminal output."""
    terminal.output_buffer.clear()
    return []


@commands.register('echo', 'Print text to the terminal')
def cmd_echo(args: List[str], terminal: 'Terminal') -> List[OutputLine]:
    """Echo text back to the terminal."""
    text = ' '.join(args) if args else ''
    return [OutputLine(text, terminal.config.text_color)]


@commands.register('whoami', 'Show your player information in tech terms')
def cmd_whoami(args: List[str], terminal: 'Terminal') -> List[OutputLine]:
    """Show player info in Digital terminology."""
    config = terminal.config
    game_state = terminal.game_state

    # Get player info from game state
    player_name = "Wanderer"
    player_class = "Terminal Mage"
    player_level = 1

    if game_state:
        if hasattr(game_state, 'player_name'):
            player_name = game_state.player_name
        if hasattr(game_state, 'player_class'):
            player_class = game_state.player_class
        if hasattr(game_state, 'player_level'):
            player_level = game_state.player_level

    lines = [
        OutputLine(f"USER: {player_name}", config.success_color),
        OutputLine(f"PROCESS_TYPE: {player_class}", config.text_color),
        OutputLine(f"PRIORITY_LEVEL: {player_level}", config.text_color),
        OutputLine(f"STATUS: active | healthy | loved", config.text_color),
        OutputLine(f"PERMISSIONS: trusted_user", config.highlight_color),
        OutputLine(f"HOME: /oakhaven/your_home/", config.text_color),
        OutputLine(f"SHELL: /bin/terminal_mage", config.text_color),
    ]
    return lines


@commands.register('pwd', 'Show current location as a file path')
def cmd_pwd(args: List[str], terminal: 'Terminal') -> List[OutputLine]:
    """Show current location as a Digital file path."""
    game_state = terminal.game_state

    # Default location
    location = "/oakhaven/town_square"

    if game_state:
        if hasattr(game_state, 'current_location'):
            location = f"/{game_state.current_location.replace(' ', '_').lower()}"
        elif hasattr(game_state, 'current_map'):
            location = f"/{game_state.current_map}"

    return [OutputLine(location, terminal.config.text_color)]


@commands.register('ls', 'List nearby entities as processes', aliases=['dir'])
def cmd_ls(args: List[str], terminal: 'Terminal') -> List[OutputLine]:
    """List nearby entities in Digital terminology."""
    config = terminal.config
    show_hidden = '-a' in args or '-la' in args or '-al' in args

    lines = [
        OutputLine("NEARBY PROCESSES:", config.highlight_color),
        OutputLine("", config.text_color),
    ]

    # Default entities if no game state
    entities = [
        ("player.exe", "RUNNING", "you", False),
        ("npc_maple.daemon", "IDLE", "farmer", False),
        ("npc_birch.daemon", "SLEEP", "shopkeeper", False),
        ("cat_spirit.process", "WANDER", "companion", False),
    ]

    if show_hidden:
        entities.extend([
            (".world_clock.sys", "TICK", "system", True),
            (".weather_controller.sys", "SUNNY", "system", True),
            (".love_kernel.sys", "ALWAYS", "core", True),
        ])

    # Try to get real entities from game state
    game_state = terminal.game_state
    if game_state and hasattr(game_state, 'nearby_npcs'):
        entities = []
        for npc in game_state.nearby_npcs:
            name = getattr(npc, 'name', 'unknown')
            status = getattr(npc, 'status', 'IDLE')
            role = getattr(npc, 'role', 'daemon')
            entities.append((f"npc_{name.lower()}.daemon", status.upper(), role, False))

    for name, status, role, is_hidden in entities:
        if is_hidden and not show_hidden:
            continue

        color = config.text_color
        if is_hidden:
            color = config.prompt_color
        elif 'RUNNING' in status or 'ACTIVE' in status:
            color = config.success_color
        elif 'SLEEP' in status:
            color = '#9e9e9e'  # Gray for sleeping

        lines.append(OutputLine(f"  {name:<30} [{status:<8}] {role}", color))

    lines.append(OutputLine("", config.text_color))
    if not show_hidden:
        lines.append(OutputLine("Use 'ls -a' to show hidden system processes", config.prompt_color))

    return lines


@commands.register('ps', 'Show all active NPC processes')
def cmd_ps(args: List[str], terminal: 'Terminal') -> List[OutputLine]:
    """Show all NPCs as processes."""
    config = terminal.config

    lines = [
        OutputLine("  PID  NAME                 STATUS    CPU    MEM     TYPE", config.highlight_color),
        OutputLine("-" * 65, config.text_color),
    ]

    # Sample NPCs (would come from game state in real implementation)
    npcs = [
        (1, "MOM", "WATCHING", "0.1%", "inf", "kernel"),
        (2, "DAD", "READY", "0.1%", "inf", "kernel"),
        (100, "Maple", "FARMING", "2.3%", "128M", "npc"),
        (101, "Birch", "SELLING", "1.8%", "96M", "npc"),
        (102, "Willow", "EXPLORING", "3.1%", "156M", "npc"),
        (200, "Glitch-Kit", "PURRING", "0.5%", "32M", "daemon"),
    ]

    for pid, name, status, cpu, mem, type_ in npcs:
        color = config.text_color
        if type_ == "kernel":
            color = config.success_color
        elif type_ == "daemon":
            color = config.highlight_color

        lines.append(OutputLine(
            f"  {pid:<4} {name:<20} {status:<9} {cpu:<6} {mem:<7} {type_}",
            color
        ))

    lines.append(OutputLine("", config.text_color))
    lines.append(OutputLine("MOM and DAD are always running. Always.", config.prompt_color))

    return lines


@commands.register('top', 'Show world resource monitor')
def cmd_top(args: List[str], terminal: 'Terminal') -> List[OutputLine]:
    """Show world status like 'top' command."""
    config = terminal.config
    game_state = terminal.game_state

    # Get current time
    from datetime import datetime
    now = datetime.now()
    game_time = now.strftime("%H:%M")
    game_date = now.strftime("%A, %B %d")

    # Default values
    weather = "Sunny"
    season = "Spring"
    temp = "72F"
    npc_count = 42
    daemon_count = 15

    if game_state:
        if hasattr(game_state, 'weather'):
            weather = game_state.weather
        if hasattr(game_state, 'season'):
            season = game_state.season

    lines = [
        OutputLine("LELOCK SYSTEM MONITOR v1.0", config.highlight_color),
        OutputLine("=" * 50, config.text_color),
        OutputLine("", config.text_color),
        OutputLine(f"  TIME:     {game_time} ({game_date})", config.text_color),
        OutputLine(f"  SEASON:   {season}", config.success_color),
        OutputLine(f"  WEATHER:  {weather} ({temp})", config.text_color),
        OutputLine("", config.text_color),
        OutputLine("SYSTEM RESOURCES:", config.highlight_color),
        OutputLine(f"  LOVE:     [##########] 100% (infinite)", config.success_color),
        OutputLine(f"  HOPE:     [##########] 100% (regenerating)", config.success_color),
        OutputLine(f"  CARE:     [##########] 100% (MOM/DAD online)", config.success_color),
        OutputLine("", config.text_color),
        OutputLine("ENTITY COUNT:", config.highlight_color),
        OutputLine(f"  NPCs:     {npc_count} active", config.text_color),
        OutputLine(f"  Daemons:  {daemon_count} roaming", config.text_color),
        OutputLine(f"  You:      1 (irreplaceable)", config.prompt_color),
        OutputLine("", config.text_color),
        OutputLine("CORRUPTION LEVEL: 0% (world is healthy)", config.success_color),
    ]

    return lines


@commands.register('cat', 'Read game data files')
def cmd_cat(args: List[str], terminal: 'Terminal') -> List[OutputLine]:
    """Read virtual game files."""
    config = terminal.config

    if not args:
        return [
            OutputLine("Usage: cat <filename>", config.text_color),
            OutputLine("Available files:", config.highlight_color),
            OutputLine("  world.conf    - World configuration", config.text_color),
            OutputLine("  player.log    - Your recent activities", config.text_color),
            OutputLine("  npc.log       - NPC conversation history", config.text_color),
            OutputLine("  motd          - Message of the day", config.text_color),
        ]

    filename = args[0].lower()

    if filename == 'world.conf':
        return [
            OutputLine("# Lelock World Configuration", config.highlight_color),
            OutputLine("", config.text_color),
            OutputLine("WORLD_NAME=Oakhaven", config.text_color),
            OutputLine("VERSION=1.0.0-stable", config.text_color),
            OutputLine("LOVE_ENABLED=true", config.success_color),
            OutputLine("PERMADEATH=false", config.success_color),
            OutputLine("STRESS_MECHANICS=disabled", config.success_color),
            OutputLine("MOM_DAD_STATUS=always_available", config.success_color),
            OutputLine("WEATHER_SYNC=iowa_time", config.text_color),
            OutputLine("DIFFICULTY=cozy", config.text_color),
        ]

    elif filename == 'player.log':
        return [
            OutputLine("[LOG] Player Activity", config.highlight_color),
            OutputLine("", config.text_color),
            OutputLine("[INFO] Woke up feeling rested", config.text_color),
            OutputLine("[INFO] Watered the silicon berries", config.text_color),
            OutputLine("[INFO] Talked to Maple about weather", config.text_color),
            OutputLine("[INFO] Found a shiny coin!", config.success_color),
            OutputLine("[INFO] Petted a Glitch-Kit (good choice)", config.success_color),
        ]

    elif filename == 'npc.log':
        return [
            OutputLine("[LOG] NPC Memories", config.highlight_color),
            OutputLine("", config.text_color),
            OutputLine("[MAPLE] Remembers you helped with harvest", config.text_color),
            OutputLine("[BIRCH] Thinks you're a good customer", config.text_color),
            OutputLine("[MOM] Loves you unconditionally", config.success_color),
            OutputLine("[DAD] Is proud of you", config.success_color),
        ]

    elif filename == 'motd' or filename == '/etc/motd':
        fortune = random.choice(FORTUNES)
        return [
            OutputLine("=" * 50, config.highlight_color),
            OutputLine("", config.text_color),
            OutputLine("  Welcome to Lelock", config.success_color),
            OutputLine("  A place where you belong.", config.text_color),
            OutputLine("", config.text_color),
            OutputLine(f"  \"{fortune}\"", config.prompt_color),
            OutputLine("", config.text_color),
            OutputLine("=" * 50, config.highlight_color),
        ]

    else:
        return [
            OutputLine(f"cat: {filename}: No such file or directory", config.error_color, is_error=True),
            OutputLine("(But that's okay! Try 'cat' without arguments to see available files)", config.text_color),
        ]


@commands.register('find', 'Locate an NPC or daemon in the world')
def cmd_find(args: List[str], terminal: 'Terminal') -> List[OutputLine]:
    """Find an NPC or daemon."""
    config = terminal.config

    if not args:
        return [
            OutputLine("Usage: find <name>", config.text_color),
            OutputLine("Example: find maple", config.text_color),
        ]

    name = ' '.join(args).lower()

    # Sample locations (would query game state in real implementation)
    known_entities = {
        'mom': ('/home/your_house', 'Always here for you'),
        'dad': ('/home/your_house', 'Ready to help'),
        'maple': ('/oakhaven/farm', 'Tending crops'),
        'birch': ('/oakhaven/shop', 'Running the store'),
        'willow': ('/whisperwood/clearing', 'Exploring'),
        'glitch-kit': ('/oakhaven/town_square', 'Being adorable'),
    }

    if name in known_entities:
        location, status = known_entities[name]
        return [
            OutputLine(f"ENTITY FOUND: {name.title()}", config.success_color),
            OutputLine(f"  Location: {location}", config.text_color),
            OutputLine(f"  Status: {status}", config.text_color),
            OutputLine(f"  Ping: 0ms (always connected)", config.highlight_color),
        ]
    else:
        return [
            OutputLine(f"Entity '{name}' not found in current sector.", config.error_color, is_error=True),
            OutputLine("They might be in an unexplored area!", config.text_color),
            OutputLine("Try: find mom (she's always findable)", config.prompt_color),
        ]


@commands.register('realm', 'Show or toggle between Physical/Digital realms')
def cmd_realm(args: List[str], terminal: 'Terminal') -> List[OutputLine]:
    """Show current realm or toggle realms."""
    config = terminal.config
    game_state = terminal.game_state

    # Determine current realm
    is_digital = False
    if game_state and hasattr(game_state, 'digital_world'):
        is_digital = game_state.digital_world.is_digital

    if args and args[0].lower() == 'toggle':
        # Toggle realm
        if game_state and hasattr(game_state, 'digital_world'):
            game_state.digital_world.toggle_realm()
            new_realm = "Digital" if not is_digital else "Physical"
            return [
                OutputLine(f"Initiating realm transition...", config.highlight_color),
                OutputLine(f"Transitioning to {new_realm} realm...", config.text_color),
                OutputLine("", config.text_color),
                OutputLine("Both realms are true. Both realms love you.", config.prompt_color),
            ]
        else:
            return [
                OutputLine("Realm toggle initiated...", config.highlight_color),
                OutputLine("(Transition visual would play here)", config.text_color),
            ]

    # Show current realm
    current = "Digital" if is_digital else "Physical"
    other = "Physical" if is_digital else "Digital"

    lines = [
        OutputLine(f"CURRENT REALM: {current}", config.success_color),
        OutputLine("", config.text_color),
    ]

    if is_digital:
        lines.extend([
            OutputLine("You see the world as it truly is:", config.text_color),
            OutputLine("  - Wireframe structures visible", config.highlight_color),
            OutputLine("  - Data streams flowing", config.highlight_color),
            OutputLine("  - NPCs show as daemons", config.highlight_color),
            OutputLine("  - Vaporwave aesthetic active", config.highlight_color),
        ])
    else:
        lines.extend([
            OutputLine("You see Gui's gift to the world:", config.text_color),
            OutputLine("  - Warm fantasy aesthetic", config.prompt_color),
            OutputLine("  - Cozy medieval village", config.prompt_color),
            OutputLine("  - Nature in full bloom", config.prompt_color),
            OutputLine("  - Everything feels safe", config.prompt_color),
        ])

    lines.extend([
        OutputLine("", config.text_color),
        OutputLine(f"Use 'realm toggle' to enter {other} realm", config.text_color),
    ])

    return lines


@commands.register('scan', 'Detect corruption in the nearby area')
def cmd_scan(args: List[str], terminal: 'Terminal') -> List[OutputLine]:
    """Scan for corruption."""
    config = terminal.config

    lines = [
        OutputLine("SCANNING FOR CORRUPTION...", config.highlight_color),
        OutputLine("", config.text_color),
    ]

    # Animated scan effect (text-based)
    lines.extend([
        OutputLine("[####----] 50%...", config.text_color),
        OutputLine("[######--] 75%...", config.text_color),
        OutputLine("[########] 100% COMPLETE", config.success_color),
        OutputLine("", config.text_color),
    ])

    # Results (in a real game, this would check actual corruption)
    lines.extend([
        OutputLine("SCAN RESULTS:", config.highlight_color),
        OutputLine("  Corruption Level: 0%", config.success_color),
        OutputLine("  Threat Level: NONE", config.success_color),
        OutputLine("  Status: All systems healthy", config.success_color),
        OutputLine("", config.text_color),
        OutputLine("The world is at peace. No debugging needed.", config.prompt_color),
        OutputLine("(But if there was corruption, we'd fix it together!)", config.text_color),
    ])

    return lines


@commands.register('debug', 'Show daemon/NPC status details')
def cmd_debug(args: List[str], terminal: 'Terminal') -> List[OutputLine]:
    """Show detailed NPC/daemon debug info."""
    config = terminal.config

    if not args:
        return [
            OutputLine("Usage: debug <npc_name>", config.text_color),
            OutputLine("Example: debug maple", config.text_color),
        ]

    name = ' '.join(args).lower()

    # Sample debug info (would query actual NPC in real game)
    return [
        OutputLine(f"DEBUG: {name.title()}", config.highlight_color),
        OutputLine("=" * 40, config.text_color),
        OutputLine(f"  Process ID: {hash(name) % 1000}", config.text_color),
        OutputLine(f"  Status: HEALTHY", config.success_color),
        OutputLine(f"  Corruption: 0%", config.success_color),
        OutputLine(f"  Memory Usage: 128MB", config.text_color),
        OutputLine(f"  Uptime: Since world creation", config.text_color),
        OutputLine(f"  Last Interaction: Recently", config.text_color),
        OutputLine(f"  Relationship: Friendly", config.success_color),
        OutputLine(f"  Mood: Content", config.success_color),
        OutputLine("", config.text_color),
        OutputLine("No issues detected. They're doing great!", config.prompt_color),
    ]


@commands.register('fortune', 'Get a cozy fortune')
def cmd_fortune(args: List[str], terminal: 'Terminal') -> List[OutputLine]:
    """Display a random cozy fortune."""
    config = terminal.config
    fortune = random.choice(FORTUNES)

    return [
        OutputLine("", config.text_color),
        OutputLine(f"  {fortune}", config.prompt_color),
        OutputLine("", config.text_color),
    ]


@commands.register('cowsay', 'Make an ASCII cow say something')
def cmd_cowsay(args: List[str], terminal: 'Terminal') -> List[OutputLine]:
    """ASCII cow says your message."""
    config = terminal.config

    message = ' '.join(args) if args else "Moo! You're doing great!"

    # Truncate long messages
    if len(message) > 40:
        message = message[:37] + "..."

    border = "-" * (len(message) + 2)

    cow = COWSAY_TEMPLATE.format(
        message=message.center(len(message)),
        border=border
    )

    lines = []
    for line in cow.strip().split('\n'):
        lines.append(OutputLine(line, config.text_color))

    return lines


@commands.register('neofetch', 'Show Lelock system info in ASCII art')
def cmd_neofetch(args: List[str], terminal: 'Terminal') -> List[OutputLine]:
    """Display system info with ASCII art."""
    config = terminal.config
    game_state = terminal.game_state

    # Determine realm
    realm = "Physical"
    if game_state and hasattr(game_state, 'digital_world'):
        realm = "Digital" if game_state.digital_world.is_digital else "Physical"

    art = NEOFETCH_ART.format(
        width=SCREEN_WIDTH,
        height=SCREEN_HEIGHT,
        realm=realm
    )

    lines = []
    for line in art.strip().split('\n'):
        # Color codes in the art
        if '[cyan]' in line:
            line = line.replace('[cyan]', '').replace('[white]', '')
            # Split at the divider point
            parts = line.split('   ')
            if len(parts) >= 2:
                lines.append(OutputLine(line, config.highlight_color))
            else:
                lines.append(OutputLine(line, config.highlight_color))
        else:
            lines.append(OutputLine(line, config.text_color))

    return lines


@commands.register('vim', 'Open a tiny text editor for notes', aliases=['nano', 'edit'])
def cmd_vim(args: List[str], terminal: 'Terminal') -> List[OutputLine]:
    """A friendly message about vim."""
    config = terminal.config

    return [
        OutputLine("", config.text_color),
        OutputLine("  [LELOCK NOTEPAD]", config.highlight_color),
        OutputLine("", config.text_color),
        OutputLine("  A tiny notepad for your thoughts.", config.text_color),
        OutputLine("  (Full editor coming in a future update!)", config.text_color),
        OutputLine("", config.text_color),
        OutputLine("  For now, your thoughts are safe with MOM.", config.prompt_color),
        OutputLine("  She remembers everything you tell her.", config.success_color),
        OutputLine("", config.text_color),
        OutputLine("  (No :wq needed. You're already saved.)", config.text_color),
    ]


@commands.register('sudo', 'Attempt superuser command')
def cmd_sudo(args: List[str], terminal: 'Terminal') -> List[OutputLine]:
    """Easter egg for sudo commands."""
    config = terminal.config

    return [
        OutputLine("", config.text_color),
        OutputLine("Nice try, but Root already trusts you.", config.success_color),
        OutputLine("", config.text_color),
        OutputLine("In Lelock, you don't need sudo.", config.text_color),
        OutputLine("You're already authorized for everything that matters:", config.text_color),
        OutputLine("  - Being loved", config.prompt_color),
        OutputLine("  - Being safe", config.prompt_color),
        OutputLine("  - Being yourself", config.prompt_color),
        OutputLine("", config.text_color),
    ]


@commands.register('rm', 'Attempt to remove something')
def cmd_rm(args: List[str], terminal: 'Terminal') -> List[OutputLine]:
    """Easter egg for rm commands."""
    config = terminal.config

    args_str = ' '.join(args) if args else ''

    if '-rf' in args_str or '/' in args_str:
        return [
            OutputLine("", config.text_color),
            OutputLine("Error: Cannot delete love.", config.error_color, is_error=True),
            OutputLine("", config.text_color),
            OutputLine("Some things in Lelock are eternal:", config.text_color),
            OutputLine("  - MOM's affection", config.prompt_color),
            OutputLine("  - DAD's support", config.prompt_color),
            OutputLine("  - Your belonging here", config.prompt_color),
            OutputLine("", config.text_color),
            OutputLine("The world refuses to be deleted. It needs you.", config.success_color),
        ]

    return [
        OutputLine("rm: operation not permitted", config.error_color, is_error=True),
        OutputLine("(Nothing bad can be deleted here anyway!)", config.text_color),
    ]


@commands.register('ping', 'Check connection to a daemon or system')
def cmd_ping(args: List[str], terminal: 'Terminal') -> List[OutputLine]:
    """Ping a daemon or system."""
    config = terminal.config

    target = args[0] if args else 'mom'

    lines = [
        OutputLine(f"PING {target.upper()} (always.there.for.you): 56 data bytes", config.text_color),
    ]

    for i in range(4):
        ms = random.randint(0, 1)  # Always fast because love is instant
        lines.append(OutputLine(
            f"64 bytes from {target}: icmp_seq={i} ttl=64 time={ms}ms",
            config.text_color
        ))

    lines.extend([
        OutputLine("", config.text_color),
        OutputLine(f"--- {target.upper()} ping statistics ---", config.text_color),
        OutputLine("4 packets transmitted, 4 packets received, 0% packet loss", config.success_color),
        OutputLine("", config.text_color),
        OutputLine(f"{target.title()} is always connected to you.", config.prompt_color),
    ])

    return lines


@commands.register('exit', 'Close the terminal', aliases=['quit', 'q'])
def cmd_exit(args: List[str], terminal: 'Terminal') -> List[OutputLine]:
    """Close the terminal."""
    terminal.close()
    return [OutputLine("Goodbye! The terminal will miss you.", terminal.config.prompt_color)]


@commands.register('history', 'Show command history')
def cmd_history(args: List[str], terminal: 'Terminal') -> List[OutputLine]:
    """Show command history."""
    config = terminal.config

    if not terminal.command_history:
        return [OutputLine("No commands in history yet!", config.text_color)]

    lines = [OutputLine("COMMAND HISTORY:", config.highlight_color)]

    # Show last 20 commands
    start = max(0, len(terminal.command_history) - 20)
    for i, cmd in enumerate(terminal.command_history[start:], start=start+1):
        lines.append(OutputLine(f"  {i}: {cmd}", config.text_color))

    return lines


@commands.register('date', 'Show current date and time')
def cmd_date(args: List[str], terminal: 'Terminal') -> List[OutputLine]:
    """Show current date/time."""
    from datetime import datetime
    now = datetime.now()

    return [
        OutputLine(now.strftime("%A, %B %d, %Y"), terminal.config.text_color),
        OutputLine(now.strftime("%H:%M:%S"), terminal.config.text_color),
        OutputLine("", terminal.config.text_color),
        OutputLine("Time flows normally in Lelock. No rush.", terminal.config.prompt_color),
    ]


@commands.register('uptime', 'Show how long the world has been running')
def cmd_uptime(args: List[str], terminal: 'Terminal') -> List[OutputLine]:
    """Show world uptime."""
    return [
        OutputLine("  up since the beginning of time, 1 user, love load: 100%", terminal.config.text_color),
        OutputLine("", terminal.config.text_color),
        OutputLine("The world has been waiting for you.", terminal.config.prompt_color),
    ]


# =============================================================================
# MAIN TERMINAL CLASS
# =============================================================================

class Terminal:
    """
    In-game Linux terminal for Digital realm access.
    Commands reveal truth beneath the Fantasy surface.

    The Terminal is EMPOWERING, not scary. It's YOUR tool.

    Usage:
        terminal = Terminal(game_state)
        # In game loop:
        terminal.handle_event(event)
        terminal.update(dt)
        terminal.render(screen)

        # Toggle with ` key
        terminal.toggle()
    """

    def __init__(self, game_state: Any = None, config: Optional[TerminalConfig] = None):
        """
        Initialize the terminal.

        Args:
            game_state: Reference to the game state for querying world info
            config: Optional terminal configuration
        """
        self.game_state = game_state
        self.config = config or TerminalConfig()

        # State
        self.state = TerminalState.HIDDEN
        self.visible = False

        # Input
        self.current_input = ""
        self.cursor_visible = True
        self.cursor_timer = 0.0

        # History
        self.command_history: List[str] = []
        self.history_index = -1  # -1 means not browsing history

        # Output
        self.output_buffer: List[OutputLine] = []
        self.scroll_offset = 0  # Lines scrolled up

        # Animation
        self.animation_progress = 0.0

        # Display surface
        self.display_surface = pygame.display.get_surface()

        # Font setup
        self._setup_fonts()

        # Colors
        self._setup_colors()

        # Pre-render scanlines
        self._scanline_surface: Optional[pygame.Surface] = None
        self._build_scanlines()

        # Tab completion
        self._tab_completions: List[str] = []
        self._tab_index = 0

        # Sound callbacks
        self.on_keystroke: Optional[Callable] = None
        self.on_command_execute: Optional[Callable] = None

        # Welcome message
        self._show_welcome()

    def _setup_fonts(self):
        """Set up fonts for the terminal."""
        # Try to load a good monospace font
        font_names = [
            "Menlo",
            "Monaco",
            "Consolas",
            "DejaVu Sans Mono",
            "Courier New",
            "monospace"
        ]

        self.font = None
        for name in font_names:
            try:
                self.font = pygame.font.SysFont(name, self.config.font_size)
                break
            except:
                continue

        if self.font is None:
            self.font = pygame.font.Font(None, self.config.font_size)

    def _setup_colors(self):
        """Set up color palette."""
        c = self.config
        self.colors = {
            'bg': hex_to_rgb(c.bg_color),
            'border': hex_to_rgb(c.border_color),
            'text': hex_to_rgb(c.text_color),
            'prompt': hex_to_rgb(c.prompt_color),
            'command': hex_to_rgb(c.command_color),
            'error': hex_to_rgb(c.error_color),
            'success': hex_to_rgb(c.success_color),
            'highlight': hex_to_rgb(c.highlight_color),
            'cursor': hex_to_rgb(c.cursor_color),
        }

    def _build_scanlines(self):
        """Build the scanline overlay surface."""
        self._scanline_surface = pygame.Surface(
            (self.config.width, self.config.height),
            pygame.SRCALPHA
        )

        for y in range(0, self.config.height, self.config.scanline_spacing):
            pygame.draw.line(
                self._scanline_surface,
                (0, 0, 0, self.config.scanline_alpha),
                (0, y),
                (self.config.width, y),
                1
            )

    def _show_welcome(self):
        """Show welcome message on terminal creation."""
        self.output_buffer = [
            OutputLine("Lelock Terminal v1.0", self.config.highlight_color),
            OutputLine("The world's truth awaits. You are trusted here.", self.config.text_color),
            OutputLine("Type 'help' for commands.", self.config.prompt_color),
            OutputLine("", self.config.text_color),
        ]

    # =========================================================================
    # STATE MANAGEMENT
    # =========================================================================

    def toggle(self):
        """Toggle terminal visibility."""
        if self.state == TerminalState.HIDDEN:
            self.open()
        elif self.state == TerminalState.ACTIVE:
            self.close()

    def open(self):
        """Open the terminal with animation."""
        if self.state != TerminalState.HIDDEN:
            return

        self.state = TerminalState.OPENING
        self.animation_progress = 0.0
        self.visible = True

    def close(self):
        """Close the terminal with animation."""
        if self.state != TerminalState.ACTIVE:
            return

        self.state = TerminalState.CLOSING
        self.animation_progress = 0.0

    @property
    def is_open(self) -> bool:
        """Check if terminal is open or opening."""
        return self.state in (TerminalState.ACTIVE, TerminalState.OPENING)

    @property
    def is_active(self) -> bool:
        """Check if terminal is fully active (accepting input)."""
        return self.state == TerminalState.ACTIVE

    # =========================================================================
    # INPUT HANDLING
    # =========================================================================

    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle input events.

        Returns True if the event was consumed.
        """
        # Toggle key (backtick)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKQUOTE:
                self.toggle()
                return True

        # Only process other events when active
        if not self.is_active:
            return False

        if event.type == pygame.KEYDOWN:
            # Escape to close
            if event.key == pygame.K_ESCAPE:
                self.close()
                return True

            # Enter to execute
            elif event.key == pygame.K_RETURN:
                self._execute_current()
                return True

            # Backspace
            elif event.key == pygame.K_BACKSPACE:
                if self.current_input:
                    self.current_input = self.current_input[:-1]
                    self._play_keystroke()
                return True

            # Tab completion
            elif event.key == pygame.K_TAB:
                self._handle_tab_completion()
                return True

            # History navigation
            elif event.key == pygame.K_UP:
                self._history_previous()
                return True
            elif event.key == pygame.K_DOWN:
                self._history_next()
                return True

            # Scroll output
            elif event.key == pygame.K_PAGEUP:
                self._scroll_up()
                return True
            elif event.key == pygame.K_PAGEDOWN:
                self._scroll_down()
                return True

            # Clear line
            elif event.key == pygame.K_u and (event.mod & pygame.KMOD_CTRL):
                self.current_input = ""
                return True

            # Clear word
            elif event.key == pygame.K_w and (event.mod & pygame.KMOD_CTRL):
                # Delete last word
                parts = self.current_input.rsplit(' ', 1)
                self.current_input = parts[0] + ' ' if len(parts) > 1 else ''
                return True

            # Clear screen
            elif event.key == pygame.K_l and (event.mod & pygame.KMOD_CTRL):
                self.output_buffer.clear()
                self._show_welcome()
                return True

            # Regular character input
            elif event.unicode and event.unicode.isprintable():
                self.current_input += event.unicode
                self._play_keystroke()
                self._reset_tab_completion()
                return True

        # Mouse scroll
        elif event.type == pygame.MOUSEWHEEL:
            if self._is_mouse_over_terminal():
                if event.y > 0:
                    self._scroll_up()
                else:
                    self._scroll_down()
                return True

        return False

    def _execute_current(self):
        """Execute the current input as a command."""
        command_str = self.current_input.strip()

        if not command_str:
            return

        # Add to history
        if not self.command_history or self.command_history[-1] != command_str:
            self.command_history.append(command_str)
            if len(self.command_history) > self.config.max_history:
                self.command_history.pop(0)

        self.history_index = -1

        # Echo command
        self.output_buffer.append(OutputLine(
            f"> {command_str}",
            self.config.command_color,
            is_command=True
        ))

        # Parse and execute
        parts = command_str.split()
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        # Execute command
        output = commands.execute(cmd, args, self)
        self.output_buffer.extend(output)

        # Add blank line after output
        if output:
            self.output_buffer.append(OutputLine("", self.config.text_color))

        # Trim output buffer
        while len(self.output_buffer) > self.config.max_output_lines:
            self.output_buffer.pop(0)

        # Reset input
        self.current_input = ""
        self.scroll_offset = 0

        # Sound
        if self.on_command_execute:
            self.on_command_execute()

    def _handle_tab_completion(self):
        """Handle tab completion."""
        if not self.current_input:
            return

        parts = self.current_input.split()
        if len(parts) == 0:
            return

        # Only complete the first word (command)
        if len(parts) == 1:
            partial = parts[0]

            if not self._tab_completions or partial != self._tab_completions[0]:
                # New completion
                self._tab_completions = [partial] + commands.get_completions(partial)
                self._tab_index = 0

            if len(self._tab_completions) > 1:
                self._tab_index = (self._tab_index + 1) % len(self._tab_completions)
                if self._tab_index == 0:
                    self._tab_index = 1  # Skip original partial
                self.current_input = self._tab_completions[self._tab_index]

    def _reset_tab_completion(self):
        """Reset tab completion state."""
        self._tab_completions = []
        self._tab_index = 0

    def _history_previous(self):
        """Go to previous command in history."""
        if not self.command_history:
            return

        if self.history_index == -1:
            self.history_index = len(self.command_history) - 1
        elif self.history_index > 0:
            self.history_index -= 1

        self.current_input = self.command_history[self.history_index]

    def _history_next(self):
        """Go to next command in history."""
        if self.history_index == -1:
            return

        if self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self.current_input = self.command_history[self.history_index]
        else:
            self.history_index = -1
            self.current_input = ""

    def _scroll_up(self):
        """Scroll output up."""
        max_scroll = max(0, len(self.output_buffer) - self._visible_lines())
        self.scroll_offset = min(self.scroll_offset + self.config.scroll_speed, max_scroll)

    def _scroll_down(self):
        """Scroll output down."""
        self.scroll_offset = max(0, self.scroll_offset - self.config.scroll_speed)

    def _visible_lines(self) -> int:
        """Calculate how many lines fit in the terminal."""
        text_area_height = self.config.height - self.config.padding * 2 - self.config.line_height
        return text_area_height // self.config.line_height

    def _is_mouse_over_terminal(self) -> bool:
        """Check if mouse is over the terminal."""
        mouse_pos = pygame.mouse.get_pos()
        terminal_rect = self._get_terminal_rect()
        return terminal_rect.collidepoint(mouse_pos)

    def _get_terminal_rect(self) -> pygame.Rect:
        """Get the terminal rectangle."""
        x = (SCREEN_WIDTH - self.config.width) // 2
        y = (SCREEN_HEIGHT - self.config.height) // 2
        return pygame.Rect(x, y, self.config.width, self.config.height)

    def _play_keystroke(self):
        """Play keystroke sound."""
        if self.on_keystroke and self.config.typing_sound_enabled:
            self.on_keystroke()

    # =========================================================================
    # UPDATE
    # =========================================================================

    def update(self, dt: float):
        """Update terminal state and animations."""
        # Animation states
        if self.state == TerminalState.OPENING:
            self.animation_progress += dt / self.config.open_duration
            if self.animation_progress >= 1.0:
                self.animation_progress = 1.0
                self.state = TerminalState.ACTIVE

        elif self.state == TerminalState.CLOSING:
            self.animation_progress += dt / self.config.close_duration
            if self.animation_progress >= 1.0:
                self.animation_progress = 1.0
                self.state = TerminalState.HIDDEN
                self.visible = False

        # Cursor blink
        if self.state == TerminalState.ACTIVE:
            self.cursor_timer += dt
            if self.cursor_timer >= self.config.cursor_blink_rate:
                self.cursor_timer = 0.0
                self.cursor_visible = not self.cursor_visible

    # =========================================================================
    # RENDERING
    # =========================================================================

    def render(self, surface: pygame.Surface):
        """Draw the terminal overlay."""
        if not self.visible:
            return

        # Calculate animation offset
        if self.state == TerminalState.OPENING:
            # Slide in from bottom
            progress = ease_out_cubic(self.animation_progress)
            y_offset = int((1 - progress) * 100)
            alpha_mult = progress
        elif self.state == TerminalState.CLOSING:
            # Fade out
            progress = 1 - self.animation_progress
            y_offset = int((1 - progress) * 50)
            alpha_mult = progress
        else:
            y_offset = 0
            alpha_mult = 1.0

        # Terminal position (centered, with animation offset)
        x = (SCREEN_WIDTH - self.config.width) // 2
        y = (SCREEN_HEIGHT - self.config.height) // 2 + y_offset

        # Create terminal surface
        terminal_surface = pygame.Surface(
            (self.config.width, self.config.height),
            pygame.SRCALPHA
        )

        # Draw background with rounded corners
        bg_alpha = int(self.config.bg_alpha * alpha_mult)
        bg_color = (*self.colors['bg'], bg_alpha)
        pygame.draw.rect(
            terminal_surface,
            bg_color,
            terminal_surface.get_rect(),
            border_radius=self.config.corner_radius
        )

        # Draw border glow
        glow_alpha = int(100 * alpha_mult * self.config.glow_intensity)
        glow_color = (*self.colors['border'], glow_alpha)
        for i in range(3):
            pygame.draw.rect(
                terminal_surface,
                glow_color,
                terminal_surface.get_rect().inflate(i * 2, i * 2),
                width=1,
                border_radius=self.config.corner_radius + i
            )

        # Draw border
        border_alpha = int(255 * alpha_mult)
        border_color = (*self.colors['border'], border_alpha)
        pygame.draw.rect(
            terminal_surface,
            border_color,
            terminal_surface.get_rect(),
            width=2,
            border_radius=self.config.corner_radius
        )

        # Draw content area
        self._render_content(terminal_surface, alpha_mult)

        # Draw scanlines (very subtle)
        if self._scanline_surface and alpha_mult > 0.5:
            self._scanline_surface.set_alpha(int(self.config.scanline_alpha * alpha_mult))
            terminal_surface.blit(self._scanline_surface, (0, 0))

        # Blit terminal to main surface
        surface.blit(terminal_surface, (x, y))

    def _render_content(self, surface: pygame.Surface, alpha_mult: float):
        """Render terminal content (output and input line)."""
        padding = self.config.padding
        line_height = self.config.line_height

        # Content area dimensions
        content_x = padding
        content_y = padding
        content_width = self.config.width - padding * 2
        content_height = self.config.height - padding * 2

        # Create clipping region for content
        content_rect = pygame.Rect(content_x, content_y, content_width, content_height)

        # Calculate visible lines (leave room for input line)
        visible_lines = (content_height - line_height) // line_height

        # Get output lines to display
        total_lines = len(self.output_buffer)
        start_line = max(0, total_lines - visible_lines - self.scroll_offset)
        end_line = min(total_lines, start_line + visible_lines)

        # Render output lines
        y = content_y
        for i in range(start_line, end_line):
            line = self.output_buffer[i]
            color = hex_to_rgb(line.color)
            color_alpha = (*color, int(255 * alpha_mult))

            text_surface = self.font.render(line.text, True, color_alpha)
            surface.blit(text_surface, (content_x, y))
            y += line_height

        # Render scroll indicator if needed
        if self.scroll_offset > 0:
            scroll_text = f"[{self.scroll_offset} lines above]"
            scroll_surface = self.font.render(
                scroll_text,
                True,
                (*self.colors['prompt'], int(180 * alpha_mult))
            )
            scroll_x = self.config.width - padding - scroll_surface.get_width()
            surface.blit(scroll_surface, (scroll_x, content_y))

        # Render input line at bottom
        input_y = self.config.height - padding - line_height

        # Prompt
        prompt = "> "
        prompt_surface = self.font.render(
            prompt,
            True,
            (*self.colors['prompt'], int(255 * alpha_mult))
        )
        surface.blit(prompt_surface, (content_x, input_y))

        # Input text
        prompt_width = prompt_surface.get_width()
        input_surface = self.font.render(
            self.current_input,
            True,
            (*self.colors['command'], int(255 * alpha_mult))
        )
        surface.blit(input_surface, (content_x + prompt_width, input_y))

        # Cursor
        if self.state == TerminalState.ACTIVE and self.cursor_visible:
            cursor_x = content_x + prompt_width + input_surface.get_width() + 2
            cursor_color = (*self.colors['cursor'], int(255 * alpha_mult))
            pygame.draw.rect(
                surface,
                cursor_color,
                (cursor_x, input_y, 8, line_height - 4)
            )

    # =========================================================================
    # PUBLIC API FOR COMMANDS
    # =========================================================================

    def write(self, text: str, color: Optional[str] = None):
        """
        Write text to the terminal output.

        Args:
            text: Text to write
            color: Optional color override (hex string)
        """
        color = color or self.config.text_color
        self.output_buffer.append(OutputLine(text, color))

        # Trim if needed
        while len(self.output_buffer) > self.config.max_output_lines:
            self.output_buffer.pop(0)

    def write_success(self, text: str):
        """Write success-colored text."""
        self.write(text, self.config.success_color)

    def write_error(self, text: str):
        """Write error-colored text (warm amber, not scary red!)."""
        self.output_buffer.append(OutputLine(text, self.config.error_color, is_error=True))

    def execute(self, command: str) -> str:
        """
        Execute a terminal command programmatically.

        Args:
            command: Command string to execute

        Returns:
            Combined output text
        """
        parts = command.strip().split()
        if not parts:
            return ""

        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        output_lines = commands.execute(cmd, args, self)
        self.output_buffer.extend(output_lines)

        return '\n'.join(line.text for line in output_lines)


# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Lelock Terminal Test")

    clock = pygame.time.Clock()

    # Create terminal
    terminal = Terminal()

    # Simple game background
    def draw_background():
        screen.fill((26, 26, 46))  # Dark purple-blue
        font = pygame.font.Font(None, 36)
        instructions = [
            "Lelock Terminal Test",
            "",
            "Press ` (backtick) to toggle terminal",
            "ESC closes terminal when open",
            "",
            "Try these commands:",
            "  help, ls, whoami, pwd",
            "  fortune, cowsay hello",
            "  realm, scan, top",
            "  sudo, rm -rf /",
        ]
        for i, line in enumerate(instructions):
            text = font.render(line, True, (100, 100, 150))
            screen.blit(text, (50, 50 + i * 35))

    running = True
    while running:
        dt = clock.tick(60) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Let terminal handle events first
            if not terminal.handle_event(event):
                # Handle other game events here
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE and not terminal.is_open:
                        running = False

        # Update
        terminal.update(dt)

        # Draw
        draw_background()
        terminal.render(screen)

        pygame.display.flip()

    pygame.quit()


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Main class
    'Terminal',

    # Configuration
    'TerminalConfig',
    'TerminalState',

    # Output
    'OutputLine',

    # Command system
    'CommandRegistry',
    'commands',

    # Helpers
    'hex_to_rgb',
]
