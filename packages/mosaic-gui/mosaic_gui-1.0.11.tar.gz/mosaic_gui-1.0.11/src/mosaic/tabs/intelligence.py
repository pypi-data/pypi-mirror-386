import re
from os import listdir
from typing import Union
from platform import system
from os.path import join, exists, basename

import numpy as np
from qtpy.QtWidgets import QWidget, QVBoxLayout, QFileDialog, QMessageBox, QApplication

from ..parallel import submit_task
from ..widgets.ribbon import create_button
from ..stylesheets import QPushButton_style


def on_run_complete(self, *args, **kwargs):
    self.cdata.data.render()
    self.cdata.models.render()


def _getExistingDirectory(parent, text):
    dialog = QFileDialog(parent)
    dialog.setWindowTitle(text)

    dialog.setFileMode(QFileDialog.Directory)

    # The native dialog on macOS omits the dialog text which can be confusing
    if system() == "Darwin":
        dialog.setOptions(
            QFileDialog.DontUseCustomDirectoryIcons | QFileDialog.DontUseNativeDialog
        )
    else:
        dialog.setOptions(QFileDialog.DontUseCustomDirectoryIcons)

    dialog.setStyleSheet(QPushButton_style)
    return dialog


class IntelligenceTab(QWidget):
    def __init__(self, cdata, ribbon, **kwargs):
        super().__init__()
        self.cdata = cdata
        self.ribbon = ribbon

        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.ribbon)

    def show_ribbon(self):
        from ..segmentation import MEMBRAIN_SETTINGS
        from ..dialogs import TemplateMatchingDialog

        self.ribbon.clear()

        hmff_actions = [
            create_button("Equilibrate", "mdi.molecule", self, self._equilibrate_fit),
            create_button("Setup", "mdi.export", self, self._setup_hmff),
            create_button(
                "Trajectory",
                "mdi.chart-line-variant",
                self,
                self._import_trajectory,
                "Import Trajectory",
                IMPORT_SETTINGS,
            ),
            create_button("Backmapping", "mdi.set-merge", self, self._map_fit),
        ]
        self.ribbon.add_section("DTS Simulation", hmff_actions)

        matching_actions = [
            create_button(
                "Setup",
                "mdi.magnify",
                self,
                lambda: TemplateMatchingDialog().exec_(),
                "Identify proteins using template matching",
            ),
        ]
        self.ribbon.add_section("Template Matching", matching_actions)

        segmentation_actions = [
            create_button("Add", "mdi.plus", self, self.add_cloud, "Add test data"),
            create_button(
                "Membrane",
                "mdi.border-all-variant",
                self,
                self._run_membrane_segmentation,
                "Segment membranes using Membrain-seg",
                MEMBRAIN_SETTINGS,
            ),
        ]
        self.ribbon.add_section("Segmentation", segmentation_actions)

    def _equilibrate_fit(self):
        from ..dialogs import MeshEquilibrationDialog
        from ..meshing import equilibrate_fit

        geometries = self.cdata.models.get_selected_geometries()
        if len(geometries) != 1:
            msg = "Can only equilibrate a single mesh at a time."
            return QMessageBox.warning(self, "Error", msg)

        geometry = geometries[0]
        if not hasattr(geometry._meta.get("fit", None), "mesh"):
            msg = f"{index} is not a triangular mesh."
            return QMessageBox.warning(self, "Error", msg)

        dialog = _getExistingDirectory(self, "Select or create directory")
        if dialog.exec_() != QFileDialog.Accepted:
            return None

        directory = dialog.selectedFiles()[0]
        if not directory:
            return -1

        dialog = MeshEquilibrationDialog(None)
        if not dialog.exec():
            return -1

        submit_task(
            "Equilibrate",
            equilibrate_fit,
            None,
            geometry,
            directory,
            dialog.get_parameters(),
        )

    def _setup_hmff(self):
        from ..meshing import setup_hmff
        from ..dialogs import HMFFDialog

        dialog = _getExistingDirectory(
            self, "Select directory with equilibrated meshes."
        )
        if dialog.exec_() != QFileDialog.Accepted:
            return None

        directory = dialog.selectedFiles()[0]
        if not directory:
            return -1

        mesh_config = join(directory, "mesh.txt")
        if not exists(mesh_config):
            msg = f"Missing mesh_config at {mesh_config}. Most likely {directory} "
            "is not a valid directory created by Equilibrate Mesh."
            return QMessageBox.warning(self, "Error", msg)

        with open(mesh_config, mode="r", encoding="utf-8") as infile:
            data = [x.strip() for x in infile.read().split("\n")]
            data = [x.split("\t") for x in data if len(x)]

        headers = data.pop(0)
        ret = {header: list(column) for header, column in zip(headers, zip(*data))}

        if not all(t in ret.keys() for t in ("file", "scale_factor", "offset")):
            print(
                "mesh_config is malformated. Expected file, scale_factor, "
                f"offset columns, got {', '.join(list(ret.keys()))}."
            )
            return -1

        dialog = HMFFDialog(None, mesh_options=ret["file"])
        if not dialog.exec():
            return -1

        submit_task(
            "HMFF Setup",
            setup_hmff,
            None,
            ret,
            directory=directory,
            **dialog.get_parameters(),
        )

    def _import_trajectory(
        self,
        scale: float = 1.0,
        offset: Union[str, float] = 0.0,
        drop_pbc: bool = False,
        **kwargs,
    ):
        from ..meshing import to_open3d
        from ..formats import open_file
        from ..dialogs import ProgressDialog
        from ..geometry import GeometryTrajectory
        from ..parametrization import TriangularMesh

        dialog = _getExistingDirectory(self, "Select directory with DTS trajectory")
        if dialog.exec_() != QFileDialog.Accepted:
            return None

        directory = dialog.selectedFiles()[0]
        if not directory:
            return -1

        ret = []
        files = [join(directory, x) for x in listdir(directory)]
        files = [
            x
            for x in files
            if x.endswith(".tsi") or x.endswith(".vtu") and x != "conf-1.vtu"
        ]
        files = sorted(files, key=lambda x: int(re.findall(r"\d+", basename(x))[0]))

        if isinstance(offset, str):
            try:
                offset = np.array([float(x) for x in offset.split(",")])
            except Exception as e:
                raise ValueError(
                    "Offset should be a single or three comma-separated floats."
                ) from e

        with ProgressDialog(files, title="Importing Trajectory", parent=None) as pbar:
            for index, filename in enumerate(pbar):
                container = open_file(filename)[0]
                faces = container.faces.astype(int)
                points = np.divide(np.subtract(container.vertices, offset), scale)

                if drop_pbc:
                    from ..meshing.utils import _edge_lengths

                    points_norm = points - points.min(axis=0)

                    box_stop = points_norm.max(axis=0)
                    points_pbc = np.mod(points_norm, 0.85 * box_stop)

                    dist_regular = _edge_lengths(points_norm, faces)
                    dist_pbc = _edge_lengths(points_pbc, faces)

                    keep = np.all(dist_pbc >= dist_regular, axis=-1)
                    faces = faces[keep]

                # Avoid detecting PBC as ill-defined meshes
                fit = TriangularMesh(to_open3d(points, faces), repair=False)

                ret.append(
                    {
                        "fit": fit,
                        "filename": filename,
                        "name": basename(directory),
                        "vertex_properties": container.vertex_properties,
                    }
                )

        if len(ret) == 0:
            raise ValueError(f"No meshes found at: {directory}.")

        base = ret[0]["fit"]
        trajectory = GeometryTrajectory(
            points=base.vertices.copy(),
            normals=base.compute_vertex_normals().copy(),
            sampling_rate=1 / scale,
            meta=ret[0].copy(),
            trajectory=ret,
            vertex_properties=ret[0]["vertex_properties"],
        )
        trajectory.change_representation("mesh")
        self.cdata._models.add(trajectory)
        self.cdata.models.data_changed.emit()
        return self.cdata.models.render()

    def _map_fit(self):
        from ..meshing import mesh_to_cg
        from ..dialogs import MeshMappingDialog

        dialog = _getExistingDirectory(self, "Select output directory")
        if dialog.exec_() != QFileDialog.Accepted:
            return None

        directory = dialog.selectedFiles()[0]
        if not directory:
            return -1

        fits = self.cdata.format_datalist("models", mesh_only=True)
        clusters = self.cdata.format_datalist("data")
        dialog = MeshMappingDialog(fits=fits, clusters=clusters)
        if not dialog.exec():
            return -1

        fit, edge_length, mappings, cast_ray, flip = dialog.get_parameters()

        submit_task(
            "Coarse graining",
            mesh_to_cg,
            None,
            edge_length=edge_length,
            output_directory=directory,
            inclusions=mappings,
            include_normals=cast_ray,
            flip_normals=flip,
        )

    def _run_membrain(self, *args, **kwargs):
        from ..gui import App
        from ..formats import open_file
        from ..segmentation import run_membrainseg

        def _callback(output_name: str):
            if output_name is None:
                return QMessageBox.warning(
                    None, "Error", "No segmentation was created."
                )

            # Preferred because it also updates viewport
            app = QApplication.instance().activeWindow()
            if isinstance(app, App):
                return app._open_files([output_name])

            container = open_file(output_name)
            for data in container:
                self.cdata.data.add(
                    points=data.vertices,
                    normals=data.normals,
                    sampling_rate=data.sampling,
                )
            self.cdata.data.data_changed.emit()
            self.cdata.data.render()

        submit_task(
            "Membrane Segmentation", run_membrainseg, _callback, *args, **kwargs
        )

    def _run_membrane_segmentation(self, **kwargs):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Select volume", "", "MRC Files (*.mrc);;All Files (*.*)"
        )
        if not file_name:
            return None

        if not exists(kwargs.get("model_path", "")):
            return QMessageBox.warning(None, "Error", "Missing path to membrain model.")

        return self._run_membrain(tomogram_path=file_name, **kwargs)

    def add_cloud(self, *args):
        num_points = 1000
        points = np.random.rand(num_points, 3) * 100
        self.cdata.data.add(points=points, sampling_rate=1)

        self.cdata.data.render()
        # self.cdata.models.render()


IMPORT_SETTINGS = {
    "title": "Trajectory Import",
    "settings": [
        {
            "label": "Scale",
            "parameter": "scale",
            "type": "text",
            "default": 1.0,
            "description": "Scale imported points by 1 / scale.",
        },
        {
            "label": "Offset",
            "parameter": "offset",
            "type": "text",
            "default": "0.0",
            "description": "Add offset as (points - offset) / scale ",
        },
        {
            "label": "Remove PBC",
            "parameter": "drop_pbc",
            "type": "boolean",
            "default": False,
            "description": "Drop triangles arising from periodic boundaries.",
        },
    ],
}
