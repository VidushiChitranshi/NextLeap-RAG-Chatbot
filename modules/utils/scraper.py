import os
import time
import logging
from typing import Optional
from playwright.sync_api import sync_playwright

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CourseScraper:
    """Fetches course page content using Playwright for dynamic rendering."""

    def __init__(self, base_url: str, wait_timeout: int = 5000):
        self.base_url = base_url
        self.wait_timeout = wait_timeout
        # Ensure HOME is set for Playwright
        if 'HOME' not in os.environ:
            os.environ['HOME'] = os.path.expanduser('~')

    def fetch_page(self, retries: int = 3) -> Optional[str]:
        """Fetches fully rendered HTML content."""
        for attempt in range(retries):
            try:
                with sync_playwright() as p:
                    logger.info(f"Launching browser to fetch: {self.base_url} (Attempt {attempt+1})")
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()
                    
                    # Navigate and wait for content
                    try:
                        page.goto(self.base_url, wait_until="load", timeout=60000)
                    except Exception as e:
                        logger.warning(f"Initial load timed out or failed: {e}. Continuing anyway.")
                    
                    page.wait_for_timeout(self.wait_timeout)
                    
                    # Scroll to ensure lazy content is loaded
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(3000) # Increased wait for lazy content
                    
                    html = page.content()
                    browser.close()
                    
                    if html and len(html) > 1000:
                        return html
                    
            except Exception as e:
                logger.error(f"Attempt {attempt+1} failed: {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    
        return None

if __name__ == "__main__":
    # Test run
    scraper = CourseScraper("https://nextleap.app/course/product-management-course")
    html = scraper.fetch_page()
    if html:
        print(f"Successfully fetched {len(html)} characters.")
