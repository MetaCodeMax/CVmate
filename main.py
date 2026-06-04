"""Entry point for CVmate. Loads the dev .env, then launches the GUI."""

from dotenv import load_dotenv

load_dotenv(override=True)

import gui

if __name__ == "__main__":
    app = gui.App()
    app.mainloop()
