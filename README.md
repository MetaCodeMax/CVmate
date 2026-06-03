# CVmate

A local Windows desktop tool that tailors your CV to a specific job. Attach your CV as a
PDF, paste a job description, click **Generate**, and CVmate uses Google Gemini to rewrite
the CV to emphasize the experience most relevant to that role — then exports a clean PDF.

Everything runs locally. Nothing is stored, no accounts, no database. The only data that
leaves your machine is the CV text and job description sent to the Gemini API on Generate.

> **No fabrication:** Gemini is explicitly instructed to use only information already
> present in your CV — it reorders and rephrases, it does not invent skills or experience.

---

## Features

- **Attach CV (PDF)** — extracts text from text-based PDFs (`pdfplumber`).
- **Paste job description** — free-form text, no length limit.
- **Generate tailored CV** — Gemini rewrites the CV to match the job (runs in a background
  thread, so the UI never freezes).
- **Download PDF** — clean, single-column A4 layout (`reportlab`).

---

## Requirements

- **Windows 11**
- **Python 3.11+** (developed and verified on 3.13)
- A **Google Gemini API key** — free from [Google AI Studio](https://aistudio.google.com/apikey)

---

## Setup

```powershell
# 1. Clone
git clone https://github.com/MetaCodeMax/CVmate.git
cd CVmate

# 2. (Recommended) create a virtual environment
py -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install dependencies
py -m pip install -r requirements.txt

# 4. Configure your API key
copy .env.example .env
#    then open .env and set:
#    GEMINI_API_KEY=your-real-key-here
```

> The `py` launcher selects your Python 3.11+ interpreter. If `python` on your machine
> points at the Microsoft Store stub, use `py` instead (as shown above).

---

## Running

```powershell
py main.py
```

On startup the app verifies your API key. If `GEMINI_API_KEY` is missing, you'll get a
clear error dialog instead of a broken window.

### Using it

1. Click **Attach CV (PDF)** and select a text-based PDF.
2. Paste the job description into the text area.
3. Click **Generate Tailored CV** and wait for the status to read *Done!*
4. Click **Download PDF** and choose where to save.

---

## Project structure

```
CVmate/
├── main.py            # Entry point: API-key startup guard, then launches the GUI
├── gui.py             # CustomTkinter window + event handlers (App class)
├── cv_parser.py       # extract_text(), segment_sections()
├── gemini_client.py   # build_prompt(), generate_tailored_cv()
├── pdf_exporter.py    # export_pdf()
├── config.py          # GEMINI_MODEL, APP_TITLE, WINDOW_SIZE
├── requirements.txt   # 5 dependencies
├── .env.example       # Template — copy to .env and add your key
├── PRD.md             # Product requirements
└── MVP-PLAN.md        # Phase-by-phase build plan
```

Each logic module (`cv_parser`, `gemini_client`, `pdf_exporter`) has a `__main__` block so
it can be verified on its own:

```powershell
py cv_parser.py path\to\cv.pdf
py gemini_client.py
py pdf_exporter.py
```

---

## Configuration

`config.py` holds the model name and UI constants — change the Gemini model in one place:

```python
GEMINI_MODEL = "gemini-2.0-flash"
```

---

## Security notes

- **`.env` is gitignored** and must never be committed — it holds your API key.
- `.env.example` is the committed template and contains only a placeholder.
- If your key is ever exposed, revoke it at
  [Google AI Studio](https://aistudio.google.com/apikey) and generate a new one.

---

## Tech stack

| Layer | Library |
|---|---|
| GUI | `customtkinter` |
| PDF parsing | `pdfplumber` |
| AI | `google-generativeai` (Gemini) |
| PDF export | `reportlab` |
| Config | `python-dotenv` |

---

## License

Personal project — no license specified. All rights reserved by the author.
