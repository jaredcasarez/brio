"""
Selection control for track manipulation
"""

from direct.showbase import DirectObject
from panda3d.core import (
    Vec3,
    RigidBodyCombiner,
    NodePath,
)

from ..logging import get_logger

logger = get_logger(__name__)


class SelectionControl(DirectObject.DirectObject):
    """Handles track selection, movement, rotation, and snapping"""
    
    def __init__(self, window):
        self.window = window
        self.active_tracks = []
        self.connection_tolerance = 50
        self.angle_tolerance = 91
        
        # Key bindings
        self.accept("control-a", self.selectAll)
        self.accept("control-shift-a", self.resetSelection)
        self.accept("control-mouse1", self.handleClick, extraArgs=['multiselect'])
        self.accept("mouse1", self.handleClick, extraArgs=['normal'])
        self.accept("shift-mouse1", self.handleClick, extraArgs=['connections'])
        self.accept("z", self.dragStart)
        self.accept("q", self.animate, extraArgs=[self.rotateTrack, 90])
        self.accept("shift-q", self.animate, extraArgs=[self.rotateTrack, 15])
        self.accept("e", self.animate, extraArgs=[self.rotateTrack, -90])
        self.accept("shift-e", self.animate, extraArgs=[self.rotateTrack, -15])
        self.accept("escape", self.resetSelection)
        self.accept("backspace", self.deleteSelection)
        self.accept("r", self.animate, extraArgs=[self.raiseTrack, 50])
        self.accept("f", self.animate, extraArgs=[self.raiseTrack, -50])
        self.accept("shift-r", self.animate, extraArgs=[self.raiseTrack, 1])
        self.accept("shift-f", self.animate, extraArgs=[self.raiseTrack, -1])
        self.accept("x", self.animate, extraArgs=[self.flipTrack, 180])
        
        self.selection = None
        self.rbc = None
        self.rbc_nodepath = None

    def selectAll(self):
        """Select all tracks on the table"""
        self.resetSelection(message=False)
        for track in list(self.window.table.tracks):
            track.toggleTexture(selected=True)
            self.active_tracks.append(track)
        self.makeCombinedNode()
        self.window.messenger.send("state change")

    def deleteSelection(self, message=True):
        """Delete selected tracks"""
        if self.selection:
            self.window.table.clearTracks(list(self.active_tracks), message=False)
            self.active_tracks = []
            self.selection = None
            if self.rbc_nodepath:
                self.rbc_nodepath.removeNode()
                self.rbc_nodepath = None
                self.rbc = None
            if message:
                self.window.messenger.send("state change")

    def select(self, track, message=True, rbc_refresh=True):
        """Add a track to the selection"""
        if track not in list(self.active_tracks):
            track.toggleTexture(selected=True)
            self.active_tracks.append(track)
            if rbc_refresh:
                self.makeCombinedNode()
            if message:
                self.window.messenger.send("state change")

    def deselect(self, track, message=True, rbc_refresh=True):
        """Remove a track from the selection"""
        if track in list(self.active_tracks):
            track.toggleTexture(selected=False)
            track.nodepath.wrtReparentTo(self.window.table.nodepath)
            self.active_tracks.remove(track)
            if rbc_refresh:
                self.makeCombinedNode()
            if message:
                self.window.messenger.send("state change")

    def findMousePick(self):
        """Find which track the mouse is pointing at"""
        if self.window.mouseWatcherNode.hasMouse():
            mpos = self.window.mouseWatcherNode.getMouse()
            self.window.pickerRay.setFromLens(
                self.window.camNode, mpos.getX(), mpos.getY()
            )
            self.window.myTraverser.traverse(self.window.table.nodepath)
            if self.window.myHandler.getNumEntries() > 0:
                self.window.myHandler.sortEntries()
                entries = [
                    self.window.myHandler.getEntry(i)
                    for i in range(self.window.myHandler.getNumEntries())
                ]
                entry = entries[0]
                pickedObj = entry.getIntoNodePath()
                track = pickedObj.findNetTag("track")
                if track.isEmpty():
                    track = pickedObj.findNetTag("street")
                if not track.isEmpty():
                    track = self.findTrackByNodePath(track)
                    return track
        return None

    def handleClick(self, mode):
        """Handle mouse click for selection"""
        track = self.findMousePick()
        if track:
            self.window.preview.specifyTrack(track.track_file)
            surfacepoint = self.window.myHandler.getEntry(0).getSurfacePoint(
                self.window.table.nodepath
            )
            track_origin = track.nodepath.getPos(self.window.table.nodepath)
            offset = surfacepoint - track_origin
            
            if track in list(self.active_tracks):
                if mode == 'connections':
                    connected_tracks = self.getConnectedTracks(track)
                    logger.debug('connected_tracks: %s', connected_tracks)
                    for connected_track in list(connected_tracks):
                        if connected_track in list(self.active_tracks):
                            self.deselect(connected_track, rbc_refresh=False)
                    self.makeCombinedNode()
                else:
                    self.deselect(track)
            else:
                if mode == 'connections':
                    connected_tracks = self.getConnectedTracks(track)
                    logger.debug('connected_tracks: %s', connected_tracks)
                    for connected_track in list(connected_tracks):
                        if connected_track not in list(self.active_tracks):
                            self.select(connected_track, rbc_refresh=False)
                    self.makeCombinedNode()
                else:
                    if mode != 'multiselect':
                        self.resetSelection(message=False)
                    self.select(track)
        elif mode not in ["multiselect", "connections"]:
            self.resetSelection()
            self.selection = None

    def resetSelection(self, message=True):
        """Clear all selections"""
        for track in list(self.active_tracks):
            self.deselect(track, message=False, rbc_refresh=False)
        self.active_tracks = []
        self.makeCombinedNode()
        if message:
            self.window.messenger.send("state change")

    def dragStart(self):
        """Begin dragging the selection"""
        if self.selection:
            if self.window.myHandler.getNumEntries() > 0:
                surfacepoint = self.window.myHandler.getEntry(0).getSurfacePoint(
                    self.window.table.nodepath
                )
                self.drag_offset = surfacepoint - self.selection.getPos(
                    self.window.table.nodepath
                )
                self.window.taskMgr.add(self.dragTask, "dragTask", appendTask=True)
                self.window.myHandler.clearEntries()

    def dragTask(self, task):
        """Task for dragging selection with mouse"""
        if not self.selection:
            self.window.taskMgr.remove("dragTask")
            return task.done
            
        z = self.selection.getZ()
        if self.window.mouseWatcherNode.hasMouse():
            mpos = self.window.mouseWatcherNode.getMouse()
            self.window.pickerRay.setFromLens(
                self.window.camNode, mpos.getX(), mpos.getY()
            )
            self.window.myTraverser.traverse(self.window.table.nodepath)
            
            if self.window.myHandler.getNumEntries() > 0 and any(
                self.window.myHandler.getEntry(i).getIntoNodePath().hasNetTag("floor")
                for i in range(self.window.myHandler.getNumEntries())
            ):
                for entry in [
                    self.window.myHandler.getEntry(i)
                    for i in range(self.window.myHandler.getNumEntries())
                ]:
                    if entry.getIntoNodePath().hasNetTag("floor"):
                        new_pos = entry.getSurfacePoint(self.window.table.nodepath)

                x = new_pos.getX() - self.drag_offset.getX()
                y = new_pos.getY() - self.drag_offset.getY()
                self.selection.setPos(self.window.table.nodepath, x, y, z)
                
        if not self.window.mouseWatcherNode.is_button_down("z"):
            self.window.taskMgr.remove("dragTask")
            self.onCollision()
            self.window.messenger.send("state change")
            self.makeCombinedNode()
            return task.done

        return task.cont

    def dissolveCombinedNode(self):
        """Break apart the combined selection node"""
        logger.debug('dissolving combined node')
        if self.rbc_nodepath:
            for track in list(self.active_tracks):
                logger.debug('reparenting track: %s', track)
                track.nodepath.wrtReparentTo(self.window.table.nodepath)
            self.rbc_nodepath.removeNode()
            self.rbc_subnodepath.removeNode()
            self.rbc_nodepath = None
            self.rbc = None

    def traverseConnectedTracks(self, track, visited=None):
        """Find collision entries for connected tracks"""
        self.window.trackTraverser.traverse(self.window.table.nodepath)
        track_entries = []
        if self.window.trackHandler.getNumEntries() > 0:
            self.window.trackHandler.sortEntries()
        for entry in self.window.trackHandler.getEntries():
            logger.debug('Collision detected between: %s and %s', entry.getFromNodePath(), entry.getIntoNodePath())
            both_tagged = (
                entry.getFromNodePath().getParent().hasNetTag("track") and 
                entry.getIntoNodePath().getParent().hasNetTag("track")
            ) or (
                entry.getFromNodePath().getParent().hasNetTag("street") and
                entry.getIntoNodePath().getParent().hasNetTag("street")
            )
            special_case = ((entry.getFromNodePath().getParent().hasNetTag("track") and entry.getIntoNodePath().getParent().hasNetTag("street")) or (entry.getFromNodePath().getParent().hasNetTag("street") and entry.getIntoNodePath().getParent().hasNetTag("track"))) and ('rail' in self.findTrackByNodePath(entry.getFromNodePath().getParent()).name or 'rail' in self.findTrackByNodePath(entry.getIntoNodePath().getParent()).name)
            if not both_tagged and not special_case:   
                logger.debug('Skipping entry without track tags: %s and %s', entry.getFromNodePath(), entry.getIntoNodePath())
                continue
            track_entries.append(entry)
        return track_entries
    
    def getConnectedTracks(self, track, tracks_to_check=None, connected_tracks=None):
        """Find all tracks connected to the given track through connections"""
        if connected_tracks is None:
            connected_tracks = []
        if tracks_to_check is None:
            tracks_to_check = list(self.window.table.tracks)
        
        if track in connected_tracks:
            return connected_tracks
        
        connected_tracks.append(track)
        self.window.trackTraverser.traverse(self.window.table.nodepath)
        
        if self.window.trackHandler.getNumEntries() > 0:
            self.window.trackHandler.sortEntries()
            for entry in self.window.trackHandler.getEntries():
                from_track = self.findTrackByNodePath(entry.getFromNodePath().getParent())
                into_track = self.findTrackByNodePath(entry.getIntoNodePath().getParent())
                
                if from_track == track:
                    if into_track not in connected_tracks:
                        self.getConnectedTracks(into_track, tracks_to_check, connected_tracks)
                elif into_track == track:
                    if from_track not in connected_tracks:
                        self.getConnectedTracks(from_track, tracks_to_check, connected_tracks)
        
        self.window.trackHandler.clearEntries()
        return connected_tracks   
    
    def onCollision(self, entries=None):
        """Handle track connection/snapping on collision"""
        if entries is None:
            entries = self.traverseConnectedTracks(
                list(self.active_tracks)[0]
            ) if list(self.active_tracks) else []
            
        for entry in entries:
            from_active = self.findTrackByNodePath(
                entry.getFromNodePath().getParent()
            ) in list(self.active_tracks)
            into_active = self.findTrackByNodePath(
                entry.getIntoNodePath().getParent()
            ) in list(self.active_tracks)
            
            if entry.getFromNodePath().getPos() == entry.getIntoNodePath().getPos():
                logger.debug('already aligned: %s and %s', entry.getFromNodePath(), entry.getIntoNodePath())
                continue
                
            if (from_active != into_active):
                moving_plane, stable_plane = self.getCollisionPlanes(entry)
                if moving_plane and stable_plane:
                    moving_plane_pos = moving_plane.getPos(self.window.table.nodepath)
                    stable_plane_pos = stable_plane.getPos(self.window.table.nodepath)
                    distance = (moving_plane_pos - stable_plane_pos).length()
                    angle_diff = self.getAngleDifference(moving_plane, stable_plane)
                    
                    if distance <= self.connection_tolerance and angle_diff <= self.angle_tolerance:
                        logger.debug(f'Auto-adjusting connection (distance: {distance:.2f}, angle: {angle_diff:.2f}°)')
                        self.handleCollision(entry)
                        entries.remove(entry)
                        break
                    else:
                        if distance < 0.1 and angle_diff < 0.1:
                            logger.debug('Exact collision detected')
                            self.handleCollision(entry)
                            entries.remove(entry)
                            break
                        else:
                            logger.debug(f'Collision detected but not within snapping thresholds (distance: {distance:.2f}, angle: {angle_diff:.2f}°)')
                else:
                    logger.debug('Collision detected but could not determine planes for entry: %s', entry)
            else:
                logger.debug('Collision detected between active tracks, skipping snapping: %s and %s', entry.getFromNodePath(), entry.getIntoNodePath())
            
        self.window.trackHandler.clearEntries()

    def getAngleDifference(self, moving_plane, stable_plane):
        """Calculate the angular difference between two connection planes"""
        moving_h = moving_plane.getH(self.window.table.nodepath)
        stable_h = stable_plane.getH(self.window.table.nodepath)
        diff = stable_h - moving_h
        
        while diff > 180:
            diff -= 360
        while diff < -180:
            diff += 360
            
        angle_error = abs(abs(diff) - 180)
        return angle_error

    def handleCollision(self, entry):
        """Process a collision entry and align tracks"""
        logger.debug('Handling collision for entry: %s', entry)
        moving_plane, stable_plane = self.getCollisionPlanes(entry)
        if moving_plane is None or stable_plane is None:
            logger.debug("Could not determine collision planes for entry: %s", entry)
            return

        male_plane = (
            moving_plane if moving_plane.getName().startswith("male") else stable_plane
        )
        female_plane = (
            moving_plane if moving_plane.getName().startswith("female") else stable_plane
        )
        logger.debug("Aligning connection between: %s and %s", male_plane, female_plane)
        logger.debug("checking connected %s", self.window.connections)
        self.alignConnection(moving_plane, stable_plane)

    def getCollisionPlanes(self, entry):
        """Get the connection planes from a collision entry"""
        from_sphere = entry.getFromNodePath()
        from_track = self.findTrackByNodePath(from_sphere.getParent())
        into_sphere = entry.getIntoNodePath()
        into_track = self.findTrackByNodePath(into_sphere.getParent())
        
        male_sphere = (
            from_sphere if from_sphere.getName().startswith("male") 
            else into_sphere if into_sphere.getName().startswith("male") 
            else None
        )
        female_sphere = (
            into_sphere if into_sphere.getName().startswith("female") 
            else from_sphere if from_sphere.getName().startswith("female") 
            else None
        )
        if male_sphere is None or female_sphere is None:
            return None, None
        
        moving_track = (
            from_track if from_track in list(self.active_tracks) 
            else into_track if into_track in list(self.active_tracks) 
            else None
        )
        stable_track = from_track if moving_track == into_track else into_track
        moving_sphere = male_sphere if moving_track == from_track else female_sphere
        stable_sphere = female_sphere if moving_sphere == male_sphere else male_sphere
        
        if moving_track is None or stable_track is None:
            return None, None
        
        moving_plane = None
        stable_plane = None
        
        for plane in moving_track.planes:
            if moving_sphere.getBounds().contains(plane.getPos()):
                moving_plane = plane
                break

        for plane in stable_track.planes:
            if stable_sphere.getBounds().contains(plane.getPos()):
                stable_plane = plane
                break
    
        return moving_plane, stable_plane

    def alignConnection(self, moving_plane, stable_plane):
        """Align two tracks at their connection planes"""
        moving_track = self.findTrackByPlane(moving_plane)
        stable_track = self.findTrackByPlane(stable_plane)
        moving_plane_h = moving_plane.getH(self.window.table.nodepath)
        stable_plane_h = stable_plane.getH(self.window.table.nodepath)

        heading_diff = stable_plane_h - moving_plane_h

        while heading_diff > 180:
            heading_diff -= 360
        while heading_diff < -180:
            heading_diff += 360

        current_hpr = moving_track.nodepath.getHpr()
        self.rbc_nodepath.setH(self.rbc_nodepath.getH() + heading_diff - 180)
        
        moving_plane_pos = moving_plane.getPos(self.window.table.nodepath)
        stable_plane_pos = stable_plane.getPos(self.window.table.nodepath)
        plane_offset = stable_plane_pos - moving_plane_pos
        logger.debug("Plane offset: %s", plane_offset)
        
        track_pos = moving_track.nodepath.getPos(self.window.table.nodepath)
        new_x = track_pos.getX() + plane_offset.getX()
        new_y = track_pos.getY() + plane_offset.getY()
        new_z = track_pos.getZ() + plane_offset.getZ()
        new_pos = Vec3(new_x, new_y, new_z)
        
        rbc_offset = self.rbc_nodepath.getPos(self.window.table.nodepath) - track_pos
        self.rbc_nodepath.setPos(self.window.table.nodepath, new_pos + rbc_offset)

    def makeCombinedNode(self):
        """Create a combined node for all selected tracks"""
        logger.debug("Creating combined node for selected tracks...")
        
        self.dissolveCombinedNode()
        self.rbc = RigidBodyCombiner("combined")
        self.rbc_subnodepath = NodePath(self.rbc)
        minpoint, maxpoint = None, None
        is_new = False
        
        for track in list(self.active_tracks):
            track.nodepath.wrtReparentTo(self.rbc_subnodepath)
            if track.nodepath.getTightBounds() is not None:
                if minpoint is None or minpoint > track.nodepath.getTightBounds()[0]:
                    minpoint = track.nodepath.getTightBounds()[0]
                if maxpoint is None or maxpoint < track.nodepath.getTightBounds()[1]:
                    maxpoint = track.nodepath.getTightBounds()[1]
                    
        logger.debug("Collecting combined node geometry...")
        self.rbc.collect()
        
        if minpoint is None or maxpoint is None:
            minpoint = Vec3(0, 0, 0)
            maxpoint = Vec3(0, 0, 0)
            
        center_offset = self.rbc_subnodepath.getPos() - ((minpoint + maxpoint) / 2)
        logger.debug("Center offset for combined node: %s", center_offset)
        
        self.rbc_nodepath = self.window.table.nodepath.attachNewNode("rbc_nodepath")
        self.rbc_subnodepath.reparentTo(self.rbc_nodepath)
        self.rbc_subnodepath.setPos(center_offset)
        self.selection = self.rbc_nodepath
        self.rbc_nodepath.wrtReparentTo(self.window.table.nodepath)
        self.rbc_nodepath.setPos(-self.rbc_subnodepath.getPos())

    def animate(self, func, delta, message=True):
        """Animate a transformation over multiple frames"""
        numframes = abs(delta / 10)
        for framenum in range(1, int(numframes) + 1):
            diff = delta / numframes
            logger.debug(f"Animating frame {framenum}/{numframes} with diff {diff:.4f}")
            self.window.task_mgr.doMethodLater(
                self.window.dt * framenum, 
                lambda task: func(diff, False), 
                "animateTask"
            )
        if message:
            self.window.messenger.send("state change")
        
    def flipTrack(self, amount=180, message=True):
        """Flip the selected tracks"""
        if self.selection:
            if self.selection.getH() > 180:
                amount = -abs(amount)
            if self.selection.getH() < -180:
                amount = abs(amount)
            self.selection.setHpr(
                self.selection.getH(),
                self.selection.getP(),
                self.selection.getR() + amount,
            )
            if message:
                self.window.messenger.send("state change")
            self.makeCombinedNode()

    def rotateTrack(self, angle=15, message=True):
        """Rotate the selected tracks"""
        if self.selection:
            self.selection.setHpr(
                self.selection.getH() + angle,
                self.selection.getP(),
                self.selection.getR(),
            )
        if message:
            self.window.messenger.send("state change")
        self.makeCombinedNode()

    def raiseTrack(self, amount=50, message=True):
        """Raise or lower the selected tracks"""
        if self.selection:
            if (
                self.selection.getZ() + amount < 1000 and 
                self.selection.getZ() + amount >= 0
            ):
                self.selection.setZ(self.selection.getZ() + amount)
                if message:
                    self.window.messenger.send("state change")
                self.makeCombinedNode()

    def findTrackByNodePath(self, nodepath):
        """Find a Track object by its nodepath"""
        for track in list(self.window.table.tracks):
            if track.nodepath == nodepath or track.nodepath.isAncestorOf(nodepath):
                return track
        return None

    def findTrackByPlane(self, plane):
        """Find a Track object by one of its connection planes"""
        for track in list(self.window.table.tracks):
            if plane in track.planes:
                return track
        return None
