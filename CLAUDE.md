# CVmate — Agent Reference

## What This Project Is

CVmate is a local Windows 11 desktop tool. The user attaches their CV as a PDF, pastes a job description, and clicks Generate. Gemini rewrites the CV to match the job, then the user downloads a PDF. Single session, no persistence, no database, no accounts.

Full requirements: `PRD.md`. Execution phases: `MVP-PLAN.md`.

---

## Tech Stack (Final — Do Not Suggest Alternatives)

| Layer | Library | Import |
|---|---|---|
| GUI | `customtkinter` | `import customtkinter as ctk` |
| PDF parse | `pdfplumber` | `import pdfplumber` |
| AI | `google-generativeai` | `import google.generativeai as genai` |
| PDF export | `reportlab` | `from reportlab.lib...` |
| Config | `python-dotenv` | `from dotenv import load_dotenv` |

Gemini model: `gemini-2.0-flash` — defined in `config.py`, not hardcoded elsewhere.

---

## Project Structure

```
CVmate/
├── main.py           # Entry point. Startup API key check, then launches gui.App()
├── gui.py            # All CustomTkinter layout and event handlers. Class: App(ctk.CTk)
├── cv_parser.py      # extract_text(pdf_path) → str, segment_sections(text) → dict
├── gemini_client.py  # build_prompt(cv, jd) → str, generate_tailored_cv(cv, jd) → str
├── pdf_exporter.py   # export_pdf(cv_text, output_path) → None
├── config.py         # GEMINI_MODEL, APP_TITLE, WINDOW_SIZE constants
├── requirements.txt  # 5 packages, no version pins
├── .env              # GEMINI_API_KEY=... (gitignored, never read or edit)
├── .env.example      # Committed placeholder template
├── .gitignore        # Covers .env, test_output.pdf, __pycache__, venv/
├── PRD.md            # Product requirements
└── MVP-PLAN.md       # Phase-by-phase build plan with Done-When checklists
```

Each module (except `main.py` and `gui.py`) has a `if __name__ == "__main__":` block so it can be verified in isolation without the GUI.

---

## Module Responsibilities

### `config.py`
Constants only. No logic, no imports from this project.
```python
GEMINI_MODEL = "gemini-2.0-flash"
APP_TITLE = "CVmate"
WINDOW_SIZE = "720x600"
```

### `cv_parser.py`
- `extract_text(pdf_path: str) -> str` — uses `pdfplumber`, raises `ValueError` if text is empty/under 50 chars (scanned PDF).
- `segment_sections(text: str) -> dict[str, str]` — heuristic split on ALL-CAPS headings or known keywords. Falls back to `{"FULL_TEXT": text}`.

### `gemini_client.py`
- Loads `.env` and instantiates the Gemini client at module level.
- Raises `EnvironmentError` if `GEMINI_API_KEY` is missing.
- `build_prompt(cv_text, job_description) -> str` — assembles the structured prompt.
- `generate_tailored_cv(cv_text, job_description) -> str` — calls the API, returns raw text. Does NOT catch exceptions (GUI handles display).

### `pdf_exporter.py`
- `export_pdf(cv_text: str, output_path: str) -> None` — A4, Helvetica, black/white, single column.
- ALL-CAPS lines → bold 11pt section headers with a rule below.
- Body text → regular 10pt, leading 14pt.
- Raises `IOError` on write failure.

### `gui.py`
- One class: `App(ctk.CTk)`. Appearance: dark mode, blue theme.
- Window: 720×600, non-resizable.
- Three state variables: `self.cv_text`, `self.tailored_cv_text`, `self.cv_path`.
- Gemini call runs in `threading.Thread` — UI must never freeze.
- Download button is disabled until `self.tailored_cv_text` is populated.
- Re-attaching a CV or editing the job description resets `tailored_cv_text` and disables Download.

### `main.py`
```python
from dotenv import load_dotenv
load_dotenv()
import gemini_client  # triggers EnvironmentError if key missing
import gui
app = gui.App()
app.mainloop()
```
Wrap the import in a try/except: show `tkinter.messagebox.showerror` and `sys.exit(1)` if the key is missing.

---

## Prompt Structure (Exact — Do Not Reword)

```
SYSTEM:
You are a professional CV writer. You must only use information already present in the
provided CV. Do not invent, add, or imply any skills, roles, tools, or achievements
that are not explicitly stated in the CV.

CV:
{cv_text}

JOB DESCRIPTION:
{job_description}

TASK:
Rewrite the CV above to best match the job description. Follow these rules:
- Prioritize and lead with experience most relevant to the job.
- Use keywords from the job description naturally where they match existing experience.
- Reorder and rephrase bullet points to highlight the most relevant work first.
- Keep all original sections: Summary, Experience, Skills, Education (and any others present).
- Do not add any experience, skills, or tools not present in the original CV.
- Return the result as plain text with clear ALL-CAPS section headers.
- Do not include any commentary, preamble, or explanation — output only the CV.
```

---

## Error Handling Contract

| Trigger | Module that raises | What GUI shows |
|---|---|---|
| Scanned/empty PDF | `cv_parser` raises `ValueError` | Status label: error message |
| Missing API key | `gemini_client` raises `EnvironmentError` | Messagebox on startup, then exit |
| Gemini API failure | `gemini_client` propagates exception | Status label: `f"Error: {e}"` |
| PDF write failure | `pdf_exporter` raises `IOError` | Status label: "Error saving file. Check permissions." |
| Generate clicked, no CV | GUI validates | Status label: "Please attach your CV first." |
| Generate clicked, no JD | GUI validates | Status label: "Please paste the job description." |

---

## PDF Export Layout Rules

- Page: A4
- Margins: 2cm all sides
- Font: Helvetica (built-in, no external font files)
- Section headers (ALL-CAPS lines): Bold, 11pt, horizontal rule below
- Body: Regular, 10pt, leading 14pt
- Blank input lines → 4pt vertical spacer
- No colour, no images, no columns

---

## Code Conventions

- No comments unless the WHY is genuinely non-obvious.
- No classes where module-level functions suffice (except `App` in `gui.py`).
- No error handling for scenarios that cannot happen at runtime.
- No features, flags, or abstractions beyond the MVP scope.
- `config.py` is the only place model names and UI constants live — import from there.
- Never hardcode `"gemini-2.0-flash"` anywhere except `config.py`.

---

## Running the App

```bash
# First time
pip install -r requirements.txt
cp .env.example .env
# Add your GEMINI_API_KEY to .env

# Every time
python main.py
```

## Verifying a Module in Isolation

```bash
python cv_parser.py path/to/cv.pdf
python gemini_client.py
python pdf_exporter.py
```

Each prints a confirmation and exits cleanly when working correctly.
