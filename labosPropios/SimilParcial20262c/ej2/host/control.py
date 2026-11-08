#!/usr/bin/env python3
import os, base64
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# la passphrase de la clave SSH viaja base64 en un header (como en Basic auth / SMTP AUTH).
# el valor sale de la MISMA variable con la que se cifro la clave -> siempre en sync.
PW = os.environ.get("KEY_PASSPHRASE", "")
PW_B64 = base64.b64encode(PW.encode()).decode()

PAGE = b"""<!doctype html><meta charset="utf-8"><title>control panel</title>
<pre>
 ctOS :: control server interno (127.0.0.1:8080)
 Solo llegas si pegaste al puerto 81 con  Host: secrethost

 FLAG{ej2-vhost-secrethost-proxy-ok}

 nota de pepito: "la passphrase de mi clave la dejo aca mismo,
 pero NO en el body. Esta en un header, codificada como cuando
 el navegador manda user:pass en Basic auth. Activa el modo verboso."
</pre>"""

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(PAGE)))
        # <-- la passphrase, en base64, SOLO visible con  curl -v / -i
        self.send_header("X-Passphrase-B64", PW_B64)
        self.end_headers()
        self.wfile.write(PAGE)

ThreadingHTTPServer(("127.0.0.1", 8080), H).serve_forever()
