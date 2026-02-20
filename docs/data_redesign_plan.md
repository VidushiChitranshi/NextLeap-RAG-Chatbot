# Data Correction & Schema Redesign Plan: NextLeap RAG Scraper

This document outlines the diagnosis and architectural correction strategy for the NextLeap course scraper to resolve data malformation, semantic errors, and missing critical fields.

## 1. Error Diagnosis

The initial scraper output (Phase 1) exhibited several structural and quality failures that must be mitigated:

### a. Semantic & Structural Issues
- **Marketing Copy Misuse**: Fields like `title` and `placement_support` captured long-form SEO headlines ("NextLeap... with Placement Support") rather than atomic attributes.
- **Generic Feature Bloating**: The `features` field was used as a "catch-all" array for redundant marketing strings, leading to data noise and potential context overlap in RAG.
- **Null Reference Failures**: Critical fields like `fellowship_timeline`, `cohort`, and `faculty` remained `null` due to overly strict or fragile pattern matching.

### b. Normalization Failures
- **Lack of Atomicity**: Duration ("16 weeks") and Timeline ("4 months") were not separated from their descriptive text.
- **Schema Variance**: The current schema does not distinguish between required and optional attributes, allowing incomplete objects to be serialized.

---

## 2. Corrected Target Schema

The new schema enforces strict typing and atomicity, removing the generic `features` field in favor of explicit attributes.

```json
{
  "course": {
    "title": "string",
    "duration_weeks": "integer",
    "fellowship_months": "integer",
    "live_class_hours": "integer",
    "placement_support_years": "integer",
    "certification_awarded": "boolean"
  },
  "cohort": {
    "id": "integer",
    "start_date": "ISO-8601-String",
    "status": "enum [UPCOMING, ONGOING, CLOSED]"
  },
  "pricing": {
    "amount": "integer",
    "currency": "ISO-4217 (string)",
    "display_price": "string (formatted)"
  },
  "faculty": {
    "mentors": [
      {
        "name": "string",
        "designation": "string",
        "company": "string",
        "profile_url": "URL (string)"
      }
    ],
    "instructors": [ "same_as_mentors" ]
  },
  "metadata": {
    "scraped_at": "ISO-8601",
    "source_url": "URL"
  }
}
```

---

## 3. Normalization & Cleaning Rules

To ensure data consistency across different course pages or layout updates:

- **Numeric Extraction**: Use regex `(\d+)` on duration strings to isolate integers (e.g., "16 weeks" -> `16`).
- **Date Normalization**: 
    - Convert "Mar 7" -> `YYYY-03-07`.
    - Infer Year: If current month > March, target year = current_year + 1.
- **Currency Parsing**: Strip symbols and whitespace; map `₹` to `INR`.
- **Text Deduplication**: Trim whitespace, remove hidden line breaks, and collapse multiple spaces. 
- **Mapping Fallbacks**: If "Live class hours" is missing from the sidebar, fallback to a secondary search in the "Syllabus" section.

---

## 4. Validation Layer (Hardening)

A validation step must be executed before final serialization:

| Rule Tier | Description | Action on Failure |
| :--- | :--- | :--- |
| **Critical Check** | `course.title`, `pricing.amount`, and `cohort.start_date` must not be null. | **Fatal Error**: Stop scraper. |
| **Type Validation** | `duration_weeks` must be `integer`; `profile_url` must match URL pattern. | **Warning**: Log and set to `null`. |
| **Sanity Check** | Pricing must be within range (e.g., 20k - 100k) to detect decimal errors. | **Warning**: Escalation log. |
| **Cohort Check** | `cohort.id` must be greater than 0. | **Fatal Error**: Incorrect parsing. |

---

## 5. Extraction Constraints & Filtering

To maintain a high signal-to-noise ratio:

- **Exclusion Filters**:
    - **Tag Filter**: Explicitly skip `<script>`, `<style>`, `<nav>`, `<footer>`, and `aside.reviews`.
    - **Header Filtering**: Skip any string contained within sections titled "FAQs", "Reviews", or "Testimonials".
- **Semantic Anchoring**: Target data only within sections containing keywords like "Course Fees", "Curriculum", or "Meet your Instructors".

---

## 6. Change Detection Strategy

The system must detect changes in the underlying site to prevent stale data:

- **Price Guard**: Compare `pricing.amount` with the previous run. If delta > 15%, flag for human review (potential surge or decimal error).
- **Cohort Watch**: If `cohort.id` does not increment or change from the last run, trigger a "Likely Stale Content" alert.
- **Layout Signature**: Store the MD5 hash of the stripped HTML structure. If the hash changes significantly, flag potential "Parser Breakage".
