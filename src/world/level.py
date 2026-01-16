"""
Lelock Level System
The Mandala of Safety - home at center, gentle adventure outward.

This is the beating heart of Lelock's world. Every tree, every NPC,
every tile exists to make the player feel safe and loved.
"""

import pygame
from pytmx.util_pygame import load_pygame

from settings import TILE_SIZE, LAYERS, COLORS
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

        # Calculate map dimensions
        self.map_width = self.tmx_data.width * TILE_SIZE
        self.map_height = self.tmx_data.height * TILE_SIZE

        # Tell camera about map bounds
        self.all_sprites.set_map_bounds(self.map_width, self.map_height)

        # Process each layer
        self._load_ground_layers()
        self._load_collision_layer()
        self._load_object_layers()
        self._load_interaction_layer()

    def _load_ground_layers(self):
        """
        Load visual ground layers (no collision).

        Expected Tiled layers:
        - Ground: Base terrain
        - Water: Animated water tiles
        - Paths: Walkable paths
        """
        ground_layers = ['Ground', 'Water', 'Paths', 'Decorations']

        for layer_name in ground_layers:
            layer = self._get_layer_safe(layer_name)
            if layer is None:
                continue

            # Determine render layer
            if layer_name == 'Water':
                z = LAYERS['water']
            elif layer_name == 'Decorations':
                z = LAYERS['ground_plant']
            else:
                z = LAYERS['ground']

            # Create tiles
            for x, y, surface in layer.tiles():
                if surface:
                    pos = (x * TILE_SIZE, y * TILE_SIZE)
                    GenericSprite(pos, surface, [self.all_sprites], z)

    def _load_collision_layer(self):
        """
        Load invisible collision tiles.

        Expected Tiled layer: Collision
        These are invisible but block player movement.
        """
        layer = self._get_layer_safe('Collision')
        if layer is None:
            return

        for x, y, surface in layer.tiles():
            if surface:
                pos = (x * TILE_SIZE, y * TILE_SIZE)
                # Create invisible collision rect
                collision_surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
                collision_surf.set_alpha(0)  # Invisible
                GenericSprite(
                    pos,
                    collision_surf,
                    [self.collision_sprites],
                    z=LAYERS['ground']
                )

    def _load_object_layers(self):
        """
        Load object layers (trees, buildings, etc).

        Expected Tiled object layers:
        - Trees: Harvestable trees
        - Buildings: House structures (bottom and top)
        - Furniture: Interior objects
        """
        # House bottom layer (floor, lower walls)
        for layer_name in ['HouseFloor', 'HouseFurnitureBottom']:
            layer = self._get_layer_safe(layer_name)
            if layer is None:
                continue
            for x, y, surface in layer.tiles():
                if surface:
                    pos = (x * TILE_SIZE, y * TILE_SIZE)
                    GenericSprite(pos, surface, [self.all_sprites], LAYERS['house_bottom'])

        # House top layer (roofs, upper walls)
        for layer_name in ['HouseWalls', 'HouseFurnitureTop', 'HouseTop']:
            layer = self._get_layer_safe(layer_name)
            if layer is None:
                continue
            for x, y, surface in layer.tiles():
                if surface:
                    pos = (x * TILE_SIZE, y * TILE_SIZE)
                    GenericSprite(pos, surface, [self.all_sprites], LAYERS['house_top'])

        # Fence (collision)
        layer = self._get_layer_safe('Fence')
        if layer:
            for x, y, surface in layer.tiles():
                if surface:
                    pos = (x * TILE_SIZE, y * TILE_SIZE)
                    GenericSprite(
                        pos,
                        surface,
                        [self.all_sprites, self.collision_sprites],
                        LAYERS['main']
                    )

    def _load_interaction_layer(self):
        """
        Load interaction zones (NPCs, beds, terminals, etc).

        Expected Tiled object layer: Interactions
        Objects should have 'name' property indicating type.
        """
        layer = self._get_layer_safe('Player')  # Skeleton uses 'Player' layer
        if layer is None:
            layer = self._get_layer_safe('Interactions')
        if layer is None:
            return

        for obj in layer:
            # Skip player start position (handled separately)
            if obj.name == 'Start':
                continue

            # Create interaction zone
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
        self.display_surface.fill(COLORS['background'])

        # Draw all sprites with camera offset
        if self.player:
            self.all_sprites.custom_draw(self.player, dt)

        # Update sprites (only if menu not active)
        if not self.menu_active:
            self.all_sprites.update(dt)

        # Weather overlay (rain drops, etc)
        if self.weather and not self.menu_active:
            self.weather.update(dt)

        # Time-of-day sky overlay
        if self.sky_overlay:
            self.sky_overlay.display(dt)


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
