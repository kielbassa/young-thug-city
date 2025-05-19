import pygame as pg
from .utils import draw_text
from .buildings import Buildings
from .settings import ELECTRICITY_MULTIPLIER, MOISTURE_MULTIPLIER, WATER_PUMP_COST_MULTIPLIER, SOLAR_PANEL_CLEANING_COST_MULTIPLIER

class Hud:
    def __init__(self,resource_manager,width,height):
        self.resource_manager = resource_manager
        self.width = width
        self.height = height
        self.building = Buildings()

        self.hud_color = (198, 155, 93, 175)

        #resources hud
        self.resources_surface = pg.Surface((width, height*0.02), pg.SRCALPHA)
        self.game_time = 0  # Track the game time (0-23 hours)
        self.resources_rect = self.resources_surface.get_rect(topleft=(0,0))
        self.resources_surface.fill(self.hud_color)

        # For tracking changes to examined_tile for caching
        self.prev_examined_tile_attr = {}

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
        self.select_surface = pg.Surface((width * 0.3, height* 0.25), pg.SRCALPHA)
        self.select_rect = self.select_surface.get_rect(topleft=(self.width * 0.35, self.height*0.8))
        self.select_surface.fill(self.hud_color)

        # Caching variables for select hud
        self.select_cache_valid = False
        self.cached_select_surface = pg.Surface((width * 0.3, height* 0.25), pg.SRCALPHA)
        self.last_examined_tile = None

        # Caching statistics for performance tracking
        self.cache_hits = 0
        self.cache_misses = 0

        self.images = self.load_images()
        self.tiles = self.create_build_hud()

        self.selected_tile = None
        self.examined_tile = None

        self.delete_mode = False  # Track delete mode

        # building preview hud
        self.preview_surface = pg.Surface((width * 0.25, height * 0.15), pg.SRCALPHA)
        self.preview_rect = self.preview_surface.get_rect(topleft=(width * 0.02, height * 0.75))
        self.preview_surface.fill(self.hud_color)

        # Create a transparent surface for the red frame
        self.frame_surface = pg.Surface((width, height), pg.SRCALPHA)

    def update(self):
        mouse_pos = pg.mouse.get_pos()
        mouse_action = pg.mouse.get_pressed()

        if mouse_action[2]:
            self.selected_tile = None

        # Invalidate the select HUD cache if the examined tile has changed
        if self.examined_tile != self.last_examined_tile:
            self.select_cache_valid = False
            self.last_examined_tile = self.examined_tile

            # Store current attribute values for deeper comparison
            if self.examined_tile is not None:
                self.prev_examined_tile_attr = {
                    'name': getattr(self.examined_tile, 'name', None),
                    'electricity_consumption': getattr(self.examined_tile, 'electricity_consumption', None),
                    'water_consumption': getattr(self.examined_tile, 'water_consumption', None),
                    'thugoleon_consumption': getattr(self.examined_tile, 'thugoleon_consumption', None),
                    'electricity_production_rate': getattr(self.examined_tile, 'electricity_production_rate', None),
                    'water_production_rate': getattr(self.examined_tile, 'water_production_rate', None),
                    'thugoleon_production_rate': getattr(self.examined_tile, 'thugoleon_production_rate', None)
                }

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
        screen.blit(self.resources_surface, (0, 0))

        # Display cache efficiency stats
        cache_total = self.cache_hits + self.cache_misses
        if cache_total > 0:
            efficiency = (self.cache_hits / cache_total) * 100
            draw_text(screen, f"Cache: {efficiency:.1f}% ({self.cache_hits}/{cache_total})", 20, (0, 255, 0), (15, 35))

        # build hud
        screen.blit(self.build_surface, (self.building_hud_x, self.building_hud_y))
        draw_text(screen, "Build", 30, (255, 255, 255), (self.building_hud_x + 12, self.building_hud_y + 12))

        for tile in self.tiles:
            icon = tile["icon"].copy()
            if not tile["affordable"]:
                icon.set_alpha(100)
            screen.blit(icon, tile["rect"].topleft)

        # select hud
        if self.examined_tile is not None:
            self.draw_select_hud(screen)

        # resources
        pos = self.width - 950
        for resource, resource_value in self.resource_manager.resources.items():
            txt = resource + ": " + str(resource_value)
            draw_text(screen, txt, 30, (255, 255, 255), (pos, 5))
            pos += len(txt) * 13

        # Draw in-game clock at the end of resources
        if hasattr(self, 'game_time'):
            hours_str = str(self.game_time).zfill(2)
            minutes_str = "00"
            time_str = f"Time: {hours_str}:{minutes_str}"
            draw_text(screen, time_str, 30, (255, 255, 255), (pos, 5))

        # Draw building information tooltip if temp_tile exists
        if hasattr(self, 'world') and self.world.temp_tile is not None:
            self.draw_building_info(screen)

        if hasattr(self, 'world') and self.world.temp_tile is not None and self.selected_tile is not None:
            if self.world.temp_tile["buildable"] or (
                self.world.temp_tile.get("water_resource", False) and
                self.selected_tile["name"] == "water_treatment_plant"
            ):
                self.draw_building_preview(screen)

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
            draw_text(screen, "Delete mode active, press the key again to deactivate", 60, (255, 0, 0),
                      (self.width * 0.02, self.height * 0.95))
    def draw_select_hud(self, screen):
        # Use cached surface if valid
        if self.select_cache_valid and self.examined_tile == self.last_examined_tile:
            # Do deeper attribute comparison to ensure nothing changed
            if self.examined_tile is not None:
                current_attrs = {
                    'name': getattr(self.examined_tile, 'name', None),
                    'electricity_consumption': getattr(self.examined_tile, 'electricity_consumption', None),
                    'water_consumption': getattr(self.examined_tile, 'water_consumption', None),
                    'thugoleon_consumption': getattr(self.examined_tile, 'thugoleon_consumption', None),
                    'electricity_production_rate': getattr(self.examined_tile, 'electricity_production_rate', None),
                    'water_production_rate': getattr(self.examined_tile, 'water_production_rate', None),
                    'thugoleon_production_rate': getattr(self.examined_tile, 'thugoleon_production_rate', None),
                    'worker_count': getattr(self.examined_tile, 'worker_count', None),
                    'worker_count_current': getattr(self.examined_tile, 'worker_count_current', None),
                }
                if current_attrs != self.prev_examined_tile_attr:
                    self.select_cache_valid = False
                    self.prev_examined_tile_attr = current_attrs

            if self.select_cache_valid:
                self.cache_hits += 1
                screen.blit(self.cached_select_surface, (self.width * 0.35, self.height * 0.74))
                return

        # If cache is invalid, render to cached surface
        self.cache_misses += 1
        self.cached_select_surface.fill(self.hud_color)
        w, h = self.select_rect.width, self.select_rect.height

        img = self.examined_tile.image.copy()
        img_scale = self.scale_image(img, h=h * 0.7)
        self.cached_select_surface.blit(img_scale, (85, h * 0.05 + 45))

        # Add building name
        draw_text(self.cached_select_surface, self.examined_tile.name.replace('_', ' ').title(), 40, (255, 255, 255),
                (10, 10))

        # Display resource production/consumption information
        text_size = 28
        description_text_size = 25
        resource_y = h * 0.05 + 50
        resource_x = w * 0.5 + 50

        # Consumption section header
        draw_text(self.cached_select_surface, "Consumption:", text_size, (255, 180, 180), (resource_x, resource_y))
        resource_y += text_size

        # Check if the building has consumption attributes
        if hasattr(self.examined_tile, 'electricity_consumption'):
            consumption_text = f"Electricity: -{self.examined_tile.electricity_consumption}/s"
            draw_text(self.cached_select_surface, consumption_text, text_size, (255, 100, 100), (resource_x, resource_y))
            resource_y += text_size

        if hasattr(self.examined_tile, 'water_consumption'):
            consumption_text = f"Water: -{self.examined_tile.water_consumption}/s"
            draw_text(self.cached_select_surface, consumption_text, text_size, (255, 100, 100), (resource_x, resource_y))
            resource_y += text_size

        if hasattr(self.examined_tile, 'thugoleon_consumption'):
            consumption_text = f"Thugoleons: -{self.examined_tile.thugoleon_consumption}/s"
            draw_text(self.cached_select_surface, consumption_text, text_size, (255, 100, 100), (resource_x, resource_y))
            resource_y += text_size

        # Production section
        resource_y += text_size  # Add some spacing
        draw_text(self.cached_select_surface, "Production:", text_size, (180, 255, 180), (resource_x, resource_y))
        resource_y += text_size

        # Production attributes
        if hasattr(self.examined_tile, 'thugoleon_production_rate'):
            production_text = f"Thugoleons: +{self.examined_tile.thugoleon_production_rate}/s"
            draw_text(self.cached_select_surface, production_text, text_size, (100, 255, 100), (resource_x, resource_y))
            resource_y += text_size

        if hasattr(self.examined_tile, 'electricity_production_rate'):
            production_text = f"Electricity: +{self.examined_tile.electricity_production_rate}/s"
            draw_text(self.cached_select_surface, production_text, text_size, (100, 255, 100), (resource_x, resource_y))
            resource_y += text_size

        if hasattr(self.examined_tile, 'water_production_rate'):
            production_text = f"Water: +{self.examined_tile.water_production_rate}/s"
            draw_text(self.cached_select_surface, production_text, text_size, (100, 255, 100), (resource_x, resource_y))
            resource_y += text_size

        if hasattr(self.examined_tile, 'worker_count'):
            production_text = f"Workers: {self.examined_tile.worker_count}/{self.examined_tile.worker_max_capacity}"
            draw_text(self.cached_select_surface, production_text, text_size, (255, 255, 255), (resource_x, resource_y))
            resource_y += text_size
            production_text = f"Current workers: {self.examined_tile.worker_count_current}"
            draw_text(self.cached_select_surface, production_text, text_size, (255, 255, 255), (resource_x, resource_y))
            resource_y += text_size

        # Add building description if available
        if hasattr(self.world.building_attributes, 'description') and self.examined_tile.name in self.world.building_attributes.description:
            description = self.world.building_attributes.description[self.examined_tile.name]
            # Render description text with word wrapping to fit the panel
            max_width = self.select_rect.width - 20  # Leave a margin

            # Position for the description text (below the image)
            desc_y = 40
            desc_x = 10

            # Simple word wrapping
            words = description.split(' ')
            line = ''
            y_offset = 0

            for word in words:
                test_line = line + word + ' '
                test_width = pg.font.SysFont(None, text_size).size(test_line)[0]

                if test_width > max_width:
                    draw_text(self.cached_select_surface, line, description_text_size, (255, 255, 255), (desc_x, desc_y + y_offset))
                    y_offset += text_size
                    line = word + ' '
                else:
                    line = test_line

            # Render the last line
            if line:
                draw_text(self.cached_select_surface, line, text_size, (255, 255, 255), (desc_x, desc_y + y_offset))

        # Mark cache as valid and display it
        self.select_cache_valid = True
        screen.blit(self.cached_select_surface, (self.width * 0.35, self.height * 0.74))

    def draw_building_info(self, screen):
        # Get mouse position
        mouse_pos = pg.mouse.get_pos()

        # Get the building cost
        building_name = self.selected_tile["name"]
        cost_info = self.resource_manager.costs[building_name]

        # Access building description
        if building_name == "road":
            from .roads import Road
            road_attributes = Road(None, None)  # Pass None for resource_manager too
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

    def draw_building_preview(self, screen):
        # Clear preview surface
        self.preview_surface.fill(self.hud_color)

        # Get grid position and calculate potential production
        grid_pos = self.world.mouse_to_grid(pg.mouse.get_pos()[0], pg.mouse.get_pos()[1], self.world.camera.scroll)
        building_name = self.selected_tile["name"]

        # Only display for production buildings
        if building_name in ["factory", "residential_building", "solar_panels", "water_treatment_plant"]:
            # Draw the preview panel
            screen.blit(self.preview_surface, self.preview_rect.topleft)

            # Panel title
            draw_text(screen, f"{building_name.replace('_', ' ').title()} resource preview", 30,
                     (255, 255, 255), (self.preview_rect.x + 10, self.preview_rect.y + 10))

            # Calculate potential resource values
            font = pg.font.SysFont(None, 26)
            y_offset = 45
            y_margin = 25

            # Draw building costs
            cost_text = f"Cost: {self.resource_manager.costs[building_name]['thugoleons']} thugoleons"
            cost_surface = font.render(cost_text, True, (255, 200, 100))
            screen.blit(cost_surface, (self.preview_rect.x + 10, self.preview_rect.y + y_offset))
            y_offset += 30

            # Draw production estimates
            if building_name == "factory":
                thugoleon_production = self.building.production["factory"]["thugoleons"]
                electricity_consumption = self.building.consumption["factory"]["electricity"]
                water_consumption = self.building.consumption["factory"]["water"]

                prod_text = f"Production: +{thugoleon_production} thugoleons/s"
                cons_text1 = f"Consumes: +{electricity_consumption} electricity/s"
                cons_text2 = f"Consumes: +{water_consumption} water/s"

                prod_surface = font.render(prod_text, True, (100, 255, 100))
                screen.blit(prod_surface, (self.preview_rect.x + 10, self.preview_rect.y + y_offset))
                y_offset += y_margin

                cons_surface1 = font.render(cons_text1, True, (255, 100, 100))
                screen.blit(cons_surface1, (self.preview_rect.x + 10, self.preview_rect.y + y_offset))
                y_offset += y_margin

                cons_surface2 = font.render(cons_text2, True, (255, 100, 100))
                screen.blit(cons_surface2, (self.preview_rect.x + 10, self.preview_rect.y + y_offset))

            elif building_name == "residential_building":
                thugoleon_production = self.building.production["residential_building"]["thugoleons"]
                electricity_consumption = self.building.consumption["residential_building"]["electricity"]
                water_consumption = self.building.consumption["residential_building"]["water"]

                prod_text = f"Production: +{thugoleon_production} thugoleons/s"
                cons_text1 = f"Consumes: +{electricity_consumption} electricity/s"
                cons_text2 = f"Consumes: +{water_consumption} water/s"

                prod_surface = font.render(prod_text, True, (100, 255, 100))
                screen.blit(prod_surface, (self.preview_rect.x + 10, self.preview_rect.y + y_offset))
                y_offset += y_margin

                cons_surface1 = font.render(cons_text1, True, (255, 100, 100))
                screen.blit(cons_surface1, (self.preview_rect.x + 10, self.preview_rect.y + y_offset))
                y_offset += y_margin

                cons_surface2 = font.render(cons_text2, True, (255, 100, 100))
                screen.blit(cons_surface2, (self.preview_rect.x + 10, self.preview_rect.y + y_offset))

            elif building_name == "solar_panels":
                # Calculate potential electricity production based on elevation
                potential_rate = round(self.world.world[grid_pos[0]][grid_pos[1]]["elevation"] * ELECTRICITY_MULTIPLIER)

                potential_water_consumption = round(self.building.consumption["solar_panels"]["water"] + potential_rate * SOLAR_PANEL_CLEANING_COST_MULTIPLIER)
                thugoleon_consumption = self.building.consumption["solar_panels"]["thugoleons"]

                prod_text = f"Production: +{potential_rate} electricity/s"
                cons_text1 = f"Consumes: +{potential_water_consumption} water/s"
                cons_text2 = f"Consumes: +{thugoleon_consumption} thugoleon/s"

                prod_surface = font.render(prod_text, True, (100, 255, 100))
                screen.blit(prod_surface, (self.preview_rect.x + 10, self.preview_rect.y + y_offset))
                y_offset += y_margin

                cons_surface1 = font.render(cons_text1, True, (255, 100, 100))
                screen.blit(cons_surface1, (self.preview_rect.x + 10, self.preview_rect.y + y_offset))
                y_offset += y_margin

                cons_surface2 = font.render(cons_text2, True, (255, 100, 100))
                screen.blit(cons_surface2, (self.preview_rect.x + 10, self.preview_rect.y + y_offset))

            elif building_name == "water_treatment_plant":
                # Calculate potential water production based on moisture
                potential_rate = round(self.world.world[grid_pos[0]][grid_pos[1]]["moisture"] * MOISTURE_MULTIPLIER)
                potential_electricity_consumption = round(self.building.consumption["water_treatment_plant"]["electricity"] + potential_rate * WATER_PUMP_COST_MULTIPLIER)
                thugoleon_consumption = self.building.consumption["water_treatment_plant"]["thugoleons"]

                prod_text = f"Production: +{potential_rate} water/s"
                cons_text1 = f"Consumes: +{potential_electricity_consumption} electricity/s"
                cons_text2 = f"Consumes: +{thugoleon_consumption} thugoleon/s"

                prod_surface = font.render(prod_text, True, (100, 255, 100))
                screen.blit(prod_surface, (self.preview_rect.x + 10, self.preview_rect.y + y_offset))
                y_offset += y_margin

                cons_surface1 = font.render(cons_text1, True, (255, 100, 100))
                screen.blit(cons_surface1, (self.preview_rect.x + 10, self.preview_rect.y + y_offset))
                y_offset += y_margin

                cons_surface2 = font.render(cons_text2, True, (255, 100, 100))
                screen.blit(cons_surface2, (self.preview_rect.x + 10, self.preview_rect.y + y_offset))

    def load_images(self):
        """Loads all hud textures"""
        residential_building = pg.image.load("assets/graphics/residential_building.png").convert_alpha()
        factory = pg.image.load("assets/graphics/factory.png").convert_alpha()
        solar_panels = pg.image.load("assets/graphics/solar_panels.png").convert_alpha()
        water_treatment_plant = pg.image.load("assets/graphics/water_treatment_plant.png").convert_alpha()
        road = pg.image.load("assets/graphics/road_tiles/road_1.png").convert_alpha()

        return {
            "residential_building": residential_building,
            "factory": factory,
            "solar_panels": solar_panels,
            "water_treatment_plant": water_treatment_plant,
            "road": road
        }

    def scale_image(self, image, w=None, h=None):
        """Scales the given image to the specified width and height."""
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
