import bs4
import re

def find_arindam_container():
    try:
        with open('rendered_page.html', encoding='utf-8') as f:
            soup = bs4.BeautifulSoup(f, 'html.parser')
        
        target = "Arindam Mukherjee"
        match = soup.find(string=re.compile(target, re.I))
        if not match:
            print(f"'{target}' not found")
            return
            
        print(f"Found '{target}'")
        curr = match.parent
        for i in range(6):
            print(f"L{i}: Tag={curr.name}, Class={curr.get('class')}")
            curr = curr.parent
            if not curr: break
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_arindam_container()
