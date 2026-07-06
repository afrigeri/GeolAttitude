import math
import numpy as np
import pytest

#from algorithms.plane_fitter import PlaneFitter
#from plane_fitter import PlaneFitter
from GeolAttitude.plane_fitter import PlaneFitter


def assert_angle_close(actual, expected, tol=1.0):
    diff = abs((actual - expected + 180) % 360 - 180)
    assert diff <= tol


def make_points_from_plane(a, b, c, xy):
    """
    Plane: z = a*x + b*y + c
    """
    #return [(x, y, a * x + b * y + c) for x, y in xy]
    return [{"x": x, "y": y, "z": a * x + b * y + c} for x, y in xy]


def test_horizontal_plane_has_zero_dip():
    points = [
	{"x": 0, "y": 0, "z": 10},
	{"x": 1, "y": 0, "z": 10},
	{"x": 0, "y": 1, "z": 10},
	{"x": 1, "y": 1, "z": 10}
    ]

    result = PlaneFitter.fit(points, method="least_squares")

    assert result is not None
    assert result["n"] == 4
    assert result["dip"] == pytest.approx(0.0, abs=1e-6)
    assert result["rmse"] == pytest.approx(0.0, abs=1e-9)


def test_known_plane_coefficients_least_squares():
    xy = [
        (0, 0),
        (1, 0),
        (0, 1),
        (2, 1),
        (1, 2),
        (3, 2),
    ]
    points = make_points_from_plane(a=2.0, b=-3.0, c=5.0, xy=xy)

    result = PlaneFitter.fit(points, method="least_squares")

    assert result is not None
    assert result["a"] == pytest.approx(2.0, abs=1e-9)
    assert result["b"] == pytest.approx(-3.0, abs=1e-9)
    assert result["c"] == pytest.approx(5.0, abs=1e-9)
    assert result["rmse"] == pytest.approx(0.0, abs=1e-9)


def test_least_squares_reports_unit_upward_normal():
    xy = [
        (0, 0),
        (1, 0),
        (0, 1),
        (2, 1),
        (1, 2),
        (3, 2),
    ]
    points = make_points_from_plane(a=2.0, b=-3.0, c=5.0, xy=xy)

    result = PlaneFitter.fit(points, method="least_squares")
    normal_length = math.sqrt(
        sum(float(component) ** 2 for component in result["normal"])
    )

    assert normal_length == pytest.approx(1.0, abs=1e-12)
    assert result["normal"][2] > 0.0


def test_east_dipping_plane_has_dip_direction_90():
    # z decreases eastward, so the plane dips toward East.
    points = make_points_from_plane(
        a=-1.0,
        b=0.0,
        c=0.0,
        xy=[(0, 0), (1, 0), (0, 1), (2, 1), (1, 2)],
    )

    result = PlaneFitter.fit(points, method="least_squares")

    assert result is not None
    assert_angle_close(result["dip_direction"], 90.0)
    assert result["dip"] == pytest.approx(45.0, abs=1e-6)


def test_north_dipping_plane_has_dip_direction_0():
    # z decreases northward, so the plane dips toward North.
    points = make_points_from_plane(
        a=0.0,
        b=-1.0,
        c=0.0,
        xy=[(0, 0), (1, 0), (0, 1), (2, 1), (1, 2)],
    )

    result = PlaneFitter.fit(points, method="least_squares")

    assert result is not None
    assert_angle_close(result["dip_direction"], 0.0)
    assert result["dip"] == pytest.approx(45.0, abs=1e-6)


