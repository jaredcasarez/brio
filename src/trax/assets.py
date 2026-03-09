"""
Asset path configuration for trax

Provides centralized path management for all assets (textures, models, icons, fonts).
Uses relative paths from the package root to work regardless of working directory.
Supports multiple modes: 'brio' (train tracks) and 'citystreets' (city road pieces).
"""

import os
from pathlib import Path
from typing import Literal

# Get the directory containing this file (brio_pkg/)
_PACKAGE_DIR = Path(__file__).parent.absolute()
_ASSETS_DIR = _PACKAGE_DIR / "assets"

# Valid asset modes
AssetMode = Literal["brio", "citystreets"]

# Mode-specific configuration
_MODE_CONFIG = {
    "brio": {
        "categories": ["Straight", "Curved", "Crossing", "Switches", "Elevated"],
        "display_name": "Brio",
        "track_texture": "plywood_brown.jpeg",
        "select_texture": "plywood_blue.jpeg",
        "table_texture": "paper.jpeg",
        "model_subdir": "brio",
    },
    "citystreets": {
        "categories": ["Straight", "Curved", "Crossing","Rail", "Roundabout"],
        "display_name": "CityStreets",
        "track_texture": "paper.jpeg",
        "select_texture": "plywood_blue.jpeg",
        "table_texture": "paper.jpeg",
        "model_subdir": "citystreets",
    },
}


class Assets:
    """Centralized asset path management with multi-mode support.
    
    Supports two modes:
    - 'brio': Train track models (Straight, Curved, Crossing, Switches, Elevated)
    - 'citystreets': City road models (Straight, Curved, Crossing, Roundabout, Rail)
    
    Usage:
        # Set mode at startup
        Assets.set_mode('brio')  # or 'citystreets'
        
        # Get models for current mode
        models = Assets.get_category_models('Straight')
    """
    
    # Current active mode
    _mode: AssetMode = "brio"
    
    # Base directories
    package_dir = _PACKAGE_DIR
    assets_dir = _ASSETS_DIR
    _base_textures_dir = _ASSETS_DIR / "textures"
    _base_models_dir = _ASSETS_DIR / "models"
    icons_dir = _ASSETS_DIR / "icons"
    fonts_dir = _ASSETS_DIR / "fonts"
    
    texture_names = ["track_texture", "select_texture", "table_texture"]
    # --- Mode Management ---
    
    @classmethod
    def set_mode(cls, mode: str) -> None:
        """Set the active asset mode.
        
        Args:
            mode: Either 'brio' for train tracks or 'citystreets' for road pieces.
        
        Raises:
            ValueError: If mode is not valid.
        """
        if mode not in _MODE_CONFIG:
            valid_modes = list(_MODE_CONFIG.keys())
            raise ValueError(f"Invalid mode '{mode}'. Must be one of: {valid_modes}")
        cls._mode = mode  # type: ignore[assignment]
    
    @classmethod
    def get_mode(cls) -> AssetMode:
        """Get the current active mode."""
        return cls._mode
    
    @classmethod
    def get_mode_display_name(cls) -> str:
        """Get human-readable name for current mode."""
        return _MODE_CONFIG[cls._mode]["display_name"]
    
    @classmethod
    def get_available_modes(cls) -> list[str]:
        """Get list of all available modes."""
        return list(_MODE_CONFIG.keys())
    
    # --- Directory Properties ---
    
    
    @classmethod
    def get_models_dir(cls) -> Path:
        """Get models directory for current mode (method version)."""
        return cls._base_models_dir / cls._mode
    
    @classmethod
    def get_models_dir_for_mode(cls, mode: AssetMode) -> Path:
        """Get models directory for a specific mode."""
        return cls._base_models_dir / mode
    
    # --- Texture paths ---
    
    @classmethod
    def get_texture(cls ,name: str) -> str:
        """Get path to a texture file"""
        if name not in cls.texture_names:
            raise ValueError(f"Invalid texture name '{name}'. Valid names: {cls.texture_names}")
        return str(cls._base_textures_dir / _MODE_CONFIG[cls._mode][f"{name}"])
    
    # Fonts
    roadgeek_font = str(_ASSETS_DIR / "fonts" / "roadgeek.ttf")
    
    # --- Icons ---
    
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
    icon_roundabout = str(_ASSETS_DIR / "icons" / "roundabout.png")
    icon_rail = str(_ASSETS_DIR / "icons" / "rail.png")
    
    # Mode icons
    icon_brio_inactive = str(_ASSETS_DIR / "icons" / "brio_inactive.png")
    icon_brio_active = str(_ASSETS_DIR / "icons" / "brio_active.png")
    icon_citystreets_inactive = str(_ASSETS_DIR / "icons" / "citystreets_inactive.png")
    icon_citystreets_active = str(_ASSETS_DIR / "icons" / "citystreets_active.png")
    # --- Categories (mode-dependent) ---
    
    @classmethod
    def get_track_categories(cls) -> list[str]:
        """Get track categories for current mode."""
        return _MODE_CONFIG[cls._mode]["categories"]
    
    @classmethod
    def category_icon(cls, category: str) -> str:
        """Get icon path for a track category"""
        icon_map = {
            "Straight": cls.icon_straight,
            "Curved": cls.icon_curved,
            "Crossing": cls.icon_crossing,
            "Switches": cls.icon_switches,
            "Elevated": cls.icon_elevated,
            "Roundabout": cls.icon_roundabout,
            "Rail": cls.icon_rail,
        }
        return icon_map.get(category, cls.icon_straight)
    
    # --- Model paths ---
    
    @classmethod
    def model(cls, name: str) -> str:
        """Get path to a model file in current mode's directory"""
        return str(cls.get_models_dir() / name)
    
    @classmethod
    def category_models_dir(cls, category: str) -> Path:
        """Get the models directory for a category in current mode"""
        return cls.get_models_dir() / category
    
    @classmethod
    def get_category_models(cls, category: str) -> list[str]:
        """Get list of all model files in a category for current mode"""
        import glob
        files = glob.glob(str(cls.get_models_dir() / category / "*.bam"))
        files += glob.glob(str(cls.get_models_dir() / category / "*.glb"))
        return files
    
    @classmethod
    def get_all_track_files(cls) -> dict[str, list[str]]:
        """Get dictionary of category -> list of model files for current mode"""
        return {cat: cls.get_category_models(cat) for cat in cls.get_track_categories()}

    