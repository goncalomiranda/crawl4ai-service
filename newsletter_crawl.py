import asyncio
import json
import logging
import sys
from pathlib import Path

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer

from database_config import get_database_connection


LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "newsletter_crawl.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

if len(sys.argv) > 1:
    urls = json.loads(sys.argv[1])
else:
    urls = ["https://example.com"]

job_id = sys.argv[2] if len(sys.argv) > 2 else None

if job_id:
    logger.info("Job ID: %s", job_id)

conn = get_database_connection()
cur = conn.cursor()


async def main():
    try:
        if job_id:
            cur.execute(
                "UPDATE core.crawl_jobs SET status='RUNNING', started_at=NOW() WHERE id=%s",
                (job_id,),
            )
            conn.commit()
            logger.info("Job %s status: RUNNING", job_id)

        keyword_scorer = KeywordRelevanceScorer(
            keywords=["newsletter", "blog", "article", "post", "news", "update", "content"],
            weight=0.8,
        )

        deep_crawl_strategy = BestFirstCrawlingStrategy(
            max_depth=2,
            include_external=False,
            url_scorer=keyword_scorer,
            max_pages=20,
        )

        crawl_config = CrawlerRunConfig(
            deep_crawl_strategy=deep_crawl_strategy,
            stream=False,
            verbose=True,
        )

        async with AsyncWebCrawler() as crawler:
            for url in urls:
                try:
                    logger.info("Starting deep crawl from: %s", url)
                    results = await crawler.arun(url=url, config=crawl_config)
                    logger.info("Crawled %s pages in total", len(results))

                    for idx, result in enumerate(results, 1):
                        try:
                            title = (
                                result.metadata.get("title", "")
                                if result.metadata
                                else ""
                            )
                            content = result.markdown or ""
                            depth = result.metadata.get("depth", 0)
                            score = result.metadata.get("score", 0)

                            logger.info(
                                "[%s/%s] URL: %s", idx, len(results), result.url
                            )
                            logger.info(
                                "Depth: %s, Score: %.2f, Title: %s",
                                depth,
                                score,
                                title,
                            )

                            cur.execute(
                                """
                                INSERT INTO crawled_content (url, title, content)
                                VALUES (%s, %s, %s)
                                ON CONFLICT (url) DO UPDATE
                                SET title = EXCLUDED.title,
                                    content = EXCLUDED.content,
                                    created_at = CURRENT_TIMESTAMP
                                RETURNING id;
                                """,
                                (result.url, title, content),
                            )

                            row_id = cur.fetchone()[0]
                            conn.commit()

                            logger.info("Saved to DB: %s (ID: %s)", result.url, row_id)

                        except Exception as e:
                            logger.error("Error saving %s: %s", result.url, e)
                            conn.rollback()

                except Exception as e:
                    logger.error("Error crawling %s: %s", url, e)
                    conn.rollback()

        if job_id:
            cur.execute(
                "UPDATE core.crawl_jobs SET status='DONE', finished_at=NOW() WHERE id=%s",
                (job_id,),
            )
            conn.commit()
            logger.info("Job %s status: DONE", job_id)

    except Exception as e:
        logger.error("Job failed: %s", e)
        if job_id:
            cur.execute(
                "UPDATE core.crawl_jobs SET status='FAILED', error=%s, finished_at=NOW() WHERE id=%s",
                (str(e), job_id),
            )
            conn.commit()
            logger.info("Job %s status: FAILED", job_id)
        raise


asyncio.run(main())

cur.close()
conn.close()
