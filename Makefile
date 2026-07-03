# TAA developer shortcuts. All heavy commands run inside the docker compose stack
# so host tooling stays minimal (only docker + git required).
#
# `make help` lists targets. Every target is idempotent unless noted.

.DEFAULT_GOAL := help
.PHONY: help dev up down restart logs ps shell migrate makemigrations \
        test cov lint fmt check precommit-install rebuild clean ingest-tax-code

COMPOSE ?= docker compose
APP     ?= app

help:  ## Show this help.
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

dev up:  ## Start the full stack in the background.
	$(COMPOSE) up -d

down:  ## Stop the stack (containers removed, volumes kept).
	$(COMPOSE) down

restart:  ## Restart the app + celery services (no full down).
	$(COMPOSE) restart $(APP) celery-worker celery-beat

logs:  ## Tail logs for all services (Ctrl-C to stop).
	$(COMPOSE) logs -f

ps:  ## Show container status.
	$(COMPOSE) ps

shell:  ## Open a Django shell inside the app container.
	$(COMPOSE) exec $(APP) python manage.py shell

migrate:  ## Apply DB migrations.
	$(COMPOSE) exec $(APP) python manage.py migrate

makemigrations:  ## Generate new DB migrations.
	$(COMPOSE) exec $(APP) python manage.py makemigrations

test:  ## Run the test suite inside the app container.
	$(COMPOSE) exec $(APP) pytest

cov:  ## Run tests with a coverage report.
	$(COMPOSE) exec $(APP) pytest --cov=apps --cov=taa --cov-report=term-missing

lint:  ## Ruff lint (no auto-fix).
	$(COMPOSE) exec $(APP) ruff check .

fmt:  ## Ruff format (writes changes).
	$(COMPOSE) exec $(APP) ruff format .

check:  ## Match CI locally — lint + format --check + tests.
	$(COMPOSE) exec $(APP) ruff check .
	$(COMPOSE) exec $(APP) ruff format --check .
	$(COMPOSE) exec $(APP) pytest

precommit-install:  ## Install the pre-commit hook (once per clone).
	pre-commit install

rebuild:  ## Rebuild container images (after Dockerfile / requirements changes).
	$(COMPOSE) build

clean:  ## Stop containers AND drop volumes (destructive — DB wiped).
	$(COMPOSE) down -v

ingest-tax-code:  ## Fetch + ingest the full Uzbek Tax Code (needs GEMINI_API_KEY).
	$(COMPOSE) exec $(APP) python manage.py ingest_lex_uz

