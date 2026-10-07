# crawl4ai-service

A small FastAPI service that wraps [Crawl4AI](https://github.com/unclecode/crawl4ai) to run web crawls, track job status, and store results in PostgreSQL.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/crawl` | Start a crawl job |
| GET | `/job/{job_id}` | Get the status of a job |
| POST | `/openclaw-fetch` | Fetch a page on demand |

## Project layout

- `crawler_api.py` – FastAPI application
- `newsletter_crawl.py` – crawl worker (deep crawl with keyword scoring)
- `database_config.py` – shared PostgreSQL connection helper
- `service-manager.sh` – install/manage the systemd service
- `run-dev.sh` – development server with auto-reload
- `crawler-api.service.template` – systemd unit template
- `migrations/` – versioned yoyo database migrations
- `scripts/` – `backup-db.sh`, `migrate.sh`, `migrate.py`, `check_migrations.py`
- `OPERATIONS.md` – detailed operations notes

## Requirements

- Python 3.11 virtual environment with `crawl4ai`, `fastapi`, `uvicorn` and a PostgreSQL driver (default location `$HOME/crawl4ai-env`, override with `CRAWL4AI_VENV`)
- A PostgreSQL database

## Configuration

Copy `.env.example` to `.env` and fill in:

```
CRAWL4AI_DB_HOST
CRAWL4AI_DB_PORT
CRAWL4AI_DB_NAME
CRAWL4AI_DB_USER
CRAWL4AI_DB_PASSWORD
```

`.env` is git-ignored; never commit credentials.

## Running

Development (port 8000, auto-reload):

```sh
./run-dev.sh
```

As a systemd service (reads `/etc/crawl4ai/crawler-api.env`):

```sh
./service-manager.sh install
./service-manager.sh start
./service-manager.sh logs
```

Backups, restore and migrations: see the *Backups, restore and migrations* section of [OPERATIONS.md](OPERATIONS.md).

See [OPERATIONS.md](OPERATIONS.md) for environment file setup, logs and maintenance.
