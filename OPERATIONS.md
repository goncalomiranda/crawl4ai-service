# Crawl4AI service operations

Inventory checked on 2026-10-07 against the service files and the running
HTTP API. Runtime facts can change after this check.

## Locations and startup

- Service code and scripts: the directory containing this file (the app
  directory)
- Python virtual environment: `$HOME/crawl4ai-env` by default (Python 3.11);
  override with `CRAWL4AI_VENV`
- Installed service unit: `/etc/systemd/system/crawler-api.service`
- Unit source: `crawler-api.service.template` in this directory.
  `./service-manager.sh install` fills in the current user (override with
  `CRAWL4AI_USER`), app directory, and virtual environment, then installs the
  result. Re-run it after changing the template.
- The unit runs `<venv>/bin/uvicorn crawler_api:app --host 0.0.0.0 --port 8000`
  from the app directory.
- The service was active when checked; it listens on port 8000.

Install and operate the systemd service from this directory:

```sh
./service-manager.sh install
./service-manager.sh start
sudo systemctl status crawler-api
./service-manager.sh restart
./service-manager.sh stop
```

The service manager also supports `logs`, `logs-api`, and `logs-newsletter`.
Use `./run-dev.sh` to start the development server with reload enabled on
`0.0.0.0:8000`.

Application logs are written to `logs/crawler_api.log` and
`logs/newsletter_crawl.log` in the app directory.

## Database

The application connects to PostgreSQL using the environment variables
`CRAWL4AI_DB_HOST`, `CRAWL4AI_DB_PORT`, `CRAWL4AI_DB_NAME`,
`CRAWL4AI_DB_USER`, and `CRAWL4AI_DB_PASSWORD`. Both processes use the shared
connection helper in `database_config.py`, which sets the connection timezone
to `America/New_York`. The FastAPI application fails at startup with the names
of any required variables that are missing.

For systemd, create `/etc/crawl4ai/crawler-api.env` outside the application
directory, owned by `root:<service-user>` with mode `0640` (and the containing
directory owned by `root:<service-user>` with mode `0750`). Put one variable
assignment per line; do not commit this file. The unit loads it through
`EnvironmentFile`. The worker subprocess inherits the service environment.
Provision and edit the file without placing the new password in a shell
command:

```sh
sudo install -d -o root -g <service-user> -m 0750 /etc/crawl4ai
sudo install -o root -g <service-user> -m 0640 /dev/null /etc/crawl4ai/crawler-api.env
sudoedit /etc/crawl4ai/crawler-api.env
```

After rotating the PostgreSQL role password and putting the new value in that
file, reload systemd and restart the service:

```sh
sudo systemctl daemon-reload
sudo systemctl restart crawler-api
```

For development, copy `.env.example` to `.env`, replace every placeholder,
and run `./run-dev.sh`. `.env` is ignored by Git. Do not put real credentials
in `.env.example`, source files, or logs. The currently exposed database
credential still needs to be rotated and installed in the systemd environment
file before restarting the deployed service.

Relations referenced by application SQL:

| Relation | Columns used by the code | How it is used |
|---|---|---|
| `core.crawl_jobs` | `id`, `status`, `error`, `created_at`, `started_at`, `finished_at` | API inserts a `STARTING` row; worker updates status and timestamps; API reads job status. |
| `crawled_content` | `url`, `title`, `content`, `created_at`, and returned `id` | Worker inserts crawled content, upserts on `url`, updates `created_at`, and returns the row ID. The schema for this unqualified name is not established by the code alone. |

This is a code-derived list, **not a verified complete inventory of current
database tables**. A live catalog query was not completed. The database object
owners, actual schema of unqualified `crawled_content`, additional relations,
constraints, and indexes are therefore **unknown**. The application connects
as `newsletter`; that does not establish the ownership of either relation.

## HTTP API

The three application routes are confirmed by the running API's OpenAPI
document:

| Method and path | Request | Behavior |
|---|---|---|
| `POST /crawl` | `{"urls": ["https://..."]}` | Inserts a crawl job with status `STARTING`, starts `newsletter_crawl.py` in a subprocess, and returns `status`, `job_id`, and `urls`. |
| `GET /job/{job_id}` | `job_id` path parameter | Returns job status and timestamps, or an error when no matching job is found. |
| `POST /openclaw-fetch` | `{"url": "https://..."}` | Crawls one URL and returns Markdown plus title/source metadata, or an error response. |

FastAPI's default interactive documentation routes are also enabled:
`GET /openapi.json`, `GET /docs`, `GET /docs/oauth2-redirect`, and `GET /redoc`.
No application health-check route is defined in the inspected API.

## Crawl workflow and Beehiiv handoff

The documented-by-code workflow currently ends at database persistence:

1. A caller submits URLs to `POST /crawl`.
2. The API creates a `STARTING` job and launches
   `newsletter_crawl.py` with the URL list and
   job ID.
3. The worker marks the job `RUNNING`, crawls starting URLs with a depth limit
   of 2 and a maximum of 20 pages per starting URL, and saves each result to
   `crawled_content`.
4. The worker marks the job `DONE`, or records `FAILED` and an error when the
   outer job workflow fails. A caller can poll `GET /job/{job_id}`.

**Beehiiv steps are not recorded in either scoped application directory.**
The inspected API and worker contain no Beehiiv endpoint or publishing step.
Accordingly, any manual steps between saved crawl content and Beehiiv—including
content selection/editing, formatting, images, approval, scheduling, and
publication confirmation—are **unknown and need confirmation from the
operator**. Do not treat the workflow above as evidence that content is
automatically sent to Beehiiv.

## Explicitly unverified

- Complete live PostgreSQL table inventory and database object ownership.
- Schema resolution and ownership for the unqualified `crawled_content` table.
- The operator's current manual process and any credentials, configuration, or
  external tooling used to prepare or publish content in Beehiiv.
- Whether there are operational steps outside the virtual environment
  and the app directory.
- Whether the exposed PostgreSQL credential has been rotated. The systemd
  environment file must be provisioned with the new credential before restart.
