PLUGINNAME = GeolAttitude

CURR_DIR = tpp

.PHONY: zip clean

default: test clean zip

clean:
	find $(PLUGINNAME) -type d -name "__pycache__" -exec rm -rf {} +
	find $(PLUGINNAME) -type d -name ".pytest_cache" -exec rm -rf {} +
	find $(PLUGINNAME) -type d -name ".mypy_cache" -exec rm -rf {} +
	find $(PLUGINNAME) -type d -name ".ruff_cache" -exec rm -rf {} +
	find $(PLUGINNAME) -name "*.pyc" -delete
	find $(PLUGINNAME) -name "*.pyo" -delete
	find $(PLUGINNAME) -name ".DS_Store" -delete

zip: clean
	black $(PLUGINNAME)
	$(MAKE) tests
	rm -f $(PLUGINNAME).zip
	zip -r $(PLUGINNAME).zip $(PLUGINNAME) \
		-x "*/__pycache__/*" \
		-x "*.pyc" \
		-x "*.pyo" \
		-x "*/.pytest_cache/*" \
		-x "*/.mypy_cache/*" \
		-x "*/.ruff_cache/*" \
		-x "*/.git/*" \
		-x "*/.github/*" \
		-x "*/tests/*" \
		-x "*/docs/*" \
		-x "*/build/*" \
		-x "*/dist/*" \
		-x "*/.DS_Store"
		
tests:
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -p no:cacheprovider GeolAttitude/tests/test_plane_fitter.py -v		
