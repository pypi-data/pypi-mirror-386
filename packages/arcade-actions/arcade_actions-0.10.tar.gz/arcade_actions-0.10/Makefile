PACKAGE := arcade_actions
PACKAGE_DIR := src/${PACKAGE}
SHELL := env PYTHON_VERSION=3.10 /bin/bash
.SILENT: install devinstall tools test run lint format
PYTHON_VERSION ?= 3.10

setup:
	curl -LsSf https://astral.sh/uv/install.sh | sh

install:
	uv python pin $(PYTHON_VERSION)
	uv sync --no-dev

devinstall:
	uv python pin $(PYTHON_VERSION)
	uv sync --all-extras --dev

test:
	uv run pytest

run: 
	uv run python examples/invaders.py

lint:
	uv run ruff check -q

format:
	uv run ruff format

all: devinstall tools lint format test
