"""Robust plane fitting using RANSAC."""

import numpy as np

from .common import (
    base_result,
    normalize_vector,
    points_to_array,
    point_plane_residuals
)

#from .utils import point_plane_residuals


def _plane_from_three_points(p1, p2, p3):
    v1 = p2 - p1
    v2 = p3 - p1
    normal = np.cross(v1, v2)
    normal = normalize_vector(normal)

    if normal[2] < 0.0:
        normal = -normal

    return normal, p1


def _orthogonal_distances(points, normal, point_on_plane):
    return np.abs((points - point_on_plane) @ normal)


def _fit_plane_svd(arr):
    centroid = arr.mean(axis=0)
    centered = arr - centroid

    _, _, vh = np.linalg.svd(centered, full_matrices=False)
    normal = vh[-1]

    if normal[2] < 0.0:
        normal = -normal

    return normalize_vector(normal), centroid


def fit_ransac(
    points,
    iterations=300,
    threshold=None,
    min_inliers=3,
    random_seed=42,
):
    """
    Fit a plane using RANSAC.

    Parameters
    ----------
    points : list of dict
        Input points as dictionaries with x, y, z keys.
    iterations : int
        Number of random RANSAC trials.
    threshold : float or None
        Maximum orthogonal distance for a point to be considered an inlier.
        If None, a data-adaptive threshold is estimated.
    min_inliers : int
        Minimum number of inliers required.
    random_seed : int
        Seed for reproducible results.
    """
    arr = points_to_array(points)
    n_points = arr.shape[0]

    if n_points < 3:
        raise ValueError("At least three points are required.")

    #if threshold is None:
    #    extent = np.ptp(arr, axis=0)
    #    scale = float(np.linalg.norm(extent))
    #    threshold = max(scale * 0.01, 1.0e-9)

    if threshold is None:
        threshold = 0.1

    rng = np.random.default_rng(random_seed)

    best_inlier_mask = None
    best_inlier_count = 0
    best_rmse = np.inf

    for _ in range(iterations):
        sample_idx = rng.choice(n_points, size=3, replace=False)
        p1, p2, p3 = arr[sample_idx]

        try:
            normal, point_on_plane = _plane_from_three_points(p1, p2, p3)
        except ValueError:
            continue

        distances = _orthogonal_distances(arr, normal, point_on_plane)
        inlier_mask = distances <= threshold
        inlier_count = int(np.sum(inlier_mask))

        if inlier_count < min_inliers:
            continue

        rmse = float(np.sqrt(np.mean(distances[inlier_mask] ** 2)))

        if inlier_count > best_inlier_count or (
            inlier_count == best_inlier_count and rmse < best_rmse
        ):
            best_inlier_mask = inlier_mask
            best_inlier_count = inlier_count
            best_rmse = rmse

    if best_inlier_mask is None:
        raise ValueError("RANSAC could not find a valid plane.")

    inliers = arr[best_inlier_mask]

    if inliers.shape[0] < 3:
        raise ValueError("RANSAC found too few inliers.")

    normal, centroid = _fit_plane_svd(inliers)
    
    residuals = (arr - centroid) @ normal
    inlier_residuals = residuals[best_inlier_mask]
    
    result = base_result("ransac", normal, centroid, inliers.shape[0])
    
    a, b, c = result["a"], result["b"], result["c"]

    vertical_residuals = arr[:, 2] - (a * arr[:, 0] + b * arr[:, 1] + c)
    inlier_vertical_residuals = vertical_residuals[best_inlier_mask]

    #max_abs_vertical_residual = float(np.max(np.abs(inlier_vertical_residuals)))
    
    # Residuals from the utils module
    residuals = point_plane_residuals(points, normal, centroid)

    inlier_indices = np.where(np.abs(residuals) <= threshold)[0].tolist()
    outlier_indices = np.where(np.abs(residuals) > threshold)[0].tolist()

    rmse = np.sqrt(np.mean(residuals[inlier_indices] ** 2))
    max_abs_resid = np.max(np.abs(residuals[inlier_indices]))

    result = base_result("ransac", normal, centroid, inliers.shape[0])
    result.update(
        {
            "total_points": int(n_points),
            "inliers": int(best_inlier_count),
            "outliers": int(n_points - best_inlier_count),
            "inlier_ratio": float(best_inlier_count / n_points),
            "threshold": float(threshold),
            "residuals": residuals.tolist(),
            "inlier_residuals": inlier_residuals.tolist(),
            "rmse": float(np.sqrt(np.mean(inlier_residuals**2))),
            "vertical_residuals": vertical_residuals.tolist(),
            "inlier_vertical_residuals": inlier_vertical_residuals.tolist(),
            #"max_abs_vertical_residual": max_abs_vertical_residual,
            "rmse": rmse,
            "max_abs_resid": max_abs_resid,
        }
    )

    return result
