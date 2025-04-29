import pygame as pg
from game.game import Game

def main():
      # Initialize game variables
    running = True
    playing = True

    pg.init()
    pg.mixer.init()

    pg.display.set_caption("Young Thug City")
    screen = pg.display.set_mode((0, 0), pg.FULLSCREEN)
    clock = pg.time.Clock()

    # menus

    # implement game
    game = Game(screen, clock)

    # Main game loop
    while running:
        # start menu

        while playing:
            # game loop
            game.run()

if __name__ == "__main__":
    main()
