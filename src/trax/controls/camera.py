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
        self.x_offset = 0
        self.y_offset = 0
        self.z_offset = 0
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
        self.command_lookup = {"wheel_up": self.moveIn, "control_wheel_up":self.moveUp, "shift_wheel_up":self.moveRight, "wheel_down": self.moveOut, "control_wheel_down": self.moveDown, "shift_wheel_down":self.moveLeft,"wheel_right":self.moveRight, "wheel_left":self.moveLeft, "w":self.moveForward, 'a': self.strafeLeft, 's':self.moveBackward,'d':self.strafeRight,"p": self.lightToggle}
        self.last_press = None
    def onKeypress(self,key):
        
        if self.window.mouseWatcherNode.is_button_down('shift'):
            key=f"shift_{key}"
        if self.window.mouseWatcherNode.is_button_down('control') or self.window.mouseWatcherNode.is_button_down('meta'):
            key = f"control_{key}"
        if key in ['w','a','s','d']:
            self.handleWASD(key)
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
        ) + self.x_offset
        y = (
            self.radius
            * math.sin(math.radians(self.z_angle))
            * math.sin(math.radians(self.xy_angle))
        ) + self.y_offset
        z = self.radius * math.cos(math.radians(self.z_angle)) + self.z_offset
        self.camera.setPos(x, y, z)
        self.camera.lookAt(self.x_offset, self.y_offset, 0)
        pos = self.camera.getPos()
        math.degrees(math.atan2(pos.getY(), pos.getX()))


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

    def handleWASD(self, key):
        if key in self.command_lookup:
            self.window.taskMgr.add(self.moveTask, extraArgs=[key], appendTask=True)
    
    def moveTask(self, key, task):
        if not self.window.mouseWatcherNode.is_button_down(key):

            self.command_lookup[key]()
            return task.done
        if key in self.command_lookup:
            self.command_lookup[key]()
            
        return task.cont
    def crossingBounds(self, x_change, y_change):
        new_x = self.x_offset + x_change
        new_y = self.y_offset + y_change
        if new_x > self.window.table.width or new_x < -self.window.table.width or new_y > self.window.table.length or new_y < -self.window.table.length:
            logger.debug(f"Camera move to ({new_x:.2f}, {new_y:.2f}) would be out of bounds, skipping move")
            return True
        return False
    def strafeRight(self):
        xy_rad = math.radians(self.xy_angle)
        right_x = math.cos(xy_rad+math.pi/2) * 10
        right_y = math.sin(xy_rad+math.pi/2) * 10
        if self.crossingBounds(right_x, right_y): return
        self.x_offset += right_x
        self.y_offset += right_y
        self.updateCamera()
    def strafeLeft(self):
        xy_rad = math.radians(self.xy_angle)
        left_x = -math.cos(xy_rad+math.pi/2)*10
        left_y = -math.sin(xy_rad+math.pi/2)*10
        if self.crossingBounds(left_x, left_y): return
        self.x_offset += left_x
        self.y_offset += left_y
        self.updateCamera()
    def moveBackward(self):
        xy_rad = math.radians(self.xy_angle)
        backward_x = math.cos(xy_rad)*10
        backward_y = math.sin(xy_rad)*10
        if self.crossingBounds(backward_x, backward_y): return
        self.x_offset += backward_x
        self.y_offset += backward_y
        self.updateCamera()
    def moveForward(self):
        xy_rad = math.radians(self.xy_angle)
        forward_x = -math.cos(xy_rad) * 10
        forward_y = -math.sin(xy_rad) * 10
        if self.crossingBounds(forward_x, forward_y): return
        self.x_offset += forward_x
        self.y_offset += forward_y
        self.updateCamera()
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
