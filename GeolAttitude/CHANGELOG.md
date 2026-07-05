# Changelog

All notable changes to **GeolAttitude** will be documented in this file.

The format is inspired by [Keep a Changelog](https://keepachangelog.com/), and this project aims to use semantic versioning where practical.

## [Unreleased]

### Added

* Add unit tests for `PlaneFitter`.
* Add regression tests for dip-direction convention.
* Add tests for invalid point sets, including too few points and collinear points.

### Changed

* Improve documentation of geological orientation conventions.
* Clarify that coordinates are interpreted as `x = Easting`, `y = Northing`, `z = elevation`.

### Fixed

* Fix dip-direction inversion: dip direction should represent the azimuth of steepest descent, measured clockwise from north.

---

## [0.2.3] - 2026-07-05

### Added

* Plugin Builder 3-style QGIS plugin layout.
* Interactive point selection on the QGIS map canvas.
* DTM-based elevation sampling.
* Best-fit plane computation from selected points.
* User-selectable fitting methods.
* Reporting of dip, dip direction, right-hand-rule strike, normal vector, residuals and RMSE.
* Compatibility support for QGIS 3.44 and QGIS 4.x API transitions.

### Changed

* Reorganized fitting code into a dedicated `algorithms/` module.
* Improved separation between QGIS interface code and scientific computation code.
* Updated plugin metadata for GeolAttitude version `0.2.3`.

### Fixed

* Improved handling of insufficient point selections.
* Improved compatibility with newer QGIS/PyQt enum names.
* Fixed cases where computation could fail silently or return `None`.

---

## [0.1.0] - 2026-07-02

### Added

* Initial public release.
* QGIS 3 plugin for interactive structural attitude computation.
* Least-squares plane fitting from DTM-sampled points.
* Basic computation of dip and dip direction.
* GPL-3.0 licensing.

