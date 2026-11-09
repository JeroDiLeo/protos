#!/usr/bin/env python3
"""
Ejercicio 3 (Parcial 2026 1C) - servidor HTTP "acumulativo" en :3126.
Solo accesible atravesando el proxy SOCKS5 (esta en una red interna).

El alumno va sumando flags a curl, una por una, hasta aprobar:
  1) GET /            -> 302 a /debugger  (+ header X-Tip-Parcial)
  2) GET /debugger    -> falta header  X-legajo
  3) + X-legajo       -> responde en ruso (falta Accept-Language: es)
  4) + Accept-Language: es  -> el GET anda, pero "el POST falla"
  5) POST /debugger   -> pide mandar el JSON {"fix":"yes"}
  6) + JSON           -> 401, pide sudo (usuario admin / pass admin)
  7) + Authorization  -> aprobado
"""
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("PORT", "3126"))
OKAUTH = "Basic YWRtaW46YWRtaW4="   # admin:admin

class H(BaseHTTPRequestHandler):
    server_version = "ctOS-debugger/0.1"
    def log_message(self, *a): pass

    def _send(self, code, body, extra=None, ctype="text/plain; charset=utf-8"):
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def handle_one_request(self):
        try:
            super().handle_one_request()
        except Exception:
            pass

    def _debugger(self, is_post):
        h = self.headers
        legajo = h.get("X-legajo")
        if not legajo:
            return self._send(200,
                "¡Oh wow no sabia que http tenia headers!\n\n"
                "Pero parece que aun esta roto\n\n"
                "¿donde estan los logs?\n",
                {"X-Error_Message": 'Missing header "X-legajo"'})

        accept_lang = (h.get("Accept-Language") or "").lower()
        if "es" not in accept_lang:
            return self._send(200,
                "Странно, язык изменился\n",
                {"Content-Language": "ru"})

        if not is_post:
            return self._send(200,
                "Genial aprece que ya se arreglo el GET\n\n"
                "Pero el POST aun falla\n")

        # ---- de aca en adelante es POST ----
        ctype = (h.get("Content-Type") or "").lower()
        length = int(h.get("Content-Length") or 0)
        body = self.rfile.read(length).decode("utf-8", "replace") if length else ""

        if "application/json" not in ctype or '"fix"' not in body.replace(" ", ""):
            return self._send(200,
                "Ok ya se que hacer\n"
                "Llevo semanas desarrollando un fix para todos los problemas\n"
                "Proba mandar este JSON:\n\n"
                '{"fix":"yes"}\n')

        auth = h.get("Authorization")
        if auth != OKAUTH:
            return self._send(401,
                "Ups me olvide de decirte que te falta sudo, no te preocupes te "
                "presto mi cuenta, el usuario es admin y la contrasena es admin\n",
                {"WWW-Authenticate": 'Basic realm="sudo"'})

        return self._send(200,
            "¡Te doy el ejercicio por aprobado!\n")

    def do_GET(self):
        if self.path == "/" or self.path == "":
            return self._send(302,
                "¡Que bueno que estas aca!\n\n"
                "Mi servidor http esta fallando, pero no se como debugearlo.\n\n"
                "¿podrias ayudarme?\n",
                {"Location": "/debugger",
                 "X-Tip-Parcial": "el ejercicio es acumulativo asi solo te queda un comando para correr"})
        if self.path.startswith("/debugger"):
            return self._debugger(is_post=False)
        return self._send(404, "no existe ese path\n")

    def do_POST(self):
        if self.path.startswith("/debugger"):
            return self._debugger(is_post=True)
        return self._send(404, "no existe ese path\n")

if __name__ == "__main__":
    print(f"ej3 debugger server en :{PORT}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), H).serve_forever()
