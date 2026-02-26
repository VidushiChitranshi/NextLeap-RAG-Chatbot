import bs4
import re

def find_instructor_links():
    try:
        with open('rendered_page.html', encoding='utf-8') as f:
            soup = bs4.BeautifulSoup(f, 'html.parser')
        
        instructors = [
            'Arindam Mukherjee', 'Karthi Subbaraman', 'Prashanth Bhaskaran', 
            'Eshan Tiwari', 'Kartik Singh', 'Devansh', 'Saksham Arora', 'Shailesh Sharma'
        ]
        
        print("--- Searching for Instructor Profile Links ---")
        for name in instructors:
            print(f"\nInstructor: {name}")
            # Find the text match
            matches = soup.find_all(string=re.compile(re.escape(name), re.I))
            if not matches:
                print("  No text matches found.")
                continue
                
            for i, match in enumerate(matches):
                if len(match.strip()) > 100: continue
                print(f"  Match {i}: '{match.strip()}'")
                
                # Check siblings and children of the parent item
                # Instructors are usually in <li> or a specific <div>
                parent_li = match.find_parent(["li", "div"], class_=re.compile("slick-slide|instructor-card", re.I))
                if not parent_li:
                    parent_li = match.find_parent("li")
                
                if parent_li:
                    print(f"    - Search in Container: {parent_li.name} (Class: {parent_li.get('class')})")
                    links = parent_li.find_all('a', href=re.compile("linkedin", re.I))
                    if links:
                        for l in links:
                            print(f"      - Found Link: {l.get('href')}")
                    else:
                        print("      - No direct LinkedIn link in container.")
                else:
                    print("    - No card container found for instructor.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_instructor_links()
