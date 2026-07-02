# -*- coding: utf-8 -*-
"""GeolAttitude dock widget.

The UI is built programmatically to avoid Qt Designer/PyQt version friction in
QGIS 4 development builds while preserving a Plugin Builder style layout.
"""

import csv
import math
import os
from datetime import datetime

import numpy as np

from qgis.PyQt.QtCore import pyqtSignal, QVariant
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDockWidget,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from qgis.core import (
    QgsCoordinateTransform,
    QgsFeature,
    QgsField,
    QgsGeometry,
    QgsMapLayerType,
    QgsProject,
    QgsRaster,
    QgsVectorLayer,
    QgsWkbTypes,
    QgsPointXY,
    QgsMarkerSymbol,
)
from qgis.gui import QgsRubberBand, QgsVertexMarker


class GeolAttitudeDockWidget(QDockWidget):
    """Dock widget for interactive DTM sampling and plane fitting."""

    closingPlugin = pyqtSignal()
    startPickingRequested = pyqtSignal()
    stopPickingRequested = pyqtSignal()

    def __init__(self, iface, plugin, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.plugin = plugin
        self.canvas = iface.mapCanvas()
        self.points = []
        self.markers = []
        self.rubber_band = None
        self.last_result = None
        self.setWindowTitle("GeolAttitude")
        self.setObjectName("GeolAttitudeDockWidget")
        self._build_ui()
        self.refresh_rasters()

    def closeEvent(self, event):  # pylint: disable=invalid-name
        self.closingPlugin.emit()
        event.accept()

    def _build_ui(self):
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)

        layout.addWidget(QLabel("DTM / elevation raster layer:"))
        self.raster_combo = QComboBox()
        layout.addWidget(self.raster_combo)

        row = QHBoxLayout()
        self.start_button = QPushButton("Start picking")
        self.start_button.clicked.connect(self.startPickingRequested.emit)
        row.addWidget(self.start_button)
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stopPickingRequested.emit)
        row.addWidget(self.stop_button)
        layout.addLayout(row)

        row2 = QHBoxLayout()
        self.undo_button = QPushButton("Undo point")
        self.undo_button.clicked.connect(self.undo_point)
        row2.addWidget(self.undo_button)
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_points)
        row2.addWidget(self.clear_button)
        layout.addLayout(row2)

        row3 = QHBoxLayout()
        self.compute_button = QPushButton("Compute")
        self.compute_button.clicked.connect(self.compute_and_display)
        row3.addWidget(self.compute_button)
        self.export_csv_button = QPushButton("Export CSV")
        self.export_csv_button.clicked.connect(self.export_csv)
        row3.addWidget(self.export_csv_button)
        layout.addLayout(row3)

        self.create_layer_check = QCheckBox("Create result point layer on compute")
        self.create_layer_check.setChecked(True)
        layout.addWidget(self.create_layer_check)

        self.live_check = QCheckBox("Live compute after 3 points")
        self.live_check.setChecked(True)
        layout.addWidget(self.live_check)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setMinimumHeight(280)
        layout.addWidget(self.output)

        self.refresh_button = QPushButton("Refresh raster list")
        self.refresh_button.clicked.connect(self.refresh_rasters)
        layout.addWidget(self.refresh_button)

        self.setWidget(wrapper)

    def refresh_rasters(self):
        """Refresh raster combo from current project layers."""
        current = self.raster_combo.currentData()
        self.raster_combo.clear()
        for layer in QgsProject.instance().mapLayers().values():
            if layer.type() == QgsMapLayerType.RasterLayer and layer.isValid():
                self.raster_combo.addItem(layer.name(), layer.id())
        if current:
            idx = self.raster_combo.findData(current)
            if idx >= 0:
                self.raster_combo.setCurrentIndex(idx)

    def selected_raster(self):
        """Return the selected raster layer, or None."""
        layer_id = self.raster_combo.currentData()
        if not layer_id:
            return None
        return QgsProject.instance().mapLayer(layer_id)

    def add_point(self, map_point):
        """Add a clicked map point after sampling elevation from the selected DTM."""
        raster = self.selected_raster()
        if raster is None:
            QMessageBox.warning(self, "No DTM selected", "Select a DTM/elevation raster first.")
            return

        project_crs = self.canvas.mapSettings().destinationCrs()
        raster_crs = raster.crs()
        try:
            transform = QgsCoordinateTransform(project_crs, raster_crs, QgsProject.instance())
            raster_pt = transform.transform(map_point)
        except Exception as exc:  # pylint: disable=broad-except
            QMessageBox.critical(self, "CRS transform failed", str(exc))
            return

        z, message = self.sample_raster_z(raster, raster_pt)
        if z is None:
            QMessageBox.warning(self, "No raster value", message)
            return

        self.points.append({"x": map_point.x(), "y": map_point.y(), "z": z, "raster": raster.name()})
        self._add_marker(map_point)
        self._update_rubber_band()
        if self.live_check.isChecked() and len(self.points) >= 3:
            self.compute_and_display(create_layer=False)
        else:
            self._update_output_basic()

    @staticmethod
    def _is_numeric_z(value):
        if value is None:
            return False
        try:
            z = float(value)
        except Exception:  # pylint: disable=broad-except
            return False
        return math.isfinite(z)

    def sample_raster_z(self, raster, raster_pt):
        """Sample elevation from raster at raster CRS point.

        Returns tuple (z, message). z is None when sampling fails.
        """
        provider = raster.dataProvider()
        if not raster.extent().contains(raster_pt):
            return None, (
                "The clicked point is outside the selected DTM extent after CRS transformation. "
                "Check the selected raster and CRS definitions."
            )
        band_count = raster.bandCount()
        if band_count < 1:
            return None, "The selected raster has no bands."

        for band in range(1, band_count + 1):
            try:
                value, ok = provider.sample(raster_pt, band)
                if ok and self._is_numeric_z(value):
                    z = float(value)
                    try:
                        if provider.sourceHasNoDataValue(band) and z == float(provider.sourceNoDataValue(band)):
                            continue
                    except Exception:  # pylint: disable=broad-except
                        pass
                    return z, None
            except Exception:  # pylint: disable=broad-except
                pass

        try:
            ident = provider.identify(raster_pt, QgsRaster.IdentifyFormatValue)
            if ident.isValid():
                for value in ident.results().values():
                    if self._is_numeric_z(value):
                        return float(value), None
        except Exception:  # pylint: disable=broad-except
            pass

        return None, (
            "Could not read a numeric elevation at this point. The point may be NoData, "
            "outside valid DTM pixels, or the selected raster may be imagery rather than elevation."
        )

    def _add_marker(self, point):
        marker = QgsVertexMarker(self.canvas)
        marker.setCenter(QgsPointXY(point))
        marker.setColor(QColor(220, 0, 0))
        marker.setIconSize(10)
        marker.setIconType(QgsVertexMarker.ICON_CIRCLE)
        marker.setPenWidth(2)
        self.markers.append(marker)

    def _geometry_type(self, name):
        """Return a geometry type compatible with QGIS 3/4 rubber bands."""
        try:
            from qgis.core import Qgis  # pylint: disable=import-outside-toplevel
            if name == "line":
                return Qgis.GeometryType.Line
            return Qgis.GeometryType.Point
        except Exception:  # pylint: disable=broad-except
            return QgsWkbTypes.LineGeometry if name == "line" else QgsWkbTypes.PointGeometry

    def _update_rubber_band(self):
        if self.rubber_band is None:
            self.rubber_band = QgsRubberBand(self.canvas, self._geometry_type("line"))
            self.rubber_band.setColor(QColor(220, 0, 0, 120))
            self.rubber_band.setWidth(2)
        self.rubber_band.reset(self._geometry_type("line"))
        for point in self.points:
            self.rubber_band.addPoint(QgsPointXY(point["x"], point["y"]), False)
        self.rubber_band.show()

    def undo_point(self):
        if not self.points:
            return
        self.points.pop()
        marker = self.markers.pop()
        self.canvas.scene().removeItem(marker)
        self._update_rubber_band()
        if len(self.points) >= 3 and self.live_check.isChecked():
            self.compute_and_display(create_layer=False)
        else:
            self._update_output_basic()

    def clear_points(self):
        self.points = []
        self.last_result = None
        for marker in self.markers:
            self.canvas.scene().removeItem(marker)
        self.markers = []
        if self.rubber_band is not None:
            self.rubber_band.reset(self._geometry_type("line"))
        self.output.clear()

    def _update_output_basic(self):
        lines = [f"Selected points: {len(self.points)}", ""]
        for idx, point in enumerate(self.points, 1):
            lines.append(f"{idx}: X={point['x']:.3f}, Y={point['y']:.3f}, Z={point['z']:.3f}")
        self.output.setPlainText("\n".join(lines))

    @staticmethod
    def fit_plane(points):
        """Fit z = ax + by + c using least squares.

        Coordinates must use compatible linear units: x east, y north, z up.
        Dip direction is azimuth clockwise from north toward steepest descent.
        """
        if len(points) < 3:
            raise ValueError("At least three points are required.")
        arr = np.array([[p["x"], p["y"], p["z"]] for p in points], dtype=float)
        x = arr[:, 0]
        y = arr[:, 1]
        z = arr[:, 2]
        matrix = np.column_stack([x, y, np.ones_like(x)])
        coeff, residuals, rank, singular_values = np.linalg.lstsq(matrix, z, rcond=None)
        if rank < 3:
            raise ValueError("The selected points are nearly collinear or numerically degenerate.")
        a, b, c = coeff
        slope = math.hypot(a, b)
        dip = math.degrees(math.atan(slope))
        dip_direction = (math.degrees(math.atan2(-a, -b)) + 360.0) % 360.0
        strike_rhr = (dip_direction - 90.0) % 360.0
        z_fit = matrix @ coeff
        residual_vec = z - z_fit
        rmse = math.sqrt(float(np.mean(residual_vec ** 2)))
        max_abs_resid = float(np.max(np.abs(residual_vec)))
        normal = np.array([-a, -b, 1.0], dtype=float)
        normal /= np.linalg.norm(normal)
        return {
            "a": float(a),
            "b": float(b),
            "c": float(c),
            "dip": float(dip),
            "dip_direction": float(dip_direction),
            "strike_rhr": float(strike_rhr),
            "rmse": float(rmse),
            "max_abs_resid": float(max_abs_resid),
            "normal": normal,
            "rank": int(rank),
            "singular_values": singular_values,
            "n": len(points),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }

    def compute_and_display(self, create_layer=None):
        """Compute and display attitude."""
        if len(self.points) < 3:
            QMessageBox.warning(self, "Need more points", "Select at least 3 points.")
            return
        project_crs = self.canvas.mapSettings().destinationCrs()
        if project_crs.isGeographic():
            QMessageBox.warning(
                self,
                "Projected CRS recommended",
                "Dip requires XY and Z in compatible linear units. The project CRS is geographic; "
                "use a projected CRS in metres or an appropriate projected planetary CRS.",
            )
        try:
            result = self.fit_plane(self.points)
        except Exception as exc:  # pylint: disable=broad-except
            QMessageBox.critical(self, "Plane fit failed", str(exc))
            return
        self.last_result = result
        lines = [
            "GeolAttitude result",
            "==================",
            f"Selected points: {result['n']}",
            "",
            f"Best-fit plane: z = {result['a']:.8g} x + {result['b']:.8g} y + {result['c']:.8g}",
            f"Dip: {result['dip']:.2f} deg",
            f"Dip direction: {result['dip_direction']:.2f} deg azimuth",
            f"Strike RHR: {result['strike_rhr']:.2f} deg",
            f"Plane normal: [{result['normal'][0]:.6f}, {result['normal'][1]:.6f}, {result['normal'][2]:.6f}]",
            f"RMSE vertical residual: {result['rmse']:.3f}",
            f"Max abs vertical residual: {result['max_abs_resid']:.3f}",
            "",
            "Points:",
        ]
        for idx, point in enumerate(self.points, 1):
            lines.append(f"{idx}: X={point['x']:.3f}, Y={point['y']:.3f}, Z={point['z']:.3f}")
        self.output.setPlainText("\n".join(lines))
        if create_layer is None:
            create_layer = self.create_layer_check.isChecked()
        if create_layer:
            self.create_result_layer(result)

    def create_result_layer(self, result):
        """Create a memory point layer containing sampled points and attitude attributes."""
        crs_auth = self.canvas.mapSettings().destinationCrs().authid()
        uri = "Point"
        if crs_auth:
            uri += f"?crs={crs_auth}"
        layer = QgsVectorLayer(uri, "geoattitude_points", "memory")
        provider = layer.dataProvider()
        provider.addAttributes([
            QgsField("pid", QVariant.Int),
            QgsField("z", QVariant.Double),
            QgsField("dip", QVariant.Double),
            QgsField("dip_dir", QVariant.Double),
            QgsField("strike", QVariant.Double),
            QgsField("rmse", QVariant.Double),
            QgsField("npoints", QVariant.Int),
            QgsField("method", QVariant.String),
        ])
        layer.updateFields()
        features = []
        for idx, point in enumerate(self.points, 1):
            feat = QgsFeature(layer.fields())
            feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(point["x"], point["y"])))
            feat.setAttributes([
                idx,
                point["z"],
                result["dip"],
                result["dip_direction"],
                result["strike_rhr"],
                result["rmse"],
                result["n"],
                "least_squares",
            ])
            features.append(feat)
        provider.addFeatures(features)
        layer.updateExtents()
        symbol = QgsMarkerSymbol.createSimple({"name": "circle", "color": "220,0,0", "size": "3"})
        layer.renderer().setSymbol(symbol)
        QgsProject.instance().addMapLayer(layer)

    def export_csv(self):
        """Export sampled points and last result to CSV."""
        if not self.points:
            QMessageBox.warning(self, "No points", "No sampled points to export.")
            return
        if self.last_result is None and len(self.points) >= 3:
            self.compute_and_display(create_layer=False)
        path, _ = QFileDialog.getSaveFileName(self, "Export GeolAttitude CSV", os.path.expanduser("~"), "CSV (*.csv)")
        if not path:
            return
        if not path.lower().endswith(".csv"):
            path += ".csv"
        result = self.last_result or {}
        with open(path, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow([
                "pid",
                "x",
                "y",
                "z",
                "dip",
                "dip_direction",
                "strike_rhr",
                "rmse",
                "npoints",
                "method",
                "timestamp",
            ])
            for idx, point in enumerate(self.points, 1):
                writer.writerow([
                    idx,
                    point["x"],
                    point["y"],
                    point["z"],
                    result.get("dip", ""),
                    result.get("dip_direction", ""),
                    result.get("strike_rhr", ""),
                    result.get("rmse", ""),
                    result.get("n", len(self.points)),
                    "least_squares" if result else "",
                    result.get("timestamp", ""),
                ])
        QMessageBox.information(self, "CSV exported", f"Saved:\n{path}")
