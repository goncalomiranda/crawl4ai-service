from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import json
import logging
import subprocess
import sys
from pathlib import Path

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from fastapi import FastAPI
from pydantic import BaseModel

from database_config import get_database_config, get_database_connection


BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "crawler_api.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    get_database_config()
    yield


app = FastAPI(lifespan=lifespan)


def get_db_connection():
    return get_database_connection()


class CrawlRequest(BaseModel):
    urls: list[str]


class OpenClawRequest(BaseModel):
    url: str


@app.post("/crawl")
def run_crawl(request: CrawlRequest):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO core.crawl_jobs (status) VALUES ('STARTING') RETURNING id"
    )
    job_id = str(cur.fetchone()[0])
    conn.commit()
    cur.close()
    conn.close()

    logger.info("Created job: %s", job_id)

    urls_json = json.dumps(request.urls)
    subprocess.Popen(
        [sys.executable, str(BASE_DIR / "newsletter_crawl.py"), urls_json, job_id],
        cwd=BASE_DIR,
    )

    return {
        "status": "started",
        "job_id": job_id,
        "urls": request.urls,
    }


@app.get("/job/{job_id}")
def get_job_status(job_id: str):
    """Get the status of a crawl job."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, status, error, created_at, started_at, finished_at
            FROM core.crawl_jobs
            WHERE id = %s
            """,
            (job_id,),
        )
        row = cur.fetchone()
        cur.close()
        conn.close()

        if not row:
            return {"error": "Job not found"}

        return {
            "id": str(row[0]),
            "status": row[1],
            "error": row[2],
            "created_at": row[3].isoformat() if row[3] else None,
            "started_at": row[4].isoformat() if row[4] else None,
            "finished_at": row[5].isoformat() if row[5] else None,
        }
    except Exception as e:
        logger.error("Error fetching job status: %s", e)
        return {"error": str(e)}


@app.post("/openclaw-fetch")
async def openclaw_fetch(request: OpenClawRequest):
    """Fetch one URL and return Markdown for OpenClaw."""
    try:
        target_url = request.url

        if not target_url:
            return {"error": "No URL provided", "markdown": ""}

        logger.info("OpenClaw is requesting: %s", target_url)

        browser_config = BrowserConfig(headless=True, verbose=False)
        run_config = CrawlerRunConfig(cache_mode="BYPASS")

        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=target_url, config=run_config)

            return {
                "markdown": result.markdown or "",
                "metadata": {
                    "title": result.metadata.get("title", "") if result.metadata else "",
                    "source": target_url,
                },
            }

    except Exception as e:
        logger.error("OpenClaw fetch failed: %s", e)
        return {"error": str(e), "markdown": "Failed to retrieve content."}
