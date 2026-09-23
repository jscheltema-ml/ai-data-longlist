# long-list

TODO: describe Long List (one-paragraph summary of what the tool does and who it is for).

- **Backend** — `src/core` (FastAPI, deployed as an Azure Container App).

## Layout

```
src/core/
  api/        app wiring: main.py, config.py, auth.py, analytics.py
  clients/    shared outbound clients (Azure OpenAI, Foundry)
  services/   one package per service, each owning its router
  tests/
config/       per-environment settings, read by terraform and CI
infra-longlist/   terraform for the Azure resources
```

## Adding a service

A service is a package under `src/core/services/` that owns its own router, auth and
analytics. Wire it up by including its router in `api/main.py`; nothing else in the app
needs to know about it. Anything that must happen once at startup belongs in a FastAPI
`lifespan` handler rather than at import time, so importing the module does not reach
out to Azure.

## Running locally

Settings are read from the environment, falling back to `src/core/.env`. The fields
without defaults in `api/config.py` must all be present or the app refuses to start and
names what is missing.

```bash
poetry install
poetry run uvicorn api.main:app --reload --app-dir src/core
```

Then `GET http://127.0.0.1:8000/health`.

```bash
poetry run pytest
poetry run ruff check .
```

## Before the first deploy

- [ ] Fill in `foundry_endpoint` in `config/dev.json` and `config/prd.json`; they were
      blanked during the port and the app will not start without them.
- [ ] Set `project_name` in `config/prd.json`.
- [ ] Set `app_client_id` in both configs once the Entra app registrations exist.

## Docs

- **CI/CD, branch model & deploy** → [`.github/README.md`](.github/README.md)
