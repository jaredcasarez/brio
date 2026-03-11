"""
File browser dialog using Panda3D DirectGUI components
"""

import os
import glob
import json

from direct.showbase import DirectObject
from direct.gui.DirectGui import (
    DirectFrame, DirectButton, DirectLabel, DirectEntry,
    DirectScrolledFrame, DGG
)
from panda3d.core import Vec3, TextNode

from ..utils import todecimal, rgba
from ..constants import Colors
from ..logging import get_logger

logger = get_logger(__name__)

class FileBrowser(DirectObject.DirectObject):
    """A file browser dialog using only Panda3D DirectGUI components"""
    
    def __init__(self, window, mode="load", file_extension=".trax", 
                 title="File Browser", default_dir="./saves", on_confirm=None, on_cancel=None):
        """
        Initialize the file browser.
        
        Args:
            window: The main application window
            mode: "load" or "save"
            file_extension: File extension filter (e.g., ".trax", ".bom")
            title: Title for the dialog
            default_dir: Starting directory
            on_confirm: Callback function when file is selected (receives filepath)
            on_cancel: Callback function when cancelled
        """
        self.window = window
        self.mode = mode
        self.file_extension = file_extension
        self.title = title
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        self.selected_file = None
        self.file_buttons = []
        
        # Ensure default directory exists
        if not os.path.exists(default_dir):
            os.makedirs(default_dir)
        self.current_dir = os.path.abspath(default_dir)
        
        self._createDialog()
        self._refreshFileList()
    
    def _createDialog(self):
        """Create the file browser dialog UI"""
        # Main dialog frame
        self.dialog_frame = DirectFrame(
            frameColor=Colors.panelColor,
            frameSize=(-0.55, 0.55, -0.45, 0.45),
            relief=DGG.FLAT,
            borderWidth=(0.01, 0.01),
        )
        self.dialog_frame.reparentTo(self.window.aspect2d)
        
        # Title bar
        title_color = Colors.brioBlue if self.mode == "save" else Colors.brioOrange
        self.title_bar = DirectFrame(
            parent=self.dialog_frame,
            frameColor=title_color,
            frameSize=(-0.55, 0.55, 0, 0.06),
            pos=(0, 0, 0.39),
            relief=DGG.FLAT,
        )
        
        DirectLabel(
            parent=self.title_bar,
            text=self.title,
            text_font=self.window.font,
            text_scale=0.04,
            text_fg=Colors.textLightColor,
            pos=(0, 0, 0.015),
            frameColor=(0, 0, 0, 0),
        )
        
        # Path display bar
        self.path_frame = DirectFrame(
            parent=self.dialog_frame,
            frameColor=todecimal(rgba(240, 240, 240, 1)),
            frameSize=(-0.52, 0.52, -0.035, 0.035),
            pos=(0, 0, 0.32),
            relief=DGG.FLAT,
        )
        
        # Parent directory button
        self.parent_btn = DirectButton(
            parent=self.path_frame,
            text="^",
            text_font=self.window.font,
            text_scale=0.035,
            text_fg=Colors.textColor,
            frameSize=(-0.03, 0.03, -0.025, 0.025),
            frameColor=Colors.buttonColor,
            pos=(-0.48, 0, -0.02),
            command=self._goToParent,
            relief=DGG.FLAT,
        )
        
        # Path label
        self.path_label = DirectLabel(
            parent=self.path_frame,
            text=self._getDisplayPath(),
            text_font=self.window.font,
            text_scale=0.025,
            text_fg=Colors.textColor,
            text_align=TextNode.ALeft,
            pos=(-0.43, 0, -0.008),
            frameColor=(0, 0, 0, 0),
        )
        
        # File list scrolled frame
        self.file_list_frame = DirectScrolledFrame(
            parent=self.dialog_frame,
            frameColor=todecimal(rgba(255, 255, 255, 1)),
            frameSize=(-0.52, 0.52, -0.27, 0.27),
            pos=(0, 0, 0.0),
            canvasSize=(-0.5, 0.48, -1, 0),
            scrollBarWidth=0.03,
            verticalScroll_relief=DGG.FLAT,
            verticalScroll_frameColor=todecimal(rgba(200, 200, 200, 1)),
            verticalScroll_thumb_frameColor=Colors.brioBlue,
            horizontalScroll_relief=DGG.FLAT,
            horizontalScroll_frameColor=todecimal(rgba(200, 200, 200, 1)),
            horizontalScroll_thumb_frameColor=Colors.brioBlue,
            relief=DGG.SUNKEN,
            borderWidth=(0.01, 0.01),
        )
        
        # Filename entry (for save mode)
        if self.mode == "save":
            DirectLabel(
                parent=self.dialog_frame,
                text="Filename:",
                text_font=self.window.font,
                text_scale=0.035,
                text_fg=Colors.textColor,
                text_align=TextNode.ALeft,
                pos=(-0.46, 0, -0.33),
                frameColor=(0, 0, 0, 0),
            )
            
            self.filename_entry = DirectEntry(
                parent=self.dialog_frame,
                width=18,
                pos=(-0.25, 0, -0.325),
                text_scale=0.035,
                frameSize=(-0.025, 0.7, -0.02, 0.04),
                frameColor=(1, 1, 1, 1),
                text_fg=Colors.textColor,
                relief=DGG.SUNKEN,
                borderWidth=(0.005, 0.005),
                text_align=TextNode.ALeft,
            )
        
        # Buttons at bottom
        btn_y = -0.41
        confirm_text = "Save" if self.mode == "save" else "Open"
        confirm_color = Colors.brioGreen
        
        self.confirm_btn = DirectButton(
            parent=self.dialog_frame,
            text=confirm_text,
            text_font=self.window.font,
            text_scale=0.035,
            text_fg=Colors.textLightColor,
            frameSize=(-0.1, 0.1, -0.03, 0.05),
            frameColor=confirm_color,
            pos=(-0.15, 0, btn_y),
            command=self._onConfirm,
            relief=DGG.RAISED,
            borderWidth=(0.01, 0.01)
        )
        
        self.cancel_btn = DirectButton(
            parent=self.dialog_frame,
            text="Cancel",
            text_font=self.window.font,
            text_scale=0.035,
            text_fg=Colors.textLightColor,
            frameSize=(-0.1, 0.1, -0.03, 0.05),
            frameColor=Colors.brioRed,
            pos=(0.15, 0, btn_y),
            command=self._onCancel,
            relief=DGG.RAISED,
            borderWidth=(0.01, 0.01)
        )
        
        # New folder button (save mode only)
        if self.mode == "save":
            self.newfolder_btn = DirectButton(
                parent=self.dialog_frame,
                text="New Folder",
                text_font=self.window.font,
                text_scale=0.028,
                text_fg=Colors.textColor,
                frameSize=(-0.1, 0.1, -0.03, 0.05),
                frameColor=Colors.buttonColor,
                pos=(0.42, 0, btn_y),
                command=self._createNewFolder,
                relief=DGG.RAISED,
                borderWidth=(0.01, 0.01)
            )
    
    def _getDisplayPath(self):
        """Get a shortened display path"""
        path = self.current_dir
        max_len = 55
        if len(path) > max_len:
            path = "..." + path[-(max_len-3):]
        return path
    
    def _refreshFileList(self):
        """Refresh the list of files and directories"""
        # Clear existing buttons
        for btn in self.file_buttons:
            btn.destroy()
        self.file_buttons = []
        
        # Update path label
        self.path_label['text'] = self._getDisplayPath()
        
        # Get directory contents
        try:
            items = os.listdir(self.current_dir)
        except PermissionError:
            items = []
        
        # Separate and sort directories and files
        directories = []
        files = []
        
        for item in items:
            full_path = os.path.join(self.current_dir, item)
            if os.path.isdir(full_path):
                directories.append(item)
            elif item.endswith(self.file_extension):
                files.append(item)
        
        directories.sort(key=str.lower)
        files.sort(key=str.lower)
        
        # Calculate canvas size based on number of items
        item_height = 0.055
        total_items = len(directories) + len(files)
        canvas_height = max(0.54, total_items * item_height + 0.05)
        self.file_list_frame['canvasSize'] = (-0.5, 0.45, -canvas_height, 0)
        
        canvas = self.file_list_frame.getCanvas()
        y_pos = -0.03
        
        # Add directories first
        for folder in directories:
            btn = self._createFileButton(canvas, folder, y_pos, is_folder=True)
            self.file_buttons.append(btn)
            y_pos -= item_height
        
        # Add files
        for file in files:
            btn = self._createFileButton(canvas, file, y_pos, is_folder=False)
            self.file_buttons.append(btn)
            y_pos -= item_height
    
    def _createFileButton(self, parent, name, y_pos, is_folder=False):
        """Create a button for a file or folder"""
        icon = "[D] " if is_folder else "[F] "
        display_name = name if is_folder else name.replace(self.file_extension, "")
        
        frame_color = (
            todecimal(rgba(245, 245, 220, 1)) if is_folder 
            else todecimal(rgba(255, 255, 255, 1))
        )
        
        btn = DirectButton(
            parent=parent,
            text=icon + display_name,
            text_font=self.window.font,
            text_scale=0.032,
            text_fg=Colors.textColor if not is_folder else Colors.brioBlue,
            text_align=TextNode.ALeft,
            frameSize=(-0.02, 0.92, -0.022, 0.028),
            frameColor=frame_color,
            pos=(-0.48, 0, y_pos),
            command=self._onItemClick,
            extraArgs=[name, is_folder],
            relief=DGG.FLAT,
        )
        
        # Hover effect
        btn.bind(DGG.ENTER, self._onItemHover, extraArgs=[btn, True])
        btn.bind(DGG.EXIT, self._onItemHover, extraArgs=[btn, False])
        
        return btn
    
    def _onItemHover(self, btn, entering, event=None):
        """Handle hover effect on file buttons"""
        if entering:
            btn['frameColor'] = Colors.buttonActiveColor
        else:
            is_folder = btn['text'].startswith("[D]")
            btn['frameColor'] = (
                todecimal(rgba(245, 245, 220, 1)) if is_folder 
                else todecimal(rgba(255, 255, 255, 1))
            )
    
    def _onItemClick(self, name, is_folder):
        """Handle click on file or folder"""
        full_path = os.path.join(self.current_dir, name)
        
        if is_folder:
            self.current_dir = os.path.abspath(full_path)
            self._refreshFileList()
        else:
            self.selected_file = full_path
            if self.mode == "save" and hasattr(self, 'filename_entry'):
                display_name = name.replace(self.file_extension, "")
                self.filename_entry.enterText(display_name)
            
            # Highlight selected file
            for btn in self.file_buttons:
                if btn['text'] == "[F] " + name.replace(self.file_extension, ""):
                    btn['frameColor'] = Colors.trackColorHighlight
                elif btn['text'].startswith("[F]"):
                    btn['frameColor'] = todecimal(rgba(255, 255, 255, 1))
    
    def _goToParent(self):
        """Navigate to parent directory"""
        parent = os.path.dirname(self.current_dir)
        if parent and parent != self.current_dir:
            self.current_dir = parent
            self._refreshFileList()
    
    def _createNewFolder(self):
        """Create a new folder dialog"""
        self.newfolder_dialog = DirectFrame(
            parent=self.dialog_frame,
            frameColor=Colors.panelColor,
            frameSize=(-0.25, 0.25, -0.1, 0.1),
            pos=(0, 0, 0),
            relief=DGG.RAISED,
            borderWidth=(0.01, 0.01),
        )
        
        DirectLabel(
            parent=self.newfolder_dialog,
            text="Folder Name:",
            text_font=self.window.font,
            text_scale=0.03,
            text_fg=Colors.textColor,
            pos=(0, 0, 0.05),
            frameColor=(0, 0, 0, 0),
        )
        
        self.newfolder_entry = DirectEntry(
            parent=self.newfolder_dialog,
            width=12,
            pos=(0, 0, 0.01),
            text_scale=0.03,
            frameSize=(-0.18, 0.18, -0.025, 0.025),
            frameColor=(1, 1, 1, 1),
            text_fg=Colors.textColor,
        )
        
        DirectButton(
            parent=self.newfolder_dialog,
            text="Create",
            text_font=self.window.font,
            text_scale=0.028,
            text_fg=Colors.textLightColor,
            frameSize=(-0.06, 0.06, -0.02, 0.02),
            frameColor=Colors.brioGreen,
            pos=(-0.1, 0, -0.06),
            command=self._confirmNewFolder,
            relief=DGG.FLAT,
        )
        
        DirectButton(
            parent=self.newfolder_dialog,
            text="Cancel",
            text_font=self.window.font,
            text_scale=0.028,
            text_fg=Colors.textLightColor,
            frameSize=(-0.06, 0.06, -0.02, 0.02),
            frameColor=Colors.brioRed,
            pos=(0.1, 0, -0.06),
            command=lambda: self.newfolder_dialog.destroy(),
            relief=DGG.FLAT,
        )
    
    def _confirmNewFolder(self):
        """Create the new folder"""
        folder_name = self.newfolder_entry.get()
        if folder_name:
            new_path = os.path.join(self.current_dir, folder_name)
            try:
                os.makedirs(new_path)
                self._refreshFileList()
            except OSError as e:
                logger.error(f"Could not create folder: {e}")
        self.newfolder_dialog.destroy()
    
    def _onConfirm(self):
        """Handle confirm button click"""
        filepath = None
        
        if self.mode == "save":
            filename = self.filename_entry.get() if hasattr(self, 'filename_entry') else None
            if filename:
                if not filename.endswith(self.file_extension):
                    filename += self.file_extension
                filepath = os.path.join(self.current_dir, filename)
        else:
            filepath = self.selected_file
        
        if filepath:
            self.dialog_frame.destroy()
            if self.on_confirm:
                self.on_confirm(filepath)
        else:
            logger.warning("No file selected/entered")
    
    def _onCancel(self):
        """Handle cancel button click"""
        self.dialog_frame.destroy()
        if self.on_cancel:
            self.on_cancel()
    
    def destroy(self):
        """Clean up the dialog"""
        if self.dialog_frame:
            self.dialog_frame.destroy()


