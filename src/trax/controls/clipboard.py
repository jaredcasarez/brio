"""
Clipboard handling for copy/paste operations
"""

from direct.showbase import DirectObject
from panda3d.core import Vec3

from ..models.track import Track
from ..logging import get_logger

logger = get_logger(__name__)


class Clipboard(DirectObject.DirectObject):
    """Handles copy/paste operations for track selections"""
    
    def __init__(self, window):
        self.window = window
        self.tracks = []
        self.accept('keystroke', self.onKeypress)
        self.command_lookup = {"control_c": self.copySelection, "control_v": self.pasteSelection}

    def onKeypress(self, key):
        """Handle keypress events for clipboard control"""
        if self.window.mouseWatcherNode.is_button_down('shift'):
            key = f"shift_{key}"
        if self.window.mouseWatcherNode.is_button_down('control') or self.window.mouseWatcherNode.is_button_down('meta'):
            key = f"control_{key}"
        if key in self.command_lookup:
            self.command_lookup[key]()
    def copySelection(self):
        """Copy selected tracks to clipboard"""
        self.tracks = []
        for track in list(self.window.selector.active_tracks):
            track_pos = track.nodepath.getPos(self.window.selector.rbc_nodepath)
            track_pos.setZ(track.nodepath.getPos(self.window.table.inf_plane_nodepath).getZ())
            track_info = {
                "file": track.track_file,
                "pos": track_pos,
                "hpr": track.nodepath.getHpr(self.window.selector.rbc_nodepath),
                "scale": track.nodepath.getScale(self.window.selector.rbc_nodepath),
                "type": track.track_type,
            }
            self.tracks.append(track_info)
        logger.info(f"Copied {len(self.tracks)} tracks to clipboard")

    def pasteSelection(self):
        """Paste tracks from clipboard"""
        if not self.tracks:
            logger.warning("Clipboard is empty")
            return
        logger.debug('pasting tracks: %s', self.tracks)
        surfacepoint = Vec3(0, 0, 0)
        if self.window.mouseWatcherNode.hasMouse():
            mpos = self.window.mouseWatcherNode.getMouse()
            self.window.pickerRay.setFromLens(
                self.window.camNode, mpos.getX(), mpos.getY()
            )
            self.window.myTraverser.traverse(self.window.table.inf_plane_nodepath)
            self.window.myHandler.sortEntries()
            if self.window.myHandler.getNumEntries() > 0:
                for entry in self.window.myHandler.getEntries():
                    if entry.getIntoNode().hasTag('floor'):
                        surfacepoint = entry.getSurfacePoint(self.window.table.inf_plane_nodepath)
            
        self.window.selector.resetSelection(message=False)
        
        for track_info in list(self.tracks):
            new_pos = surfacepoint + track_info["pos"]
            new_pos.setZ(track_info['pos'].getZ())
            new_track = Track(
                self.window,
                self.window.table.nodepath,
                track_info["file"],
                track_info["file"].split(".")[0],
                pos=new_pos,
                hpr=track_info["hpr"],
                scale=track_info["scale"],
                track_type=track_info["type"],
            )
            self.window.table.tracks.append(new_track)
            self.window.selector.select(new_track, message=False)
            
        self.window.selector.makeCombinedNode()
        logger.info(f"Pasted {len(self.tracks)} tracks from clipboard")
