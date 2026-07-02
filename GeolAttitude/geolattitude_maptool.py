# -*- coding: utf-8 -*-
"""Map tool for GeolAttitude."""

from qgis.PyQt.QtCore import Qt
from qgis.gui import QgsMapToolEmitPoint


class GeolAttitudeMapTool(QgsMapToolEmitPoint):
    """Map tool that forwards clicked map coordinates to the dock widget."""

    def __init__(self, canvas, dockwidget):
        super().__init__(canvas)
        self.canvas = canvas
        self.dockwidget = dockwidget
        self.setCursor(Qt.CrossCursor)

    def canvasReleaseEvent(self, event):  # pylint: disable=invalid-name
        point = self.toMapCoordinates(event.pos())
        self.dockwidget.add_point(point)
