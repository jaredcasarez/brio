"""
Collision Editor - Tool for adding and editing collision geometry on BAM models

This standalone tool allows you to:
- Load BAM/GLB model files
- Add collision spheres and planes for track connections
- Position, rotate, and scale collision shapes
- Save models with collision data

Controls:
    ` / ~           Next/Previous model
    Tab             Cycle through collision shapes
    Shift+Tab       Toggle male/female collision type
    Enter           Add collision sphere
    Shift+Enter     Add collision plane
    Ctrl+Enter      Save current model
    Backspace       Delete active collision shape
    
    W/S             Move forward/backward
    A/D             Strafe left/right
    Q/E             Rotate shape
    R/V             Move up/down
    F               Flip 180 degrees
    Z/X             Resize shape
    
    Arrow Keys      Orbit camera
    Scroll          Zoom camera
"""

import glob
import math
import os
import shutil
from pathlib import Path
from typing import Optional

from direct.showbase.ShowBase import ShowBase
from direct.showbase import DirectObject
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import (
    CollisionNode,
    CollisionSphere,
    CollisionPlane,
    CollisionTraverser,
    CollisionHandlerQueue,
    Vec3,
    Plane,
    OrthographicLens,
    TextNode,
)
from ..assets import Assets

class BamConverter(ShowBase):
    """Collision editor application for BAM models"""

    def __init__(self, file_extension: str = ".bam"):
        """
        Initialize the collision editor.
        
        Args:
            tracks_dir: Path to the tracks directory containing BAM files.
                       Defaults to ./tracks/bam relative to current directory.
            file_extension: File extension for the models to load. Defaults to ".bam".
        """
        super().__init__()
        self.file_list = []
        self.file_extension = file_extension
        self.eventController = DirectObject.DirectObject()
        self.entities = []
        
        # Key bindings
        self._setup_keybindings()
        self._setup_axis_visual()
        
        self.stats = {
            'name': '',
            'pos': Vec3(0, 0, 0),
            'hpr': Vec3(0, 0, 0),
            'scale': Vec3(1, 1, 1)
        }
        
        self.active = None
        self.showActiveIndicator()
        self.task_mgr.add(self.moveActiveIndicator, "MoveActiveIndicatorTask")
        
        # Setup camera
        self.cam.setPos(300, -300, 300)
        self.cam.lookAt(0, 0, 0)
        lens = OrthographicLens()
        lens.setFilmSize(300, 200)
        self.cam.node().setLens(lens)
        
        # Load file list
        self._load_file_list()
        
        self.modelindex = 0
        self.modelfile = self.file_list[self.modelindex] if self.file_list else None
        
        if self.modelfile:
            self.load()
        
        self.textObject = OnscreenText(
            text='',
            pos=(0, -0.25),
            scale=0.07,
            align=TextNode.ALeft,
            fg=(1, 1, 1, 1),
            bg=(0, 0, 0, 0.5)
        )
        self.textObject.reparentTo(self.a2dTopLeft)
        self.cycleActive()
        self.updateStats()

    def _setup_axis_visual(self):
        """Set up visual indicators for the axes"""
        self.axis = self.loader.loadModel("models/misc/xyzAxis")
        self.axis.reparentTo(self.render)
        self.axis.setPos(100, 50, 0)
        self.axis.setScale(5)
        
    def _setup_keybindings(self):
        """Setup all keyboard event handlers"""
        ec = self.eventController
        
        # Model navigation
        ec.accept('`', self.nextModel)
        ec.accept('shift-`', self.lastModel)
        
        # Entity management
        ec.accept('tab', self.cycleActive)
        ec.accept('shift-tab', self.swapGender)
        ec.accept("enter", self.addSphere)
        ec.accept("shift-enter", self.addPlane)
        ec.accept('control-enter', self.save)
        ec.accept('backspace', self.deleteActive)
        
        # Movement
        ec.accept('w-repeat', self.move, extraArgs=[1])
        ec.accept('w', self.move, extraArgs=[1])
        ec.accept('control-w', self.move, extraArgs=[0.1])
        ec.accept('shift-w', self.move, extraArgs=[50])
        ec.accept('s-repeat', self.move, extraArgs=[-1])
        ec.accept('s', self.move, extraArgs=[-1])
        ec.accept('control-s', self.move, extraArgs=[-0.1])
        ec.accept('shift-s', self.move, extraArgs=[-50])
        ec.accept('a-repeat', self.strafe, extraArgs=[-1])
        ec.accept('d-repeat', self.strafe, extraArgs=[1])
        ec.accept('a', self.strafe, extraArgs=[-1])
        ec.accept('d', self.strafe, extraArgs=[1])
        ec.accept('control-a', self.strafe, extraArgs=[-0.1])
        ec.accept('shift-a', self.strafe, extraArgs=[-50])
        ec.accept('shift-d', self.strafe, extraArgs=[50])
        ec.accept('control-d', self.strafe, extraArgs=[0.1])
        
        # Rotation
        ec.accept('q-repeat', self.rotate, extraArgs=[-1])
        ec.accept('e-repeat', self.rotate, extraArgs=[1])
        ec.accept('q', self.rotate, extraArgs=[-1])
        ec.accept('e', self.rotate, extraArgs=[1])
        ec.accept('shift-q', self.rotate, extraArgs=[-90])
        ec.accept('shift-e', self.rotate, extraArgs=[90])
        ec.accept('control-e', self.rotate, extraArgs=[90, True, True])
        ec.accept('control-q', self.rotate, extraArgs=[90, False, True])
        ec.accept('shift-space', self.rotate, extraArgs=[90, True, False])
        ec.accept('control-space', self.rotate, extraArgs=[90, False, False])
        ec.accept('f', self.flip)
        
        # Scaling
        ec.accept('z', self.resize, extraArgs=[1])
        ec.accept('x', self.resize, extraArgs=[-1])
        
        # Camera controls
        ec.accept('arrow_left', self.camera_orbit, extraArgs=[-10])
        ec.accept('shift-arrow_left', self.camera_orbit, extraArgs=[-1])
        ec.accept('arrow_right', self.camera_orbit, extraArgs=[10])
        ec.accept('shift-arrow_right', self.camera_orbit, extraArgs=[1])
        ec.accept('arrow_up', self.camera_vertical_orbit, extraArgs=[-1])
        ec.accept('shift-arrow_up', self.camera_vertical_orbit, extraArgs=[-15])
        ec.accept('arrow_down', self.camera_vertical_orbit, extraArgs=[1])
        ec.accept('shift-arrow_down', self.camera_vertical_orbit, extraArgs=[15])
        ec.accept('scroll_up', self.camera_zoom, extraArgs=[-1])
        ec.accept('scroll_down', self.camera_zoom, extraArgs=[1])
        
        # Vertical movement
        ec.accept('r', self.vertical_move, extraArgs=[1])
        ec.accept('r-repeat', self.vertical_move, extraArgs=[1])
        ec.accept('shift-r', self.vertical_move, extraArgs=[50])
        ec.accept('v', self.vertical_move, extraArgs=[-1])
        ec.accept('v-repeat', self.vertical_move, extraArgs=[-1])
        ec.accept('shift-v', self.vertical_move, extraArgs=[-50])

    def _load_file_list(self):
        """Load and sort the list of model files from the tracks directory"""
        # Sort by filename
        self.file_list = Assets.get_all_track_files()
        self.file_list = [f for files in self.file_list.values() for f in files]  # Flatten list of lists
        self.filenames = [os.path.basename(f) for f in self.file_list]
        sorted_indices = sorted(range(len(self.filenames)), key=lambda i: self.filenames[i])
        self.file_list = [self.file_list[i] for i in sorted_indices]
        
        print(f"Found {len(self.file_list)} model files")

    def cycleActive(self):
        """Cycle through collision entities"""
        if self.entities:
            if self.active:
                self.active = self.entities[(self.entities.index(self.active) + 1) % len(self.entities)]
            else:
                self.active = self.entities[0]
            self.updateStats()
        print("Active entity:", self.active)
        
    def updateStats(self):
        """Update the stats display"""
        if self.active:
            self.stats['model'] = os.path.basename(self.modelfile).split('.')[0] if self.modelfile else "None"
            self.stats['name'] = self.active.getName()
            self.stats['pos'] = list(self.active.getPos())
            self.stats['hpr'] = list(self.active.getHpr())
            self.stats['scale'] = self.active.getScale()
            self.textObject.setText(
                f"{self.stats['model']}\n{self.stats['name']}\n"
                f"Pos: {self.stats['pos']}\nHpr: {self.stats['hpr']}"
            )

    def showActiveIndicator(self):
        """Show a red sphere indicator at the active entity position"""
        self.active_indicator = self.loader.loadModel("models/misc/sphere")
        self.active_indicator.reparentTo(self.render)
        self.active_indicator.setScale(2)
        self.active_indicator.setColor(1, 0, 0, 1)
        self.active_indicator.set_bin("fixed", 0)
        self.active_indicator.set_depth_test(False)
        self.active_indicator.set_depth_write(False)

    def moveActiveIndicator(self, task):
        """Task to move the indicator to the active entity"""
        if self.active:
            self.active_indicator.setPos(self.active.getPos(self.render))
        return task.cont

    def addSphere(self):
        """Add a new collision sphere"""
        print("Adding sphere")
        collision_node = CollisionNode('male_sphere')
        cnodepath = self.model.attachNewNode(collision_node)
        shape = CollisionSphere(0, 0, 0, 20)
        cnodepath.node().addSolid(shape)
        cnodepath.setColor(1, 0, 0, 1)
        cnodepath.show()
        cnodepath.setPos(self.active.getPos() if self.active else Vec3(0, 0, 0))
        self.entities.append(cnodepath)
        self.active = cnodepath
        self.textObject.setText(f"{self.active.getName()}")
    
    def addPlane(self):
        """Add a new collision plane"""
        print("Adding plane")
        collision_node = CollisionNode('male_plane')
        cnodepath = self.model.attachNewNode(collision_node)
        shape = CollisionPlane(Plane(Vec3(0, 1, 0), 0))
        cnodepath.node().addSolid(shape)
        cnodepath.setPos(self.model.getChild(0).getBounds().getCenter())
        cnodepath.setColor(1, 0, 0, 1)
        cnodepath.show()
        cnodepath.setPos(self.active.getPos() if self.active else Vec3(0, 0, 0))
        self.entities.append(cnodepath)
        self.active = cnodepath
        self.updateStats()
    
    def move(self, amount):
        """Move active entity forward/backward"""
        if self.active:
            self.active.setPos(self.active.getPos() + Vec3(0, amount, 0))
            self.updateStats()

    def strafe(self, amount):
        """Move active entity left/right"""
        if self.active:
            self.active.setPos(self.active.getPos() + Vec3(amount, 0, 0))
            self.updateStats()

    def rotate(self, amount, non_horizontal=False, track=False):
        """Rotate active entity"""
        if track: 
            to_rotate = self.model
            print('rotating model')
        else: to_rotate = self.active
        if self.active or track:
            if non_horizontal:
                to_rotate.setP(to_rotate.getP() + amount)
            elif non_horizontal is None:
                to_rotate.setH(to_rotate.getH() + amount)
            else:
                to_rotate.setR(to_rotate.getR() + amount)
            self.updateStats()

    def flip(self):
        """Flip active entity 180 degrees"""
        if self.active:
            current_h = self.active.getH()
            self.active.setH(current_h + 180 if current_h < 180 else current_h - 180)
            self.updateStats()
    
    def resize(self, amount):
        """Resize active entity"""
        if self.active:
            scale = self.active.getScale()
            new_scale = Vec3(
                max(0.1, scale.x + amount * 0.1),
                max(0.1, scale.y + amount * 0.1),
                max(0.1, scale.z + amount * 0.1)
            )
            self.active.setScale(new_scale)
    
    def camera_orbit(self, amount):
        """Orbit camera horizontally"""
        cam_pos = self.cam.getPos()
        angle_rad = amount * (math.pi / 180)
        new_x = cam_pos.x * math.cos(angle_rad) - cam_pos.y * math.sin(angle_rad)
        new_y = cam_pos.x * math.sin(angle_rad) + cam_pos.y * math.cos(angle_rad)
        self.cam.setPos(new_x, new_y, cam_pos.z)
        self.cam.lookAt(0, 0, 0)
    
    def vertical_move(self, amount):
        """Move active entity up/down"""
        if self.active:
            self.active.setPos(self.active.getPos() + Vec3(0, 0, amount))
            self.updateStats()
    
    def load(self):
        """Load the current model file"""
        if hasattr(self, 'model'):
            self.model.detachNode()
            for entity in self.entities:
                entity.removeNode()
            self.entities.clear()
            
        self.model = self.loader.loadModel(self.modelfile)
        
        for child in self.model.getChildren():
            if child.node().isOfType(CollisionNode.getClassType()):
                print('Found collision child:', child.getName())
                self.entities.append(child)
                self.active = child
                child.wrtReparentTo(self.model)
            print('entities:', self.entities)
            
        self.model.reparentTo(self.render)
        self.model.setPos(0, 0, 0)
        print(f"Loaded model: {self.modelfile}")
        
    def nextModel(self):
        """Load the next model in the list"""
        if not self.file_list:
            return
        self.modelindex = (self.modelindex + 1) % len(self.file_list)
        self.modelfile = self.file_list[self.modelindex]
        print('Loading model:', self.modelfile)
        self.load()
        self.updateStats()
    
    def lastModel(self):
        """Load the previous model in the list"""
        if not self.file_list:
            return
        self.modelindex = (self.modelindex - 1) % len(self.file_list)
        self.modelfile = self.file_list[self.modelindex]
        if hasattr(self, 'model'):
            self.model.detachNode()
            for entity in self.entities:
                entity.removeNode()
            self.entities.clear()
        print('Loading model:', self.modelfile)
        self.load()
        self.updateStats()

    def swapGender(self):
        """Toggle between male and female collision type"""
        if self.active:
            name = self.active.getName()
            
            if name.startswith('male'):
                tag = 'female'
            else:
                tag = 'male'
                
            if 'sphere' in name:
                tag += "_sphere"
            elif "plane" in name:
                tag += "_plane"
                
            self.active.setName(tag)
            self.updateStats()
    
    def save(self):
        """Save the model with collision data"""
        if not self.active or not self.modelfile:
            return
        if not self.modelfile.endswith('_collision.bam'):
            filename = self.modelfile.replace(self.file_extension, '_collision.bam')
            noncollision_dir = Path(self.modelfile).parent / 'noncollision'
            noncollision_dir.mkdir(exist_ok=True)
            
            try:
                shutil.move(self.modelfile, str(noncollision_dir / os.path.basename(self.modelfile)))
            except Exception as e:
                print(f"Error moving file: {e}")
        elif self.modelfile.endswith(self.file_extension) and self.file_extension != '.bam':
            filename = self.modelfile.replace(self.file_extension, '_collision.bam')
        else:
            filename = self.modelfile
            
        self.model.writeBamFile(filename)
        print(f"Saved to {filename}")
        
        # Refresh file list
        self._load_file_list()

    def deleteActive(self):
        """Delete the active collision entity"""
        if self.active:
            self.active.removeNode()
            self.entities.remove(self.active)
            self.active = None
            self.updateStats()
        
    def camera_zoom(self, amount):
        """Zoom camera in/out"""
        cam_pos = self.cam.getPos()
        direction = cam_pos.normalized()
        new_pos = cam_pos + direction * amount * 10
        self.cam.setPos(new_pos)
        self.cam.lookAt(0, 0, 0)
        
    def camera_vertical_orbit(self, amount):
        """Orbit camera vertically"""
        cam_pos = self.cam.getPos()
        radius = math.sqrt(cam_pos.x**2 + cam_pos.y**2)
        sphere_radius = math.sqrt(cam_pos.x**2 + cam_pos.y**2 + cam_pos.z**2)
        angle_rad = amount * (math.pi / 180)
        new_z = cam_pos.z * math.cos(angle_rad) - radius * math.sin(angle_rad)
        new_radius = cam_pos.z * math.sin(angle_rad) + radius * math.cos(angle_rad)
        angle_around_z = math.atan2(cam_pos.y, cam_pos.x)
        new_x = new_radius * math.cos(angle_around_z)
        new_y = new_radius * math.sin(angle_around_z)
        self.cam.setPos(new_x, new_y, new_z)
        self.cam.lookAt(0, 0, 0)


def main():
    """Entry point for collision editor"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Collision Editor - Add collision geometry to BAM models"
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=Assets.get_available_modes(),
        default=Assets.get_mode(),
        help="Asset mode to use (affects which models are loaded)"
    )
    parser.add_argument(
        "--extension",
        type=str,
        default=".bam",
        help="File extension for the models to load"
    )
    args = parser.parse_args()
    Assets.set_mode(args.mode)
    app = BamConverter(file_extension=args.extension)
    app.run()


if __name__ == "__main__":
    main()
