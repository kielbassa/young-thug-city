import pygame as pg
import random
import noise
from .settings import TILE_SIZE
from .buildings import Residential_Building, Factory, Solar_Panels

class World:
    def __init__(self,resource_manager, entities, hud, clock, grid_length_x, grid_length_y, width, height, seed=None):
        self.resource_manager = resource_manager
        self.entities = entities
        self.hud = hud
        self.clock = clock
        self.grid_length_x = grid_length_x
        self.grid_length_y = grid_length_y
        self.width = width
        self.height = height

        # Set seed
        self.seed = seed if seed is not None else random.randint(0, 999999)
        random.seed(self.seed)

        self.perlin_scale = grid_length_x/2

        # Add animation variables
        self.animation_frame = 0
        self.animation_speed = 0.2  # Controls how fast frames change
        self.animation_timer = 0
        self.water_frames = self.load_water_frames()

        self.grass_tiles = pg.Surface((grid_length_x * TILE_SIZE * 2, grid_length_y * TILE_SIZE + 2 * TILE_SIZE)).convert_alpha()
        self.tiles = self.load_images()
        self.world = self.create_world()
        self.collision_matrix = self.create_collision_matrix()

        self.buildings = [[None for x in range(self.grid_length_x)] for y in range(self.grid_length_y)]
        self.citizens = [[None for x in range(self.grid_length_x)] for y in range(self.grid_length_y)]


        self.temp_tile = None
        self.examine_tile = None

        # load click sound
        self.click_sound = pg.mixer.Sound('assets/audio/click.wav')

    def update(self, clock, camera):
        # Update animation timer and frame
        self.animation_timer += clock.get_time() / 1000.0  # Convert to seconds
        if self.animation_timer >= self.animation_speed:
            self.animation_frame = (self.animation_frame + 1) % len(self.water_frames)
            self.animation_timer = 0

        mouse_pos = pg.mouse.get_pos()
        mouse_action = pg.mouse.get_pressed()

        if mouse_action[2]:
            self.examine_tile = None
            self.hud.examined_tile = None

        self.temp_tile = None
        if self.hud.selected_tile is not None:
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

                self.temp_tile = {
                        "image": img,
                        "render_pos": render_pos,
                        "iso_poly": iso_poly,
                        "buildable": buildable and self.resource_manager.is_affordable(self.hud.selected_tile["name"]),  # Check if affordable
                        "empty": empty,
                        "user_built": user_built
                    }

                if (mouse_action[0] and
                    buildable and
                    self.buildings[grid_pos[0]][grid_pos[1]] is None and
                    self.resource_manager.is_affordable(self.hud.selected_tile["name"])):  # Check if affordable

                    ent = None
                    if self.hud.selected_tile["name"] == "factory":
                        ent = Factory(render_pos, self.resource_manager)
                    elif self.hud.selected_tile["name"] == "residential_building":
                        ent = Residential_Building(render_pos, self.resource_manager)
                    elif self.hud.selected_tile["name"] == "solar_panels":
                        ent = Solar_Panels(render_pos, self.resource_manager)

                    self.entities.append(ent)
                    self.buildings[grid_pos[0]][grid_pos[1]] = ent
                    self.world[grid_pos[0]][grid_pos[1]]["buildable"] = False
                    self.world[grid_pos[0]][grid_pos[1]]["empty"] = False
                    self.world[grid_pos[0]][grid_pos[1]]["walkable"] = False
                    self.world[grid_pos[0]][grid_pos[1]]["user_built"] = True
                    self.collision_matrix[grid_pos[1]][grid_pos[0]] = 0
                    self.click_sound.play()

        else:
            # navigation and selection
            grid_pos = self.mouse_to_grid(mouse_pos[0], mouse_pos[1], camera.scroll)
            if self.can_place_tile(grid_pos):
                building = self.buildings[grid_pos[0]][grid_pos[1]]
                if mouse_action[0] and (building is not None):
                    self.examine_tile = grid_pos
                    self.hud.examined_tile = building



    def draw(self, screen, camera):
        screen.blit(self.grass_tiles, (camera.scroll.x, camera.scroll.y))

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
                citizen = self.citizens[x][y]
                if citizen is not None:
                    screen.blit(citizen.image,
                                (citizen.current_pos.x + self.grass_tiles.get_width()/2 + camera.scroll.x,
                                 citizen.current_pos.y - (citizen.image.get_height() - 1.5*TILE_SIZE) + camera.scroll.y))


        if self.temp_tile is not None:
            iso_poly = self.temp_tile["iso_poly"]
            iso_poly = [(x + self.grass_tiles.get_width()/2 + camera.scroll.x, y - (self.temp_tile["image"].get_height() - 2.5*TILE_SIZE) + camera.scroll.y) for x, y in iso_poly]
            if self.temp_tile["buildable"]:
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
        if self.temp_tile is not None:
            # Get mouse position
            mouse_pos = pg.mouse.get_pos()

            # Get the building cost
            building_name = self.hud.selected_tile["name"]
            cost_info = self.resource_manager.costs[building_name]

            # Create cost text
            cost_text = f"Cost: {cost_info['thugoleons']} thugoleons"

            # Render text
            font = pg.font.SysFont(None, 24)
            text_surface = font.render(cost_text, True, (255, 255, 255))
            text_rect = text_surface.get_rect()

            # Position text near cursor (offset by 20 pixels)
            text_rect.topleft = (mouse_pos[0] + 20, mouse_pos[1] + 20)
            bg_rect = text_rect.copy()
            bg_rect.inflate_ip(10, 10)  # Make background slightly larger than text
            pg.draw.rect(screen, (0, 0, 0, 180), bg_rect)
            screen.blit(text_surface, text_rect)

    def create_world(self):
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

            # Multiple octaves of Perlin noise
            elevation = 0
            amplitude = 1.1
            frequency = 1.0
            persistence = 0.5
            octaves = 2

            for i in range(octaves):
                elevation += amplitude * noise.pnoise2(
                    base_x * frequency / self.perlin_scale,
                    base_y * frequency / self.perlin_scale,
                    octaves=1
                )
                amplitude *= persistence
                frequency *= 2

            # Moisture noise for vegetation
            moisture = noise.pnoise2(
                base_x/self.perlin_scale * 2,
                base_y/self.perlin_scale * 2,
                octaves=4
            )

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
                    if random_variation < 0.04:  # 5% chance
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
                "buildable": True if tile in ["","trees"] else False,
                "empty": True if tile in ["","mud","water"] else False,
                "walkable": True if tile in [""] else False,
                "user_built": False
            }

            return out

    def cart_to_iso(self,x,y):
        iso_x = x - y
        iso_y = (x + y) / 2
        return iso_x, iso_y

    def mouse_to_grid(self, x, y, scroll):
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
        collision_matrix = [[1 for x in range(self.grid_length_x)] for y in range(self.grid_length_y)]

        for x in range(self.grid_length_x):
            for y in range(self.grid_length_y):
                if not self.world[x][y]["empty"]:
                    collision_matrix[y][x] = 0

        return collision_matrix



    def can_place_tile(self, grid_pos):
        mouse_on_panel = False
        for rect in [self.hud.resources_rect, self.hud.build_rect, self.hud.select_rect]:
            if rect.collidepoint(pg.mouse.get_pos()):
                mouse_on_panel = True
                break

        world_bounds = (0 <= grid_pos[0] < self.grid_length_x) and (0 <= grid_pos[1] < self.grid_length_y)
        return world_bounds and not mouse_on_panel

    def load_water_frames(self):
            # Load your water animation frames
            frames = []
            for i in range(4):  # Adjust range based on number of frames you have
                frame = pg.image.load(f"assets/graphics/water_animation/water_{i}.png").convert_alpha()
                frames.append(frame)
            return frames

    def load_images(self):
        block = pg.image.load("assets/graphics/block.png").convert_alpha()
        rock = pg.image.load("assets/graphics/rock.png").convert_alpha()
        trees = pg.image.load("assets/graphics/trees.png").convert_alpha()
        water = pg.image.load("assets/graphics/water.png").convert_alpha()
        mud = pg.image.load("assets/graphics/mud.png").convert_alpha()
        residential_building = pg.image.load("assets/graphics/residential_building.png").convert_alpha()
        factory = pg.image.load("assets/graphics/factory.png").convert_alpha()
        solar_panels = pg.image.load("assets/graphics/solar_panels.png").convert_alpha()

        return {
            "block": block,
            "rock": rock,
            "trees": trees,
            "water": water,
            "mud": mud,
            "residential_building": residential_building,
            "factory": factory,
            "solar_panels": solar_panels
        }
