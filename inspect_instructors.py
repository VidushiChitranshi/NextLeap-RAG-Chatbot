import bs4
import re

def inspect_instructor_section():
    try:
        with open('rendered_page.html', encoding='utf-8') as f:
            soup = bs4.BeautifulSoup(f, 'html.parser')
        
        h = (soup.find(string=re.compile("Instructors who are Industry experts", re.I)) or 
             soup.find(string=re.compile("Learn Concepts From Our Instructors", re.I)))
        
        if not h:
            print("Header not found")
            return
            
        print(f"Header: '{h.strip()}'")
        section = h.find_parent(['div', 'section'])
        print(f"Section Class: {section.get('class')}")
        
        # Look for all slick-slides in this section
        slides = section.find_all(class_=re.compile('slick-slide', re.I))
        print(f"Found {len(slides)} slides in section")
        
        for i, slide in enumerate(slides):
            text = slide.get_text(strip=True)
            if not text: continue
            print(f"\n[Slide {i}] Text: {text[:200]}...")
            links = slide.find_all('a', href=re.compile("linkedin", re.I))
            if links:
                print(f"  Links: {[l.get('href') for l in links]}")
            else:
                print("  No LinkedIn links.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_instructor_section()
