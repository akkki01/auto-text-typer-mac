#!/usr/bin/env python3
"""
Auto Text Typer for Mac
Type text sentences with keyboard shortcuts. Configure shortcuts, delays,
and save/load configurations via the built-in web UI.
"""

import json
import os
import signal
import socketserver
import sys
import threading
import time
import uuid
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

import pyautogui
from pynput import keyboard as kb

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0

CONFIG_DIR = os.path.expanduser("~/.autotyper")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
UI_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui.html")
PORT = 8787


class Config:
    def __init__(self):
        self.entries = []
        self.settings = {"key_delay_ms": 10, "char_delay_ms": 30}
        self._lock = threading.Lock()
        self.load()

    def load(self, path=None):
        path = path or CONFIG_FILE
        try:
            with open(path, "r") as f:
                data = json.load(f)
            with self._lock:
                self.entries = data.get("entries", [])
                self.settings.update(data.get("settings", {}))
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def save(self, path=None):
        path = path or CONFIG_FILE
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with self._lock:
            with open(path, "w") as f:
                json.dump(self.to_dict(), f, indent=2)

    def to_dict(self):
        return {"entries": list(self.entries), "settings": dict(self.settings)}

    def add_entry(self, entry):
        entry["id"] = str(uuid.uuid4())
        entry.setdefault("enabled", True)
        with self._lock:
            self.entries.append(entry)
        self.save()
        return entry

    def update_entry(self, entry_id, data):
        with self._lock:
            for i, e in enumerate(self.entries):
                if e["id"] == entry_id:
                    self.entries[i].update(data)
                    self.save()
                    return self.entries[i]
        return None

    def delete_entry(self, entry_id):
        with self._lock:
            self.entries = [e for e in self.entries if e["id"] != entry_id]
        self.save()

    def update_settings(self, settings):
        with self._lock:
            self.settings.update(settings)
        self.save()


class TypingEngine:
    def __init__(self, config):
        self.config = config
        self.typing = False
        self.stop_flag = False

    def type_text(self, text):
        if self.typing:
            self.stop_flag = True
            time.sleep(0.15)

        self.typing = True
        self.stop_flag = False

        key_delay = self.config.settings["key_delay_ms"] / 1000.0
        char_delay = self.config.settings["char_delay_ms"] / 1000.0
        pyautogui.PAUSE = key_delay

        for char in text:
            if self.stop_flag:
                break
            try:
                if char == "\n":
                    pyautogui.press("return")
                elif char == "\t":
                    pyautogui.press("tab")
                elif char.isascii() and char.isprintable():
                    pyautogui.write(char)
                else:
                    import pyperclip
                    pyperclip.copy(char)
                    pyautogui.hotkey("command", "v")
            except Exception:
                pass
            time.sleep(char_delay)

        self.typing = False

    def stop(self):
        self.stop_flag = True


class HotkeyMonitor:
    def __init__(self, config, engine):
        self.config = config
        self.engine = engine
        self.listener = None
        self.active = True

    def rebuild(self):
        if self.listener:
            try:
                self.listener.stop()
            except Exception:
                pass
            self.listener = None

        if not self.active:
            return

        hotkeys = {}
        for entry in self.config.entries:
            if entry.get("enabled", True):
                shortcut = entry["shortcut"]
                text = entry["text"]
                hotkeys[shortcut] = self._make_callback(text)

        if hotkeys:
            try:
                self.listener = kb.GlobalHotKeys(hotkeys)
                self.listener.daemon = True
                self.listener.start()
            except Exception as e:
                print(f"  ⚠ Hotkey error: {e}")

    def _make_callback(self, text):
        def callback():
            if self.active:
                threading.Thread(
                    target=self.engine.type_text, args=(text,), daemon=True
                ).start()
        return callback

    def toggle(self):
        self.active = not self.active
        self.rebuild()
        return self.active

    def stop(self):
        self.active = False
        if self.listener:
            try:
                self.listener.stop()
            except Exception:
                pass


config = Config()
engine = TypingEngine(config)
monitor = HotkeyMonitor(config, engine)


class ReusableHTTPServer(HTTPServer):
    allow_reuse_address = True
    allow_reuse_port = True


class APIHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _send(self, body, content_type="application/json", status=200, headers=None):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, data, status=200):
        self._send(json.dumps(data), status=status)

    def _body(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw) if raw else {}

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            try:
                with open(UI_FILE, "r") as f:
                    self._send(f.read(), "text/html; charset=utf-8")
            except FileNotFoundError:
                self._send("<h1>UI file not found</h1>", "text/html", 404)
        elif path == "/api/config":
            self._json(config.to_dict())
        elif path == "/api/status":
            self._json({
                "active": monitor.active,
                "typing": engine.typing,
                "count": len(config.entries),
            })
        elif path == "/api/export":
            self._send(
                json.dumps(config.to_dict(), indent=2),
                "application/json",
                headers={"Content-Disposition": 'attachment; filename="autotyper_config.json"'},
            )
        else:
            self._send("Not found", "text/plain", 404)

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            data = self._body()
        except json.JSONDecodeError:
            self._json({"error": "Invalid JSON"}, 400)
            return

        if path == "/api/entries":
            entry = config.add_entry(data)
            monitor.rebuild()
            self._json(entry, 201)
        elif path == "/api/settings":
            config.update_settings(data)
            self._json(config.settings)
        elif path == "/api/toggle":
            active = monitor.toggle()
            self._json({"active": active})
        elif path == "/api/import":
            config.entries = data.get("entries", [])
            config.settings.update(data.get("settings", {}))
            config.save()
            monitor.rebuild()
            self._json(config.to_dict())
        else:
            self._send("Not found", "text/plain", 404)

    def do_PUT(self):
        path = urlparse(self.path).path
        if path.startswith("/api/entries/"):
            eid = path.split("/")[-1]
            data = self._body()
            entry = config.update_entry(eid, data)
            if entry:
                monitor.rebuild()
                self._json(entry)
            else:
                self._json({"error": "Not found"}, 404)
        else:
            self._send("Not found", "text/plain", 404)

    def do_DELETE(self):
        path = urlparse(self.path).path
        if path.startswith("/api/entries/"):
            eid = path.split("/")[-1]
            config.delete_entry(eid)
            monitor.rebuild()
            self._json({"ok": True})
        else:
            self._send("Not found", "text/plain", 404)


def main():
    print()
    print("  ┌──────────────────────────────────────┐")
    print("  │       ⌨  Auto Text Typer for Mac      │")
    print("  └──────────────────────────────────────┘")
    print()

    monitor.rebuild()
    n = len(config.entries)
    print(f"  Loaded {n} shortcut{'s' if n != 1 else ''}")
    print(f"  Hotkeys: {'Active' if monitor.active else 'Paused'}")
    print()

    server = ReusableHTTPServer(("127.0.0.1", PORT), APIHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    url = f"http://127.0.0.1:{PORT}"
    print(f"  Config UI → {url}")
    print(f"  Press Ctrl+C to quit")
    print()

    webbrowser.open(url)

    def shutdown(signum=None, frame=None):
        print("\n  Shutting down...")
        monitor.stop()
        engine.stop()
        server.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        shutdown()


if __name__ == "__main__":
    main()
