"""Ordinary least-squares plane fitting for GeolAttitude."""

import numpy as np

from .common import (
    points_to_array,
    base_result,
    add_point_usage_fields,
    compute_plane_statistics,
)


def fit_least_squares(points):
    """Fit z = ax + by + c using ordinary least squares."""
    arr = points_to_array(points)
    x = arr[:, 0]
    y = arr[:, 1]
    z = arr[:, 2]

    matrix = np.column_stack([x, y, np.ones_like(x)])
    coeff, _, rank, singular_values = np.linalg.lstsq(matrix, z, rcond=None)

    if rank < 3:
        raise ValueError("The selected points are nearly collinear or numerically degenerate.")

    a, b, c = coeff
    normal = np.array([-a, -b, 1.0], dtype=float)
    centroid = arr.mean(axis=0)

    result = base_result("least_squares", normal, centroid, len(points))

    result.update(
        {
            "a": float(a),
            "b": float(b),
            "c": float(c),
            "rank": int(rank),
            "singular_values": singular_values,
        }
    )

    result.update(
        compute_plane_statistics(points, normal, centroid)
    )

    return add_point_usage_fields(result, points)
