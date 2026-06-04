# Changelog

All notable changes to CVmate are documented here. This project uses
[semantic versioning](https://semver.org/).

---

## v1.0.0 — Standalone app for everyone (no terminal required)

This release makes CVmate usable by people who don't code and don't want to touch a
command line. Previously you had to install Python, install dependencies, and run the app
from a terminal. Now you just **download one file and double-click it.**

### A friendlier way in

- **Single-file executable.** CVmate is now packaged as `CVmate.exe` — a self-contained
  Windows program with Python and every dependency bundled inside. No installs, no setup,
  no terminal. Download it from the
  [Releases page](https://github.com/MetaCodeMax/CVmate/releases) and double-click.
- **Guided first-run key setup.** On first launch a friendly window walks you through
  getting your free Google Gemini API key:
  1. Click **Open Google AI Studio** — your browser opens to the right page.
  2. Sign in, create a key, copy it.
  3. Paste it in and click **Save & Continue**.
  The key is checked on the spot and saved locally to `%APPDATA%\CVmate\config.json`, so
  you only do this once. No editing of config files, no `.env`, no terminal.
- **Change your key any time** with the **API Key** button in the top-right of the window.
- **Make it feel like a real app.** Right-click `CVmate.exe` → *Send to → Desktop (create
  shortcut)* or *Pin to Start*, and launch it like any other program.

### ⚠️ About the "unknown publisher" warning

Because `CVmate.exe` is **not code-signed** (a code-signing certificate is a paid product),
Windows SmartScreen will show a blue warning the first time you run it:

> **Windows protected your PC**

This is expected for any unsigned app — it does **not** mean the program is unsafe. To run
it: click **More info**, then **Run anyway**. You only need to do this once per machine.

If you'd rather avoid the warning entirely, run the app from source instead (see the
README's *Run from source* section) — that path has no SmartScreen prompt.

### Under the hood

- Deferred the API-key check from import time to runtime, so the app can launch and prompt
  for a key instead of crashing when one isn't set.
- New `key_store.py` resolves and persists the key (`%APPDATA%` config, with `.env`/env
  override preserved for developers).
- New `gemini_client.configure()` / `validate_api_key()` for runtime key wiring and instant
  validation feedback in the setup dialog.
- Build tooling: `build.bat` (one-click build) and `CVmate.spec` (PyInstaller bundle).

### Privacy unchanged

Your API key stays on your machine. The only data that ever leaves your computer is the CV
text and job description sent to Google Gemini when you click **Generate** — same as before.

---

## v0.1.0 — MVP

The original working version: a CustomTkinter desktop GUI that extracts text from a PDF CV,
sends it with a job description to Google Gemini for ATS-focused tailoring (with genuine
keyword matches rendered in **bold**), and exports a clean single-column A4 PDF. Run from
source with Python. Tagged as a stable rollback point.
