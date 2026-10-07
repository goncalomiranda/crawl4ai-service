import json
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from crawler_api import BASE_DIR, CrawlRequest, run_crawl


class CrawlLaunchTests(unittest.TestCase):
    def test_launch_passes_urls_as_one_argument_and_returns_job_id(self):
        urls = ["https://example.com/path with spaces/?q=$(touch /tmp/nope);&x=echo"]
        job_id = "job-42"
        connection = Mock()
        connection.cursor.return_value.fetchone.return_value = (job_id,)

        with (
            patch("crawler_api.get_db_connection", return_value=connection),
            patch("crawler_api.subprocess.Popen") as popen,
        ):
            response = run_crawl(CrawlRequest(urls=urls))

        popen.assert_called_once_with(
            [
                sys.executable,
                str(Path(BASE_DIR) / "newsletter_crawl.py"),
                json.dumps(urls),
                job_id,
            ],
            cwd=BASE_DIR,
        )
        self.assertEqual(response["job_id"], job_id)
        self.assertEqual(response["urls"], urls)
