## Poisker Backend

### Local dev (Docker)

```bash
cp .env.example .env
docker compose up --build
```

### Local dev (without Docker)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
