#!/usr/bin/env python3
"""Local dev server for easyroc — serves static files + native macOS notifications."""
import http.server
import subprocess
import json
import sys
import os
import urllib.parse

PORT = 8080

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/native-notify":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                self.send_error(400, "Bad JSON")
                return

            title = data.get("title", "EasyRoc")
            message = data.get("message", "")
            subtitle = data.get("subtitle", "")

            script = f'display notification "{message}" with title "{title}" subtitle "{subtitle}" sound name "default"'
            try:
                subprocess.run(
                    ["osascript", "-e", script],
                    check=True,
                    capture_output=True,
                    timeout=5,
                )
                self.send_json({"ok": True})
            except subprocess.CalledProcessError as e:
                self.send_json({"ok": False, "error": e.stderr.decode("utf-8", errors="replace")})
        else:
            self.send_error(404)

    def do_OPTIONS(self):
        self.send_cors_headers()
        self.send_response(204)
        self.end_headers()

    def send_json(self, data):
        self.send_cors_headers()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, format, *args):
        # Only log non-static requests
        if self.path == "/native-notify":
            super().log_message(format, *args)


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print(f"EasyRoc dev server → http://localhost:{PORT}")
    print(f"  mindful-rest: http://localhost:{PORT}/mindful-rest.html")
    print(f"  native notifications: enabled (macOS)")
    print(f"  Press Ctrl+C to stop")
    httpd = http.server.HTTPServer(("127.0.0.1", PORT), Handler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        httpd.server_close()
