import bs4
import re

def inspect_slide_0():
    try:
        with open('rendered_page.html', encoding='utf-8') as f:
            soup = bs4.BeautifulSoup(f, 'html.parser')
        
        h = soup.find(string=re.compile('Learn Concepts From Our Instructors', re.I))
        if not h:
            print("Header not found")
            return
            
        container = h.find_parent(['div', 'section'])
        slides = container.find_all(class_=re.compile('slick-slide', re.I))
        
        if slides:
            print(f"Total slides found: {len(slides)}")
            print("\n--- SLIDE 0 HTML ---")
            print(slides[0].prettify())
        else:
            print("No slides found in the instructor section.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_slide_0()
