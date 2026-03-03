"""
Main application entry point
"""

from direct.showbase.ShowBase import ShowBase
from panda3d.core import (
    AmbientLight,
    DirectionalLight,
    CollisionNode,
    CollisionRay,
    CollisionHandlerQueue,
    GeomNode,
    CollisionTraverser,
    TextureStage,
    AntialiasAttrib,
    WindowProperties,
)
import simplepbr

from .logging import LogLevel, configure_logging

from .utils import todecimal, rgba
from .constants import Colors
from .assets import Assets
from .models.table import Table
from .controls.selection import SelectionControl
from .controls.camera import CameraControl
from .controls.clipboard import Clipboard
from .state.manager import StateManager
from .gui.main_gui import GUI
from .logging import configure_logging

import argparse

class BrioApp(ShowBase):
    """Main application class"""
    
    # Color constants - expose for backwards compatibility
    tableColor = Colors.tableColor
    gridColor = Colors.gridColor
    trackColor = Colors.trackColor
    trackColorShadow = Colors.trackColorShadow
    trackColorHighlight = Colors.trackColorHighlight
    selectColor = Colors.selectColor
    brioRed = Colors.brioRed
    brioGreen = Colors.brioGreen
    brioBlue = Colors.brioBlue
    brioYellow = Colors.brioYellow
    brioOrange = Colors.brioOrange
    panelColor = Colors.panelColor
    panelBorderColor = Colors.panelBorderColor
    buttonColor = Colors.buttonColor
    buttonActiveColor = Colors.buttonActiveColor
    textColor = Colors.textColor
    textLightColor = Colors.textLightColor
    backgroundColor = Colors.backgroundColor
    statusBarColor = Colors.statusBarColor
    categoryColors = Colors.categoryColors
    
    dt = 0.0005
    
    def __init__(self):
        # Initialize the application
        ShowBase.__init__(self)
        wp = WindowProperties()
        wp.setSize(self.pipe.display_width, self.pipe.display_height)
        self.win.requestProperties(wp)

        # Initialize PBR with shadow settings
        simplepbr.init(
            enable_shadows=True,
            use_normal_maps=True,
            use_emission_maps=False,
        )
        ShowBase.disableMouse(self)
        
        # Set warm background color
        self.setBackgroundColor(self.backgroundColor)
        
        self.current_projectfile = None
        
        # Load textures using Assets paths
        self.trackBaseTexture = self.loader.loadTexture(Assets.plywood_base)
        self.trackBaseTextureStage = TextureStage("base")
        self.trackBaseTextureStage.setMode(TextureStage.MReplace)
        self.trackBaseTextureStage.setSort(10)
        
        self.trackTexture = self.loader.loadTexture(Assets.plywood_brown)
        self.trackTextureStage = TextureStage("track")
        self.trackTextureStage.setMode(TextureStage.MReplace)
        self.trackTextureStage.setSort(5)
        
        self.selectTexture = self.loader.loadTexture(Assets.plywood_blue)
        self.selectTextureStage = TextureStage("select")
        self.selectTextureStage.setMode(TextureStage.MReplace)
        self.selectTextureStage.setSort(5)
        
        self.tableTexture = self.loader.loadTexture(Assets.paper)
        self.font = self.loader.loadFont(Assets.roadgeek_font)

        # Set up collision detection for picking
        self.selector = SelectionControl(self)
        self.myTraverser = CollisionTraverser()
        self.myHandler = CollisionHandlerQueue()
        self.pickerNode = CollisionNode("mouseRay")
        self.pickerNP = self.camera.attachNewNode(self.pickerNode)
        self.pickerNode.setFromCollideMask(GeomNode.getDefaultCollideMask())
        self.pickerRay = CollisionRay()
        self.trackHandler = CollisionHandlerQueue()
        self.pickerNode.addSolid(self.pickerRay)
        self.myTraverser.addCollider(self.pickerNP, self.myHandler)
        self.trackTraverser = CollisionTraverser()
        self.connections = []

        # Set up the scene
        self.stateManager = StateManager(self)
        self.table = Table(self)
        self.table.nodepath.reparentTo(self.render)
        self.gui = GUI(self)
        self.preview = self.gui.preview
        self.clipboard = Clipboard(self)

        # Set up lighting
        self.dlight = DirectionalLight("dlight")
        self.alight = AmbientLight("alight")
        
        # Reduced intensities for PBR
        self.dlight.setColor((0.7, 0.65, 0.6, 1))
        self.alight.setColor((0.15, 0.14, 0.12, 1))
        
        # Higher resolution shadows with bias
        self.dlight.setShadowCaster(True, 4096, 4096)
        self.dlight.getLens().setNearFar(100, 3000)
        self.dlight.getLens().setFilmSize(1500, 1500)
        
        self.dlight_render_node = self.render.attachNewNode(self.dlight)
        self.alight_render_node = self.render.attachNewNode(self.alight)
        self.dlight_render_node.setPos(-800, 800, 1200)
        self.alight_render_node.setPos(1000, -1000, 1000)
        self.dlight_render_node.lookAt(0, 0, 0)
        
        # Add fill light
        self.fill_light = DirectionalLight("fill_light")
        self.fill_light.setColor((0.2, 0.22, 0.25, 1))
        self.fill_light_node = self.render.attachNewNode(self.fill_light)
        self.fill_light_node.setPos(600, -600, 400)
        self.fill_light_node.lookAt(0, 0, 0)
        self.render.setLight(self.fill_light_node)

        self.render.setLight(self.alight_render_node)
        self.render.setLight(self.dlight_render_node)
        self.render.setShaderAuto()
        self.render.setAntialias(AntialiasAttrib.MAuto)
        self.aspect2d.setAntialias(AntialiasAttrib.MAuto)

        # Set up camera
        self.cam_pos = (1000, 1000, 1000)
        self.camera.setPos(*self.cam_pos)
        self.camera.lookAt(0, 0, 0)
        self.camera_controller = CameraControl(self, self.camera)
        self.units = []


def main():
    """Entry point"""
    parser = argparse.ArgumentParser(description="Brio - A Panda3D-based train track layout designer")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--logfile", type=str, help="Specify a log file")
    args = parser.parse_args()

    if args.debug:
        configure_logging(level=LogLevel.DEBUG, console=True)
    elif args.logfile:
        configure_logging(level=LogLevel.INFO, console=False, log_file=args.logfile)
    
    app = BrioApp()
    app.run()


if __name__ == "__main__":
    main()
