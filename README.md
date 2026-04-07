## Poisker (Local MVP)

Regional classifieds platform MVP for the Chechen Republic.

### Prerequisites
- Docker + Docker Compose
- (Optional) Python 3.12 (only if running backend outside Docker)
- (Optional) Flutter SDK (frontend runs outside Docker for now)

### Quick start (Docker)

1) Copy env (root is for ports/secrets; backend env is app settings):

```bash
cp .env.example .env
cp backend/.env.example backend/.env
```

2) Start services:

```bash
make up
```

Backend will wait for Postgres/Redis/Typesense and run migrations automatically on startup.

### Useful commands

```bash
make logs
make down
make migrate
make seed
make reindex
```

### Ports (defaults)
- Backend: `http://localhost:8000`
- Postgres: `localhost:5432`
- Redis: `localhost:6379`
- Typesense: `http://localhost:8108`

### Frontend (Flutter)
Frontend is expected to run outside Docker initially.
Containerization can be added later (e.g. nginx for web build).
