Quick Start
===========

1. Open QGIS.
2. Enable the GeolAttitude plugin.
3. Press **Start Picking**.
4. Select at least three points.
5. Choose the fitting algorithm.
6. Press **Compute**.

The plugin displays:

* Strike
* Dip
* Dip Direction
* Upward-pointing unit plane normal
* Orthogonal RMSE
* Vertical RMSE
* Maximum orthogonal residual
* Maximum vertical residual

When using RANSAC, the plugin also reports:

* Number of inliers
* Number of rejected outliers
* Outlier indices

CSV export writes the fitting method stored in the computed result, so exported
rows identify whether the result was produced with least squares, PCA/SVD or
RANSAC.

When result-layer creation is enabled, GeolAttitude creates a ``PointZ`` memory
layer. Each point stores the sampled elevation both as geometry Z and in the
``elevation`` attribute.
