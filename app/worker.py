import asyncio
from redis import Redis
import os
from app.gptcrawlercore import GPTCrawlerCore

redis_conn = Redis(host="redis", port=6379)

def run_crawler(job_id: str, start_url: str, max_pages: int = 10):
    redis_conn.hset(f"job:{job_id}", "status", "in_progress")

    # Create the crawler
    crawler = GPTCrawlerCore(start_url=start_url, max_pages=max_pages, concurrency=5)

    # Run the crawler
    asyncio.run(crawler.crawl())

    # Ensure the output directory is correctly passed
    output_file = os.path.join("app", "outputs", f"{job_id}.json")
    crawler.write_output(output_file=output_file)

    redis_conn.hset(f"job:{job_id}", "status", "completed")
    print(f"[INFO] Job {job_id} completed")

