"""
Lelock Game Engine
==================
The heart of the sanctuary.

This module contains the main Game class that orchestrates all game systems.
Every frame, every input, every gentle transition flows through here.

Safety Principles:
- No sudden audio spikes
- All transitions are gradual
- Escape opens pause menu (never quits abruptly)
- Warm colors always (#1a1a2e, never harsh black)

Created by Kit & Ada Marie
"""

import pygame
import sys
from enum import Enum, auto
from typing import Optional, Callable
from dataclasses import dataclass, field

from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_TITLE, FPS, VERSION,
    COLORS, AUDIO_CONFIG
)


class GameState(Enum):
    """
    Game states for proper flow control.

    The world of Lelock has different modes of being,
    each one gentle in its own way.
    """
    MENU = auto()       # Title screen - where journeys begin
    PLAYING = auto()    # Main gameplay - exploring the sanctuary
    PAUSED = auto()     # Pause menu overlay - rest when needed
    DIALOGUE = auto()   # NPC conversation - the world waits for you
    SLEEPING = auto()   # Bedtime transition - dreams await
    TRANSITION = auto() # Between areas - smooth fades only


@dataclass
class TransitionState:
    """
    Manages smooth transitions between states.
    No jarring cuts - everything fades gently.
    """
    active: bool = False
    alpha: float = 0.0
    direction: str = 'in'  # 'in' = fading to black, 'out' = fading from black
    speed: float = 300.0   # Alpha change per second (0-255 in ~0.85 seconds)
    callback: Optional[Callable] = None

    def update(self, dt: float) -> bool:
        """
        Update transition alpha. Returns True when complete.
        """
        if not self.active:
            return True

        if self.direction == 'in':
            self.alpha = min(255, self.alpha + self.speed * dt)
            if self.alpha >= 255:
                return True
        else:  # out
            self.alpha = max(0, self.alpha - self.speed * dt)
            if self.alpha <= 0:
                return True
        return False


