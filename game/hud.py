import pygame as pg
from .utils import draw_text

class Hud:

    def __init__(self,width,height):
        self.width = width
        self.height = height

        self.hud_color = (198, 155, 93, 175)

        #resources hud
        self.resources_surface = pg.Surface((width, height*0.02), pg.SRCALPHA)
        self.resources_rect = self.resources_surface.get_rect(topleft=(0,0))
        self.resources_surface.fill(self.hud_color)

        #building hud
        self.build_surface = pg.Surface((width * 0.15, height* 0.15), pg.SRCALPHA)
        self.build_rect = self.build_surface.get_rect(topleft=(self.width * 0.84, self.height*0.84))
        self.build_surface.fill(self.hud_color)

        #select hud
        self.select_surface = pg.Surface((width * 0.3, height* 0.2), pg.SRCALPHA)
        self.select_rect = self.select_surface.get_rect(topleft=(self.width * 0.35, self.height*0.84))
        self.select_surface.fill(self.hud_color)

        self.images = self.load_images()
        self.tiles = self.create_build_hud()

        self.selected_tile = None
        self.examined_tile = None

    def update(self):
        mouse_pos = pg.mouse.get_pos()
        mouse_action = pg.mouse.get_pressed()

        if mouse_action[2]:
            self.selected_tile = None

        for tile in self.tiles:
            if tile["rect"].collidepoint(mouse_pos):
                if mouse_action[0]:
                    self.selected_tile = tile


    def create_build_hud(self):
        render_pos = [self.width*0.84 + 10, self.height*0.84+10]
        object_width = self.build_surface.get_width() // 5

        tiles = []

        for image_name, image in self.images.items():
            pos = render_pos.copy()
            image_tmp = image.copy()
            image_scale = self.scale_image(image_tmp, w=object_width)
            rect = image_scale.get_rect(topleft=pos)

            tiles.append(
                {
                    "name": image_name,
                    "icon": image_scale,
                    "image": self.images[image_name],
                    "rect": rect
                }
            )

            render_pos[0] += image_scale.get_width() + 10
        return tiles



    def draw(self, screen):
        # resource
        screen.blit(self.resources_surface, (0,0))
        # build hud
        screen.blit(self.build_surface, (self.width * 0.84, self.height*0.84))
        # select hud
        if self.examined_tile is not None:
            w, h = self.select_rect.width, self.select_rect.height
            screen.blit(self.select_surface, (self.width * 0.35, self.height * 0.79))
            img = self.images[self.examined_tile["tile"]].copy()
            img_scale = self.scale_image(img, h=h*0.9)
            screen.blit(img_scale, (self.width * 0.35 + 10, self.height * 0.79 + 10))
            draw_text(screen, self.examined_tile["tile"],40,(255,255,255),self.select_rect.center)
        for tile in self.tiles:
            screen.blit(tile["icon"], tile["rect"].topleft)

        # resources
        pos = self.width - 400
        for resource in ["water:", "electricity:"]:
            draw_text(screen, resource,30,(255,255,255),(pos,0))
            pos += self.width*0.06

    def load_images(self):
        trees = pg.image.load("assets/graphics/trees.png").convert_alpha()
        rock = pg.image.load("assets/graphics/rock.png").convert_alpha()
        residential_building = pg.image.load("assets/graphics/residential_building.png").convert_alpha()
        factory = pg.image.load("assets/graphics/factory.png").convert_alpha()

        return {"residential_building": residential_building, "factory": factory, "rock": rock, "trees": trees}


    def scale_image(self, image, w=None, h=None):
        if w is None and h is None:
            pass
        elif h is None:
            scale = w / image.get_width()
            h = scale * image.get_height()
            image = pg.transform.scale(image, (int(w), int(h)))
        elif w is None:
            scale = h / image.get_height()
            w = scale * image.get_width()
            image = pg.transform.scale(image, (int(w), int(h)))
        else:
            image = pg.transform.scale(image, (int(w), int(h)))
        return image
