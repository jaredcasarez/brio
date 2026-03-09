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
        self.accept("control-c", self.copySelection)
        self.accept("control-v", self.pasteSelection)

    def copySelection(self):
        """Copy selected tracks to clipboard"""
        self.tracks = []
        for track in list(self.window.selector.active_tracks):
            track_info = {
                "file": track.track_file,
                "pos": track.nodepath.getPos(self.window.table.nodepath),
                "hpr": track.nodepath.getHpr(self.window.table.nodepath),
                "scale": track.nodepath.getScale(self.window.table.nodepath),
            }
            self.tracks.append(track_info)
        logger.info(f"Copied {len(self.tracks)} tracks to clipboard")

    def pasteSelection(self):
        """Paste tracks from clipboard"""
        if not self.tracks:
            logger.warning("Clipboard is empty")
            return
        logger.debug('pasting tracks: %s', self.tracks)
        if self.window.mouseWatcherNode.hasMouse():
            mpos = self.window.mouseWatcherNode.getMouse()
            self.window.pickerRay.setFromLens(
                self.window.camNode, mpos.getX(), mpos.getY()
            )
            self.window.myTraverser.traverse(self.window.table.nodepath)
            if self.window.myHandler.getNumEntries() > 0:
                self.window.myHandler.sortEntries()
                entry = self.window.myHandler.getEntry(0)
                surfacepoint = entry.getSurfacePoint(self.window.table.nodepath)
        else:
            surfacepoint = Vec3(0, 0, 0)
            
        self.window.selector.resetSelection(message=False)
        
        for track_info in list(self.tracks):
            new_track = Track(
                self.window,
                self.window.table.nodepath,
                track_info["file"],
                track_info["file"].split(".")[0],
                pos=surfacepoint + track_info["pos"],
                hpr=track_info["hpr"],
                scale=track_info["scale"],
                track_tag="street" if self.window.mode == "street" else "track",
            )
            self.window.table.tracks.append(new_track)
            self.window.selector.select(new_track, message=False)
            
        self.window.selector.makeCombinedNode()
        logger.info(f"Pasted {len(self.tracks)} tracks from clipboard")
