"""Bootstrap uncertainty estimation for GeolAttitude plane fitting."""

import numpy as np

from .common import orientation_from_normal, points_to_array


def _fit_bootstrap_pca_normal(sample):
    """Fit a plane normal to a bootstrap sample using PCA/SVD."""
    centroid = sample.mean(axis=0)
    centered = sample - centroid

    if np.linalg.matrix_rank(centered) < 2:
        return None

    _, _, vh = np.linalg.svd(centered, full_matrices=False)
    normal = vh[-1, :]
    normal, _, _, _ = orientation_from_normal(normal)
    return normal


def _angular_distance_deg(v1, v2):
    """Return angular distance between two unit vectors in degrees."""
    dot = float(np.clip(np.dot(v1, v2), -1.0, 1.0))
    return float(np.degrees(np.arccos(dot)))


def bootstrap_orientation_uncertainty(
    points,
    reference_normal,
    n_bootstrap=1000,
    confidence=95.0,
    random_seed=42,
):
    """Estimate orientation uncertainty by bootstrap resampling.

    Parameters
    ----------
    points : sequence
        Input points, either dictionaries or DigitizedPoint-like objects.
    reference_normal : array-like
        Normal vector from the original fitted plane.
    n_bootstrap : int
        Number of bootstrap resamples.
    confidence : float
        Confidence level, usually 95.
    random_seed : int or None
        Random seed for reproducible results.

    Returns
    -------
    dict
        Bootstrap uncertainty statistics for dip, dip direction and normal vector.
    """
    arr = points_to_array(points)
    n_points = len(arr)

    if n_points < 3:
        raise ValueError(
            "At least three points are required for bootstrap uncertainty."
        )

    reference_normal, _, _, _ = orientation_from_normal(reference_normal)

    rng = np.random.default_rng(random_seed)

    normals = []
    dips = []
    dip_directions = []

    for _ in range(int(n_bootstrap)):
        indices = rng.integers(0, n_points, size=n_points)
        sample = arr[indices]

        normal = _fit_bootstrap_pca_normal(sample)
        if normal is None:
            continue

        # Keep bootstrap normals in the same hemisphere as the reference
        # normal.
        if np.dot(normal, reference_normal) < 0.0:
            normal = -normal

        normal, dip, dip_direction, _ = orientation_from_normal(normal)

        normals.append(normal)
        dips.append(dip)
        dip_directions.append(dip_direction)

    if not normals:
        return {
            "bootstrap_enabled": True,
            "bootstrap_success": False,
            "bootstrap_n": 0,
            "bootstrap_message": "No valid bootstrap samples were produced.",
        }

    normals = np.asarray(normals, dtype=float)
    dips = np.asarray(dips, dtype=float)
    dip_directions = np.asarray(dip_directions, dtype=float)

    angular_distances = np.array(
        [_angular_distance_deg(normal, reference_normal) for normal in normals],
        dtype=float,
    )

    alpha = (100.0 - float(confidence)) / 2.0
    lo = alpha
    hi = 100.0 - alpha

    # Circular handling for dip direction: unwrap around reference azimuth.
    _, _, reference_dip_direction, _ = orientation_from_normal(reference_normal)
    dd_delta = ((dip_directions - reference_dip_direction + 180.0) % 360.0) - 180.0

    return {
        "bootstrap_enabled": True,
        "bootstrap_success": True,
        "bootstrap_n": int(len(normals)),
        "bootstrap_requested_n": int(n_bootstrap),
        "bootstrap_confidence": float(confidence),
        # Useful scalar summary: confidence cone around the normal.
        "normal_confidence_cone_deg": float(
            np.percentile(angular_distances, confidence)
        ),
        "normal_angular_std_deg": (
            float(np.std(angular_distances, ddof=1))
            if len(angular_distances) > 1
            else 0.0
        ),
        # Dip uncertainty.
        "dip_bootstrap_mean": float(np.mean(dips)),
        "dip_bootstrap_std": (float(np.std(dips, ddof=1)) if len(dips) > 1 else 0.0),
        "dip_bootstrap_ci_low": float(np.percentile(dips, lo)),
        "dip_bootstrap_ci_high": float(np.percentile(dips, hi)),
        # Dip direction uncertainty, expressed around the reference azimuth.
        "dip_direction_bootstrap_std": (
            float(np.std(dd_delta, ddof=1)) if len(dd_delta) > 1 else 0.0
        ),
        "dip_direction_bootstrap_ci_low": float(
            (reference_dip_direction + np.percentile(dd_delta, lo)) % 360.0
        ),
        "dip_direction_bootstrap_ci_high": float(
            (reference_dip_direction + np.percentile(dd_delta, hi)) % 360.0
        ),
        # Optional detailed arrays for advanced use.
        "bootstrap_dips": dips.tolist(),
        "bootstrap_dip_directions": dip_directions.tolist(),
        "bootstrap_normal_angular_distances": angular_distances.tolist(),
    }
