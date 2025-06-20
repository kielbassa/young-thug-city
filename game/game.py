import pygame as pg
import sys
import time
from .world import World
from .settings import WORLD_SIZE, TEXT_SIZE
from .utils import draw_text
from .camera import Camera
from .hud import Hud
from .resource_manager import ResourceManager
from .buildings import Buildings

class Game:
    def __init__(self, screen, clock):
        self.screen = screen
        self.clock = clock
        self.width, self.height = screen.get_size()
        self.buildings = Buildings()
        self.entities = []
        self.resource_manager = ResourceManager()

        # In-game clock (24-hour format)
        self.game_time = 12  # starting hour
        self.real_time_last_hour = time.time()  # to track when to increase the hour
        self.hour_duration = 5  # seconds in real time for 1 in-game hour

        self.hud = Hud(self.resource_manager,self.width, self.height)
        self.world = World(self.buildings, self.resource_manager, self.entities, self.hud, self.clock, WORLD_SIZE, WORLD_SIZE, self.width, self.height)
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
                if event.key == pg.K_DELETE or event.key == pg.K_BACKSPACE: # toggle delete mode
                    self.hud.delete_mode = not self.hud.delete_mode
                if event.key == pg.K_a: # toggle agent visibility
                    self.world.show_agents = not self.world.show_agents

    def update(self):
        # Update game clock
        current_time = time.time()
        if current_time - self.real_time_last_hour >= self.hour_duration:
            self.game_time = (self.game_time + 1) % 24  # Loop back to 0 after 23
            self.real_time_last_hour = current_time

        # Pass the game time to the HUD
        self.hud.game_time = self.game_time

        self.camera.update()
        for entity in self.entities: # update every entity on the list
            entity.update()
        self.hud.update()
        self.world.update(self.clock, self.camera)

    def draw(self):
        self.screen.fill((0, 0, 0))
        self.world.draw(self.screen, self.camera)
        self.hud.draw(self.screen)

        # Draw FPS counter
        draw_text(self.screen,"fps={}".format(round(self.clock.get_fps())),TEXT_SIZE,(0,255,0),(15, 15))

        # camera scroll debug info
        # draw_text(self.screen,"camera position x={}".format(self.camera.scroll.x),25,(0,255,0),(15, 45))
        # draw_text(self.screen,"camera position y={}".format(self.camera.scroll.y),25,(0,255,0),(15, 75))
        pg.display.flip()
