"""Entry point for CVmate.

Loads any developer .env, then launches the GUI. The Gemini API key is resolved
at runtime by the GUI (from %APPDATA% or its first-run dialog), so a missing key
no longer prevents the app from starting.
"""

from dotenv import load_dotenv

load_dotenv(override=True)

import gui

if __name__ == "__main__":
    app = gui.App()
    app.mainloop()
