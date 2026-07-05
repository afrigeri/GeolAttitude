# Changelog

All notable changes to **GeolAttitude** will be documented in this file.

The format is inspired by [Keep a Changelog](https://keepachangelog.com/), and this project aims to use semantic versioning where practical.

## [Unreleased]

### Added


### Changed


### Fixed

## [0.2.7] - 2026-07-06

### Added
* RANSAC method

### Changed
* improved orientation_from_normal

### Fixed



---

## [0.2.3] - 2026-07-05

### Added

* Compatibility support for QGIS 3.44 and QGIS 4.x API transitions.
* Add unit tests for `PlaneFitter`.
* Add regression tests for dip-direction convention.
* Add tests for invalid point sets, including too few points and collinear points.

### Changed

* Reorganized fitting code into a dedicated `algorithms/` module.
* Improved separation between QGIS interface code and scientific computation code.
* Updated plugin metadata for GeolAttitude version `0.2.3`.
* Improve documentation of geological orientation conventions.
* Clarify that coordinates are interpreted as `x = Easting`, `y = Northing`, `z = elevation`.

### Fixed

* Improved handling of insufficient point selections.
* Improved compatibility with newer QGIS/PyQt enum names.
* Fixed cases where computation could fail silently or return `None`.+
* Fix dip-direction inversion: dip direction should represent the azimuth of steepest descent, measured clockwise from north.
* Method not reported into the generated vector

---

## [0.1.0] - 2026-07-02

### Added

* Initial public release.
* QGIS 3 plugin for interactive structural attitude computation.
* Least-squares plane fitting from DTM-sampled points.
* Basic computation of dip and dip direction.
* GPL-3.0 licensing.
* Interactive point selection on the QGIS map canvas.
* DTM-based elevation sampling.
* Best-fit plane computation from selected points.
* User-selectable fitting methods.
* Reporting of dip, dip direction, right-hand-rule strike, normal vector, residuals and RMSE.

