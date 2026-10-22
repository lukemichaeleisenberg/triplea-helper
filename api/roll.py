"""Vercel Python function: POST a raw .tsvg body, get the four rolls as JSON.

Run directly (`python api/roll.py`) to serve it on localhost:8000 for local
development behind the Vite dev-server proxy.
"""

import io
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from triplea_rolls import SaveParseError, roll_save  # noqa: E402

MAX_BYTES = 4 * 1024 * 1024  # Vercel caps request bodies at 4.5 MB


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length == 0:
            return self._send(400, {"error": "No file uploaded."})
        if length > MAX_BYTES:
            return self._send(413, {"error": "File is too large (4 MB max)."})

        body = self.rfile.read(length)
        try:
            result = roll_save(io.BytesIO(body))
        except SaveParseError as e:
            return self._send(422, {"error": str(e)})
        except Exception as e:
            return self._send(500, {"error": f"Unexpected error: {e}"})
        self._send(200, result)

    def _send(self, status, payload):
        data = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    print("Serving /api/roll on http://localhost:8000")
    HTTPServer(("127.0.0.1", 8000), handler).serve_forever()
