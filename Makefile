COMPOSE ?= docker compose

.PHONY: help up down logs build test test-cov clean

help:
	@echo "Targets:"
	@echo "  build          - Build game and persistence images"
	@echo "  up             - Start persistence + game (Streamlit) containers"
	@echo "  down           - Stop all containers"
	@echo "  logs           - Tail compose logs"
	@echo "  test           - Run pytest locally with game/persistence on PYTHONPATH"
	@echo "  test-cov       - Run tests with coverage reporting"
	@echo "  clean          - Remove caches and coverage artifacts"

build:
	$(COMPOSE) build

up:
	$(COMPOSE) up -d persistence bingo-game
	@echo "Waiting for services to be ready..."
	@sleep 3
	@echo "Opening Streamlit UI in browser..."
	@open http://localhost:8501 || xdg-open http://localhost:8501 || start http://localhost:8501 2>/dev/null || true
	$(COMPOSE) logs -f bingo-game persistence

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f


test:
	uv run pytest --cov=game/src --cov=game/clients --cov=game/ui --cov=persistence/src --cov-report=term-missing

clean:
	find . -name "__pycache__" -type d -prune -exec rm -rf {} +
	rm -rf .pytest_cache .coverage .coverage.*
