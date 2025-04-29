import pygame as pg
from game.game import Game

def main():
      # Initialize game variables
    running = True
    playing = True

    pg.init()
    pg.mixer.init()

    pg.display.set_caption("Young Thug City")
    screen = pg.display.set_mode((0, 0), pg.FULLSCREEN, vsync = 1)
    clock = pg.time.Clock()

    # menus

    # implement game
    game = Game(screen, clock)

    # Main game loop
    while running:
        # start menu
        # Splash screen
        screen.fill((0, 0, 0))  # Fill screen with black

        # Load and display splash image
        splash_img = pg.image.load('assets/graphics/splashscreen.png')  # Make sure to have this image
        splash_img = pg.transform.scale(splash_img, (screen.get_width(), screen.get_height()))
        screen.blit(splash_img, (0, 0))
        font = pg.font.SysFont(None, 174)
        text = font.render('Young Thug City welcomes', True, (255, 255, 255))
        text_rect = text.get_rect(center=(screen.get_width()/2, screen.get_height()/2))
        screen.blit(text, text_rect)
        pg.display.flip()
        pg.time.delay(2000)  # Show splash screen for 2 seconds

        while playing:
            # game loop
            game.run()

if __name__ == "__main__":
    main()
