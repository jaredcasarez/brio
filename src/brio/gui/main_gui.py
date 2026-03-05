"""
Main GUI controller
"""

from direct.gui.DirectGui import (
    DirectFrame, DirectButton, DirectLabel, DGG
)
from panda3d.core import TextNode

from ..utils import todecimal, rgba
from ..constants import Colors
from ..assets import Assets
from .properties import PropertiesPanel
from .gallery import TrackGallery


class GUI:
    """Main GUI controller with sidebar, category tabs, track gallery, and status bar"""
    
    def __init__(self, window):
        self.window = window
        
        # Dimensions
        self.sidebar_width = 0.45
        self.statusbar_height = 0.06
        self.toolbar_height = 0.08
        self.tab_height = 0.08
        
        # Create main sidebar panel (left side)
        self.sidebar = DirectFrame(
            frameColor=Colors.panelColor,
            frameSize=(0, self.sidebar_width, -1, 1),
            relief=DGG.FLAT,
        )
        self.sidebar.reparentTo(self.window.a2dLeftCenter)
        self.sidebar.setPos(0, 0, 0)
        
        # Add subtle border/shadow effect
        self.sidebar_border = DirectFrame(
            parent=self.sidebar,
            frameColor=Colors.panelBorderColor,
            frameSize=(self.sidebar_width - 0.005, self.sidebar_width, -1, 1),
            relief=DGG.FLAT,
        )
        
        # Create toolbar at top of sidebar
        self._createToolbar()
        
        # Create category tabs
        self._createCategoryTabs()
        
        # Create preview/gallery area
        self.preview = TrackGallery(
            self.window, self.sidebar, 
            top_offset=self.toolbar_height + self.tab_height
        )
        
        self.properties_panel = PropertiesPanel(self.window, self.sidebar)
        
        # Create status bar at bottom of screen
        self._createStatusBar()
        
        # Start status update task
        self.window.taskMgr.add(self._updateStatus, "updateStatusTask")
    
    def reset(self):
        """Reset the GUI to initial state (e.g. after mode switch)"""
        self.sidebar.destroy()
        self.sidebar_border.destroy()
        self.preview.destroy()
        self.properties_panel.destroy()
        self.__init__(self.window)
        
    def _createToolbar(self):
        """Create the toolbar with file operation buttons"""
        toolbar_y = 1 - self.toolbar_height / 2
        
        self.toolbar = DirectFrame(
            parent=self.sidebar,
            frameColor=Colors.statusBarColor,
            frameSize=(0, self.sidebar_width, -self.toolbar_height/2, self.toolbar_height/2),
            pos=(0, 0, 1 - self.toolbar_height/2),
            relief=DGG.FLAT,
        )
        
        # App title on the left with logo styling
        self.title_label = DirectLabel(
            parent=self.toolbar,
            text="brio",
            text_font=self.window.font,
            text_scale=0.055,
            text_fg=(1, 1, 1, 1),
            text_align=TextNode.ALeft,
            pos=(0.01, 0, -0.015),
            frameColor=(0, 0, 0, 0),
        )
        
        button_size = 0.028
        button_spacing = 0.075
        start_x = 0.15
        
        buttons = [
            ("New", Assets.icon_new, self.window.stateManager.newProject),
            ("Save", Assets.icon_save, self.window.stateManager.saveStateToFile),
            ("Open", Assets.icon_open, self.window.stateManager.loadStateFromFile),
            ("BOM", Assets.icon_bom, self.window.stateManager.saveBOMToFile),
        ]
        
        self.toolbar_buttons = []
        for i, (tooltip, icon_path, command) in enumerate(buttons):
            btn_texture = self.window.loader.loadTexture(icon_path)
            btn_bg = DirectFrame(
                parent=self.toolbar,
                frameColor=(0, 0, 0, 0),
                frameSize=(-button_size - 0.008, button_size + 0.008, 
                          -button_size - 0.008, button_size + 0.008),
                pos=(start_x + i * button_spacing, 0, 0),
                relief=DGG.FLAT,
            )
            btn = DirectButton(
                parent=btn_bg,
                frameSize=(-button_size, button_size, -button_size, button_size),
                frameTexture=btn_texture,
                pos=(0, 0, 0),
                command=command,
                relief=DGG.FLAT,
                frameColor=(1, 1, 1, 1),
            )
            btn.setTransparency(True)
            self.toolbar_buttons.append((btn_bg, btn, tooltip))
    
    def _createCategoryTabs(self):
        """Create colorful category tab buttons"""
        tab_y = 1 - self.toolbar_height - self.tab_height / 2 
        tab_width = 0.43 / len(Colors.categoryColors)
        
        self.tab_frame = DirectFrame(
            parent=self.sidebar,
            frameColor=(0, 0, 0, 0),
            frameSize=(0, 0.43, -self.tab_height/2, (self.tab_height/2)-0.005),
            pos=(0.01, 0, tab_y),
            relief=DGG.FLAT,
        )
        
        self.category_buttons = {}
        categories = Assets.get_track_categories()
        
        cat_icons = {cat: Assets.category_icon(cat) for cat in categories}
        
        for i, cat in enumerate(categories):
            btn_background = DirectButton(
                parent=self.tab_frame,
                frameColor=Colors.categoryColors[cat],
                frameSize=(-tab_width/2+0.0025, tab_width/2-0.0025, 
                          -self.tab_height/2, self.tab_height/2-0.015),
                pos=(tab_width/2 + i * tab_width, 0, 0),
                relief=DGG.FLAT,
                command=self._onCategorySelect,
                extraArgs=[cat]
            )
            btn = DirectButton(
                parent=btn_background,
                image=self.window.loader.loadTexture(cat_icons[cat]),
                image_scale=(0.02, 0.02, 0.02),
                frameColor=Colors.categoryColors[cat],
                pos=(0, 0, -0.01),
                relief=DGG.FLAT,
                command=self._onCategorySelect,
                extraArgs=[cat]
            )
            btn.setTransparency(True)
            btn_background.setTransparency(True)
            self.category_buttons[cat] = btn
            
        # Highlight initial category
        self._highlightCategory("Straight")
    
    def _highlightCategory(self, category):
        """Visually highlight the selected category tab"""
        for cat, btn in self.category_buttons.items():
            if cat == category:
                btn['image_scale'] = (0.025, 0.025, 0.025)
            else:
                btn['image_scale'] = (0.02, 0.02, 0.02)
    
    def _onCategorySelect(self, category):
        """Handle category tab click"""
        self._highlightCategory(category)
        self.preview.setCategory(category)
    
    def _createStatusBar(self):
        """Create the bottom status bar with info and hints"""
        self.statusbar = DirectFrame(
            frameColor=Colors.statusBarColor,
            frameSize=(-2, 2, 0, self.statusbar_height),
            relief=DGG.FLAT,
        )
        self.statusbar.reparentTo(self.window.a2dBottomCenter)
        
        # Selection info (left)
        self.selection_label = DirectLabel(
            parent=self.statusbar,
            text="No selection",
            text_font=self.window.font,
            text_scale=0.032,
            text_fg=Colors.textLightColor,
            text_align=TextNode.ALeft,
            pos=(-1.7, 0, 0.02),
            frameColor=todecimal(rgba(0, 0, 0, 0)),
        )
        
        # Current track info (center)
        self.track_label = DirectLabel(
            parent=self.statusbar,
            text="Use arrow keys to browse tracks",
            text_font=self.window.font,
            text_scale=0.028,
            text_fg=todecimal(rgba(180, 180, 180, 1)),
            text_align=TextNode.ACenter,
            pos=(0, 0, 0.02),
            frameColor=todecimal(rgba(0, 0, 0, 0)),
        )
        
        # Keyboard hints (right)
        self.hints_label = DirectLabel(
            parent=self.statusbar,
            text="[Enter] Place    [Z] Drag    [Q/E] Rotate    [R/F] Raise/Lower    [X] Flip   [Shift] Modifier key    [WASD] Move camera",
            text_font=self.window.font,
            text_scale=0.025,
            text_fg=todecimal(rgba(140, 140, 140, 1)),
            text_align=TextNode.ARight,
            pos=(1.7, 0, 0.02),
            frameColor=todecimal(rgba(0, 0, 0, 0)),
        )
    
    def _updateStatus(self, task):
        """Update status bar information"""
        num_selected = len(self.window.selector.active_tracks)
        total_tracks = len(self.window.table.tracks)
        
        if num_selected == 0:
            self.selection_label['text'] = f"Tracks: {total_tracks}"
        else:
            self.selection_label['text'] = f"Selected: {num_selected} / {total_tracks}"
        
        return task.cont
