"""
Track model class
"""

from panda3d.core import (
    Vec3,
    CollisionNode,
    BitMask32,
)
from ..logging import get_logger

logger = get_logger(__name__)

class Track:
    """Represents a single track piece in the scene"""
    
    def __init__(
        self, window, parent, track_file, track_tag_name, track_tag="track", **kwargs
    ):
        self.connections = {'male': [], 'female': []}
        self.window = window
        name = track_file.split('/')[-1].split('.')[0]
        self.scenenodepath = self.window.loader.loadModel(track_file)
        self.tracknodepath = self.scenenodepath.find("**/+GeomNode")
        track_tag_name = f"{name}_{len(self.window.table.tracks)}"
        self.tracknodepath.setTag(track_tag, track_tag_name)
        self.track_file = track_file
        self.children = self.scenenodepath.getChildren()
        self.center_offset = (
            self.tracknodepath.getPos() - self.tracknodepath.getBounds().getCenter()
        )
        self.z_offset = self.tracknodepath.getPos().z - self.tracknodepath.getTightBounds()[0].z
        self.nodepath = parent.attachNewNode("pivot")
        self.tracknodepath.reparentTo(self.nodepath)
        self.tracknodepath.setName(track_tag_name)
        self.tracknodepath.setDepthOffset(1)
        logger.debug('textstage: %s', self.tracknodepath.findAllTextureStages())
        logger.debug('texts: %s', self.tracknodepath.findAllTextures())
        self.tracknodepath.setPos(self.center_offset.x, self.center_offset.y, self.z_offset)
        self.nodepath.setPos(kwargs.get("pos", Vec3(0, 0, 0)))
        self.nodepath.setHpr(kwargs.get("hpr", Vec3(0, 0, 0)))
        self.nodepath.setScale(kwargs.get("scale", Vec3(1, 1, 1)))
        self.collisionNode = self.tracknodepath.attachNewNode(
            CollisionNode(f"{track_tag_name}_collision")
        )
        self.planes = []
        if track_tag == "track":
            for child in self.children:
                if "plane" in child.getName().lower():
                    self.planes.append(child)
                    child.reparentTo(self.tracknodepath)
                    child.hide()
                    child.node().setIntoCollideMask(BitMask32.bit(4))
                    child.node().setFromCollideMask(BitMask32.bit(4))

                if "sphere" in child.getName().lower():
                    child.reparentTo(self.tracknodepath)
                    child.hide()
                    if child.getName().startswith("male"):
                        child.node().setIntoCollideMask(BitMask32.bit(1))
                        child.node().setFromCollideMask(BitMask32.bit(2))
                        self.window.trackTraverser.addCollider(
                            child, self.window.trackHandler
                        )
                    else:
                        child.node().setIntoCollideMask(BitMask32.bit(2))
                        child.node().setFromCollideMask(BitMask32.bit(1))

    def removeNode(self):
        """Remove this track from the scene"""
        self.nodepath.removeNode()
    
    def toggleTexture(self, selected=True):
        """Toggle track selection texture"""
        if selected:
            self.tracknodepath.setTexture(
                self.window.selectTextureStage, 
                self.window.selectTexture, 1
            )
        else:
            try:
                self.tracknodepath.clearTexture(self.window.selectTextureStage)
            except:
                pass
