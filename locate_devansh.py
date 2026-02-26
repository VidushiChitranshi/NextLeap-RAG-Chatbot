import bs4
import re

def locate_devansh():
    try:
        with open('rendered_page.html', encoding='utf-8') as f:
            soup = bs4.BeautifulSoup(f, 'html.parser')
        
        target = "Devansh Jain"
        match = soup.find(string=re.compile(target, re.I))
        if not match:
            print("Devansh Jain not found")
            return
            
        print(f"Found {target}")
        curr = match.parent
        for i in range(12):
            print(f"D{i}: {curr.name} | Class: {curr.get('class')}")
            # Check for headers in ancestors
            siblings = curr.find_previous_siblings(["h1", "h2", "h3", "h4"])
            if siblings:
                print(f"  Prev Headers: {[s.get_text(strip=True) for s in siblings]}")
            curr = curr.parent
            if not curr: break

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    locate_devansh()
