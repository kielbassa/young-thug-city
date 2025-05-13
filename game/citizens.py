import pygame as pg
import random
from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder

class Citizen:
    def __init__(self, tile, world):
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

        self.create_path()

    def create_path(self):
        max_attempts = 50
        attempts = 0

        while attempts < max_attempts:
            # Instead of random destination, find road tiles
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

            # Mark all non-road tiles as non-walkable
            for i in range(self.world.grid_length_x):
                for j in range(self.world.grid_length_y):
                    if self.world.roads[i][j] is None:
                        temp_collision_matrix[j][i] = 0

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
        # Remove citizen from current tile
        self.world.citizens[self.tile["grid"][0]][self.tile["grid"][1]] = None

        # Only move if the new tile is not occupied and has a road
        if (self.world.citizens[new_tile[0]][new_tile[1]] is None and
            self.world.roads[new_tile[0]][new_tile[1]] is not None):
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

        # Handle movement interpolation
        if self.is_moving:
            direction = self.target_pos - self.current_pos
            if direction.length() > 1:  # If not close enough to target
                direction = direction.normalize()
                self.current_pos += direction * self.movement_speed * self.world.clock.get_time()
            else:
                self.current_pos = self.target_pos.copy()
                self.is_moving = False

        if now - self.move_timer > 1000 and not self.is_moving:
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
                        self.create_path()
                else:
                    # If destination has no road, find new path
                    self.create_path()

                self.move_timer = now
