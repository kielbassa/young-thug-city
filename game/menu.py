import pygame as pg

from game.utils import draw_text
from .settings import TEXT_SIZE

class Menu:
    def __init__(self, screen, clock):
        self.screen = screen
        self.clock = clock

        # Button properties
        self.button_width = 200
        self.button_height = 50
        self.button_x = self.screen.get_width()/2 - self.button_width/2
        self.button_y = self.screen.get_height()/2 + 100
        self.button_color = (50, 168, 82)  # Green color
        self.button_hover_color = (40, 140, 70)  # Darker green for hover

        # Create button rectangle
        self.button_rect = pg.Rect(self.button_x, self.button_y,
                                  self.button_width, self.button_height)

        # load click sound
        self.click_sound = pg.mixer.Sound('assets/audio/click.wav')

        # Load splash image
        try:
            self.splash_img = pg.image.load('assets/graphics/splashscreen.png')
            # Scale image to be slightly smaller to leave room for text
            scaled_height = self.screen.get_height() * 1
            scaled_width = self.screen.get_width() * 1
            self.splash_img = pg.transform.scale(self.splash_img,
                                               (int(scaled_width),
                                                int(scaled_height)))
            # Calculate position to center the image
            self.img_x = (self.screen.get_width() - scaled_width) // 2
            self.img_y = (self.screen.get_height() - scaled_height) // 3  # Position higher up
        except:
            self.splash_img = None

    def draw(self):
        running = True
        while running:
            # Draw background
            self.screen.fill((0, 0, 0))

            # Draw splash image
            if self.splash_img:
                self.screen.blit(self.splash_img, (self.img_x, self.img_y))

            # Draw title text
            text = "Welcome to Young Thug City"
            draw_text(self.screen, text, TEXT_SIZE * 3, (255,255,255), (self.screen.get_width()/2 - (len(text) * (TEXT_SIZE+4))/2,
                                            self.screen.get_height()/2))

            # Get mouse position and check for hover
            mouse_pos = pg.mouse.get_pos()
            if self.button_rect.collidepoint(mouse_pos):
                button_color_current = self.button_hover_color
            else:
                button_color_current = self.button_color

            # Draw button
            pg.draw.rect(self.screen, button_color_current, self.button_rect)

            # Draw button text
            button_font = pg.font.Font(None, 36)
            button_text = button_font.render('Start Game', True, (255, 255, 255))
            text_rect = button_text.get_rect(center=self.button_rect.center)
            self.screen.blit(button_text, text_rect)

            # Update display
            pg.display.flip()

            # Event handling
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    return False  # Signal to quit game
                elif event.type == pg.MOUSEBUTTONDOWN:
                    if self.button_rect.collidepoint(event.pos):
                        self.click_sound.play()
                        return True  # Signal to start game
                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_ESCAPE:
                        return False  # Signal to quit game

            self.clock.tick(60)
