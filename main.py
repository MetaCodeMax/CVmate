"""Entry point for CVmate. Verifies the API key, then launches the GUI."""

import sys
from tkinter import messagebox

from dotenv import load_dotenv

load_dotenv()

try:
    import gemini_client  # noqa: F401  triggers EnvironmentError if key missing
except EnvironmentError as e:
    messagebox.showerror("CVmate — Configuration Error", str(e))
    sys.exit(1)

import gui

if __name__ == "__main__":
    app = gui.App()
    app.mainloop()
