"""Ordinary least-squares plane fitting for GeolAttitude."""

import math

import numpy as np

from .common import (
    points_to_array,
    base_result,
    point_plane_residuals,
    add_point_usage_fields,
)


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

    # new residuals
    residuals = point_plane_residuals(points, normal, centroid)
    rmse = float(np.sqrt(np.mean(residuals ** 2)))
    max_abs_resid = float(np.max(np.abs(residuals)))

    #result = base_result("least_squares", normal, centroid, len(points))
    
    result = base_result(
        normal=normal,
        centroid=centroid,
        n=len(points),
        #method="Least squares",
        rmse=rmse,
        max_abs_resid=max_abs_resid,
    )
    
    result["rmse"] = rmse
    result["max_abs_resid"] = max_abs_resid
    
    result.update(
        {
            "a": float(a),
            "b": float(b),
            "c": float(c),
            "rmse": rmse,
            "max_abs_resid": max_abs_resid,
            "rank": int(rank),
            "singular_values": singular_values,
            "residuals": residual_vec,
        }
    )

    #return result
    return add_point_usage_fields(result, points)
