import bs4
import re

def map_all_linkedin_links():
    try:
        with open('rendered_page.html', encoding='utf-8') as f:
            soup = bs4.BeautifulSoup(f, 'html.parser')
        
        links = soup.find_all('a', href=re.compile("linkedin", re.I))
        print(f"Total LinkedIn links found: {len(links)}")
        
        for i, link in enumerate(links):
            href = link.get('href')
            text = link.get_text(strip=True)
            # Find closest text-bearing ancestor
            parent = link.parent
            while parent and not parent.get_text(strip=True):
                parent = parent.parent
            
            p_text = parent.get_text(strip=True)[:100] if parent else "N/A"
            print(f"[{i}] {href}")
            print(f"    Text: '{text}'")
            print(f"    Context: '{p_text}'")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    map_all_linkedin_links()
