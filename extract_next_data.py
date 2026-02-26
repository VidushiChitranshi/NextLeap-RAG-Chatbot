import bs4
import json
import re

def extract_next_data():
    with open('debug_page.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    soup = bs4.BeautifulSoup(html, 'html.parser')
    script = soup.find('script', id='__NEXT_DATA__')
    if not script:
        print("NOT FOUND")
        return None
    
    data = json.loads(script.string)
    return data

def find_pricing_and_cohort(data):
    # Recursively search for keys
    def search(obj, key_patterns):
        results = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                for p in key_patterns:
                    if re.search(p, k, re.IGNORECASE):
                        results.append((k, v))
                results.extend(search(v, key_patterns))
        elif isinstance(obj, list):
            for item in obj:
                results.extend(search(item, key_patterns))
        return results

    patterns = ['price', 'fee', 'cohort', 'start', 'date', 'mentor', 'instructor', 'faculty']
    found = search(data, patterns)
    
    # Store unique key-value pairs for brevity
    seen = set()
    unique_found = []
    for k, v in found:
        # If value is simple, show it. If complex, show its type/length
        val_summary = v
        if isinstance(v, (dict, list)):
            val_summary = f"{type(v)} (len={len(v)})"
        
        entry = (k, str(val_summary))
        if entry not in seen:
            unique_found.append(entry)
            seen.add(entry)
            
    return unique_found

data = extract_next_data()
if data:
    # Look into props.pageProps
    page_props = data.get('props', {}).get('pageProps', {})
    print("\n--- PageProps Keys ---")
    print(list(page_props.keys()))
    
    # Check for 'course' or 'data' or 'content' in props
    print("\n--- Searching for patterns in data ---")
    results = find_pricing_and_cohort(data)
    for k, v in results:
        print(f"{k}: {v}")

    # Explicitly check for 36999
    json_str = json.dumps(data)
    if "36999" in json_str:
        print("\nFOUND 36999 in JSON!")
    else:
        print("\n36999 NOT FOUND in JSON.")
    
    with open('extracted_next_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
