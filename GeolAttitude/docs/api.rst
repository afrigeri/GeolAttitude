API
===

Plane Fitter
------------

.. automodule:: GeolAttitude.plane_fitter
   :members:

Result Dictionary
-----------------

All fitting algorithms return a dictionary with a common set of fields. The
``normal`` field is an upward-pointing unit vector. Plane coefficients are
reported as ``a``, ``b`` and ``c`` for the equation ``z = ax + by + c`` when
that representation is available.

Residual statistics are reported with explicit orthogonal and vertical fields:

* ``orthogonal_rmse``
* ``vertical_rmse``
* ``max_abs_orthogonal_residual``
* ``max_abs_vertical_residual``
* ``orthogonal_residuals``
* ``vertical_residuals``

The compatibility aliases ``rmse`` and ``max_abs_resid`` refer to the
orthogonal RMSE and maximum absolute orthogonal residual. RANSAC results also
include inlier and outlier indices.

Common Utilities
----------------

.. automodule:: GeolAttitude.algorithms.common
   :members:

Least Squares
-------------

.. automodule:: GeolAttitude.algorithms.least_squares
   :members:

PCA
---

.. automodule:: GeolAttitude.algorithms.pca_svd
   :members:

RANSAC
------

.. automodule:: GeolAttitude.algorithms.ransac
   :members:
