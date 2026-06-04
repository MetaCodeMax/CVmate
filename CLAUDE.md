# CVmate — Agent Reference

## What This Project Is

CVmate is a local Windows 11 desktop tool. The user attaches their CV as a PDF, pastes a job description, and clicks Generate. Gemini rewrites the CV to match the job, then the user downloads a PDF. Single session, no database, no accounts. The only persisted state is the user's Gemini API key (see Project Structure). Ships as a one-file `dist\CVmate.exe` (PyInstaller) so non-technical users never touch a terminal.

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
| Packaging | `pyinstaller` (build-time only, not in requirements.txt) | — |

Gemini model: `gemini-flash-latest` — defined in `config.py`, not hardcoded elsewhere.
(Was `gemini-2.0-flash`; that model returns 429 on the free tier, so the constant moved to
`gemini-flash-latest`.)

---

## Project Structure

```
CVmate/
├── main.py           # Entry point. Loads dev .env, launches gui.App() (no key check)
├── gui.py            # All CustomTkinter layout, first-run API-key dialog, handlers. Class: App(ctk.CTk)
├── cv_parser.py      # extract_text(pdf_path) → str, segment_sections(text) → dict
├── gemini_client.py  # configure(key), validate_api_key(key), build_prompt(cv, jd), generate_tailored_cv(cv, jd)
├── key_store.py      # get_api_key() / save_api_key(key) — %APPDATA%\CVmate\config.json
├── pdf_exporter.py   # export_pdf(cv_text, output_path) → None
├── config.py         # GEMINI_MODEL, APP_TITLE, WINDOW_SIZE, AI_STUDIO_URL constants
├── requirements.txt  # 5 runtime packages, no version pins
├── build.bat         # One-click PyInstaller build → dist\CVmate.exe
├── CVmate.spec       # PyInstaller one-file bundle spec
├── .env              # GEMINI_API_KEY=... (gitignored, never read or edit; optional dev override)
├── .env.example      # Committed placeholder template
├── .gitignore        # Covers .env, build/, dist/, test_output.pdf, __pycache__, venv/
├── PRD.md            # Product requirements
└── MVP-PLAN.md       # Phase-by-phase build plan with Done-When checklists
```

Each module (except `main.py` and `gui.py`) has a `if __name__ == "__main__":` block so it can be verified in isolation without the GUI.

**API key persistence:** the packaged app saves the key to `%APPDATA%\CVmate\config.json`
via the first-run dialog. This is the one allowed on-disk state besides the exported PDF —
it is config, not user data, and is required for the no-terminal `.exe` experience. The key
is never committed and `key_store.get_api_key()` still lets `GEMINI_API_KEY` (env/`.env`)
take precedence for development.

---

## Module Responsibilities

### `config.py`
Constants only. No logic, no imports from this project.
```python
GEMINI_MODEL = "gemini-flash-latest"
APP_TITLE = "CVmate"
WINDOW_SIZE = "720x600"
AI_STUDIO_URL = "https://aistudio.google.com/apikey"
```

### `key_store.py`
- `get_api_key() -> str | None` — resolves the key: `GEMINI_API_KEY` env/`.env` first, then
  `%APPDATA%\CVmate\config.json`. Returns `None` if neither is set.
- `save_api_key(key) -> None` — writes the key to `config.json` (creates the dir).
- `config_path() -> str` — the config file path, for diagnostics.

### `cv_parser.py`
- `extract_text(pdf_path: str) -> str` — uses `pdfplumber`, raises `ValueError` if text is empty/under 50 chars (scanned PDF).
- `segment_sections(text: str) -> dict[str, str]` — heuristic split on ALL-CAPS headings or known keywords. Falls back to `{"FULL_TEXT": text}`.

### `gemini_client.py`
- Importing the module never fails (no key check at import) — the GUI supplies the key at runtime.
- `configure(api_key) -> None` — points the SDK at the key and builds the model. Call once before generating.
- `is_configured() -> bool` — whether `configure()` has run; the GUI guards Generate on this.
- `validate_api_key(api_key) -> bool` — lightweight auth check (lists models) for the first-run dialog; no generation quota used.
- `build_prompt(cv_text, job_description) -> str` — assembles the structured prompt.
- `generate_tailored_cv(cv_text, job_description) -> str` — calls the API, returns raw text. Raises `RuntimeError` if not configured. Does NOT catch API exceptions (GUI handles display).

### `pdf_exporter.py`
- `export_pdf(cv_text: str, output_path: str) -> None` — A4, Helvetica, black/white, single column.
- ALL-CAPS lines → bold 11pt section headers with a rule below.
- Body text → regular 10pt, leading 14pt.
- `**double asterisks**` in body text → rendered as inline bold (Helvetica-Bold 10pt), used
  for keyword emphasis from the prompt. Word-wrapping handles mixed regular/bold runs.
