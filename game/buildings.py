import pygame as pg

class Buildings:
    def __init__(self):
        # these attributes are available to all buildings
        self.description = {
            "factory": "A factory that employs citizens and produces thugoleons.",
            "residential_building": "A residential building that provides housing for citizens.",
            "solar_panels": "Solar panels that generate electricity.",
            "water_treatment_plant": "A water treatment plant that pumps, cleans and purifies water.",
        }

        self.consumption = {
            "factory": {
                "electricity": 2,
                "water": 1,
            },
            "residential_building": {
                "electricity": 1,
                "water": 2,
            },
            "solar_panels": {
                "water": 1,
                "thugoleons": 800,
            },
            "water_treatment_plant": {
                "electricity": 1,
                "thugoleons": 1000,
            },
        }

        self.production = {
            "factory": {
                "thugoleons": 5000,
            },
            "residential_building": {
                "thugoleons": 2500,
            },
            "solar_panels": {
                "electricity": 10,
            },
            "water_treatment_plant": {
                "water": 10,
            },
        }

    def find_adjacent_road(self, world, grid_pos):
        """Find an adjacent road to the building and store its position"""
        x, y = grid_pos
        # Check for adjacent roads
        adjacent_positions = [
            (x - 1, y),  # Left
            (x + 1, y),  # Right
            (x, y - 1),  # Top
            (x, y + 1)   # Bottom
        ]
        for nx, ny in adjacent_positions:
            if 0 <= nx < world.grid_length_x and 0 <= ny < world.grid_length_y:
                if world.roads[nx][ny] is not None:
                    self.adjacent_road = (nx, ny)
                    return

class Factory(Buildings):
    def __init__(self, pos, resource_manager, world=None, grid_pos=None):
        image = pg.image.load("assets/graphics/factory.png")
        resources = Buildings()
        self.image = image
        self.name = "factory"
        self.rect = self.image.get_rect(topleft=pos)
        self.resource_manager = resource_manager
        self.resource_manager.apply_cost_to_resource(self.name)

        # Track number of workers at this factory
        self.worker_count = 0

        # Cooldowns for resource generation and consumption
        self.production_cooldown = pg.time.get_ticks()
        self.consumption_cooldown = pg.time.get_ticks()

        # Resource consumption rates per second
        self.electricity_consumption = resources.consumption["factory"]["electricity"]
        self.water_consumption = resources.consumption["factory"]["water"]

        # Production rates per second
        self.thugoleon_production_rate = resources.production["factory"]["thugoleons"]

        # Store adjacent road position
        self.adjacent_road = None
        if world and grid_pos:
            self.find_adjacent_road(world, grid_pos)

    def update(self):
        now = pg.time.get_ticks()

        # Production of thugoleons every second
        if now - self.production_cooldown >= 1000:
            if (self.resource_manager.resources["electricity"] >= self.electricity_consumption and
                self.resource_manager.resources["water"] >= self.water_consumption):
                    self.resource_manager.resources["thugoleons"] += self.thugoleon_production_rate
                    self.production_cooldown = now

        # Consumption of resources every second
        if now - self.consumption_cooldown >= 1000:
            # Only consume if there are enough resources
            if (self.resource_manager.resources["electricity"] >= self.electricity_consumption and
                self.resource_manager.resources["water"] >= self.water_consumption):

                self.resource_manager.resources["electricity"] -= self.electricity_consumption
                self.resource_manager.resources["water"] -= self.water_consumption
                self.consumption_cooldown = now

class Residential_Building(Buildings):
    def __init__(self, pos, resource_manager, world=None, grid_pos=None):
        image = pg.image.load("assets/graphics/residential_building.png")
        self.image = image
        resources = Buildings()
        self.name = "residential_building"
        self.rect = self.image.get_rect(topleft=pos)
        self.resource_manager = resource_manager
        self.resource_manager.apply_cost_to_resource(self.name)

        # Track number of workers at this factory
        self.worker_count = 0

        # Cooldowns for resource generation and consumption
        self.production_cooldown = pg.time.get_ticks()
        self.consumption_cooldown = pg.time.get_ticks()

        # Resource consumption rates per second
        self.electricity_consumption = resources.consumption["residential_building"]["electricity"]
        self.water_consumption = resources.consumption["residential_building"]["water"]

        # Resource production rates per second
        self.thugoleon_production_rate = resources.production["residential_building"]["thugoleons"]

        # Store adjacent road position
        self.adjacent_road = None
        if world and grid_pos:
            self.find_adjacent_road(world, grid_pos)
            # Spawn a citizen on the adjacent road
            if self.adjacent_road:
                from .citizens import Citizen
                road_tile = world.world[self.adjacent_road[0]][self.adjacent_road[1]]
                # Pass the grid position of the residential building as home_tile
                Citizen(road_tile, world)
                # Store this building's position to help citizens identify their home
                world.residential_buildings.append((grid_pos, self.adjacent_road))

    def update(self):
        now = pg.time.get_ticks()

        # Production of thugoleons every second
        if now - self.production_cooldown >= 1000:
            if (self.resource_manager.resources["electricity"] >= self.electricity_consumption and
                self.resource_manager.resources["water"] >= self.water_consumption):
                    self.resource_manager.resources["thugoleons"] += self.thugoleon_production_rate
                    self.production_cooldown = now

        # Consumption of resources every second
        if now - self.consumption_cooldown >= 1000:
            # Only consume if there are enough resources
            if (self.resource_manager.resources["electricity"] >= self.electricity_consumption and
                self.resource_manager.resources["water"] >= self.water_consumption):

                self.resource_manager.resources["electricity"] -= self.electricity_consumption
                self.resource_manager.resources["water"] -= self.water_consumption
                self.consumption_cooldown = now


