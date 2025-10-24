# Based on Makefile for pydantic (github.com/pydantic/pydantic/blob/main/Makefile)

.DEFAULT_GOAL := all
sources = src

.PHONY: .uv  ## Check that uv is installed
.uv:
	@uv --version || echo 'Please install uv: https://docs.astral.sh/uv/getting-started/installation/'

.PHONY: .pre-commit  ## Check that pre-commit is installed
.pre-commit:
	@pre-commit -V || echo 'Please install pre-commit: https://pre-commit.com/'

.PHONY: install  ## Install the package, dependencies, and pre-commit for local development
install: .uv .pre-commit
	uv pip install -e ".[dev,linting]"
	pre-commit install --install-hooks

.PHONY: sync  ## Sync dependencies and lockfiles
sync: .uv clean
	uv pip install -e . --force-reinstall
	uv sync

.PHONY: format  ## Auto-format python source files
format: .uv
	uv run ruff format $(sources)
	uv run ruff check --fix $(sources)

.PHONY: lint  ## Lint python source files
lint: .uv
	uv run ruff format --check $(sources)
	uv run ruff check $(sources)
	uv run mypy $(sources)

.PHONY: codespell  ## Use Codespell to do spellchecking
codespell: .pre-commit
	pre-commit run codespell --all-files

.PHONY: all  ## Run the standard set of checks performed in CI
all: lint codespell

.PHONY: clean  ## Clear local caches and build artifacts
clean:
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name '*.py[co]' -exec rm -f {} +
	find . -type f -name '*~' -exec rm -f {} +
	find . -type f -name '.*~' -exec rm -f {} +
	rm -rf .cache
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf htmlcov
	rm -rf *.egg-info
	rm -f .coverage
	rm -f .coverage.*
	rm -rf build
	rm -rf dist
	rm -rf site
	rm -rf docs/_build
	rm -rf docs/.changelog.md docs/.version.md docs/.tmp_schema_mappings.html
	rm -rf fastapi/test.db
	rm -rf coverage.xml
	rm -rf __pypackages__ uv.lock

.PHONY: help  ## Display this message
help:
	@grep -E \
		'^.PHONY: .*?## .*$$' $(MAKEFILE_LIST) | \
		sort | \
		awk 'BEGIN {FS = ".PHONY: |## "}; {printf "\033[36m%-19s\033[0m %s\n", $$2, $$3}'
