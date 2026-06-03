"""Drive the real CVmate GUI through the full flow, capturing a screenshot at each stage.

Bypasses only the native file dialogs (monkeypatched to fixed paths) so the actual
event handlers, threading, Gemini call, and PDF export all run for real.
"""

import os
import sys
import time
from tkinter import filedialog

from PIL import ImageGrab

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

SAMPLE_CV = os.path.join(HERE, "sample_cv.pdf")
OUTPUT_PDF = os.path.join(HERE, "tailored_cv_output.pdf")

JOB_DESCRIPTION = (
    "We are hiring a Backend Python Engineer to design and scale REST APIs. "
    "You will work with Python, Docker, and SQL databases, and collaborate with "
    "a small team. Experience mentoring junior engineers and writing tests is a "
    "strong plus. Familiarity with React for occasional dashboard work is welcome."
)

import gui  # noqa: E402


def shot(app, name):
    app.update_idletasks()
    app.update()
    time.sleep(0.4)
    app.lift()
    app.attributes("-topmost", True)
    app.update()
    time.sleep(0.3)
    x, y = app.winfo_rootx(), app.winfo_rooty()
    w, h = app.winfo_width(), app.winfo_height()
    # include the title bar (~32px) above the client area
    bbox = (x, max(0, y - 32), x + w, y + h)
    img = ImageGrab.grab(bbox)
    path = os.path.join(HERE, name)
    img.save(path)
    app.attributes("-topmost", False)
    print(f"  saved {name}  ({img.size[0]}x{img.size[1]})")


def main():
    app = gui.App()
    app.update()
    time.sleep(0.5)

    print("Stage 1: initial window")
    shot(app, "01_initial.png")

    print("Stage 2: attach CV")
    filedialog.askopenfilename = lambda *a, **k: SAMPLE_CV
    app.on_attach_cv()
    shot(app, "02_cv_attached.png")

    print("Stage 3: paste job description")
    app.job_textbox.insert("1.0", JOB_DESCRIPTION)
    shot(app, "03_job_pasted.png")

    print("Stage 4: generating (background thread)")
    app.on_generate()
    app.update()
    shot(app, "04_generating.png")

    print("Stage 5: waiting for Gemini result...")
    deadline = time.time() + 60
    while time.time() < deadline:
        app.update()
        if app.tailored_cv_text or app.status_label.cget("text").startswith("Status: Error"):
            break
        time.sleep(0.1)
    shot(app, "05_done.png")

    status = app.status_label.cget("text")
    if not app.tailored_cv_text:
        print("  GENERATION FAILED:", status)
        app.destroy()
        sys.exit(1)
    print("  generated", len(app.tailored_cv_text), "chars")

    print("Stage 6: download PDF")
    filedialog.asksaveasfilename = lambda *a, **k: OUTPUT_PDF
    app.on_download_pdf()
    shot(app, "06_saved.png")
    print("  saved PDF:", os.path.getsize(OUTPUT_PDF), "bytes")

    # save the tailored text too, for the README/showcase
    with open(os.path.join(HERE, "tailored_cv_output.txt"), "w", encoding="utf-8") as f:
        f.write(app.tailored_cv_text)

    app.destroy()
    print("SHOWCASE COMPLETE")


if __name__ == "__main__":
    main()
