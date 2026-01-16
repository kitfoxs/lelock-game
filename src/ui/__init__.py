"""
Lelock UI Module
Warm, cozy, friend-shaped interfaces for the digital sanctuary

All UI follows the "Bouba" aesthetic:
- Rounded corners everywhere
- Soft, semi-transparent backgrounds
- Warm color palette (2700K-3000K feel)
- No red warnings (use orange instead)
- Gentle hover effects (glow, not snap)

"In Lelock, every interface feels like a warm hug."
"""

from .hud import HUD
from .menu import Button, PauseMenu, TitleMenu, SettingsMenu
from .dialogue_box import (
    DialogueBox,
    DialogueConfig,
    DialogueState,
    PortraitFrame,
    NamePlate,
    TypewriterText,
    InputField,
    ThinkingIndicator,
    ContinueIndicator,
)
from .terminal import (
    Terminal,
    TerminalConfig,
    TerminalState,
    OutputLine,
    CommandRegistry,
    commands,
)

__all__ = [
    # HUD
    'HUD',

    # Menu system
    'Button',
    'PauseMenu',
    'TitleMenu',
    'SettingsMenu',

    # Dialogue system
    'DialogueBox',
    'DialogueConfig',
    'DialogueState',
    'PortraitFrame',
    'NamePlate',
    'TypewriterText',
    'InputField',
    'ThinkingIndicator',
    'ContinueIndicator',

    # Terminal (Digital realm access)
    'Terminal',
    'TerminalConfig',
    'TerminalState',
    'OutputLine',
    'CommandRegistry',
    'commands',
]
