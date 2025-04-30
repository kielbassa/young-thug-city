import pygame as pg

class ResourceManager:
    def __init__(self):

        # resources
        self.resources = {
            "electricity": 100,
            "water": 50,
            "thugoleons": 25
        }

        # costs
        self.costs = {
            "factory": {"thugoleons": 10},
            "residential_building": {"thugoleons": 5},
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
