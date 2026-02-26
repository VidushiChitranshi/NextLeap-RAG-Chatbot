import json
import logging
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

class DataProcessor:
    """
    Processes course data JSON into LangChain Documents.
    """

    def load_data(self, file_path: str) -> Dict[str, Any]:
        """Loads JSON data from the given file path."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Successfully loaded data from {file_path}")
            return data
        except Exception as e:
            logger.error(f"Error loading data from {file_path}: {e}")
            raise

    def process_course(self, data: Dict[str, Any]) -> List[Document]:
        """
        Converts course data (single or multiple) into a list of Documents.
        """
        documents = []
        
        # Check if it's the multi-course "scraped" format
        courses = data.get("courses", [])
        if not courses and "course" in data:
            # Fallback to single course format
            courses = [data]

        for course_data in courses:
            documents.extend(self._process_single_course(course_data))
            
        # Add a global summary document if multiple courses exist
        if len(courses) > 1:
            summary_doc = self.generate_catalog_summary(courses)
            if summary_doc:
                documents.insert(0, summary_doc)
                
        return documents

    def _process_single_course(self, course_data: Dict[str, Any]) -> List[Document]:
        """Internal helper to process a single course dictionary."""
        documents = []
        
        # 1. Course Overview
        course_info = course_data.get("course", {})
        metadata = course_data.get("metadata", {})
        source_url = metadata.get("source_url", "")
        
        title = course_info.get('title', 'N/A')
        overview_text = (
            f"Course Title: {title}\n"
            f"Duration: {course_info.get('duration_weeks', 'N/A')} weeks\n"
            f"Fellowship Duration: {course_info.get('fellowship_months', 'N/A')} months\n"
            f"Live Hours: {course_info.get('live_class_hours', 'N/A')}+\n"
            f"Placement Support: {course_info.get('placement_support_years', 'N/A')} year(s)\n"
            f"Certification: {course_info.get('certification_awarded', 'N/A')}"
        )
        
        documents.append(Document(
            page_content=overview_text,
            metadata={
                "source": source_url,
                "section_type": "overview",
                "title": f"Overview: {title}"
            }
        ))

        # 2. Pricing & Cohort
        pricing = course_data.get("pricing", {})
        cohort = course_data.get("cohort", {})
        
        pricing_text = (
            f"Course: {title}\n"
            f"Current Cohort Price: {pricing.get('display', 'N/A')}\n"
            f"Cohort Status: {cohort.get('status', 'N/A')}\n"
            f"Start Date: {cohort.get('start_date', 'N/A')}"
        )
        
        documents.append(Document(
            page_content=pricing_text,
            metadata={
                "source": source_url,
                "section_type": "pricing",
                "title": f"Pricing: {title}"
            }
        ))

        # 3. Faculty
        faculty = course_data.get("faculty", {})
        instructors = faculty.get("instructors", [])
        mentors = faculty.get("mentors", [])
        
        if instructors:
            instructor_lines = [f"Instructors for {title}:"]
            for inst in instructors:
                line = f"- {inst.get('name')} ({inst.get('designation')} at {inst.get('company')})"
                instructor_lines.append(line)
            
            documents.append(Document(
                page_content="\n".join(instructor_lines),
                metadata={
                    "source": source_url,
                    "section_type": "faculty",
                    "subtype": "instructors",
                    "title": f"Instructors: {title}"
                }
            ))

        if mentors:
            mentor_lines = [f"Mentors for {title}:"]
            for men in mentors:
                line = f"- {men.get('name')} ({men.get('designation')} at {men.get('company')})"
                mentor_lines.append(line)
            
            documents.append(Document(
                page_content="\n".join(mentor_lines),
                metadata={
                    "source": source_url,
                    "section_type": "faculty",
                    "subtype": "mentors",
                    "title": f"Mentors: {title}"
                }
            ))
            
        return documents

    def generate_catalog_summary(self, courses: List[Dict[str, Any]]) -> Optional[Document]:
        """Generates a summary document listing all available courses."""
        if not courses:
            return None
            
        course_list = []
        for c in courses:
            c_info = c.get("course", {})
            title = c_info.get("title")
            url = c_info.get("url")
            if title:
                course_list.append(f"- {title} ({url if url else 'Contact us for details'})")
        
        summary_text = (
            "NextLeap offers several fellowship programs to help you transition into high-growth roles. "
            f"Currently, there are {len(course_list)} courses offered by NextLeap:\n\n"
            + "\n".join(course_list)
        )
        
        return Document(
            page_content=summary_text,
            metadata={
                "source": "https://nextleap.app/courses",
                "section_type": "catalog_summary",
                "title": "Available Courses Summary"
            }
        )
