import os
from dataclasses import dataclass
from typing import Mapping

import psycopg2


@dataclass(frozen=True)
class DatabaseConfig:
    host: str
    port: int
    database: str
    user: str
    password: str


def get_database_config(
    environ: Mapping[str, str] | None = None,
) -> DatabaseConfig:
    env = os.environ if environ is None else environ
    variable_names = (
        "CRAWL4AI_DB_HOST",
        "CRAWL4AI_DB_PORT",
        "CRAWL4AI_DB_NAME",
        "CRAWL4AI_DB_USER",
        "CRAWL4AI_DB_PASSWORD",
    )
    missing = [name for name in variable_names if not env.get(name, "").strip()]
    if missing:
        raise RuntimeError(
            "Missing required database configuration: "
            + ", ".join(missing)
            + ". Set these environment variables before starting the service."
        )

    try:
        port = int(env["CRAWL4AI_DB_PORT"])
    except ValueError:
        raise RuntimeError("CRAWL4AI_DB_PORT must be an integer from 1 to 65535.") from None
    if not 1 <= port <= 65535:
        raise RuntimeError("CRAWL4AI_DB_PORT must be an integer from 1 to 65535.")

    return DatabaseConfig(
        host=env["CRAWL4AI_DB_HOST"],
        port=port,
        database=env["CRAWL4AI_DB_NAME"],
        user=env["CRAWL4AI_DB_USER"],
        password=env["CRAWL4AI_DB_PASSWORD"],
    )


def get_database_connection():
    config = get_database_config()
    connection = psycopg2.connect(
        host=config.host,
        port=config.port,
        database=config.database,
        user=config.user,
        password=config.password,
    )
    with connection.cursor() as cursor:
        cursor.execute("SET TIME ZONE 'America/New_York'")
    connection.commit()
    return connection
