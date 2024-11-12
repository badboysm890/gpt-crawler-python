import asyncio
import json
import re
import os
from typing import List, Set
from urllib.parse import urlparse, urljoin
from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlunparse


class GPTCrawlerCore:
    def __init__(self, start_url: str, max_pages: int = 100, concurrency: int = 5):
        self.start_url = start_url.rstrip('/')  # Ensure no trailing slash
        parsed_start = urlparse(start_url)
        print(max_pages,"max_pages")
        self.domain = parsed_start.netloc.lower()
        self.allowed_domains = {self.domain, "www." + self.domain}
        self.max_pages = max_pages
        self.concurrency = concurrency  # Number of concurrent tasks
        self.visited: Set[str] = set()
        self.to_visit: List[str] = [self.start_url]
        self.results: List[dict] = []
        self.retry_limit = 3  # Number of retries for failed pages
        self.retry_count = {}  # Track retries per URL
        self.sem = asyncio.Semaphore(self.concurrency)  # Semaphore for concurrency control
        self.page_pool = []
        self.page_queue = asyncio.Queue()
    async def init_page_pool(self, context):
        print(self.concurrency)
        for _ in range(self.concurrency):
            page = await context.new_page()
            await self.page_queue.put(page)
            self.page_pool.append(page)
            print(self.page_pool)
    async def get_page_html(self, page: Page, selector: str = "body") -> str:
        try:
            element = await page.query_selector(selector)
            if element:
                html = await element.inner_html()
                return html.strip() if html else ""
            return ""
        except Exception as e:
            print(f"[ERROR] Failed to get HTML content with selector '{selector}': {e}")
            return ""

    def extract_text_from_html(self, html_content: str) -> str:
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            for script_or_style in soup(['script', 'style', 'noscript']):
                script_or_style.decompose()
            for tag in ['navbar', 'footer', 'header','ads' ,'nav']:
             for unwanted in soup.find_all(tag):
                unwanted.decompose()
            for unwanted in soup.find_all(class_=['navbar', 'footer', 'header', 'ads','nav']):
                unwanted.decompose()
            for unwanted in soup.find_all(['aside', 'div'], {'class': 'ad'}):
                unwanted.decompose()
            text = soup.get_text(separator=' ', strip=True)
            return ' '.join(text.split())
        except Exception as e:
            print(f"[ERROR] Failed to extract text from HTML: {e}")
            return ""

    async def extract_links(self, page: Page) -> List[str]:
        try:
            links = await page.evaluate(
                """() => Array.from(document.querySelectorAll('a[href]'))
                           .map(a => a.href)
                           .filter(href => href)"""
            )
            print(f"[DEBUG] Extracted links: {links}")
            download_extensions = {
            '.pdf', '.zip', '.rar', '.tar', '.gz', '.7z',
            '.exe', '.msi', '.dmg', '.pkg', '.deb', '.rpm',
            '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.mp3', '.mp4', '.avi', '.mov', '.jpg', '.jpeg', '.png', '.gif'
        }
            download_patterns = re.compile(r'(download|archive|attachment|file|document)s?', re.IGNORECASE)
            normalized_links = []
            for link in links:
                parsed = urlparse(link)
                # Handle relative URLs by joining with the start URL
                if not parsed.netloc:
                    link = urljoin(self.start_url, link)

                parsed = urlparse(link)  # Re-parse to get the absolute URL
                link_domain = parsed.netloc.lower()

                if any(parsed.path.lower().endswith(ext) for ext in download_extensions):
                  print(f"[DEBUG] Skipping download link: {link}")
                  continue
                if download_patterns.search(parsed.path):
                  print(f"[DEBUG] Skipping download pattern link: {link}")
                  continue

                if link_domain not in self.allowed_domains:
                    continue  # Skip external links and undesired subdomains

                clean_link = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip('/')
                if clean_link and clean_link not in normalized_links:
                    normalized_links.append(clean_link)

            return list(set(normalized_links))
        except Exception as e:
            print(f"[ERROR] Failed to extract links: {e}")
            return []

    async def navigate_with_retry(self, page: Page, url: str) -> bool:
        retries = self.retry_count.get(url, 0)
        while retries < self.retry_limit:
            try:
                await page.goto(url, timeout=30000, wait_until="domcontentloaded")  # Use 'domcontentloaded' to avoid waiting for all resources
                await page.wait_for_load_state('domcontentloaded')
                await asyncio.sleep(1)
                return True
            except PlaywrightTimeoutError:
                retries += 1
                self.retry_count[url] = retries
                print(f"[ERROR] Timeout while navigating to {url} (Attempt {retries}/{self.retry_limit})")
            except Exception as e:
                retries += 1
                self.retry_count[url] = retries
                print(f"[ERROR] Failed to navigate to {url}: {e} (Attempt {retries}/{self.retry_limit})")
            # Adding a delay between retries to avoid hammering the server
            await asyncio.sleep(2)
        return False

    def normalize_url(self,url):
      parsed_url = urlparse(url)
      return urlunparse(parsed_url._replace(fragment=""))
    async def crawl_page(self, context, url: str):
        async with self.sem:
            page = await self.page_queue.get()
            url = self.normalize_url(url)
            if url in self.visited:
                self.page_queue.put_nowait(page)  # Return the page to the pool
                return
            print(f"[INFO] Crawling ({len(self.visited)}/{self.max_pages}) - {url}")
            success = await self.navigate_with_retry(page, url)
            if not success:
                self.page_queue.put_nowait(page)
                return
            self.visited.add(url)

            try:
                title = await page.title()
                html_content = await self.get_page_html(page, "body")
                text_content = self.extract_text_from_html(html_content)

                self.results.append({
                    "title": title,
                    "url": url,
                    "text": text_content
                })

                print(f"[INFO] Successfully crawled: {url}")
                links = await self.extract_links(page)
                for link in links:
                    normalized_link = self.normalize_url(link)
                    if normalized_link not in self.visited and normalized_link not in self.to_visit and len(self.visited) < self.max_pages:
                         self.to_visit.append(normalized_link)
                         print(f"[INFO] Enqueued: {normalized_link}")
                self.page_queue.put_nowait(page)
            except Exception as e:
                print(f"[ERROR] Error processing {url}: {e}")
                self.page_queue.put_nowait(page)
            finally:
                self.page_queue.put_nowait(page)
    async def crawl(self):
        async with async_playwright() as p:
            print("[INFO] Launching browser...")
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/115.0.0.0 Safari/537.36"
                )
            )
            await context.route("**/*.{png,jpg,jpeg,gif,svg,css,font,woff,woff2}", lambda route, _: route.abort())
           # Initialize the page pool
            await self.init_page_pool(context)
            while self.to_visit and len(self.visited) < self.max_pages:
                tasks = []

                print(f"[DEBUG] To visit queue length: {len(self.to_visit)}")
                while self.to_visit and len(tasks) < self.concurrency:
                    url = self.to_visit.pop(0)
                    if url not in self.visited:
                        tasks.append(self.crawl_page(context, url))

                if tasks:
                    await asyncio.gather(*tasks)
                    tasks = []



            for page in self.page_pool:
                await page.close()
            await context.close()  # Close the context
            await browser.close()
            print("[INFO] Browser closed.")
    def write_output(self, output_file: str):
        try:
            # Get the absolute path to ensure the directory exists
            output_dir = os.path.dirname(output_file)
            os.makedirs(output_dir, exist_ok=True)  # Ensure the output directory exists
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            print(f"[INFO] Output written to {output_file}")
        except Exception as e:
            print(f"[ERROR] Failed to write output file: {e}")
