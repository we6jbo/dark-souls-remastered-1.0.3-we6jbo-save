#!/usr/bin/env python3
"""Simple two-tab BBS GUI with Local Talk integration."""

from __future__ import annotations

import socket
import subprocess
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox

HOST = "127.0.0.1"
PORT = 32512
LOCALCHAT = Path("/home/we6jbo/Darksouls-game/KVS6/localchat.py")
ERRORS = Path("/home/we6jbo/Darksouls-game/KVS6/errors.json")


class LocalTalkBridge:
    """Small client for localchat.py's local-only TCP control interface."""

    def __init__(self, host=HOST, port=PORT, script=LOCALCHAT):
        self.host = host
        self.port = int(port)
        self.script = Path(script)

    def _exchange(self, command: str, timeout: float = 3.0) -> str:
        with socket.create_connection((self.host, self.port), timeout=timeout) as sock:
            sock.settimeout(timeout)
            f = sock.makefile("rwb", buffering=0)

            greeting = f.readline().decode("utf-8", "replace").rstrip("\r\n")
            if greeting != "LOCALCHAT READY":
                raise RuntimeError(f"Unexpected Local Talk greeting: {greeting!r}")

            f.write((command + "\n").encode("utf-8"))

            if command.upper() == "HEALTH":
                rows = []
                while True:
                    line = f.readline().decode("utf-8", "replace").rstrip("\r\n")
                    if not line or line == ".":
                        break
                    rows.append(line)
                return "\n".join(rows)

            return f.readline().decode("utf-8", "replace").rstrip("\r\n")

    def is_running(self) -> bool:
        try:
            return self._exchange("PING", timeout=0.75) == "PONG"
        except Exception:
            return False

    def ensure_running(self, startup_timeout: float = 12.0) -> bool:
        if self.is_running():
            return True

        if not self.script.exists():
            raise FileNotFoundError(
                f"{self.script} does not exist. Install localchat.py there first."
            )

        subprocess.Popen(
            [sys.executable, str(self.script)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            cwd=str(self.script.parent),
        )

        deadline = time.monotonic() + startup_timeout
        while time.monotonic() < deadline:
            if self.is_running():
                return True
            time.sleep(0.2)
        return False

    def status(self) -> str:
        return self._exchange("STATUS")

    def send(self, message: str) -> str:
        message = str(message).replace("\r", " ").replace("\n", " ").strip()
        if not message:
            return "ERROR empty message"
        return self._exchange("SEND " + message, timeout=5.0)

    def shutdown(self) -> str:
        try:
            return self._exchange("SHUTDOWN")
        except OSError:
            return "OK already stopped"


class BBSApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("BBS")
        self.root.geometry("720x420")
        self.root.minsize(560, 330)

        self.bridge = LocalTalkBridge()
        self.closing = False

        notebook = ttk.Notebook(root)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Tab 1: Messages
        messages_tab = ttk.Frame(notebook, padding=16)
        notebook.add(messages_tab, text="Messages")

        static_message = (
            "From: Sysop\n"
            "To: Everyone\n"
            "Body: Welcome to the BBS."
        )
        msg_label = ttk.Label(
            messages_tab,
            text=static_message,
            justify="left",
            font=("TkDefaultFont", 12),
        )
        msg_label.pack(anchor="nw")

        # Tab 2: Local Talk
        local_tab = ttk.Frame(notebook, padding=16)
        notebook.add(local_tab, text="Local Talk")

        self.status_var = tk.StringVar(value="[Stop talking]")
        self.status_label = ttk.Label(
            local_tab,
            textvariable=self.status_var,
            anchor="center",
            font=("TkDefaultFont", 18, "bold"),
        )
        self.status_label.pack(fill="x", pady=(10, 24))

        self.message_var = tk.StringVar()
        self.entry = ttk.Entry(local_tab, textvariable=self.message_var)
        self.entry.pack(fill="x", pady=(0, 10))
        self.entry.bind("<Return>", lambda event: self.send_message())

        self.send_button = ttk.Button(
            local_tab,
            text="Send",
            command=self.send_message,
        )
        self.send_button.pack(anchor="e")

        self.info_var = tk.StringVar(value="Starting Local Talk...")
        self.info_label = ttk.Label(
            local_tab,
            textvariable=self.info_var,
            anchor="w",
        )
        self.info_label.pack(fill="x", pady=(16, 0))

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Start localchat.py without blocking the GUI.
        threading.Thread(target=self.start_localtalk, daemon=True).start()

        # Keep BBS.py's display synchronized with localchat.py.
        self.root.after(1000, self.poll_status)

    def ui_set(self, variable: tk.StringVar, value: str):
        if not self.closing:
            self.root.after(0, variable.set, value)

    def start_localtalk(self):
        try:
            if self.bridge.ensure_running():
                self.ui_set(self.info_var, "Local Talk connected.")
            else:
                self.ui_set(
                    self.info_var,
                    f"Local Talk did not start. Check {ERRORS}",
                )
        except Exception as exc:
            self.ui_set(
                self.info_var,
                f"Local Talk startup error: {exc}. Check {ERRORS}",
            )

    def poll_status(self):
        if self.closing:
            return
        try:
            if self.bridge.is_running():
                status = self.bridge.status()
                if status in ("[Start talking]", "[Stop talking]"):
                    self.status_var.set(status)
                self.info_var.set("Local Talk connected.")
            else:
                self.status_var.set("[Start talking]")
                self.info_var.set(
                    "Local Talk is not running. Sending a message will try to start it."
                )
        except Exception as exc:
            self.status_var.set("[Start talking]")
            self.info_var.set(f"Local Talk status error: {exc}")
        finally:
            if not self.closing:
                self.root.after(1000, self.poll_status)

    def send_message(self):
        message = self.message_var.get().strip()
        if not message:
            return

        self.send_button.config(state="disabled")
        self.info_var.set("Sending to Local Talk...")

        def worker():
            try:
                if not self.bridge.ensure_running():
                    result = f"ERROR Local Talk did not start. Check {ERRORS}"
                else:
                    result = self.bridge.send(message)
                    if not result.upper().startswith("ERROR"):
                        self.root.after(0, self.message_var.set, "")
                self.ui_set(self.info_var, result)
            except Exception as exc:
                self.ui_set(self.info_var, f"Send error: {exc}. Check {ERRORS}")
            finally:
                if not self.closing:
                    self.root.after(
                        0, lambda: self.send_button.config(state="normal")
                    )

        threading.Thread(target=worker, daemon=True).start()

    def on_close(self):
        if self.closing:
            return
        self.closing = True
        self.info_var.set("Stopping Local Talk...")

        def worker():
            try:
                self.bridge.shutdown()
            except Exception:
                pass
            self.root.after(0, self.root.destroy)

        threading.Thread(target=worker, daemon=True).start()


def main():
    root = tk.Tk()
    BBSApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
