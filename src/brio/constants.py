"""
Color constants and application settings
"""

from .utils import todecimal, rgba


class Colors:
    """Playful Brio-inspired color palette"""
    
    # Table and grid colors
    tableColor = todecimal(rgba(245, 235, 220, 1))  # Light birch wood
    gridColor = todecimal(rgba(0, 0, 0, 1))  # Soft wood grain
    trackColor = todecimal(rgba(130, 255, 170, 1))
    trackColorShadow = tuple(i * 0.75 for i in trackColor[:3]) + (trackColor[3],)
    trackColorHighlight = todecimal(rgba(255, 255, 200, 1))
    selectColor = todecimal(rgba(238, 227, 171, 1))
    
    # Playful toy colors (classic Brio palette)
    brioRed = todecimal(rgba(220, 60, 50, 1))
    brioGreen = todecimal(rgba(80, 180, 80, 1))
    brioBlue = todecimal(rgba(65, 135, 200, 1))
    brioYellow = todecimal(rgba(245, 200, 60, 1))
    brioOrange = todecimal(rgba(240, 140, 50, 1))
    
    # UI Colors - playful and warm
    panelColor = todecimal(rgba(250, 245, 235, 1))  # Warm white
    panelBorderColor = todecimal(rgba(180, 160, 130, 1))  # Warm border
    buttonColor = todecimal(rgba(240, 235, 225, 1))  # Light button
    buttonActiveColor = todecimal(rgba(255, 220, 140, 1))  # Highlighted yellow
    textColor = todecimal(rgba(70, 55, 40, 1))  # Dark brown text
    textLightColor = todecimal(rgba(255, 255, 255, 1))  # White text
    backgroundColor = todecimal(rgba(65, 150, 255, 1))  # Soft sky blue
    statusBarColor = todecimal(rgba(60, 50, 40, 1))  # Dark bar
    
    # Category colors (vibrant tabs)
    categoryColors = {
        "Straight": todecimal(rgba(65, 135, 200, 1)),   # Blue
        "Curved": todecimal(rgba(80, 180, 80, 1)),      # Green
        "Crossing": todecimal(rgba(220, 60, 50, 1)),    # Red
        "Switches": todecimal(rgba(240, 140, 50, 1)),   # Orange
        "Elevated": todecimal(rgba(160, 100, 180, 1)),  # Purple
    }


# Application settings
class Settings:
    dt = 0.0005
