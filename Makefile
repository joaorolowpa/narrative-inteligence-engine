COMPOSE_FILE=infra/compose/docker-compose.yml

up:
	docker compose -f $(COMPOSE_FILE) up --build -d

down:
	docker compose -f $(COMPOSE_FILE) down

test:
	docker compose -f $(COMPOSE_FILE) run --rm api pytest -q

lint:
	docker compose -f $(COMPOSE_FILE) run --rm api ruff check .
