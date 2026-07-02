# -*- coding: utf-8 -*-
"""GeolAttitude QGIS plugin."""


def classFactory(iface):  # pylint: disable=invalid-name
    """Load GeolAttitude class from file GeolAttitude."""
    from .geolattitude import GeolAttitude
    return GeolAttitude(iface)
