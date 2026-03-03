"""
Utility functions for color and data conversions
"""


def todecimal(color_tuple):
    """Convert 0-255 RGBA to 0-1 decimal format"""
    return tuple(c / 255 for c in color_tuple[:3]) + (color_tuple[3],)


def rgba(r, g, b, a):
    """Create an RGBA tuple"""
    return (r, g, b, a)
