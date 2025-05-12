import pygame as pg

class Road:
    def __init__(self, pos, resource_manager=None):
        self.name = "road"
        self.tiles = self.load_images()
        self.image = self.tiles["straight_13"]  # Default texture
        self.rect = self.image.get_rect(topleft=pos) if pos else None
        self.description = "A road tile that connects buildings and allows citizens and resources to move around."

        # Apply cost if resource manager is provided
        if resource_manager:
            self.resource_manager = resource_manager
            self.resource_manager.apply_cost_to_resource(self.name)

    def update_texture(self, grid_pos, roads):
        # Determine connections to adjacent tiles
        connections = {
            "top": roads[grid_pos[0]][grid_pos[1] - 1] if grid_pos[1] > 0 else None,
            "right": roads[grid_pos[0] + 1][grid_pos[1]] if grid_pos[0] < len(roads) - 1 else None,
            "bottom": roads[grid_pos[0]][grid_pos[1] + 1] if grid_pos[1] < len(roads[0]) - 1 else None,
            "left": roads[grid_pos[0] - 1][grid_pos[1]] if grid_pos[0] > 0 else None,
        }

        # Convert connections to a binary representation (1 for connected, 0 for not)
        connected = [
            1 if connections["top"] else 0,
            1 if connections["right"] else 0,
            1 if connections["bottom"] else 0,
            1 if connections["left"] else 0
        ]

        # connection mapping
        connection_to_texture = {
            (1, 1, 1, 1): "crossroad",    # All connections
            (1, 1, 1, 0): "T_123",        # Top, Right, Bottom
            (0, 1, 1, 1): "T_234",        # Right, Bottom, Left
            (1, 0, 1, 1): "T_134",        # Top, Bottom, Left
            (1, 1, 0, 1): "T_124",        # Top, Right, Left
            (1, 0, 1, 0): "straight_13",  # Top, Bottom
            (0, 1, 0, 1): "straight_24",  # Left, Right
            (1, 1, 0, 0): "curve_12",     # Top, Right
            (0, 1, 1, 0): "curve_23",     # Right, Bottom
            (0, 0, 1, 1): "curve_34",     # Bottom, Left
            (1, 0, 0, 1): "curve_14",     # Left, Top
            (1, 0, 0, 0): "end_1",        # Top only
            (0, 1, 0, 0): "end_2",        # Right only
            (0, 0, 1, 0): "end_3",        # Bottom only
            (0, 0, 0, 1): "end_4",        # Left only
            (0, 0, 0, 0): "straight_13",  # Default texture (no connections)
        }

        # Get texture name based on connection pattern
        texture_name = connection_to_texture.get(tuple(connected), "straight_13")
        self.image = self.tiles[texture_name]

    def update(self):
        pass

    def draw(self, screen, camera):
        if self.image:
            screen.blit(self.image, (self.rect.x + camera.scroll.x, self.rect.y + camera.scroll.y))

    def load_images(self):
        # Load road textures
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

        return {
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
            "crossroad": crossroad,
        }
