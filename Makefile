COMPOSE_FILE=infra/compose/docker-compose.yml

up:
	docker compose -f $(COMPOSE_FILE) up --build -d

down:
	docker compose -f $(COMPOSE_FILE) down

test:
	docker compose -f $(COMPOSE_FILE) run --rm api pytest -q

test-cov:
	docker compose -f $(COMPOSE_FILE) run --rm api pytest -q --cov=core --cov=services.api --cov-report=term-missing --cov-fail-under=80

lint:
	docker compose -f $(COMPOSE_FILE) run --rm api ruff check .

check:
	docker compose -f $(COMPOSE_FILE) run --rm api ruff check .
	docker compose -f $(COMPOSE_FILE) run --rm api pytest -q --cov=core --cov=services.api --cov-report=term-missing --cov-fail-under=80
