PLUGINNAME = GeolAttitude
REPO_DIR = tpp

.PHONY: default clean tests zip

PYTHON := python
RUFF := $(PYTHON) -m ruff

default: tests zip

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	find . -name ".DS_Store" -delete
	rm -rf build dist $(PLUGINNAME).zip


# Check formatting 
format-check:
	$(RUFF) format --check .

# Format
format:
	$(RUFF) format .
	$(RUFF) check --fix .


# Check code without modifying files.
lint:
	$(RUFF) check .

# Apply all safe automatic lint fixes.
fix:
	$(RUFF) check --fix .
	$(RUFF) format .

docs: html

html:
	cd docs && $(MAKE) html

tests:
	cd .. && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -p no:cacheprovider GeolAttitude/tests -v

zip: clean format
	rm -rf build/$(PLUGINNAME)
	mkdir -p build/$(PLUGINNAME)
	rsync -av \
		--exclude "requirements.txt"\
		--exclude ".git" \
		--exclude ".github" \
		--exclude "build" \
		--exclude "dist" \
		--exclude "tests" \
		--exclude "docs" \
		--exclude "__pycache__" \
		--exclude ".pytest_cache" \
		--exclude ".mypy_cache" \
		--exclude ".ruff_cache" \
		--exclude "*.pyc" \
		--exclude "*.pyo" \
		--exclude ".DS_Store" \
		./ build/$(PLUGINNAME)/
	cd build && zip -r ../$(PLUGINNAME).zip $(PLUGINNAME)
