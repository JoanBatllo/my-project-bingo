COMPOSE ?= docker compose

.PHONY: help up down logs build rebuild test test-cov clean lint lint-fix test-integration

help:
	@echo "Targets:"
	@echo "  build          - Build game and persistence images"
	@echo "  rebuild        - Rebuild and restart containers (for code changes)"
	@echo "  up             - Start persistence + game (Streamlit) containers"
	@echo "  down           - Stop all containers"
	@echo "  logs           - Tail compose logs"
	@echo "  test           - Run pytest locally with game/persistence on PYTHONPATH"
	@echo "  test-cov       - Run tests with coverage reporting"
	@echo "  lint           - Run ruff linter on entire codebase"
	@echo "  lint-fix       - Run ruff linter and auto-fix issues"
	@echo "  test-integration - Run integration tests"
	@echo "  clean          - Remove caches and coverage artifacts"

build:
	$(COMPOSE) build

rebuild:
	$(COMPOSE) up -d --build persistence bingo-game
	@echo "Waiting for services to be ready..."
	@sleep 3
	@echo "Opening Streamlit UI in browser..."
	@open http://localhost:8501 || xdg-open http://localhost:8501 || start http://localhost:8501 2>/dev/null || true
	$(COMPOSE) logs -f bingo-game persistence

up:
	$(COMPOSE) up -d persistence bingo-game
	@echo "Waiting for services to be ready..."
	@sleep 3
	@echo "Opening Streamlit UI in browser..."
	@open http://localhost:8501 || xdg-open http://localhost:8501 || start http://localhost:8501 2>/dev/null || true
	$(COMPOSE) logs -f bingo-game persistence

down:
	$(COMPOSE) down --rmi local

logs:
	$(COMPOSE) logs -f


test-persistence:
	cd persistence && uv run pytest

test-game:
	cd game && uv run pytest

test-integration:
	uv run pytest tests-integration/

test: test-persistence test-game test-integration


lint:
	uv run ruff check game/ persistence/ tests-integration/

lint-fix:
	uv run ruff check --fix --unsafe-fixes game/ persistence/ tests-integration/

clean:
	find . -name "__pycache__" -type d -prune -exec rm -rf {} +
	rm -rf .pytest_cache .coverage .coverage.*
