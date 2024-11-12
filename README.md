```markdown
# OctoBotCrawler

🚀 **OctoBotCrawler** - A Python alternative to the [**GPT Crawler by Builder.io**](https://github.com/BuilderIO/gpt-crawler)! 🔍🕸️ Built with FastAPI, Redis, and RQ workers, it's designed for scalable web crawling with concurrent page processing! 🐍✨

## Features
- **Unique Job Identifiers:** Utilizes UUIDs to ensure each crawl job is uniquely identifiable, preventing output file overwrites.
- **Filtered Data Retrieval:** Provides an endpoint to retrieve a subset of crawled data based on a list of specific URLs.
- **Concurrent Crawling:** Supports concurrent crawling of multiple pages for faster data collection.
- **JSON Output:** Outputs the crawled data in JSON format.
- **Headless Browser Automation:** Uses Playwright for efficient and reliable headless browser operations.

### Upload Data to OpenAI

Once the crawl generates a file called `output.json` in the `app/outputs/` directory, you can upload it to OpenAI to create your **custom GPT** or **custom assistant**.

#### **Create a Custom GPT** 🧑‍💻

Use this option for UI access to your generated knowledge that you can easily share with others.

1. Go to [ChatGPT](https://chat.openai.com/).
2. Click your name in the bottom left corner.
3. Choose **"My GPTs"** in the menu.
4. Choose **"Create a GPT"**.
5. Choose **"Configure"**.
6. Under **"Knowledge"**, choose **"Upload a file"** and upload the `output.json` file generated from the crawl.

![Gif showing how to upload a custom GPT](https://private-user-images.githubusercontent.com/844291/282630007-22f27fb5-6ca5-4748-9edd-6bcf00b408cf.gif?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3MzE0NDQ5MzksIm5iZiI6MTczMTQ0NDYzOSwicGF0aCI6Ii84NDQyOTEvMjgyNjMwMDA3LTIyZjI3ZmI1LTZjYTUtNDc0OC05ZWRkLTZiY2YwMGI0MDhjZi5naWY_WC1BbXotQWxnb3JpdGhtPUFXUzQtSE1BQy1TSEEyNTYmWC1BbXotQ3JlZGVudGlhbD1BS0lBVkNPRFlMU0E1M1BRSzRaQSUyRjIwMjQxMTEyJTJGdXMtZWFzdC0xJTJGczMlMkZhd3M0X3JlcXVlc3QmWC1BbXotRGF0ZT0yMDI0MTExMlQyMDUwMzlaJlgtQW16LUV4cGlyZXM9MzAwJlgtQW16LVNpZ25hdHVyZT1iZTgzZDdmZTZjNGY0Yzc2MGUxNjc5ZjM5MTdiYjBjMmExMGYxYjliNDg5YzJjMmI1YjE4ZDlhMzg0ODI4Njk1JlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCJ9.vf8QSW9hqs4XZtArmXTVtbJxlFphEZ-LHJwLczTANF8)

*Gif credit: [Builder.io](https://github.com/BuilderIO/gpt-crawler)*

#### **Create a Custom Assistant** 🤖

Use this option for API access to your generated knowledge, which you can integrate into your product.

1. Go to [OpenAI Assistants](https://platform.openai.com/assistants).
2. Click **"+ Create"**.
3. Choose **"Upload"** and upload the `output.json` file generated from the crawl.

This will allow you to create an assistant using the knowledge you generated during the crawl!

## Project Structure

```bash
.
├── Dockerfile                 # Docker configuration for FastAPI and worker
├── docker-compose.yml         # Docker Compose configuration for all services
├── app/
│   ├── main.py                # FastAPI application entry point
│   ├── worker.py              # RQ worker for processing crawl jobs
│   ├── gptcrawlercore.py      # Core logic for crawling web pages using Playwright
│   ├── outputs/               # Directory for storing crawl output JSON files
│   ├── requirements.txt       # Python dependencies
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
  "job_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "queued"
}
```

### Check Job Status and Retrieve Results

Once the job is complete, you can retrieve the results using the `job_id` returned in the `/crawl` request.

#### Get Job Status:

To get the status of a crawl job, use the `/status/{job_id}` endpoint.

##### Example Request:

```bash
curl "http://localhost:8000/status/3fa85f64-5717-4562-b3fc-2c963f66afa6"
```

##### Example Response:

```json
{
  "job_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "in_progress",
  "links_found": 50,
  "pages_crawled": 10,
  "current_url": "https://example.com/page10",
  "crawled_urls": [
    "https://example.com",
    "https://example.com/about",
    "... more URLs ..."
  ],
  "crawling_urls": [
    "https://example.com/contact"
  ],
  "start_time": 1700000000,
  "end_time": null,
  "errors": [
    {
      "url": "https://example.com/broken-link",
      "message": "Timeout while navigating to https://example.com/broken-link (Attempt 3/3)",
      "timestamp": 1700000100
    }
  ]
}
```

### Retrieve Filtered Crawl Data

Before downloading the entire JSON output, you can request a subset of the crawled data based on a list of specific URLs using the `/filtered-output/{job_id}` endpoint.

#### Example Request:

```bash
curl -X POST "http://localhost:8000/filtered-output/3fa85f64-5717-4562-b3fc-2c963f66afa6" \
-H "Content-Type: application/json" \
-d '{"urls": ["https://example.com/page1", "https://example.com/page2"]}'
```

#### Example Response:

```json
{
  "job_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "filtered_data": [
    {
      "title": "Page 1 Title",
      "url": "https://example.com/page1",
      "text": "Content of page 1..."
    },
    {
      "title": "Page 2 Title",
      "url": "https://example.com/page2",
      "text": "Content of page 2..."
    }
  ],
  "missing_urls": [
    "https://example.com/page3"
  ]
}
```

**Field Descriptions:**
- **`filtered_data`**: Contains data for URLs that were found and crawled.
- **`missing_urls`**: Lists URLs that were requested but not found in the crawl results.

### Download Full Crawl Results

You can download the entire crawl results using the `/get-output/{job_id}` endpoint.

#### Example Request:

```bash
curl -O "http://localhost:8000/get-output/3fa85f64-5717-4562-b3fc-2c963f66afa6"
```

If the job is complete, you will receive the `3fa85f64-5717-4562-b3fc-2c963f66afa6.json` file with the crawled data.

### Error Handling

If the job hasn't finished or if there's an issue retrieving the output, you'll receive an appropriate error message, such as:

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
- **requirements.txt**: Lists the Python dependencies required for the project.
- **Dockerfile**: Docker configuration for containerizing the FastAPI app and worker.
- **docker-compose.yml**: Docker Compose configuration for orchestrating the FastAPI app, Redis, and worker services.

## Customizing the Crawler

You can modify the number of pages to be crawled by adjusting the `max_pages` parameter in the request. The concurrency of the crawler can be modified by editing the `GPTCrawlerCore` class in `gptcrawlercore.py`.

## Troubleshooting

### Common Issues

- **Redis Connection Error**: If you see `redis.exceptions.ConnectionError`, ensure that your FastAPI app is connecting to Redis using the `redis` service name in Docker and not `localhost`.
- **Permission Issues**: If you encounter permission issues when writing files to the `outputs` directory, ensure the directory has appropriate write permissions (e.g., `chmod -R 777 app/outputs`).
- **Job ID Not Found**: Ensure that the `job_id` provided in the request matches an existing job. Use the `/status/{job_id}` endpoint to verify job existence.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
```