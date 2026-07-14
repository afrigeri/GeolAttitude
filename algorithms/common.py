"""Shared helpers for GeolAttitude plane-fitting algorithms."""

import math
from datetime import datetime

import numpy as np


def points_to_array(points):
    """Convert point dictionaries or DigitizedPoint objects to an Nx3 NumPy
    array."""
    if len(points) < 3:
        raise ValueError("At least three points are required.")

    rows = []
    for p in points:
        if isinstance(p, dict):
            rows.append([p["x"], p["y"], p["z"]])
        else:
            rows.append([p.x, p.y, p.z])

    arr = np.array(rows, dtype=float)

    if arr.ndim != 2 or arr.shape[1] != 3:
        raise ValueError("Points must define x, y, z coordinates.")

    if not np.all(np.isfinite(arr)):
        raise ValueError("Point coordinates must be finite numeric values.")

    return arr


def normalize_vector(vector):
    """Return a normalized vector."""
    vector = np.asarray(vector, dtype=float)
    norm = np.linalg.norm(vector)

    if norm == 0.0 or not np.isfinite(norm):
        raise ValueError("Cannot normalize a zero or invalid vector.")

    return vector / norm


def orientation_from_normal(normal):
    """Compute geological orientation from a plane normal.

    Coordinates are assumed to be x=east, y=north, z=up.
    Dip direction is the azimuth of steepest descent, clockwise from north.
    Strike is returned using the right-hand rule.

    Parameters
    ----------
    normal : array-like
        Plane normal vector. It does not need to be normalized.

    Returns
    -------
    normal : numpy.ndarray
        Upward-pointing unit normal vector.
    dip : float
    dip_direction : float
    strike_rhr : float
    """
    normal = normalize_vector(normal)

    if normal[2] < 0.0:
        normal = -normal

    nx, ny, nz = normal

    dip = math.degrees(math.atan2(math.hypot(nx, ny), nz))

    dip_direction = (math.degrees(math.atan2(nx, ny)) + 360.0) % 360.0

    strike_rhr = (dip_direction - 90.0) % 360.0

    return normal, float(dip), float(dip_direction), float(strike_rhr)


def orientation_from_normal_old(normal):
    """Compute geological orientation from an upward-pointing plane normal.

    Coordinates are assumed to be x=east, y=north, z=up. Dip direction
    is the azimuth of steepest descent, clockwise from north. Strike is
    returned using the right-hand rule.
    """
    normal = normalize_vector(normal)

    if normal[2] < 0.0:
        normal = -normal

    nx, ny, nz = normal

    dip = math.degrees(math.atan2(math.hypot(nx, ny), abs(nz)))
    # dip_direction = (math.degrees(math.atan2(-nx, -ny)) + 360.0) % 360.0
    dip_direction = (math.degrees(math.atan2(nx, ny)) + 360.0) % 360.0
    strike_rhr = (dip_direction - 90.0) % 360.0

    return normal, float(dip), float(dip_direction), float(strike_rhr)


def plane_coefficients_from_normal(normal, centroid):
    """Return z = ax + by + c coefficients from a plane normal and centroid.

    Vertical planes cannot be represented as z = ax + by + c, so the
    coefficients are returned as NaN in that case.
    """
    normal = normalize_vector(normal)
    centroid = np.asarray(centroid, dtype=float)

    nx, ny, nz = normal

    if abs(nz) < 1.0e-12:
        return float("nan"), float("nan"), float("nan")

    a = -nx / nz
    b = -ny / nz
    c = (nx * centroid[0] + ny * centroid[1] + nz * centroid[2]) / nz

    return float(a), float(b), float(c)


def base_result(method, normal, centroid, n):
    """Create the common part of a plane-fit result dictionary."""
    normal, dip, dip_direction, strike_rhr = orientation_from_normal(normal)
    a, b, c = plane_coefficients_from_normal(normal, centroid)

    return {
        "method": method,
        "n": int(n),
        "normal": normal,
        "centroid": centroid,
        "a": a,
        "b": b,
        "c": c,
        "dip": dip,
        "dip_direction": dip_direction,
        "strike_rhr": strike_rhr,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "n_selected": int(n),
        "n_used": int(n),
        "n_inliers": int(n),
        "inlier_indices": list(range(int(n))),
        "outlier_indices": [],
    }


