import pygame as pg
from .utils import draw_text

class Hud:

    def __init__(self,resource_manager,width,height):
        self.resource_manager = resource_manager
        self.width = width
        self.height = height

        self.hud_color = (198, 155, 93, 175)

        #resources hud
        self.resources_surface = pg.Surface((width, height*0.02), pg.SRCALPHA)
        self.resources_rect = self.resources_surface.get_rect(topleft=(0,0))
        self.resources_surface.fill(self.hud_color)

        # Variables to control building HUD size and position
        self.building_hud_width = width * 0.25  # 25% of the screen width
        self.building_hud_height = height * 0.12  # 12% of the screen height
        self.building_hud_x = width * 0.73  # Positioned at 73% of the screen width
        self.building_hud_y = height * 0.85  # Positioned at 85% of the screen height

        #building hud
        self.build_surface = pg.Surface((self.building_hud_width, self.building_hud_height), pg.SRCALPHA)
        self.build_rect = self.build_surface.get_rect(topleft=(self.building_hud_x-10, self.building_hud_y-10))
        self.build_surface.fill(self.hud_color)

        #select hud
        self.select_surface = pg.Surface((width * 0.3, height* 0.2), pg.SRCALPHA)
        self.select_rect = self.select_surface.get_rect(topleft=(self.width * 0.35, self.height*0.8))
        self.select_surface.fill(self.hud_color)

        self.images = self.load_images()
        self.tiles = self.create_build_hud()

        self.selected_tile = None
        self.examined_tile = None

        self.delete_mode = False  # Track delete mode

        # Create a transparent surface for the red frame
        self.frame_surface = pg.Surface((width, height), pg.SRCALPHA)

    def update(self):
        mouse_pos = pg.mouse.get_pos()
        mouse_action = pg.mouse.get_pressed()

        if mouse_action[2]:
            self.selected_tile = None

        for tile in self.tiles:
            if self.resource_manager.is_affordable(tile["name"]):
                tile["affordable"] = True
            else:
                tile["affordable"] = False
            if tile["rect"].collidepoint(mouse_pos) and tile["affordable"]:
                if mouse_action[0]:
                    self.selected_tile = tile

    def create_build_hud(self):
        render_pos = [self.building_hud_x+20, self.building_hud_y+50] # Start position for rendering building icons
        object_width = self.build_surface.get_width() // 6
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
                    "rect": rect,
                    "affordable": True
                }
            )

            render_pos[0] += image_scale.get_width() + 10
        return tiles

    def draw(self, screen):
        # resource
        screen.blit(self.resources_surface, (0,0))

        # build hud
        screen.blit(self.build_surface, (self.building_hud_x, self.building_hud_y))
        draw_text(screen, "Build", 30, (255, 255, 255), (self.building_hud_x + 12, self.building_hud_y + 12))

        # select hud
        if self.examined_tile is not None:
            w, h = self.select_rect.width, self.select_rect.height
            screen.blit(self.select_surface, (self.width * 0.35, self.height * 0.79))
            img = self.examined_tile.image.copy()
            img_scale = self.scale_image(img, h=h*0.7)
            screen.blit(img_scale, (self.width * 0.35 + 10, self.height * 0.79 + 45))

            # Add building name
            draw_text(screen, self.examined_tile.name, 40, (255, 255, 255),
                     (self.width * 0.35 + 10, self.height * 0.79 + 10))

            # Display resource production/consumption information
            font = pg.font.SysFont(None, 30)
            resource_y = self.height * 0.79 + 45
            resource_x = self.width * 0.5

            # Consumption section header
            consumption_header = font.render("Consumption:", True, (255, 180, 180))
            screen.blit(consumption_header, (resource_x, resource_y))
            resource_y += font.get_linesize()

            # Check if the building has consumption attributes
            if hasattr(self.examined_tile, 'electricity_consumption'):
                consumption_text = f"Electricity: -{self.examined_tile.electricity_consumption}/s"
                text_surface = font.render(consumption_text, True, (255, 100, 100))
                screen.blit(text_surface, (resource_x, resource_y))
                resource_y += font.get_linesize()

            if hasattr(self.examined_tile, 'water_consumption'):
                consumption_text = f"Water: -{self.examined_tile.water_consumption}/s"
                text_surface = font.render(consumption_text, True, (255, 100, 100))
                screen.blit(text_surface, (resource_x, resource_y))
                resource_y += font.get_linesize()

            if hasattr(self.examined_tile, 'thugoleon_consumption'):
                consumption_text = f"Thugoleons: -{self.examined_tile.thugoleon_consumption}/s"
                text_surface = font.render(consumption_text, True, (255, 100, 100))
                screen.blit(text_surface, (resource_x, resource_y))
                resource_y += font.get_linesize()

            # Production section
            resource_y += font.get_linesize()  # Add some spacing
            production_header = font.render("Production:", True, (180, 255, 180))
            screen.blit(production_header, (resource_x, resource_y))
            resource_y += font.get_linesize()

            # Production attributes
            if hasattr(self.examined_tile, 'thugoleon_production_rate'):
                production_text = f"Thugoleons: +{self.examined_tile.thugoleon_production_rate}/s"
                text_surface = font.render(production_text, True, (100, 255, 100))
                screen.blit(text_surface, (resource_x, resource_y))
                resource_y += font.get_linesize()

            if hasattr(self.examined_tile, 'electricity_production_rate'):
                production_text = f"Electricity: +{self.examined_tile.electricity_production_rate}/s"
                text_surface = font.render(production_text, True, (100, 255, 100))
                screen.blit(text_surface, (resource_x, resource_y))
                resource_y += font.get_linesize()

            if hasattr(self.examined_tile, 'water_production_rate'):
                production_text = f"Water: +{self.examined_tile.water_production_rate}/s"
                text_surface = font.render(production_text, True, (100, 255, 100))
                screen.blit(text_surface, (resource_x, resource_y))
                resource_y += font.get_linesize()

            # Add building description if available
            if hasattr(self.world.building_attributes, 'description') and self.examined_tile.name in self.world.building_attributes.description:
                description = self.world.building_attributes.description[self.examined_tile.name]
                # Render description text with word wrapping to fit the panel
                max_width = self.select_rect.width - 20  # Leave a margin

                # Position for the description text (below the image)
                desc_y = self.height * 0.79 + 40 + img_scale.get_height() + 10
                desc_x = self.width * 0.35 + 10

                # Simple word wrapping
                words = description.split(' ')
                line = ''
                y_offset = 0

                for word in words:
                    test_line = line + word + ' '
                    test_width = font.size(test_line)[0]

                    if test_width > max_width:
                        text_surface = font.render(line, True, (255, 255, 255))
                        screen.blit(text_surface, (desc_x, desc_y + y_offset))
                        y_offset += font.get_linesize()
                        line = word + ' '
                    else:
                        line = test_line

                # Render the last line
                if line:
                    text_surface = font.render(line, True, (255, 255, 255))
                    screen.blit(text_surface, (desc_x, desc_y + y_offset))

        for tile in self.tiles:
            icon = tile["icon"].copy()
            if not tile["affordable"]:
                icon.set_alpha(100)
            screen.blit(icon, tile["rect"].topleft)

        # resources
        pos = self.width - 600
        for resource, resource_value in self.resource_manager.resources.items():
            txt = resource + ": " + str(resource_value)
            draw_text(screen, txt, 30, (255, 255, 255), (pos, 0))
            pos += self.width * 0.08

        # Draw building information tooltip if temp_tile exists
        if hasattr(self, 'world') and self.world.temp_tile is not None:
            self.draw_building_info(screen)

        # Display a message if delete mode is active
        if self.delete_mode:
            # Render a red frame with alpha
            frame_thickness = 10  # Thickness of the red frame
            frame_color = (255, 0, 0, 128)  # Red color with 50% transparency (alpha = 128)

            # Clear the frame surface
            self.frame_surface.fill((0, 0, 0, 0))  # Fully transparent background

            # Draw the red frame on the transparent surface
            pg.draw.rect(self.frame_surface, frame_color, (0, 0, self.width, frame_thickness))  # Top border
            pg.draw.rect(self.frame_surface, frame_color, (0, 0, frame_thickness, self.height))  # Left border
            pg.draw.rect(self.frame_surface, frame_color, (0, self.height - frame_thickness, self.width, frame_thickness))  # Bottom border
            pg.draw.rect(self.frame_surface, frame_color, (self.width - frame_thickness, 0, frame_thickness, self.height))  # Right border

            # Blit the frame surface onto the screen
            screen.blit(self.frame_surface, (0, 0))
            draw_text(screen, "Delete mode active, press the key again to deactivate", 60, (255, 0, 0), (self.width * 0.02, self.height * 0.95))

    def load_images(self):
        residential_building = pg.image.load("assets/graphics/residential_building.png").convert_alpha()
        factory = pg.image.load("assets/graphics/factory.png").convert_alpha()
        solar_panels = pg.image.load("assets/graphics/solar_panels.png").convert_alpha()
        water_treatment_plant = pg.image.load("assets/graphics/water_treatment_plant.png").convert_alpha()
        road = pg.image.load("assets/graphics/road_tiles/road_1.png").convert_alpha()

        return {"residential_building": residential_building, "factory": factory, "solar_panels": solar_panels, "water_treatment_plant": water_treatment_plant, "road": road}

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

    def draw_building_info(self, screen):
        # Get mouse position
        mouse_pos = pg.mouse.get_pos()

        # Get the building cost
        building_name = self.selected_tile["name"]
        cost_info = self.resource_manager.costs[building_name]

        # Access building description
        if building_name == "road":
            from .roads import Road
            road_attributes = Road(None)
            description_text = f"Description: {road_attributes.description}"
        else:
            # For other buildings, get the description from the Buildings class
            buildings_attributes = self.world.building_attributes
            if hasattr(buildings_attributes, 'description') and building_name in buildings_attributes.description:
                description_text = f"Description: {buildings_attributes.description[building_name]}"
            else:
                description_text = ""

        # Create cost text
        cost_text = f"Cost: {cost_info['thugoleons']} thugoleons"

        # Render text
        font = pg.font.SysFont(None, 24)
        cost_surface = font.render(cost_text, True, (255, 255, 255))
        cost_rect = cost_surface.get_rect()
        cost_rect.topleft = (mouse_pos[0] + 20, mouse_pos[1] + 20)

        # Create background rect
        bg_rect = cost_rect.copy()
        bg_rect.inflate_ip(10, 10)  # Make background slightly larger than text

        # Draw cost info
        pg.draw.rect(screen, (0, 0, 0, 180), bg_rect)
        screen.blit(cost_surface, cost_rect)

        # Draw description if available
        if description_text:
            description_surface = font.render(description_text, True, (255, 255, 255))
            description_rect = description_surface.get_rect()
            description_rect.topleft = (mouse_pos[0] + 20, mouse_pos[1] + 50)

            bg_rect = description_rect.copy()
            bg_rect.inflate_ip(10, 10)
            pg.draw.rect(screen, (0, 0, 0, 180), bg_rect)
            screen.blit(description_surface, description_rect)
