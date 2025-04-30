import pygame as pg
import random
from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder

class Citizen:

    def __init__(self, tile, world):
        self.world = world
        self.world.entities.append(self)
        image = pg.image.load("assets/graphics/citizen.png").convert_alpha()
        self.name = "citizen"
        self.image = pg.transform.scale(image, (image.get_width()*2, image.get_height()*2))
        self.tile = tile

        # pathfinding
        self.world.citizens[tile["grid"][0]][tile["grid"][1]] = self
        self.move_timer = pg.time.get_ticks()

        self.create_path()

    def create_path(self):
        max_attempts = 50  # Limit the number of attempts to find a path
        attempts = 0

        while attempts < max_attempts:
            x = random.randint(0, self.world.grid_length_x - 1)
            y = random.randint(0, self.world.grid_length_y - 1)
            dest_tile = self.world.world[x][y]

            if dest_tile["walkable"]:  # Only choose walkable destinations
                self.grid = Grid(matrix=self.world.collision_matrix)
                self.start = self.grid.node(self.tile["grid"][0], self.tile["grid"][1])
                self.end = self.grid.node(x, y)
                finder = AStarFinder(diagonal_movement=DiagonalMovement.never)
                path, runs = finder.find_path(self.start, self.end, self.grid)

                # Only accept the path if one was found
                if len(path) > 0:
                    self.path_index = 0
                    self.path = path
                    return

            attempts += 1

        # If no path is found after max attempts, stay in place
        self.path = [self.grid.node(self.tile["grid"][0], self.tile["grid"][1])]
        self.path_index = 0

    def change_tile(self, new_tile):
        self.world.citizens[self.tile["grid"][0]][self.tile["grid"][1]] = None
        self.world.citizens[new_tile[0]][new_tile[1]] = self
        self.tile = self.world.world[new_tile[0]][new_tile[1]]

    def update(self):
        now = pg.time.get_ticks()
        if now - self.move_timer > 1000:
            # Check if we have a valid path and haven't reached the end
            if self.path and self.path_index < len(self.path):
                node = self.path[self.path_index]
                new_pos = [node.x, node.y]

                # Only move if the destination is walkable
                if self.world.world[new_pos[0]][new_pos[1]]["walkable"]:
                    self.change_tile(new_pos)
                    self.path_index += 1

                    # Create new path when reaching destination
                    if self.path_index >= len(self.path):
                        self.create_path()
                else:
                    # If destination is no longer walkable, find new path
                    self.create_path()

                self.move_timer = now
