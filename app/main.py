# main.py

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware  # Import CORSMiddleware
from redis import Redis
from rq import Queue
import os
import time
from worker import run_crawler
import json
import uuid  # For generating unique job IDs
from typing import List  # Import List for type hinting

app = FastAPI()

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Redis connection
redis_conn = Redis(host="redis", port=6379, decode_responses=True)
queue = Queue(connection=redis_conn)

@app.get("/")
async def root():
    """
    Root endpoint to verify the API is running.
    """
    return {"message": "Hello, world!"}

# health endpoint
# health endpoint
@app.get("/health")
async def health():
    """
    Health check endpoint to verify the service is running and Redis is accessible.
    """
    try:
        redis_conn.ping()
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


# POST endpoint to submit a new crawl job
@app.post("/crawl")
async def crawl(url: str, max_pages: int = Query(10, ge=1)):
    """
    Submits a new crawl job.

    Args:
        url (str): The URL to start crawling from.
        max_pages (int, optional): Maximum number of pages to crawl. Must be at least 1. Defaults to 10.

    Returns:
        dict: Contains the job ID and initial status.
    """
    job_id = str(uuid.uuid4())  # Generate a unique job ID using UUID4
    # Enqueue the job with max_pages as input
    queue.enqueue(run_crawler, job_id, url, max_pages)
    return {"job_id": job_id, "status": "queued"}

# GET endpoint to check the status of the crawl job
@app.get("/status/{job_id}")
async def get_status(job_id: str):
    """
    Retrieves the status of a specific crawl job.

    Args:
        job_id (str): The unique identifier of the crawl job.

    Returns:
        dict: Contains job status, links found, pages crawled, current URL, crawled URLs, crawling URLs, and errors.
    """
    job_key = f"job:{job_id}"
    if not redis_conn.exists(job_key):
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Fetch basic status information
    status = redis_conn.hget(job_key, "status")
    links_found = redis_conn.hget(job_key, "links_found")
    pages_crawled = redis_conn.hget(job_key, "pages_crawled")
    current_url = redis_conn.hget(job_key, "current_url")
    start_time = redis_conn.hget(job_key, "start_time")
    end_time = redis_conn.hget(job_key, "end_time")
    errors = redis_conn.hget(job_key, "errors")
    
    # Fetch crawled and crawling URLs
    crawled_urls = redis_conn.lrange(f"{job_key}:crawled_urls", 0, -1)
    crawling_urls = redis_conn.lrange(f"{job_key}:crawling_urls", 0, -1)
    
    return {
        "job_id": job_id,
        "status": status,
        "links_found": int(links_found) if links_found else 0,
        "pages_crawled": int(pages_crawled) if pages_crawled else 0,
        "current_url": current_url if current_url else "N/A",
        "crawled_urls": crawled_urls,
        "crawling_urls": crawling_urls,
        "start_time": int(start_time) if start_time else None,
        "end_time": int(end_time) if end_time else None,
        "errors": json.loads(errors) if errors else []
    }

# POST endpoint to retrieve filtered JSON based on a list of URLs
@app.post("/filtered-output/{job_id}")
async def get_filtered_output(job_id: str, payload: dict):
    """
    Retrieves a filtered JSON containing only the specified URLs' data from the crawl results.

    Args:
        job_id (str): The unique identifier of the crawl job.
        payload (dict): Contains a list of URLs to filter. Expected format:
                        {
                            "urls": ["https://example.com/page1", "https://example.com/page2"]
                        }

    Returns:
        JSONResponse: Filtered JSON data containing only the specified URLs.
    """
    job_key = f"job:{job_id}"
    output_file = f"app/outputs/{job_id}.json"
    
    if not os.path.exists(output_file):
        raise HTTPException(status_code=404, detail="Output file not found")
    
    # Extract URLs from the request payload
    urls = payload.get("urls", [])
    if not isinstance(urls, list):
        raise HTTPException(status_code=400, detail="The 'urls' field must be a list of URLs.")
    
    # Load the entire crawl result
    with open(output_file, 'r', encoding='utf-8') as f:
        crawl_data = json.load(f)
    
    # Create a dictionary for quick lookup
    crawl_data_dict = {item['url']: item for item in crawl_data}
    
    # Prepare filtered data
    filtered_data = []
    missing_urls = []
    for url in urls:
        if url in crawl_data_dict:
            filtered_data.append(crawl_data_dict[url])
        else:
            missing_urls.append(url)
    
    return JSONResponse(content={
        "job_id": job_id,
        "filtered_data": filtered_data,
        "missing_urls": missing_urls
    })

# GET endpoint to retrieve the output.json as a downloadable file
@app.get("/get-output/{job_id}")
def get_output(job_id: str):
    """
    Allows downloading the crawl results as a JSON file.

    Args:
        job_id (str): The unique identifier of the crawl job.

    Returns:
        FileResponse: The JSON file containing crawl results.
    """
    output_file = os.path.join("app", "outputs", f"{job_id}.json")
    if not os.path.exists(output_file):
        raise HTTPException(status_code=404, detail="Output file not found")
    return FileResponse(output_file, media_type='application/json', filename=f"{job_id}.json")


@app.get("/get-meta-output/{job_id}")
def get_output(job_id: str):
    """
    Allows downloading the crawl results as a JSON file.

    Args:
        job_id (str): The unique identifier of the crawl job.

    Returns:
        FileResponse: The JSON file containing crawl results.
    """
    output_file = os.path.join("app", "outputs", f"{job_id}_meta.json")
    if not os.path.exists(output_file):
        raise HTTPException(status_code=404, detail="Output file not found")
    return FileResponse(output_file, media_type='application/json', filename=f"{job_id}_meta.json")
