from __future__ import annotations

from typing import Optional

import napari
import numpy as np
from funtracks.data_model import NodeType, SolutionTracks
from funtracks.data_model.tracks_controller import TracksController
from psygnal import Signal

from motile_tracker.data_views.graph_attributes import NodeAttr
from motile_tracker.data_views.views.layers.track_labels import new_label
from motile_tracker.data_views.views.layers.tracks_layer_group import TracksLayerGroup
from motile_tracker.data_views.views.tree_view.tree_widget_utils import (
    extract_lineage_tree,
)
from motile_tracker.data_views.views_coordinator.key_binds import (
    KEYMAP,
    bind_keymap,
)
from motile_tracker.data_views.views_coordinator.node_selection_list import (
    NodeSelectionList,
)
from motile_tracker.data_views.views_coordinator.tracks_list import TracksList


class TracksViewer:
    """Purposes of the TracksViewer:
    - Emit signals that all widgets should use to update selection or update
        the currently displayed Tracks object
    - Storing the currently displayed tracks
    - Store shared rendering information like colormaps (or symbol maps)
    """

    tracks_updated = Signal(Optional[bool])  # noqa: UP007 UP045
    update_track_id = Signal()

    @classmethod
    def get_instance(cls, viewer=None):
        if not hasattr(cls, "_instance"):
            if viewer is None:
                raise ValueError("Make a viewer first please!")
            cls._instance = TracksViewer(viewer)
        return cls._instance

    def __init__(
        self,
        viewer: napari.Viewer,
    ):
        self.viewer = viewer
        self.colormap = napari.utils.colormaps.label_colormap(
            49,
            seed=0.5,
            background_value=0,
        )

        self.symbolmap: dict[NodeType, str] = {
            NodeType.END: "x",
            NodeType.CONTINUE: "disc",
            NodeType.SPLIT: "triangle_up",
        }
        self.mode = "all"
        self.tracks: SolutionTracks | None = None
        self.visible: list | str = []
        self.tracking_layers = TracksLayerGroup(self.viewer, self.tracks, "", self)
        self.selected_nodes = NodeSelectionList()
        self.selected_nodes.list_updated.connect(self.update_selection)

        self.tracks_list = TracksList()
        self.tracks_list.view_tracks.connect(self.update_tracks)
        self.selected_track = None
        self.track_id_color = [0, 0, 0, 0]

        self.set_keybinds()

    def set_keybinds(self):
        bind_keymap(self.viewer, KEYMAP, self)

    def request_new_track(self) -> None:
        """Request a new track id (with new segmentation label if a seg layer is present)"""

        if self.tracking_layers.seg_layer is not None:
            new_label(self.tracking_layers.seg_layer)
        else:
            self.set_new_track_id()

    def set_new_track_id(self) -> None:
        """Set a new track id (if needed), update the color, and emit signal. Only updates
        the track id if the tracks.max_track_id value is used already."""

        self.selected_track = self.tracks.max_track_id  # to check if available
        if self.selected_track in self.tracks.track_id_to_node:
            self.selected_track = self.tracks.get_next_track_id()
        self.set_track_id_color(self.selected_track)
        self.update_track_id.emit()

    def set_track_id_color(self, track_id: int) -> None:
        """Update self.track_id color with the rgba color or given track_id, or a list of
        0 if the provided  track_id is None"""

        self.track_id_color = (
            [0, 0, 0, 0] if track_id is None else self.colormap.map(track_id)
        )

    def _refresh(self, node: str | None = None, refresh_view: bool = False) -> None:
        """Call refresh function on napari layers and the submit signal that tracks are
        updated. Restore the selected_nodes, if possible
        """

        if len(self.selected_nodes) > 0 and any(
            not self.tracks.graph.has_node(node) for node in self.selected_nodes
        ):
            self.selected_nodes.reset()

        self.tracking_layers._refresh()

        self.tracks_updated.emit(refresh_view)

        # if a new node was added, we would like to select this one now (call this after
        # emitting the signal, because if the node is a new node, we have to update the
        # table in the tree widget first, or it won't be present)
        if node is not None:
            self.selected_nodes.add(node)

        # restore selection and/or highlighting in all napari Views (napari Views do not
        # know about their selection ('all' vs 'lineage'), but TracksViewer does)
        self.update_selection()

    def update_tracks(self, tracks: SolutionTracks, name: str) -> None:
        """Stop viewing a previous set of tracks and replace it with a new one.
        Will create new segmentation and tracks layers and add them to the viewer.

        Args:
            tracks (funtracks.data_model.Tracks): The tracks to visualize in napari.
            name (str): The name of the tracks to display in the layer names
        """
        self.selected_nodes._list = []

        if self.tracks is not None:
            self.tracks.refresh.disconnect(self._refresh)

        self.tracks = tracks
        self.tracks_controller = TracksController(self.tracks)

        # listen to refresh signals from the tracks
        self.tracks.refresh.connect(self._refresh)

        # deactivate the input labels layer
        for layer in self.viewer.layers:
            if isinstance(layer, (napari.layers.Labels | napari.layers.Points)):
                layer.visible = False

        self.set_display_mode("all")
        self.tracking_layers.set_tracks(tracks, name)
        self.selected_nodes.reset()

        # ensure a valid track is selected from the start
        self.request_new_track()

        # emit the update signal
        self.tracks_updated.emit(True)

    def toggle_display_mode(self, event=None) -> None:
        """Toggle the display mode between available options"""

        if self.mode == "lineage":
            self.set_display_mode("all")
        else:
            self.set_display_mode("lineage")

    def set_display_mode(self, mode: str) -> None:
        """Update the display mode and call to update colormaps for points, labels, and
        tracks
        """

        # toggle between 'all' and 'lineage'
        if mode == "lineage":
            self.mode = "lineage"
            self.viewer.text_overlay.text = "Toggle Display [Q]\n Lineage"
        else:
            self.mode = "all"
            self.viewer.text_overlay.text = "Toggle Display [Q]\n All"

        self.viewer.text_overlay.visible = True
        visible_tracks = self.filter_visible_nodes()
        self.tracking_layers.update_visible(visible_tracks, self.visible)

    def filter_visible_nodes(self) -> list[int]:
        """Construct a list of track_ids that should be displayed"""

        if self.tracks is None or self.tracks.graph is None:
            return []
        if self.mode == "lineage":
            # if no nodes are selected, check which nodes were previously visible and
            # filter those
            if len(self.selected_nodes) == 0 and self.visible is not None:
                prev_visible = [
                    node for node in self.visible if self.tracks.graph.has_node(node)
                ]
                self.visible = []
                for node_id in prev_visible:
                    self.visible += extract_lineage_tree(self.tracks.graph, node_id)
                    if set(prev_visible).issubset(self.visible):
                        break
            else:
                self.visible = []
                for node in self.selected_nodes:
                    self.visible += extract_lineage_tree(self.tracks.graph, node)

            return list(
                {
                    self.tracks.graph.nodes[node][NodeAttr.TRACK_ID.value]
                    for node in self.visible
                }
            )
        self.visible = "all"
        return "all"

    def update_selection(self) -> None:
        """Sets the view and triggers visualization updates in other components"""

        self.set_napari_view()
        visible_tracks = self.filter_visible_nodes()
        self.tracking_layers.update_visible(visible_tracks, self.visible)

        if len(self.selected_nodes) > 0:
            self.selected_track = self.tracks.get_track_id(self.selected_nodes[-1])
        else:
            self.selected_track = None

        self.set_track_id_color(self.selected_track)
        self.update_track_id.emit()

    def set_napari_view(self) -> None:
        """Adjust the current_step of the viewer to jump to the last item of the
        selected_nodes list
        """
        if len(self.selected_nodes) > 0:
            node = self.selected_nodes[-1]
            self.tracking_layers.center_view(node)

    def delete_node(self, event=None):
        """Calls the tracks controller to delete currently selected nodes"""

        self.tracks_controller.delete_nodes(self.selected_nodes._list)

    def delete_edge(self, event=None):
        """Calls the tracks controller to delete an edge between the two currently
        selected nodes
        """

        if len(self.selected_nodes) == 2:
            node1 = self.selected_nodes[0]
            node2 = self.selected_nodes[1]

            time1 = self.tracks.get_time(node1)
            time2 = self.tracks.get_time(node2)

            if time1 > time2:
                node1, node2 = node2, node1

            self.tracks_controller.delete_edges(edges=np.array([[node1, node2]]))

    def create_edge(self, event=None):
        """Calls the tracks controller to add an edge between the two currently selected
        nodes
        """

        if len(self.selected_nodes) == 2:
            node1 = self.selected_nodes[0]
            node2 = self.selected_nodes[1]

            time1 = self.tracks.get_time(node1)
            time2 = self.tracks.get_time(node2)

            if time1 > time2:
                node1, node2 = node2, node1

            self.tracks_controller.add_edges(edges=np.array([[node1, node2]]))

    def undo(self, event=None):
        self.tracks_controller.undo()

    def redo(self, event=None):
        self.tracks_controller.redo()
