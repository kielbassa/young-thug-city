import pygame as pg
from game.game import Game
from game.menu import Menu

def main():
    running = True
    playing = False

    pg.init()
    pg.mixer.init()

    pygame_icon = pg.image.load('assets/graphics/icon.png')
    pg.display.set_icon(pygame_icon)

    pg.display.set_caption("Young Thug City")
    screen = pg.display.set_mode((1024, 768),)
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
