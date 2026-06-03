# CVmate — Product Requirements Document

## Overview

CVmate is a local desktop tool that takes a job description and a CV (PDF) as inputs, then uses the Gemini AI model to produce a tailored, rewritten CV (exported as PDF) that emphasizes the skills and experience most relevant to that specific job. The goal is to reduce the manual effort of customizing a CV for every application.

---

## Problem Statement

Job seekers spend significant time manually adjusting their CV for each application to match the language and requirements of the job description. CVmate automates this by intelligently rewriting the CV to align with each specific role while keeping all claims truthful and grounded in the user's real experience.

---

## Goals

- Parse and extract structured data from a user's CV (PDF format).
- Accept a job description as free-form pasted text.
- Use Gemini to compare the two and generate a rewritten, job-tailored CV.
- Export the tailored CV as a clean, professional PDF.
- Run entirely locally; no data stored, no external services beyond the Gemini API.

---

## Non-Goals

- No user accounts or cloud sync.
- No session history or database.
- No cover letter generation (potential future feature).
- No multi-CV management.
- The tool does not fabricate experience — Gemini is instructed to only use information already present in the CV.

---

## Target User

A single user (the developer) running this locally on Windows 11. Not a multi-user or SaaS product.

---

## Tech Stack

| Layer | Choice | Rationale |
|---|---|---|
| Language | Python 3.11+ | Fast to build, strong ecosystem for PDF + AI |
| GUI | Tkinter (built-in) or CustomTkinter | Zero install friction; CustomTkinter for modern styling |
| PDF parsing | `pdfplumber` or `PyMuPDF (fitz)` | Reliable text extraction from PDFs |
| AI | Google Gemini API (`google-generativeai`) | User's stated choice |
| PDF export | `reportlab` or `WeasyPrint` | Programmatic PDF generation |
| Config | `python-dotenv` + `.env` file | API key management |
| Packaging | Single folder, run with `python main.py` | Local use only |

---

## Features

### F1 — CV Upload
- A file picker button in the GUI labelled "Attach CV (PDF)".
- Accepts `.pdf` files only.
- Displays the selected filename once chosen.
- On load, extracts and stores the text content from the PDF.

### F2 — Job Description Input
- A multi-line text area labelled "Job Requirements".
- User pastes the full job description text here.
- No character limit enforced at the UI level.

### F3 — CV Data Extraction
- On PDF load, `pdfplumber` (primary) extracts raw text.
- A light pre-processing step segments the CV into logical sections (e.g. Summary, Experience, Skills, Education) using heuristic heading detection.
- Extracted data is held in memory only; nothing is written to disk from this step.

### F4 — Gemini Analysis & CV Rewrite
- Triggered by a "Generate Tailored CV" button.
- Validates that both a CV and a job description are present before proceeding.
- Constructs a structured prompt that:
  - Provides the extracted CV text.
  - Provides the job description.
  - Instructs Gemini to rewrite the CV to maximize relevance to the job.
  - Explicitly instructs Gemini NOT to add skills or experience not present in the original CV.
  - Requests output in a consistent structured format (defined sections).
- Calls the Gemini API (model: `gemini-1.5-pro` or `gemini-2.0-flash`, configurable).
- Shows a loading/spinner state in the UI while waiting.

### F5 — PDF Export
- After a successful Gemini response, a "Download PDF" button becomes active.
- Clicking it opens a save-file dialog defaulting to `tailored_cv_<timestamp>.pdf`.
- The PDF is rendered from the Gemini output using a clean, professional single-column layout.
- Font: inter or similar clean sans-serif. Sections are clearly delineated.

### F6 — Configuration
- A `.env` file at the project root holds `GEMINI_API_KEY`.
- On startup, the app reads this file. If the key is missing, an error dialog is shown with instructions to add it.
- Optionally, a `config.py` holds the Gemini model name so it can be changed without touching core logic.

---

## UI Layout (Wireframe — text description)

```
+--------------------------------------------------+
|  CVmate                                          |
+--------------------------------------------------+
|                                                  |
|  [ Attach CV (PDF) ]   my_cv.pdf                 |
|                                                  |
|  Job Requirements:                               |
|  +--------------------------------------------+ |
|  |  (multi-line text area — paste here)       | |
|  |                                            | |
|  |                                            | |
|  +--------------------------------------------+ |
|                                                  |
|  [ Generate Tailored CV ]                        |
|                                                  |
|  Status: Ready / Processing... / Done            |
|                                                  |
|  [ Download PDF ]  (disabled until generation)  |
|                                                  |
+--------------------------------------------------+
```

---

## Prompt Engineering Strategy

The Gemini prompt will follow this structure:

1. **System instruction**: You are a professional CV writer. You must only use information from the provided CV. Do not invent skills, roles, or achievements.
2. **CV section**: Full extracted CV text.
3. **Job description section**: Full pasted job description.
4. **Task instruction**: Rewrite the CV to best match this job description. Prioritize relevant experience, use keywords from the job description naturally, and reorder/rephrase bullet points to highlight the most relevant work. Keep all sections (Summary, Experience, Skills, Education). Return the result as structured plain text with clear section headers.

---

## Data Flow

```
[User] --attach PDF--> [CV Parser] --extracted text--> [Memory]
[User] --paste job desc--> [Memory]
[User] --click Generate--> [Prompt Builder] --> [Gemini API]
                                                    |
                                               [Rewritten CV text]
                                                    |
                                             [PDF Renderer] --> [Save dialog] --> [PDF file]
```

---

## Error Handling

| Scenario | Behavior |
|---|---|
| No CV attached on Generate | Show inline warning: "Please attach your CV first." |
| Job description empty | Show inline warning: "Please paste the job description." |
| Missing API key on startup | Dialog: "GEMINI_API_KEY not found in .env. See README." |
| Gemini API error | Show error message in status bar with the error detail. |
| PDF parse failure (corrupt/scanned) | Show warning: "Could not extract text from this PDF. Try a text-based PDF." |

---

## Project Structure

```
CVmate/
├── main.py              # Entry point, launches GUI
├── gui.py               # Tkinter/CustomTkinter layout and event handlers
├── cv_parser.py         # PDF text extraction and section segmentation
├── gemini_client.py     # Gemini API wrapper and prompt builder
├── pdf_exporter.py      # Tailored CV → PDF renderer
├── config.py            # Model name, defaults
├── .env                 # GEMINI_API_KEY (not committed)
├── .env.example         # Template for the above
├── requirements.txt     # Python dependencies
└── PRD.md               # This file
```

---

## Milestones

| # | Milestone | Description |
|---|---|---|
| 1 | Project scaffold | Folder structure, venv, requirements.txt, .env setup |
| 2 | CV parser | PDF load + text extraction + section detection |
| 3 | GUI shell | Window, file picker, text area, buttons wired up |
| 4 | Gemini integration | Prompt builder + API call + response handling |
| 5 | PDF export | Render Gemini output to a clean PDF |
| 6 | Polish | Error states, loading indicator, styling |

---

## Open Questions / Future Ideas

- Cover letter generation (separate tab, same inputs).
- Multiple CV profiles (e.g. "engineering CV", "management CV").
- Side-by-side diff view showing what changed between original and tailored CV.
- Match score / gap analysis view before committing to the rewrite.
