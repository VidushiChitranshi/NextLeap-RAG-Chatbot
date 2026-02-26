import requests
from bs4 import BeautifulSoup
import re

url = "https://nextleap.app/course/product-management-course"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
}

resp = requests.get(url, headers=headers)
html = resp.text

with open("debug_page.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"Status: {resp.status_code}")
print(f"HTML Length: {len(html)}")

# Search for specific strings
patterns = [
    "36,999",
    "39,999",
    "Cohort",
    "Certification",
    "Placement Support",
    "1 year",
    "4 months"
]

for p in patterns:
    matches = [m.start() for m in re.finditer(p, html, re.IGNORECASE)]
    print(f"Pattern '{p}' found at indices: {matches[:5]} (Total: {len(matches)})")

# Print snippets around pricing
price_index = html.find("36,999")
if price_index != -1:
    print("\n--- Snippet around 36,999 ---")
    print(html[price_index-100:price_index+100])

cohort_index = html.find("Cohort")
if cohort_index != -1:
    print("\n--- Snippet around Cohort ---")
    print(html[cohort_index-100:cohort_index+100])
