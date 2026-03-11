"""
Camera control for orbiting around the scene
"""

import math
from direct.showbase import DirectObject

from ..logging import get_logger

logger = get_logger(__name__)


class CameraControl(DirectObject.DirectObject):
    """Orbital camera controls using spherical coordinates"""
    
    def __init__(self, window, camera):
        self.window = window
        self.camera = camera
        
        # Spherical coordinates: radius, azimuthal (xy_angle), polar (z_angle)
        pos = self.camera.getPos()
        self.radius = math.sqrt(pos.getX() ** 2 + pos.getY() ** 2 + pos.getZ() ** 2)
        self.xy_angle = math.degrees(math.atan2(pos.getY(), pos.getX()))
        self.z_angle = (
            math.degrees(math.acos(pos.getZ() / self.radius))
            if self.radius != 0
            else 90
        )
        self.updateCamera()
        
        # Key bindings
        self.accept('keystroke', self.onKeypress)
        self.command_lookup = {"wheel_up": self.moveIn, "control_wheel_up":self.moveUp, "shift_wheel_up":self.moveRight, "wheel_down": self.moveOut, "control_wheel_down": self.moveDown, "shift_wheel_down":self.moveLeft,"wheel_right":self.moveRight, "wheel_left":self.moveLeft, "p": self.lightToggle}
        self.last_press = None
    def onKeypress(self,key):
        
        if self.window.mouseWatcherNode.is_button_down('shift'):
            key=f"shift_{key}"
        if self.window.mouseWatcherNode.is_button_down('control') or self.window.mouseWatcherNode.is_button_down('meta'):
            key = f"control_{key}"
        if key in self.command_lookup and self.last_press == key:
            self.command_lookup[key]()
        self.last_press=key
    def onScrollUp(self):
        if self.window.mouseWatcherNode.is_button_down('s'):
            self.moveLeft()
        else:
            self.moveIn()
    def onScrollDown(self):
        if self.window.mouseWatcherNode.is_button_down('shift'):
            self.moveRight()
        else:
            self.moveOut()
    def updateCamera(self):
        """Convert spherical to cartesian coordinates and update camera"""
        x = (
            self.radius
            * math.sin(math.radians(self.z_angle))
            * math.cos(math.radians(self.xy_angle))
        )
        y = (
            self.radius
            * math.sin(math.radians(self.z_angle))
            * math.sin(math.radians(self.xy_angle))
        )
        z = self.radius * math.cos(math.radians(self.z_angle))
        self.camera.setPos(x, y, z)
        self.camera.lookAt(0, 0, 0)

    def lightToggle(self):
        """Toggle directional lighting"""
        if self.window.render.hasLight(self.window.dlight_render_node):
            self.window.render.setLightOff(self.window.dlight_render_node)
            self.window.render.setLightOff(self.window.fill_light_node)
            logger.info("Directional lights turned off")
        else:
            self.window.render.setLight(self.window.dlight_render_node)
            self.window.render.setLight(self.window.fill_light_node)
            logger.info("Directional lights turned on")

    def moveRight(self):
        self.xy_angle = (self.xy_angle + 5) % 360
        self.updateCamera()

    def moveLeft(self):
        self.xy_angle = (self.xy_angle - 5) % 360
        self.updateCamera()

    def moveUp(self):
        self.z_angle = max(1, self.z_angle - 5)  # Avoid going over the pole
        self.updateCamera()

    def moveDown(self):
        self.z_angle = min(89, self.z_angle + 5)  # Avoid going under the pole
        self.updateCamera()

    def moveIn(self):
        self.radius = max(10, self.radius - 50)
        self.updateCamera()

    def moveOut(self):
        self.radius += 50
        self.updateCamera()
