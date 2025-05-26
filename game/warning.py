import pygame as pg

def create_warning_image():
    """Creates a warning image (exclamation mark)"""

    warning_img = pg.Surface((36, 36), pg.SRCALPHA)

    # Draw a red triangle
    pg.draw.polygon(warning_img, (255, 0, 0), [(18, 0), (36, 33), (0, 33)], 0)

    # exclamation mark
    # The vertical line of the exclamation mark
    pg.draw.rect(warning_img, (255, 255, 0), (15, 8, 6, 15), 0)
    # The dot of the exclamation mark
    pg.draw.rect(warning_img, (255, 255, 0), (15, 26, 6, 6), 0)

    return warning_img
