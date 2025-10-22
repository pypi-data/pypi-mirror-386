"""
Implemenents DataContainerInteractor and LinkedDataContainerInteractor,
which mediate interaction between the GUI and underlying DataContainers.
This includes selection, editing and rendering.

Copyright (c) 2024 European Molecular Biology Laboratory

Author: Valentin Maurer <valentin.maurer@embl-hamburg.de>
"""

import numpy as np
from os.path import splitext
from typing import Tuple, List, Dict

import vtk
from qtpy.QtGui import QAction
from qtpy.QtWidgets import (
    QListWidget,
    QMenu,
    QFileDialog,
    QMessageBox,
    QDialog,
)
from qtpy.QtCore import (
    Qt,
    QObject,
    Signal,
    QEvent,
)
from .parallel import submit_task

from .widgets.container_list import StyledTreeWidgetItem

__all__ = ["DataContainerInteractor"]


class DataContainerInteractor(QObject):
    """Handle interaction between GUI and DataContainer"""

    data_changed = Signal()
    render_update = Signal()
    vtk_pre_render = Signal()

    def __init__(self, container, vtk_widget, prefix="Cluster"):
        from .widgets import ContainerListWidget

        super().__init__()
        self.prefix = prefix
        self.point_selection, self.rendered_actors = {}, set()
        self.vtk_widget, self.container = vtk_widget, container

        # Interaction element for the GUI
        self.data_list = ContainerListWidget()
        self.data_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.data_list.itemChanged.connect(self._on_item_renamed)
        self.data_list.itemSelectionChanged.connect(self._on_cluster_selection_changed)

        self.data_list.tree_widget.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.data_list.tree_widget.customContextMenuRequested.connect(
            self._show_context_menu
        )

        # Functionality to add points
        self._interaction_mode, self._active_cluster = False, None
        self.point_picker = vtk.vtkWorldPointPicker()
        self.vtk_widget.installEventFilter(self)

        self.set_coloring_mode("default")

    def _get_selected_uuids(self):
        """Get UUIDs of selected items."""
        uuids = []
        for item in self.data_list.selected_items():
            if uuid := item.metadata.get("uuid"):
                uuids.append(uuid)
        return uuids

    def get_selected_geometries(self):
        ret = [self.container.get(uuid) for uuid in self._get_selected_uuids()]
        return [x for x in ret if x is not None]

    def attach_area_picker(self):
        self.interactor = self.vtk_widget.GetRenderWindow().GetInteractor()
        if self.interactor is None:
            print("Initialize an Interactor first.")
            return None
        self.area_picker = vtk.vtkAreaPicker()
        style = vtk.vtkInteractorStyleRubberBandPick()

        self.interactor.SetPicker(self.area_picker)
        self.interactor.SetInteractorStyle(style)
        self.area_picker.AddObserver("EndPickEvent", self._on_area_pick)

    def get_event_position(self, event, return_event_position: bool = True):
        pos = event.pos()
        return self._get_event_position(
            (pos.x(), pos.y(), 0), return_event_position=return_event_position
        )

    def _get_event_position(self, position, return_event_position: bool = True):
        # Avoid DPI/scaling issue on MacOS Retina displays
        dpr = self.vtk_widget.devicePixelRatio()

        y = (self.vtk_widget.height() - position[1]) * dpr
        event_position = (position[0] * dpr, y, 0)
        r = self.vtk_widget.GetRenderWindow().GetRenderers().GetFirstRenderer()
        self.point_picker.Pick(*event_position, r)
        world_position = self.point_picker.GetPickPosition()

        # Projection onto current camera plane
        camera = r.GetActiveCamera()
        camera_plane = vtk.vtkPlane()
        camera_plane.SetNormal(camera.GetDirectionOfProjection())
        camera_plane.SetOrigin(world_position)

        t = vtk.mutable(0.0)
        x = [0, 0, 0]
        camera_plane.IntersectWithLine(camera.GetPosition(), world_position, t, x)
        if return_event_position:
            return x, event_position
        return x

    def eventFilter(self, watched_obj, event):
        # VTK camera also observes left-click, so duplicate calls need to be handled
        if self._interaction_mode in ("draw", "pick") and event.type() in [
            QEvent.Type.MouseButtonPress,
            QEvent.Type.MouseMove,
        ]:
            if event.buttons() & Qt.MouseButton.LeftButton:
                world_position, event_position = self.get_event_position(event, True)
                if self._interaction_mode == "draw":
                    self._add_point(world_position)
                elif self._interaction_mode == "pick":
                    self._pick_prop(event_position)
                return True

        # Let vtk events pass through
        return super().eventFilter(watched_obj, event)

    def _on_item_renamed(self, item):
        if (uuid := item.metadata.get("uuid")) is None:
            return None

        if (geometry := self.container.get(uuid)) is not None:
            # Consider adding bidrecitional uuid lookup to render instead
            if item.text() != geometry._meta.get("name"):
                geometry._meta["name"] = item.text()
                self.data_changed.emit()
                self.render()

    def next_color(self):
        if not hasattr(self, "colors"):
            return self.container.base_color

        color = self.colors.pop(0)
        self.colors.append(color)
        return color

    def set_coloring_mode(self, mode: str):
        from .utils import get_cmap

        if mode not in ("default", "entity"):
            raise ValueError("Only mode 'default' and 'entity' are supported.")

        self.colors = [self.container.base_color]
        if mode == "entity":
            cmap = get_cmap("Set2")
            self.colors = [cmap(i)[:3] for i in range(cmap.N)]

        for i in range(len(self.container)):
            if (geometry := self.container.get(i)) is None:
                continue
            self.container.update_appearance(
                [i], geometry._appearance | {"base_color": self.next_color()}
            )
        self.container.highlight([])
        return self.render_vtk()

    def add(self, *args, **kwargs):
        if kwargs.get("color", None) is None:
            kwargs["color"] = self.next_color()
        ret = self.container.add(*args, **kwargs)
        self.data_changed.emit()
        return ret

    def add_selection(self, selected_point_ids: Dict[vtk.vtkActor, np.ndarray]) -> int:
        """Add new cloud from selected points.

        Parameters
        ----------
        selected_point_ids : dict
            Mapping of vtkActor to selected point IDs.

        Returns
        -------
        int
            Index of new cloud, -1 if creation failed.
        """
        from .geometry import Geometry

        new_cluster, remove_cluster = [], []
        for uuid, point_ids in selected_point_ids.items():
            if (geometry := self.container.get(uuid)) is None:
                continue

            n_points = geometry.get_number_of_points()
            if not geometry.visible or n_points == 0 or point_ids.size == 0:
                continue

            new_cluster.append(geometry[point_ids])
            inverse = np.setdiff1d(np.arange(n_points), point_ids, assume_unique=True)
            if inverse.size != 0:
                self.container.update(uuid, geometry[inverse])
            else:
                # All points were selected, mark for removal
                remove_cluster.append(geometry)

        self.container.remove(remove_cluster)
        if len(new_cluster):
            return self.add(Geometry.merge(new_cluster))
        return -1

    def _add_point(self, point):
        if (geometry := self.container.get(self._active_cluster)) is None:
            return -1

        # We call swap data to automatically handle other Geometry attributes
        geometry.swap_data(np.concatenate((geometry.points, np.asarray(point)[None])))
        self.data_changed.emit()
        return self.render()

    def activate_viewing_mode(self):
        self._interaction_mode = None
        self._active_cluster = None

    def activate_drawing_mode(self):
        self._active_cluster = None
        self._interaction_mode = "draw"

        new_cluster_index = self.add(points=np.empty((0, 3), dtype=np.float32))
        self._active_cluster = self.container.get(new_cluster_index).uuid

    def activate_picking_mode(self):
        self._interaction_mode = "pick"

    def set_selection_by_uuid(self, uuids):
        """
        Set selection by UUIDs.

        Parameters
        ----------
        uuids : list of str
            UUIDs to select
        """
        items = []
        for item, parent, _ in self.data_list.traverse(reverse=False):
            if item.metadata.get("uuid") in uuids:
                items.append(item)

        self.data_list._set_selection(items)
        self._highlight_selection()

    def _on_cluster_selection_changed(self):
        # This is of course not ideal but prevents unhighlight/highlight
        # when clicking on groups due to itemClicked behaviour. So we
        # handle actual deselect all using _highlight_selection
        if not len(self._get_selected_uuids()):
            return None
        self._highlight_selection()

    def deselect(self):
        """Deselect on right-click"""
        self.data_list.clearSelection()
        self._highlight_selection()
        self.deselect_points()

    def _highlight_selection(self):
        self.container.highlight(self._get_selected_uuids())
        self.render_vtk()

    def _on_area_pick(self, obj, event):
        frustum = obj.GetFrustum()
        extractor = vtk.vtkExtractSelectedFrustum()
        extractor.SetFrustum(frustum)

        interactor = self.vtk_widget.GetRenderWindow().GetInteractor()
        if not interactor.GetShiftKey():
            self.deselect_points()

        for geometry in self.container.data:
            extractor.SetInputData(geometry._data)
            extractor.Update()

            output = extractor.GetOutput()
            if output.GetNumberOfPoints() == 0:
                continue

            uuid = geometry.uuid
            selected_ids = output.GetPointData().GetArray("vtkOriginalPointIds")
            if selected_ids and selected_ids.GetNumberOfTuples() > 0:
                ids = vtk.util.numpy_support.vtk_to_numpy(selected_ids)

                if uuid not in self.point_selection:
                    self.point_selection[uuid] = np.array([], dtype=np.int32)

                union = np.union1d(ids, self.point_selection[uuid])
                self.point_selection[uuid] = union.astype(np.int32, copy=False)

        self.highlight_selected_points(color=None)

    def _pick_prop(self, event_pos):
        picker = vtk.vtkPropPicker()
        r = self.vtk_widget.GetRenderWindow().GetRenderers().GetFirstRenderer()
        picker.Pick(*event_pos, r)

        picked_actor = picker.GetActor()
        actors = self.container.get_actors()
        if picked_actor in actors:
            index = actors.index(picked_actor)
            uuid = self.container.get(index).uuid
            self.set_selection_by_uuid([uuid, *self._get_selected_uuids()])
        return None

    def _show_context_menu(self, position):
        item = self.data_list.itemAt(position)
        if not item:
            return -1

        # Make sure right click also selects group members
        self.data_list._select_group_children(item)
        context_menu = QMenu(self.data_list)

        show_action = QAction("Show", self.data_list)
        show_action.triggered.connect(lambda: self.visibility(visible=True))
        context_menu.addAction(show_action)
        hide_action = QAction("Hide", self.data_list)
        hide_action.triggered.connect(lambda: self.visibility(visible=False))
        context_menu.addAction(hide_action)

        duplicate_action = QAction("Duplicate", self.data_list)
        duplicate_action.triggered.connect(self.duplicate)
        context_menu.addAction(duplicate_action)
        remove_action = QAction("Remove", self.data_list)
        remove_action.triggered.connect(self.remove)
        context_menu.addAction(remove_action)

        formats = [
            "Points",
            "Gaussian Density",
            "Normals",
            "Basis",
        ]
        formats_extended = [
            None,
            "Mesh",
            "Surface",
            "Wireframe",
        ]
        for geometry in self.get_selected_geometries():
            try:
                geometry._meta["fit"].vertices
                formats.extend(formats_extended)
                break
            except Exception:
                pass

        representation_menu = QMenu("Representation", context_menu)
        for format_name in formats:
            if format_name is None:
                representation_menu.addSeparator()
                continue
            action = QAction(format_name, representation_menu)
            action.triggered.connect(
                lambda checked, f=format_name: self.change_representation(f)
            )
            representation_menu.addAction(action)
        context_menu.addMenu(representation_menu)

        context_menu.addSeparator()

        group_action = QAction("Group", self.data_list)
        group_action.triggered.connect(
            lambda: self.data_list.group_selected("New Group")
        )
        context_menu.addAction(group_action)

        ungroup_action = QAction("Ungroup", self.data_list)
        ungroup_action.triggered.connect(
            lambda: (self.data_list.ungroup_selected(), self.render())
        )
        context_menu.addAction(ungroup_action)

        context_menu.addSeparator()
        export_menu = QAction("Export As", self.data_list)
        export_menu.triggered.connect(lambda: self._handle_export())
        context_menu.addAction(export_menu)

        properties_action = QAction("Properties", self.data_list)
        properties_action.triggered.connect(self._show_properties_dialog)
        context_menu.addAction(properties_action)

        context_menu.exec(self.data_list.mapToGlobal(position))

    def _handle_export(self, *args, **kwargs):
        from .dialogs import ExportDialog

        enabled_categories = ["pointcloud", "volume"]
        for geometry in self.get_selected_geometries():
            fit = geometry._meta.get("fit", None)
            if hasattr(fit, "mesh"):
                enabled_categories.append("mesh")

        # Shape and sampling are given if MosaicData.open_file loaded a volume.
        # For convenience, outputs will be handled w.r.t to the initial volume
        sampling, shape = 1, self.container.metadata.get("shape")
        dialog = ExportDialog(
            parent=None,
            parameters={"shape": shape},
            enabled_categories=enabled_categories,
        )

        if shape is not None:
            sampling = self.container.metadata.get("sampling_rate", 1)
            shape = np.rint(np.divide(shape, sampling)).astype(int)
        else:
            shape = (64, 64, 64)

        dialog.set_shape(shape)
        dialog.export_requested.connect(self._wrap_export)

        return dialog.exec()

    def _wrap_export(self, export_data):
        file_format = export_data.get("format")

        file_dialog = QFileDialog(None)
        file_path, _ = file_dialog.getSaveFileName(
            None, "Save File", "", f"{file_format.upper()} Files (*.{file_format})"
        )
        if not file_path:
            return -1

        try:
            _export_data(
                geometries=self.get_selected_geometries(),
                metadata=self.container.metadata,
                file_path=file_path,
                export_data=export_data,
            )
        except Exception as e:
            QMessageBox.warning(None, "Error", str(e))
        return None

    def _show_properties_dialog(self) -> int:
        from .dialogs import GeometryPropertiesDialog

        uuids = self._get_selected_uuids()
        if not len(uuids):
            return -1

        base_container = self.container.get(uuids[0])
        base_parameters = base_container._appearance.copy()
        base_parameters["sampling_rate"] = base_container.sampling_rate

        dialog = GeometryPropertiesDialog(initial_properties=base_parameters)

        def on_parameters_changed(parameters):
            sampling_rate = parameters.pop("sampling_rate")
            full_render = self.container.update_appearance(uuids, parameters)
            for uuid in uuids:
                if (geometry := self.container.get(uuid)) is None:
                    continue
                geometry.sampling_rate = sampling_rate

            if full_render:
                self.render()

            # Make sure selection is maintained and invoke render_vtk afterwards
            self.set_selection_by_uuid(uuids)

        dialog.parametersChanged.connect(on_parameters_changed)

        if dialog.exec() == QDialog.DialogCode.Rejected:
            on_parameters_changed(base_parameters)
        return 1

    def _uuid_to_items(self):
        uuid_to_items = {}
        for i in range(len(self.container)):
            if (geometry := self.container.get(i)) is None:
                continue

            name = geometry._meta.get("name", None)
            if name is None:
                name = f"{self.prefix} {i}"

            item_type = "cluster"
            if (fit := geometry._meta.get("fit", None)) is not None:
                item_type = "mesh" if hasattr(fit, "mesh") else "parametric"
                if item_type == "mesh" and hasattr(geometry, "_trajectory"):
                    item_type = "trajectory"

            info = {"item_type": item_type, "name": name, "uuid": geometry.uuid}

            geometry._meta["name"] = name
            geometry._meta["info"] = info

            item = StyledTreeWidgetItem(
                name, geometry.visible, info, editable=True, parent=None
            )
            uuid_to_items[geometry.uuid] = item
        return uuid_to_items

    def render(self):
        """Synchronize vtk actors and tree data structure with subsequent render."""
        renderer = self.vtk_widget.GetRenderWindow().GetRenderers().GetFirstRenderer()

        current_actors = set(self.container.get_actors())
        actors_to_remove = self.rendered_actors - current_actors
        for actor in actors_to_remove:
            renderer.RemoveActor(actor)
            self.rendered_actors.remove(actor)

        actors_to_add = current_actors - self.rendered_actors
        for actor in actors_to_add:
            renderer.AddActor(actor)
            self.rendered_actors.add(actor)

        uuid_to_items = self._uuid_to_items()
        self.data_list.update(uuid_to_items)

        self.render_vtk()
        self.render_update.emit()

    def render_vtk(self):
        """Update the vtk scene."""
        self.vtk_pre_render.emit()
        return self.vtk_widget.GetRenderWindow().Render()

    def deselect_points(self):
        for uuid, point_ids in self.point_selection.items():
            if (geometry := self.container.get(uuid)) is None:
                continue

            color = geometry._appearance.get("base_color", (0.7, 0.7, 0.7))
            self.container.highlight_points(uuid, point_ids, color)

        self.point_selection.clear()

    def highlight_selected_points(self, color):
        for uuid, point_ids in self.point_selection.items():
            self.container.highlight_points(uuid, point_ids, color)
        return self.render_vtk()

    def highlight_clusters_from_selected_points(self):
        return self.set_selection_by_uuid(list(self.point_selection.keys()))

    def change_representation(self, representation: str):
        geometries = self.get_selected_geometries()
        if not len(geometries):
            return -1

        representation = representation.lower().replace(" ", "_")

        if representation == "points":
            representation = "pointcloud"

        for geometry in geometries:
            # BUG: Moving from pointcloud_normals to a different representation and
            # back breaks glyph rendering. This could be due to incorrect cleanup in
            # Geometry.change_representation or an issue of vtk 9.3.1. Creating a copy
            # of the Geometry instance circumvents the issue.
            if representation in ("normals", "basis", "gaussian_density"):
                self.container.update(geometry.uuid, geometry[...])
                geometry = self.container.get(geometry.uuid)

            geometry.change_representation(representation)
        self.render()

    def _backup(self):
        # Save clusters and points that are modified by the operation
        self._merge_uuid = None
        try:
            self._geometry_backup = {
                x.uuid: x[...] for x in self.get_selected_geometries()
            }
            self._point_backup = {
                i: self.container.get(i)[ix] for i, ix in self.point_selection.items()
            }
        except Exception:
            self._geometry_backup = None
            self._point_backup = None

    def undo(self):
        if getattr(self, "_geometry_backup", None) is None:
            return None

        if getattr(self, "_merge_uuid", None) is not None:
            self.container.remove(self._merge_uuid)

        for _, geometry in self._geometry_backup.items():
            self.add(geometry)

        for uuid, geometry in self._point_backup.items():
            prev_geometry = self.container.get(uuid)
            if prev_geometry is None:
                self.add(geometry)
                continue
            self.container.update(uuid, geometry.merge((prev_geometry, geometry)))

        self._geometry_backup = None
        self._point_backup = None
        self._merge_uuid = None
        self.data_changed.emit()
        self.render()

    def merge(self):
        from .geometry import Geometry

        self._backup()
        point_cluster = self.add_selection(self.point_selection)
        self.deselect_points()

        merge = [*self.get_selected_geometries(), self.container.get(point_cluster)]
        merged_geometry = Geometry.merge(merge)

        self.container.remove(merge)
        new_index = self.add(merged_geometry)
        self._merge_uuid = self.container.get(new_index).uuid

        self.render()

    def remove(self):
        self._backup()

        added_cluster = self.add_selection(self.point_selection)
        self.point_selection.clear()

        self.container.remove(
            [self.container.get(added_cluster), *self.get_selected_geometries()]
        )
        self.data_changed.emit()
        self.render()

    def refresh_actors(self):
        for index in range(len(self.container)):
            geometry = self.container.get(index)
            self.container.update(geometry, geometry[...])
        return self.render()

    def update(self, container, tree_state=None):
        """Update container with new data and optionally restore tree structure.

        Parameters
        ----------
        container : :py:class:`mosaic.container.DataContainer`
            Container with new data
        tree_state : TreeState, optional
            Tree structure to restore. If None, items added to root.
        """
        if not isinstance(container, type(self.container)):
            raise ValueError(
                f"Can not update {type(self.container)} using {type(container)}."
            )

        self.container.clear()
        self.container.metadata.update(container.metadata)
        _ = [self.add(x) for x in container.data]

        if tree_state is not None:
            self.data_list.apply_state(tree_state, self._uuid_to_items())

        self.data_changed.emit()


