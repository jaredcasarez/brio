"""
Asset path configuration for Brio

Provides centralized path management for all assets (textures, models, icons, fonts).
Uses relative paths from the package root to work regardless of working directory.
"""

import os
from pathlib import Path

# Get the directory containing this file (brio_pkg/)
_PACKAGE_DIR = Path(__file__).parent.absolute()
_ASSETS_DIR = _PACKAGE_DIR / "assets"


class Assets:
    """Centralized asset path management"""
    
    # Base directories
    package_dir = _PACKAGE_DIR
    assets_dir = _ASSETS_DIR
    textures_dir = _ASSETS_DIR / "textures"
    models_dir = _ASSETS_DIR / "models"
    icons_dir = _ASSETS_DIR / "icons"
    fonts_dir = _ASSETS_DIR / "fonts"
    
    # Texture paths
    @classmethod
    def texture(cls, name: str) -> str:
        """Get path to a texture file"""
        return str(cls.textures_dir / name)
    
    # Textures
    plywood_base = str(_ASSETS_DIR / "textures" / "plywood_base.jpeg")
    plywood_brown = str(_ASSETS_DIR / "textures" / "plywood_brown.jpeg")
    plywood_blue = str(_ASSETS_DIR / "textures" / "plywood_blue.jpeg")
    paper = str(_ASSETS_DIR / "textures" / "paper.jpg")
    
    # Fonts
    roadgeek_font = str(_ASSETS_DIR / "fonts" / "roadgeek.ttf")
    
    # Icons
    @classmethod
    def icon(cls, name: str) -> str:
        """Get path to an icon file"""
        return str(cls.icons_dir / name)
    
    # Toolbar icons
    icon_new = str(_ASSETS_DIR / "icons" / "file.png")
    icon_save = str(_ASSETS_DIR / "icons" / "save.png")
    icon_open = str(_ASSETS_DIR / "icons" / "folder.png")
    icon_bom = str(_ASSETS_DIR / "icons" / "bom.png")
    
    # Category icons
    icon_straight = str(_ASSETS_DIR / "icons" / "straight.png")
    icon_curved = str(_ASSETS_DIR / "icons" / "curve.png")
    icon_crossing = str(_ASSETS_DIR / "icons" / "cross.png")
    icon_switches = str(_ASSETS_DIR / "icons" / "switch.png")
    icon_elevated = str(_ASSETS_DIR / "icons" / "elev.png")
    
    # Track categories
    track_categories = ["Straight", "Curved", "Crossing", "Switches", "Elevated"]
    
    @classmethod
    def category_icon(cls, category: str) -> str:
        """Get icon path for a track category"""
        icon_map = {
            "Straight": cls.icon_straight,
            "Curved": cls.icon_curved,
            "Crossing": cls.icon_crossing,
            "Switches": cls.icon_switches,
            "Elevated": cls.icon_elevated,
        }
        return icon_map.get(category, cls.icon_straight)
    
    # Model paths
    @classmethod
    def model(cls, name: str) -> str:
        """Get path to a model file"""
        return str(cls.models_dir / name)
    
    @classmethod
    def category_models_dir(cls, category: str) -> Path:
        """Get the models directory for a category"""
        return cls.models_dir / category
    
    @classmethod
    def get_category_models(cls, category: str) -> list:
        """Get list of all model files in a category"""
        import glob
        pattern = str(cls.models_dir / category / "*.bam")
        return glob.glob(pattern)
    
    @classmethod
    def get_all_track_files(cls) -> dict:
        """Get dictionary of category -> list of model files"""
        return {cat: cls.get_category_models(cat) for cat in cls.track_categories}
