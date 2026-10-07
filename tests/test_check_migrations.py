import tempfile
import unittest
from pathlib import Path

from scripts.check_migrations import find_violations

ROOT = Path(__file__).resolve().parent.parent


class CheckMigrationsTests(unittest.TestCase):
    def test_repository_migrations_are_additive(self):
        self.assertEqual(find_violations(ROOT / "migrations"), [])

    def test_destructive_statements_are_rejected(self):
        for sql in ["DROP TABLE crawled_content;", "truncate crawled_content;",
                    "ALTER TABLE crawled_content DROP COLUMN title;"]:
            with tempfile.TemporaryDirectory() as d:
                (Path(d) / "0002_bad.sql").write_text(sql)
                self.assertTrue(find_violations(Path(d)), sql)

    def test_comments_and_rollbacks_are_ignored(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "0002_ok.sql").write_text("-- DROP TABLE x\nALTER TABLE t ADD COLUMN c TEXT;")
            (Path(d) / "0002_ok.rollback.sql").write_text("DROP TABLE x;")
            self.assertEqual(find_violations(Path(d)), [])


if __name__ == "__main__":
    unittest.main()