- Raises `IOError` on write failure.

### `gui.py`
- One class: `App(ctk.CTk)`. Appearance: dark mode, blue theme.
- Window: 720×600, non-resizable. Header row has an **API Key** button to reopen the dialog any time.
- Three state variables: `self.cv_text`, `self.tailored_cv_text`, `self.cv_path`.
- On startup (`_ensure_api_key`) resolves the key via `key_store`; if present calls
  `gemini_client.configure()`, otherwise opens the first-run dialog (`_prompt_api_key`).
- `_prompt_api_key` — modal `CTkToplevel`: guided steps, an "Open Google AI Studio" button
  (`webbrowser.open(AI_STUDIO_URL)`), a paste box. On Save it validates the key on a worker
  thread (UI never freezes), then `key_store.save_api_key()` + `gemini_client.configure()`.
- `on_generate` guards on `gemini_client.is_configured()` — reopens the dialog if no key.
- Gemini call runs in `threading.Thread`; results returned via `queue.Queue` polled on the
  main thread (`_poll_result_queue`). Never call `self.after()` from a worker thread.
- Download button is disabled until `self.tailored_cv_text` is populated.
- Re-attaching a CV or editing the job description resets `tailored_cv_text` and disables Download.

### `main.py`
```python
from dotenv import load_dotenv
load_dotenv(override=True)
import gui
app = gui.App()
app.mainloop()
```
No key check here — the GUI resolves the key at runtime (saved config or first-run dialog),
so a missing key no longer blocks startup. `override=True` makes a dev `.env` authoritative
over a stale OS env var.

---

## Prompt Structure

The full prompt lives in `gemini_client.build_prompt()` — that function is the single source
of truth; do not duplicate the prompt text elsewhere (it drifted once and caused bugs). Its
design, which must be preserved when editing:

- **Role:** expert resume writer + ATS optimization specialist (directive, not timid).
- **Truthfulness block:** may rephrase/reframe/reorder/emphasize and adopt the job's
  terminology for genuine experience; must NOT invent skills, tools, employers, titles,
  dates, certifications, or metrics. This is non-negotiable.
- **Step 1 — silent analysis:** extract the target title, must-have skills/tools, and the
  employer's recurring keywords.
- **Step 2 — rewrite:** targeted SUMMARY for the exact role; EXPERIENCE bullets reordered by
  relevance, action-verb-first, mirroring the job's wording, real metrics kept, employers/
  titles/dates unchanged; SKILLS reordered so job-matched skills lead; other sections kept.
- **Keyword emphasis:** wrap phrases that are BOTH in the CV AND a job requirement in
  `**double asterisks**`. The PDF exporter renders these as bold inline. Only genuine matches.
- **Output:** plain text, ALL-CAPS section headers, bullets start with `- `, no commentary.

---

## Error Handling Contract

| Trigger | Module that raises | What GUI shows |
|---|---|---|
| Scanned/empty PDF | `cv_parser` raises `ValueError` | Status label: error message |
| No API key on startup / Generate | GUI checks `key_store` / `is_configured()` | First-run dialog opens to enter & save a key |
| Invalid key entered in dialog | `gemini_client.validate_api_key()` returns False | Dialog inline: "That key didn't work — check it and try again." |
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
- Inline `**bold**` keyword emphasis: Helvetica-Bold 10pt within body lines
- Blank input lines → 4pt vertical spacer
- No colour, no images, no columns

---

## Code Conventions

- No comments unless the WHY is genuinely non-obvious.
- No classes where module-level functions suffice (except `App` in `gui.py`).
- No error handling for scenarios that cannot happen at runtime.
- No features, flags, or abstractions beyond the MVP scope.
- `config.py` is the only place model names and UI constants live — import from there.
- Never hardcode the model name anywhere except `config.py`.

---

## Running the App

```powershell
# First time
py -m pip install -r requirements.txt

# Every time
py main.py
```

On first run the GUI prompts for a Gemini API key and saves it to `%APPDATA%\CVmate`.
A dev `.env` (`copy .env.example .env`, then set `GEMINI_API_KEY=...`) is optional and
overrides the saved key.

## Building the .exe

```powershell
.\build.bat        # installs PyInstaller, bundles per CVmate.spec → dist\CVmate.exe
```

Distribute `dist\CVmate.exe` via a GitHub Release (`gh release create ... dist\CVmate.exe`).
Do not commit the binary — `build/` and `dist/` are gitignored.

## Verifying a Module in Isolation

```bash
python cv_parser.py path/to/cv.pdf
python gemini_client.py
python pdf_exporter.py
```

Each prints a confirmation and exits cleanly when working correctly.
