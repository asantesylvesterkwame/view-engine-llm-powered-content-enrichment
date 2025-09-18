# View-Engine's LLM-Powered Content Enrichment

## Overview

This project enriches Markdown articles by programmatically inserting relevant media (images/videos) and contextual hyperlinks using a Large Language Model (LLM). The system is designed for robust data handling, effective prompt engineering, and strict adherence to brand guidelines.

## Media & Link Selection Logic

- **Data Retrieval:** The script queries the provided `media.db` and `links.db` SQLite databases to retrieve all available media and link candidates, including their metadata (title, description, tags, etc.).
- **Shortlisting:** All candidates are passed to the LLM, which is responsible for selecting the most contextually relevant hero image, in-context media, and two links based on the article content, provided keywords, and brand rules. No hardcoding or manual filtering is used, ensuring dynamic operation for unseen articles.

## Prompt Engineering Strategy

- The LLM receives a structured prompt containing:
  - The full article text
  - Target keywords for anchor text
  - Media and link candidates (with metadata)
  - Brand rules (voice, accessibility, alt-text)
- The prompt instructs the LLM to:
  - Select one hero image and one in-context media
  - Select two links and generate anchor text around the provided keywords
  - Specify insertion points for each link
  - Return a strict JSON object for reliable parsing
- The system parses the LLM's JSON response and programmatically inserts enrichments at the specified locations.

## Logging & Error Handling

- The script uses Python's `logging` module to log all major steps, including LLM requests/responses and parsing outcomes.
- All exceptions are caught and logged with stack traces for easy debugging.
- The system is resilient to minor LLM output variations and will append links at the end if insertion points are not found.

## Running the Script

1. **Environment Setup:**
   - Install [uv](https://github.com/astral-sh/uv) (if not already):
     ```bash
     pip install uv
     ```
   - Create a virtual environment and install dependencies:
     ```bash
     uv venv
     uv pip install -r requirements.txt
     ```
2. **Run the Enrichment Script:**
   ```bash
   python run.py --article_path resources/article_1.md --keywords_path resources/keywords_1.txt --output_path enriched_article_1.md
   ```
   - Replace the input/output paths as needed for other articles.

## Notes

- Requires Python 3.11+.
- All enrichments are LLM-selected and brand-compliant.
- Efficient API usage is encouraged to conserve OpenRouter credits.
