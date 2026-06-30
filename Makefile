UV = uv run

help:	## Show this help.
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

install:	## Install dependencies (all groups).
	uv sync --all-groups

run:	## Run the MCP server over stdio.
	$(UV) hubstaff-mcp

test:	## Run the tests.
	$(UV) pytest

lint:	## Lint with ruff.
	$(UV) ruff check

format:	## Format with ruff.
	$(UV) ruff format

typecheck:	## Type-check with ty.
	$(UV) ty check

check: lint typecheck test	## Run lint, type-check and tests.
	$(UV) ruff format --check
