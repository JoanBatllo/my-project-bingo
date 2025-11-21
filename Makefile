UV ?= uv
UV_RUN ?= $(UV) run
DOCKER ?= docker
IMAGE ?= my-project-bingo

.PHONY: help install run streamlit test coverage clean docker-build docker-run

help:
	@echo "Common targets:"
	@echo "  install  - Install project dependencies with uv"
	@echo "  run      - Launch the Streamlit Bingo UI (alias: streamlit)"
	@echo "  streamlit- Launch the Streamlit Bingo UI"
	@echo "  test     - Run the test suite"
	@echo "  coverage - Run tests with coverage details"
	@echo "  clean    - Remove caches and coverage artifacts"
	@echo "  docker-build - Build the Docker image"
	@echo "  docker-run   - Run the Docker image"

install:
	$(UV) sync

run: streamlit

streamlit:
	$(UV_RUN) streamlit run src/ui/streamlit_app.py

test:
	$(UV_RUN) pytest

coverage:
	$(UV_RUN) pytest --cov=src --cov-report=term-missing

clean:
	find . -name "__pycache__" -type d -prune -exec rm -rf {} +
	rm -rf .pytest_cache .coverage

docker-build:
	$(DOCKER) build -t $(IMAGE) .

docker-run: docker-build
	$(DOCKER) run --rm -it $(IMAGE)