class FileSelector(DirectObject.DirectObject):
    """Handles file selection dialogs for save/load operations"""
    
    def __init__(self, window):
        self.window = window
        self.saved_files = glob.glob("./saves/*.trax") if os.path.exists("./saves") else []
        self.file_index = 0
        self.file_input = None
        self.result_file = None
    
    def getSavedFiles(self):
        """Refresh the list of saved files"""
        self.saved_files = glob.glob("./saves/*.trax") if os.path.exists("./saves") else []
        return self.saved_files
    
    def askBOM(self):
        """Open file browser dialog to save BOM file"""
        from ..state.exporter import BOMExporter
        
        self.browser = FileBrowser(
            self.window,
            mode="save",
            file_extension=".csv",
            title="Save Bill of Materials",
            default_dir="./boms",
            on_confirm=self._saveBOM,
            on_cancel=None
        )
        
    def _saveBOM(self, filepath):
        """Handle save BOM button click"""
        from ..state.exporter import BOMExporter
        
        exporter = BOMExporter(self.window) 
        exporter.exportBOM(filepath=filepath)
        self.bom_file = filepath
        logger.info(f"Saved BOM to {filepath}")
    
    def askSave(self):
        """Open file browser dialog to save project"""
        self.browser = FileBrowser(
            self.window,
            mode="save",
            file_extension=".trax",
            title="Save Project",
            default_dir="./saves",
            on_confirm=self._savefile,
            on_cancel=None
        )
        
    def _savefile(self, filepath):
        """Handle save button click - save state to file"""
        self.result_file = filepath
        self.window.current_projectfile = os.path.basename(filepath).replace('.trax', '')
        
        state = self.window.stateManager.getState()
        state_reformatted = {
            'tracks': [],
            'table': state.get('table', {'width': 600, 'length': 1200})
        }
        
        for track_data in state.get('tracks', []):
            track_dict = {
                'track_file': track_data['track_file'],
                'pos': {
                    '__type__': 'Vec3', 
                    'values': [
                        track_data['pos'].getX(), 
                        track_data['pos'].getY(), 
                        track_data['pos'].getZ()
                    ]
                },
                'hpr': {
                    '__type__': 'Vec3', 
                    'values': [
                        track_data['hpr'].getX(), 
                        track_data['hpr'].getY(), 
                        track_data['hpr'].getZ()
                    ]
                },
                'scale': {
                    '__type__': 'Vec3', 
                    'values': [
                        track_data['scale'].getX(), 
                        track_data['scale'].getY(), 
                        track_data['scale'].getZ()
                    ]
                },
                'selected': track_data['selected']
            }
            state_reformatted['tracks'].append(track_dict)
        
        with open(filepath, "w") as f:
            json.dump(state_reformatted, f, indent=2)
        
        logger.info(f"Saved project to {filepath}")
    
    def askLoad(self):
        """Open file browser dialog to load project"""
        self.browser = FileBrowser(
            self.window,
            mode="load",
            file_extension=".trax",
            title="Open Project",
            default_dir="./saves",
            on_confirm=self._loadfile,
            on_cancel=None
        )
    
    def _loadfile(self, filepath):
        """Handle load button click - restore state from file"""
        self.result_file = filepath
        
        try:
            with open(filepath, "r") as f:
                unparsed_state = json.load(f)
                logger.info("Loaded state from: %s", filepath)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.info(f"Failed to load file: {e}")
            return
        
        if not unparsed_state:
            logger.info("Failed to load state from file - empty or invalid")
            return
        
        # Handle both old format (list of tracks) and new format (dict with tracks and table)
        if isinstance(unparsed_state, list):
            tracks_data = unparsed_state
            table_data = {'width': 600, 'length': 1200}
        else:
            tracks_data = unparsed_state.get('tracks', [])
            table_data = unparsed_state.get('table', {'width': 600, 'length': 1200})
        
        state = {
            'tracks': [],
            'table': table_data
        }
        
        for track_data in tracks_data:
            track_dict = {
                'track_file': track_data['track_file'],
                'pos': Vec3(*track_data['pos']['values']),
                'hpr': Vec3(*track_data['hpr']['values']),
                'scale': Vec3(*track_data['scale']['values']),
                'selected': track_data['selected']
            }
            state['tracks'].append(track_dict)
        
        self.window.stateManager.restoreState(state)
        self.window.current_projectfile = os.path.basename(filepath).replace('.trax', '')
        logger.info(f"Loaded project: {self.window.current_projectfile}")
    
    def loadFile(self):
        """Show load dialog"""
        self.askLoad()
