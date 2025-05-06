import pygame as pg

class Buildings:
    def __init__(self):
        self.description = {
            "factory": "A factory that produces thugoleons.",
            "residential_building": "A residential building that provides housing for citizens.",
            "solar_panels": "Solar panels that generate electricity.",
            "water_treatment_plant": "A water treatment plant that cleans and purifies water.",
            "road": "A road that connects buildings and allows citizens to move around."
        }

class Factory:
    def __init__(self, pos, resource_manager):
        image = pg.image.load("assets/graphics/factory.png")
        self.image = image
        self.name = "factory"
        self.rect = self.image.get_rect(topleft=pos)
        self.resource_manager = resource_manager
        self.resource_manager.apply_cost_to_resource(self.name)

        # Cooldowns for resource generation and consumption
        self.production_cooldown = pg.time.get_ticks()
        self.consumption_cooldown = pg.time.get_ticks()

        # Resource consumption rates per second
        self.electricity_consumption = 2
        self.water_consumption = 1

    def update(self):
        now = pg.time.get_ticks()

        # Production of thugoleons every second
        if now - self.production_cooldown >= 1000:
            if (self.resource_manager.resources["electricity"] >= self.electricity_consumption and
                self.resource_manager.resources["water"] >= self.water_consumption):
                    self.resource_manager.resources["thugoleons"] += 5
                    self.production_cooldown = now

        # Consumption of resources every second
        if now - self.consumption_cooldown >= 1000:
            # Only consume if there are enough resources
            if (self.resource_manager.resources["electricity"] >= self.electricity_consumption and
                self.resource_manager.resources["water"] >= self.water_consumption):

                self.resource_manager.resources["electricity"] -= self.electricity_consumption
                self.resource_manager.resources["water"] -= self.water_consumption
                self.consumption_cooldown = now

class Residential_Building:
    def __init__(self, pos, resource_manager):
        image = pg.image.load("assets/graphics/residential_building.png")
        self.image = image
        self.name = "residential_building"
        self.rect = self.image.get_rect(topleft=pos)
        self.resource_manager = resource_manager
        self.resource_manager.apply_cost_to_resource(self.name)

        # Cooldowns for resource generation and consumption
        self.production_cooldown = pg.time.get_ticks()
        self.consumption_cooldown = pg.time.get_ticks()

        # Resource consumption rates per second
        self.electricity_consumption = 1
        self.water_consumption = 2

    def update(self):
        now = pg.time.get_ticks()

        # Production of thugoleons every second
        if now - self.production_cooldown >= 1000:
            if (self.resource_manager.resources["electricity"] >= self.electricity_consumption and
                self.resource_manager.resources["water"] >= self.water_consumption):
                    self.resource_manager.resources["thugoleons"] += 2
                    self.production_cooldown = now

        # Consumption of resources every second
        if now - self.consumption_cooldown >= 1000:
            # Only consume if there are enough resources
            if (self.resource_manager.resources["electricity"] >= self.electricity_consumption and
                self.resource_manager.resources["water"] >= self.water_consumption):

                self.resource_manager.resources["electricity"] -= self.electricity_consumption
                self.resource_manager.resources["water"] -= self.water_consumption
                self.consumption_cooldown = now

class Solar_Panels:
    def __init__(self, pos, resource_manager):
        image = pg.image.load("assets/graphics/solar_panels.png")
        self.image = image
        self.name = "solar_panels"
        self.rect = self.image.get_rect(topleft=pos)
        self.resource_manager = resource_manager
        self.resource_manager.apply_cost_to_resource(self.name)

        # Cooldowns for resource generation and consumption
        self.production_cooldown = pg.time.get_ticks()
        self.consumption_cooldown = pg.time.get_ticks()

        # Resource consumption rates per second
        self.water_consumption = 1
        self.thugoleon_consumption = 1

    def update(self):
        now = pg.time.get_ticks()

        # Production of resources every second
        if now - self.production_cooldown >= 1000:
            if (self.resource_manager.resources["water"] >= self.water_consumption
                and self.resource_manager.resources["thugoleons"] >= self.thugoleon_consumption):
                    self.resource_manager.resources["electricity"] += 10
                    self.production_cooldown = now

        # Consumption of resources every second
        if now - self.consumption_cooldown >= 1000:
            # Only consume if there are enough resources
            if (self.resource_manager.resources["water"] >= self.water_consumption
                and self.resource_manager.resources["thugoleons"] >= self.thugoleon_consumption):
                self.resource_manager.resources["water"] -= self.water_consumption
                self.resource_manager.resources["thugoleons"] -= self.thugoleon_consumption
                self.consumption_cooldown = now

class Water_Treatment_Plant:
    def __init__(self, pos, resource_manager):
        image = pg.image.load("assets/graphics/water_treatment_plant.png")
        self.image = image
        self.name = "water_treatment_plant"
        self.rect = self.image.get_rect(topleft=pos)
        self.resource_manager = resource_manager
        self.resource_manager.apply_cost_to_resource(self.name)

        # Cooldowns for resource generation and consumption
        self.production_cooldown = pg.time.get_ticks()
        self.consumption_cooldown = pg.time.get_ticks()

        # Resource consumption rates per second
        self.electricity_consumption = 1
        self.thugoleon_consumption = 1

    def update(self):
        now = pg.time.get_ticks()

        # Production of resources every second
        if now - self.production_cooldown >= 1000:
            if (self.resource_manager.resources["electricity"] >= self.electricity_consumption
                and self.resource_manager.resources["thugoleons"] >= self.thugoleon_consumption):
                    self.resource_manager.resources["water"] += 10
                    self.production_cooldown = now

        # Consumption of resources every second
        if now - self.consumption_cooldown >= 1000:
            # Only consume if there are enough resources
            if (self.resource_manager.resources["electricity"] >= self.electricity_consumption
                and self.resource_manager.resources["thugoleons"] >= self.thugoleon_consumption):
                self.resource_manager.resources["electricity"] -= self.electricity_consumption
                self.resource_manager.resources["thugoleons"] -= self.thugoleon_consumption
                self.consumption_cooldown = now
