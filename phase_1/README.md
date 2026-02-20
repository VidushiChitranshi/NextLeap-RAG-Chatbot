# Phase 1: URL Discovery

## Purpose
This module handles the discovery of course URLs from the NextLeap homepage. It is the first step in the scraping pipeline.

## Input
- **Homepage URL**: Defaults to `https://nextleap.app/`.

## Output
- **List of Valid Course URLs**: A list of strings, each representing a unique, full URL to a course landing page.

## Filtering Rules
The module applies the following rules to filter discovered links:
1.  **Must contain `/course/`**: Only URLs with this path segment are considered.
2.  **Exclusions**: Links matching specific patterns (e.g., `/blog/`, `/events`, `/about`) are excluded to prevent false positives.
3.  **Deduplication**: URLs are stored in a set to ensure uniqueness.
4.  **Normalization**: Relative URLs are converted to absolute URLs. Query parameters are removed.

## Usage
The `CourseDiscovery` class in `discovery.py` is the main entry point. Use `get_course_urls()` to execute the discovery process.
