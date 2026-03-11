"""
Main application entry point
"""

from direct.showbase.ShowBase import ShowBase
from direct.showbase.DirectObject import DirectObject
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
    Material,
    ModifierButtons,   
)
import simplepbr

from .utils import todecimal, rgba
from .constants import Colors
from .assets import Assets
from .models.table import Table
from .controls.selection import SelectionControl
from .controls.camera import CameraControl
from .controls.clipboard import Clipboard
from .state.manager import StateManager
from .gui.main_gui import GUI


class SandboxApp(ShowBase):
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
    
    def __init__(self, mode: str = 'brio', **kwargs):
        # Set asset mode before loading any assets
        Assets.set_mode(mode)
        self.mode = mode
        
        # Initialize the application
        ShowBase.__init__(self)
        wp = WindowProperties()
        wp.setSize(self.pipe.display_width, self.pipe.display_height)
        self.win.requestProperties(wp)
        self.show_collisions = kwargs.get('show_collisions', False)
        # Initialize PBR with shadow settings
        simplepbr.init(
            enable_shadows=True,
            use_normal_maps=True,
            use_emission_maps=False,
        )
        ShowBase.disableMouse(self)
        
        # Set up key event handling
        self.mouseWatcherNode.set_modifier_buttons(ModifierButtons())
        self.buttonThrowers[0].node().set_modifier_buttons(ModifierButtons())
        self.buttonThrowers[0].node().setButtonDownEvent('keystroke')
        
        # Set warm background color
        self.setBackgroundColor(self.backgroundColor)
        
        self._preloadTracks()
        self.current_projectfile = None
        
        # Load textures using Assets paths
        self.trackBaseTexture = self.loader.loadTexture(Assets.get_texture("track_texture"))
        self.trackBaseTextureStage = TextureStage("base")
        self.trackBaseTextureStage.setMode(TextureStage.MDecal)
        self.trackBaseTextureStage.setSort(5)
        
        self.myMaterial = Material()
        self.myMaterial.setShininess(100)  # Make it less shiny
        self.myMaterial.setSpecular(todecimal(rgba(51, 51, 51, 1)))  # Reduce specular highlights
        self.myMaterial.setAmbient(todecimal(rgba(204, 204, 204, 1)))  # Add some ambient reflection
        self.myMaterial.setDiffuse(todecimal(rgba(204, 204, 204, 1)))  # Set diffuse color to match track color
        
        self.trackTexture = self.loader.loadTexture(Assets.get_texture("track_texture"))
        self.trackTextureStage = TextureStage("track")
        self.trackTextureStage.setMode(TextureStage.MReplace)
        self.trackTextureStage.setSort(10)
        
        self.selectTexture = self.loader.loadTexture(Assets.get_texture("select_texture"))
        self.selectTextureStage = TextureStage("select")
        self.selectTextureStage.setMode(TextureStage.MReplace)
        self.selectTextureStage.setSort(10)
        
        self.tableTexture = self.loader.loadTexture(Assets.get_texture("table_texture"))
        self.font = self.loader.loadFont(Assets.roadgeek_font)

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


        # Set up camera
        self.cam_pos = (1000, 1000, 1000)
        self.camera.setPos(*self.cam_pos)
        self.camera.lookAt(0, 0, 0)
        self.camera_controller = CameraControl(self, self.camera)
        self.units = []

    def _preloadTracks(self):
        """Preload track models for smoother browsing"""
        files=Assets.get_all_track_files(ignore_mode=True)
        self.preloaded_models = {mode:{cat: [] for cat in files[mode]} for mode in files}
        for mode in files:
            for cat in files[mode]:
                for file in files[mode][cat]:
                    self.loader.loadModel(
                        file, 
                        callback=lambda model, cat=cat, mode=mode: self._preloadCallback(model, cat, mode)
                    )
                
    def _preloadCallback(self, model, cat, mode):
        model.setShaderAuto()
        structure = list(self.preloaded_models.keys()), list(self.preloaded_models[mode].keys())
        self.preloaded_models[mode][cat].append(model)

    def toggleMode(self):
        """Toggle between 'brio' and 'citystreets' modes"""
        current_mode = self.mode
        new_mode = 'citystreets' if current_mode == 'brio' else 'brio'
        self.setMode(new_mode)

    def setMode(self, mode):
        """Switch between 'brio' and 'citystreets' modes"""
        if mode == self.mode:
            return  # No change
        self.mode = mode
        Assets.set_mode(mode)
        self.gui.reset()
        
    
    @property
    def mode(self):
        return Assets._mode
    
    @mode.setter
    def mode(self, value):
        Assets.set_mode(value)