#!/usr/bin/env python3
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MSG = {
    "from": "Wrench",
    "to": "you",
    "city": "San Francisco",
    "message": [
        "Vaya, vaya, al fin te conectas.",
        "No hay tiempo, hay mucho que hackear.",
        "Un infiltrado consiguio acceso al sistema de ctOS.",
        "Hay un servidor en http://secrets.ct.os con las llaves para voltear a Bloom.",
        "Pero la IP esta escondida detras de un proxy socks5.",
        "Corri un escaneo: puerto abierto en 172.30.0.12:1080 (socks5).",
        "Tunelizá por ahi y traeme lo que haya en secrets.ct.os.",
        "Ah, y activá el MODO VERBOSO: te dejo pistas en los headers de respuesta."
    ]
}

class H(BaseHTTPRequestHandler):
    server_version = "ctOS-edge/1.0"
    def log_message(self, *a): pass

    def do_GET(self):
        body = json.dumps(MSG, ensure_ascii=False, indent=2).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        # PISTAS en headers -> solo visibles con  curl -v  / curl -i
        self.send_header("X-CTOS-Proxy", "172.30.0.12:1080 socks5")
        self.send_header("X-CTOS-Target", "http://secrets.ct.os/")
        self.send_header("X-Wrench", "usa curl --socks5-hostname para que el DNS lo resuelva el proxy")
        # eco del header que mandes (para practicar -H)
        echo = self.headers.get("X-You")
        if echo:
            self.send_header("X-Wrench-Reply", f"te escucho, {echo}")
        self.end_headers()
        self.wfile.write(body)

if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 3126), H).serve_forever()
