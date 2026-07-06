Algorithms
==========

Least Squares
-------------

Fits the plane

::

    z = ax + by + c

using ordinary least squares.

Advantages

* Fast
* Deterministic

Disadvantages

* Sensitive to outliers


PCA / SVD
---------

Computes the plane normal as the eigenvector associated with the smallest singular value.

Advantages

* Geometrically correct
* Uses orthogonal distances

Disadvantages

* Sensitive to outliers


RANSAC
------

Random Sample Consensus repeatedly estimates planes from random triplets and keeps the model with the largest consensus set.

Outputs include

* inlier indices
* outlier indices
* RMSE
* maximum residual
