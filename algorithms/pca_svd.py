"""PCA/SVD plane fitting for GeolAttitude."""

import numpy as np

from .common import (
    points_to_array,
    base_result,
    normalize_vector,
    add_point_usage_fields,
    compute_plane_statistics,
)


from .bootstrap import bootstrap_orientation_uncertainty


def fit_pca_svd(points):
    """Fit a plane using PCA/SVD and orthogonal distances.

    This minimizes the orthogonal point-to-plane distance and can fit steep or
    vertical planes, unlike z = ax + by + c least squares.
    """
    arr = points_to_array(points)
    centroid = arr.mean(axis=0)
    centered = arr - centroid

    if np.linalg.matrix_rank(centered) < 2:
        raise ValueError(
            "The selected points are nearly collinear or numerically degenerate."
        )

    _, singular_values, vh = np.linalg.svd(centered, full_matrices=False)
    normal = normalize_vector(vh[-1, :])

    if normal[2] < 0.0:
        normal = -normal

    result = base_result("pca_svd", normal, centroid, len(points))

    result.update(
        {
            "rank": int(np.linalg.matrix_rank(centered)),
            "singular_values": singular_values,
            "eigenvalues": (singular_values**2) / max(len(points) - 1, 1),
        }
    )

    result.update(compute_plane_statistics(points, normal, centroid))

    result.update(
        bootstrap_orientation_uncertainty(
            points,
            result["normal"],
            n_bootstrap=1000,
            confidence=95.0,
            random_seed=42,
        )
    )

    return add_point_usage_fields(result, points)
