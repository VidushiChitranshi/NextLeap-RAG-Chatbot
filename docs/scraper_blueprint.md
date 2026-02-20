# Scraper Blueprint: NextLeap Course Extraction Module

This document defines the specialized technical architecture for a web scraper targeting the [NextLeap Product Management Fellowship](https://nextleap.app/course/product-management-course). The system is designed to extract strictly defined course metadata while filtering out non-essential marketing and community content.

## 1. Objective & Scope

The objective is to gather high-fidelity, structured data for the RAG system's knowledge base. 

### Inclusion List (Targeted Data)
*   **Core Course Information**: Title, duration, certification details, placement support status.
*   **Cohort Information**: Specific cohort number (e.g., Cohort 47) and start date.
*   **Pricing**: Numeric amount and currency.
*   **Faculty**: Mentors and Instructors (Name, Title, Company, Bio links).

### Exclusion List (Explicit Ignore)
*   Blogs and Article snippets.
*   FAQs (unless specifically requested in future phases).
*   Testimonials and Success Stories.
*   Generic footer links and navigation menus.

---

## 2. Scraping Strategy

### Rendering Requirements
- **Primary Method**: **Static Scraping** via `requests` + `BeautifulSoup4`. Initial analysis shows core metadata (title, cohort, pricing) is embedded in the initial HTML for SEO performance.
- **Fallback Method**: **Selective Dynamic Rendering** via `Playwright`. Required only if Mentor/Instructor profiles are loaded via client-side API calls after the initial page load.

### DOM Targeting Strategy
- **Section-Based Anchoring**: Identify unique IDs or `data-testid` attributes or semantic classes (e.g., `section#curriculum`, `div.faculty-card`).
- **Pattern Matching**: RegEx for cohort identification (e.g., `Cohort\s*(\d+)`) and currency extraction (e.g., `₹\s*([\d,]+)`).
- **CSS Selectors**: Use specific selectors to pinpoint pricing and start dates to minimize the risk of layout change impact.

### Rate Limiting & Politeness
- **Concurrency**: Sequential scraping only; no parallel workers on the same domain.
- **Interval**: 2-second delay between requests.
- **User-Agent**: Custom string identifying the bot for transparent communication with NextLeap's server.

---

## 3. Modular System Design

The module is partitioned into five logical components to ensure separation of concerns:

| Module | Responsibility |
| :--- | :--- |
| **Fetcher** | Handles HTTP requests, retries (exponential backoff), and Playwright sessions. |
| **Parser** | Locates DOM elements and extracts raw text/attributes. |
| **Cleaner** | Normalizes data types (string to int/float), cleans whitespace, and formats dates. |
| **Validator** | Ensures extracted data matches the defined JSON schema. |
| **Output Formatter** | Serializes the validated object into the final JSON file. |

---

## 4. Data Structuring (JSON Schema)

The output must conform to the following nested structure:

```json
{
  "course_metadata": {
    "title": "string",
    "features": ["string"],
    "fellowship_timeline": "string",
    "placement_support": "string"
  },
  "cohort": {
    "id": "integer",
    "start_date": "ISO-8601-String"
  },
  "pricing": {
    "amount": "float",
    "currency": "string"
  },
  "faculty": {
    "mentors": [
      {
        "name": "string",
        "designation": "string",
        "company": "string (optional)",
        "profile_link": "URL (optional)"
      }
    ],
    "instructors": [ ... same as mentors ... ]
  }
}
```

---

## 5. Data Cleaning & Normalization

- **Currency**: Strip symbols (₹) and commas; convert to numeric float.
- **Date**: Convert strings like "Mar 7" to a standard ISO structure `YYYY-MM-DD` using the current year context.
- **Missing Data**: Use `null` for optional fields (Company, Profile Link) rather than empty strings.
- **Deduplication**: Sanitize faculty lists to ensure no duplicate entries are recorded if they appear in multiple sections.

---

## 6. Logic & Edge Case Handling

- **Multiple Cohorts**: If more than one cohort is listed, the parser will default to the earliest upcoming date unless otherwise configured.
- **Layout Changes**: If a critical field (Title or Price) is not found, the module will halt and log a "Critical Selector Failure" event.
- **Partial Loads**: Check for Footer presence to confirm full page render before parsing.

---

## 7. Future Extensibility

- **Multi-Course Support**: The Parser can be subclassed to support other NextLeap courses (e.g., Product Growth).
- **Update Frequency**: The system can be scheduled to run weekly to detect new cohorts or price updates.
- **CDP Integration**: Data can be pushed directly to a search index or database via the Output Formatter module.
