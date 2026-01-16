#!/usr/bin/env python3
"""
Lelock Asset & Dependency Test Script
Tests that all required assets exist and dependencies work correctly.

Run with: python test_assets.py
"""

import os
import sys
from pathlib import Path

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

# Global counter
ok_count = 0

def ok(msg):
    global ok_count
    ok_count += 1
    print(f"{Colors.GREEN}[OK]{Colors.RESET} {msg}")

def fail(msg):
    print(f"{Colors.RED}[FAIL]{Colors.RESET} {msg}")

def warn(msg):
    print(f"{Colors.YELLOW}[WARN]{Colors.RESET} {msg}")

def info(msg):
    print(f"{Colors.BLUE}[INFO]{Colors.RESET} {msg}")

def header(msg):
    print(f"\n{Colors.BOLD}{Colors.BLUE}=== {msg} ==={Colors.RESET}")

def main():
    global ok_count

    # Ensure we're in the right directory
    project_root = Path(__file__).parent.absolute()
    os.chdir(project_root)

    errors = []
    warnings = []

    # ==========================================================================
    # DEPENDENCY CHECKS
    # ==========================================================================
    header("Python Dependencies")

    # Pygame-CE
    try:
        import pygame
        ok(f"pygame-ce: {pygame.version.ver}")
    except ImportError as e:
        fail(f"pygame-ce not installed: {e}")
        errors.append("pygame-ce not installed")

    # PyTMX
    try:
        import pytmx
        ok("pytmx: installed")
    except ImportError as e:
        fail(f"pytmx not installed: {e}")
        errors.append("pytmx not installed")

    try:
        from pytmx.util_pygame import load_pygame
        ok("pytmx.util_pygame.load_pygame: available")
    except ImportError as e:
        fail(f"load_pygame not available: {e}")
        errors.append("pytmx load_pygame not available")

    # ==========================================================================
    # MAP LOADING TEST
    # ==========================================================================
    header("Map Loading")

    map_path = project_root / "assets" / "maps" / "map.tmx"
    if map_path.exists():
        ok(f"map.tmx exists")

        # Initialize pygame for map loading
        pygame.init()
        pygame.display.set_mode((100, 100))

        try:
            tmx_data = load_pygame(str(map_path))
            ok(f"Map loads successfully!")
            info(f"  Size: {tmx_data.width}x{tmx_data.height} tiles")
            info(f"  Tile size: {tmx_data.tilewidth}x{tmx_data.tileheight}")
            info(f"  Layers: {len(list(tmx_data.visible_layers))}")

            # Note: Map uses 64x64 tiles
            if tmx_data.tilewidth != 64 or tmx_data.tileheight != 64:
                warn(f"  Map tile size is {tmx_data.tilewidth}x{tmx_data.tileheight}, expected 64x64")

        except Exception as e:
            fail(f"Map failed to load: {e}")
            errors.append(f"Map loading failed: {e}")

        pygame.quit()
    else:
        fail(f"map.tmx not found at {map_path}")
        errors.append("map.tmx missing")

    # ==========================================================================
    # TILESET IMAGE CHECKS
    # ==========================================================================
    header("Tileset Images")

    tilesets_dir = project_root / "assets" / "maps" / "Tilesets"
    required_tilesets = [
        "Grass.tsx", "Hills.tsx", "Fences.tsx", "Plant Decoration.tsx",
        "Objects.tsx", "Paths.tsx", "interaction.tsx", "Water.tsx",
        "House.tsx", "House Decoration.tsx"
    ]

    for tsx_file in required_tilesets:
        tsx_path = tilesets_dir / tsx_file
        if tsx_path.exists():
            ok(f"Tileset: {tsx_file}")
        else:
            fail(f"Missing tileset: {tsx_file}")
            errors.append(f"Missing tileset: {tsx_file}")

    # Check tileset source images (referenced via ../../graphics/environment/)
    environment_dir = project_root / "assets" / "graphics" / "environment"
    required_env_images = [
        "Grass.png", "Hills.png", "Fences.png", "Plant Decoration.png",
        "Paths.png", "Water.png", "House.png", "House Decoration.png",
        "interaction.png"
    ]

    for img in required_env_images:
        img_path = environment_dir / img
        if img_path.exists():
            ok(f"Environment: {img}")
        else:
            fail(f"Missing image: {img}")
            errors.append(f"Missing: graphics/environment/{img}")

    # ==========================================================================
    # CHARACTER SPRITES
    # ==========================================================================
    header("Character Sprites")

    character_dir = project_root / "assets" / "graphics" / "character"
    directions = ["up", "down", "left", "right"]
    actions = ["", "_idle", "_axe", "_hoe", "_water"]

    for direction in directions:
        for action in actions:
            folder_name = f"{direction}{action}"
            folder_path = character_dir / folder_name
            if folder_path.exists():
                sprites = list(folder_path.glob("*.png"))
                if sprites:
                    ok(f"Character/{folder_name}: {len(sprites)} frames")
                else:
                    warn(f"Character/{folder_name}: exists but empty")
                    warnings.append(f"Empty sprite folder: {folder_name}")
            else:
                fail(f"Missing character folder: {folder_name}")
                errors.append(f"Missing: character/{folder_name}")

    # ==========================================================================
    # PLAYER SPRITES (uses character sprites)
    # ==========================================================================
    header("Player Sprites")

    player_dir = project_root / "assets" / "graphics" / "player"
    if player_dir.exists():
        sprites = list(player_dir.glob("*.png"))
        if sprites:
            ok(f"Player sprites: {len(sprites)} files")
        else:
            info("Player directory empty - using character sprites (this is fine)")
    else:
        info("No separate player directory - using character sprites (this is fine)")

    # ==========================================================================
    # OBJECT SPRITES
    # ==========================================================================
    header("Object Sprites")

    objects_dir = project_root / "assets" / "graphics" / "objects"
    required_objects = [
        "bush.png", "flower.png", "merchant.png", "mushroom.png",
        "mushrooms.png", "stump_medium.png", "stump_small.png",
        "sunflower.png", "tree_medium.png", "tree_small.png"
    ]

    for obj in required_objects:
        obj_path = objects_dir / obj
        if obj_path.exists():
            ok(f"Object: {obj}")
        else:
            fail(f"Missing object: {obj}")
            errors.append(f"Missing: objects/{obj}")

    # ==========================================================================
    # UI ELEMENTS
    # ==========================================================================
    header("UI Elements")

    ui_dir = project_root / "assets" / "graphics" / "ui"
    if ui_dir.exists():
        ui_files = list(ui_dir.glob("*.png"))
        if ui_files:
            ok(f"UI graphics: {len(ui_files)} files")
        else:
            warn("UI directory is empty - placeholder graphics may be needed")
            warnings.append("UI directory empty")
    else:
        warn("UI directory doesn't exist")
        warnings.append("No UI directory")

    # ==========================================================================
    # OVERLAY (Tool icons, etc)
    # ==========================================================================
    header("Overlay Graphics")

    overlay_dir = project_root / "assets" / "graphics" / "overlay"
    if overlay_dir.exists():
        overlay_files = list(overlay_dir.glob("*.png"))
        if overlay_files:
            ok(f"Overlay graphics: {len(overlay_files)} files")
        else:
            warn("Overlay directory is empty")
            warnings.append("Overlay directory empty")

    # ==========================================================================
    # AUDIO
    # ==========================================================================
    header("Audio Assets")

    audio_dir = project_root / "assets" / "audio"
    if audio_dir.exists():
        audio_files = list(audio_dir.glob("*.*"))
        audio_files = [f for f in audio_files if f.suffix in ['.mp3', '.wav', '.ogg']]
        if audio_files:
            ok(f"Audio files: {len(audio_files)}")
        else:
            warn("No audio files found")
            warnings.append("No audio files")
    else:
        warn("Audio directory doesn't exist")
        warnings.append("No audio directory")

    # ==========================================================================
    # SOIL & FARMING
    # ==========================================================================
    header("Soil & Farming Graphics")

    soil_dir = project_root / "assets" / "graphics" / "soil"
    if soil_dir.exists():
        soil_files = list(soil_dir.glob("*.png"))
        ok(f"Soil tiles: {len(soil_files)} files")
    else:
        warn("Soil directory missing")
        warnings.append("No soil graphics")

    soil_water_dir = project_root / "assets" / "graphics" / "soil_water"
    if soil_water_dir.exists():
        sw_files = list(soil_water_dir.glob("*.png"))
        ok(f"Soil water tiles: {len(sw_files)} files")
    else:
        warn("Soil water directory missing")
        warnings.append("No soil water graphics")

    fruit_dir = project_root / "assets" / "graphics" / "fruit"
    if fruit_dir.exists():
        fruit_items = list(fruit_dir.iterdir())
        ok(f"Fruit/crop items: {len(fruit_items)}")
    else:
        warn("Fruit directory missing")
        warnings.append("No fruit graphics")

    # ==========================================================================
    # SETTINGS CHECK
    # ==========================================================================
    header("Settings Configuration")

    settings_path = project_root / "src" / "settings.py"
    if settings_path.exists():
        ok(f"settings.py exists")

        # Check for TILE_SIZE mismatch
        with open(settings_path, 'r') as f:
            content = f.read()
            if "TILE_SIZE = 32" in content:
                warn("TILE_SIZE = 32 in settings, but map uses 64x64 tiles!")
                warn("Consider updating TILE_SIZE = 64 to match map.tmx")
                warnings.append("TILE_SIZE mismatch (32 vs 64)")
            elif "TILE_SIZE = 64" in content:
                ok("TILE_SIZE = 64 matches map.tmx")
    else:
        fail("settings.py not found!")
        errors.append("settings.py missing")

    # ==========================================================================
    # SUMMARY
    # ==========================================================================
    header("SUMMARY")

    print(f"\n{Colors.GREEN}Checks passed: {ok_count}{Colors.RESET}")

    if warnings:
        print(f"\n{Colors.YELLOW}Warnings ({len(warnings)}):{Colors.RESET}")
        for w in warnings:
            print(f"  - {w}")

    if errors:
        print(f"\n{Colors.RED}Errors ({len(errors)}):{Colors.RESET}")
        for e in errors:
            print(f"  - {e}")
        print(f"\n{Colors.RED}ASSET CHECK FAILED{Colors.RESET}")
        return 1
    else:
        print(f"\n{Colors.GREEN}ALL CRITICAL ASSETS PRESENT!{Colors.RESET}")
        if warnings:
            print(f"{Colors.YELLOW}Some warnings to address when you have time.{Colors.RESET}")
        return 0

if __name__ == "__main__":
    sys.exit(main())
