# -*- coding: utf-8 -*-
"""QGIS plugin: Dip Direction Sampler.

Interactively click map points, sample Z from a selected DTM raster, and compute
best-fit plane attitude as dip, dip direction, and strike.

Install by copying the containing folder into the QGIS profile plugins directory.
"""

import math
import numpy as np

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QAction, QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QComboBox, QTextEdit, QMessageBox, QCheckBox
)
from qgis.PyQt.QtGui import QColor

from qgis.core import (
    QgsProject, QgsMapLayerType, QgsPointXY, QgsCoordinateTransform,
    QgsCoordinateReferenceSystem, QgsRaster, QgsWkbTypes, QgsFeature,
    QgsGeometry, QgsField, QgsFields, QgsVectorLayer, QgsMarkerSymbol,
    QgsPalLayerSettings, QgsVectorLayerSimpleLabeling, QgsTextFormat, QgsRectangle
)
from qgis.gui import QgsMapToolEmitPoint, QgsRubberBand, QgsVertexMarker
from qgis.PyQt.QtCore import QVariant


class DipPointTool(QgsMapToolEmitPoint):
    def __init__(self, canvas, plugin):
        super().__init__(canvas)
        self.canvas = canvas
        self.plugin = plugin
        self.setCursor(Qt.CrossCursor)

    def canvasReleaseEvent(self, event):
        point = self.toMapCoordinates(event.pos())
        self.plugin.add_point(point)


class DipDirectionSamplerPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.action = None
        self.dock = None
        self.map_tool = None
        self.previous_tool = None
        self.points = []  # list of dicts: x, y in project CRS, z, layer name
        self.markers = []
        self.rubber_band = None

    def initGui(self):
        self.action = QAction("Dip Direction Sampler", self.iface.mainWindow())
        self.action.setCheckable(True)
        self.action.triggered.connect(self.toggle)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&Dip Direction Sampler", self.action)

    def unload(self):
        self.deactivate_tool()
        if self.action:
            self.iface.removePluginMenu("&Dip Direction Sampler", self.action)
            self.iface.removeToolBarIcon(self.action)
        if self.dock:
            self.iface.removeDockWidget(self.dock)
            self.dock = None

    def toggle(self, checked):
        if checked:
            self.show_dock()
            self.activate_tool()
        else:
            self.deactivate_tool()

    def show_dock(self):
        if self.dock is None:
            self.dock = QDockWidget("Dip Direction Sampler", self.iface.mainWindow())
            self.dock.setObjectName("DipDirectionSamplerDock")
            self.dock.setWidget(self._make_panel())
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock)
        self.refresh_rasters()
        self.dock.show()

    def _make_panel(self):
        w = QWidget()
        layout = QVBoxLayout(w)

        layout.addWidget(QLabel("DTM raster layer:"))
        self.raster_combo = QComboBox()
        layout.addWidget(self.raster_combo)

        row = QHBoxLayout()
        self.pick_button = QPushButton("Start picking")
        self.pick_button.clicked.connect(self.activate_tool)
        row.addWidget(self.pick_button)
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.deactivate_tool)
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

        self.create_layer_check = QCheckBox("Create result point layer on compute")
        self.create_layer_check.setChecked(True)
        layout.addWidget(self.create_layer_check)

        self.compute_button = QPushButton("Compute dip / dip direction")
        self.compute_button.clicked.connect(self.compute_and_display)
        layout.addWidget(self.compute_button)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setMinimumHeight(260)
        layout.addWidget(self.output)

        self.refresh_button = QPushButton("Refresh rasters")
        self.refresh_button.clicked.connect(self.refresh_rasters)
        layout.addWidget(self.refresh_button)

        return w

    def refresh_rasters(self):
        if not hasattr(self, "raster_combo"):
            return
        current = self.raster_combo.currentData()
        self.raster_combo.clear()
        for lyr in QgsProject.instance().mapLayers().values():
            if lyr.type() == QgsMapLayerType.RasterLayer and lyr.isValid():
                self.raster_combo.addItem(lyr.name(), lyr.id())
        if current:
            idx = self.raster_combo.findData(current)
            if idx >= 0:
                self.raster_combo.setCurrentIndex(idx)

    def activate_tool(self):
        self.show_dock()
        if self.map_tool is None:
            self.map_tool = DipPointTool(self.canvas, self)
        self.previous_tool = self.canvas.mapTool()
        self.canvas.setMapTool(self.map_tool)
        if self.action:
            self.action.setChecked(True)
        self.iface.messageBar().pushInfo("Dip Direction Sampler", "Click points on the map. Use at least 3 points.")

    def deactivate_tool(self):
        if self.map_tool and self.canvas.mapTool() == self.map_tool:
            if self.previous_tool and self.previous_tool != self.map_tool:
                self.canvas.setMapTool(self.previous_tool)
            else:
                self.canvas.unsetMapTool(self.map_tool)
        if self.action:
            self.action.setChecked(False)

    def selected_raster(self):
        layer_id = self.raster_combo.currentData() if hasattr(self, "raster_combo") else None
        if not layer_id:
            return None
        return QgsProject.instance().mapLayer(layer_id)

    def add_point(self, map_point):
        raster = self.selected_raster()
        if raster is None:
            QMessageBox.warning(self.iface.mainWindow(), "No DTM selected", "Select a raster DTM layer first.")
            return

        # Transform clicked project/canvas coordinates to raster CRS for sampling.
        project_crs = self.canvas.mapSettings().destinationCrs()
        raster_crs = raster.crs()
        try:
            transform = QgsCoordinateTransform(project_crs, raster_crs, QgsProject.instance())
            raster_pt = transform.transform(map_point)
        except Exception as exc:
            QMessageBox.critical(self.iface.mainWindow(), "CRS transform failed", str(exc))
            return

        z, error_msg = self.sample_raster_z(raster, raster_pt)
        if z is None:
            QMessageBox.warning(self.iface.mainWindow(), "No raster value", error_msg)
            return

        self.points.append({"x": map_point.x(), "y": map_point.y(), "z": z, "raster": raster.name()})
        self._add_marker(map_point, len(self.points))
        self._update_rubber_band()
        self._update_output_basic()

    @staticmethod
    def _is_numeric_z(value):
        """Return True when a raster value can safely be used as elevation."""
        if value is None:
            return False
        try:
            z = float(value)
        except Exception:
            return False
        return math.isfinite(z)

    def sample_raster_z(self, raster, raster_pt):
        """Sample elevation from a raster at a point in raster CRS.

        Uses provider.sample first, then falls back to identify. This is more
        reliable across QGIS versions and raster providers. Returns (z, error).
        """
        provider = raster.dataProvider()

        # First check whether the transformed point is within the DTM extent.
        extent = raster.extent()
        if not extent.contains(raster_pt):
            return None, (
                "The clicked point is outside the selected DTM extent after CRS transformation. "
                "Check that you selected the correct raster and that the project/raster CRS is defined correctly."
            )

        band_count = raster.bandCount()
        if band_count < 1:
            return None, "The selected raster has no bands."

        # Try direct provider sampling for every band; elevation is usually band 1.
        for band in range(1, band_count + 1):
            try:
                value, ok = provider.sample(raster_pt, band)
                if ok and self._is_numeric_z(value):
                    z = float(value)
                    try:
                        if provider.sourceHasNoDataValue(band) and z == float(provider.sourceNoDataValue(band)):
                            continue
                    except Exception:
                        pass
                    return z, None
            except Exception:
                pass

        # Fallback to identify, useful for some providers.
        try:
            ident = provider.identify(raster_pt, QgsRaster.IdentifyFormatValue)
            if ident.isValid():
                for value in ident.results().values():
                    if self._is_numeric_z(value):
                        z = float(value)
                        return z, None
        except Exception:
            pass

        return None, (
            "Could not read a numeric elevation at this point. The point may fall on NoData, "
            "outside the raster's valid pixels, or the selected layer may be imagery rather than a DTM. "
            "Try clicking well inside the DTM footprint and ensure the DTM/elevation raster is selected."
        )

    def _add_marker(self, pt, idx):
        marker = QgsVertexMarker(self.canvas)
        marker.setCenter(QgsPointXY(pt))
        marker.setColor(QColor(255, 0, 0))
        marker.setIconSize(10)
        marker.setIconType(QgsVertexMarker.ICON_CIRCLE)
        marker.setPenWidth(2)
        self.markers.append(marker)

    def _update_rubber_band(self):
        if self.rubber_band is None:
            self.rubber_band = QgsRubberBand(self.canvas, QgsWkbTypes.LineGeometry)
            self.rubber_band.setColor(QColor(255, 0, 0, 120))
            self.rubber_band.setWidth(2)
        self.rubber_band.reset(QgsWkbTypes.LineGeometry)
        for p in self.points:
            self.rubber_band.addPoint(QgsPointXY(p["x"], p["y"]), False)
        self.rubber_band.show()

    def undo_point(self):
        if not self.points:
            return
        self.points.pop()
        marker = self.markers.pop()
        self.canvas.scene().removeItem(marker)
        self._update_rubber_band()
        self._update_output_basic()

    def clear_points(self):
        self.points = []
        for marker in self.markers:
            self.canvas.scene().removeItem(marker)
        self.markers = []
        if self.rubber_band:
            self.rubber_band.reset(QgsWkbTypes.LineGeometry)
        if hasattr(self, "output"):
            self.output.clear()

    def _update_output_basic(self):
        lines = [f"Selected points: {len(self.points)}", ""]
        for i, p in enumerate(self.points, 1):
            lines.append(f"{i}: X={p['x']:.3f}, Y={p['y']:.3f}, Z={p['z']:.3f}")
        if hasattr(self, "output"):
            self.output.setPlainText("\n".join(lines))

    @staticmethod
    def fit_plane(points):
        """Fit z = ax + by + c. Return attitude and diagnostics.

        Coordinate convention: x east, y north, z up in a projected CRS.
        Dip direction is azimuth clockwise from north, toward steepest descent.
        """
        arr = np.array([[p["x"], p["y"], p["z"]] for p in points], dtype=float)
        x = arr[:, 0]
        y = arr[:, 1]
        z = arr[:, 2]

        A = np.column_stack([x, y, np.ones_like(x)])
        coeff, residuals, rank, s = np.linalg.lstsq(A, z, rcond=None)
        a, b, c = coeff

        # z = ax + by + c. Gradient uphill is (a, b); steepest descent is (-a, -b).
        slope = math.sqrt(a * a + b * b)
        dip_rad = math.atan(slope)
        dip_deg = math.degrees(dip_rad)

        # Azimuth from north, clockwise. x=east, y=north.
        dip_dir = (math.degrees(math.atan2(-a, -b)) + 360.0) % 360.0
        strike_rhr = (dip_dir - 90.0) % 360.0

        z_fit = A @ coeff
        residual_vec = z - z_fit
        rmse = math.sqrt(float(np.mean(residual_vec ** 2))) if len(points) else float("nan")
        max_abs_resid = float(np.max(np.abs(residual_vec))) if len(points) else float("nan")

        # Plane normal. Upward normal is (-a, -b, 1), normalized.
        normal = np.array([-a, -b, 1.0], dtype=float)
        normal = normal / np.linalg.norm(normal)

        return {
            "a": float(a), "b": float(b), "c": float(c),
            "dip": dip_deg,
            "dip_direction": dip_dir,
            "strike_rhr": strike_rhr,
            "rmse": rmse,
            "max_abs_resid": max_abs_resid,
            "normal": normal,
            "rank": int(rank),
            "n": len(points),
        }

    def compute_and_display(self):
        if len(self.points) < 3:
            QMessageBox.warning(self.iface.mainWindow(), "Need more points", "Select at least 3 points.")
            return
        # Warn if map CRS is geographic; XY units in degrees make dip invalid.
        project_crs = self.canvas.mapSettings().destinationCrs()
        if project_crs.isGeographic():
            QMessageBox.warning(
                self.iface.mainWindow(),
                "Projected CRS recommended",
                "The project CRS is geographic. Dip requires XY and Z in compatible linear units. Reproject the project/canvas to a suitable metric CRS."
            )

        res = self.fit_plane(self.points)
        lines = [
            f"Selected points: {res['n']}",
            "",
            f"Best-fit plane: z = {res['a']:.8g} x + {res['b']:.8g} y + {res['c']:.8g}",
            f"Dip: {res['dip']:.2f}°",
            f"Dip direction: {res['dip_direction']:.2f}° azimuth",
            f"Strike RHR: {res['strike_rhr']:.2f}°",
            f"Plane normal: [{res['normal'][0]:.6f}, {res['normal'][1]:.6f}, {res['normal'][2]:.6f}]",
            f"RMSE vertical residual: {res['rmse']:.3f}",
            f"Max abs vertical residual: {res['max_abs_resid']:.3f}",
            "",
            "Points:",
        ]
        for i, p in enumerate(self.points, 1):
            lines.append(f"{i}: X={p['x']:.3f}, Y={p['y']:.3f}, Z={p['z']:.3f}")
        self.output.setPlainText("\n".join(lines))

        if self.create_layer_check.isChecked():
            self.create_result_layer(res)

    def create_result_layer(self, res):
        crs_auth = self.canvas.mapSettings().destinationCrs().authid()
        vl = QgsVectorLayer(f"Point?crs={crs_auth}", "dip_direction_selected_points", "memory")
        pr = vl.dataProvider()
        pr.addAttributes([
            QgsField("pid", QVariant.Int),
            QgsField("z", QVariant.Double),
            QgsField("dip", QVariant.Double),
            QgsField("dip_dir", QVariant.Double),
            QgsField("strike", QVariant.Double),
            QgsField("rmse", QVariant.Double),
        ])
        vl.updateFields()
        feats = []
        for i, p in enumerate(self.points, 1):
            f = QgsFeature(vl.fields())
            f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(p["x"], p["y"])))
            f.setAttributes([i, p["z"], res["dip"], res["dip_direction"], res["strike_rhr"], res["rmse"]])
            feats.append(f)
        pr.addFeatures(feats)
        vl.updateExtents()
        symbol = QgsMarkerSymbol.createSimple({"name": "circle", "color": "255,0,0", "size": "3"})
        vl.renderer().setSymbol(symbol)
        QgsProject.instance().addMapLayer(vl)
