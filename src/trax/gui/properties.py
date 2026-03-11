"""
Properties panel for track and table settings
"""

from direct.gui.DirectGui import (
    DirectFrame, DirectLabel, DirectSlider, DirectButton, DGG
)
from panda3d.core import TextNode

from ..constants import Colors
from ..logging import get_logger
from ..assets import Assets

logger = get_logger(__name__)

class PropertiesPanel:
    """Panel for displaying and editing properties of the selected track(s)"""
    
    def __init__(self, window, parent):
        self.window = window
        self.frame = DirectFrame(
            parent=parent,
            frameColor=(0,0,0,0),
            frameSize=(0.01, 0.44, -1.1, -0.7),
            pos=(0, 0, -0.1),
            relief=DGG.FLAT,
        )
        
        # Load mode icons
        self.brio_active = loader.loadTexture(Assets.icon_brio_active)
        self.brio_inactive = loader.loadTexture(Assets.icon_brio_inactive)
        self.citystreets_active = loader.loadTexture(Assets.icon_citystreets_active)
        self.citystreets_inactive = loader.loadTexture(Assets.icon_citystreets_inactive)
        
        self.brio_mode_button = DirectButton(
            parent=self.frame,
            image=self.brio_inactive if self.window.mode!='brio' else self.brio_active,
            image_scale=0.085,
            frameColor=(0, 0, 0, 0),
            pos=(0.11125, 0, -0.735),
            relief=DGG.FLAT,
            command=self._setMode,
            extraArgs=['brio'],
        )
        self.brio_mode_button.bind(DGG.ENTER, lambda x: self._onModeButtonEnter(self.brio_mode_button, 'brio'))
        self.brio_mode_button.bind(DGG.EXIT, lambda x: self._onModeButtonExit(self.brio_mode_button, 'brio'))
        
        self.street_mode_button = DirectButton(
            parent=self.frame,
            image=self.citystreets_inactive if self.window.mode!='citystreets' else self.citystreets_active,
            image_scale=0.085,
            frameColor=(0, 0, 0, 0),
            pos=(0.32, 0, -0.75),
            relief=DGG.FLAT,
            command=self._setMode,
            extraArgs=['citystreets'],
        )
        
        self.street_mode_button.bind(DGG.ENTER, lambda x: self._onModeButtonEnter(self.street_mode_button, 'citystreets'))
        self.street_mode_button.bind(DGG.EXIT, lambda x: self._onModeButtonExit(self.street_mode_button, 'citystreets'))
        self.brio_mode_button.setTransparency(True)
        self.street_mode_button.setTransparency(True)
        self._disabledColor = (
            Colors.buttonColor[0] * 0.5,
            Colors.buttonColor[1] * 0.5,
            Colors.buttonColor[2] * 0.5,
            Colors.buttonColor[3],
        )
        self._disabledTextColor = (
            Colors.textColor[0] * 0.4,
            Colors.textColor[1] * 0.4,
            Colors.textColor[2] * 0.4,
            Colors.textColor[3],
        )
        self.citystreets_label = DirectLabel(
            parent=self.frame,
            text="CityStreets",
            text_font=self.window.font,
            text_scale=0.03,
            text_fg=Colors.textColor,
            text_align=TextNode.ALeft,
            pos=(0.24, 0, -0.875),
            frameColor=(0, 0, 0, 0),
        )
        self.tracks_label = DirectLabel(
            parent=self.frame,
            text="Brio",
            text_font=self.window.font,
            text_scale=0.03,
            text_fg=Colors.textColor,
            text_align=TextNode.ALeft,
            pos=(0.0775, 0, -0.875),
            frameColor=(0, 0, 0, 0),
        )
    
        self.makePropertiesTable()
        self.window.accept('tab', self._switchMode)
        # Initialize button states after all widgets are created
        # self.updateModeButtons()
    
    def _setMode(self, mode):
        """Set the application mode and update button states"""
        if self.window.mode != mode:
            self.window.setMode(mode)
            # self.updateModeButtons()
    
    def _switchMode(self):
        if self.window.mode == 'brio':
            self.window.setMode('citystreets')
        else:
            self.window.setMode('brio')
    def _onModeButtonEnter(self, button, mode):
        """Highlight mode button on hover"""
        # if self.window.mode != mode:
        button['image_scale'] = 0.11
        button.setColorScale(1.3, 1.3, 1.3, 1)
    
    def _onModeButtonExit(self, button, mode):
        """Reset mode button color on hover exit"""
        # if self.window.mode != mode:
        button['image_scale'] = 0.085
        button.setColorScale(1, 1, 1, 1)

    def makePropertiesTable(self):
        """Create the properties table with sliders"""
        # Main container frame for all sliders
        self.sliders_container = DirectFrame(
            parent=self.frame,
            frameColor=(0, 0, 0, 0),
            frameSize=(0.02, 0.78, -0.7, 0),
            pos=(0.475, 0, -0.55),
            relief=DGG.FLAT,
        )
        
        self.width_frame_border = DirectFrame(
            parent=self.sliders_container,
            frameColor=Colors.panelBorderColor,
            frameSize=(0.005, 0.385, -0.265, -0.135),
            pos=(0.35, 0, -0.025),
        )
        
        # Width slider frame
        self.width_frame = DirectFrame(
            parent=self.width_frame_border,
            frameColor=Colors.panelColor,
            frameSize=(0, 0.38, -0.26, -0.14),
            pos=(0, 0, 0), 
            relief=DGG.FLAT,
        )
        self.width_adjust = DirectSlider(
            parent=self.width_frame,
            range=(200, 5000),
            value=self.window.table.width,
            pageSize=200,
            scrollSize=200,
            command=lambda: self.resizeTable('width'),
            frameSize=(0.02, 0.36, -0.1, -0.05),
            pos=(0, 0, -0.1),
            thumb_frameSize=(-0.01, 0.01, -0.02, 0.02),
            frameColor=(0.2, 0.2, 0, 1),
            thumb_color=(0.8, 0.8, 0.8, 1),
        )
        self.width_label = DirectLabel(
            parent=self.width_frame,
            text="Table width: {} cm".format(int(self.window.table.width / 10)),
            text_font=self.window.font,
            text_scale=0.03,
            text_fg=Colors.textColor,
            text_align=TextNode.ALeft,
            pos=(0.02, 0, -0.225),
            frameColor=(0, 0, 0, 0),
        )
        
        # Length slider frame
        self.length_frame_border = DirectFrame(
            parent=self.sliders_container,
            frameColor=Colors.panelBorderColor,
            frameSize=(0.005, 0.38, -0.265, -0.135),
            pos=(-0.025, 0, -0.025),
        )
        self.length_frame = DirectFrame(
            parent=self.length_frame_border,
            frameColor=Colors.panelColor,
            frameSize=(0, 0.38, -0.26, -0.14),
            pos=(0, 0, 0),
        )
        self.length_adjust = DirectSlider(
            parent=self.length_frame,
            range=(200, 5000),
            value=self.window.table.length,
            pageSize=200,
            scrollSize=200,
            command=lambda: self.resizeTable('length'),
            frameSize=(0.02, 0.36, -0.1, -0.05),
            pos=(0, 0, -0.1),
            thumb_frameSize=(-0.01, 0.01, -0.02, 0.02),
            frameColor=(0.2, 0.2, 0.2, 1),
            thumb_color=(0.8, 0.8, 0.8, 1),
        )
        self.length_label = DirectLabel(
            parent=self.length_frame,
            text="Table length: {} cm".format(int(self.window.table.length / 10)),
            text_font=self.window.font,
            text_scale=0.03,
            text_fg=Colors.textColor,
            text_align=TextNode.ALeft,
            pos=(0.02, 0, -0.225),
            frameColor=(0, 0, 0, 0),
        )
    
    def resizeTable(self, which):
        """Handle table resize from slider"""
        logger.debug('resizing table: %s value: width=%s length=%s', 
                     which, self.width_adjust['value'], self.length_adjust['value'])
        value = self.width_adjust['value'] if which == 'width' else self.length_adjust['value']
        
        if value % 200 != 0:
            value = round(value / 200) * 200
            if which == 'width':
                self.width_adjust['value'] = value
            else:
                self.length_adjust['value'] = value
                
        if which == 'width':
            self.width_label['text'] = "Table width: {} cm".format(int(value / 10))
        else:
            self.length_label['text'] = "Table length: {} cm".format(int(value / 10))
            
        self.window.table.resize(value, which=which)
    
    def destroy(self):
        """Clean up the properties panel"""
        self.frame.destroy()
