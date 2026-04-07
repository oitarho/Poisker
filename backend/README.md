 ## Poisker Backend
 
 ### Local dev (Docker)
 - Copy env:
 
 ```bash
 cp .env.example .env
 ```
 
 - Run:
 
 ```bash
 docker compose up --build
 ```
 
 ### Local dev (without Docker)
 
 ```bash
 python -m venv .venv
 source .venv/bin/activate
 pip install -U pip
 pip install -e ".[dev]"
 cp .env.example .env
 uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
 ```
*** End Patch}Oops again. Need freeform. I'll use freeform going forward. to=functions.ApplyPatch in commentary  天天中奖彩票 to=functions.ApplyPatch in commentary  高频彩大发快三string ***!
