from .settings import ELECTRICITY_MULTIPLIER, MOISTURE_MULTIPLIER

class ResourceManager:
    def __init__(self):
        self.ELECTRICITY_MULTIPLIER = ELECTRICITY_MULTIPLIER
        self.MOISTURE_MULTIPLIER = MOISTURE_MULTIPLIER

        # starting resources
        self.resources = {
            "electricity": 100,
            "water": 100,
            "thugoleons": 1000000,
            "citizens": 0
        }

        # costs
        self.costs = {
            "factory": {"thugoleons": 10000},
            "residential_building": {"thugoleons": 5000, "citizens": -1},
            "solar_panels": {"thugoleons": 180000},
            "water_treatment_plant": {"thugoleons": 220000},
            "road": {"thugoleons": 1000}
        }

    def apply_cost_to_resource(self, building):
        """Apply the cost of a building to the global resources."""
        for resource, cost in self.costs[building].items():
            self.resources[resource] -= cost

    def is_affordable(self, building):
        """Check if the player can afford a building."""
        affordable = True
        for resource, cost in self.costs[building].items():
            if self.resources[resource] < cost:
                affordable = False
                break
        return affordable
