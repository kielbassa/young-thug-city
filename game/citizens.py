import pygame as pg
import random
from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder

class Citizen:
    def __init__(self, tile, world, home_tile):
        """Initialize a citizen object."""
        self.world = world
        self.world.entities.append(self)
        image = pg.image.load("assets/graphics/citizen.png").convert_alpha()
        self.name = "citizen"
        self.image = pg.transform.scale(image, (image.get_width()*2, image.get_height()*2))
        self.tile = tile

        # pathfinding
        self.world.citizens[tile["grid"][0]][tile["grid"][1]] = self
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
        self.home_grid_pos = None  # Will store the grid position of home's adjacent road
        self.workplace = None
        self.workplace_grid_pos = None
        self.at_work = False
        self.at_home = False
        self.in_Building = False
        self.destination_tile = None
        self.last_hour_checked = -1  # To track hour changes

        # Find the adjacent road to home for returning home
        self.find_home_road()

        # Find a factory to work at
        self.find_workplace()

        self.create_path()

    def find_home_road(self):
        """Find the road adjacent to home for returning later"""
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
        """Find a factory to work at"""
        factories = []

        # Look for all factories in the world
        for x in range(self.world.grid_length_x):
            for y in range(self.world.grid_length_y):
                building = self.world.buildings[x][y]
                if building is not None and building.name == "factory":
                    if building.adjacent_road:
                        # Store factory, its position, and the adjacent road position
                        factories.append((building, (x, y), building.adjacent_road))

        if factories:
            # Choose a random factory as workplace
            self.workplace, workplace_pos, self.workplace_grid_pos = random.choice(factories)
        else:
            # If no factory exists, citizen won't have a workplace
            self.workplace = None
            self.workplace_grid_pos = None

    def set_destination(self, destination_tile):
        self.destination_tile = destination_tile
        self.create_path()

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

            # Reset flags
            self.at_work = False

            # Set home as new destination with high priority
            self.set_destination(self.home_grid_pos)
            return True
        return False

    def create_path(self):
        # Check if it's night time and not heading home
        if hasattr(self.world.hud, 'game_time'):
            game_time = self.world.hud.game_time
            if (game_time >= 20 or game_time < 7) and self.destination_tile != self.home_grid_pos:
                # It's night time and not going home - force going home
                self.go_home()
        if self.destination_tile is not None:
            # Create a path to the destination tile
            # Create temporary collision matrix that includes other citizens
            temp_collision_matrix = [row[:] for row in self.world.collision_matrix]

            # Mark positions of all citizens as non-walkable (except self)
            for i in range(self.world.grid_length_x):
                for j in range(self.world.grid_length_y):
                    if self.world.citizens[i][j] is not None and self.world.citizens[i][j] != self:
                        temp_collision_matrix[j][i] = 0

            # Mark all non-road tiles as non-walkable
            for i in range(self.world.grid_length_x):
                for j in range(self.world.grid_length_y):
                    if self.world.roads[i][j] is None:
                        temp_collision_matrix[j][i] = 0

            # Exception for current citizen's position
            current_pos = self.tile["grid"]
            temp_collision_matrix[current_pos[1]][current_pos[0]] = 1

            # Ensure destination is walkable
            dest_x, dest_y = self.destination_tile
            if 0 <= dest_y < len(temp_collision_matrix) and 0 <= dest_x < len(temp_collision_matrix[0]):
                temp_collision_matrix[dest_y][dest_x] = 1
            else:
                # Invalid destination
                self.destination_tile = None
                self.wander_randomly()
                return

            # Create grid and find path
            self.grid = Grid(matrix=temp_collision_matrix)
            self.start = self.grid.node(self.tile["grid"][0], self.tile["grid"][1])
            self.end = self.grid.node(dest_x, dest_y)
            finder = AStarFinder(diagonal_movement=DiagonalMovement.never)
            path, runs = finder.find_path(self.start, self.end, self.grid)

            if len(path) > 0:
                self.path_index = 0
                self.path = path
                return
            # If path to destination failed, clear destination
            self.destination_tile = None
        # If no destination or path failed, wander randomly
        self.wander_randomly()

    def wander_randomly(self):
        """Create a random path when no specific destination"""
        # Check if it's night time
        if hasattr(self.world.hud, 'game_time'):
            game_time = self.world.hud.game_time
            if game_time >= 20 or game_time < 7:
                # It's night time - go home instead of wandering
                self.go_home()
                return

        max_attempts = 50
        attempts = 0

        while attempts < max_attempts:
            # find road tiles
            road_tiles = []
            for i in range(self.world.grid_length_x):
                for j in range(self.world.grid_length_y):
                    # Check if tile has a road on it and is not occupied by another citizen
                    if self.world.roads[i][j] is not None and self.world.citizens[i][j] is None:
                        road_tiles.append((i, j))

            # If no road tiles are available, stay in place
            if not road_tiles:
                break

            # Choose a random road tile as destination
            x, y = random.choice(road_tiles)

            # Create temporary collision matrix that includes other citizens
            temp_collision_matrix = [row[:] for row in self.world.collision_matrix]

            # Mark positions of all citizens as non-walkable
            for i in range(self.world.grid_length_x):
                for j in range(self.world.grid_length_y):
                    if self.world.citizens[i][j] is not None:
                        temp_collision_matrix[j][i] = 0

            # Mark all road tiles as walkable
            for i in range(self.world.grid_length_x):
                for j in range(self.world.grid_length_y):
                    if self.world.roads[i][j] is not None:
                        temp_collision_matrix[j][i] = 1

            # Exception for current citizen's position
            current_pos = self.tile["grid"]
            temp_collision_matrix[current_pos[1]][current_pos[0]] = 1

            self.grid = Grid(matrix=temp_collision_matrix)
            self.start = self.grid.node(self.tile["grid"][0], self.tile["grid"][1])
            self.end = self.grid.node(x, y)
            finder = AStarFinder(diagonal_movement=DiagonalMovement.never)
            path, runs = finder.find_path(self.start, self.end, self.grid)

            if len(path) > 0:
                self.path_index = 0
                self.path = path
                return

            attempts += 1
        # If no path is found after max attempts, stay in place
        self.grid = Grid(matrix=self.world.collision_matrix)
        self.path = [self.grid.node(self.tile["grid"][0], self.tile["grid"][1])]
        self.path_index = 0

    def change_tile(self, new_tile):
        # Get current position before removing
        current_grid_pos = self.tile["grid"]

        # Remove citizen from current tile temporarily
        self.world.citizens[current_grid_pos[0]][current_grid_pos[1]] = None

        # Check if the new tile is valid and not occupied
        if (self.world.citizens[new_tile[0]][new_tile[1]] is None and
            self.world.roads[new_tile[0]][new_tile[1]] is not None):
            # Valid move - update citizen position
            self.world.citizens[new_tile[0]][new_tile[1]] = self
            self.tile = self.world.world[new_tile[0]][new_tile[1]]
            self.target_pos = pg.Vector2(self.tile["render_pos"][0], self.tile["render_pos"][1])
            self.is_moving = True
        else:
            # If tile is occupied or has no road, stay in current tile
            self.world.citizens[self.tile["grid"][0]][self.tile["grid"][1]] = self
            self.create_path()  # Find a new path

    def update(self):
        now = pg.time.get_ticks()

        # Check game time and manage work schedule
        if hasattr(self.world.hud, 'game_time'):
            game_time = self.world.hud.game_time

            # Only process schedule when the hour changes
            if game_time != self.last_hour_checked:
                self.last_hour_checked = game_time

                # 7:00 AM - Head to work
                if game_time == 7:
                    if self.workplace == None:
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

                # If we've reached the workplace during work hours, stay there
                if hasattr(self.world.hud, 'game_time'):
                    work_hours = self.world.hud.game_time >= 8 and self.world.hud.game_time < 16
                    at_workplace = (self.workplace_grid_pos and
                                    self.tile["grid"][0] == self.workplace_grid_pos[0] and
                                    self.tile["grid"][1] == self.workplace_grid_pos[1])

                    if at_workplace and work_hours:
                        self.at_work = True
                        # Clear destination to stay put
                        self.destination_tile = None
                        self.path = None

        if now - self.move_timer > 1000 and not self.is_moving:
            # Don't move if at work during work hours or at home during night hours
            if hasattr(self.world.hud, 'game_time'):
                game_time = self.world.hud.game_time
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
                            old_destination = self.destination_tile
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
                                    if hasattr(self.world.hud, 'game_time'):
                                        game_time = self.world.hud.game_time
                                        if game_time >= 20 or game_time < 7:
                                            # At home during night hours - stay home until morning
                                            self.at_home = True
                                            # Extend time before next movement attempt
                                            self.move_timer = now + random.randint(5000, 10000)
                                            return

                                    # If daytime, just wait longer before wandering
                                    self.move_timer = now + random.randint(2000, 5000)

                        # Create a new random path if not at work and not at home during night
                        if not self.at_work and not self.at_home:
                            self.create_path()
                else:
                    # If destination has no road, find new path
                    self.create_path()

                self.move_timer = now
