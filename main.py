import http.server
import socketserver
import urllib.request
import json
from pathlib import Path

PORT = 8080
MAVLINK_URL = "http://localhost:6040/v1/mavlink/vehicles/1/components/1/messages/GLOBAL_POSITION_INT"

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # suppress noisy logs

    def do_GET(self):
        if self.path == "/api/gps":
            self._proxy_mavlink()
        elif self.path in ("/", "/index.html"):
            self._serve_file("index.html", "text/html")
        else:
            self.send_response(404)
            self.end_headers()

    def _proxy_mavlink(self):
        try:
            with urllib.request.urlopen(MAVLINK_URL, timeout=2) as r:
                body = r.read()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            body = json.dumps({"error": str(e)}).encode()
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)

    def _serve_file(self, filename, content_type):
        path = Path(__file__).parent / filename
        if path.exists():
            body = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

print(f"GPS Tracker running on port {PORT}")
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    httpd.serve_forever()
