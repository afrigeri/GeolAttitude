tests:
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -p no:cacheprovider GeolAttitude/tests/test_plane_fitter.py -v
