# CVmate — MVP Execution Plan

> **Purpose:** This document is the authoritative execution guide for agents building CVmate.
> Read it fully before writing a single line of code. Each phase must be completed and
> verified before the next one starts. Do not skip ahead or combine phases.

---

## Locked Decisions (Do Not Re-evaluate)

These choices are final. Do not suggest alternatives or open them for discussion.

| Concern | Decision |
|---|---|
| Language | Python 3.11+ |
| GUI | `customtkinter` |
| PDF parsing | `pdfplumber` |
| AI model | `gemini-2.0-flash` (configurable via `config.py`) |
| PDF export | `reportlab` |
| Config | `python-dotenv` + `.env` |
| Entry point | `python main.py` |
| Platform | Windows 11 |

---

## Constraints for All Phases

- **No fabrication** — Gemini must be instructed to use only information from the CV.
- **No persistence** — nothing is written to disk except the final exported PDF.
- **No over-engineering** — no classes where functions suffice, no abstractions for hypothetical future features.
- **No comments** unless the WHY is non-obvious to a future reader.
- **No tests** — this is a local single-user tool; verify by running.
- Each module must be independently runnable with a `if __name__ == "__main__":` block for quick verification during development.

---

## Phase 0 — Scaffold

**Goal:** A runnable project skeleton with all dependencies declared and the environment ready.

### Tasks

1. Create `requirements.txt` with exact packages:
   ```
   customtkinter
   pdfplumber
   google-generativeai
   reportlab
   python-dotenv
   ```

2. Create `.env.example`:
   ```
   GEMINI_API_KEY=your-gemini-api-key-here
   ```

3. Create `config.py`:
   ```python
   GEMINI_MODEL = "gemini-2.0-flash"
   APP_TITLE = "CVmate"
   WINDOW_SIZE = "720x600"
   ```

4. Create empty module stubs (just a module docstring, no logic yet):
   - `main.py`
   - `gui.py`
   - `cv_parser.py`
   - `gemini_client.py`
   - `pdf_exporter.py`

5. Create `main.py` with a single call to launch the GUI (can show a blank window for now).

6. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

### Done When
- [ ] `python main.py` launches without errors (blank window is fine).
- [ ] All 5 module files exist.
- [ ] `requirements.txt` and `.env.example` exist at project root.
- [ ] `pip install -r requirements.txt` completes cleanly.

---

## Phase 1 — CV Parser

**Goal:** Given a path to a PDF file, extract clean text and segment it into named sections.

### File: `cv_parser.py`

#### Function: `extract_text(pdf_path: str) -> str`
- Use `pdfplumber` to open the PDF and concatenate text from all pages.
- Strip excessive whitespace between lines but preserve paragraph breaks.
- Raise `ValueError` with message `"Could not extract text from this PDF. Try a text-based PDF."` if the extracted text is empty or under 50 characters (likely a scanned image PDF).

#### Function: `segment_sections(text: str) -> dict[str, str]`
- Heuristically detect common CV section headings by scanning for lines that are:
  - All caps, OR
  - Followed by a blank line and match a known keyword list: `["summary", "experience", "education", "skills", "projects", "certifications", "languages", "objective"]`
- Return a dict: `{"SUMMARY": "...", "EXPERIENCE": "...", "SKILLS": "...", ...}`
- If no sections are detected, return `{"FULL_TEXT": text}` as fallback.

#### `__main__` block
- Accept a PDF path as `sys.argv[1]`.
- Print extracted text length and detected section keys.

### Done When
- [ ] `python cv_parser.py path/to/cv.pdf` prints section keys and char count without errors.
- [ ] A scanned/image PDF raises `ValueError` with the correct message.
- [ ] A multi-page PDF extracts text from all pages.

---

## Phase 2 — Gemini Client

**Goal:** Given CV text and a job description string, call the Gemini API and return a rewritten CV as plain text.

### File: `gemini_client.py`

#### Setup
- Load `GEMINI_API_KEY` from environment using `python-dotenv` at module import time.
- Raise `EnvironmentError` with message `"GEMINI_API_KEY not found in .env. See .env.example."` if the key is missing.
- Instantiate the Gemini client once at module level using `google.generativeai`.

