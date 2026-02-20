import json
import os
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional

from modules.utils.scraper import CourseScraper
from modules.scraper.parser import CourseParser
from modules.scraper.cleaner import DataCleaner
from phase_1.discovery import CourseDiscovery

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ScraperValidator:
    """Hardened validation layer to prevent malformed data."""
    
    @staticmethod
    def validate(data: dict) -> bool:
        """Checks for critical nulls and type mismatches."""
        if not data.get("course") or not data.get("pricing"):
            logger.error("CRITICAL VALIDATION FAILURE: Missing core sections.")
            return False

        critical_fields = [
            ("course.title", data["course"].get("title")),
            ("pricing.amount", data["pricing"].get("amount")),
        ]
        
        for name, value in critical_fields:
            if value is None:
                logger.error(f"CRITICAL VALIDATION FAILURE: {name} is null.")
                return False
                
        # Pricing sanity check
        amount = data["pricing"].get("amount")
        if amount and (amount < 5000 or amount > 200000): # Adjusted range for broader courses
            logger.warning(f"SANITY CHECK WARNING: Pricing amount ({amount}) is out of expected range.")
            
        return True

def scrape_single_course(url: str, cleaner: DataCleaner) -> Optional[Dict]:
    """Scrapes a single course URL and returns the data dict."""
    logger.info(f"Starting scrape for: {url}")
    scraper = CourseScraper(url)
    
    # 1. Fetch
    html = scraper.fetch_page()
    if not html:
        logger.error(f"Failed to fetch content for {url}")
        return None

    # 2. Parse (Raw)
    parser = CourseParser(html)
    raw_core = parser.parse_core_info()
    raw_cohort = parser.parse_cohort()
    raw_pricing = parser.parse_pricing()
    raw_faculty = parser.parse_faculty()

    # 3. Assemble and Normalize
    data = {
        "course": {
            "title": cleaner.clean_text(raw_core.get("title")),
            "url": url, # Added URL to course object
            "duration_weeks": cleaner.extract_numeric(raw_core.get("duration_weeks_raw")),
            "fellowship_months": cleaner.extract_numeric(raw_core.get("fellowship_months_raw")),
            "live_class_hours": cleaner.extract_numeric(raw_core.get("live_hours_raw")),
            "placement_support_years": cleaner.extract_numeric(raw_core.get("placement_support_raw")),
            "certification_awarded": raw_core.get("certification_awarded", "No")
        },
        "cohort": {
            "id": cleaner.extract_numeric(raw_cohort.get("cohort_raw")),
            "start_date": cleaner.normalize_date(raw_cohort.get("date_raw")),
            "status": "CLOSED" # Default
        },
        "pricing": cleaner.normalize_price(raw_pricing.get("price_raw")),
        "faculty": raw_faculty,
        "metadata": {
            "scraped_at": datetime.now().isoformat(),
            "source_url": url
        }
    }

    # Dynamic status derivation
    if data["cohort"]["start_date"]:
        try:
            start_dt = datetime.fromisoformat(data["cohort"]["start_date"])
            if start_dt > datetime.now():
                data["cohort"]["status"] = "OPEN"
            else:
                data["cohort"]["status"] = "CLOSED"
        except ValueError:
            pass # Keep default if date parsing fails

    # 4. Validate
    if not ScraperValidator.validate(data):
        logger.error(f"Data validation failed for {url}. Skipping.")
        return None
        
    logger.info(f"Successfully scraped: {data['course']['title']}")
    return data

def main():
    logger.info("Starting Scalable Scraper Orchestrator...")
    cleaner = DataCleaner()
    
    # 1. Discovery
    discovery = CourseDiscovery()
    course_urls = discovery.get_course_urls()
    
    if not course_urls:
        logger.warning("No course URLs found. Exiting.")
        return

    all_courses_data = []

    # 2. Orchestration Loop
    for url in course_urls:
        try:
            course_data = scrape_single_course(url, cleaner)
            if course_data:
                all_courses_data.append(course_data)
            
            # Rate Limiting
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"Unexpected error scraping {url}: {e}")
            continue

    # 3. Aggregation
    final_output = {
        "metadata": {
            "scraped_at": datetime.now().isoformat(),
            "total_courses_found": len(course_urls),
            "total_courses_scraped": len(all_courses_data)
        },
        "courses": all_courses_data
    }

    # 4. Save Output
    output_path = "data/raw/all_courses.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Refactor complete. Scraped {len(all_courses_data)} courses. Data saved to {output_path}")

if __name__ == "__main__":
    main()
