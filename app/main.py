from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from redis import Redis
from rq import Queue
import os
import time
from app.worker import run_crawler

app = FastAPI()

# Redis connection
redis_conn = Redis(host="redis", port=6379)
queue = Queue(connection=redis_conn)

@app.get("/")
async def root():
    return {"message": "Hello, world!"}

# POST endpoint to submit a new crawl job
@app.post("/crawl")
async def crawl(url: str, max_pages: int = Query(10, ge=1)):
    job_id = str(int(time.time()))  # Generate job ID
    redis_conn.hset(f"job:{job_id}", "status", "queued")
    
    # Enqueue the job with max_pages as input
    queue.enqueue(run_crawler, job_id, url, max_pages)
    
    return {"job_id": job_id, "status": "queued"}



# GET endpoint to check the status of the crawl job
@app.get("/status/{job_id}")
async def get_status(job_id: str):
    status = redis_conn.hget(f"job:{job_id}", "status")
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    progress = redis_conn.hget(f"job:{job_id}", "progress")
    crawled_pages = redis_conn.hget(f"job:{job_id}", "crawled_pages")
    
    return {
        "job_id": job_id,
        "status": status.decode("utf-8"),
        "progress": progress.decode("utf-8") if progress else "N/A",
        "crawled_pages": crawled_pages.decode("utf-8") if crawled_pages else "N/A"
    }

# GET endpoint to retrieve the output.json as a downloadable file
@app.get("/get-output/{job_id}")
def get_output(job_id: str):
    output_file = f"app/outputs/{job_id}.json"
    
    if not os.path.exists(output_file):
        raise HTTPException(status_code=404, detail="Output file not found")

    return FileResponse(output_file, media_type='application/json', filename=f"{job_id}.json")

