# GeolAttitude

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
![QGIS](https://img.shields.io/badge/QGIS-3.44%20%7C%204.0-green)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)

**GeolAttitude** is an open-source **QGIS** plugin for estimating the **orientation (attitude) of geological planes** from Digital Terrain Models (DTMs). By interactively selecting points on a topographic surface, the plugin computes the best-fitting plane and derives its geological orientation together with quantitative quality statistics.

Originally developed as a GRASS GIS script during the author's PhD research, GeolAttitude has been completely redesigned as a modern QGIS plugin implementing multiple fitting algorithms, robust estimation methods and uncertainty analysis.

<p align="center">
<img src="icon.png" alt="GeolAttitude" width="180"/>
</p>

---

## Author

**Alessandro Frigeri**

Italian National Institute for Astrophysics (INAF)

---

# Features

- Interactive sampling of terrain elevations from raster DTMs
- Automatic plane fitting from selected points
- Multiple estimation algorithms
  - Least Squares
  - PCA / SVD
  - RANSAC
- Bootstrap uncertainty estimation
- Computation of
  - Dip
  - Dip Direction
  - Right-Hand Rule Strike
  - Plane normal vector
- Residual statistics
  - RMSE
  - Orthogonal residuals
  - Vertical residuals
  - Maximum residual
- Creation of point and fitted-plane layers
- Compatible with terrestrial and planetary datasets
- Works with **QGIS 3.44** and **QGIS 4**

---

# Geological Attitude

In structural geology, the **attitude** describes the three-dimensional orientation of a geological feature.

For planar structures such as bedding, faults or fractures, the orientation is defined by:

- **Strike** – the compass direction of the horizontal line formed by the intersection of a geological plane with a horizontal plane.
- **Dip** – the maximum angle of inclination measured downward from the horizontal.
- **Dip Direction** – the azimuth of the direction of maximum slope.

For linear structures, orientation is expressed as:

- **Trend**
- **Plunge**

GeolAttitude focuses on estimating the orientation of planar geological surfaces directly from topographic data.

---

# Motivation

Measuring geological attitude from topography is a common task in:

- Structural geology
- Field geology
- Planetary geology
- Digital outcrop analysis
- Geomorphology
- Engineering geology

GeolAttitude provides a reproducible and quantitative workflow for estimating plane orientation directly inside QGIS, eliminating the need for external software.

The project originated from software developed during the author's PhD research and has evolved into a modern open-source QGIS plugin.

---

# Quick Start

1. Load a projected Digital Terrain Model.
2. Optionally load an orthophoto or satellite imagery.
3. Open **Plugins → GeolAttitude**.
4. Select the DTM.
5. Pick at least **three points** on the geological surface.
6. Choose the fitting algorithm.
7. Compute the best-fitting plane.
8. Inspect the resulting attitude and residual statistics.
9. Optionally create the output layers.

---

# Algorithms

Several estimation methods are available.

| Algorithm | Description |
|------------|-------------|
| Least Squares | Classical plane fitting |
| PCA / SVD | Eigenvector-based solution |
| RANSAC | Robust estimation in the presence of outliers |
| Bootstrap | Confidence estimation for dip and dip direction |

---

# Output

GeolAttitude computes:

- Dip
- Dip Direction
- Strike (Right-Hand Rule)
- Unit normal vector
- Plane equation
- Root Mean Square Error (RMSE)
- Orthogonal residuals
- Vertical residuals
- Maximum residual
- Bootstrap uncertainty (when enabled)

---

# Coordinate Reference System

The input DTM should use a **projected Coordinate Reference System** with linear units (typically metres).

Using geographic coordinates (latitude/longitude) will produce incorrect dip values.

The plugin can be applied to Earth, Moon, Mars or other planetary bodies provided that an appropriate projected CRS is used.

---

# Related Plugins

GeolAttitude complements several excellent QGIS plugins for structural geology and geological mapping.

## ThreePointMethod

Determines the orientation of geological surfaces using the classical three-point method.

QGIS Plugin Repository

https://plugins.qgis.org/plugins/ThreePointMethod/

GitHub

https://github.com/ThreePointPlugin/ThreePointMethod

---

## Dip-Strike Tools

Tools for digitizing, analysing and symbolizing structural measurements.

QGIS Plugin Repository

https://plugins.qgis.org/plugins/dip_strike_tools/

GitHub

https://github.com/fpennica/dip-strike-tools

---

## DipStrike To KMZ

Exports structural measurements to KMZ preserving geological symbols.

QGIS Plugin Repository

https://plugins.qgis.org/plugins/DipStrikeToKMZ/

GitHub

https://github.com/mellow2334/DipStriketoKMZ

---

## Limiti Geo

Computes the intersection between a geological plane and a Digital Terrain Model.

QGIS Plugin Repository

https://plugins.qgis.org/plugins/LimitiGeo/

---

## How GeolAttitude differs

While the plugins above mainly focus on digitizing measurements, three-point solutions, geological symbology or data export, **GeolAttitude** is specifically designed to estimate geological plane orientation directly from Digital Terrain Models using robust numerical methods together with residual analysis and uncertainty estimation.

---

# Documentation

Complete documentation is available on **Read the Docs**.

https://geolattitude.readthedocs.io/

---

# Development

The source code is hosted on GitHub.

https://github.com/afrigeri/GeolAttitude

Contributions, bug reports and feature requests are welcome.

---

# Citation

If GeolAttitude contributes to your scientific work, please cite the software repository and any associated scientific publication.

---

# Acknowledgements

This software has been developed at the **Italian National Institute for Astrophysics (INAF)**.

Development has been partially supported by the **ASI–INAF Contract No. 2023-3-HH.0 — Esplorazione di Marte**.

The author also wishes to acknowledge the developers of the QGIS ecosystem, whose work makes projects like GeolAttitude possible.

---

# License

GeolAttitude is released under the **GNU General Public License v3.0 (GPL-3.0)**.