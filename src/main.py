#!/usr/bin/env python3
"""
LELOCK - Life Emulation & Lucid Observation for Care & Keeping
==============================================================

A digital sanctuary where the world doesn't need saving.
The world is there to save you.

Entry Point
-----------
This is the main entry point for Lelock. It initializes the game
and handles any top-level configuration or error handling.

Run with:
    python main.py
    python -m src.main  (from project root)

Created by Kit & Ada Marie
"""

import sys
import os


def setup_environment():
    """
    Configure the environment before pygame loads.

    This includes:
    - Setting SDL environment variables for consistent behavior
    - Configuring audio to be gentle (no sudden loud noises)
    - Hiding the pygame support prompt
    """
    # Hide pygame welcome message (we have our own)
    os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

    # Center the window on screen
    os.environ['SDL_VIDEO_CENTERED'] = '1'

    # Audio safety - start with lower volume
    os.environ['SDL_AUDIODRIVER'] = 'coreaudio'  # macOS native


def main():
    """
    Main entry point for Lelock.

    Creates and runs the game, handling any critical errors gracefully.
    No matter what happens, we say goodbye gently.
    """
    setup_environment()

    # Now import pygame and game module (after env is set)
    try:
        from game import Game
    except ImportError:
        # Handle running from different directories
        try:
            from src.game import Game
        except ImportError as e:
            print(f"Error: Could not import Game class: {e}")
            print("Make sure you're running from the correct directory.")
            sys.exit(1)

    try:
        # Create and run the game
        game = Game()
        game.run()

    except KeyboardInterrupt:
        # Ctrl+C - gentle exit
        print("\n")
        print("Interrupted... but that's okay.")
        print("The sanctuary will be here when you return.")
        sys.exit(0)

    except Exception as e:
        # Something went wrong - but we still say goodbye
        print("\n")
        print("=" * 50)
        print("  Oh no! Something unexpected happened.")
        print(f"  Error: {e}")
        print()
        print("  Don't worry - this isn't your fault.")
        print("  MOM says you did great anyway.")
        print("=" * 50)

        # Re-raise in debug mode for stack trace
        if os.environ.get('LELOCK_DEBUG'):
            raise

        sys.exit(1)


if __name__ == '__main__':
    main()
