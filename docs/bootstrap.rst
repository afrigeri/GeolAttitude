Bootstrap Uncertainty Estimation
================================

Overview
--------

The orientation of a geological plane estimated from a finite number of observations is always affected by
uncertainty. Even when all sampled points lie close to a plane, the estimated dip and dip direction depend on

* the number of observations,
* their spatial distribution,
* measurement errors,
* the presence of outliers.

GeolAttitude estimates this uncertainty using a **non-parametric bootstrap** approach. Unlike analytical error
propagation, the bootstrap makes very few assumptions about the statistical distribution of the observations and
naturally accounts for the geometry of the sampled point cloud.

The implementation follows the general principles introduced by Efron :cite:`Efron1979` and later expanded by
Efron and Tibshirani :cite:`EfronTibshirani1993`.


Why Bootstrap?
--------------

The least-squares solution provides a single best-fitting plane, but does not directly quantify how stable that
solution is.

Consider two datasets:

* ten points distributed over a large outcrop;
* ten points nearly aligned along a single line.

Both datasets may exhibit identical residual RMS values, yet the second dataset constrains the plane orientation
much less effectively.

Bootstrap resampling evaluates this stability by repeatedly estimating the plane from randomly resampled versions
of the original dataset.


Bootstrap Algorithm
-------------------

Given a set of :math:`N` measured points

.. math::

   P=\{\mathbf{p}_1,\mathbf{p}_2,\ldots,\mathbf{p}_N\},

the bootstrap procedure performs the following steps.

1. Randomly sample :math:`N` observations **with replacement**.
2. Fit a plane using the selected fitting algorithm.
3. Store the estimated normal vector.
4. Repeat the procedure :math:`B` times.

Typical values are

* :math:`B=1000`
* :math:`B=5000`

The resulting collection of plane normals represents the empirical probability distribution of the estimated
orientation.


Normal Vector Distribution
--------------------------

Each bootstrap realization produces a unit normal vector

.. math::

   \mathbf{n}_i.

Because a geological plane is unchanged if its normal vector changes sign,

.. math::

   \mathbf{n}
   \equiv
   -\mathbf{n},

GeolAttitude first forces every bootstrap normal to lie in the same hemisphere as the reference solution.

This avoids artificial 180° flips during statistical analysis.


Confidence Cone
---------------

Rather than treating dip and dip direction independently, GeolAttitude first estimates the uncertainty of the
normal vector itself.

The angular distance between a bootstrap normal and the reference normal is

.. math::

   \theta_i
   =
   \arccos
   \left(
   \mathbf{n}_i\cdot\mathbf{n}_{ref}
   \right).

The empirical distribution of these angular distances defines the confidence region around the estimated normal.

For a confidence level of 95%, the confidence cone is computed as the 95th percentile of the bootstrap angular
distances.

For example,

.. code-block:: text

   Normal confidence cone (95%)
   ±2.3°

means that 95% of the bootstrap solutions fall within a cone of semi-angle 2.3° around the reference normal.

This provides a coordinate-independent measure of orientation uncertainty.


Dip Uncertainty
---------------

For each bootstrap realization the normal vector is converted into geological attitude.

The dip distribution is therefore

.. math::

   \delta_1,
   \delta_2,
   \ldots,
   \delta_B.

GeolAttitude reports

* bootstrap mean,
* bootstrap standard deviation,
* confidence interval.

Example

.. code-block:: text

   Dip
   37.4°

   Bootstrap standard deviation
   0.9°

   95% confidence interval
   35.8° – 39.1°

The standard deviation describes the dispersion of the estimated dip values, whereas the confidence interval
provides an estimate of the expected range of the true dip.


Dip Direction Uncertainty
-------------------------

Dip direction is an angular quantity defined on the interval

.. math::

   [0^\circ,360^\circ).

Direct statistical analysis of azimuths is problematic because

.. math::

   359^\circ
   \approx
   1^\circ.

GeolAttitude therefore unwraps all bootstrap dip directions around the reference azimuth before computing the
statistics.

This approach avoids discontinuities at North and produces stable estimates of

* standard deviation,
* confidence interval.

Example

.. code-block:: text

   Dip direction
   122.8°

   Bootstrap standard deviation
   2.6°

   95% confidence interval
   118.1° – 127.4°


Relationship with Residuals
---------------------------

Residual statistics and bootstrap uncertainty describe different aspects of the fitted plane.

Residual statistics quantify

* goodness of fit,
* point-to-plane distances,
* measurement scatter.

Bootstrap uncertainty quantifies

* orientation stability,
* sensitivity to the sampled observations,
* confidence in dip and dip direction.

A dataset may therefore exhibit

* very small residuals but large orientation uncertainty if the points are poorly distributed,
* relatively large residuals but small orientation uncertainty if many well-distributed observations constrain the
  plane.

For this reason GeolAttitude reports both residual statistics and bootstrap uncertainty.


Computational Cost
------------------

Bootstrap estimation requires repeated plane fitting.

The computational complexity is approximately

.. math::

   O(BN),

where

* :math:`B` is the number of bootstrap realizations,
* :math:`N` is the number of observations.

Because plane fitting using Singular Value Decomposition is computationally inexpensive, several thousand
bootstrap realizations can typically be completed in a fraction of a second for datasets containing a few hundred
points.


Limitations
-----------

Bootstrap uncertainty estimates assume that the sampled observations are representative of the geological
surface.

The reported uncertainty does not account for

* systematic measurement bias,
* incorrect point selection,
* multiple geological planes,
* non-planar surfaces.

When several geological surfaces are present within the sampled dataset, robust estimation techniques such as
RANSAC should be applied before interpreting bootstrap uncertainties.


References
----------

.. bibliography::
   :filter: docname in docnames