def test_pca_svd_reports_common_residual_statistics():
    points = make_points_from_plane(
        a=-1.0,
        b=0.0,
        c=0.0,
        xy=[(0, 0), (1, 0), (0, 1), (1, 1)],
    )

    result = PlaneFitter.fit(points, method="pca_svd")

    for key in [
        "rmse",
        "orthogonal_rmse",
        "vertical_rmse",
        "max_abs_resid",
        "max_abs_orthogonal_residual",
        "max_abs_vertical_residual",
        "residuals",
        "orthogonal_residuals",
        "vertical_residuals",
    ]:
        assert key in result

    assert result["orthogonal_rmse"] == pytest.approx(0.0, abs=1e-9)
    assert result["vertical_rmse"] == pytest.approx(0.0, abs=1e-9)


'''
def test_noisy_plane_has_small_rmse():
    rng = np.random.default_rng(42)

    xy = [(x, y) for x in range(5) for y in range(5)]
    clean = np.array(make_points_from_plane(0.5, -0.25, 3.0, xy), dtype=float)
    clean[:, 2] += rng.normal(0, 0.01, size=len(clean))

    result = PlaneFitter.fit(clean.tolist(), method="least_squares")

    assert result is not None
    assert result["a"] == pytest.approx(0.5, abs=0.02)
    assert result["b"] == pytest.approx(-0.25, abs=0.02)
    assert result["c"] == pytest.approx(3.0, abs=0.05)
    assert result["rmse"] < 0.03

'''
    
@pytest.mark.parametrize(
    "points",
    [
        [],
        [(0, 0, 0)],
        [(0, 0, 0), (1, 1, 1)],
    ],
)

 
    
def test_too_few_points_raises_value_error(points):
    with pytest.raises(ValueError):
        PlaneFitter.fit(points, method="least_squares")

'''
def test_collinear_points_raise_value_error():
    points = [
        (0, 0, 0),
        (1, 1, 1),
        (2, 2, 2),
        (3, 3, 3),
    ]

    with pytest.raises(ValueError):
        PlaneFitter.fit(points, method="least_squares")

'''

def test_unknown_method_raises_value_error():
    points = [
        (0, 0, 0),
        (1, 0, 1),
        (0, 1, 1),
    ]

    with pytest.raises(ValueError):
        PlaneFitter.fit(points, method="wrong_method")
        
        
def test_ransac_rejects_outlier():
    points = [
        {"x": 0, "y": 0, "z": 0},
        {"x": 1, "y": 0, "z": -1},
        {"x": 0, "y": 1, "z": 0},
        {"x": 1, "y": 1, "z": -1},
        {"x": 2, "y": 1, "z": -2},
        {"x": 100, "y": 100, "z": 1000},  # outlier
    ]

    result = PlaneFitter.fit(points, method="ransac")

    assert result["method"] == "ransac"
    assert result["inliers"] >= 5
    assert result["outliers"] >= 1
    assert_angle_close(result["dip_direction"], 90.0)
    assert result["dip"] == pytest.approx(45.0, abs=1.0)
    
def test_ransac_reports_max_abs_vertical_residual():
    points = [
        {"x": 0, "y": 0, "z": 0},
        {"x": 1, "y": 0, "z": -1},
        {"x": 0, "y": 1, "z": 0},
        {"x": 1, "y": 1, "z": -1},
        {"x": 2, "y": 1, "z": -2},
        {"x": 100, "y": 100, "z": 1000},
    ]

    result = PlaneFitter.fit(points, method="ransac")

    assert "max_abs_vertical_residual" in result
    assert result["max_abs_vertical_residual"] >= 0.0
    assert result["max_abs_vertical_residual"] < 1.0

def test_ransac_reports_outlier_indices():
    points = [
        {"x": 0, "y": 0, "z": 0},
        {"x": 1, "y": 0, "z": -1},
        {"x": 0, "y": 1, "z": 0},
        {"x": 1, "y": 1, "z": -1},
        {"x": 2, "y": 1, "z": -2},
        {"x": 100, "y": 100, "z": 1000},
    ]

    result = PlaneFitter.fit(points, method="ransac")

    assert result["outlier_indices"] == [5]
    assert result["rejected_outliers"] == 1    
    
            
