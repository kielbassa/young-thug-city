import pygame as pg

def create_warning_image():
    """
    Creates a warning image (exclamation mark).
    Returns a pygame Surface containing a yellow exclamation mark on a red triangle.
    """
    # Create a transparent surface
    warning_img = pg.Surface((24, 24), pg.SRCALPHA)
    
    # Draw a red triangle
    pg.draw.polygon(warning_img, (255, 0, 0), [(12, 0), (24, 22), (0, 22)], 0)
    
    # Draw a yellow exclamation mark
    # The vertical line of the exclamation mark
    pg.draw.rect(warning_img, (255, 255, 0), (10, 5, 4, 10), 0)
    # The dot of the exclamation mark
    pg.draw.rect(warning_img, (255, 255, 0), (10, 17, 4, 4), 0)
    
    return warning_img