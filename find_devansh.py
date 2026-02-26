import bs4
import re

def find_devansh():
    try:
        with open('rendered_page.html', encoding='utf-8') as f:
            soup = bs4.BeautifulSoup(f, 'html.parser')
        
        target = "Devansh"
        matches = soup.find_all(string=re.compile(target, re.I))
        
        for i, match in enumerate(matches):
            parent = match.parent
            if parent.name in ['script', 'style', 'head']: continue
            print(f"\nMatch {i}: {match.strip()}")
            curr = parent
            for depth in range(6):
                if not curr: break
                print(f"  D{depth}: {curr.name} | Class: {curr.get('class')}")
                curr = curr.parent
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_devansh()
