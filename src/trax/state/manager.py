"""
State management for undo/redo functionality
"""

from trax.assets import Assets
from direct.showbase import DirectObject
from ..logging import get_logger

logger = get_logger(__name__)

class StateManager(DirectObject.DirectObject):
    """Manages application state for undo/redo operations"""
    
    def __init__(self, window):
        self.window = window
        self.current_state = []
        self.undo_stack = []
        self.redo_stack = []
        self.command_lookup={'control_z':self.undo, 'control_y':self.redo}
        self.accept('keystroke', self.onKeypress)
        self.accept('state change', self.storeState)

    def onKeypress(self, key):
        if self.window.mouseWatcherNode.is_button_down('control') or self.window.mouseWatcherNode.is_button_down('meta'):
            key=f"control_{key}"
        print(key)
        if key in self.command_lookup:
            self.command_lookup[key]()

    def printState(self, state, label="State"):
        """Debug print of a state"""
        logger.debug(f"{label}:")
        for ind, track in enumerate(state['tracks']):
            logger.debug(f"    Track {ind}:")
            for key, value in track.items():
                logger.debug(f"        {key}: {value}")
        logger.debug("    Table:")
        for key, value in state['table'].items():
            logger.debug(f"        {key}: {value}")

    def storeState(self):
        """Store a deep copy of the current state of tracks"""
        state = self.getState()
        logger.debug('is state same: %s', state == self.undo_stack[-1] if self.undo_stack else False)
        if self.undo_stack and state == self.undo_stack[-1]:
            logger.debug("State unchanged, not storing duplicate state")
            return
        else:
            for ind, track in enumerate(state['tracks']):
                logger.debug(f"Track {ind}: {track['track_file']} at {track['pos']} selected={track['selected']}")
        self.undo_stack.append(self.current_state)
        self.current_state = state
        self.printState(state, label="Recorded State")
        self.redo_stack.clear()  # Clear redo stack on new action
    
    def getState(self):
        """Get the current state as a dictionary"""
        logger.debug("Current tracks: %s", self.window.table.tracks)
        return {
            'tracks': [
                {
                    "track_file": track.track_file,
                    "pos": track.nodepath.getPos(self.window.table.inf_plane_nodepath),
                    "hpr": track.nodepath.getHpr(self.window.table.inf_plane_nodepath),
                    "scale": track.nodepath.getScale(self.window.table.inf_plane_nodepath),
                    "selected": track in self.window.selector.active_tracks,
                } for track in self.window.table.tracks
            ],
            'table': {
                'width': self.window.table.width,
                'length': self.window.table.length,
            }
        }

    def saveStateToFile(self):
        """Open save dialog"""
        # Import here to avoid circular imports
        from ..gui.file_browser import FileSelector
        fs = FileSelector(self.window)
        fs.askSave()
    
    def loadStateFromFile(self):
        """Open load dialog"""
        from ..gui.file_browser import FileSelector
        fs = FileSelector(self.window)
        fs.askLoad()

    def saveBOMToFile(self):
        """Open BOM export dialog"""
        from ..gui.file_browser import FileSelector
        fs = FileSelector(self.window)
        fs.askBOM()

    def restoreState(self, state):
        """Restore application state from a state dictionary"""
        # Import here to avoid circular imports
        from ..models.track import Track
        
        self.window.selector.resetSelection(message=False)
        self.window.table.clearTracks(message=False)
        
        for track_data in state['tracks']:
            new_track = Track(
                self.window,
                self.window.table.nodepath,
                track_data["track_file"],
                track_data["track_file"].split(".")[0],
                track_tag="citystreets" if self.window.mode == "citystreets" else "track",
            )
            new_track.nodepath.setPos(track_data["pos"])
            new_track.nodepath.setHpr(track_data["hpr"])
            new_track.nodepath.setScale(track_data["scale"])
            self.window.table.tracks.append(new_track)
            if track_data["selected"]:
                self.window.selector.select(new_track, message=False)
                
        self.window.selector.makeCombinedNode()
        self.window.table.resize(state['table']['width'], which='width', message=False)
        self.window.table.resize(state['table']['length'], which='length', message=False)

    def undo(self):
        """Undo the last action"""
        if self.undo_stack:
            current_state = self.getState()
            self.printState(current_state, label="Current State before Undo")
            if len(self.undo_stack) < 2:
                logger.warning("Undo stack is empty, cannot undo")
                return
            self.redo_stack.append(current_state)
            last_state = self.undo_stack.pop()
            self.printState(last_state, label="Restoring State")
            self.restoreState(last_state)
            logger.debug(f"Undo performed. Undo stack size: {len(self.undo_stack)}, Redo stack size: {len(self.redo_stack)}")
        else:
            logger.warning("Undo stack is empty, cannot undo")

    def redo(self):
        """Redo the last undone action"""
        if self.redo_stack:
            current_state = self.getState()
            self.undo_stack.append(current_state)
            next_state = self.redo_stack.pop()
            self.printState(next_state, label="Restoring State")
            self.restoreState(next_state)
            logger.debug(f"Redo performed. Undo stack size: {len(self.undo_stack)}, Redo stack size: {len(self.redo_stack)}")
        else:
            logger.warning("Redo stack is empty, cannot redo")

    def newProject(self):
        """Start a new project, clearing all state"""
        self.window.selector.resetSelection(message=False)
        self.window.table.clearTracks(message=False)
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.current_state = []
        self.window.current_projectfile = None
        logger.info("New project created, all states cleared")
