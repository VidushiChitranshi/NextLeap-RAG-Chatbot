from modules.scraper.scraper import CourseScraper
from bs4 import BeautifulSoup

def inspect():
    url = "https://nextleap.app/course/business-analyst-course"
    scraper = CourseScraper(url)
    html = scraper.fetch_page()
    
    if not html:
        print("Failed to fetch.")
        return

    soup = BeautifulSoup(html, "html.parser")
    
    # 1. Look for H1
    h1 = soup.find("h1")
    print(f"H1: {h1.get_text() if h1 else 'None'}")
    
    # 2. Look for title tag
    title = soup.find("title")
    print(f"Title Tag: {title.get_text() if title else 'None'}")
    
    # 3. Save for manual checking if needed
    with open("data/raw/ba_debug.html", "w", encoding="utf-8") as f:
        f.write(html)
        
if __name__ == "__main__":
    inspect()
