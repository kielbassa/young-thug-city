import pygame as pg
import sys
from .world import World
from .settings import TILE_SIZE, WORLD_SIZE
from .utils import draw_text
from .camera import Camera
from .hud import Hud

class Game:
    def __init__(self, screen, clock):
        self.screen = screen
        self.clock = clock
        self.width, self.height = screen.get_size()

        # world
        self.world = World(WORLD_SIZE, WORLD_SIZE, self.width, self.height)

        # camera
        self.camera = Camera(self.width, self.height)

        # hud
        self.hud = Hud(self.width, self.height)

    def run(self):
        self.playing = True
        while self.playing:
            self.clock.tick(60)
            self.events()
            self.update()
            self.draw()

    def events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    pg.quit()
                    sys.exit()
    def update(self):
        self.camera.update()
        self.hud.update()

    def draw(self):
        self.screen.fill((0, 0, 0))

        # Update animation timer and frame
        current_time = pg.time.get_ticks()
        self.world.animation_timer += self.clock.get_time() / 1000.0  # Convert to seconds
        if self.world.animation_timer >= self.world.animation_speed:
            self.world.animation_frame = (self.world.animation_frame + 1) % len(self.world.water_frames)
            self.world.animation_timer = 0

        self.screen.blit(self.world.grass_tiles, (self.camera.scroll.x, self.camera.scroll.y))

        for x in range(self.world.grid_length_x):
            for y in range(self.world.grid_length_y):
                render_pos = self.world.world[x][y]["render_pos"]
                tile = self.world.world[x][y]["tile"]

                if tile != "":
                    if tile == "water":
                        # Render animated water frame
                        water_frame = self.world.water_frames[self.world.animation_frame]
                        self.screen.blit(water_frame,
                                       (render_pos[0] + self.world.grass_tiles.get_width()/2 + self.camera.scroll.x,
                                        render_pos[1] - (water_frame.get_height() - 2* TILE_SIZE) + self.camera.scroll.y))
                    else:
                        # Render other tiles normally
                        self.screen.blit(self.world.tiles[tile],
                                       (render_pos[0] + self.world.grass_tiles.get_width()/2 + self.camera.scroll.x,
                                        render_pos[1] - (self.world.tiles[tile].get_height() - 2* TILE_SIZE) + self.camera.scroll.y))

        self.hud.draw(self.screen)
        draw_text(self.screen,"fps={}".format(round(self.clock.get_fps())),25,(255,255,255),(15, 15))
        pg.display.flip()
