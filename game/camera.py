import pygame as pg

class Camera:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.scroll = pg.Vector2(0, 0)
        self.dx = 0
        self.dy = 0
        self.max_speed = 20  # Max speed at edge

    def update(self):
        mouse_x, mouse_y = pg.mouse.get_pos()

        # Define edge zones as 10% of width/height
        edge_x = self.width * 0.1
        edge_y = self.height * 0.1

        self.dx = 0
        self.dy = 0

        # X-axis movement
        if mouse_x < edge_x:
            proximity = 1 - (mouse_x / edge_x)  # 1 near edge, 0 at boundary of zone
            self.dx = self.max_speed * proximity
        elif mouse_x > self.width - edge_x:
            proximity = (mouse_x - (self.width - edge_x)) / edge_x
            self.dx = -self.max_speed * proximity

        # Y-axis movement
        if mouse_y < edge_y:
            proximity = 1 - (mouse_y / edge_y)
            self.dy = self.max_speed * proximity
        elif mouse_y > self.height - edge_y:
            proximity = (mouse_y - (self.height - edge_y)) / edge_y
            self.dy = -self.max_speed * proximity

        # Update scroll
        self.scroll.x += self.dx
        self.scroll.y += self.dy
