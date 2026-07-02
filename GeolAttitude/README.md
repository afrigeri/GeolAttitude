# GeolAttitude

Plugin Builder 3 style QGIS 3.44 plugin to compute structural attitude from points sampled on a DTM.

## Workflow

1. Load a projected DTM/elevation raster and optional imagery.
2. Open **Plugins > GeolAttitude > GeolAttitude**.
3. Select the DTM in the dock widget.
4. Click at least three points on the map canvas.
5. GeolAttitude samples Z from the DTM and fits `z = ax + by + c`.
6. It reports dip, dip direction, right-hand-rule strike, normal vector and residuals.

## Important CRS note

Use a projected CRS with linear XY units compatible with DTM elevation units. A geographic CRS in degrees will produce invalid dip angles.

For planetary use, use an appropriate projected Moon/Mars/etc. CRS where XY units are metres.

## Files

This plugin follows a Plugin Builder 3-style layout for QGIS 3.44:

- `metadata.txt`
- `__init__.py`
- `geolattitude.py`
- `geolattitude_dockwidget.py`
- `geolattitude_maptool.py`
- `resources.qrc`
- `resources.py`
- `pb_tool.cfg`

## Method

The current version uses least-squares plane fitting. Coordinates are treated as x=east, y=north, z=up. Dip direction is the azimuth of steepest descent measured clockwise from north.
