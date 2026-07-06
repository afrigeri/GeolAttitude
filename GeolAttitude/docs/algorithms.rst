Algorithms
==========

Least Squares
-------------

Fits the plane

::

    z = ax + by + c

using ordinary least squares.

Least squares minimizes vertical elevation residuals for the equation above.
GeolAttitude then reports the plane through the same shared result structure
used by the other algorithms, including an upward-pointing unit normal vector
and both orthogonal and vertical residual statistics.

Advantages

* Fast
* Deterministic

Disadvantages

* Sensitive to outliers


PCA / SVD
---------

Computes the plane normal as the eigenvector associated with the smallest singular value.
The returned normal vector is normalized and forced upward.

PCA/SVD minimizes orthogonal point-to-plane distances. The result includes the
same residual fields as the other methods, including orthogonal RMSE, vertical
RMSE, maximum orthogonal residual and maximum vertical residual.

Advantages

* Geometrically correct
* Uses orthogonal distances

Disadvantages

* Sensitive to outliers


RANSAC
------

Random Sample Consensus repeatedly estimates planes from random triplets and keeps the model with the largest consensus set.
The final plane is refit from the inlier set, and residual statistics are
reported for the accepted inliers while outlier indices remain available.

Outputs include

* inlier indices
* outlier indices
* orthogonal RMSE
* vertical RMSE
* maximum orthogonal residual
* maximum vertical residual
