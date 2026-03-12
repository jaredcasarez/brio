"""
Main GUI controller
"""

from direct.gui.DirectGui import (
    DirectFrame, DirectButton, DirectLabel, DGG
)
from panda3d.core import TextNode, Vec3

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
            text="trax",
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
            self.toolbar_buttons[-1][1].bind(DGG.ENTER, lambda x, t=tooltip, rel_pos= (0,0,-0.025),relative=self.toolbar_buttons[-1][1], parent=self.sidebar: self._showTooltip(t, -1, relative, parent, rel_pos=rel_pos, text_bg=Colors.panelColor, text_frame=Colors.panelBorderColor, text_scale=0.7))
            self.toolbar_buttons[-1][1].bind(DGG.EXIT, lambda x: self._hideTooltip())
        
    def _showTooltip(self, frametext, updown, relative, parent, rel_pos=(0,0,0), ww=None, **kwargs):
        """Display a tooltip above the toolbar button"""
        if hasattr(self, 'tooltip_label'):
            self.tooltip_label.destroy()
        self.tooltip_label = DirectLabel(
            parent=parent,
            text=frametext,
            text_font=self.window.font,
            text_scale=kwargs.pop('text_scale', 0.025),
            text_fg=Colors.textColor,
            text_align=TextNode.ACenter,
            frameColor=Colors.panelBorderColor,
            pad=(0.005,0.005),
            relief=DGG.FLAT,
            text_wordwrap=ww if ww is not None else len(frametext),
            **kwargs
        )
        z = updown*self.tooltip_label.getHeight()
        self.tooltip_label.setPos(relative, (0,0,0))
        self.tooltip_label.setPos(self.tooltip_label, Vec3(0,0,z)+Vec3(rel_pos))
        self.tooltip_label.setTransparency(True)
    def _hideTooltip(self):
        """Hide the tooltip"""
        if hasattr(self, 'tooltip_label'):
            self.tooltip_label.destroy()
    
    def _createCategoryTabs(self):
        """Create colorful category tab buttons"""
        tab_y = 1 - self.toolbar_height - self.tab_height / 2 
        tab_width = 0.6 / len(Colors.categoryColors)
        
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
        
        
        # Current track info (center)
        self.track_label = DirectLabel(
            parent=self.statusbar,
            text="Use arrow keys to browse tracks",
            text_font=self.window.font,
            text_scale=0.028,
            text_fg=todecimal(rgba(180, 180, 180, 1)),
            text_align=TextNode.ACenter,
            pos=(-1, 0, 0.02),
            frameColor=todecimal(rgba(0, 0, 0, 0)),
        )
        self.control_labels=[]
        control_list = {"[Enter] Place": 'Press enter to place previewed track at your cursor', "[Z] Drag": 'Press z to drag selected piece(s). Snap pieces to cursor with shift', "[Q/E] Rotate":'Rotate selected piece(s) in either direction. Hold shift for smaller increments', "[R/F] Raise/Lower": 'Raise and lower selected piece(s). Useful for elevated pieces', "[X] Flip": 'Flip selected piece(s). Only helpful with Brio tracks', "[Scroll] Zoom":'Zoom camera in towards the point of focus', "[Shift/Cmd+Scroll] Orbit": 'Scroll while holding down either command or shift to orbit up-down and left-right, respectively', "[WASD] Move":'Move point of focus of the camera anywhere within the table surface'}
        control_width=0
        for control, tip in list(control_list.items())[-1:0:-1]:
            self.control_labels.append(DirectButton(
                parent=self.window.a2dBottomRight,
                text=control,
                text_font=self.window.font,
                text_scale=0.025,
                text_fg=todecimal(rgba(140, 140, 140, 1)),
                text_align=TextNode.ABoxedCenter,
                frameColor=todecimal(rgba(0, 0, 0, 0)),
                pad=(-0.1,-0.08),
            ))
            self.control_labels[-1].setPos(-0.5-control_width-self.control_labels[-1].getWidth()/2, 0, 0.02)
            self.control_labels[-1].setTransparency(True)
            control_width+=self.control_labels[-1].getWidth()+0.25
            self.control_labels[-1].bind(DGG.ENTER, lambda x, t=tip, relative=self.control_labels[-1], ww=15, parent=self.window.aspect2d: self._showTooltip(t, 1,relative, parent, ww=ww,rel_pos=(0,0,0.0125), text_bg=Colors.panelColor, text_frame=Colors.panelBorderColor, text_scale=0.0325))
            self.control_labels[-1].bind(DGG.EXIT, lambda x: self._hideTooltip())
            

        
        
        