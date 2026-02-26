import bs4
import re

def list_instructor_headers():
    try:
        with open('rendered_page.html', encoding='utf-8') as f:
            soup = bs4.BeautifulSoup(f, 'html.parser')
        
        h_text = "Instructors who are Industry experts|Learn Concepts From Our Instructors"
        matches = soup.find_all(string=re.compile(h_text, re.I))
        
        print(f"Found {len(matches)} potential instructor headers:")
        for i, m in enumerate(matches):
            p = m.parent
            gp = p.parent if p else None
            ggp = gp.parent if gp else None
            print(f"\nMatch {i}: '{m.strip()}'")
            print(f"  Parent: {p.name} | Class: {p.get('class')}")
            if gp: print(f"  Grandparent: {gp.name} | Class: {gp.get('class')}")
            if ggp: print(f"  Great-Grandparent: {ggp.name} | Class: {ggp.get('class')}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_instructor_headers()
