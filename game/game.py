import pygame as pg
import sys
import random
from .world import World
from .settings import WORLD_SIZE
from .utils import draw_text
from .camera import Camera
from .hud import Hud
from .resource_manager import ResourceManager
from .citizens import Citizen

class Game:
    def __init__(self, screen, clock):
        self.screen = screen
        self.clock = clock
        self.width, self.height = screen.get_size()

        # entities
        self.entities = []

        # resource manager
        self.resource_manager = ResourceManager()

        # hud
        self.hud = Hud(self.resource_manager,self.width, self.height)

        # world
        self.world = World(self.resource_manager, self.entities, self.hud, self.clock, WORLD_SIZE, WORLD_SIZE, self.width, self.height)
        # citizens
        for _ in range(10):
            # Find a random walkable tile
            while True:
                x = random.randint(0, WORLD_SIZE-2)
                y = random.randint(0, WORLD_SIZE-2)
                if self.world.world[x][y]["walkable"]:
                    Citizen(self.world.world[x][y], self.world)
                    break

        # camera
        self.camera = Camera(self.width, self.height, self.hud)

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
        for entity in self.entities:
            entity.update()
        self.hud.update()
        self.world.update(self.clock, self.camera)

    def draw(self):
        self.screen.fill((0, 0, 0))
        self.world.draw(self.screen, self.camera)
        self.hud.draw(self.screen)
        draw_text(self.screen,"fps={}".format(round(self.clock.get_fps())),25,(255,255,255),(15, 15))
        pg.display.flip()