def point_plane_residuals(points, normal, centroid):
    """
    Compute the signed orthogonal residuals of a set of 3D points
    relative to a plane.

    The residual of each point is the perpendicular (orthogonal)
    distance from the point to the plane defined by its unit normal
    vector and a point lying on the plane (the centroid).

    Positive and negative residuals indicate on which side of the
    plane the point lies with respect to the plane normal.

    Unlike vertical residuals (Δz), orthogonal residuals are
    independent of the plane orientation and therefore provide a
    geometrically meaningful measure of plane-fitting accuracy for
    arbitrarily dipping geological surfaces.

    Parameters
    ----------
    points : list of dict
        Input points as dictionaries with keys ``'x'``, ``'y'`` and
        ``'z'``.

    normal : array-like, shape (3,)
        Plane normal vector. It does not need to be normalized; the
        function automatically converts it to a unit vector.

    centroid : array-like, shape (3,)
        Any point belonging to the fitted plane, typically the centroid
        of the input points.

    Returns
    -------
    numpy.ndarray
        One signed orthogonal residual for each input point, expressed
        in the same units as the input coordinates (typically metres).

    Notes
    -----
    The residual is computed as

    .. math::

        r_i = (\\mathbf{p}_i - \\mathbf{c}) \\cdot \\hat{\\mathbf{n}}

    where

    * :math:`\\mathbf{p}_i` is the i-th point,
    * :math:`\\mathbf{c}` is a point on the plane,
    * :math:`\\hat{\\mathbf{n}}` is the unit normal vector.

    These residuals are used to compute:

    * Root Mean Square Error (RMSE)
    * Maximum absolute orthogonal residual
    * RANSAC inlier/outlier classification

    They should not be confused with vertical residuals, which measure
    only elevation differences and depend on the dip of the fitted
    plane.
    """

    arr = points_to_array(points)
    normal = normalize_vector(normal)
    centroid = np.asarray(centroid, dtype=float)

    return (arr - centroid) @ normal


def point_plane_vertical_residuals(points, a, b, c):
    """
    Return vertical residuals between observed z values and the plane
    z = ax + by + c.

    Units are the same as the input z coordinates.
    """
    arr = points_to_array(points)

    z_fit = a * arr[:, 0] + b * arr[:, 1] + c

    return arr[:, 2] - z_fit


def compute_plane_statistics(points, normal, centroid, inlier_indices=None):
    """
    Compute common residual statistics for a fitted plane.

    Orthogonal residuals are perpendicular distances to the plane.
    Vertical residuals are elevation differences relative to z = ax + by + c.

    Returns
    -------
    dict
        Common residual statistics, including RMSE values and maximum residuals.
    """
    # arr = points_to_array(points)

    orthogonal_residuals = point_plane_residuals(points, normal, centroid)
    abs_orthogonal_residuals = np.abs(orthogonal_residuals)

    temp = base_result("statistics", normal, centroid, len(points))
    a, b, c = temp["a"], temp["b"], temp["c"]

    vertical_residuals = point_plane_vertical_residuals(points, a, b, c)

    abs_vertical_residuals = np.abs(vertical_residuals)
    abs_orthogonal_residuals = np.abs(orthogonal_residuals)

    if inlier_indices is None:
        used_indices = list(range(len(points)))
    else:
        used_indices = [int(i) for i in inlier_indices]

    used_orthogonal = orthogonal_residuals[used_indices]
    used_vertical = vertical_residuals[used_indices]

    return {
        "orthogonal_residuals": orthogonal_residuals.tolist(),
        "abs_orthogonal_residuals": abs_orthogonal_residuals.tolist(),
        "vertical_residuals": vertical_residuals.tolist(),
        "abs_vertical_residuals": abs_vertical_residuals.tolist(),
        "abs_residuals": abs_orthogonal_residuals.tolist(),
        "residuals": orthogonal_residuals.tolist(),
        "inlier_residuals": used_orthogonal.tolist(),
        "inlier_vertical_residuals": used_vertical.tolist(),
        "rmse": float(np.sqrt(np.mean(used_orthogonal**2))),
        "orthogonal_rmse": float(np.sqrt(np.mean(used_orthogonal**2))),
        "vertical_rmse": float(np.sqrt(np.mean(used_vertical**2))),
        "max_abs_resid": float(np.max(np.abs(used_orthogonal))),
        "max_abs_orthogonal_residual": float(np.max(np.abs(used_orthogonal))),
        "max_abs_vertical_residual": float(np.max(np.abs(used_vertical))),
    }


def add_point_usage_fields(result, points, inlier_indices=None):
    """Add common selected/used/inlier/outlier fields to a fit result."""
    n_selected = len(points)

    if inlier_indices is None:
        inlier_indices = list(range(n_selected))
    else:
        inlier_indices = sorted(int(i) for i in inlier_indices)

    inlier_set = set(inlier_indices)
    outlier_indices = [i for i in range(n_selected) if i not in inlier_set]

    result["n"] = n_selected
    result["n_selected"] = n_selected
    result["n_used"] = len(inlier_indices)
    result["n_inliers"] = len(inlier_indices)
    result["inlier_indices"] = inlier_indices
    result["outlier_indices"] = outlier_indices

    return result
