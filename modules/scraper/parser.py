import logging
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional
import re

logger = logging.getLogger(__name__)

class CourseParser:
    """Parses NextLeap course page HTML into structured data."""
    
    def __init__(self, html_content: str):
        self.soup = BeautifulSoup(html_content, 'html.parser')

    def parse_core_info(self) -> Dict[str, Any]:
        """Extracts atomic attributes: title, duration, hours, etc."""
        # Certification check: Return "Yes" or "No" string
        cert_text = self._find_text_by_pattern("Certification", partial=True)
        
        # Generic Title Extraction
        title = None
        h1_tag = self.soup.find("h1")
        if h1_tag:
            title = h1_tag.get_text(strip=True)
        elif self.soup.title:
            title = self.soup.title.get_text(strip=True).split("|")[0].strip()
        
        return {
            "title": title,
            "duration_weeks_raw": self._find_text_by_pattern(r"(\d+)\s*weeks?", regex=True),
            "live_hours_raw": self._find_text_by_pattern(r"(\d+)\+\s*Hours", regex=True),
            "fellowship_months_raw": self._find_text_by_pattern(r"(\d+)\s*months?", regex=True),
            "placement_support_raw": self._find_text_by_pattern(r"1\s*year", regex=True),
            "certification_awarded": "Yes" if cert_text else "No"
        }

    def parse_cohort(self) -> Dict[str, Any]:
        """Extracts cohort ID and raw start date string."""
        # Find in the registration component discovered in rendered HTML
        reg_comp = self.soup.find(class_=re.compile("compact-registration-component-parent", re.IGNORECASE))
        if reg_comp:
            text = reg_comp.get_text()
            cohort_match = re.search(r"Cohort\s*(\d+)", text, re.IGNORECASE)
            date_match = re.search(r"starts on\s*(.*)", text, re.IGNORECASE)
            return {
                "cohort_raw": cohort_match.group(0) if cohort_match else None,
                "date_raw": date_match.group(1).split("\n")[0].strip() if date_match else None
            }
        
        # Fallback to general search
        return {
            "cohort_raw": self._find_text_by_pattern(r"Cohort\s*\d+", regex=True),
            "date_raw": self._find_text_by_pattern(r"starts on", partial=True)
        }

    def parse_pricing(self) -> Dict[str, Any]:
        """Extracts pricing amount and currency."""
        # Target the registration component first for the final price
        reg_comp = self.soup.find(class_=re.compile("compact-registration-component-parent", re.IGNORECASE))
        price_raw = None
        if reg_comp:
            # Look for pricing patterns in that component specifically
            price_match = re.search(r"₹[0-9,]+", reg_comp.get_text())
            if price_match:
                price_raw = price_match.group(0)
        
        if not price_raw:
            price_raw = self._find_text_by_pattern(r"₹\s*[\d,]+", regex=True)
            
        return {"price_raw": price_raw}

    def parse_faculty(self) -> Dict[str, List[Dict[str, Any]]]:
        """Extracts mentors and instructors from faculty cards."""
        faculty = {"mentors": [], "instructors": []}
        
        # Tools and features to exclude from instructors
        exclude_names = {
            "Microsoft Clarity", "Whimsical", "Figma", "JIRA", "Google Analytics", 
            "Microsoft Excel", "Open AI", "Claude", "N8n", "Make", "Lovable", "Cursor", "GitHub",
            "Fortnightly assignments", "Learn in Public Challenges", "AI Hackathons", "Graduation Project",
            "Community Event", "Class on", "Session on"
        }
        
        # Comprehensive list of instructor name patterns (to exclude from mentors)
        core_instructor_patterns = [
            "Arindam", "Karthi", "Prashanth", "Bhaskaran", "Bhaskar",
            "Eshan", "Tiwari", "Kartik", "Singh", "Devansh", "Saksham", "Arora", "Shailesh", "Sharma",
            "Subbaraman", "Mukherjee"
        ]
        
        # 1. Instructors extraction (Standard section)
        # Prioritizing the body header "Learn Concepts From Our Instructors" over the footer one
        instructor_header = (self.soup.find(string=re.compile("Learn Concepts From Our Instructors", re.IGNORECASE)) or 
                             self.soup.find(string=re.compile("Instructors who are Industry experts", re.IGNORECASE)))
        
        if instructor_header:
            container = instructor_header.find_parent(["div", "section"])
            if container:
                # Find all potential instructor cards directly
                final_items = container.find_all("div", class_=re.compile("compact-id-card-image-card-parent", re.I))
                
                # Fallback if no specific cards found
                if not final_items:
                    final_items = container.find_all(["li", "div"], class_=re.compile("slick-slide|instructor-card", re.I))

                for item in final_items:
                    # Search for name in h3 or strong
                    name_tag = item.find(["h3", "strong"]) if item.name not in ["h3", "strong"] else item
                    if not name_tag: continue
                    
                    name = name_tag.get_text(strip=True).strip(":")
                    if not name or any(ex in name for ex in exclude_names) or "Live " in name or "Session" in name or "Challenge" in name:
                        continue
                    
                    if len(name.split()) > 4: continue

                    # Combined approach: use item text but split by name and then clean up carefully
                    item_text = item.get_text(" ", strip=True)
                    parts = item_text.split(name)
                    desc = parts[1].strip().strip(":") if len(parts) > 1 else ""
                    
                    # Clean up desc if it contains the start of the next card information
                    # (e.g. if another h3 was inside)
                    if item.find_all("h3"):
                         # Re-calculate desc based on siblings only if multiple h3s
                         meta_parts = []
                         for sibling in name_tag.next_siblings:
                             if sibling.name == "h3": break
                             t = sibling.get_text(strip=True)
                             if t: meta_parts.append(t)
                         desc = " ".join(meta_parts)

                    # Updated Regex for Instructors (Robust Split)
                    # Split by common separators with word boundaries to avoid partial matches
                    split_pattern = r"\b(?:at|previously at|@|of)\b"
                    meta_parts = re.split(split_pattern, desc, flags=re.IGNORECASE)
                    
                    designation = meta_parts[0].strip().strip(",")
                    
                    # Extract Company
                    company_match = re.search(r"\b(?:at|previously at|@)\s*([A-Z0-9][A-Za-z0-9\s]+?)(?:\s+\b(?:at|previously at|@|for)\b|\.|$)", desc, re.I)
                    company = company_match.group(1).strip() if company_match else "Top Tech Company"
                    
                    # Extract Profile URL
                    instructor_url = None
                    link_tag = item.find("a", href=re.compile("linkedin", re.I))
                    if link_tag:
                        instructor_url = link_tag.get("href")
                        if instructor_url and "?" in instructor_url:
                            instructor_url = instructor_url.split("?")[0]

                    # Deduplicate by name
                    if not any(inst["name"].lower() == name.lower() for inst in faculty["instructors"]):
                        faculty["instructors"].append({
                            "name": name,
                            "designation": designation,
                            "company": company,
                            "profile_url": instructor_url
                        })

        # 2. Mentors extraction
        # Find all matches for the header text to avoid grabbing script content
        mentor_header_candidates = self.soup.find_all(string=re.compile("Mentorship from industry experts|Get Personalised Feedback from Mentors|Meet your Mentors", re.I))
        mentor_section = None
        
        for candidate in mentor_header_candidates:
            if candidate.parent.name not in ["script", "style", "head", "title", "meta"]:
                mentor_section = candidate
                break
        
        # Fallback to h2 check if string search failed or only found scripts
        if not mentor_section:
             h2_candidate = self.soup.find("h2", string=re.compile("Mentor", re.I))
             if h2_candidate:
                 mentor_section = h2_candidate

        if mentor_section:
            container = mentor_section.find_parent(["div", "section"])
            if container:
                name_tags = container.find_all("h3")
                seen_mentors = set()
                
                for name_tag in name_tags:
                    name = name_tag.get_text(strip=True).strip(":")
                    if not name or any(ex in name for ex in exclude_names) or len(name.split()) > 4 or name.lower() in seen_mentors:
                        continue
                    
                    # Get designation/company using siblings
                    # Based on inspection, the next sibling is often a div with designation
                    meta_parts = []
                    for sibling in name_tag.next_siblings:
                        if sibling.name in ["h3", "h2", "h4"]: break
                        t = sibling.get_text(strip=True)
                        if t: meta_parts.append(t)
                    
                    full_meta = " ".join(meta_parts)
                    # Use parent text relative to name if siblings fail
                    if not full_meta:
                         card_box = name_tag.find_parent(["div", "li"])
                         if card_box:
                             full_meta = card_box.get_text(" ", strip=True).replace(name, "").strip()

                    # Updated Regex for Mentors (Robust Split)
                    split_pattern = r"\b(?:at|previously at|@|of)\b"
                    meta_split = re.split(split_pattern, full_meta, flags=re.IGNORECASE)
                    
                    designation = meta_split[0].strip().strip(",")
                    
                    # Robust Company Extraction
                    company_match = re.search(r"\b(?:at|previously at|@|of)\s*([A-Z0-9][A-Za-z0-9\s]+?)(?:\s+\b(?:at|previously at|@|for|of)\b|\.|$)", full_meta, re.I)
                    company = company_match.group(1).strip() if company_match else "Top Tech Company"
                    
                    # Profile URL extraction
                    profile_url = None
                    card_container = name_tag.find_parent(class_=re.compile("slick-slide|instructor-card|compact-id-card-image-card-parent", re.I))
                    if not card_container:
                        card_container = name_tag.find_parent(["div", "li"])
                        
                    if card_container:
                        link_tag = card_container.find("a", href=re.compile("linkedin", re.I))
                        if link_tag:
                            profile_url = link_tag.get("href")
                            if profile_url and "?" in profile_url:
                                profile_url = profile_url.split("?")[0]

                    faculty["mentors"].append({
                        "name": name,
                        "designation": designation if designation else "Senior Mentor",
                        "company": company if company else "Top Tech Company",
                        "profile_url": profile_url
                    })
                    seen_mentors.add(name.lower())

        # Cleanup: Remove instructors who might have been missed by core patterns
        instructor_names = {i["name"].lower() for i in faculty["instructors"]}
        faculty["mentors"] = [m for m in faculty["mentors"] if m["name"].lower() not in instructor_names]

        return faculty

    def _find_text_by_pattern(self, pattern: str, regex: bool = False, partial: bool = False) -> Optional[str]:
        """Helper to find text nodes or elements containing text matching a pattern."""
        ignore_tags = ['script', 'style', 'noscript']
        
        # 1. Try direct string search first (excluding scripts)
        for element in self.soup.find_all(string=True):
            if element.parent.name in ignore_tags: continue
            text = element.strip()
            if not text: continue

            if regex:
                if re.search(pattern, text, re.IGNORECASE): return text
            elif partial:
                if pattern.lower() in text.lower(): return text
            else:
                if pattern in text: return text
        
        # 2. Try searching in tag text if no direct match found
        if not regex:
            target = self.soup.find(lambda tag: tag.name not in ignore_tags and pattern.lower() in tag.get_text().lower())
            if target:
                return target.get_text(strip=True)
                
        return None

    def _extract_features(self) -> List[str]:
        """Extracts list of course features based on specific user requirements."""
        features = []
        patterns = [
            "100+ Hours Live Classes", 
            "Mentorship",
            "Placement Support",
            "Certification",
            "Fellowship"
        ]
        unique_features = set()
        for p in patterns:
            text = self._find_text_by_pattern(p, partial=True)
            if text and len(text) < 200: # Limit length to avoid capturing huge blocks
                unique_features.add(text)
        return list(unique_features)
