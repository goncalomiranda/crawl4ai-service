"""Apply pending yoyo migrations using the CRAWL4AI_DB_* environment variables."""
import sys
from pathlib import Path
from urllib.parse import quote

from yoyo import get_backend, read_migrations

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from database_config import get_database_config  # noqa: E402


def database_uri() -> str:
    c = get_database_config()
    return (
        f"postgresql://{quote(c.user, safe='')}:{quote(c.password, safe='')}"
        f"@{c.host}:{c.port}/{quote(c.database, safe='')}"
    )


def main() -> None:
    backend = get_backend(database_uri())
    migrations = read_migrations(str(ROOT / "migrations"))
    with backend.lock():
        pending = backend.to_apply(migrations)
        print(f"Applying {len(pending)} migration(s)")
        backend.apply_migrations(pending)


if __name__ == "__main__":
    main()
