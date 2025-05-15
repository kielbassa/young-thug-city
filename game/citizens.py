import pygame as pg
import random
from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder

class Citizen:
    def __init__(self, start_road_tile, world, home_tile):
        """Initialize a citizen object."""
        self.world = world
        self.world.entities.append(self)
        image = pg.image.load("assets/graphics/citizen.png").convert_alpha()
        self.name = "citizen"
        self.image = pg.transform.scale(image, (image.get_width()*2, image.get_height()*2))
        self.start_road_tile = start_road_tile
        self.tile = start_road_tile  # Current tile the citizen is on

        # hour timer
        self.last_hour_checked = -1  # To track hour changes

        # Initialize a placeholder grid for the initial path creation
        self.grid = Grid(matrix=self.world.collision_matrix)

        # destination and home tile
        self.home_tile = home_tile
        self.home_road_pos = start_road_tile["grid"]  # grid position of home's adjacent road
        self.workplace = None
        self.workplace_road_pos = None # grid position of workplace's adjacent road
        self.destination_tile = None  # Current destination

        # Movement and state tracking
        self.path = None  # Current path being followed
        self.path_index = 0  # Current position in the path
        self.is_moving = False  # Whether citizen is currently moving

        self.at_work = False
        self.at_home = True  # Starting at home
        self.in_Building = True
        self.wandering = False

        # Add citizen to the current tile's list
        self.world.citizens[start_road_tile["grid"][0]][start_road_tile["grid"][1]].append(self)
        self.go_home()

    def cleanup(self):
        """Clean up citizen data when removed from the world"""
        # Decrement worker count at workplace if employed
        if self.workplace is not None:
            self.workplace.worker_count = max(0, self.workplace.worker_count - 1) # bounded to 0

        # Remove from current tile's citizen list
        if self.tile and "grid" in self.tile:
            current_grid_pos = self.tile["grid"]
            if current_grid_pos[0] < len(self.world.citizens) and current_grid_pos[1] < len(self.world.citizens[0]):
                if self in self.world.citizens[current_grid_pos[0]][current_grid_pos[1]]:
                    self.world.citizens[current_grid_pos[0]][current_grid_pos[1]].remove(self)

    def find_road(self):
        """Find the road adjacent to the building"""
        # The home_tile is the grid position of the residential building
        self.home_grid_pos = self.home_tile  # Store building position

        # Directly use the building from the world
        x, y = self.home_tile
        building = self.world.buildings[x][y]

        # If the building has an adjacent road, use that for navigation
        if building is not None and building.name == "residential_building" and building.adjacent_road:
            self.home_grid_pos = building.adjacent_road
            return

    def find_workplace(self):
        """Find a factory to work at, prioritizing factories with the lowest worker count"""
        factories = []
        # Look for all factories in the world
        for x in range(self.world.grid_length_x):
            for y in range(self.world.grid_length_y):
                building = self.world.buildings[x][y]
                if building is not None and building.name == "factory":
                    if building.adjacent_road:
                        # Store factory, its position, the adjacent road position, and worker count
                        factories.append((building, (x, y), building.adjacent_road, building.worker_count))

        if factories:
            # Sort factories by worker count (lowest first)
            factories.sort(key=lambda f: f[3])
            # Choose the factory with the lowest worker count
            self.workplace, workplace_pos, self.workplace_road_pos, _ = factories[0]
            # Increment the worker count for the chosen factory
            self.workplace.worker_count += 1
        else:
            # If no factory exists, citizen won't have a workplace
            self.workplace = None
            self.workplace_road_pos = None

    def go_to_work(self):
        """Send the citizen to their workplace"""
        self.create_path(self.workplace_road_pos)

    def go_home(self):
        """Send the citizen back to their home"""
        self.create_path(self.home_road_pos)

    def wander_randomly(self):
        """Make the citizen wander randomly with no specific destination"""
        self.create_path(None)

    def update_collision_matrix(self):
        """updates the world collision matrix"""

    def create_path(self, destination):
        """Creates a path for the citizen or a random one if no destination is provided"""
        self.update_collision_matrix()
        if destination is not None:
            # Create a path to the destination tile

            # Get destination coordinates
            dest_x, dest_y = destination

            # Create grid and find path
            self.grid = Grid(matrix=self.world.collision_matrix)
            self.start = self.grid.node(self.tile["grid"][0], self.tile["grid"][1])
            self.end = self.grid.node(dest_x, dest_y)
            finder = AStarFinder(diagonal_movement=DiagonalMovement.never)
            path, runs = finder.find_path(self.start, self.end, self.grid)

            # Check if path is valid and long enough to follow
            if path and len(path) > 1:  # Need at least start and one more node
                self.path_index = 0
                self.path = path
                self.destination_tile = destination
                return

            # If path to destination failed, clear destination if it's our current destination
            if hasattr(self, 'destination_tile') and destination == self.destination_tile:
                self.destination_tile = None
        else:
            # create a random path to wander
            available_roads = []
            # Find all available roads within a certain radius
            current_x, current_y = self.tile["grid"]
            search_radius = 10

            for x in range(max(0, current_x - search_radius), min(self.world.grid_length_x, current_x + search_radius)):
                for y in range(max(0, current_y - search_radius), min(self.world.grid_length_y, current_y + search_radius)):
                    if self.world.roads[x][y] is not None:
                        available_roads.append((x, y))

            if available_roads:
                # Choose a random road to walk to
                random_dest = random.choice(available_roads)

                # Create path to the random destination
                self.grid = Grid(matrix=self.world.collision_matrix)
                self.start = self.grid.node(self.tile["grid"][0], self.tile["grid"][1])
                self.end = self.grid.node(random_dest[0], random_dest[1])
                finder = AStarFinder(diagonal_movement=DiagonalMovement.never)
                path, runs = finder.find_path(self.start, self.end, self.grid)

                if path and len(path) > 1:
                    self.path_index = 0
                    self.path = path
                    self.destination_tile = random_dest

    def change_tile(self, new_tile):
        """Change the citizen's tile"""
        # Get current position before removing
        current_grid_pos = self.tile["grid"]

        # Remove citizen from current tile
        if self in self.world.citizens[current_grid_pos[0]][current_grid_pos[1]]:
            self.world.citizens[current_grid_pos[0]][current_grid_pos[1]].remove(self)

        # Validate new tile coordinates are within bounds
        if (0 <= new_tile[0] < self.world.grid_length_x and
            0 <= new_tile[1] < self.world.grid_length_y and
            self.world.roads[new_tile[0]][new_tile[1]] is not None):
            # Valid move - update citizen position
            self.world.citizens[new_tile[0]][new_tile[1]].append(self)
            self.tile = self.world.world[new_tile[0]][new_tile[1]]
            self.is_moving = True
        else:
            # If tile has no road or is out of bounds, stay in current tile
            self.world.citizens[self.tile["grid"][0]][self.tile["grid"][1]].append(self)
            # Create a new path since the current one is invalid
            self.path = None
            self.create_path(None)

    def update(self):
        # citizen movement logic
        if hasattr(self, 'path') and self.path and hasattr(self, 'path_index'):
            # If we have a valid path and haven't reached the end
            if self.path_index < len(self.path) - 1:
                # Get next position in path
                next_pos = self.path[self.path_index + 1]

                # Move to the next tile
                self.change_tile(next_pos)

                # Increment path index
                self.path_index += 1

                # Check if we've reached our destination
                if self.path_index >= len(self.path) - 1:
                    # Arrived at destination
                    self.is_moving = False

                    # Handle arrival at specific destinations
                    if hasattr(self, 'destination_tile'):
                        if self.destination_tile == self.workplace_road_pos:
                            self.at_work = True
                            self.at_home = False
                            self.wandering = False
                        elif self.destination_tile == self.home_road_pos:
                            self.at_home = True
                            self.at_work = False
                            self.wandering = False

            # If wandering and reached end of current path, create new random path
            elif self.wandering and self.path_index >= len(self.path) - 1:
                self.create_path(None)

        # citizen scheduling
        game_time = self.world.hud.game_time
        # Only process schedule when the hour changes
        if game_time != self.last_hour_checked:
            self.last_hour_checked = game_time
            match game_time:
                case 7:
                    # head to work and stay there
                    print("DEBUG: Citizen is going to work")
                    self.find_workplace()
                    if self.workplace is not None: # check if finding the workplace was successful
                        self.at_work = False
                        self.at_home = False
                        self.wandering = False
                        self.go_to_work()
                    else:
                        print("DEBUG: Citizen couldn't find workplace, wandering instead")
                        self.at_work = False
                        self.at_home = False
                        self.wandering = True
                        self.wander_randomly()
                case 16:
                    # wander randomly
                    print("DEBUG: Citizen leaving work, wandering randomly")
                    self.at_work = False
                    self.at_home = False
                    self.wandering = True
                    self.wander_randomly()
                case 20:
                    # go home for the night and stay there
                    print("DEBUG: Citizen going home for the night")
                    self.at_work = False
                    self.at_home = False
                    self.wandering = False
                    self.go_home()
