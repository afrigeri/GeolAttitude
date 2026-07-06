Principal Component Analysis (PCA-SVD)
======================================

GeolAttitude implements **Principal Component Analysis using Singular Value
Decomposition (PCA-SVD)** as a robust alternative to both classical least-squares
plane fitting and covariance-based PCA.

Rather than computing the covariance matrix explicitly, PCA-SVD directly
decomposes the centered coordinate matrix using Singular Value Decomposition
(SVD). This approach is mathematically equivalent to PCA but is generally more
numerically stable and is considered the standard implementation in modern
scientific computing.

For geological applications, PCA-SVD provides a reliable estimate of the best-fit
plane by minimizing the orthogonal distance between the sampled points and the
plane.

Background
----------

Given a set of :math:`N` sampled points

.. math::

   \mathbf{p}_i = (x_i, y_i, z_i),

the objective is to estimate the orientation of the plane that best represents
the point cloud.

The fitted plane is defined by

* its centroid;
* its normal vector;
* its geological orientation (dip and dip direction).

Centroid
--------

The centroid of the observations is

.. math::

   \mathbf{c}
   =
   (\bar{x},\bar{y},\bar{z})

where

.. math::

   \bar{x}
   =
   \frac1N
   \sum_i x_i,

.. math::

   \bar{y}
   =
   \frac1N
   \sum_i y_i,

.. math::

   \bar{z}
   =
   \frac1N
   \sum_i z_i.

Each point is translated to the centroid,

.. math::

   \mathbf{q}_i
   =
   \mathbf{p}_i-\mathbf{c}.

Centered Data Matrix
--------------------

The centered coordinates are assembled into the matrix

.. math::

   \mathbf{A}
   =
   \begin{bmatrix}
   q_{1x} & q_{1y} & q_{1z} \\
   q_{2x} & q_{2y} & q_{2z} \\
   \vdots & \vdots & \vdots \\
   q_{Nx} & q_{Ny} & q_{Nz}
   \end{bmatrix}.

Each row corresponds to one sampled point.

Singular Value Decomposition
----------------------------

The centered matrix is factorized using Singular Value Decomposition,

.. math::

   \mathbf{A}
   =
   \mathbf{U}
   \mathbf{\Sigma}
   \mathbf{V}^T.

where

* :math:`\mathbf{U}` contains the left singular vectors;
* :math:`\mathbf{\Sigma}` is the diagonal matrix of singular values;
* :math:`\mathbf{V}` contains the right singular vectors.

The singular values satisfy

.. math::

   \sigma_1
   \ge
   \sigma_2
   \ge
   \sigma_3.

Relationship with PCA
---------------------

The covariance matrix can be written as

.. math::

   \mathbf{C}
   =
   \frac1N
   \mathbf{A}^T
   \mathbf{A}.

Since

.. math::

   \mathbf{A}
   =
   \mathbf{U}
   \mathbf{\Sigma}
   \mathbf{V}^T,

it follows that

.. math::

   \mathbf{C}
   =
   \frac1N
   \mathbf{V}
   \mathbf{\Sigma}^2
   \mathbf{V}^T.

Therefore,

* the columns of :math:`\mathbf{V}` are the principal directions;
* the squared singular values are proportional to the covariance eigenvalues.

Consequently, PCA-SVD and covariance-based PCA produce the same geological
solution while using different numerical algorithms.

Plane Normal
------------

The plane normal corresponds to the right singular vector associated with the
smallest singular value,

.. math::

   \mathbf{n}
   =
   (n_x,n_y,n_z).

Its direction is arbitrary,

.. math::

   \mathbf{n}
   \equiv
   -\mathbf{n},

therefore GeolAttitude always forces

.. math::

   n_z > 0,

ensuring a unique upward-pointing unit normal.

Dip and Dip Direction
---------------------

The geological dip is computed from the normal vector as

.. math::

   \delta
   =
   \arctan
   \left(
   \frac{\sqrt{n_x^2+n_y^2}}
        {n_z}
   \right).

The dip direction corresponds to the azimuth of maximum downward slope,

.. math::

   \theta
   =
   \operatorname{atan2}(n_x,n_y),

expressed clockwise from geographic north.

The right-hand-rule strike is

.. math::

   \mathrm{Strike}
   =
   (\theta-90^\circ)
   \bmod
   360^\circ.

Residuals
---------

Once the normal vector is known, the orthogonal residual of each point is

.. math::

   d_i
   =
   \mathbf{n}
   \cdot
   (\mathbf{p}_i-\mathbf{c}).

The orthogonal Root Mean Square Error (RMSE) is

.. math::

   \mathrm{RMSE}_{orthogonal}
   =
   \sqrt{
   \frac1N
   \sum_i
   d_i^2
   }.

GeolAttitude also reports vertical residuals against the equivalent
``z = ax + by + c`` plane when that representation is available,

.. math::

   r_i
   =
   z_i - (a x_i + b y_i + c),

and their corresponding vertical RMSE. Orthogonal residuals are the preferred
geometric measure of point-to-plane fit, while vertical residuals are useful
when comparing fitted elevations against the DTM samples.

Advantages of PCA-SVD
---------------------

Compared with covariance-based PCA, SVD offers several practical advantages:

* avoids explicit construction of the covariance matrix;
* improved numerical stability;
* better handling of nearly degenerate point clouds;
* efficient implementation in optimized linear algebra libraries (LAPACK);
* standard approach adopted by NumPy and SciPy;
* mathematically equivalent to PCA.

For these reasons, PCA-SVD is generally regarded as the preferred implementation
of Principal Component Analysis.

Limitations
-----------

As with any planar fitting method, PCA-SVD assumes that the sampled surface is
approximately planar.

Results may become unreliable when

* fewer than three points are available;
* the sampled points are nearly collinear;
* the surface is strongly curved;
* the dataset contains significant outliers.

Implementation
--------------

The PCA-SVD implementation in GeolAttitude performs the following steps:

#. Compute the centroid of the selected points.
#. Translate the points to the centroid.
#. Construct the centered coordinate matrix.
#. Compute its Singular Value Decomposition using NumPy.
#. Select the last right singular vector as the plane normal.
#. Normalize the normal vector and force it upward (:math:`n_z>0`).
#. Compute dip, dip direction and right-hand-rule strike.
#. Compute orthogonal and vertical residual statistics.

Computational Complexity
------------------------

For an :math:`N \times 3` matrix, the computational complexity is approximately

.. math::

   O(N),

since only three spatial dimensions are involved.

For the relatively small point sets typically used in geological attitude
measurements, PCA-SVD is computationally inexpensive and provides excellent
numerical robustness.

References
----------

Golub, G. H., & Van Loan, C. F. (2013).
*Matrix Computations* (4th Edition).
Johns Hopkins University Press.

Jolliffe, I. T. (2002).
*Principal Component Analysis*.
Springer.

Allmendinger, R. W., Cardozo, N., & Fisher, D. (2012).
*Structural Geology Algorithms: Vectors and Tensors*.
Cambridge University Press.

Press, W. H., Teukolsky, S. A., Vetterling, W. T., & Flannery, B. P. (2007).
*Numerical Recipes: The Art of Scientific Computing*.
Cambridge University Press.