_GEOMETRY_OPERATIONS = {
    "decimate": {"remove_original": False, "background": True},
    "downsample": {"remove_original": False, "background": True},
    "remove_outliers": {"remove_original": False, "background": True},
    "compute_normals": {"remove_original": True, "background": True},
    "cluster": {"remove_original": True, "background": True},
    "duplicate": {"remove_original": False},
    "visibility": {
        "remove_original": False,
        "render": "full",
        "background": False,
        "batch": True,
    },
}

for op_name, config in _GEOMETRY_OPERATIONS.items():
    method_name = config.get("method_name", op_name)
    remove_orig = config.get("remove_original", False)
    render = config.get("render", "full")
    background = config.get("background", False)
    batch = config.get("batch", False)

    def create_method(op_name, remove_orig, render_flag, bg_task, batch_flag):
        def method(self, **kwargs):
            f"""Apply {op_name} operation to selected geometries in background."""
            from .operations import GeometryOperations

            def _render_callback(*args, **kwargs):
                if render_flag == "full":
                    self.render()
                elif render_flag == "vtk":
                    self.render_vtk()

            if (geometries := kwargs.get("geometries", None)) is None:
                geometries = self.get_selected_geometries()

            for geometry in geometries:
                if geometry is None:
                    continue

                def _callback(ret, geom=geometry):
                    if ret is None:
                        pass
                    elif isinstance(ret, (List, Tuple)):
                        _ = [self.add(x) for x in ret]
                    else:
                        self.add(ret)

                    if remove_orig:
                        self.container.remove(geom)

                    if not batch_flag:
                        _render_callback()

                func = getattr(GeometryOperations, op_name)

                if bg_task:
                    submit_task(op_name.title(), func, _callback, geometry, **kwargs)
                    continue
                _callback(func(geometry, **kwargs))

            if batch_flag:
                _render_callback()

        method.__name__ = method_name
        method.__doc__ = f"Apply {op_name} operation using GeometryOperations."
        return method

    setattr(
        DataContainerInteractor,
        method_name,
        create_method(op_name, remove_orig, render, background, batch),
    )


