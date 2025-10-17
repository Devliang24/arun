.PHONY: clean clean-build clean-test clean-reports deepclean

# Basic cleanup: Python bytecode and caches
clean:
	@echo "[clean] Removing Python caches and bytecode..."
	@find . -type d -name __pycache__ -prune -exec rm -rf {} +
	@find . -type f -name '*.py[co]' -delete
	@find . -type f -name '*$$py.class' -delete
	@rm -rf .pytest_cache .mypy_cache .ruff_cache .hypothesis .cache

# Build artifacts: sdist/wheels/egg-info
clean-build:
	@echo "[clean-build] Removing build artifacts..."
	@rm -rf build dist .eggs
	@find . -maxdepth 1 -type d -name '*.egg-info' -exec rm -rf {} +
	@find . -maxdepth 1 -type f -name '*.egg' -delete

# Test and coverage outputs
clean-test:
	@echo "[clean-test] Removing test outputs..."
	@rm -rf .coverage .coverage.* htmlcov coverage.xml

# Reports and logs (runtime artifacts)
clean-reports:
	@echo "[clean-reports] Removing logs and reports..."
	@rm -rf logs reports allure-results allure-report

# Everything above; optionally add GIT=1 to also purge ignored files
deepclean: clean clean-build clean-test clean-reports
	@if [ "$(GIT)" = "1" ]; then \
		echo "[deepclean] Running git clean for ignored files..."; \
		git clean -fdX; \
	fi

