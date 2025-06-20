import pygame as pg

def draw_text(screen, text, size, color, pos):
    """Draws text on the screen."""
    font = pg.font.SysFont(None, int(size))
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(topleft=pos)

    screen.blit(text_surface, text_rect)
