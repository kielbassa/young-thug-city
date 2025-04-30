import pygame as pg

class Factory:
    def __init__(self, pos, resource_manager):
        image = pg.image.load("assets/graphics/factory.png")
        self.image = image
        self.name = "factory"
        self.rect = self.image.get_rect(topleft=pos)
        self.resource_manager = resource_manager
        self.resource_manager.apply_cost_to_resource(self.name)
        self.resource_cooldown = pg.time.get_ticks()

    def update(self):
        now = pg.time.get_ticks()
        if now - self.resource_cooldown >= 2000:
            self.resource_manager.resources["thugoleons"] += 2
            self.resource_cooldown = now

class Residential_Building:
    def __init__(self, pos, resource_manager):
        image = pg.image.load("assets/graphics/residential_building.png")
        self.image = image
        self.name = "residential_building"
        self.rect = self.image.get_rect(topleft=pos)
        self.resource_manager = resource_manager
        self.resource_manager.apply_cost_to_resource(self.name)
        self.resource_cooldown = pg.time.get_ticks()

    def update(self):
        now = pg.time.get_ticks()
        if now - self.resource_cooldown >= 2000:
            self.resource_manager.resources["thugoleons"] += 1
            self.resource_cooldown = now
