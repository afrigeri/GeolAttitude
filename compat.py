# This file is generated to make the plug-in
# compatible with QGIS 3 and 4

from qgis.core import Qgis
from qgis.PyQt.QtCore import Qt

QGIS_VERSION_INT = Qgis.QGIS_VERSION_INT
IS_QGIS4 = QGIS_VERSION_INT >= 40000
"""From qgis.PyQt.QtCore import Qt, QVariant, QCoreApplication from
qgis.PyQt.QtGui import QIcon from qgis.PyQt.QtWidgets import ( QMessageBox,
QDockWidget, QWidget, QVBoxLayout, QPushButton, QLabel, QTextEdit,

QComboBox, )
"""

try:
    RIGHT_DOCK_WIDGET_AREA = Qt.DockWidgetArea.RightDockWidgetArea  # Qt6 / QGIS4
except AttributeError:
    RIGHT_DOCK_WIDGET_AREA = Qt.RightDockWidgetArea  # Qt5 / QGIS3

try:
    CROSS_CURSOR = Qt.CursorShape.CrossCursor  # Qt6 / QGIS4
except AttributeError:
    CROSS_CURSOR = Qt.CrossCursor  # Qt5 / QGIS3
