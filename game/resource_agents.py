import pygame as pg
import random
from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder

class ResourceAgent:
    def __init__(self, origin_name, origin_pos, road_tile, world, resource_type):
        """Initialize a resource agent object."""
        self.world = world
        self.world.entities.append(self) # add itself to entities for updating
        if resource_type == "electricity":
            image = pg.image.load("assets/graphics/agent_electricity.png").convert_alpha()
        elif resource_type == "water":
            image = pg.image.load("assets/graphics/agent_water.png").convert_alpha()
        self.name = f"agent_{random.randint(1, 1000)}"
        self.image = pg.transform.scale(image, (image.get_width()*2, image.get_height()*2))
        self.road_tile = road_tile

        # resource carrying
        self.resource_type = resource_type
        self.carried_amount = 100
        self.max_capacity = 160
        self.single_dropoff_amount = 24
        self.replenishing = False

        # pathfinding
        self.world.resource_agents[road_tile["grid"][0]][road_tile["grid"][1]].append(self)

        # Movement interpolation
        self.movement_speed = 0.1  # Adjust this to control movement speed
        self.current_pos = pg.Vector2(road_tile["render_pos"][0], road_tile["render_pos"][1])
        self.target_pos = pg.Vector2(road_tile["render_pos"][0], road_tile["render_pos"][1])
        self.is_moving = False

        # Initialize a placeholder grid for the initial path creation
        self.grid = Grid(matrix=self.world.collision_matrix)

        # initialize schedule variables
        self.origin_pos = origin_pos
        self.origin_grid_pos = road_tile["grid"]
        self.origin = self.world.buildings[origin_pos[0]][origin_pos[1]]
        self.origin_name = origin_name
        self.destination = None
        self.destination_grid_pos = None

        # movement timers
        self.move_timer = pg.time.get_ticks()

    def pathfinder(self, x, y, origin):
        ## Check if the destination is reachable for the agent
        road_road_tiles = []
        for i in range(self.world.grid_length_x):
            for j in range(self.world.grid_length_y):
                # Check if the tile has a road on it
                if self.world.roads[i][j] is not None:
                    road_road_tiles.append((i, j))

        # Create temporary collision matrix
        temp_collision_matrix = [row[:] for row in self.world.collision_matrix]

        # Mark all non-road road_tiles as non-walkable
        for i in range(self.world.grid_length_x):
            for j in range(self.world.grid_length_y):
                if self.world.roads[i][j] is None:
                    temp_collision_matrix[j][i] = 0

        # Exception for current agent's position
        current_pos = self.road_tile["grid"]
        temp_collision_matrix[current_pos[1]][current_pos[0]] = 1

        self.grid = Grid(matrix=temp_collision_matrix) # collision matrix
        self.start = self.grid.node(self.road_tile["grid"][0], self.road_tile["grid"][1])
        self.end = self.grid.node(x, y) # destination
        finder = AStarFinder(diagonal_movement=DiagonalMovement.never)
        path, runs = finder.find_path(self.start, self.end, self.grid)
        return [path, runs]


    def find_destination(self):
        """Find a building to go to, prioritize ones with the lowest resource"""
        destinations = []
        # Look for all buildings in the world
        for x in range(self.world.grid_length_x):
            for y in range(self.world.grid_length_y):
                building = self.world.buildings[x][y]
                if building is not None and building.name != self.origin_name:
                    if building.adjacent_road:
                        # Store factory, its position, the adjacent road position, and current resources
                        destinations.append((building, (x, y), building.adjacent_road, building.electricity, building.water))

        if destinations:
            # Sort buildings by resource
            if self.resource_type == "electricity":
                destinations.sort(key=lambda f: f[3])
            elif self.resource_type == "water":
                destinations.sort(key=lambda f: f[4])
            # Choose the building with the lowest resource count
            self.destination, destination_pos, self.destination_grid_pos, _, _ = destinations[0]

            path, runs = self.pathfinder(self.destination_grid_pos[0], self.destination_grid_pos[1], self.road_tile["grid"])

            if len(path) <= 0: # if path is invalid
                # print(f"{self.name} has no valid path to destination {self.destination_grid_pos}")
                self.destination, self.destination_grid_pos = None, None
            else:
                pass
                # print(f"{self.name} valid path to destination of length {len(path)}")

        else:
            # If no destination exists, agent won't have a destination
            print(f"{self.name} no destinations found")
            self.destination = None
            self.destination_grid_pos = None

    def create_path(self, destination):
        """Create a path to the destination road_tile or a random one if no destination is set"""
        # find road road_tiles
        road_road_tiles = []
        for i in range(self.world.grid_length_x):
            for j in range(self.world.grid_length_y):
                # Check if road_tile has a road on it
                if self.world.roads[i][j] is not None:
                    road_road_tiles.append((i, j))
        # If no road road_tiles are available, stay in place
        if road_road_tiles is None:
            self.change_road_tile(self.road_tile) # stay in place

        if destination is not None:
            x, y = destination # set the x and y coordinates to the destination
        else:
            # Choose a random road road_tile as destination
            x, y = random.choice(road_road_tiles)

        path, runs = self.pathfinder(x, y, self.road_tile["grid"])

        if len(path) > 0: # if path is valid
            self.path_index = 0
            self.path = path
            return

    def change_road_tile(self, new_road_tile):
        current_grid_pos = self.road_tile["grid"]
        # Remove agent from current road_tile
        if self.world.roads[new_road_tile[0]][new_road_tile[1]] is not None:
            self.world.resource_agents[current_grid_pos[0]][current_grid_pos[1]].remove(self) # remove agent from current grid
            self.is_moving = True
            if self.world.resource_agents[new_road_tile[0]][new_road_tile[1]] is None:
                self.world.resource_agents[new_road_tile[0]][new_road_tile[1]] = []
            self.world.resource_agents[new_road_tile[0]][new_road_tile[1]].append(self) # add agent to new tile
            self.road_tile = self.world.world[new_road_tile[0]][new_road_tile[1]]
            self.target_pos = pg.Vector2(self.road_tile["render_pos"][0], self.road_tile["render_pos"][1])
            # print(f"{self.name} moved to new road_tile : {current_grid_pos}->{new_road_tile}")
        else:
            print(f"{self.name} couldn't move to new road_tile, created a new path to {new_road_tile} instead")
            self.create_path(new_road_tile)  # If going to the next road_tile fails, find a path there

    def update(self):
        if self.destination is None:
            self.find_destination()
            self.create_path(self.destination_grid_pos)
        now = pg.time.get_ticks()

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
                    self.change_road_tile(new_pos)
                    # print(f"Path of length {len(self.path)}, done {self.path_index}, carrying {self.carried_amount} {self.resource_type}")
                    self.path_index += 1
                else:
                    # If destination has no road, find new path
                    self.create_path(self.destination_grid_pos)
                self.move_timer = now

            # Reaching destination
            if self.path_index == len(self.path) and self.is_moving:
                if self.destination:
                    if self.replenishing:
                        self.origin = self.world.buildings[self.origin_pos[0]][self.origin_pos[1]]
                        # print(f"{self.name} reached the origin road_tile")
                        self.destination = None
                        self.destination_grid_pos = None
                        # replenish resource when reached the origin road_tile
                        if self.resource_type == "electricity":
                            resource_portion = min(getattr(self.origin, 'electricity'), self.max_capacity - self.carried_amount)
                            self.carried_amount += resource_portion
                            self.origin.electricity -= resource_portion
                            # print(f"{self.name} replenished {resource_portion} electricity, now carrying {self.carried_amount}")
                        elif self.resource_type == "water":
                            resource_portion = min(getattr(self.origin, 'water'), self.max_capacity - self.carried_amount)
                            self.carried_amount += resource_portion
                            self.origin.water -= resource_portion
                            # print(f"{self.name} replenished {resource_portion} water, now carrying {self.carried_amount}")
                        self.replenishing = False
                        self.find_destination()  # find a new destination and create a path there
                        if self.destination and self.destination_grid_pos:
                            self.create_path(self.destination_grid_pos)
                    else:
                        # give the destination building a part of the carried resource
                        resource_portion = min(self.carried_amount, self.single_dropoff_amount) # resource portion to give away to the destination building, cant be more than the amount carried
                        if self.resource_type == "electricity":
                            self.destination.electricity += resource_portion
                            self.carried_amount -= resource_portion
                        elif self.resource_type == "water":
                            self.destination.water += resource_portion
                            self.carried_amount -= resource_portion
                        # print(f"{self.name} delivered {resource_portion} of {self.resource_type} to {self.destination}, carrying {self.carried_amount}")
                        if self.carried_amount < self.single_dropoff_amount:
                            # create a path to the origin road_tile for resource replenishment
                            self.replenishing = True
                            self.create_path(self.origin_grid_pos)
                        else:
                            self.find_destination() # find a new destination and create a path there
                            self.create_path(self.destination_grid_pos)
                else:
                    print(f"{self.name} no destination exists")
                    self.find_destination()
                    if self.destination and self.destination_grid_pos:
                        self.create_path(self.destination_grid_pos)
