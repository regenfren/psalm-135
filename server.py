#!/usr/bin/env python3
"""Static server for the chant experience.

Two things the stock http.server can't do, both needed here:
  1. HTTP Range requests  -> so the browser can SEEK/scrub the audio.
  2. POST /save           -> so the Timing Studio writes data/chant.json in one click.

Run: python3 server.py
"""
import http.server, socketserver, json, os, re

PORT = 8080
ROOT = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'   # keep-alive + reliable media seeking

    def __init__(self, *a, **k):
        super().__init__(*a, directory=ROOT, **k)

    # browsers abort range requests constantly while seeking — don't crash on it
    def handle_one_request(self):
        try:
            super().handle_one_request()
        except (BrokenPipeError, ConnectionResetError):
            self.close_connection = True

    # ---- POST /save : write data/chant.json ----
    def do_POST(self):
        if self.path != '/save':
            self.send_error(404); return
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        try:
            data = json.loads(body)
            os.makedirs(os.path.join(ROOT, 'data'), exist_ok=True)
            with open(os.path.join(ROOT, 'data', 'chant.json'), 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(b'{"ok":true}')
        except Exception as e:
            self.send_response(500); self.end_headers()
            self.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode())

    # ---- GET with Range support (so audio can seek) ----
    def do_GET(self):
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            return super().do_GET()
        if not os.path.isfile(path):
            return super().do_GET()

        ctype = self.guess_type(path)
        fs = os.stat(path)
        size = fs.st_size
        rng = self.headers.get('Range')

        # no-store only for the text/code files so reloads are fresh;
        # media is cacheable so the browser can scrub it freely.
        cache = 'no-store' if path.endswith(('.html', '.js', '.css', '.json')) else 'public, max-age=3600'

        if rng:
            m = re.match(r'bytes=(\d*)-(\d*)', rng)
            start = int(m.group(1)) if m and m.group(1) else 0
            end = int(m.group(2)) if m and m.group(2) else size - 1
            end = min(end, size - 1)
            start = max(0, min(start, end))
            length = end - start + 1
            self.send_response(206)
            self.send_header('Content-Type', ctype)
            self.send_header('Accept-Ranges', 'bytes')
            self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
            self.send_header('Content-Length', str(length))
            self.send_header('Cache-Control', cache)
            self.end_headers()
            with open(path, 'rb') as f:
                f.seek(start)
                self.wfile.write(f.read(length))
        else:
            self.send_response(200)
            self.send_header('Content-Type', ctype)
            self.send_header('Accept-Ranges', 'bytes')
            self.send_header('Content-Length', str(size))
            self.send_header('Cache-Control', cache)
            self.end_headers()
            with open(path, 'rb') as f:
                self.wfile.write(f.read())

class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

with Server(("", PORT), Handler) as httpd:
    print(f"serving {ROOT} at http://localhost:{PORT}  (threaded · Range + POST /save)")
    httpd.serve_forever()
