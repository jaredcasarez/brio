"""
Table model class - the play surface for track layout
"""

from panda3d.core import (
    NodePath,
    LineSegs,
    CardMaker,
    CollisionNode,
    CollisionPlane,
    BitMask32,
    Plane,
    Point3,
    Vec3,
    GeomNode,
)
from ..constants import Colors
from ..logging import get_logger

logger = get_logger(__name__)

class Table:
    """The table/play surface for laying out tracks"""
    
    def __init__(self, window):
        self.nodepath = NodePath("table")
        self.window = window
        self.width = 600
        self.length = 1200
        self.tick_length = 5
        self.offset = -6
        self.tick_space = 100
        self.tracks = []

        self.setUpTablePlane()
        self.setUpTableGrid()
        self.setUpInfPlane()
    
    def setUpInfPlane(self):
        """Set up an invisible infinite plane for mouse ray collision picking"""
        # Create a collision plane facing up (normal = +Z)
        collision_plane = CollisionPlane(Plane(Vec3(0, 0, 1), Point3(0, 0, 0)))
        
        # Create a collision node and add the plane to it
        self.inf_plane_node = CollisionNode("inf_plane")
        self.inf_plane_node.addSolid(collision_plane)
        
        # Set collision masks - this plane can be collided INTO by rays
        self.inf_plane_node.setIntoCollideMask(GeomNode.getDefaultCollideMask())
        
        self.inf_plane_nodepath = self.nodepath.attachNewNode(self.inf_plane_node)
        self.inf_plane_nodepath.setTag('floor', 'ground')

    def setUpTablePlane(self, redraw=False):
        """Create or redraw the table surface plane"""
        if redraw and hasattr(self, 'tableplane'):
            self.tableplane.removeNode()
        self.tablegen = CardMaker("floor")
        self.tablegen.setFrame(
            self.width / 2, -self.width / 2, -self.length / 2, self.length / 2
        )
        self.tableplane = self.nodepath.attachNewNode(self.tablegen.generate())
        self.tableplane.setTexture(self.window.tableTexture)
        self.tableplane.setColor(Colors.tableColor)
        self.tableplane.setHpr(0, 90, 0)
        self.tableplane.setPos(0, 0, 0)
        self.tableplane.setTag("floor", "ground")
        self.tableplane.setDepthOffset(-1)

    def setUpTableGrid(self, redraw=False):
        """Create or redraw the table grid lines"""
        if redraw and hasattr(self, 'grid_node'):   
            self.grid_node.removeNode()
        self.grid = LineSegs("grid")
        self.grid.set_thickness(3)
        self.grid.set_color(Colors.gridColor)
        
        halfwidth = int(self.width // 2)
        halflength = int(self.length // 2)
        
        for line in range(0, halflength + 1, self.tick_space):
            self.grid.moveTo(-halfwidth, line, 0.1)
            self.grid.drawTo(halfwidth, line, 0.1)
        for line in range(0, -halflength - 1, -self.tick_space):
            self.grid.moveTo(-halfwidth, line, 0.1)
            self.grid.drawTo(halfwidth, line, 0.1)
        for line in range(0, halfwidth + 1, self.tick_space):
            self.grid.moveTo(line, -halflength, 0.1)
            self.grid.drawTo(line, halflength, 0.1)
        for line in range(0, -halfwidth - 1, -self.tick_space):
            self.grid.moveTo(line, -halflength, 0.1)
            self.grid.drawTo(line, halflength, 0.1)
            
        grid_geom = self.grid.create()
        self.grid_node = self.nodepath.attachNewNode(grid_geom)
        self.grid_node.setColor(Colors.gridColor)
        self.grid_node.setTag("floor", "ground")
        self.grid_node.setPos(0, 0, -0.2)
        self.grid_node.setDepthOffset(-1)
    
    def resize(self, dimension, which='width', message=True):
        """Resize the table dimensions"""
        if which == 'width':
            self.width = dimension
        elif which == 'length':
            self.length = dimension
        self.tablegen.setFrame(
            self.width / 2, -self.width / 2, -self.length / 2, self.length / 2
        )
        logger.debug('resizing table: %s new dimension: %s', which, dimension)
        self.setUpTablePlane(redraw=True)
        self.setUpTableGrid(redraw=True)
        if message:
            self.window.messenger.send("state change")
        
    def clearTracks(self, tracks=None, message=True):
        """Remove tracks from the table"""
        if tracks is None:
            tracks = self.tracks
        logger.debug('clearing tracks: %s', tracks)
        for track in list(tracks):
            track.nodepath.removeNode()
            if self.window.selector.rbc_nodepath:
                self.window.selector.rbc_nodepath.removeNode()
                self.window.selector.rbc_nodepath = None
                self.window.selector.rbc = None
            if track in self.window.selector.active_tracks:
                self.window.selector.active_tracks.remove(track)
        self.tracks = [track for track in self.tracks if track not in tracks]
        if message:
            self.window.messenger.send("state change")
