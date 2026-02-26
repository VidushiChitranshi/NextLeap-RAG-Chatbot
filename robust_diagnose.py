import bs4
import json
import re

def search_html():
    with open('debug_page.html', 'r', encoding='utf-8') as f:
        html = f.read()

    results_file = open('diagnose_results.txt', 'w', encoding='utf-8')

    # 1. Search for specific strings
    targets = ["36,999", "36999", "39,999", "Cohort", "starts on", "Mar 7", "Mar 07", "7th Mar", "Certification", "Placement Support", "1 year", "4 months", "Kartik Singh", "Saksham Arora", "Arindam Mukherjee", "Karthi Subbaraman", "Prashanth Bhaskaran", "Eshan Tiwari"]
    results_file.write("--- String Search ---\n")
    for t in targets:
        matches = [m.start() for m in re.finditer(re.escape(t), html, re.IGNORECASE)]
        results_file.write(f"'{t}': {len(matches)} matches\n")
        if matches:
            snippet = html[matches[0]-100 : matches[0]+200]
            results_file.write(f"  Snippet: {snippet.strip()}\n\n")

    # 2. Inspect all script tags for JSON-like state
    results_file.write("--- Script Tag Inspection ---\n")
    soup = bs4.BeautifulSoup(html, 'html.parser')
    for i, s in enumerate(soup.find_all('script')):
        if not s.string: continue
        content = s.string
        if any(x in content for x in ["36999", "36,999", "Cohort", "starts on", "Mar 7"]):
            results_file.write(f"Script {i} (type={s.get('type') or 'none'} src={s.get('src') or 'none'}):\n")
            # If it's a huge script, look for the text
            for t in ["36999", "36,999", "Cohort", "starts on", "Mar 7"]:
                if t in content:
                    idx = content.find(t)
                    results_file.write(f"  Found '{t}' at {idx}: ...{content[idx-50:idx+150]}...\n")

    results_file.close()
    print("Diagnosis complete. See diagnose_results.txt")

if __name__ == "__main__":
    search_html()
