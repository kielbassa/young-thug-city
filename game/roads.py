import pygame as pg
from .settings import TILE_SIZE

class Road:
    def __init__(self, pos):
        pass

    def update(self):
        pass

    def draw(self, screen, world, camera):
        pass
        
    def load_images(self):
        # Directions of road connections: 
        # 1 = top right quadrant, 
        # 2 = bottom right quadrant, 
        # 3 = bottom left quadrant, 
        # 4 = top left quadrant

        straight_13 = pg.image.load("assets/graphics/road_tiles/road_1.png").convert_alpha()
        straight_24 = pg.image.load("assets/graphics/road_tiles/road_2.png").convert_alpha()
        curve_12 = pg.image.load("assets/graphics/road_tiles/road_3.png").convert_alpha()
        curve_34 = pg.image.load("assets/graphics/road_tiles/road_4.png").convert_alpha()
        curve_14 = pg.image.load("assets/graphics/road_tiles/road_5.png").convert_alpha()
        curve_23 = pg.image.load("assets/graphics/road_tiles/road_6.png").convert_alpha()
        T_134 = pg.image.load("assets/graphics/road_tiles/road_7.png").convert_alpha()
        T_234 = pg.image.load("assets/graphics/road_tiles/road_8.png").convert_alpha()
        T_123 = pg.image.load("assets/graphics/road_tiles/road_9.png").convert_alpha()
        T_124 = pg.image.load("assets/graphics/road_tiles/road_13.png").convert_alpha()
        end_2 = pg.image.load("assets/graphics/road_tiles/road_10.png").convert_alpha()
        end_1 = pg.image.load("assets/graphics/road_tiles/road_11.png").convert_alpha()
        end_4 = pg.image.load("assets/graphics/road_tiles/road_12.png").convert_alpha()
        end_3 = pg.image.load("assets/graphics/road_tiles/road_15.png").convert_alpha()
        crossroad = pg.image.load("assets/graphics/road_tiles/road_14.png").convert_alpha()

        out = {
            "straight_13": straight_13,
            "straight_24": straight_24,
            "curve_12": curve_12,
            "curve_34": curve_34,
            "curve_14": curve_14,
            "curve_23": curve_23,
            "T_134": T_134,
            "T_234": T_234,
            "T_123": T_123,
            "T_124": T_124,
            "end_2": end_2,
            "end_1": end_1,
            "end_4": end_4,
            "end_3": end_3,
            "crossroad": crossroad
        }
        return out
