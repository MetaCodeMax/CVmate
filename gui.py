"""CustomTkinter GUI: layout and event handlers for CVmate."""

import os
import queue
import threading
from datetime import datetime
from tkinter import filedialog

import customtkinter as ctk

import cv_parser
import gemini_client
import pdf_exporter
from config import APP_TITLE, WINDOW_SIZE

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.cv_text = ""
        self.tailored_cv_text = ""
        self.cv_path = ""
        self._result_queue = queue.Queue()

        self.title(APP_TITLE)
        self.geometry(WINDOW_SIZE)
        self.resizable(False, False)

        self._build_layout()
        self.after(100, self._poll_result_queue)

    def _build_layout(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            container, text=APP_TITLE, font=ctk.CTkFont(size=28, weight="bold")
        ).pack(anchor="w")

        attach_row = ctk.CTkFrame(container, fg_color="transparent")
        attach_row.pack(fill="x", pady=(16, 8))
        self.attach_button = ctk.CTkButton(
            attach_row, text="Attach CV (PDF)", width=160, command=self.on_attach_cv
        )
        self.attach_button.pack(side="left")
        self.filename_label = ctk.CTkLabel(
            attach_row, text="No file selected", text_color="gray70"
        )
        self.filename_label.pack(side="left", padx=12)

        ctk.CTkLabel(container, text="Job Requirements:").pack(anchor="w", pady=(8, 4))
        self.job_textbox = ctk.CTkTextbox(container, height=240, wrap="word")
        self.job_textbox.pack(fill="both", expand=True)
        self.job_textbox.bind("<KeyRelease>", self._on_job_edit)

        self.generate_button = ctk.CTkButton(
            container, text="Generate Tailored CV", command=self.on_generate
        )
        self.generate_button.pack(fill="x", pady=(12, 8))

        self.status_label = ctk.CTkLabel(
            container, text="Status: Ready", anchor="w", justify="left"
        )
        self.status_label.pack(fill="x")

        self.download_button = ctk.CTkButton(
            container,
            text="Download PDF",
            command=self.on_download_pdf,
            state="disabled",
            fg_color="gray30",
        )
        self.download_button.pack(fill="x", pady=(8, 0))

    def _set_status(self, text):
        if len(text) > 90:
            text = text[:89] + "…"
        self.status_label.configure(text=f"Status: {text}")

    def _reset_generation(self):
        self.tailored_cv_text = ""
        self.download_button.configure(state="disabled", fg_color="gray30")

    def _on_job_edit(self, _event=None):
        if self.tailored_cv_text:
            self._reset_generation()
            self._set_status("Ready")

    def on_attach_cv(self):
        path = filedialog.askopenfilename(
            title="Select your CV", filetypes=[("PDF files", "*.pdf")]
        )
        if not path:
            return
        try:
            self.cv_text = cv_parser.extract_text(path)
            self.cv_path = path
            self.filename_label.configure(text=os.path.basename(path))
            self._reset_generation()
            self._set_status(f"CV loaded: {len(self.cv_text)} characters extracted.")
        except ValueError as e:
            self.cv_text = ""
            self.cv_path = ""
            self.filename_label.configure(text="No file selected")
            self._set_status(f"Error: {e}")

    def on_generate(self):
        if not self.cv_text:
            self._set_status("Please attach your CV first.")
            return
        job_desc = self.job_textbox.get("1.0", "end").strip()
        if not job_desc:
            self._set_status("Please paste the job description.")
            return

        self.generate_button.configure(state="disabled", text="Generating…")
        self.attach_button.configure(state="normal")
        self.download_button.configure(state="disabled", fg_color="gray30")
        self._set_status("Generating tailored CV… please wait.")

        thread = threading.Thread(
            target=self._generate_worker, args=(self.cv_text, job_desc), daemon=True
        )
        thread.start()

    def _generate_worker(self, cv_text, job_desc):
        try:
            result = gemini_client.generate_tailored_cv(cv_text, job_desc)
            self._result_queue.put(("success", result))
        except Exception as e:
            self._result_queue.put(("error", str(e)))

    def _poll_result_queue(self):
        try:
            while True:
                kind, payload = self._result_queue.get_nowait()
                if kind == "success":
                    self._on_generate_success(payload)
                else:
                    self._on_generate_error(payload)
        except queue.Empty:
            pass
        self.after(100, self._poll_result_queue)

    def _on_generate_success(self, result):
        self.tailored_cv_text = result
        self.generate_button.configure(state="normal", text="Generate Tailored CV")
        self.download_button.configure(state="normal", fg_color=["#3a7ebf", "#1f538d"])
        self._set_status("Done! Click Download PDF to save.")

    def _on_generate_error(self, message):
        self.generate_button.configure(state="normal", text="Generate Tailored CV")
        self._set_status(f"Error: {message}")

    def on_download_pdf(self):
        if not self.tailored_cv_text:
            return
        default_name = f"tailored_cv_{datetime.now():%Y%m%d_%H%M%S}.pdf"
        path = filedialog.asksaveasfilename(
            title="Save tailored CV",
            defaultextension=".pdf",
            initialfile=default_name,
            filetypes=[("PDF files", "*.pdf")],
        )
        if not path:
            return
        try:
            pdf_exporter.export_pdf(self.tailored_cv_text, path)
            self._set_status(f"Saved to {path}")
        except IOError:
            self._set_status("Error saving file. Check permissions.")
