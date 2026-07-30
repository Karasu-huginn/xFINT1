# xFINT1 — SUP Herman

Projet scolaire : application interne de gestion des notes de frais.

## Prerequisites

- Docker and Docker Compose

## Quick start

```bash
docker compose up --build
```

No configuration step is required: every environment variable has a working
development default. The API is then available at <http://localhost:8000>, and the
interactive documentation at <http://localhost:8000/api/docs>.

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