def _export_data(geometries, metadata, file_path: str, export_data: Dict):
    from .utils import points_to_volume
    from .formats import OrientationsWriter, write_density

    mesh_formats = ("obj", "stl", "ply")
    volume_formats = ("mrc", "em", "h5")
    point_formats = ("tsv", "star", "xyz")

    file_format = export_data.get("format")
    if not len(geometries):
        raise ValueError("Select at least one object.")

    file_path, _ = splitext(file_path)

    shape = metadata.get("shape", None)
    if shape is not None:
        _sampling = metadata.get("sampling_rate", 1)
        shape = np.rint(np.divide(shape, _sampling)).astype(int)

    center = 0
    if {"shape_x", "shape_y", "shape_z"}.issubset(export_data):
        shape = tuple(export_data[x] for x in ["shape_x", "shape_y", "shape_z"])

    orientation_kwargs = {}
    data = {"points": [], "quaternions": []}
    for index, geometry in enumerate(geometries):
        if file_format in mesh_formats:
            fit = geometry._meta.get("fit", None)
            if not hasattr(fit, "mesh"):
                raise ValueError(f"Selected geometry {index} is not a mesh.")
            fit.to_file(f"{file_path}_{index}.{file_format}")
            continue

        points, quaternions = geometry.points, None
        if file_format in point_formats:
            points, quaternions = geometry.points, geometry.quaternions

        if quaternions is None:
            quaternions = np.full((points.shape[0], 4), fill_value=(1, 0, 0, 0))

        sampling = export_data.get("sampling", -1)
        if sampling < 0:
            sampling = geometry.sampling_rate

        if export_data.get("relion_5_format", False):
            center = np.divide(shape, 2).astype(int) if shape is not None else 0
            center = np.multiply(center, sampling)
            orientation_kwargs["version"] = "# version 50001"
            sampling = 1

        points = np.subtract(np.divide(points, sampling), center)
        data["points"].append(points)
        data["quaternions"].append(quaternions)

    if file_format in mesh_formats:
        return None

    if len(data["points"]) == 0:
        raise ValueError("No elements suitable for export")

    if file_format in volume_formats:
        if shape is None:
            temp = np.rint(np.concatenate(data["points"]))
            shape = temp.astype(int).max(axis=0) + 1

        volume = None
        for index, points in enumerate(data["points"]):
            volume = points_to_volume(
                points, sampling_rate=1, shape=shape, weight=index + 1, out=volume
            )

        # Try saving some memory on write. uint8 would be padded to 16 hence int8
        dtype = np.float32
        if index < np.iinfo(np.int8).max:
            dtype = np.int8
        elif index < np.iinfo(np.uint16).max:
            dtype = np.uint16

        return write_density(
            volume.astype(dtype),
            filename=f"{file_path}.{file_format}",
            sampling_rate=sampling,
        )

    if file_format not in point_formats:
        return None

    data["entities"] = [
        np.full(x.shape[0], fill_value=i) for i, x in enumerate(data["points"])
    ]
    if single_file := export_data.get("single_file", True):
        data = {k: [np.concatenate(v)] for k, v in data.items()}

    if file_format == "xyz":
        for index, points in enumerate(data["points"]):
            fname = f"{file_path}_{index}.{file_format}"
            if single_file:
                fname = f"{file_path}.{file_format}"

            header = ""
            if export_data.get("header", True):
                header = ",".join(["x", "y", "z"])

            np.savetxt(fname, points, delimiter=",", header=header, comments="")
        return 1

    for index in range(len(data["points"])):
        orientations = OrientationsWriter(**{k: v[index] for k, v in data.items()})
        fname = f"{file_path}_{index}.{file_format}"
        if single_file:
            fname = f"{file_path}.{file_format}"
        orientations.to_file(fname, file_format=file_format, **orientation_kwargs)