#### Function: `build_prompt(cv_text: str, job_description: str) -> str`
- Construct and return the full prompt string using this exact structure:

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

#### Function: `generate_tailored_cv(cv_text: str, job_description: str) -> str`
- Call `build_prompt` to construct the prompt.
- Send to Gemini using `model.generate_content(prompt)`.
- Return the response text.
- Propagate any API exceptions — do not swallow them (the GUI layer handles display).

#### `__main__` block
- Load a sample CV text from a hardcoded short string and a sample job description.
- Call `generate_tailored_cv` and print the first 500 chars of the result.

### Done When
- [ ] `python gemini_client.py` prints a non-empty rewritten CV snippet.
- [ ] Missing `GEMINI_API_KEY` raises `EnvironmentError` with the correct message.
- [ ] The returned text contains recognizable section headers.

---

## Phase 3 — PDF Exporter

**Goal:** Given the plain-text output from Gemini, render and save a clean professional PDF.

### File: `pdf_exporter.py`

#### Layout Rules (hard rules, do not deviate)
- Page size: A4.
- Margins: 2cm all sides.
- Font: Helvetica (built-in reportlab font; no external font dependency).
- Section headers (`ALL-CAPS` lines): Bold, 11pt, 2pt space above, 1pt rule line below.
- Body text: Regular, 10pt, leading 14pt.
- No colours — black text on white only.
- No images, no sidebar, no columns — single-column flowing text.

#### Function: `export_pdf(cv_text: str, output_path: str) -> None`
- Parse `cv_text` line by line.
- Detect section headers: lines that are ALL-CAPS and non-empty.
- Render headers with the section header style; all other lines with body style.
- Blank lines in the input become a small vertical spacer (4pt).
- Save the PDF to `output_path`.
- Raise `IOError` if the file cannot be written (e.g., permission denied).

#### `__main__` block
- Use a hardcoded sample CV text (2-3 sections, a few bullet points).
- Export to `test_output.pdf` in the current directory.
- Print `"Exported to test_output.pdf"` on success.

### Done When
- [ ] `python pdf_exporter.py` creates `test_output.pdf` in the project folder.
- [ ] Opening the PDF shows clearly delineated sections with bold headers.
- [ ] Body text is readable at 10pt with correct line spacing.
- [ ] `test_output.pdf` is **not** committed — add it to `.gitignore`.

---

## Phase 4 — GUI

**Goal:** A working desktop window that wires all three modules together behind a clean interface.

### File: `gui.py`

#### Window Setup
- Use `customtkinter`. Set appearance mode `"dark"` and color theme `"blue"`.
- Window title: `"CVmate"`. Size: `720x600`. Non-resizable.

#### Layout (top to bottom, single column, padded 20px)

```
[ CVmate ]                              ← title label, large bold

[ Attach CV (PDF) ]  filename.pdf       ← button + label side by side

Job Requirements:                       ← section label
┌──────────────────────────────────┐
│  (scrollable text area, 10 rows) │    ← CTkTextbox
└──────────────────────────────────┘

[ Generate Tailored CV ]                ← primary action button

Status: Ready                           ← status label (updates dynamically)

[ Download PDF ]                        ← secondary button, DISABLED until generation
```

#### Event Handlers

**`on_attach_cv()`** — triggered by "Attach CV" button:
- Open a file dialog filtered to `.pdf` files only.
- If a file is selected:
  - Try `cv_parser.extract_text(path)` and store result in `self.cv_text`.
  - Update filename label to the selected file's basename.
  - Set status: `"CV loaded: {n} characters extracted."`
- On `ValueError` from parser: show status `"Error: Could not extract text from this PDF. Try a text-based PDF."` — do not crash.

**`on_generate()`** — triggered by "Generate Tailored CV" button:
- Validate: if `self.cv_text` is empty → status `"Please attach your CV first."`, return.
- Validate: if job description textarea is empty → status `"Please paste the job description."`, return.
- Disable both action buttons.
- Set status: `"Generating tailored CV… please wait."`
- Run `gemini_client.generate_tailored_cv(cv_text, job_desc)` in a **background thread** (use `threading.Thread`) to keep the UI responsive.
- On success: store result in `self.tailored_cv_text`, set status `"Done! Click Download PDF to save."`, enable Download button.
- On exception: set status `f"Error: {str(e)}"`, re-enable Generate button.

