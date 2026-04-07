BACKEND_DIR=backend

.PHONY: up
up:
	docker compose up --build

.PHONY: down
down:
	docker compose down

.PHONY: logs
logs:
	docker compose logs -f --tail=200

.PHONY: migrate
migrate:
	docker compose run --rm backend alembic upgrade head

.PHONY: seed
seed: seed-locations seed-categories

.PHONY: seed-dev
seed-dev: seed
	docker compose run --rm backend python3 -m app.scripts.seed_dev

.PHONY: reindex
reindex: reindex-typesense

.PHONY: seed-locations
seed-locations:
	docker compose run --rm backend python3 -m app.scripts.seed_locations

.PHONY: seed-categories
seed-categories:
	docker compose run --rm backend python3 -m app.scripts.seed_categories

.PHONY: reindex-typesense
reindex-typesense:
	docker compose run --rm backend python3 -m app.scripts.reindex_typesense

