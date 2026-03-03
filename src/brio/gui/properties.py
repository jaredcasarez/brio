"""
Properties panel for track and table settings
"""

from direct.gui.DirectGui import (
    DirectFrame, DirectLabel, DirectSlider, DGG
)
from panda3d.core import TextNode

from ..constants import Colors
from ..logging import get_logger

logger = get_logger(__name__)

class PropertiesPanel:
    """Panel for displaying and editing properties of the selected track(s)"""
    
    def __init__(self, window, parent):
        self.window = window
        self.frame = DirectFrame(
            parent=parent,
            frameColor=Colors.panelColor,
            frameSize=(0.01, 0.44, -1.1, -0.2),
            pos=(0, 0, 0.15),
            relief=DGG.FLAT,
        )
        self.label = DirectLabel(
            parent=self.frame,
            text="Parameters",
            text_font=self.window.font,
            text_scale=0.04,
            text_fg=Colors.textColor,
            text_align=TextNode.ALeft,
            pos=(0.035, 0, -0.25),
            frameColor=(0, 0, 0, 0),
        )
        
        self.makePropertiesTable()
        
    def makePropertiesTable(self):
        """Create the properties table with sliders"""
        # Main container frame for all sliders
        self.sliders_container = DirectFrame(
            parent=self.frame,
            frameColor=(0, 0, 0, 0),
            frameSize=(0.02, 0.4, -0.7, 0),
            pos=(0.035, 0, -0.15),
            relief=DGG.FLAT,
        )
        
        self.width_frame_border = DirectFrame(
            parent=self.sliders_container,
            frameColor=Colors.panelBorderColor,
            frameSize=(-0.005, 0.385, -0.265, -0.135),
            pos=(0, 0, 0),
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
            frameSize=(-0.005, 0.385, -0.265, -0.135),
            pos=(0, 0, -0.15),
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
