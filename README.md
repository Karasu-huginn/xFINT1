# xFINT1

Projet scolaire : application interne de gestion des notes de frais.

## Prerequisites

- Docker and Docker Compose

## Quick start

```bash
docker compose up --build
```

No configuration step is required, every environment variable has a working development default.
Every route is served under the `/api` prefix:

| What | URL |
|---|---|
| Health check | <http://localhost:8000/api/health> |
| Interactive documentation (Swagger UI) | <http://localhost:8000/api/docs> |
| Alternative documentation (ReDoc) | <http://localhost:8000/api/redoc> |
| OpenAPI schema | <http://localhost:8000/api/openapi.json> |

Creating a `.env` is optional and only needed to override a default:

```bash
cp .env.example .env
```

## Manager account

The manager account is seeded automatically on every start:

| Email | Password |
|---|---|
| `manager@supherman.com` | `Suph3rm4n!` |

## Running the tests

```bash
docker compose run --rm api pytest
```
