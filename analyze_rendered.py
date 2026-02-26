import bs4
import re

def analyze():
    with open('rendered_page.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    soup = bs4.BeautifulSoup(html, 'html.parser')
    
    def get_path(el):
        path = []
        while el and el.name != '[document]':
            name = el.name
            if 'class' in el.attrs:
                name += '.' + '.'.join(el['class'])
            path.append(name)
            el = el.parent
        return ' > '.join(reversed(path))

    print("--- Pricing (36,999) ---")
    for el in soup.find_all(string=re.compile("36,999")):
        parent = el.parent
        print(f"Path: {get_path(parent)}")
        print(f"Text: {parent.get_text(strip=True)}")

    print("\n--- Cohort (47) ---")
    for el in soup.find_all(string=re.compile("Cohort 47|Cohort-47")):
        parent = el.parent
        print(f"Path: {get_path(parent)}")
        print(f"Text: {parent.get_text(strip=True)}")

    print("\n--- Start Date (Mar 7) ---")
    for el in soup.find_all(string=re.compile("Mar 7|March 7")):
        parent = el.parent
        print(f"Path: {get_path(parent)}")
        print(f"Text: {parent.get_text(strip=True)}")

    print("\n--- Instructors Section ---")
    instr_header = soup.find(string=re.compile("Instructors who are Industry experts"))
    if instr_header:
        # Look for the container
        container = instr_header.parent
        for _ in range(3): # Go up a few levels
            if container: container = container.parent
        if container:
            print(f"Possible container for instructors: {get_path(container)}")
            # Count strong elements
            strongs = container.find_all('strong')
            print(f"Found {len(strongs)} strong elements in this container")

if __name__ == "__main__":
    analyze()
