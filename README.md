# OctoBotCrawler

🚀 **OctoBotCrawler** - A Python alternative to the [**GPT Crawler by Builder.io**](https://github.com/BuilderIO/gpt-crawler)! 🔍🕸️ Built with FastAPI, Redis, and RQ workers, it's designed for scalable web crawling with concurrent page processing! 🐍✨


## Project Structure

```bash
.
├── Dockerfile                 # Docker configuration for FastAPI and worker
├── docker-compose.yml          # Docker Compose configuration for all services
├── app/
│   ├── main.py                # FastAPI application entry point
│   ├── worker.py              # RQ worker for processing crawl jobs
│   ├── gptcrawlercore.py       # Core logic for crawling web pages using Playwright
│   ├── outputs/               # Directory for storing crawl output JSON files
│   ├── requirements.txt        # Python dependencies
└── README.md                  # Project documentation
```

## Prerequisites

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Setting Up the Project

### Step 1: Clone the Repository

```bash
git clone https://github.com/badboysm890/octobotcrawler.git
cd octobotcrawler
```

### Step 2: Build and Run the Docker Containers

Use Docker Compose to build and run the FastAPI, Redis, and worker services.

```bash
docker-compose up --build
```

This command will:
- Build the FastAPI app container.
- Build the RQ worker container.
- Start the Redis container.

FastAPI will be running on `http://localhost:8000`.

## Interacting with the API

### Start a Crawl Job

To start a new crawl job, make a POST request to the `/crawl` endpoint with the URL you want to crawl and the number of pages (`max_pages`) you want to scrape.

#### Example Request:

```bash
curl -X POST "http://localhost:8000/crawl?url=https://example.com&max_pages=10"
```

#### Example Response:

```json
{
  "job_id": "172789XXXX",
  "status": "queued"
}
```

### Check Job Status and Retrieve Results

Once the job is complete, you can retrieve the results using the `job_id` returned in the `/crawl` request.

To get the output, use the `/get-output/{job_id}` endpoint.

#### Example Request:

```bash
curl http://localhost:8000/get-output/172789XXXX
```

If the job is complete, you will receive the `output.json` file with the crawled data.

### Error Handling

If the job hasn't finished or if there's an issue retrieving the output, you'll get an appropriate error message, such as:

```json
{
  "detail": "Output file not found"
}
```

## Services

### FastAPI

- **Port**: `8000`
- **Purpose**: Serves as the API interface for the crawler system. It accepts crawl requests, returns job status, and provides access to the crawl results.

### Redis

- **Port**: `6379`
- **Purpose**: Acts as the message broker and queue system for the worker processes. Jobs are enqueued in Redis and processed by RQ workers.

### Worker

- **Purpose**: Processes the crawl jobs. It pulls jobs from the Redis queue and executes them using the core crawling logic in `gptcrawlercore.py`.

## File Structure

- **main.py**: The FastAPI application that handles crawl requests and retrieves results.
- **worker.py**: The RQ worker responsible for executing crawl jobs asynchronously.
- **gptcrawlercore.py**: Contains the core logic for web crawling using Playwright.
- **outputs/**: Directory where the crawled data (output files) is stored as JSON.

## Customizing the Crawler

You can modify the number of pages to be crawled by adjusting the `max_pages` parameter in the request. The concurrency of the crawler can be modified by editing the `GPTCrawlerCore` class in `gptcrawlercore.py`.

## Troubleshooting

### Common Issues

- **Redis Connection Error**: If you see `redis.exceptions.ConnectionError`, ensure that your FastAPI app is connecting to Redis using the `redis` service name in Docker and not `localhost`.
- **Permission Issues**: If you encounter permission issues when writing files to the `outputs` directory, ensure the directory has appropriate write permissions (e.g., `chmod -R 777 app/outputs`).

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
