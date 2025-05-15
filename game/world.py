import pygame as pg
import random
import math
import perlin_noise as noise
from .settings import TILE_SIZE, ELECTRICITY_MULTIPLIER, MOISTURE_MULTIPLIER
from .buildings import Residential_Building, Factory, Solar_Panels, Water_Treatment_Plant
from .roads import Road

class World:
    def __init__(self, buildings, resource_manager, entities, hud, clock, grid_length_x, grid_length_y, width, height, seed=None):
        """Initializes the game world with its attributes"""
        self.resource_manager = resource_manager
        self.building_attributes = buildings
        self.entities = entities
        self.hud = hud
        self.hud.world = self
        self.clock = clock
        self.grid_length_x = grid_length_x
        self.grid_length_y = grid_length_y
        self.width = width
        self.height = height

        # Set seed
        self.seed = seed if seed is not None else random.randint(0, 999999)
        random.seed(self.seed)

        self.perlin_scale = grid_length_x/2

        # animation variables
        self.animation_frame = 0
        self.animation_speed = 0.2  # Controls how fast frames change
        self.animation_timer = 0
        self.water_frames = self.load_water_frames()

        self.grass_tiles = pg.Surface((grid_length_x * TILE_SIZE * 2, grid_length_y * TILE_SIZE + 2 * TILE_SIZE)).convert_alpha()
        self.tiles = self.load_images()
        self.world = self.create_world()
        self.collision_matrix = self.create_collision_matrix()

        # grid maps of objects
        self.buildings = [[None for x in range(self.grid_length_x)] for y in range(self.grid_length_y)]
        self.citizens = [[[] for x in range(self.grid_length_x)] for y in range(self.grid_length_y)]
        self.roads = [[None for x in range(self.grid_length_x)] for y in range(self.grid_length_y)]
        # List to track residential buildings and factories for citizen pathing
        self.residential_buildings = []

        # tile variables for hud
        self.temp_tile = None
        self.examine_tile = None

        # sounds
        self.click_sound = pg.mixer.Sound('assets/audio/click.wav')

    def update_road_textures(self, grid_pos):
        """ Update the texture of the road at the given position and its neighbors"""
        neighbors = [
            (grid_pos[0], grid_pos[1] - 1),  # Top
            (grid_pos[0] + 1, grid_pos[1]),  # Right
            (grid_pos[0], grid_pos[1] + 1),  # Bottom
            (grid_pos[0] - 1, grid_pos[1]),  # Left
        ]

        # Update the current road
        road = self.roads[grid_pos[0]][grid_pos[1]]
        if road:
            road.update_texture(grid_pos, self.roads)

        # Update neighboring roads
        for nx, ny in neighbors:
            if 0 <= nx < self.grid_length_x and 0 <= ny < self.grid_length_y:
                neighbor_road = self.roads[nx][ny]
                if neighbor_road:
                    neighbor_road.update_texture((nx, ny), self.roads)

    def update(self, clock, camera):
        """Logic that updates every frame"""
        self.camera = camera
        # Update animation timer and frame
        self.animation_timer += clock.get_time() / 1000.0  # Convert to seconds
        if self.animation_timer >= self.animation_speed:
            self.animation_frame = (self.animation_frame + 1) % len(self.water_frames)
            self.animation_timer = 0

        mouse_pos = pg.mouse.get_pos()
        mouse_action = pg.mouse.get_pressed()

        # on right click stop examining tile
        if mouse_action[2]:
            self.examine_tile = None
            self.hud.examined_tile = None

        self.temp_tile = None
        if self.hud.selected_tile is not None and not self.hud.delete_mode:
            # placing objects
            grid_pos = self.mouse_to_grid(mouse_pos[0], mouse_pos[1], camera.scroll)

            if self.can_place_tile(grid_pos):
                img = self.hud.selected_tile["image"].copy()
                img.set_alpha(100)

                render_pos = self.world[grid_pos[0]][grid_pos[1]]["render_pos"]
                iso_poly = self.world[grid_pos[0]][grid_pos[1]]["iso_poly"]
                buildable = self.world[grid_pos[0]][grid_pos[1]]["buildable"]
                empty = self.world[grid_pos[0]][grid_pos[1]]["empty"]
                user_built = self.world[grid_pos[0]][grid_pos[1]]["user_built"]
                tile_type = self.world[grid_pos[0]][grid_pos[1]]["tile"]

                # Check if the building can be placed on this tile type
                building_can_be_placed_here = True

                # Special case for water treatment plant - can be built on mud
                if self.hud.selected_tile["name"] == "water_treatment_plant":
                    building_can_be_placed_here = tile_type == "mud"
                    # override the default buildable check since mud tiles aren't normally buildable
                    if tile_type == "mud":
                        buildable = True

                # Special case for roads - can be built on mud
                elif self.hud.selected_tile["name"] == "road":
                    if tile_type == "mud":
                        buildable = True

                self.temp_tile = {
                        "image": img,
                        "render_pos": render_pos,
                        "iso_poly": iso_poly,
                        "buildable": buildable and self.resource_manager.is_affordable(self.hud.selected_tile["name"]) and building_can_be_placed_here,
                        "empty": empty,
                        "user_built": user_built,
                        "road_access": self.check_adjacent_roads(grid_pos),  # Check if there are adjacent roads
                        "water_resource": tile_type == "mud" and self.hud.selected_tile["name"] == "water_treatment_plant",
                    }

                # Special placement conditions for water treatment plant
                if self.hud.selected_tile["name"] == "water_treatment_plant" and tile_type == "mud":
                    can_place = (
                        mouse_action[0] and
                        self.check_adjacent_roads(grid_pos) and
                        self.buildings[grid_pos[0]][grid_pos[1]] is None and
                        self.roads[grid_pos[0]][grid_pos[1]] is None and
                        self.resource_manager.is_affordable(self.hud.selected_tile["name"])
                    )
                # Special placement conditions for roads on mud
                elif self.hud.selected_tile["name"] == "road" and tile_type == "mud":
                    can_place = (
                        mouse_action[0] and
                        self.roads[grid_pos[0]][grid_pos[1]] is None and
                        self.buildings[grid_pos[0]][grid_pos[1]] is None and
                        self.resource_manager.is_affordable(self.hud.selected_tile["name"])
                    )
                else:
                    # Normal placement conditions for other buildings
                    can_place = (
                        mouse_action[0] and
                        buildable and
                        self.check_adjacent_roads(grid_pos) and
                        self.buildings[grid_pos[0]][grid_pos[1]] is None and
                        self.roads[grid_pos[0]][grid_pos[1]] is None and
                        building_can_be_placed_here and
                        self.resource_manager.is_affordable(self.hud.selected_tile["name"])
                    )

                if can_place:
                    ent = None
                    match self.hud.selected_tile["name"]:
                        case "road":
                            ent = Road(self.world[grid_pos[0]][grid_pos[1]]["render_pos"], self.resource_manager)
                            self.world[grid_pos[0]][grid_pos[1]]["walkable"] = True
                            # Update collision matrix to allow pathing through this tile
                            self.collision_matrix[grid_pos[1]][grid_pos[0]] = 1
                            self.roads[grid_pos[0]][grid_pos[1]] = ent
                            self.update_road_textures(grid_pos)
                        case "factory":
                            ent = Factory(render_pos, self.resource_manager, self, grid_pos)
                            self.buildings[grid_pos[0]][grid_pos[1]] = ent
                        case "residential_building":
                            ent = Residential_Building(render_pos, self.resource_manager, self, grid_pos)
                            self.buildings[grid_pos[0]][grid_pos[1]] = ent
                        case "solar_panels":
                            ent = Solar_Panels(render_pos, self.resource_manager, self, grid_pos)
                            electricity_production_rate = round(self.world[grid_pos[0]][grid_pos[1]]["elevation"]*ELECTRICITY_MULTIPLIER)
                            water_consumption_rate = round(ent.water_consumption + electricity_production_rate*0.15)
                            ent.electricity_production_rate = electricity_production_rate
                            ent.water_consumption = water_consumption_rate
                            self.buildings[grid_pos[0]][grid_pos[1]] = ent
                        case "water_treatment_plant":
                            ent = Water_Treatment_Plant(render_pos, self.resource_manager, self, grid_pos)
                            water_production_rate = round(self.world[grid_pos[0]][grid_pos[1]]["moisture"]*MOISTURE_MULTIPLIER)
                            electricity_consumption_rate = round(ent.electricity_consumption + water_production_rate*0.3)
                            ent.water_production_rate = water_production_rate
                            ent.electricity_consumption = electricity_consumption_rate
                            self.buildings[grid_pos[0]][grid_pos[1]] = ent
                    # add the created entity to the list
                    self.entities.append(ent)
                    if self.world[grid_pos[0]][grid_pos[1]]["tile"] == "trees":
                        self.world[grid_pos[0]][grid_pos[1]]["tile"] = ""
                    self.world[grid_pos[0]][grid_pos[1]]["buildable"] = False
                    self.world[grid_pos[0]][grid_pos[1]]["empty"] = False
                    if self.hud.selected_tile["name"] == "road":
                        # Only mark road tiles as walkable
                        self.world[grid_pos[0]][grid_pos[1]]["walkable"] = True
                    else:
                        # Only update collision matrix for non-road buildings
                        self.collision_matrix[grid_pos[1]][grid_pos[0]] = 0
                    self.world[grid_pos[0]][grid_pos[1]]["user_built"] = True
                    self.click_sound.play()

        elif self.hud.delete_mode and mouse_action[0]:  # Check if delete mode is active and left-click
            self.temp_tile = None
            grid_pos = self.mouse_to_grid(mouse_pos[0], mouse_pos[1], camera.scroll)
            if self.can_place_tile(grid_pos):
                building = self.buildings[grid_pos[0]][grid_pos[1]]
                if building is not None:
                    # If a factory is being demolished, its workers need to find new jobs
                    if building.name == "factory" and hasattr(building, 'worker_count') and building.worker_count > 0:
                        # Find all citizens that might be working here
                        for entity in self.entities:
                            if hasattr(entity, 'workplace') and entity.workplace == building:
                                # Reset this citizen's workplace and make them find a new one
                                entity.workplace = None
                                entity.workplace_road_pos = None
                                entity.find_workplace()

                    # Remove building
                    self.click_sound.play()
                    self.entities.remove(building)
                    self.buildings[grid_pos[0]][grid_pos[1]] = None

                road = self.roads[grid_pos[0]][grid_pos[1]]
                if road is not None:
                    # Remove road
                    self.click_sound.play()
                    self.entities.remove(road)
                    self.roads[grid_pos[0]][grid_pos[1]] = None
                self.world[grid_pos[0]][grid_pos[1]]["buildable"] = True
                self.world[grid_pos[0]][grid_pos[1]]["empty"] = True
                self.world[grid_pos[0]][grid_pos[1]]["walkable"] = True
                self.world[grid_pos[0]][grid_pos[1]]["user_built"] = False
                self.collision_matrix[grid_pos[1]][grid_pos[0]] = 1

                # Update road textures after deletion
                self.update_road_textures(grid_pos)
        else:
            # navigation and selection
            grid_pos = self.mouse_to_grid(mouse_pos[0], mouse_pos[1], camera.scroll)
            if self.can_place_tile(grid_pos):
                building = self.buildings[grid_pos[0]][grid_pos[1]]
                if mouse_action[0] and (building is not None):
                    self.examine_tile = grid_pos
                    self.hud.examined_tile = building

    def draw(self, screen, camera):
        """draw logic for the world class"""
        screen.blit(self.grass_tiles, (camera.scroll.x, camera.scroll.y))
        # Get the game time from the HUD if available
        game_time = getattr(self.hud, 'game_time', 12)  # Default to noon if not available
        for x in range(self.grid_length_x):
            for y in range(self.grid_length_y):
                render_pos = self.world[x][y]["render_pos"]
                # draw world tiles
                tile = self.world[x][y]["tile"]
                if tile != "":
                    if tile == "water":
                        # Render animated water frame
                        water_frame = self.water_frames[self.animation_frame % len(self.water_frames)]
                        screen.blit(water_frame,
                                    (render_pos[0] + self.grass_tiles.get_width()/2 + camera.scroll.x,
                                    render_pos[1] - (water_frame.get_height() - 2 * TILE_SIZE) + camera.scroll.y))
                    else:
                        # Render other tiles normally
                        screen.blit(self.tiles[tile],
                                    (render_pos[0] + self.grass_tiles.get_width()/2 + camera.scroll.x,
                                    render_pos[1] - (self.tiles[tile].get_height() - 2 * TILE_SIZE) + camera.scroll.y))

                # draw roads
                road = self.roads[x][y]
                if road is not None:
                    screen.blit(road.image,
                                (render_pos[0] + self.grass_tiles.get_width()/2 + camera.scroll.x,
                                render_pos[1] - (road.image.get_height() - 2 * TILE_SIZE) + camera.scroll.y))
                # draw buildings
                building = self.buildings[x][y]
                if building is not None:
                    screen.blit(building.image,
                                (render_pos[0] + self.grass_tiles.get_width()/2 + camera.scroll.x,
                                render_pos[1] - (building.image.get_height() - 2 * TILE_SIZE) + camera.scroll.y))
                    if self.examine_tile is not None:
                        if (x==self.examine_tile[0] and y==self.examine_tile[1]):
                            mask = pg.mask.from_surface(building.image).outline()
                            mask = [(x + render_pos[0] + self.grass_tiles.get_width()/2 + camera.scroll.x,
                                    y + render_pos[1] - (building.image.get_height() - 2 * TILE_SIZE) + camera.scroll.y
                                    ) for x, y in mask]
                            pg.draw.polygon(screen, (255, 255, 255), mask, 3)

                # draw citizens
                citizens_on_tile = self.citizens[x][y]
                for i, citizen in enumerate(citizens_on_tile):
                    if not citizen.in_Building:
                        # Add a small offset for each citizen to make them visible
                        x_offset = 0
                        y_offset = 0

                        if len(citizens_on_tile) > 1:
                            # Create a circular pattern around the center point
                            radius = 12  # Radius of the circle
                            angle = (i * 2 * 3.14159) / min(len(citizens_on_tile), 8)  # Distribute evenly around the circle
                            x_offset = int(radius * math.cos(angle))
                            y_offset = int(radius * math.sin(angle))

                            # For more than 8 citizens, create an outer circle
                            if i >= 8:
                                outer_radius = 20
                                outer_angle = ((i - 8) * 2 * 3.14159) / min(len(citizens_on_tile) - 8, 12)
                                x_offset = int(outer_radius * math.cos(outer_angle))
                                y_offset = int(outer_radius * math.sin(outer_angle))

                        screen.blit(citizen.image,
                                   (citizen.current_pos.x + self.grass_tiles.get_width()/2 + camera.scroll.x + x_offset,
                                    citizen.current_pos.y - (citizen.image.get_height() - 1.5*TILE_SIZE) + camera.scroll.y + y_offset))

                # Draw red polygon around the tile in delete mode
                if self.hud.delete_mode:
                    grid_pos = self.mouse_to_grid(pg.mouse.get_pos()[0], pg.mouse.get_pos()[1], camera.scroll)
                    if grid_pos == (x, y):
                        iso_poly = self.world[x][y]["iso_poly"]
                        iso_poly = [(px + self.grass_tiles.get_width() / 2 + camera.scroll.x,
                                    py + camera.scroll.y + 0.5*TILE_SIZE) for px, py in iso_poly]

                        # Create a transparent surface for the polygon
                        polygon_surface = pg.Surface(screen.get_size(), pg.SRCALPHA)
                        pg.draw.polygon(polygon_surface, (255, 0, 0, 128), iso_poly)  # Red with 50% transparency
                        screen.blit(polygon_surface, (0, 0))

        # Draw the temporary tile's polygon
        if self.temp_tile is not None:
            iso_poly = self.temp_tile["iso_poly"]
            iso_poly = [(x + self.grass_tiles.get_width()/2 + camera.scroll.x, y - (self.temp_tile["image"].get_height() - 2.5*TILE_SIZE) + camera.scroll.y) for x, y in iso_poly]
            if self.temp_tile["buildable"] or self.temp_tile["water_resource"] and self.hud.selected_tile["name"] == "water_treatment_plant":
                pg.draw.polygon(screen, (255, 255, 255), iso_poly, 3)
            elif self.temp_tile["user_built"]:
                pg.draw.polygon(screen, (0, 0, 255), iso_poly, 3)
            else:
                pg.draw.polygon(screen, (255, 0, 0), iso_poly, 3)
            render_pos = self.temp_tile["render_pos"]
            screen.blit(self.temp_tile["image"],
                        (
                            render_pos[0] + self.grass_tiles.get_width()/2 + camera.scroll.x,
                            render_pos[1] - (self.temp_tile["image"].get_height() - 2 * TILE_SIZE) + camera.scroll.y)
                        )

        # Define sunrise and sunset times
        sunrise_start = 5   # 5:00 AM
        sunrise_end = 7     # 7:00 AM
        sunset_start = 18   # 6:00 PM
        sunset_end = 21     # 8:00 PM

        # Create a surface for the tint overlay
        tint_overlay = pg.Surface((screen.get_width(), screen.get_height()), pg.SRCALPHA)

        # Apply blue night tint if time is between sunset_end and sunrise_start
        if game_time >= sunset_end or game_time < sunrise_start:
            # Calculate alpha based on time (darkest at midnight, gradually lightens toward dawn/dusk)
            if game_time >= sunset_end:
                # Evening: sunset_end (alpha=50) to midnight (alpha=120)
                night_progress = (game_time - sunset_end) / (24 - sunset_end)  # 0 to 1
                alpha = int(40 + night_progress * 70)

                # Keep some orange hue right after sunset (first 1.5 hours after sunset_end)
                if game_time < sunset_end + 1.5:
                    orange_factor = 1 - (game_time - sunset_end) / 1.5  # 1 to 0
                    # Blend blue with orange
                    blue = int(0 * (1 - orange_factor) + 0 * orange_factor)
                    green = int(0 * (1 - orange_factor) + 80 * orange_factor)
                    red = int(80 * (1 - orange_factor) + 150 * orange_factor)
                    tint_overlay.fill((red, green, blue, alpha))
                else:
                    tint_overlay.fill((0, 0, 80, alpha))  # Dark blue with alpha transparency
            else:
                # Morning: midnight (alpha=120) to sunrise_start (alpha=50)
                night_progress = (sunrise_start - game_time) / sunrise_start  # 1 to 0
                alpha = int(50 + night_progress * 70)

                # Add some orange hue right before sunrise (last 1.5 hours before sunrise_start)
                if game_time > sunrise_start - 1.5:
                    orange_factor = 1 - (sunrise_start - game_time) / 1.5  # 0 to 1
                    # Blend blue with orange
                    blue = int(80 * (1 - orange_factor) + 90 * orange_factor)
                    green = int(0 * (1 - orange_factor) + 80 * orange_factor)
                    red = int(0 * (1 - orange_factor) + 150 * orange_factor)
                    tint_overlay.fill((red, green, blue, alpha))
                else:
                    tint_overlay.fill((0, 0, 80, alpha))  # Dark blue with alpha transparency

        # Apply pinkish/orange hue during sunrise
        elif game_time >= sunrise_start and game_time < sunrise_end:
            # Transition from blue to normal
            sunrise_progress = (game_time - sunrise_start) / (sunrise_end - sunrise_start)  # 0 to 1
            alpha = int(80 * (1 - sunrise_progress))
            # Pink/orange sunrise color
            tint_overlay.fill((150, 80, 90, alpha))

        # Apply pinkish/orange hue during sunset
        elif game_time >= sunset_start and game_time < sunset_end:
            # Transition from normal to blue
            sunset_progress = (game_time - sunset_start) / (sunset_end - sunset_start)  # 0 to 1
            alpha = int(80 * sunset_progress)
            # Pink/orange sunset color
            tint_overlay.fill((150, 80, 90, alpha))

        # Apply the tint if we have one
        if game_time >= sunset_start or game_time < sunrise_end:
            screen.blit(tint_overlay, (0, 0))

    def create_world(self):
        """Initializes the world and its coordinates"""
        world = []
        for grid_x in range(self.grid_length_x):
            world.append([])
            for grid_y in range(self.grid_length_y):
                world_tile = self.grid_to_world(grid_x, grid_y)
                world[grid_x].append(world_tile)

                render_pos = world_tile["render_pos"]
                self.grass_tiles.blit(self.tiles["block"], (render_pos[0] + self.grass_tiles.get_width()/2, render_pos[1]))
        return world

    def grid_to_world(self, grid_x, grid_y):
        """converts the empty world grid to one with a procedurally generated world"""
        rect = [
            (grid_x * TILE_SIZE, grid_y * TILE_SIZE),
            (grid_x * TILE_SIZE + TILE_SIZE, grid_y * TILE_SIZE),
            (grid_x * TILE_SIZE + TILE_SIZE, grid_y * TILE_SIZE + TILE_SIZE),
            (grid_x * TILE_SIZE, grid_y * TILE_SIZE + TILE_SIZE),
        ]

        iso_poly = [self.cart_to_iso(x, y) for x, y in rect]
        minx = min([x for x, y in iso_poly])
        miny = min([y for x, y in iso_poly])

        # Add seed to coordinates for unique but consistent generation
        base_x = grid_x + self.seed * 0.1
        base_y = grid_y + self.seed * 0.1

        # Initialize Perlin noise generators
        elevation_noise = noise.PerlinNoise(octaves=1, seed=int(self.seed))
        moisture_noise = noise.PerlinNoise(octaves=2, seed=int(self.seed + 1))

        # Calculate elevation using multiple octaves (2D noise)
        elevation = 0
        amplitude = 1.1
        frequency = 1.0
        persistence = 0.5
        octaves = 2

        for i in range(octaves):
            elevation += amplitude * elevation_noise([base_x / self.perlin_scale * frequency, base_y / self.perlin_scale * frequency])
            amplitude *= persistence
            frequency *= 2

        # Calculate moisture (2D noise)
        moisture = moisture_noise([base_x / self.perlin_scale * 2, base_y / self.perlin_scale * 2])

        # Normalize values
        elevation = (elevation + 1) / 2
        moisture = (moisture + 1) / 2

        # Use seeded random for consistent variation
        random_variation = random.random()

        # Biome determination
        if elevation <= 0.35:
            tile = "water"
        elif elevation <= 0.41:  # Mud around water
            tile = "mud"
        else:
            if elevation > 0.8:
                tile = "rock"
            elif moisture > 0.6 and elevation < 0.7:
                tile = "trees"
            else:
                if random_variation < 0.04:  # 4% chance
                    if moisture > 0.4:
                        tile = "trees"
                    elif elevation > 0.58:
                        tile = "rock"
                    else:
                        tile = ""
                else:
                    tile = ""

        out = {
            "grid": [grid_x, grid_y],
            "cart_rect": rect,
            "iso_poly": iso_poly,
            "render_pos": [minx, miny],
            "tile": tile,
            "elevation": elevation,
            "moisture": moisture,
            "buildable": True if tile in ["", "trees"] else False,
            "empty": True if tile in ["", "mud", "water"] else False,
            "walkable": True if tile in ["", "mud"] else False,
            "user_built": False
        }

        return out

    def check_adjacent_roads(self, grid_pos):
        """Check if the tile has a road adjacent to it"""
        if self.hud.selected_tile["name"] == "road":
            return True
        else:
        # Check if the tile has a road adjacent to it
            x, y = grid_pos
            # Ensure the grid position is within bounds
            if not (0 <= x < self.grid_length_x and 0 <= y < self.grid_length_y):
                return False
            # Check for adjacent roads
            adjacent_positions = [
                (x - 1, y),  # Left
                (x + 1, y),  # Right
                (x, y - 1),  # Top
                (x, y + 1)   # Bottom
            ]
            for nx, ny in adjacent_positions:
                if 0 <= nx < self.grid_length_x and 0 <= ny < self.grid_length_y:
                    if self.roads[nx][ny] is not None:
                        return True
            return False

    def cart_to_iso(self,x,y):
        """convert cartesian coordinates to isometric coordinates"""
        iso_x = x - y
        iso_y = (x + y) / 2
        return iso_x, iso_y

    def mouse_to_grid(self, x, y, scroll):
        """convert mouse position to grid coordinates"""
        # transform to world position (remove camera scroll and offset)
        world_x = x - scroll.x - self.grass_tiles.get_width()/2
        world_y = y - scroll.y
        # transform to cart (inverse of cart_to_iso)
        cart_y = (2*world_y - world_x)/2
        cart_x = cart_y + world_x
        # transform to grid coordinates
        grid_x = int(cart_x // TILE_SIZE)
        grid_y = int(cart_y // TILE_SIZE)
        return grid_x, grid_y

    def create_collision_matrix(self):
        """Create a collision matrix for the world and its entities."""
        collision_matrix = [[1 for x in range(self.grid_length_x)] for y in range(self.grid_length_y)]
        for x in range(self.grid_length_x):
            for y in range(self.grid_length_y):
                if not self.world[x][y]["walkable"]:
                    collision_matrix[y][x] = 0

        return collision_matrix

    def can_place_tile(self, grid_pos):
        """Check if a tile can be placed at the given grid position."""
        mouse_on_panel = False
        for rect in [self.hud.resources_rect, self.hud.build_rect]:
            if rect.collidepoint(pg.mouse.get_pos()):
                mouse_on_panel = True
                break

        world_bounds = (0 <= grid_pos[0] < self.grid_length_x) and (0 <= grid_pos[1] < self.grid_length_y)
        return world_bounds and not mouse_on_panel

    def load_water_frames(self):
        """Load water animation frames"""
        frames = []
        for i in range(4):  # Adjust range based on number of frames you have
            frame = pg.image.load(f"assets/graphics/water_animation/water_{i}.png").convert_alpha()
            frames.append(frame)
        return frames

    def load_images(self):
        """Loads all textures used in the game."""
        block = pg.image.load("assets/graphics/block.png").convert_alpha()
        rock = pg.image.load("assets/graphics/rock.png").convert_alpha()
        trees = pg.image.load("assets/graphics/trees.png").convert_alpha()
        water = pg.image.load("assets/graphics/water.png").convert_alpha()
        mud = pg.image.load("assets/graphics/mud.png").convert_alpha()
        residential_building = pg.image.load("assets/graphics/residential_building.png").convert_alpha()
        factory = pg.image.load("assets/graphics/factory.png").convert_alpha()
        solar_panels = pg.image.load("assets/graphics/solar_panels.png").convert_alpha()
        water_treatment_plant = pg.image.load("assets/graphics/water_treatment_plant.png").convert_alpha()

        return {
            "block": block,
            "rock": rock,
            "trees": trees,
            "water": water,
            "mud": mud,
            "residential_building": residential_building,
            "factory": factory,
            "solar_panels": solar_panels,
            "water_treatment_plant": water_treatment_plant
        }