class Solar_Panels(Buildings):
    def __init__(self, pos, resource_manager, world=None, grid_pos=None):
        image = pg.image.load("assets/graphics/solar_panels.png")
        self.image = image
        resources = Buildings()
        self.name = "solar_panels"
        self.rect = self.image.get_rect(topleft=pos)
        self.resource_manager = resource_manager
        self.resource_manager.apply_cost_to_resource(self.name)

        # Cooldowns for resource generation and consumption
        self.production_cooldown = pg.time.get_ticks()
        self.consumption_cooldown = pg.time.get_ticks()

        # Resource consumption rates per second
        self.water_consumption = resources.consumption["solar_panels"]["water"]
        self.thugoleon_consumption = resources.consumption["solar_panels"]["thugoleons"]

        # Resource production rates per second
        self.electricity_production_rate = resources.production["solar_panels"]["electricity"]

        # Store adjacent road position
        self.adjacent_road = None
        if world and grid_pos:
            self.find_adjacent_road(world, grid_pos)

    def update(self):
        now = pg.time.get_ticks()

        # Production of resources every second
        if now - self.production_cooldown >= 1000:
            if (self.resource_manager.resources["water"] >= self.water_consumption
                and self.resource_manager.resources["thugoleons"] >= self.thugoleon_consumption):
                    self.resource_manager.resources["electricity"] += self.electricity_production_rate
                    self.production_cooldown = now

        # Consumption of resources every second
        if now - self.consumption_cooldown >= 1000:
            # Only consume if there are enough resources
            if (self.resource_manager.resources["water"] >= self.water_consumption
                and self.resource_manager.resources["thugoleons"] >= self.thugoleon_consumption):
                self.resource_manager.resources["water"] -= self.water_consumption
                self.resource_manager.resources["thugoleons"] -= self.thugoleon_consumption
                self.consumption_cooldown = now

class Water_Treatment_Plant(Buildings):
    def __init__(self, pos, resource_manager, world=None, grid_pos=None):
        image = pg.image.load("assets/graphics/water_treatment_plant.png")
        self.image = image
        resources = Buildings()
        self.name = "water_treatment_plant"
        self.rect = self.image.get_rect(topleft=pos)
        self.resource_manager = resource_manager
        self.resource_manager.apply_cost_to_resource(self.name)

        # Cooldowns for resource generation and consumption
        self.production_cooldown = pg.time.get_ticks()
        self.consumption_cooldown = pg.time.get_ticks()

        # Resource consumption rates per second
        self.electricity_consumption = resources.consumption["water_treatment_plant"]["electricity"]
        self.thugoleon_consumption = resources.consumption["water_treatment_plant"]["thugoleons"]

        # Resource production rates per second
        self.water_production_rate = resources.production["water_treatment_plant"]["water"]

        # Store adjacent road position
        self.adjacent_road = None
        if world and grid_pos:
            self.find_adjacent_road(world, grid_pos)

    def update(self):
        now = pg.time.get_ticks()

        # Production of resources every second
        if now - self.production_cooldown >= 1000:
            if (self.resource_manager.resources["electricity"] >= self.electricity_consumption
                and self.resource_manager.resources["thugoleons"] >= self.thugoleon_consumption):
                    self.resource_manager.resources["water"] += self.water_production_rate
                    self.production_cooldown = now

        # Consumption of resources every second
        if now - self.consumption_cooldown >= 1000:
            # Only consume if there are enough resources
            if (self.resource_manager.resources["electricity"] >= self.electricity_consumption
                and self.resource_manager.resources["thugoleons"] >= self.thugoleon_consumption):
                self.resource_manager.resources["electricity"] -= self.electricity_consumption
                self.resource_manager.resources["thugoleons"] -= self.thugoleon_consumption
                self.consumption_cooldown = now