**`on_download_pdf()`** — triggered by "Download PDF" button:
- Open a save dialog with default filename `tailored_cv_{timestamp}.pdf`.
- Call `pdf_exporter.export_pdf(self.tailored_cv_text, chosen_path)`.
- On success: set status `"Saved to {chosen_path}"`.
- On `IOError`: set status `"Error saving file. Check permissions."`.

#### `__main__` block in `main.py`
```python
import gui
app = gui.App()
app.mainloop()
```

### Done When
- [ ] `python main.py` opens the window with correct layout.
- [ ] Attaching a valid PDF updates the filename label and status.
- [ ] Attaching a scanned PDF shows the correct error in the status bar without crashing.
- [ ] Clicking Generate without a CV or job description shows the correct inline warnings.
- [ ] Generate button runs without freezing the UI (window stays responsive).
- [ ] A completed generation enables the Download button.
- [ ] Downloading saves a readable PDF to the chosen path.
- [ ] Missing `.env` / API key shows the correct error in the status bar on first Generate click.

---

## Phase 5 — Integration & Polish

**Goal:** End-to-end smoke test and final UX hardening. No new features.

### Checklist

#### Startup guard
- In `main.py`, before launching the GUI, call `gemini_client` import to trigger the
  `EnvironmentError` check. If it fires, show a `CTkMessagebox` (or `tkinter.messagebox`)
  with the error text, then exit — do not silently continue to a broken state.

#### UX details
- The "Generate Tailored CV" button label changes to `"Generating…"` while the API call is in progress, and reverts to `"Generate Tailored CV"` when done.
- The "Attach CV" button remains functional at all times (user can swap CV mid-session).
- After a successful generation, if the user attaches a new CV or edits the job description, the Download button is disabled again and status resets to `"Ready"`.
- Status label text is left-aligned, truncated with `"…"` if too long for the window width.

#### Final file hygiene
- `test_output.pdf` is in `.gitignore`.
- `.env` is in `.gitignore`.
- `.env.example` is committed and contains a clear placeholder.
- All 5 module files are present and import without errors.

#### End-to-end test (manual, run this yourself)
1. `python main.py` — window opens, no errors.
2. Click "Attach CV" — file dialog opens, select a real PDF CV.
3. Status updates with character count.
4. Paste a real job description into the text area.
5. Click "Generate Tailored CV" — status shows "Generating…", window stays responsive.
6. Status updates to "Done!" — Download button becomes active.
7. Click "Download PDF" — save dialog opens, save to desktop.
8. Open the saved PDF — readable, professional layout, correct sections.

### Done When
- [ ] All 8 steps in the end-to-end test pass.
- [ ] No unhandled exceptions visible in the terminal during normal use.
- [ ] `.gitignore` covers `.env` and `test_output.pdf`.

---

## File Checklist (final state)

```
CVmate/
├── main.py              ← entry point, startup guard, launches gui.App()
├── gui.py               ← CustomTkinter layout + all event handlers
├── cv_parser.py         ← extract_text(), segment_sections()
├── gemini_client.py     ← build_prompt(), generate_tailored_cv()
├── pdf_exporter.py      ← export_pdf()
├── config.py            ← GEMINI_MODEL, APP_TITLE, WINDOW_SIZE
├── requirements.txt     ← 5 packages, no version pins needed for MVP
├── .env                 ← GEMINI_API_KEY (gitignored)
├── .env.example         ← committed template
├── .gitignore           ← covers .env, test_output.pdf, __pycache__, venv/
├── PRD.md               ← product requirements
└── MVP-PLAN.md          ← this file
```

---

## Execution Order Summary

```
Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5
Scaffold   Parser    Gemini    Export    GUI       Polish
           ↓          ↓         ↓         ↓
         verify     verify    verify    verify
         alone      alone     alone     e2e
```

Each phase must pass its **Done When** checklist before the next phase begins.
The GUI (Phase 4) should only be built after Phases 1–3 pass — it is the assembly
layer, not the logic layer.
