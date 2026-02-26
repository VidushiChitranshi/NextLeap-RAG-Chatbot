import os
try:
    from playwright.sync_api import sync_playwright
    print("Playwright imported successfully")
except ImportError:
    print("Playwright not installed")
    exit(1)

# Set HOME if it's missing (PowerShell might not have it)
if 'HOME' not in os.environ:
    os.environ['HOME'] = os.path.expanduser('~')
    print(f"Set HOME to {os.environ['HOME']}")

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print("Browser and page created")
        page.goto("https://nextleap.app/course/product-management-course")
        page.wait_for_timeout(5000) # Wait for dynamic bits
        html = page.content()
        print(f"Captured HTML length: {len(html)}")
        
        # Search for the user values
        if "36,999" in html: print("FOUND 36,999")
        if "36999" in html: print("FOUND 36999")
        if "Cohort" in html: print("FOUND Cohort")
        if "47" in html: print("FOUND 47")
        if "Mar 7" in html: print("FOUND Mar 7")
        
        with open("rendered_page.html", "w", encoding="utf-8") as f:
            f.write(html)
        
        browser.close()
except Exception as e:
    print(f"Playwright execution failed: {e}")
