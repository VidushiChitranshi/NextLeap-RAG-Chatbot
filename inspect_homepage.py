from modules.scraper.scraper import CourseScraper
from bs4 import BeautifulSoup
import re

def inspect_home():
    url = "https://nextleap.app/"
    scraper = CourseScraper(url)
    print(f"Fetching {url}...")
    html = scraper.fetch_page()
    
    if not html:
        print("Failed to fetch HTML")
        return

    soup = BeautifulSoup(html, "html.parser")
    links = soup.find_all("a", href=True)
    
    print(f"Found {len(links)} links.")
    
    course_links = set()
    other_links = set()
    
    for a in links:
        href = a['href']
        if href.startswith("/"):
            href = "https://nextleap.app" + href
            
        if "/course/" in href:
            course_links.add(href)
        else:
            other_links.add(href)
            
    print("\n--- Potential Course Links ---")
    for l in sorted(course_links):
        print(l)
        
    print("\n--- Other Links (Sample) ---")
    for l in sorted(list(other_links))[:10]:
        print(l)

if __name__ == "__main__":
    inspect_home()
