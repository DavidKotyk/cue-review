"""Loopback-only HTTP UI for Cue Review. Run python3 server.py."""
import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from core import Store, Invalid, Conflict

ROOT = Path(__file__).resolve().parent


def make_handler(store):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass  # Captions and document IDs do not belong in access logs.

        def send(self, status, content, kind='application/json; charset=utf-8'):
            body = json.dumps(content).encode() if kind.startswith('application/json') else content
            self.send_response(status)
            self.send_header('Content-Type', kind)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(body)

        def allowed(self):
            valid = {f'localhost:{self.server.server_port}', f'127.0.0.1:{self.server.server_port}'}
            if self.headers.get('Host') not in valid:
                self.send(403, {'error': 'Loopback Host required.'})
                return False
            origin = self.headers.get('Origin')
            if origin is not None and origin not in {'http://' + h for h in valid}:
                self.send(403, {'error': 'Same-origin local requests only.'})
                return False
            if self.headers.get('Sec-Fetch-Site') == 'cross-site':
                self.send(403, {'error': 'Cross-site requests are not allowed.'})
                return False
            return True

        def do_GET(self):
            if not self.allowed():
                return
            parsed = urlparse(self.path)
            try:
                if parsed.path == '/api/review':
                    doc_id = parse_qs(parsed.query).get('id', [''])[0]
                    from core import view
                    return self.send(200, view(store.get(doc_id)))
                assets = {'/': ('index.html', 'text/html; charset=utf-8'),
                          '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
                          '/style.css': ('style.css', 'text/css; charset=utf-8')}
                if parsed.path == '/demo.srt':
                    return self.send(200, (ROOT / 'demo' / 'studio-demo.srt').read_bytes(), 'text/plain; charset=utf-8')
                if parsed.path not in assets:
                    return self.send(404, {'error': 'Not found.'})
                name, mime = assets[parsed.path]
                self.send(200, (ROOT / 'static' / name).read_bytes(), mime)
            except Invalid as exc:
                self.send(400, {'error': str(exc)})

        def do_POST(self):
            if not self.allowed():
                return
            if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                return self.send(415, {'error': 'JSON required.'})
            try:
                size = int(self.headers.get('Content-Length', 0))
                if not 0 < size <= 300_000:
                    return self.send(413, {'error': 'Request must be 1–300000 bytes.'})
                data = json.loads(self.rfile.read(size))
                if not isinstance(data, dict):
                    raise Invalid('JSON object required.')
                if self.path == '/api/import':
                    result = store.create(data['source'], data.get('name', 'captions.srt'), data.get('glossary', []), data.get('max_cps', 20))
                elif self.path == '/api/propose':
                    result = store.propose(data['id'], data['revision'], data['index'])
                elif self.path == '/api/decide':
                    result = store.decide(data['id'], data['revision'], data['index'], data['action'], data.get('text'))
                elif self.path == '/api/export':
                    result = store.export(data['id'], data['revision'])
                else:
                    return self.send(404, {'error': 'Not found.'})
                self.send(200, result)
            except Conflict as exc:
                self.send(409, {'error': str(exc)})
            except (Invalid, KeyError, TypeError, ValueError, UnicodeError) as exc:
                self.send(400, {'error': str(exc) if isinstance(exc, Invalid) else 'Invalid request fields or JSON.'})
            except Exception:
                self.send(500, {'error': 'Local operation failed. Original captions are preserved.'})
    return Handler


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=4190)
    parser.add_argument('--db', default=str(ROOT / 'data' / 'reviews.sqlite3'))
    args = parser.parse_args()
    Path(args.db).parent.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer(('127.0.0.1', args.port), make_handler(Store(args.db)))
    print(f'Cue Review: http://127.0.0.1:{args.port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
