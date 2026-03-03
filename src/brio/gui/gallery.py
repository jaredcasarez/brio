"""
Track gallery for browsing and placing tracks
"""

import glob
import threading

from direct.showbase import DirectObject
from direct.gui.DirectGui import (
    DirectFrame, DirectButton, DirectLabel, DGG
)
from direct.task import Task
from panda3d.core import TextNode

from ..utils import todecimal, rgba
from ..constants import Colors
from ..assets import Assets
from ..models.track import Track
from ..logging import get_logger

logger = get_logger(__name__)

class TrackGallery:
    """Track selection gallery with thumbnails and preview"""
    
    track_cats = Assets.track_categories
    track_files = Assets.get_all_track_files()
    event_handler = DirectObject.DirectObject()
    
    def __init__(self, window, parent, top_offset=0.2):
        self.window = window
        self.parent = parent
        self.current_cat = "Straight"
        self.cat_indices = {cat: 0 for cat in self.track_cats}
        self.thumbnail_tracks = []
        
        # Gallery dimensions
        self.gallery_width = 0.43
        self.preview_height = 0.35
        self.thumbnail_size = 0.12
        self.thumbnails_per_row = 3
        self.thumbnails_per_column = 3
        
        # Main frame for the gallery
        self.frame = DirectFrame(
            parent=parent,
            frameColor=(0, 0, 0, 0),
            frameSize=(0, self.gallery_width, -1.8, 0),
            pos=(0.01, 0, 1 - top_offset),
            relief=DGG.FLAT,
        )
        
        # Featured track preview (larger, spinning)
        self._createFeaturedPreview()
        
        # Track name display
        self._createTrackLabel()
        
        # Thumbnail grid
        self._createThumbnailGrid()
        
        # Navigation arrows
        self._createNavigation()
        
        # Keyboard bindings
        self.event_handler.accept("arrow_right", self.nextTrack)
        self.event_handler.accept("arrow_left", self.prevTrack)
        self.event_handler.accept("arrow_up", self.nextCategory)
        self.event_handler.accept("arrow_down", self.prevCategory)
        self.event_handler.accept("enter", self.placeTrack)
        
        # Initialize
        self.busy = False
        self.currentTrack()
        while self.busy:
            pass
        self.window.taskMgr.add(self.spinTrack, "spinTrackTask")
        self._preloadTracks()
        self._updateThumbnails()
    
    def _preloadTracks(self):
        """Preload track models for smoother browsing"""
        self.preloaded_models = {}
        for cat, files in self.track_files.items():
            self.preloaded_models[cat] = []
            for file in files:
                model = self.window.loader.loadModel(
                    file, 
                    callback=lambda model, cat=cat: self._preloadCallback(model, cat)
                )
                
    def _preloadCallback(self, model, cat=None):
        model.setShaderAuto()
        self.preloaded_models[cat].append(model)
        
    def _createFeaturedPreview(self):
        """Create the main preview area with spinning track"""
        preview_y = 0
        
        # Preview background with category color
        self.previewBg = DirectFrame(
            parent=self.frame,
            frameColor=Colors.categoryColors[self.current_cat],
            frameSize=(0, self.gallery_width, -self.preview_height, 0),
            pos=(0, 0, preview_y),
            relief=DGG.FLAT,
        )
        
        # Inner preview area (lighter)
        self.previewInner = DirectFrame(
            parent=self.previewBg,
            frameColor=todecimal(rgba(255, 255, 255, 0.9)),
            frameSize=(0.015, self.gallery_width - 0.015, 
                      -self.preview_height + 0.015, -0.015),
            pos=(0, 0, 0),
            relief=DGG.FLAT,
        )
        
        # This is where the 3D track preview will be rendered
        self.trackFrame = self.previewInner
    
    def _createTrackLabel(self):
        """Create the track name label below preview with scrolling text"""
        self.label_area_height = 0.08
        label_y = -self.preview_height - 0.02
        
        # Container for the label area
        self.label_container = DirectFrame(
            parent=self.frame,
            frameColor=Colors.panelColor,
            frameSize=(0.06, self.gallery_width - 0.06, -self.label_area_height, 0),
            pos=(0, 0, label_y),
            relief=DGG.FLAT,
        )
        
        self.scroll_offset = 0
        self.scroll_direction = 1
        self.scroll_pause = 0
        
        # Track counter below name
        self.counterLabel = DirectLabel(
            parent=self.label_container,
            text="1 / 5",
            text_font=self.window.font,
            text_scale=0.05,
            text_fg=todecimal(rgba(120, 100, 80, 1)),
            text_align=TextNode.ACenter,
            pos=((self.gallery_width) / 2, 0, -0.055),
            frameColor=todecimal(rgba(0, 0, 0, 0)),
        )
        
        # Start scroll task
        self.window.taskMgr.add(self._scrollNameTask, "scrollNameTask")
    
    def _scrollNameTask(self, task):
        """Scroll long track names back and forth"""
        if not hasattr(self, 'nameLabel'):
            return task.cont
        
        text_node = self.nameLabel.component('text0')
        if text_node:
            bounds = text_node.getTightBounds()
            if bounds:
                text_width = (bounds[1][0] - bounds[0][0]) * 0.032
                clip_width = self.gallery_width - 0.14
                
                if text_width > clip_width:
                    if self.scroll_pause > 0:
                        self.scroll_pause -= self.window.globalClock.getDt()
                    else:
                        max_scroll = text_width - clip_width + 0.02
                        self.scroll_offset += (
                            self.scroll_direction * self.window.globalClock.getDt() * 0.03
                        )
                        
                        if self.scroll_offset > max_scroll:
                            self.scroll_offset = max_scroll
                            self.scroll_direction = -1
                            self.scroll_pause = 1.5
                        elif self.scroll_offset < 0:
                            self.scroll_offset = 0
                            self.scroll_direction = 1
                            self.scroll_pause = 1.5
                        
                        self.nameLabel.setPos(0.02 - self.scroll_offset, 0, -0.028)
                else:
                    self.nameLabel.setPos((clip_width - text_width) / 2 + 0.02, 0, -0.028)
                    self.scroll_offset = 0
        
        return task.cont
    
    def _createThumbnailGrid(self):
        """Create grid of track thumbnails with 3D track previews"""
        grid_y = -self.preview_height - self.label_area_height - 0.021
        
        self.thumbnailFrame = DirectFrame(
            parent=self.frame,
            frameColor=(0, 0, 0, 0),
            frameSize=(0, self.gallery_width, -0.5, 0),
            pos=(-0.005, 0, grid_y),
            relief=DGG.FLAT,
        )
        
        self.thumbnail_buttons = []
        self.thumbnail_tracks_np = []
        
        # Create thumbnail slots
        for row in range(self.thumbnails_per_column):
            for col in range(self.thumbnails_per_row):
                idx = row * self.thumbnails_per_row + col
                x = 0.02 + col * (self.thumbnail_size + 0.02 if col > 0 else 0)
                y = -0.02 - row * (self.thumbnail_size + 0.02)
                
                # Outer border frame
                border = DirectFrame(
                    parent=self.thumbnailFrame,
                    frameColor=Colors.panelBorderColor,
                    frameSize=(0, self.thumbnail_size, -self.thumbnail_size, 0),
                    pos=(x, 0, y),
                    relief=DGG.FLAT,
                )
                
                # Inner button with track preview
                btn = DirectButton(
                    parent=border,
                    frameSize=(0.004, self.thumbnail_size - 0.004, 
                              -self.thumbnail_size + 0.004, -0.004),
                    frameColor=Colors.buttonColor,
                    pos=(0, 0, 0),
                    command=self._onThumbnailClick,
                    extraArgs=[idx],
                    relief=DGG.FLAT,
                )
                self.thumbnail_buttons.append(btn)
                self.thumbnail_tracks_np.append(None)
    
    def _createNavigation(self):
        """Create navigation arrows on sides of label area"""
        nav_y = -self.preview_height - 0.02 - self.label_area_height / 2
        
        # Previous button (left arrow)
        self.prevBtn = DirectButton(
            parent=self.frame,
            text="<",
            text_scale=0.04,
            text_fg=Colors.textLightColor,
            text_pos=(0, -0.01),
            frameSize=(-0.025, 0.025, -0.035, 0.035),
            frameColor=Colors.categoryColors[self.current_cat],
            pos=(0.03, 0, nav_y),
            command=self.prevTrack,
            relief=DGG.FLAT,
        )
        
        # Next button (right arrow)
        self.nextBtn = DirectButton(
            parent=self.frame,
            text=">",
            text_scale=0.04,
            text_fg=Colors.textLightColor,
            text_pos=(0, -0.01),
            frameSize=(-0.025, 0.025, -0.035, 0.035),
            frameColor=Colors.categoryColors[self.current_cat],
            pos=(self.gallery_width - 0.03, 0, nav_y),
            command=self.nextTrack,
            relief=DGG.FLAT,
        )
    
    def _onThumbnailClick(self, index):
        """Handle thumbnail click"""
        tracks = self.track_files[self.current_cat]
        if index < len(tracks):
            self.cat_indices[self.current_cat] = index
            self.currentTrack()
            self._updateThumbnails()
    
    def _updateThumbnails(self):
        """Update thumbnail highlights and load track previews"""
        tracks = self.track_files[self.current_cat]
        current_idx = self.cat_indices[self.current_cat]
        
        # Clear existing thumbnail track models
        for np in self.thumbnail_tracks_np:
            if np is not None:
                np.removeNode()
        self.thumbnail_tracks_np = [None] * len(self.thumbnail_buttons)
        
        page_correction = (
            self.cat_indices[self.current_cat] // 
            (self.thumbnails_per_row * self.thumbnails_per_column) * 
            self.thumbnails_per_row * self.thumbnails_per_column
        )
        logger.debug('page: %s', page_correction)
        
        for i, btn in enumerate(self.thumbnail_buttons):
            track_ind = i + page_correction
            if track_ind < len(tracks):
                # Highlight current selection
                if track_ind == current_idx:
                    btn['frameColor'] = Colors.buttonActiveColor
                else:
                    btn['frameColor'] = Colors.buttonColor
                
                # Load track model for thumbnail
                try:
                    track_np = self.window.loader.loadModel(tracks[track_ind])
                    geom_np = track_np.find("**/+GeomNode")
                    if geom_np:
                        thumb_container = btn.attachNewNode(f"thumb_{track_ind}")
                        geom_np.reparentTo(thumb_container)
                        geom_np.setHpr(90, 45, 0)
                        
                        bounds = geom_np.getTightBounds()
                        if bounds:
                            size = bounds[1] - bounds[0]
                            max_dim = max(size[0], size[1], size[2])
                            if max_dim > 0:
                                scale = 0.0005
                                geom_np.setScale(scale, scale, scale)
                            
                            center = (bounds[0] + bounds[1]) / 2
                            geom_np.setPos(-center * scale)
                        
                        thumb_container.setPos(self.thumbnail_size / 2, 0, -self.thumbnail_size / 2)
                        thumb_container.setHpr(-90, 45, 0)
                        
                        self.thumbnail_tracks_np[i] = thumb_container
                    else:
                        track_np.removeNode()
                except Exception as e:
                    logger.warning(f"Could not load thumbnail for {tracks[i]}: {e}")
            else:
                btn['frameColor'] = todecimal(rgba(220, 220, 220, 0.5))
    
    def setCategory(self, category):
        """Change the active category"""
        self.current_cat = category
        self.previewBg['frameColor'] = Colors.categoryColors[category]
        self.prevBtn['frameColor'] = Colors.categoryColors[category]
        self.nextBtn['frameColor'] = Colors.categoryColors[category]
        self.currentTrack()
        self._updateThumbnails()
        self._updateLabels()
    
    def _updateLabels(self):
        """Update track name and counter labels"""
        tracks = self.track_files[self.current_cat]
        current_idx = self.cat_indices[self.current_cat]
        
        if tracks:
            track_name = (
                tracks[current_idx].split('/')[-1]
                .replace('.bam', '')
                .replace('_collision', '')
                .replace('_', ' ')
            )
            if hasattr(self, 'nameLabel'):
                self.nameLabel['text'] = track_name
            if hasattr(self, 'counterLabel'):
                self.counterLabel['text'] = f"{current_idx + 1} / {len(tracks)}"
            self.scroll_offset = 0
            self.scroll_pause = 1.0
        
        # Update status bar if available
        if hasattr(self.window, 'gui') and hasattr(self.window.gui, 'track_label'):
            self.window.gui.track_label['text'] = f"{self.current_cat}: {track_name}"
    
    def spinTrack(self, task):
        """Spin the preview track"""
        if hasattr(self, 'track'):
            self.track.nodepath.setHpr(self.track.nodepath, 0, 0, 1)
        return Task.cont
    
    def generateTrack(self, track_file, stop_event):
        """Generate track model in background thread"""
        while not stop_event.is_set():
            self.new_track = Track(
                self.window,
                self.trackFrame,
                track_file,
                track_file.split(".")[0],
                track_tag="preview",
            )
            if hasattr(self, "track"):
                self.track.nodepath.removeNode()
            self.new_track.nodepath.setScale(0.00125, 0.00125, 0.00125)
            self.new_track.nodepath.setHpr(-90, 45, 0)
            self.new_track.nodepath.setPos(0.215, 0, -0.175)
            self.track = self.new_track
            break
        self._updateLabels()
        self.busy = False
    
    def sendForGeneration(self, track_file):
        """Send track for background generation"""
        if self.busy:
            self.stop_event.set()
        stop_event = threading.Event()
        timed_event = threading.Timer(0.5, stop_event.set)
        timed_event.start()
        self.busy = True
        thread = threading.Thread(target=self.generateTrack, args=(track_file, stop_event))
        thread.start()
        return stop_event
    
    def nextTrack(self):
        """Go to next track in category"""
        track_names = list(self.track_files[self.current_cat])
        if not track_names:
            return
        next_index = self.cat_indices[self.current_cat] = (
            self.cat_indices[self.current_cat] + 1
        ) % len(track_names)
        self.stop_event = self.sendForGeneration(track_names[next_index])
        self.track_file = track_names[next_index]
        self._updateThumbnails()
    
    def currentTrack(self):
        """Load current track"""
        track_names = list(self.track_files[self.current_cat])
        if not track_names:
            return
        current_index = self.cat_indices[self.current_cat]
        self.stop_event = self.sendForGeneration(track_names[current_index])
        self.track_file = track_names[current_index]
    
    def prevTrack(self):
        """Go to previous track in category"""
        track_names = list(self.track_files[self.current_cat])
        if not track_names:
            return
        prev_index = self.cat_indices[self.current_cat] = (
            self.cat_indices[self.current_cat] - 1
        ) % len(track_names)
        self.stop_event = self.sendForGeneration(track_names[prev_index])
        self.track_file = track_names[prev_index]
        self._updateThumbnails()
    
    def nextCategory(self):
        """Go to next category"""
        current_cat_index = self.track_cats.index(self.current_cat)
        next_cat_index = (current_cat_index + 1) % len(self.track_cats)
        self.setCategory(self.track_cats[next_cat_index])
        if hasattr(self.window, 'gui'):
            self.window.gui._highlightCategory(self.current_cat)
    
    def prevCategory(self):
        """Go to previous category"""
        current_cat_index = self.track_cats.index(self.current_cat)
        prev_cat_index = (current_cat_index - 1) % len(self.track_cats)
        self.setCategory(self.track_cats[prev_cat_index])
        if hasattr(self.window, 'gui'):
            self.window.gui._highlightCategory(self.current_cat)
    
    def specifyTrack(self, track_file):
        """Jump to a specific track"""
        if track_file == getattr(self, "track_file", None):
            return
        for cat in self.track_cats:
            if track_file in self.track_files[cat]:
                self.current_cat = cat
                self.cat_indices[self.current_cat] = self.track_files[cat].index(track_file)
                self.stop_event = self.sendForGeneration(track_file)
                self.track_file = track_file
                self._updateThumbnails()
                if hasattr(self.window, 'gui'):
                    self.window.gui._highlightCategory(cat)
                break
    
    def placeTrack(self, message=True):
        """Place the current track on the table"""
        track_files = self.track_files[self.current_cat]
        if not track_files:
            return
        new_track = Track(
            self.window,
            self.window.table.nodepath,
            track_files[self.cat_indices[self.current_cat]],
            self.track_file.split(".")[0],
        )
        self.window.table.tracks.append(new_track)
        self.window.selector.resetSelection(message=False)
        self.window.selector.select(new_track, message=False)
        if message:
            self.window.messenger.send("state change")
    
    def updateLabel(self):
        """Compatibility alias"""
        self._updateLabels()
