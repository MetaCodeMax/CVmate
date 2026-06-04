"""CustomTkinter GUI: layout and event handlers for CVmate."""

import os
import queue
import threading
import webbrowser
from datetime import datetime
from tkinter import filedialog

import customtkinter as ctk

import cv_parser
import gemini_client
import key_store
import pdf_exporter
from config import AI_STUDIO_URL, APP_TITLE, WINDOW_SIZE

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
        self.after(200, self._ensure_api_key)

    def _build_layout(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        header_row = ctk.CTkFrame(container, fg_color="transparent")
        header_row.pack(fill="x")
        ctk.CTkLabel(
            header_row, text=APP_TITLE, font=ctk.CTkFont(size=28, weight="bold")
        ).pack(side="left")
        ctk.CTkButton(
            header_row,
            text="API Key",
            width=80,
            fg_color="gray30",
            command=self._prompt_api_key,
        ).pack(side="right")

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

    def _ensure_api_key(self):
        key = key_store.get_api_key()
        if key:
            gemini_client.configure(key)
            self._set_status("Ready")
        else:
            self._prompt_api_key()

    def _prompt_api_key(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Set up your Gemini API key")
        dialog.geometry("540x380")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.after(250, dialog.grab_set)

        frame = ctk.CTkFrame(dialog, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=24, pady=24)

        ctk.CTkLabel(
            frame,
            text="Connect your Gemini API key",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(anchor="w")
        ctk.CTkLabel(
            frame,
            justify="left",
            wraplength=480,
            text=(
                "CVmate uses Google Gemini to tailor your CV. A key is free.\n\n"
                "1.  Click the button below to open Google AI Studio.\n"
                '2.  Sign in, click "Create API key", and copy the key.\n'
                "3.  Paste it here and click Save. It is stored only on this PC."
            ),
        ).pack(anchor="w", pady=(8, 12))

        ctk.CTkButton(
            frame,
            text="Open Google AI Studio  ↗",
            command=lambda: webbrowser.open(AI_STUDIO_URL),
        ).pack(fill="x")

        entry = ctk.CTkEntry(frame, placeholder_text="Paste your API key here")
        entry.pack(fill="x", pady=(16, 6))

        status = ctk.CTkLabel(frame, text="", text_color="gray70", anchor="w")
        status.pack(fill="x")

        save_btn = ctk.CTkButton(frame, text="Save & Continue")
        save_btn.pack(fill="x", pady=(12, 0))

        result_q = queue.Queue()

        def poll():
            try:
                key, ok = result_q.get_nowait()
            except queue.Empty:
                dialog.after(100, poll)
                return
            if ok:
                key_store.save_api_key(key)
                gemini_client.configure(key)
                dialog.destroy()
                self._set_status("API key saved. Ready to tailor your CV.")
            else:
                save_btn.configure(state="normal", text="Save & Continue")
                status.configure(
                    text="That key didn't work — check it and try again.",
                    text_color="#e06666",
                )

        def on_save():
            key = entry.get().strip()
            if not key:
                status.configure(
                    text="Please paste your API key.", text_color="#e06666"
                )
                return
            save_btn.configure(state="disabled", text="Checking…")
            status.configure(text="Validating key…", text_color="gray70")
            threading.Thread(
                target=lambda: result_q.put((key, gemini_client.validate_api_key(key))),
                daemon=True,
            ).start()
            dialog.after(100, poll)

        save_btn.configure(command=on_save)
        entry.bind("<Return>", lambda _e: on_save())
        entry.focus()

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
        if not gemini_client.is_configured():
            self._set_status("Set your Gemini API key to continue.")
            self._prompt_api_key()
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
