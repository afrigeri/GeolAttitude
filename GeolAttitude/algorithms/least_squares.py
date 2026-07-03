"""Ordinary least-squares plane fitting for GeolAttitude."""

import math

import numpy as np

from .common import base_result, points_to_array


def fit_least_squares(points):
    """Fit z = ax + by + c using ordinary least squares."""
    arr = points_to_array(points)
    x = arr[:, 0]
    y = arr[:, 1]
    z = arr[:, 2]

    matrix = np.column_stack([x, y, np.ones_like(x)])
    coeff, residuals, rank, singular_values = np.linalg.lstsq(matrix, z, rcond=None)

    if rank < 3:
        raise ValueError("The selected points are nearly collinear or numerically degenerate.")

    a, b, c = coeff
    normal = np.array([-a, -b, 1.0], dtype=float)
    centroid = arr.mean(axis=0)

    z_fit = matrix @ coeff
    residual_vec = z - z_fit

    result = base_result("least_squares", normal, centroid, len(points))
    result.update(
        {
            "a": float(a),
            "b": float(b),
            "c": float(c),
            "rmse": math.sqrt(float(np.mean(residual_vec**2))),
            "max_abs_resid": float(np.max(np.abs(residual_vec))),
            "rank": int(rank),
            "singular_values": singular_values,
            "residuals": residual_vec,
        }
    )
