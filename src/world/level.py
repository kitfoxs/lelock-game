"""
Lelock Level System
The Mandala of Safety - home at center, gentle adventure outward.

This is the beating heart of Lelock's world. Every tree, every NPC,
every tile exists to make the player feel safe and loved.
"""

import os
import pygame
from pytmx.util_pygame import load_pygame

from settings import TILE_SIZE, LAYERS, COLORS, SCREEN_WIDTH, SCREEN_HEIGHT
from world.camera import CameraGroup


class Level:
    """
    Manages the game world - sprites, collisions, interactions.

    Design Philosophy:
    - The world is a sanctuary, not a challenge
    - Every object should feel "friend-shaped"
    - Transitions are gentle (no harsh cuts)
    - NPCs and weather hook in here but live elsewhere

    The Level is the "Stage" - it holds all the actors,
    but the drama comes from the systems that plug into it.
    """

    def __init__(self, map_path: str = None):
        """
        Initialize the level.

        Args:
            map_path: Path to .tmx Tiled map file. If None, creates empty level.
        """
        # Get the display surface
        self.display_surface = pygame.display.get_surface()

        # Sprite groups
        # all_sprites: Everything that gets drawn (uses CameraGroup for offset)
        # collision_sprites: Things the player bumps into
        # interaction_sprites: Things the player can interact with (E to use)
        self.all_sprites = CameraGroup()
        self.collision_sprites = pygame.sprite.Group()
        self.interaction_sprites = pygame.sprite.Group()

        # NPC group (separate for easy iteration)
        self.npc_sprites = pygame.sprite.Group()

        # Tree group (for fruit regeneration)
        self.tree_sprites = pygame.sprite.Group()

        # Player reference (set during setup)
        self.player = None

        # Map data
        self.tmx_data = None
        self.map_width = 0
        self.map_height = 0

        # Actual tile size from map (may differ from TILE_SIZE setting)
        self.map_tile_size = TILE_SIZE

        # Weather system placeholder (injected by Game)
        self.weather = None

        # Time of day overlay placeholder
        self.sky_overlay = None

        # Shop/menu state
        self.menu_active = False

        # Load map if provided
        if map_path:
            self.load_map(map_path)

    def load_map(self, map_path: str):
        """
        Load a Tiled .tmx map file.

        Parses all layers and creates appropriate sprites.
        Layer names in Tiled should match expected patterns.

        Args:
            map_path: Absolute or relative path to .tmx file
        """
        self.tmx_data = load_pygame(map_path)

        # Use the tile size from the map itself!
        self.map_tile_size = self.tmx_data.tilewidth

        # Calculate map dimensions using MAP's tile size
        self.map_width = self.tmx_data.width * self.map_tile_size
        self.map_height = self.tmx_data.height * self.map_tile_size

        # Tell camera about map bounds
        self.all_sprites.set_map_bounds(self.map_width, self.map_height)

        # Load the ground image first (like skeleton does)
        self._load_ground_image(map_path)

        # Process each layer from the TMX
        self._load_tile_layers()
        self._load_object_layers()
        self._load_player_layer()

    def _load_ground_image(self, map_path: str):
        """
        Load the pre-rendered ground image if it exists.

        The skeleton uses graphics/world/ground.png as the base layer.
        This is faster than rendering individual tiles.
        """
        # Try to find ground.png relative to the map
        map_dir = os.path.dirname(map_path)

        # Check common locations
        possible_paths = [
            os.path.join(map_dir, '..', 'graphics', 'world', 'ground.png'),
            os.path.join(map_dir, 'ground.png'),
            'assets/graphics/world/ground.png',
        ]

        for path in possible_paths:
            if os.path.exists(path):
                ground_surf = pygame.image.load(path).convert_alpha()
                GenericSprite(
                    pos=(0, 0),
                    surface=ground_surf,
                    groups=[self.all_sprites],
                    z=LAYERS['ground']
                )
                return

        # No ground.png found - that's okay, we'll render from tiles

    def _load_tile_layers(self):
        """
        Load all tile layers from the TMX map.

        Actual layers in our map:
        - Ground, Forest Grass, Outside Decoration, Hills (ground layer)
        - Fence (collision)
        - HouseFloor, HouseWalls, HouseFurnitureBottom, HouseFurnitureTop (house)
        """
        tile_size = self.map_tile_size

        # Ground layers (visual only, no collision)
        ground_layers = ['Ground', 'Forest Grass', 'Outside Decoration', 'Hills']
        for layer_name in ground_layers:
            layer = self._get_layer_safe(layer_name)
            if layer is None:
                continue
            for x, y, surface in layer.tiles():
                if surface:
                    pos = (x * tile_size, y * tile_size)
                    GenericSprite(pos, surface, [self.all_sprites], LAYERS['ground'])

        # Fence (collision + visual)
        layer = self._get_layer_safe('Fence')
        if layer:
            for x, y, surface in layer.tiles():
                if surface:
                    pos = (x * tile_size, y * tile_size)
                    GenericSprite(
                        pos,
                        surface,
                        [self.all_sprites, self.collision_sprites],
                        LAYERS['main']
                    )

        # House bottom layer (floor, lower furniture)
        for layer_name in ['HouseFloor', 'HouseFurnitureBottom']:
            layer = self._get_layer_safe(layer_name)
            if layer is None:
                continue
            for x, y, surface in layer.tiles():
                if surface:
                    pos = (x * tile_size, y * tile_size)
                    GenericSprite(pos, surface, [self.all_sprites], LAYERS['house_bottom'])

        # House walls and top (rendered above player)
        for layer_name in ['HouseWalls', 'HouseFurnitureTop']:
            layer = self._get_layer_safe(layer_name)
            if layer is None:
                continue
            for x, y, surface in layer.tiles():
                if surface:
                    pos = (x * tile_size, y * tile_size)
                    GenericSprite(pos, surface, [self.all_sprites], LAYERS['main'])

    def _load_object_layers(self):
        """
        Load object layers (Trees, Decoration).

        Objects have x, y, width, height, and image properties.
        """
        # Trees (collision + visual)
        layer = self._get_layer_safe('Trees')
        if layer:
            for obj in layer:
                if hasattr(obj, 'image') and obj.image:
                    GenericSprite(
                        pos=(obj.x, obj.y),
                        surface=obj.image,
                        groups=[self.all_sprites, self.collision_sprites, self.tree_sprites],
                        z=LAYERS['main']
                    )

        # Decoration objects (wildflowers, etc - collision)
        layer = self._get_layer_safe('Decoration')
        if layer:
            for obj in layer:
                if hasattr(obj, 'image') and obj.image:
                    GenericSprite(
                        pos=(obj.x, obj.y),
                        surface=obj.image,
                        groups=[self.all_sprites, self.collision_sprites],
                        z=LAYERS['main']
                    )

        # Generic objects layer
        layer = self._get_layer_safe('Objects')
        if layer:
            for obj in layer:
                if hasattr(obj, 'image') and obj.image:
                    GenericSprite(
                        pos=(obj.x, obj.y),
                        surface=obj.image,
                        groups=[self.all_sprites],
                        z=LAYERS['main']
                    )

    def _load_player_layer(self):
        """
        Load player spawn point and interaction zones from Player layer.
        """
        layer = self._get_layer_safe('Player')
        if layer is None:
            return

        for obj in layer:
            # Skip player start position (handled by get_player_spawn)
            if obj.name == 'Start':
                continue

            # Create interaction zones for Bed, Trader, etc
            if hasattr(obj, 'width') and hasattr(obj, 'height'):
                InteractionSprite(
                    (obj.x, obj.y),
                    (obj.width, obj.height),
                    self.interaction_sprites,
                    obj.name
                )

    def _get_layer_safe(self, layer_name: str):
        """
        Safely get a layer by name, returning None if not found.

        Prevents crashes from missing layers in development.
        """
        if self.tmx_data is None:
            return None
        try:
            return self.tmx_data.get_layer_by_name(layer_name)
        except ValueError:
            # Layer doesn't exist - that's okay during development
            return None

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

    def get_player_spawn(self) -> tuple:
        """
        Get the player spawn position from the map.

        Looks for object named 'Start' in 'Player' layer.

        Returns:
            (x, y) tuple for player spawn, or center of map if not found
        """
        layer = self._get_layer_safe('Player')
        if layer:
            for obj in layer:
                if obj.name == 'Start':
                    return (obj.x, obj.y)

        # Fallback to map center
        return (self.map_width // 2, self.map_height // 2)

    def set_player(self, player: pygame.sprite.Sprite):
        """
        Register the player with this level.

        Args:
            player: The player sprite
        """
        self.player = player
        self.all_sprites.add(player)

        # Snap camera to player initially
        self.all_sprites.snap_to_target(player)

    def add_npc(self, npc: pygame.sprite.Sprite):
        """
        Add an NPC to the level.

        NPCs are added to both npc_sprites (for iteration)
        and all_sprites (for drawing).

        Args:
            npc: The NPC sprite
        """
        self.npc_sprites.add(npc)
        self.all_sprites.add(npc)

    def reset(self):
        """
        Reset the level for a new day.

        Called when player sleeps. Handles:
        - Weather randomization (if weather system attached)
        - Tree fruit regeneration
        - Soil state updates
        - Sky color reset

        This is a NEW DAY, not a level reload.
        All memories persist, only nature refreshes.
        """
        # Reset sky overlay to morning
        if self.sky_overlay:
            self.sky_overlay.reset_to_morning()

        # Randomize weather for new day
        if self.weather:
            self.weather.new_day()

        # Regenerate tree fruit
        for tree in self.tree_sprites.sprites():
            if hasattr(tree, 'regenerate_fruit'):
                tree.regenerate_fruit()

    def toggle_menu(self):
        """Toggle the menu/shop active state."""
        self.menu_active = not self.menu_active

    def get_interactable_at_player(self) -> str:
        """
        Check if player is near an interactable object.

        Returns:
            Name of interaction (e.g., 'Bed', 'Trader', 'Terminal')
            or None if nothing nearby
        """
        if self.player is None:
            return None

        for sprite in self.interaction_sprites.sprites():
            if sprite.rect.colliderect(self.player.hitbox):
                return sprite.name

        return None

    def run(self, dt: float):
        """
        Main update and draw loop for the level.

        Args:
            dt: Delta time for frame-independent updates
        """
        # Clear screen with cozy background color
        # Parse hex color to RGB tuple if needed
        bg_color = COLORS['background']
        if isinstance(bg_color, str) and bg_color.startswith('#'):
            bg_color = tuple(int(bg_color[i:i+2], 16) for i in (1, 3, 5))
        self.display_surface.fill(bg_color)

        # Draw all sprites with camera offset
        if self.player:
            self.all_sprites.custom_draw(self.player, dt)
        else:
            # No player yet - still draw sprites centered
            # Create a temporary target at map center for camera
            self._draw_without_player()

        # Update sprites (only if menu not active)
        if not self.menu_active:
            self.all_sprites.update(dt)

        # Weather overlay (rain drops, etc)
        if self.weather and not self.menu_active:
            self.weather.update(dt)

        # Time-of-day sky overlay
        if self.sky_overlay:
            self.sky_overlay.display(dt)

    def _draw_without_player(self):
        """
        Draw sprites when there's no player yet.
        Centers camera on map center.
        """
        # Calculate offset to center the map
        offset_x = self.map_width / 2 - SCREEN_WIDTH / 2
        offset_y = self.map_height / 2 - SCREEN_HEIGHT / 2

        # Get all layer values and sort them
        layer_values = sorted(LAYERS.values())

        # Draw sprites layer by layer
        for layer in layer_values:
            layer_sprites = [
                sprite for sprite in self.all_sprites.sprites()
                if hasattr(sprite, 'z') and sprite.z == layer
            ]

            for sprite in sorted(layer_sprites, key=lambda s: s.rect.centery):
                offset_rect = sprite.rect.copy()
                offset_rect.center = (
                    sprite.rect.centerx - offset_x,
                    sprite.rect.centery - offset_y
                )
                self.display_surface.blit(sprite.image, offset_rect)


class GenericSprite(pygame.sprite.Sprite):
    """
    Basic sprite with position, image, and layer.

    The building block of Lelock's visual world.
    Every tile, every decoration is a GenericSprite.
    """

    def __init__(
        self,
        pos: tuple,
        surface: pygame.Surface,
        groups: list,
        z: int = LAYERS['main']
    ):
        """
        Create a generic sprite.

        Args:
            pos: (x, y) position in world
            surface: pygame Surface to display
            groups: List of sprite groups to add to
            z: Layer for rendering order
        """
        super().__init__(groups)
        self.image = surface
        self.rect = self.image.get_rect(topleft=pos)
        self.z = z

        # Hitbox for collision (same as rect by default)
        self.hitbox = self.rect.copy()


class InteractionSprite(pygame.sprite.Sprite):
    """
    Invisible sprite that marks an interaction zone.

    When player overlaps, they can press E to interact.
    The 'name' property determines what happens.
    """

    def __init__(
        self,
        pos: tuple,
        size: tuple,
        groups,
        name: str
    ):
        """
        Create an interaction zone.

        Args:
            pos: (x, y) position of top-left corner
            size: (width, height) of zone
            groups: Sprite group(s) to add to
            name: Identifier for this interaction (e.g., 'Bed', 'Trader')
        """
        super().__init__(groups)
        self.image = pygame.Surface(size)
        self.image.set_alpha(0)  # Invisible
        self.rect = self.image.get_rect(topleft=pos)
        self.name = name
        self.z = LAYERS['main']  # For compatibility with camera system
