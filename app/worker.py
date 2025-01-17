# worker.py

import asyncio
from redis import Redis
import os
from gptcrawlercore import GPTCrawlerCore
import time

# Initialize Redis connection
redis_conn = Redis(host="redis", port=6379, decode_responses=True)

def run_crawler(job_id: str, start_url: str, max_pages: int = 10):
    """
    Runs the web crawler and updates the job status in Redis.

    Args:
        job_id (str): Unique identifier for the crawl job.
        start_url (str): The URL to start crawling from.
        max_pages (int, optional): Maximum number of pages to crawl. Defaults to 10.
    """
    # Set initial job status and metadata
    redis_conn.hset(f"job:{job_id}", mapping={
        "status": "in_progress",
        "links_found": 0,
        "pages_crawled": 0,
        "current_url": "",
        "start_time": int(time.time()),
        "end_time": "",
        "errors": "[]"
    })
    
    # Initialize lists for crawled and crawling URLs
    redis_conn.delete(f"job:{job_id}:crawled_urls")
    redis_conn.delete(f"job:{job_id}:crawling_urls")
    
    # Create the crawler with job_id and redis_conn
    crawler = GPTCrawlerCore(
        start_url=start_url,
        max_pages=max_pages,
        concurrency=5,
        job_id=job_id,
        redis_conn=redis_conn
    )

    # Run the crawler
    asyncio.run(crawler.crawl())

    # Define output file path using unique job_id
    output_file = os.path.join("app", "outputs", f"{job_id}.json")
    output_meta_file = os.path.join("app", "outputs", f"{job_id}_meta.json")

    # Write the crawling results to output file
    crawler.write_output(output_file=output_file, output_file_meta=output_meta_file)

    # Update job status to completed and set end_time
    redis_conn.hset(f"job:{job_id}", mapping={
        "status": "completed",
        "end_time": int(time.time()),
        "current_url": ""
    })

    print(f"[INFO] Job {job_id} completed")
