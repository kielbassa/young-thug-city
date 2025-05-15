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

        # pathfinding
        self.move_timer = pg.time.get_ticks()

        # Movement interpolation
        self.movement_speed = 0.1  # Adjust this to control movement speed
        self.current_pos = pg.Vector2(tile["render_pos"][0], tile["render_pos"][1])
        self.target_pos = pg.Vector2(tile["render_pos"][0], tile["render_pos"][1])
        self.is_moving = False

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

        self.create_path()

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

        # Fallback: set the home grid position to the same as current position
        # This ensures citizen at least has somewhere to go
        self.home_grid_pos = self.tile["grid"]

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
        """Send citizen to workplace"""
        if self.workplace_grid_pos:
            # Clear any existing path
            self.in_Building = False
            self.path = None
            self.path_index = 0
            self.destination_tile = None

            # Set workplace as new destination
            self.set_destination(self.workplace_grid_pos)
            return True
        return False

    def go_home(self):
        """Send citizen back home"""
        if self.home_grid_pos:
            # Clear any existing path
            self.in_Building = False
            self.path = None
            self.path_index = 0
            self.destination_tile = None

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

        # Remove citizen from current tile temporarily
        self.world.citizens[current_grid_pos[0]][current_grid_pos[1]] = None

        # Check if the new tile is valid and not occupied
        if self.world.roads[new_tile[0]][new_tile[1]] is not None:
            # Valid move - update citizen position
            self.world.citizens[new_tile[0]][new_tile[1]] = self
            self.tile = self.world.world[new_tile[0]][new_tile[1]]
            self.is_moving = True
        else:
            # If tile is occupied or has no road, stay in current tile
            self.world.citizens[self.tile["grid"][0]][self.tile["grid"][1]] = self
            self.create_path()  # Find a new path

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
                if self.workplace_grid_pos:
                    self.at_work = False  # Not yet at work, but going there
                    self.go_to_work()

            # 8:00 AM to 4:00 PM - At work
            elif game_time >= 8 and game_time < 16:
                # If at workplace, stay
                if self.workplace_grid_pos and self.tile["grid"][0] == self.workplace_grid_pos[0] and self.tile["grid"][1] == self.workplace_grid_pos[1]:
                    self.at_work = True
                    # Clear destination to prevent leaving work
                    self.destination_tile = None
                    self.path = None

                # If not at workplace or going there, send to work
                elif self.workplace_grid_pos and not self.at_work:
                    # Force going to work regardless of current path
                    self.go_to_work()

            # 16:00 (4:00 PM) - End work day, start wandering
            elif game_time == 16:
                self.at_work = False
                self.in_Building = False
                # Just let the citizen wander by not setting a specific destination
                self.destination_tile = None
                self.path = None
                self.wander_randomly()

            # 20:00 (8:00 PM) - Head home for the night
            elif game_time == 20:
                # Force going home regardless of current activity
                if self.go_home():
                    # Set at_home flag to keep them at home
                    self.at_home = True
                    # Clear any other destination
                    self.destination_tile = self.home_grid_pos

            # 7:00 AM - Allow leaving home
            elif game_time == 7:
                # Reset at_home flag so they can leave
                self.at_home = False

        # Handle movement interpolation
        if self.is_moving:
            direction = self.target_pos - self.current_pos
            if direction.length() > 1:  # If not close enough to target
                direction = direction.normalize()
                self.current_pos += direction * self.movement_speed * self.world.clock.get_time()
            else:
                self.current_pos = self.target_pos.copy()
                self.is_moving = False

        if now - self.move_timer > 500 and not self.is_moving:
            # Don't move if at work during work hours or at home during night hours
            work_hours = game_time >= 8 and game_time < 16
            night_hours = game_time >= 20 or game_time < 7

            at_workplace = (self.workplace_grid_pos and
                            self.tile["grid"][0] == self.workplace_grid_pos[0] and
                            self.tile["grid"][1] == self.workplace_grid_pos[1])

            at_home = (self.home_grid_pos and
                        self.tile["grid"][0] == self.home_grid_pos[0] and
                        self.tile["grid"][1] == self.home_grid_pos[1])

            # Force stay at workplace during work hours
            if at_workplace and work_hours:
                self.at_work = True
                self.move_timer = now
                self.destination_tile = None
                self.path = None
                return

            # Force stay at home during night hours
            if at_home and night_hours:
                self.at_home = True
                self.move_timer = now
                self.destination_tile = None
                self.path = None
                return

            # If it's night time and not at home, force going home
            elif night_hours and not at_home and not self.destination_tile == self.home_grid_pos:
                self.go_home()
                return

            # Check if we have a valid path and haven't reached the end
            if self.path and self.path_index < len(self.path):
                node = self.path[self.path_index]
                new_pos = [node.x, node.y]

                # Only move if the destination has a road
                if self.world.roads[new_pos[0]][new_pos[1]] is not None:
                    self.change_tile(new_pos)
                    self.path_index += 1

                    # Create new path when reaching destination
                    if self.path_index >= len(self.path):
                        # Check if we were heading to a specific destination
                        if self.destination_tile:
                            # We've reached our destination
                            dest_x, dest_y = self.destination_tile
                            reached_destination = self.tile["grid"][0] == dest_x and self.tile["grid"][1] == dest_y

                            # Clear the destination now that we've reached it
                            self.destination_tile = None
                            self.in_Building = True
                            # Special case for workplace during work hours
                            if reached_destination and self.workplace_grid_pos:
                                at_workplace = (self.tile["grid"][0] == self.workplace_grid_pos[0] and
                                               self.tile["grid"][1] == self.workplace_grid_pos[1])

                                if at_workplace and hasattr(self.world.hud, 'game_time'):
                                    work_hours = self.world.hud.game_time >= 8 and self.world.hud.game_time < 16
                                    if work_hours:
                                        self.at_work = True
                                        self.move_timer = now
                                        return

                            # Special case for arriving home
                            if reached_destination and self.home_grid_pos:
                                at_home = (self.tile["grid"][0] == self.home_grid_pos[0] and
                                          self.tile["grid"][1] == self.home_grid_pos[1])

                                if at_home:
                                    # Check if it's night time
                                    if game_time >= 20 or game_time < 7:
                                        # At home during night hours - stay home until morning
                                        self.at_home = True
                                        return

                        # Create a new random path if not at work and not at home during night
                        if not self.at_work and not self.at_home:
                            self.create_path()
                else:
                    # If destination has no road, find new path
                    self.create_path()

                self.move_timer = now
