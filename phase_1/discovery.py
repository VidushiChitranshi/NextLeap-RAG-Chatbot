import logging
import re
from typing import List, Set
from modules.utils.scraper import CourseScraper
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class CourseDiscovery:
    """Handles discovery of course URLs from the main landing page."""
    
    def __init__(self, homepage_url: str = "https://nextleap.app/"):
        self.homepage_url = homepage_url
        self.scraper = CourseScraper(homepage_url)

    def get_course_urls(self) -> List[str]:
        """
        Fetches the homepage and returns a list of unique course URLs.
        Filters for URLs containing '/course/' and excludes non-course paths.
        """
        logger.info(f"Discovering courses from {self.homepage_url}...")
        html = self.scraper.fetch_page()
        
        if not html:
            logger.error("Failed to fetch homepage for discovery.")
            return []

        soup = BeautifulSoup(html, "html.parser")
        links = soup.find_all("a", href=True)
        
        course_urls: Set[str] = set()
        
        # Known exclusion patterns (just in case, though /course/ is specific)
        exclude_patterns = [
            "/blog/", "/success-stories", "/events", "/about", "/careers", 
            "/privacy", "/terms", "/contact-us", "/for-companies", 
            "/interview-preparation"
        ]

        for link in links:
            href = link['href'].strip()
            
            # Normalize relative URLs
            if href.startswith("/"):
                href = f"https://nextleap.app{href}"
            
            # Filter logic: Must have /course/ and not be in exclusion list
            if "/course/" in href and not any(ex in href for ex in exclude_patterns):
                # Clean URL (remove query params for uniqueness)
                if "?" in href:
                    href = href.split("?")[0]
                
                # Check for "showcase" or other non-detail pages that might slip through?
                # The inspection showed /data-analyst-course/showcase/... but that doesn't have /course/ in it.
                # Inspection showed: https://nextleap.app/course/product-management-course
                # So filtering by "/course/" seems robust.
                
                course_urls.add(href)

        sorted_urls = sorted(list(course_urls))
        logger.info(f"Discovered {len(sorted_urls)} unique course URLs.")
        return sorted_urls

if __name__ == "__main__":
    # Test run
    discovery = CourseDiscovery()
    urls = discovery.get_course_urls()
    for u in urls:
        print(u)
