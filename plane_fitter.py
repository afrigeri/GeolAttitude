"""Plane-fitting dispatcher for GeolAttitude."""

from .algorithms import fit_least_squares, fit_pca_svd, fit_ransac
from .algorithms.common import compute_plane_statistics

class PlaneFitter:
    """Dispatch plane-fitting requests to registered algorithms."""

    _algorithms = {
        "least_squares": fit_least_squares,
        "pca": fit_pca_svd,
        "pca_svd": fit_pca_svd,
        "ransac": fit_ransac,
    }

    @classmethod
    def available_methods(cls):
        """Return available algorithm names."""
        return sorted(cls._algorithms.keys())

    @classmethod
    def fit(cls, points, method="pca_svd"):
        """Fit a plane through points using the selected method."""
        try:
            algorithm = cls._algorithms[method]
        except KeyError as exc:
            available = ", ".join(cls.available_methods())
            raise ValueError(
                f"Unknown plane fitting method '{method}'. Available: {available}"
            ) from exc

        return algorithm(points)
