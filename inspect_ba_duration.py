
from playwright.sync_api import sync_playwright

def inspect_ba_page_full():
    url = "https://nextleap.app/course/business-analyst-course"
    print(f"Inspecting {url}...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_timeout(5000) # Wait for hydration
        
        text_content = page.evaluate("document.body.innerText")
        
        with open("ba_page_text.txt", "w", encoding="utf-8") as f:
            f.write(text_content)
            
        print("Scraped text saved to ba_page_text.txt")
        browser.close()

if __name__ == "__main__":
    inspect_ba_page_full()
