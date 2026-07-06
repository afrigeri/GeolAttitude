"""PCA/SVD plane fitting for GeolAttitude."""

import math

import numpy as np

from .common import (
    points_to_array,
    base_result,
    normalize_vector,
    point_plane_residuals,
    add_point_usage_fields,
)


#from .utils import point_plane_residuals

def fit_pca_svd(points):
    """Fit a plane using PCA/SVD and orthogonal distances.

    This minimizes the orthogonal point-to-plane distance and can fit steep or
    vertical planes, unlike z = ax + by + c least squares.
    """
    arr = points_to_array(points)
    centroid = arr.mean(axis=0)
    centered = arr - centroid

    if np.linalg.matrix_rank(centered) < 2:
        raise ValueError("The selected points are nearly collinear or numerically degenerate.")

    _, singular_values, vh = np.linalg.svd(centered, full_matrices=False)
    normal = normalize_vector(vh[-1, :])

    if normal[2] < 0.0:
        normal = -normal

    orthogonal_residuals = centered @ normal

    residuals = point_plane_residuals(points, normal, centroid)

    rmse = np.sqrt(np.mean(residuals**2))
    max_abs_resid = np.max(np.abs(residuals))

    result = base_result("pca_svd", normal, centroid, len(points))
        
    result.update(
        {
            "rmse": rmse,
            "max_abs_resid": max_abs_resid,
            "rank": int(np.linalg.matrix_rank(centered)),
            "singular_values": singular_values,
            "eigenvalues": (singular_values**2) / max(len(points) - 1, 1),
            "residuals": orthogonal_residuals,
        }
    )
    
    result["rmse"] = rmse
    result["max_abs_resid"] = max_abs_resid

    return add_point_usage_fields(result, points)
    
    #return result
