import pygame as pg
import random
import noise
import math
from .settings import TILE_SIZE

class World:
    def __init__(self, hud, clock, grid_length_x, grid_length_y, width, height, seed=None):
        self.hud = hud
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

    def update(self, clock):
        # Update animation timer and frame
        current_time = pg.time.get_ticks()
        self.animation_timer += clock.get_time() / 1000.0  # Convert to seconds
        if self.animation_timer >= self.animation_speed:
            self.animation_frame = (self.animation_frame + 1) % len(self.water_frames)
            self.animation_timer = 0

    def draw(self, screen, camera):
        screen.blit(self.grass_tiles, (camera.scroll.x, camera.scroll.y))

        for x in range(self.grid_length_x):
            for y in range(self.grid_length_y):
                render_pos = self.world[x][y]["render_pos"]
                tile = self.world[x][y]["tile"]
                if tile != "":
                    if tile == "water":
                        # Render animated water frame
                        water_frame = self.water_frames[self.animation_frame]
                        screen.blit(water_frame,
                                    (render_pos[0] + self.grass_tiles.get_width()/2 + camera.scroll.x,
                                    render_pos[1] - (water_frame.get_height() - 2* TILE_SIZE) + camera.scroll.y))
                    else:
                        # Render other tiles normally
                        screen.blit(self.tiles[tile],
                                    (render_pos[0] + self.grass_tiles.get_width()/2 + camera.scroll.x,
                                    render_pos[1] - (self.tiles[tile].get_height() - 2* TILE_SIZE) + camera.scroll.y))

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
            amplitude = 1.0
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
                "moisture": moisture
            }

            return out

    def cart_to_iso(self,x,y):
        iso_x = x - y
        iso_y = (x + y) / 2
        return iso_x, iso_y

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
        mud = pg.image.load("assets/graphics/mud.png").convert_alpha()  # Add mud texture

        return {"block": block, "rock": rock, "trees": trees, "water": water, "mud": mud}