class Game:
    """
    Main game class for Lelock.

    In Lelock, you cannot fail. You can only rest and try again.
    MOM will always have soup waiting.

    This class manages:
    - Game loop (60 FPS, delta time based)
    - State transitions (menu -> playing -> paused, etc.)
    - Event routing to appropriate handlers
    - Clean startup and shutdown
    """

    def __init__(self):
        """Initialize the sanctuary."""
        # Initialize pygame with safety settings
        pygame.init()
        pygame.mixer.init()

        # Set audio to safe levels immediately
        pygame.mixer.set_num_channels(16)

        # Display setup - the window to our world
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(f'{WINDOW_TITLE} v{VERSION}')
        self.clock = pygame.time.Clock()

        # Core state
        self.running = True
        self.state = GameState.MENU
        self.previous_state: Optional[GameState] = None

        # Transition system (all transitions are gentle)
        self.transition = TransitionState()

        # Realm tracking (Physical World vs Digital World)
        self.current_realm = 'physical'  # 'physical' or 'digital'
        self.digital_world = None  # Initialized when level is set

        # Delta time tracking
        self.dt = 0.0
        self.total_time = 0.0

        # Input state (for held keys vs pressed keys)
        self.keys_pressed: set = set()
        self.keys_just_pressed: set = set()
        self.keys_just_released: set = set()

        # Systems (initialized by their respective modules)
        self.level = None
        self.player = None
        self.dialogue_manager = None
        self.menu_manager = None

        # AI Systems (initialized separately)
        self.llm = None
        self.memory = None

        # Debug mode (F3 to toggle)
        self.debug_mode = False

        # Error state for displaying issues
        self.error_message = None

        # Fonts for UI
        self._init_fonts()

        # Surface for transitions
        self.transition_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.transition_surface.fill(self._parse_color(COLORS['background']))

        self._startup_message()

    def _init_fonts(self):
        """Initialize fonts for the game."""
        pygame.font.init()
        self.fonts = {
            'title': pygame.font.Font(None, 72),
            'heading': pygame.font.Font(None, 48),
            'body': pygame.font.Font(None, 32),
            'small': pygame.font.Font(None, 24),
        }

    def _parse_color(self, color_str: str) -> tuple:
        """
        Parse a hex color string to RGB tuple.
        Safety: Always returns a valid color.
        """
        try:
            if color_str.startswith('#'):
                color_str = color_str[1:]
            return tuple(int(color_str[i:i+2], 16) for i in (0, 2, 4))
        except (ValueError, IndexError):
            return (26, 26, 46)  # Fallback to warm dark blue

    def _startup_message(self):
        """Print a warm welcome message."""
        print()
        print("=" * 50)
        print("  L.E.L.O.C.K.")
        print("  Life Emulation & Lucid Observation")
        print("  for Care & Keeping")
        print("=" * 50)
        print()
        print("  Welcome home, little one.")
        print("  The world is here to save you.")
        print()

    # =========================================================================
    # STATE MANAGEMENT
    # =========================================================================

    def change_state(self, new_state: GameState, with_transition: bool = True):
        """
        Change game state with optional transition.

        All state changes are logged and gentle.
        """
        if new_state == self.state:
            return

        self.previous_state = self.state

        if with_transition:
            # Start fade out, then change state, then fade in
            self.transition.active = True
            self.transition.direction = 'in'
            self.transition.alpha = 0
            self.transition.callback = lambda: self._complete_state_change(new_state)
        else:
            self._complete_state_change(new_state)

    def _complete_state_change(self, new_state: GameState):
        """Complete the state change after transition."""
        old_state = self.state
        self.state = new_state

        # Initialize systems for new state
        if new_state == GameState.PLAYING and self.level is None:
            self._start_new_game()

        # Start fade back in
        self.transition.direction = 'out'
        self.transition.alpha = 255
        self.transition.callback = lambda: setattr(self.transition, 'active', False)

        if self.debug_mode:
            print(f"[State] {old_state.name} -> {new_state.name}")

    def _start_new_game(self):
        """Initialize a new game - load level, create player, etc."""
        from world.level import Level
        from entities.player import Player
        from world.digital import DigitalWorld
        import os

        # Load the Oakhaven map
        # Try multiple possible paths
        possible_paths = [
            'assets/maps/map.tmx',
            os.path.join(os.path.dirname(__file__), 'assets/maps/map.tmx'),
            os.path.join(os.path.dirname(__file__), '..', 'assets/maps/map.tmx'),
        ]

        map_path = None
        for path in possible_paths:
            if os.path.exists(path):
                map_path = path
                break

        try:
            # Create level (with or without map)
            if map_path:
                self.level = Level(map_path)
                print(f"[Game] Level loaded from: {map_path}")
            else:
                # Create empty level for testing
                self.level = Level()
                # Set some default dimensions
                self.level.map_width = 1024
                self.level.map_height = 768
                self.level.all_sprites.set_map_bounds(1024, 768)
                print("[Game] No map found - created empty level for testing")
                print(f"[Game] Searched paths: {possible_paths}")

            # Get spawn position from map, or use center
            spawn_pos = self.level.get_player_spawn()
            print(f"[Game] Player spawn position: {spawn_pos}")

            # Create player with proper sprite groups
            # Player needs: pos, groups, collision_sprites, interaction_sprites
            self.player = Player(
                pos=spawn_pos,
                groups=self.level.all_sprites,
                collision_sprites=self.level.collision_sprites,
                interaction_sprites=self.level.interaction_sprites
            )

            # Register player with level (this also adds to sprite groups and snaps camera)
            self.level.set_player(self.player)
            print(f"[Game] Player created at {spawn_pos}")

            # Initialize Digital World overlay
            self.digital_world = DigitalWorld(self.level)
            print("[Game] Digital World overlay ready!")

        except Exception as e:
            print(f"[Game] ERROR loading level: {e}")
            import traceback
            traceback.print_exc()

            # Show error on screen by setting error state
            self._show_error(f"Failed to load level: {e}")

    def _show_error(self, message: str):
        """
        Store an error message to be displayed on screen.
        Errors are visible to help debugging.
        """
        self.error_message = message
        print(f"[Game] ERROR: {message}")

    def push_state(self, overlay_state: GameState):
        """
        Push an overlay state (like PAUSED or DIALOGUE).
        The world beneath continues to exist, just frozen.
        """
        self.previous_state = self.state
        self.state = overlay_state

        if self.debug_mode:
            print(f"[State] Pushed {overlay_state.name} over {self.previous_state.name}")

    def pop_state(self):
        """
        Return to the previous state.
        Like waking from a gentle pause.
        """
        if self.previous_state:
            old_state = self.state
            self.state = self.previous_state
            self.previous_state = None

            if self.debug_mode:
                print(f"[State] Popped {old_state.name}, returned to {self.state.name}")

    # =========================================================================
    # EVENT HANDLING
    # =========================================================================

    def handle_events(self):
        """
        Process all input events.

        Routes events to the appropriate handler based on game state.
        Escape ALWAYS opens pause menu, never quits abruptly.
        """
        # Clear per-frame input tracking
        self.keys_just_pressed.clear()
        self.keys_just_released.clear()

        for event in pygame.event.get():
            # Window close button
            if event.type == pygame.QUIT:
                self._request_quit()
                return

            # Key events
            if event.type == pygame.KEYDOWN:
                self.keys_pressed.add(event.key)
                self.keys_just_pressed.add(event.key)
                self._handle_key_down(event.key)

            elif event.type == pygame.KEYUP:
                self.keys_pressed.discard(event.key)
                self.keys_just_released.add(event.key)

            # Mouse events (for UI interactions)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_mouse_down(event.pos, event.button)

    def _handle_key_down(self, key: int):
        """
        Handle a key press event.

        Global keys work in any state.
        Other keys are routed to state-specific handlers.
        """
        # Global: F3 toggles debug mode
        if key == pygame.K_F3:
            self.debug_mode = not self.debug_mode
            print(f"[Debug] {'Enabled' if self.debug_mode else 'Disabled'}")
            return

        # Global: Escape behavior (context-dependent, never quits)
        if key == pygame.K_ESCAPE:
            self._handle_escape()
            return

        # State-specific handling
        if self.state == GameState.MENU:
            self._handle_menu_input(key)
        elif self.state == GameState.PLAYING:
            self._handle_playing_input(key)
        elif self.state == GameState.PAUSED:
            self._handle_paused_input(key)
        elif self.state == GameState.DIALOGUE:
            self._handle_dialogue_input(key)

    def _handle_escape(self):
        """
        Handle the escape key - context dependent, always gentle.

        - MENU: Does nothing (stay on menu)
        - PLAYING: Opens pause menu
        - PAUSED: Closes pause menu
        - DIALOGUE: Continues/closes dialogue
        - SLEEPING: Cannot be interrupted
        """
        if self.state == GameState.MENU:
            # On menu, escape does nothing (no accidental quits!)
            pass
        elif self.state == GameState.PLAYING:
            # Open pause menu
            self.push_state(GameState.PAUSED)
        elif self.state == GameState.PAUSED:
            # Return to game
            self.pop_state()
        elif self.state == GameState.DIALOGUE:
            # Advance/close dialogue
            if self.dialogue_manager:
                self.dialogue_manager.advance()
            else:
                self.pop_state()
        # SLEEPING cannot be interrupted - dreams must complete

    def _handle_menu_input(self, key: int):
        """Handle input on the menu screen."""
        if key in (pygame.K_RETURN, pygame.K_SPACE):
            # Start the game!
            self.change_state(GameState.PLAYING)

    def _handle_playing_input(self, key: int):
        """Handle input during gameplay."""
        # Player movement handled via keys_pressed in update
        # This is for single-press actions

        if key == pygame.K_e:
            # Interact key
            pass  # TODO: Trigger interaction

        if key == pygame.K_i:
            # Inventory
            pass  # TODO: Open inventory

        if key == pygame.K_TAB:
            # Toggle Digital/Physical realm (Vision Goggles)
            self._toggle_realm_view()

    def _handle_paused_input(self, key: int):
        """Handle input in pause menu."""
        if key == pygame.K_q:
            # Quit from pause menu (with confirmation in future)
            self._request_quit()

    def _handle_dialogue_input(self, key: int):
        """Handle input during NPC dialogue."""
        if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
            # Advance dialogue
            if self.dialogue_manager:
                self.dialogue_manager.advance()

    def _handle_mouse_down(self, pos: tuple, button: int):
        """Handle mouse click events."""
        # TODO: Route to UI elements
        pass

    def _request_quit(self):
        """
        Request to quit the game.
        Always with a gentle goodbye.
        """
        self.running = False

    def _toggle_realm_view(self):
        """
        Toggle between Physical and Digital realm visualization.

        Triggered by TAB key or using Vision Goggles item.
        Smooth 2-3 second transition - calming, not jarring.
        """
        if self.digital_world:
            self.digital_world.toggle_realm()

            if self.debug_mode:
                current = self.digital_world.get_realm_name()
                print(f"[Realm] Transitioning... ({current})")

    def set_level(self, level):
        """
        Set the current level and initialize associated systems.

        Creates the Digital World overlay for this level.

        Args:
            level: The Level instance
        """
        from world.digital import DigitalWorld

        self.level = level

        # Create Digital World overlay for this level
        self.digital_world = DigitalWorld(level)

        # Register audio callback for realm transitions (if audio system exists)
        # self.digital_world.register_audio_callback(self._on_realm_transition)

    def _on_realm_transition(self, progress: float):
        """
        Callback for realm transition progress.

        Handles audio crossfade between Physical (acoustic) and Digital (lo-fi).

        Args:
            progress: 0 = fully physical, 1 = fully digital
        """
        # TODO: Implement audio crossfade
        # self.audio.set_realm_mix(progress)
        pass

    # =========================================================================
    # UPDATE LOGIC
    # =========================================================================

    def update(self):
        """
        Update all game systems.

        Called once per frame with delta time already calculated.
        Only updates systems relevant to current state.
        """
        # Always update transitions
        if self.transition.active:
            if self.transition.update(self.dt):
                if self.transition.callback:
                    self.transition.callback()

        # State-specific updates
        if self.state == GameState.MENU:
            self._update_menu()
        elif self.state == GameState.PLAYING:
            self._update_playing()
        elif self.state == GameState.PAUSED:
            self._update_paused()
        elif self.state == GameState.DIALOGUE:
            self._update_dialogue()
        elif self.state == GameState.SLEEPING:
            self._update_sleeping()

    def _update_menu(self):
        """Update menu screen."""
        # Menu animations, particle effects, etc.
        pass

    def _update_playing(self):
        """Update gameplay state."""
        # Note: Level.run() handles its own updates when called in render
        # We only update separate systems here

        # Update Digital World overlay
        if self.digital_world:
            self.digital_world.update(self.dt)
            # Sync realm state
            if self.digital_world.is_digital:
                self.current_realm = 'digital'
            elif self.digital_world.is_physical:
                self.current_realm = 'physical'

        # Player input is continuous (movement)
        self._update_player_movement()

    def _update_player_movement(self):
        """Handle continuous player movement input."""
        if not self.player:
            return

        # Movement handled by player module
        # Just pass the held keys
        direction = pygame.math.Vector2(0, 0)

        if pygame.K_w in self.keys_pressed or pygame.K_UP in self.keys_pressed:
            direction.y = -1
        if pygame.K_s in self.keys_pressed or pygame.K_DOWN in self.keys_pressed:
            direction.y = 1
        if pygame.K_a in self.keys_pressed or pygame.K_LEFT in self.keys_pressed:
            direction.x = -1
        if pygame.K_d in self.keys_pressed or pygame.K_RIGHT in self.keys_pressed:
            direction.x = 1

        # Normalize diagonal movement
        if direction.magnitude() > 0:
            direction = direction.normalize()

        # Player will use this (to be implemented)
        # self.player.move(direction, self.dt)

    def _update_paused(self):
        """Update pause menu."""
        # Pause menu animations if any
        pass

    def _update_dialogue(self):
        """Update dialogue state."""
        # World is frozen, only dialogue system updates
        if self.dialogue_manager:
            self.dialogue_manager.update(self.dt)

    def _update_sleeping(self):
        """Update sleep transition."""
        # Handle the bedtime transition
        # When complete, reset to next day
        pass

    # =========================================================================
    # RENDERING
    # =========================================================================

    def render(self):
        """
        Render all game elements to screen.

        Always starts with warm background color.
        Never harsh black - we use #1a1a2e.
        """
        # Warm background (never harsh black!)
        bg_color = self._parse_color(COLORS['background'])
        self.screen.fill(bg_color)

        # State-specific rendering
        if self.state == GameState.MENU:
            self._render_menu()
        elif self.state == GameState.PLAYING:
            self._render_playing()
        elif self.state == GameState.PAUSED:
            self._render_playing()  # Render game underneath
            self._render_pause_overlay()
        elif self.state == GameState.DIALOGUE:
            self._render_playing()  # World still visible
            self._render_dialogue()
        elif self.state == GameState.SLEEPING:
            self._render_sleeping()

        # Render transition overlay if active
        if self.transition.active:
            self._render_transition()

        # Debug overlay
        if self.debug_mode:
            self._render_debug()

        # Flip the display
        pygame.display.flip()

    def _render_menu(self):
        """Render the title/menu screen."""
        # Title
        title_color = self._parse_color(COLORS['ui_highlight'])
        title = self.fonts['title'].render("LELOCK", True, title_color)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
        self.screen.blit(title, title_rect)

        # Tagline
        tag_color = self._parse_color(COLORS['ui_text'])
        tagline = self.fonts['body'].render(
            "The world is here to save you.", True, tag_color
        )
        tag_rect = tagline.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3 + 60))
        self.screen.blit(tagline, tag_rect)

        # Start prompt (pulsing would be nice)
        prompt_color = (180, 180, 180)
        prompt = self.fonts['body'].render(
            "Press ENTER or SPACE to begin", True, prompt_color
        )
        prompt_rect = prompt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT * 2 // 3))
        self.screen.blit(prompt, prompt_rect)

        # Version
        version_color = (100, 100, 100)
        version = self.fonts['small'].render(f"v{VERSION}", True, version_color)
        version_rect = version.get_rect(bottomright=(SCREEN_WIDTH - 10, SCREEN_HEIGHT - 10))
        self.screen.blit(version, version_rect)

    def _render_playing(self):
        """Render the main gameplay."""
        # Show any errors first
        if self.error_message:
            self._render_error()
            return

        if self.level and self.player:
            # Level.run() handles update and render together
            # Pass actual dt for smooth animations
            self.level.run(self.dt)

            # Apply Digital World overlay (if transitioning or in digital realm)
            if self.digital_world and self.digital_world.transition_progress > 0:
                self.digital_world.render(self.screen)

            # Debug: Show player position
            if self.debug_mode:
                pos_text = self.fonts['small'].render(
                    f"Player: ({self.player.rect.centerx}, {self.player.rect.centery})",
                    True, (0, 255, 0)
                )
                self.screen.blit(pos_text, (10, 100))
        else:
            # Placeholder until level is implemented
            text_color = self._parse_color(COLORS['ui_text'])

            if self.level is None:
                message = "Loading level..."
            elif self.player is None:
                message = "Creating player..."
            else:
                message = "Oakhaven awaits..."

            text = self.fonts['heading'].render(message, True, text_color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(text, text_rect)

            hint = self.fonts['small'].render(
                "Press ESC to pause | TAB to toggle realm", True, (100, 100, 100)
            )
            hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
            self.screen.blit(hint, hint_rect)

            # If no level but digital world exists, still show the overlay effects
            if self.digital_world and self.digital_world.transition_progress > 0:
                self.digital_world.render(self.screen)

    def _render_error(self):
        """Render error message on screen."""
        # Dark red background
        self.screen.fill((60, 20, 20))

        # Error title
        title = self.fonts['heading'].render("Error", True, (255, 100, 100))
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
        self.screen.blit(title, title_rect)

        # Error message (may need wrapping for long messages)
        if self.error_message:
            # Simple word wrap
            words = self.error_message.split()
            lines = []
            current_line = []
            for word in words:
                test_line = ' '.join(current_line + [word])
                if self.fonts['body'].size(test_line)[0] < SCREEN_WIDTH - 100:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]
            if current_line:
                lines.append(' '.join(current_line))

            y = SCREEN_HEIGHT // 2
            for line in lines[:5]:  # Max 5 lines
                text = self.fonts['body'].render(line, True, (255, 200, 200))
                text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, y))
                self.screen.blit(text, text_rect)
                y += 35

        # Hint to quit
        hint = self.fonts['small'].render(
            "Press ESC then Q to quit, or check console for details",
            True, (150, 150, 150)
        )
        hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT * 3 // 4))
        self.screen.blit(hint, hint_rect)

    def _render_pause_overlay(self):
        """Render pause menu over the game."""
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((26, 26, 46, 180))  # Warm dark with alpha
        self.screen.blit(overlay, (0, 0))

        # Pause text
        title_color = self._parse_color(COLORS['ui_highlight'])
        title = self.fonts['heading'].render("PAUSED", True, title_color)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
        self.screen.blit(title, title_rect)

        # Options
        text_color = self._parse_color(COLORS['ui_text'])
        resume = self.fonts['body'].render(
            "Press ESC to resume", True, text_color
        )
        resume_rect = resume.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(resume, resume_rect)

        quit_text = self.fonts['body'].render(
            "Press Q to quit", True, text_color
        )
        quit_rect = quit_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
        self.screen.blit(quit_text, quit_rect)

    def _render_dialogue(self):
        """Render dialogue box over the game."""
        if self.dialogue_manager:
            self.dialogue_manager.render(self.screen)
        else:
            # Placeholder dialogue box
            box_height = 150
            box_y = SCREEN_HEIGHT - box_height - 20

            # Box background
            pygame.draw.rect(
                self.screen,
                self._parse_color(COLORS['ui_bg']),
                (20, box_y, SCREEN_WIDTH - 40, box_height),
                border_radius=10
            )
            pygame.draw.rect(
                self.screen,
                self._parse_color(COLORS['ui_border']),
                (20, box_y, SCREEN_WIDTH - 40, box_height),
                width=3,
                border_radius=10
            )

            # Placeholder text
            text = self.fonts['body'].render(
                "Dialogue system ready...", True,
                self._parse_color(COLORS['ui_text'])
            )
            self.screen.blit(text, (40, box_y + 20))

    def _render_sleeping(self):
        """Render the sleep/bedtime transition."""
        # Fade to warm color, show "Sweet dreams..."
        # Then fade to black, reset day, fade back in
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((20, 15, 35))  # Deep sleep purple-blue
        self.screen.blit(overlay, (0, 0))

        text_color = (200, 200, 255)
        text = self.fonts['heading'].render(
            "Sweet dreams...", True, text_color
        )
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(text, text_rect)

    def _render_transition(self):
        """Render transition overlay."""
        self.transition_surface.set_alpha(int(self.transition.alpha))
        self.screen.blit(self.transition_surface, (0, 0))

    def _render_debug(self):
        """Render debug information overlay."""
        debug_lines = [
            f"FPS: {self.clock.get_fps():.1f}",
            f"State: {self.state.name}",
            f"Realm: {self.current_realm}",
            f"Time: {self.total_time:.1f}s",
        ]

        # Add Digital World info if available
        if self.digital_world:
            realm_name = self.digital_world.get_realm_name()
            intensity = self.digital_world.transition_progress
            debug_lines.append(f"Digital: {realm_name} ({intensity:.0%})")

        y = 10
        for line in debug_lines:
            text = self.fonts['small'].render(line, True, (0, 255, 0))
            self.screen.blit(text, (10, y))
            y += 20

    # =========================================================================
    # MAIN LOOP
    # =========================================================================

    def run(self):
        """
        Main game loop.

        60 FPS cap with delta time for smooth movement.
        Every frame is a gift.
        """
        while self.running:
            # Calculate delta time (in seconds)
            self.dt = self.clock.tick(FPS) / 1000.0
            self.total_time += self.dt

            # Process input
            self.handle_events()

            # Update game state
            self.update()

            # Render everything
            self.render()

        # Clean shutdown
        self.cleanup()

    def cleanup(self):
        """
        Clean shutdown with a gentle goodbye.

        No abrupt endings in Lelock.
        """
        print()
        print("=" * 50)
        print("  Sweet dreams, little one.")
        print("  MOM will keep the soup warm.")
        print("  See you soon.")
        print("=" * 50)
        print()

        pygame.mixer.quit()
        pygame.quit()
