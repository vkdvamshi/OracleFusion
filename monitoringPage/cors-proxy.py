#!/usr/bin/env python3
"""Serve fusion-job-monitor.html and proxy its Fusion REST calls.

Browsers block a local HTML page from calling Oracle Fusion directly (CORS).
This server sidesteps that: it serves the page at http://localhost:8765 and
forwards GET /fusion?url=<encoded Fusion URL> to Fusion server-side, passing
the Authorization header through untouched. Nothing is logged or stored.

Usage:
    python3 cors-proxy.py                     # allows *.oraclecloud.com, opens browser
    python3 cors-proxy.py --allow-host my.custom.domain.com
    python3 cors-proxy.py --no-browser
"""
import http.server
import os
import ssl
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
import webbrowser

PORT = 8765
ALLOWED_HOST_SUFFIXES = [".oraclecloud.com"]

# python.org macOS builds don't load system CAs by default; prefer certifi,
# then the macOS system bundle, then whatever the default context finds.
def _ssl_context():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        pass
    if os.path.exists("/etc/ssl/cert.pem"):
        return ssl.create_default_context(cafile="/etc/ssl/cert.pem")
    return ssl.create_default_context()

SSL_CTX = _ssl_context()

for i, arg in enumerate(sys.argv):
    if arg == "--allow-host" and i + 1 < len(sys.argv):
        ALLOWED_HOST_SUFFIXES.append(sys.argv[i + 1].lower().lstrip("."))


def host_allowed(host: str) -> bool:
    host = (host or "").lower()
    return any(host == s.lstrip(".") or host.endswith(s if s.startswith(".") else "." + s)
               for s in ALLOWED_HOST_SUFFIXES)


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if not self.path.startswith("/fusion?"):
            return super().do_GET()
        self._proxy("GET")

    def do_POST(self):
        if not self.path.startswith("/fusion?"):
            self.send_error(404)
            return
        self._proxy("POST")

    def _proxy(self, method):
        query = urllib.parse.urlparse(self.path).query
        target = urllib.parse.parse_qs(query).get("url", [""])[0]
        parsed = urllib.parse.urlparse(target)

        if parsed.scheme != "https" or not host_allowed(parsed.hostname):
            self.send_error(400, "Target must be https and host must match "
                                 + ", ".join("*" + s for s in ALLOWED_HOST_SUFFIXES)
                                 + " (use --allow-host for custom domains)")
            return

        headers = {"Accept": self.headers.get("Accept", "*/*"),
                   "Accept-Encoding": "identity"}
        for name in ("Authorization", "Content-Type", "SOAPAction"):
            if self.headers.get(name):
                headers[name] = self.headers[name]

        body = None
        if method == "POST":
            body = self.rfile.read(int(self.headers.get("Content-Length", 0)))

        req = urllib.request.Request(target, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=90, context=SSL_CTX) as resp:
                self._relay(resp.status, resp.headers, resp.read())
        except urllib.error.HTTPError as e:
            self._relay(e.code, e.headers, e.read())
        except Exception as e:  # DNS failure, timeout, TLS error…
            self.send_error(502, f"Could not reach Fusion: {e}")

    def _relay(self, status, resp_headers, body):
        # Some Fusion services gzip regardless of Accept-Encoding; decompress
        # so the browser gets plain bytes with a correct Content-Length.
        encoding = (resp_headers.get("Content-Encoding") or "").lower()
        if "gzip" in encoding:
            import gzip
            try: body = gzip.decompress(body)
            except OSError: pass
        elif "deflate" in encoding:
            import zlib
            try: body = zlib.decompress(body)
            except zlib.error: pass
        self.send_response(status)
        self.send_header("Content-Type", resp_headers.get("Content-Type", "application/json"))
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):  # keep credentials-bearing URLs out of the console
        pass


if __name__ == "__main__":
    url = f"http://localhost:{PORT}/fusion-job-monitor.html"
    print(f"Serving {url}")
    print(f"Proxying /fusion -> hosts matching: {', '.join('*' + s for s in ALLOWED_HOST_SUFFIXES)}")
    if "--no-browser" not in sys.argv:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
