import json
import logging
from typing import List, Dict, Any
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

    def process_course(self, course_data: Dict[str, Any]) -> List[Document]:
        """
        Converts the nested course data dictionary into a list of Documents.
        Each logical section of the course (overview, faculty, curriculum week) 
        becomes a separate Document.
        """
        documents = []
        
        # 1. Course Overview
        course_info = course_data.get("course", {})
        metadata = course_data.get("metadata", {})
        source_url = metadata.get("source_url", "")
        
        overview_text = (
            f"Course Title: {course_info.get('title', 'N/A')}\n"
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
                "title": "Course Overview"
            }
        ))

        # 2. Pricing & Cohort
        pricing = course_data.get("pricing", {})
        cohort = course_data.get("cohort", {})
        
        pricing_text = (
            f"Current Cohort Price: {pricing.get('display', 'N/A')}\n"
            f"Cohort Status: {cohort.get('status', 'N/A')}\n"
            f"Start Date: {cohort.get('start_date', 'N/A')}"
        )
        
        documents.append(Document(
            page_content=pricing_text,
            metadata={
                "source": source_url,
                "section_type": "pricing",
                "title": "Pricing and Cohort"
            }
        ))

        # 3. Faculty (Instructors & Mentors)
        faculty = course_data.get("faculty", {})
        instructors = faculty.get("instructors", [])
        mentors = faculty.get("mentors", [])
        
        # Group instructors into one document
        if instructors:
            instructor_lines = ["Instructors:"]
            for inst in instructors:
                line = f"- {inst.get('name')} ({inst.get('designation')} at {inst.get('company')})"
                instructor_lines.append(line)
            
            documents.append(Document(
                page_content="\n".join(instructor_lines),
                metadata={
                    "source": source_url,
                    "section_type": "faculty",
                    "subtype": "instructors",
                    "title": "Course Instructors"
                }
            ))

        # Group mentors into one document (or split if too large, but for now one is fine)
        if mentors:
            mentor_lines = ["Mentors:"]
            for men in mentors:
                line = f"- {men.get('name')} ({men.get('designation')} at {men.get('company')})"
                mentor_lines.append(line)
            
            documents.append(Document(
                page_content="\n".join(mentor_lines),
                metadata={
                    "source": source_url,
                    "section_type": "faculty",
                    "subtype": "mentors",
                    "title": "Course Mentors"
                }
            ))
            
        # 4. Curriculum (Future Proofing)
        # If 'sections' or 'curriculum' exists in the future
        curriculum = course_data.get("curriculum", [])
        if curriculum:
            for module in curriculum:
                # Assuming module has title and content
                text = f"Module: {module.get('title', '')}\n{module.get('content', '')}"
                documents.append(Document(
                    page_content=text,
                    metadata={
                        "source": source_url,
                        "section_type": "curriculum",
                        "title": module.get('title', 'Curriculum Module')
                    }
                ))

        return documents
