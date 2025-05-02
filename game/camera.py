import pygame as pg
from .settings import CAMERA_SPEED

class Camera:
    def __init__(self, width, height, hud):
        self.width = width
        self.height = height
        self.hud = hud

        self.scroll = pg.Vector2(0, 0)
        self.dx = 0
        self.dy = 0
        self.max_speed = CAMERA_SPEED  # Max speed at edge

    def update(self):
        mouse_x, mouse_y = pg.mouse.get_pos()

        # Define edge zones as 10% of width/height
        edge_x = self.width * 0.03
        edge_y = self.height * 0.03

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

        # Update scroll if not on hud element
        mouse_on_panel = False
        for rect in [self.hud.build_rect]:
            if rect.collidepoint(pg.mouse.get_pos()):
                mouse_on_panel = True
                break
        if not mouse_on_panel:
            self.scroll.x += self.dx
            self.scroll.y += self.dy
