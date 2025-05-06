import pygame as pg
from .settings import *

class ResourceManager:
    def __init__(self):
        self.ELECTRICITY_MULTIPLIER = ELECTRICITY_MULTIPLIER
        self.MOISTURE_MULTIPLIER = MOISTURE_MULTIPLIER

        # starting resources
        self.resources = {
            "electricity": 100,
            "water": 100,
            "thugoleons": 1000,
            "citizens": 0
        }

        # costs
        self.costs = {
            "factory": {"thugoleons": 10},
            "residential_building": {"thugoleons": 5, "citizens": -2},
            "solar_panels": {"thugoleons": 100},
            "water_treatment_plant": {"thugoleons": 100},
            "road": {"thugoleons": 1}
        }

    def apply_cost_to_resource(self, building):
        for resource, cost in self.costs[building].items():
            self.resources[resource] -= cost

    def is_affordable(self, building):
        affordable = True
        for resource, cost in self.costs[building].items():
            if self.resources[resource] < cost:
                affordable = False
                break
        return affordable
