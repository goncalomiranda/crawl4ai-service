"""Reject destructive statements in forward migrations (Milestone 1 is additive only)."""
import re
import sys
from pathlib import Path

DESTRUCTIVE = re.compile(
    r"\b(DROP\s+(TABLE|SCHEMA|COLUMN|DATABASE)|TRUNCATE|DELETE\s+FROM|"
    r"ALTER\s+TABLE\s+\S+\s+(DROP|RENAME)|ALTER\s+COLUMN\s+\S+\s+TYPE)\b",
    re.IGNORECASE,
)


def strip_comments(sql: str) -> str:
    return re.sub(r"--[^\n]*", "", sql)


def find_violations(directory: Path) -> list[str]:
    problems = []
    for path in sorted(directory.glob("*")):
        if path.suffix not in {".sql", ".py"} or ".rollback." in path.name:
            continue
        match = DESTRUCTIVE.search(strip_comments(path.read_text()))
        if match:
            problems.append(f"{path.name}: {match.group(0)}")
    return problems


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent / "migrations"
    found = find_violations(root)
    for line in found:
        print(f"Destructive statement not allowed: {line}", file=sys.stderr)
    sys.exit(1 if found else 0)
