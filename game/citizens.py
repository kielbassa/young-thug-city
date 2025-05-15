import pygame as pg
import random
from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder

class Citizen:
    def __init__(self, tile, world, home_tile):
        self.tile = tile
        self.world = world
        self.home_tile = home_tile # tile of the home that spawned the citizen
        self.path = None
        self.path_index = 0

    def update(self):
        pass
