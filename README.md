# GeolAttitude QGIS Plug-in
 
**(c) 2026 - Alessandro Frigeri, Italian National Institute for Astrophysics (INAF)**

![image](icon.png)


In geology, attitude refers to the three-dimensional orientation of a rock feature in space. For planar surfaces (like bedding planes or faults), it is defined by strike and dip, or by dip direction and dip. For linear features (like fold axes or faults), it is defined by trend and plunge.

The geometric elements are defined as:

- **Strike:** The compass direction of a horizontal line formed by the intersection of an inclined rock layer and a horizontal plane.
- **Dip:** The steepest angle at which a rock layer tilts downward from the horizontal, always measured at a 90-degree angle to the strike.
- **Trend:** The compass bearing of a linear structure projected onto a horizontal plane.
- **Plunge:** The vertical angle that a linear structure makes with an imaginary horizontal plane.

Plugin Builder 3 style QGIS 3.44 plugin to compute these quantities, also known as *structural attitude* from points sampled interactively on a DTM.

## Why "GeolAttitude"?

In geology, attitude refers to the orientation of a planar or linear geological feature, typically expressed as strike, dip, and dip direction.

The name GeolAttitude also reflects the curiosity, rigor, and field-oriented mindset that characterize geological work, from the field to the office.

## Motivation

Geolattitude comes from an appendix of an old PhD thesis.  Orginally a GRASS GIS script, now it has been implemented as QGIS plug-in and new methods added.

## Instructions

1. Load a projected DTM/elevation raster and optional imagery.
2. Open **Plugins > GeolAttitude > GeolAttitude**.
3. Select the DTM in the dock widget.
4. Click at least three points on the map canvas.
5. GeolAttitude samples Z from the DTM and fits the `z = ax + by + c` plane.
6. It reports dip, dip direction, right-hand-rule strike, normal vector and residuals.

If you want to record the attitude symbol in your map, you can generate the new layer and the symbology from the _Dip-Strike Tools_ plugin https://plugins.qgis.org/plugins/dip_strike_tools/ by Francesco Pennica, Giuseppe Cosentino.

## Important CRS note

Use a projected CRS with linear XY units compatible with DTM elevation units. A geographic CRS in degrees will produce invalid dip angles.

For planetary use, use an appropriate projected Moon/Mars/etc. CRS where XY units are metres.

## Method

Coordinates are treated as x=east, y=north, z=up. Dip direction is the azimuth of steepest descent measured clockwise from north.

**Acknowledgements** This work is supported by
ASI-INAF contract n.2023-3-HH.0 Esplorazione di
Marte.

