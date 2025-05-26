import pygame as pg
import random
from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder

class Citizen:
    def __init__(self, tile, world):
        """Initialize a citizen object."""
        self.world = world
        self.world.entities.append(self) # add itself to entities for updating

        #randomize which out of 5 images to use
        image = pg.image.load(f"assets/graphics/citizen{random.randint(1, 5)}.png").convert_alpha()
        self.name = f"citizen_{random.randint(1, 1000)}"
        self.image = pg.transform.scale(image, (image.get_width()*2, image.get_height()*2))
        self.tile = tile

        # pathfinding
        self.world.citizens[tile["grid"][0]][tile["grid"][1]].append(self)

        # Movement interpolation
        self.movement_speed = 0.1  # Adjust this to control movement speed, is glitchy
        self.current_pos = pg.Vector2(tile["render_pos"][0], tile["render_pos"][1])
        self.target_pos = pg.Vector2(tile["render_pos"][0], tile["render_pos"][1])
        self.is_moving = False

        # Initialize a placeholder grid for the initial path creation
        self.grid = Grid(matrix=self.world.collision_matrix)

        # initialize schedule variables
        self.home_grid_pos = tile["grid"]
        self.workplace = None
        self.workplace_grid_pos = None
        self.at_work = False
        self.contributed_to_worker_count = False
        self.at_home = True
        self.is_visible = False
        self.wandering = False

        # movement and schedule timers
        self.move_timer = pg.time.get_ticks()
        self.last_hour_checked = - 1

        self.create_path(tile["grid"])

    def pathfinder(self, x, y, origin):
        # Check if the factory is reachable for the citizen
        road_tiles = []
        for i in range(self.world.grid_length_x):
            for j in range(self.world.grid_length_y):
                # Check if tile has a road on it
                if self.world.roads[i][j] is not None:
                    road_tiles.append((i, j))

        # Create temporary collision matrix
        temp_collision_matrix = [row[:] for row in self.world.collision_matrix]

        # Mark all non-road tiles as non-walkable
        for i in range(self.world.grid_length_x):
            for j in range(self.world.grid_length_y):
                if self.world.roads[i][j] is None:
                    temp_collision_matrix[j][i] = 0

        # Exception for current citizen's position
        current_pos = self.tile["grid"]
        temp_collision_matrix[current_pos[1]][current_pos[0]] = 1

        self.grid = Grid(matrix=temp_collision_matrix) # collision matrix
        self.start = self.grid.node(self.tile["grid"][0], self.tile["grid"][1])
        self.end = self.grid.node(x, y) # destination
        finder = AStarFinder(diagonal_movement=DiagonalMovement.never)
        path, runs = finder.find_path(self.start, self.end, self.grid)
        return [path, runs]


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

        # If the citizen already has a workplace, update the previous workplace's worker count
        if self.workplace is not None:
            self.workplace.worker_count = max(0, self.workplace.worker_count - 1)

        if factories:
            # Sort factories by worker count (lowest first)
            factories.sort(key=lambda f: f[3])
            # Choose the factory with the lowest worker count
            self.workplace, workplace_pos, self.workplace_grid_pos, _ = factories[0]

            path, runs = self.pathfinder(self.workplace_grid_pos[0], self.workplace_grid_pos[1], self.tile["grid"])

            if len(path) > 0: # if path is valid
                # print(f"{self.name} valid path to workplace of length {len(path)}")
                if self.workplace.worker_count < self.workplace.worker_max_capacity:
                    self.workplace.worker_count += 1
                else:
                    self.workplace, self.workplace_grid_pos = None, None
            else:
                print(f"{self.name} has no valid path to workplace {self.workplace_grid_pos}")
                self.workplace, self.workplace_grid_pos = None, None
        else:
            # If no factory exists, citizen won't have a workplace
            self.workplace = None
            self.workplace_grid_pos = None

    def create_path(self, destination):
        """Create a path to the destination tile or a random one if no destination is set"""
        # find road tiles
        road_tiles = []
        for i in range(self.world.grid_length_x):
            for j in range(self.world.grid_length_y):
                # Check if tile has a road on it
                if self.world.roads[i][j] is not None:
                    road_tiles.append((i, j))
        # If no road tiles are available, stay in place
        if road_tiles is None:
            self.change_tile(self.tile) # stay in place

        if destination is not None:
            x, y = destination # set the x and y coordinates to the destination
        else:
            # Choose a random road tile as destination
            x, y = random.choice(road_tiles)

        path, runs = self.pathfinder(x, y, self.tile["grid"])

        if len(path) > 0: # if path is valid
            self.path_index = 0
            self.path = path
            return

    def change_tile(self, new_tile):
        current_grid_pos = self.tile["grid"]
        # Remove citizen from current tile
        if self.world.roads[new_tile[0]][new_tile[1]] is not None:
            self.world.citizens[current_grid_pos[0]][current_grid_pos[1]].remove(self) # remove citizen from current grid
            self.is_moving = True
            if self.world.citizens[new_tile[0]][new_tile[1]] is None:
                self.world.citizens[new_tile[0]][new_tile[1]] = []
            self.world.citizens[new_tile[0]][new_tile[1]].append(self) # add citizen to new tile
            self.tile = self.world.world[new_tile[0]][new_tile[1]]
            self.target_pos = pg.Vector2(self.tile["render_pos"][0], self.tile["render_pos"][1])
            # print(f"{self.name} moved to new tile : {current_grid_pos}->{new_tile}")
        else:
            print(f"{self.name} couldn't move to new tile, created a new path to {new_tile} instead")
            self.create_path(new_tile)  # If going to the next tile fails, find a path there

    def schedule(self, game_time):
        match game_time:
            case 7: # at 7 go to work
                self.at_home = False
                self.is_visible = True # make the citizen visible
                self.wandering = False
                self.find_workplace()
                if self.workplace:
                    # print(f"Workplace found at {self.workplace_grid_pos}, creating path")
                    self.contributed_to_worker_count = False
                    self.create_path(self.workplace_grid_pos)
                    self.at_work = True
                else:
                    print(f"{self.name}, Workplace not found")
                    self.wandering = True
                    self.create_path(None)
            case 16: # at 16 leave work and start wandering around
                self.at_work = False
                if self.workplace:
                    self.workplace.worker_count_current -= 1
                self.is_visible = True # make the citizen visible
                self.wandering = True # set the wandering flag to True
                self.create_path(None) # create a path with no destination
            case 20: # at 20 go home
                self.at_home = True
                self.wandering = False
                self.create_path(self.home_grid_pos)

    def update(self):
        now = pg.time.get_ticks()
        game_time = self.world.hud.game_time

        # only process schedule when the hour changes
        if game_time != self.last_hour_checked:
            self.last_hour_checked = game_time
            self.schedule(game_time)

        # Handle movement interpolation
        if self.is_moving:
            direction = self.target_pos - self.current_pos
            if direction.length() > 1:  # If not close enough to target
                direction = direction.normalize()
                self.current_pos += direction * self.movement_speed * self.world.clock.get_time()
            else: # don't move
                self.current_pos = self.target_pos.copy()
                self.is_moving = False

        if now - self.move_timer > 500 and not self.is_moving:
            # Check if we have a valid path and haven't reached the end
            if self.path and self.path_index < len(self.path):
                node = self.path[self.path_index]
                new_pos = [node.x, node.y]

                # Only move if the destination has a road
                if self.world.roads[new_pos[0]][new_pos[1]] is not None:
                    self.change_tile(new_pos)
                    # print(f"Path of length {len(self.path)}, done {self.path_index}")
                    self.path_index += 1
                else:
                    # If destination has no road, find new path
                    self.create_path(None)
                self.move_timer = now

            # Reaching destination
            if self.path_index == len(self.path):
                if self.wandering: # if the citizen is wandering, create a new random path
                    self.create_path(None)
                elif not self.is_moving:
                    self.is_visible = False
                    if self.at_work and self.workplace and not self.contributed_to_worker_count:
                        self.workplace.worker_count_current += 1
                        self.contributed_to_worker_count = True
