# -*- coding: utf-8 -*-
"""GeolAttitude plugin main module.

Plugin Builder 3 style QGIS plugin entry point.
"""

import os

from qgis.PyQt.QtCore import Qt, QCoreApplication
from qgis.PyQt.QtGui import QIcon
try:  # QGIS 4 / Qt6 compatibility
    from qgis.PyQt.QtGui import QAction
except ImportError:  # QGIS 3.44 / Qt5
    from qgis.PyQt.QtWidgets import QAction

from qgis.core import QgsApplication

from .geolattitude_dockwidget import GeolAttitudeDockWidget
from .geolattitude_maptool import GeolAttitudeMapTool


class GeolAttitude:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor."""
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []
        self.menu = self.tr("&GeolAttitude")
        self.toolbar = self.iface.addToolBar("GeolAttitude")
        self.toolbar.setObjectName("GeolAttitude")
        self.dockwidget = None
        self.map_tool = None
        self.previous_map_tool = None
        self.pluginIsActive = False

    def tr(self, message):
        """Get translated string."""
        return QCoreApplication.translate("GeolAttitude", message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None,
        checkable=False,
    ):
        """Add a toolbar icon to the toolbar."""
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)
        action.setCheckable(checkable)

        if status_tip is not None:
            action.setStatusTip(status_tip)
        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)
        if add_to_menu:
            self.iface.addPluginToMenu(self.menu, action)

        self.actions.append(action)
        return action

    def initGui(self):
        """Create menu entries and toolbar icons."""
        icon_path = os.path.join(self.plugin_dir, "icon.png")
        self.action = self.add_action(
            icon_path,
            text=self.tr("GeolAttitude"),
            callback=self.run,
            parent=self.iface.mainWindow(),
            checkable=True,
            status_tip=self.tr("Compute dip and dip direction from DTM-sampled points"),
        )

    def unload(self):
        """Remove the plugin menu item and icon."""
        self.deactivate_map_tool()
        for action in self.actions:
            self.iface.removePluginMenu(self.tr("&GeolAttitude"), action)
            self.iface.removeToolBarIcon(action)
        del self.toolbar
        if self.dockwidget is not None:
            self.iface.removeDockWidget(self.dockwidget)
            self.dockwidget = None

    def run(self, checked=True):
        """Run method that loads and starts the plugin."""
        if self.dockwidget is None:
            self.dockwidget = GeolAttitudeDockWidget(self.iface, self)
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockwidget)
            self.dockwidget.closingPlugin.connect(self.onClosePlugin)
            self.dockwidget.startPickingRequested.connect(self.activate_map_tool)
            self.dockwidget.stopPickingRequested.connect(self.deactivate_map_tool)

        self.dockwidget.refresh_rasters()
        self.dockwidget.show()
        self.pluginIsActive = True
        self.activate_map_tool()
        if hasattr(self, "action"):
            self.action.setChecked(True)

    def onClosePlugin(self):  # pylint: disable=invalid-name
        """Handle dock widget close."""
        self.deactivate_map_tool()
        self.pluginIsActive = False
        if hasattr(self, "action"):
            self.action.setChecked(False)

    def activate_map_tool(self):
        """Activate the point capture map tool."""
        if self.map_tool is None:
            self.map_tool = GeolAttitudeMapTool(self.canvas, self.dockwidget)
        current_tool = self.canvas.mapTool()
        if current_tool != self.map_tool:
            self.previous_map_tool = current_tool
        self.canvas.setMapTool(self.map_tool)
        if hasattr(self, "action"):
            self.action.setChecked(True)
        self.iface.messageBar().pushInfo(
            "GeolAttitude",
            "Click at least three points on the map. Elevation is sampled from the selected DTM.",
        )

    def deactivate_map_tool(self):
        """Deactivate the point capture map tool."""
        if self.map_tool is not None and self.canvas.mapTool() == self.map_tool:
            if self.previous_map_tool is not None and self.previous_map_tool != self.map_tool:
                self.canvas.setMapTool(self.previous_map_tool)
            else:
                self.canvas.unsetMapTool(self.map_tool)
        if hasattr(self, "action"):
            self.action.setChecked(False)
