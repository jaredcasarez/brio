"""
Bill of Materials (BOM) exporter
"""

import csv
import os
from direct.showbase import DirectObject
from ..logging import get_logger

logger = get_logger(__name__)

class BOMExporter(DirectObject.DirectObject):
    """Exports track inventory as a CSV bill of materials"""
    
    def __init__(self, window):
        self.window = window
        
    def exportBOM(self, filepath):
        """Export currently selected tracks as BOM file"""
        if not self.window.stateManager.getState():
            logger.warning("No tracks to export")
            return
            
        # Use selected tracks if multiple are selected, otherwise use all tracks
        tracks_to_include = (
            list(self.window.selector.active_tracks) 
            if len(self.window.selector.active_tracks) > 1 
            else list(self.window.table.tracks)
        )
        
        track_files = {}
        for track in tracks_to_include:
            if track.track_file not in track_files:
                track_files[track.track_file] = 1
            else:
                track_files[track.track_file] += 1
                
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=['Track file', 'Quantity'])
            writer.writeheader()
            for track_file, quantity in track_files.items():
                writer.writerow({
                    'Track file': os.path.basename(track_file).split('.')[0], 
                    'Quantity': quantity
                })
                
        logger.info(f"Exported selected tracks to {filepath}")
