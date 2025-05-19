import pygame as pg
from game.game import Game
from game.menu import Menu
from game.settings import HORIZONTAL_RESOLUTION, VERTICAL_RESOLUTION, FULLSCREEN

def main():
    running = True
    playing = False

    pg.init()
    pg.mixer.init()

    pygame_icon = pg.image.load('assets/graphics/icon.png')
    pg.display.set_icon(pygame_icon)

    pg.display.set_caption("Young Thug City")
    screen = pg.display.set_mode((HORIZONTAL_RESOLUTION, VERTICAL_RESOLUTION), pg.FULLSCREEN if FULLSCREEN else 0)
    clock = pg.time.Clock()

    # menus
    menu = Menu(screen, clock)
    # implement game
    game = Game(screen, clock)

    # Main game loop
    while running:
        # Show menu and get result
        playing = menu.draw()

        if not playing:  # If menu returns False, quit the game
            running = False
            break

        if playing:
            # game loop
            game.run()
            playing = False  # Reset playing when game ends

    pg.quit()

if __name__ == "__main__":
    main()
