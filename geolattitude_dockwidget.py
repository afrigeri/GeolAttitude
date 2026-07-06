# -*- coding: utf-8 -*-
"""GeolAttitude dock widget.

The UI is built programmatically to avoid Qt Designer/PyQt version friction in
QGIS 4 development builds while preserving a Plugin Builder style layout.

Hopefully this will enable a simpler transition to 4.0
"""

import csv
import math
import os

from .models.point import DigitizedPoint

from .plane_fitter import PlaneFitter

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
    QComboBox,
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
    QgsPoint,
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
        self.points = list[DigitizedPoint]
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
        # self.compute_button.clicked.connect(self.compute_and_display)
        self.compute_button.clicked.connect(self.on_compute_clicked)
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

        self.fitMethod = QComboBox()
        self.fitMethod.addItem("Least Squares", "least_squares")
        # self.fitMethod.addItem("Total Least Squares", "tls")
        self.fitMethod.addItem("PCA / SVD", "pca_svd")
        # self.fitMethod.addItem("Weighted LS", "wls")
        self.fitMethod.addItem("RANSAC", "ransac")
        # self.fitMethod.addItem("Huber", "huber")
        layout.addWidget(QLabel("Plane fit method:"))
        layout.addWidget(self.fitMethod)

        self.refresh_button = QPushButton("Refresh raster list")
        self.refresh_button.clicked.connect(self.refresh_rasters)
        layout.addWidget(self.refresh_button)

        self.setWidget(wrapper)

    def on_compute_clicked(self):
        self.compute_and_display(create_layer=None)

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
            QMessageBox.warning(
                self, "No DTM selected", "Select a DTM/elevation raster first."
            )
            return

        project_crs = self.canvas.mapSettings().destinationCrs()
        raster_crs = raster.crs()
        try:
            transform = QgsCoordinateTransform(
                project_crs, raster_crs, QgsProject.instance()
            )
            raster_pt = transform.transform(map_point)
        except Exception as exc:  # pylint: disable=broad-except
            QMessageBox.critical(self, "CRS transform failed", str(exc))
            return

        z, message = self.sample_raster_z(raster, raster_pt)
        if z is None:
            QMessageBox.warning(self, "No raster value", message)
            return

        # self.points.append(
        #    {"x": map_point.x(), "y": map_point.y(), "z": z, "raster": raster.name()}
        # )

        p = DigitizedPoint(
            pid=len(self.points) + 1,
            x=point.x(),
            y=point.y(),
            z=z,
        )

        self.points.append(p)

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
                        if provider.sourceHasNoDataValue(band) and z == float(
                            provider.sourceNoDataValue(band)
                        ):
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
            return (
                QgsWkbTypes.LineGeometry
                if name == "line"
                else QgsWkbTypes.PointGeometry
            )

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
        lines = [f"Sampled points: {len(self.points)}", ""]
        for idx, point in enumerate(self.points, 1):
            lines.append(
                f"{idx}: X={point['x']:.3f}, Y={point['y']:.3f}, Z={point['z']:.3f}"
            )
        self.output.setPlainText("\n".join(lines))

    # @staticmethod
    def fit_plane(self, points):
        """Fit the sampled points using the shared PlaneFitter API."""
        # return PlaneFitter.fit(points, method="least_squares")
        method = self.fitMethod.currentData()

        result = PlaneFitter.fit(points, method=method)
        return result

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

            if result is None:
                QMessageBox.critical(
                    self,
                    "Plane fit failed",
                    "The selected fitting algorithm returned no result.",
                )
                return
        except Exception as exc:  # pylint: disable=broad-except
            QMessageBox.critical(self, "Plane fit failed: ", str(exc))
            return
        self.last_result = result
        lines = [
            "GeolAttitude results",
            "===================",
            f"Selected points: {result['n']}",
            "",
            f"Best-fit plane: z = {result['a']:.8g} x + {result['b']:.8g} y + {result['c']:.8g}",
            f"Method: {self.fitMethod.currentData():s}",
            f"Dip: {result['dip']:.2f} deg",
            f"Dip direction: {result['dip_direction']:.2f} deg azimuth",
            f"Strike RHR: {result['strike_rhr']:.2f} deg",
            f"Plane normal: [{result['normal'][0]:.6f}, {result['normal'][1]:.6f}, {result['normal'][2]:.6f}]",
            f"Orthogonal RMSE: {result['orthogonal_rmse']:.3f}",
            f"Vertical RMSE: {result['vertical_rmse']:.3f}",
            f"Max orthogonal residual: {result['max_abs_orthogonal_residual']:.3f}",
            f"Max vertical residual: {result['max_abs_vertical_residual']:.3f}",
        ]
        if result["method"] == "ransac":
            outlier_indices = result.get("outlier_indices", [])
            if outlier_indices:
                outlier_text = ", ".join(str(i + 1) for i in outlier_indices)
            else:
                outlier_text = "none"
            lines.append("")
            lines.append(f"Rejected outliers: {len(outlier_indices)}")
            lines.append(f"Outlier point numbers: {outlier_text}")

        lines.append("")
        lines.append("Points:")
        for idx, point in enumerate(self.points, 1):
            lines.append(
                f"{idx}: X={point['x']:.3f}, Y={point['y']:.3f}, Z={point['z']:.3f}"
            )
        self.output.setPlainText("\n".join(lines))
        if create_layer is None:
            create_layer = self.create_layer_check.isChecked()
        if create_layer:
            self.create_result_layer(result)

    def create_result_layer(self, result):
        """Create a PointZ memory layer containing sampled points and attitude attributes."""
        crs_auth = self.canvas.mapSettings().destinationCrs().authid()
        uri = "PointZ"
        if crs_auth:
            uri += f"?crs={crs_auth}"
        layer = QgsVectorLayer(uri, "geolattitude_points", "memory")
        provider = layer.dataProvider()
        provider.addAttributes(
            [
                QgsField("pid", QVariant.Int),
                QgsField("elevation", QVariant.Double),
                QgsField("resid", QVariant.Double),
                QgsField("abs_resid", QVariant.Double),
                QgsField("dip", QVariant.Double),
                QgsField("dip_dir", QVariant.Double),
                QgsField("strike", QVariant.Double),
                QgsField("rmse", QVariant.Double),
                QgsField("npoints", QVariant.Int),
                QgsField("resid", QVariant.Double),
                QgsField("abs_resid", QVariant.Double),
                QgsField("method", QVariant.String),
            ]
        )
        layer.updateFields()

        features = []
        method = self.fitMethod.currentData()

        orthogonal_residuals = result.get("orthogonal_residuals", [])
        abs_orthogonal_residuals = result.get("abs_orthogonal_residuals", [])

        for idx, point in enumerate(self.points, 1):
            feat = QgsFeature(layer.fields())
            feat.setGeometry(
                QgsGeometry.fromPoint(QgsPoint(point["x"], point["y"], point["z"]))
            )

            resid = (
                orthogonal_residuals[idx - 1]
                if idx - 1 < len(orthogonal_residuals)
                else None
            )
            abs_resid = (
                abs_orthogonal_residuals[idx - 1]
                if idx - 1 < len(abs_orthogonal_residuals)
                else None
            )

            feat.setAttributes(
                [
                    idx,
                    point["z"],
                    resid,
                    abs_resid,
                    result["dip"],
                    result["dip_direction"],
                    result["strike_rhr"],
                    result["rmse"],
                    result["n"],
                    method,
                ]
            )
            features.append(feat)
        provider.addFeatures(features)
        layer.updateExtents()
        symbol = QgsMarkerSymbol.createSimple(
            {"name": "circle", "color": "220,0,0", "size": "3"}
        )
        layer.renderer().setSymbol(symbol)
        QgsProject.instance().addMapLayer(layer)

    def export_csv(self):
        """Export sampled points and last result to CSV."""
        if not self.points:
            QMessageBox.warning(self, "No points", "No sampled points to export.")
            return
        if self.last_result is None and len(self.points) >= 3:
            self.compute_and_display(create_layer=False)
        path, _ = QFileDialog.getSaveFileName(
            self, "Export GeolAttitude CSV", os.path.expanduser("~"), "CSV (*.csv)"
        )
        if not path:
            return
        if not path.lower().endswith(".csv"):
            path += ".csv"
        result = self.last_result or {}
        method = result.get("method", self.fitMethod.currentData()) if result else ""
        with open(path, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(
                [
                    "pid",
                    "x",
                    "y",
                    "z",
                    "resid",
                    "abs_resid",
                    "dip",
                    "dip_direction",
                    "strike_rhr",
                    "rmse",
                    "npoints",
                    "method",
                    "timestamp",
                ]
            )
            for idx, point in enumerate(self.points, 1):
                writer.writerow(
                    [
                        idx,
                        point["x"],
                        point["y"],
                        point["z"],
                        result.get("resid", ""),
                        result.get("abs_resid", ""),
                        result.get("dip", ""),
                        result.get("dip_direction", ""),
                        result.get("strike_rhr", ""),
                        result.get("rmse", ""),
                        result.get("n", len(self.points)),
                        method,
                        result.get("timestamp", ""),
                    ]
                )
        QMessageBox.information(self, "CSV exported", f"Saved:\n{path}")
