import bs4
import re

def find_instructor_card():
    try:
        with open('rendered_page.html', encoding='utf-8') as f:
            soup = bs4.BeautifulSoup(f, 'html.parser')
        
        target = "Arindam Mukherjee"
        # Find the text "Arindam Mukherjee"
        pattern = re.compile(re.escape(target), re.I)
        # Avoid the script/head matches
        matches = soup.find_all(string=pattern)
        
        for i, match in enumerate(matches):
            parent = match.parent
            # Skip if inside script or head
            if parent.name in ['script', 'style', 'head']: continue
            
            print(f"--- Match {i} ---")
            print(f"Tag: {parent.name}, Link: {parent.get('href')}")
            
            # Trace up to find a container
            curr = parent
            print("Path up:")
            for depth in range(8):
                if not curr: break
                print(f"  D{depth}: {curr.name} | Class: {curr.get('class')} | Links: {[a.get('href') for a in curr.find_all('a', href=re.compile('linkedin', re.I))]}")
                curr = curr.parent

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_instructor_card()
