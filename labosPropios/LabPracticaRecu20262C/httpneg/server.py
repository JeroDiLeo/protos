#!/usr/bin/env python3
"""
Ejercicio 2 (HTTP content negotiation) en :8080.

El recurso /foo/ tiene varias representaciones y usa negociacion de contenido:
  - media type:  text/plain | text/html | application/json
  - idioma:      es | en
Devuelve la representacion segun los headers Accept y Accept-Language del cliente.
El enunciado pide la representacion text/plain en espanol: solo se obtiene
mandando  Accept: text/plain  y  Accept-Language: es.
"""
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("PORT", "8080"))

PLAIN_ES = "Recurso /foo/ en texto plano y en espanol.\nLo lograste: negociaste el tipo de contenido y el idioma.\n"
PLAIN_EN = "Resource /foo/ as plain text in English.\n"
HTML_ES  = "<!doctype html><html lang=es><body><h1>/foo/</h1><p>Esta es la version HTML.</p></body></html>\n"
JSON_ES  = '{"recurso": "/foo/", "formato": "json", "nota": "pediste json, no texto plano"}\n'

def parse_accept(h):
    """Devuelve lista de (valor, q) ordenada por q desc."""
    out = []
    for part in (h or "").split(","):
        part = part.strip()
        if not part:
            continue
        toks = part.split(";")
        val = toks[0].strip().lower()
        q = 1.0
        for t in toks[1:]:
            t = t.strip()
            if t.startswith("q="):
                try: q = float(t[2:])
                except: q = 0.0
        out.append((val, q))
    out.sort(key=lambda x: x[1], reverse=True)
    return out

def wants(accepts, *types):
    """True si alguno de 'types' (o '*/*') es aceptado con q>0."""
    best = {v: q for v, q in accepts}
    for t in types:
        if best.get(t, 0) > 0:
            return True
    return False

def lang_pref(accepts):
    for v, q in accepts:
        if q <= 0:
            continue
        base = v.split("-")[0]
        if base in ("es", "en"):
            return base
        if v == "*":
            return "es"
    return None

class H(BaseHTTPRequestHandler):
    server_version = "protos-neg/1.0"
    def log_message(self, *a): pass

    def _send(self, code, body, ctype, lang=None):
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        if lang:
            self.send_header("Content-Language", lang)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Vary", "Accept, Accept-Language")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path.rstrip("/") != "/foo":
            return self._send(404, "No existe ese recurso. Proba /foo/\n", "text/plain; charset=utf-8", "es")

        acc = parse_accept(self.headers.get("Accept"))
        accl = parse_accept(self.headers.get("Accept-Language"))
        # si no manda Accept, un browser manda text/html por defecto; curl manda */*
        if not acc:
            acc = [("*/*", 1.0)]
        lang = lang_pref(accl) if accl else None

        # negociacion de media type (preferencia del servidor: text/plain primero)
        if wants(acc, "text/plain"):
            if lang == "en":
                return self._send(200, PLAIN_EN, "text/plain; charset=utf-8", "en")
            if lang == "es":
                return self._send(200, PLAIN_ES, "text/plain; charset=utf-8", "es")
            # texto plano pero sin pedir espanol -> 406 para forzar Accept-Language
            return self._send(406,
                "Hay texto plano, pero en varios idiomas. Pedi el idioma con Accept-Language.\n",
                "text/plain; charset=utf-8", "es")
        if wants(acc, "application/json"):
            return self._send(200, JSON_ES, "application/json; charset=utf-8", "es")
        if wants(acc, "text/html", "*/*"):
            return self._send(200, HTML_ES, "text/html; charset=utf-8", "es")
        return self._send(406, "Representacion no disponible para ese Accept.\n",
                          "text/plain; charset=utf-8", "es")

if __name__ == "__main__":
    print(f"httpneg server en :{PORT}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), H).serve_forever()
