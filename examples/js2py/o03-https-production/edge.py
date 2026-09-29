"""Bounded loopback-only HTTP/1.0 teaching forwarder. NOT a production server.
No streaming, websocket, HTTP/2, rate limiting or hardened request parser.
"""
import http.client
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import socket
import ssl

MAX_BODY = 4096
FORWARD = {"authorization", "content-type", "origin", "access-control-request-method",
           "access-control-request-headers", "idempotency-key"}
RESPONSE = {"content-type", "x-request-id", "access-control-allow-origin",
            "access-control-allow-methods", "access-control-allow-headers",
            "access-control-expose-headers", "access-control-max-age", "vary"}


class LocalServer(HTTPServer):
    def get_request(self):
        connection, address = super().get_request()
        connection.settimeout(3)
        try:
            return self.tls.wrap_socket(connection, server_side=True), address
        except Exception:
            connection.close()
            raise


def create_edge(backend_port, directory, port=0):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.0"  # One request per connection.
        server_version = "js2py-teaching-edge"
        sys_version = ""
        def log_message(self, *args):
            pass  # Never log incoming URL/query/headers or bodies.
        def reply(self, status, body):
            data = json.dumps({"detail": body}).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers(); self.wfile.write(data)
        def forward(self):
            if self.headers.get("Transfer-Encoding"):
                self.reply(400, "Teaching edge requires Content-Length"); return
            lengths = self.headers.get_all("Content-Length", [])
            value = lengths[0] if lengths else "0"
            if len(lengths) > 1 or not value.isascii() or not value.isdecimal():
                self.reply(400, "Invalid Content-Length"); return
            length = int(value)
            if length > MAX_BODY:
                self.reply(413, "Teaching edge body limit"); return
            if not self.path.startswith("/") or self.path.startswith("//"):
                self.reply(400, "Origin-form path required"); return
            # Host name validation and SNI/certificate validation are distinct.
            if self.headers.get("Host") not in {"lab.test", f"lab.test:{self.server.server_port}"}:
                self.reply(400, "Unexpected host"); return
            upstream = None
            try:
                body = self.rfile.read(length)
                if len(body) != length:
                    self.reply(400, "Incomplete body"); return
                # No caller Forwarded/X-Forwarded-* survives this allowlist.
                headers = {key: value for key, value in self.headers.items() if key.lower() in FORWARD}
                headers.update({"Host": "lab.test", "X-Forwarded-Proto": "https",
                                "X-Forwarded-For": self.client_address[0], "Connection": "close"})
                upstream = http.client.HTTPConnection("127.0.0.1", backend_port, timeout=3)
                upstream.request(self.command, self.path, body=body, headers=headers)
                response = upstream.getresponse()
                data = response.read(65537)
                if len(data) > 65536:
                    self.reply(502, "Teaching edge response limit"); return
                self.send_response(response.status)
                for key, value in response.getheaders():
                    if key.lower() in RESPONSE:
                        self.send_header(key, value)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers(); self.wfile.write(data)
            except (OSError, http.client.HTTPException):
                self.reply(502, "Teaching upstream unavailable")
            finally:
                if upstream is not None:
                    upstream.close()
        do_GET = do_POST = do_OPTIONS = forward
    server = LocalServer(("127.0.0.1", port), Handler)
    tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    tls.minimum_version = ssl.TLSVersion.TLSv1_2
    tls.load_cert_chain(directory / "leaf.pem", directory / "leaf.key")
    server.tls = tls
    return server
