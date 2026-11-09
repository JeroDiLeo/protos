#!/usr/bin/env python3
"""
Servidor de correo mínimo para el lab (SMTP 25 + POP3 110).
- Auto-crea buzones (no valida credenciales: user == password, como la cátedra).
- Indexa los mensajes por la direccion RCPT TO completa, en minusculas.
- Pensado para hablarse a mano con `nc -C host 25` y `nc -C host 110`.

Cubre:
  * Parcial 2026 1C - Ej5  (destino {legajo}@mail.sebikul.com)
  * Recu 2026 - Ej1        (destino {legajo}@mail.protos.foo via mx1.protos.foo:25)
"""
import socket, threading, time, os

BANNER_HOST = "mail.protos.foo"
SMTP_PORT = int(os.environ.get("SMTP_PORT", "25"))
POP3_PORT = int(os.environ.get("POP3_PORT", "110"))
MAILBOXES = {}                 # dir_destino(lower) -> [mensaje_crudo, ...]
LOCK = threading.Lock()

def deliver(rcpts, data):
    with LOCK:
        for r in rcpts:
            MAILBOXES.setdefault(r.lower(), []).append(data)

# ----------------------------- SMTP -----------------------------
def smtp_client(conn, addr):
    f = conn.makefile("rwb", buffering=0)
    def send(s): f.write((s + "\r\n").encode())
    send(f"220 {BANNER_HOST} ESMTP LabProtos ready")
    mail_from = None; rcpts = []
    try:
        while True:
            line = f.readline()
            if not line: break
            cmd = line.decode("utf-8", "replace").rstrip("\r\n")
            up = cmd.upper()
            if up.startswith("EHLO"):
                send(f"250-{BANNER_HOST} saluda a {cmd[5:].strip() or 'cliente'}")
                send("250-PIPELINING")
                send("250 8BITMIME")
            elif up.startswith("HELO"):
                send(f"250 {BANNER_HOST}")
            elif up.startswith("MAIL FROM"):
                mail_from = cmd; rcpts = []; send("250 OK")
            elif up.startswith("RCPT TO"):
                a = cmd.split(":", 1)[1].strip() if ":" in cmd else ""
                a = a.strip("<>").strip()
                if a:
                    rcpts.append(a); send("250 OK")
                else:
                    send("501 RCPT TO vacio")
            elif up == "DATA":
                if not rcpts:
                    send("503 primero RCPT TO"); continue
                send("354 Start mail input; end with <CRLF>.<CRLF>")
                body = []
                while True:
                    l = f.readline()
                    if not l: break
                    if l in (b".\r\n", b".\n"): break
                    if l.startswith(b"."): l = l[1:]      # de-stuffing
                    body.append(l)
                deliver(rcpts, b"".join(body))
                send("250 OK message queued")
            elif up == "RSET":
                mail_from = None; rcpts = []; send("250 OK")
            elif up == "NOOP":
                send("250 OK")
            elif up == "QUIT":
                send(f"221 {BANNER_HOST} Service closing transmission channel"); break
            else:
                send("500 comando no reconocido")
    except Exception:
        pass
    finally:
        try: conn.close()
        except: pass

# ----------------------------- POP3 -----------------------------
def pop3_client(conn, addr):
    f = conn.makefile("rwb", buffering=0)
    def send(s): f.write((s + "\r\n").encode())
    send("+OK LabProtos POP3 server ready")
    user = None
    try:
        while True:
            line = f.readline()
            if not line: break
            cmd = line.decode("utf-8", "replace").rstrip("\r\n")
            parts = cmd.split(" ", 1)
            verb = parts[0].upper(); arg = parts[1].strip() if len(parts) > 1 else ""
            if verb == "USER":
                user = arg.lower(); send("+OK usuario aceptado")
            elif verb == "PASS":
                # auth deshabilitada: se acepta cualquier password
                with LOCK:
                    MAILBOXES.setdefault(user, [])
                send("+OK logueado")
            elif verb == "STAT":
                with LOCK:
                    box = MAILBOXES.get(user, [])
                    total = sum(len(m) for m in box)
                send(f"+OK {len(box)} {total}")
            elif verb == "LIST":
                with LOCK:
                    box = list(MAILBOXES.get(user, []))
                if arg:
                    i = int(arg)
                    if 1 <= i <= len(box):
                        send(f"+OK {i} {len(box[i-1])}")
                    else:
                        send("-ERR no existe ese mensaje")
                else:
                    send(f"+OK {len(box)} messages")
                    for i, m in enumerate(box, 1):
                        send(f"{i} {len(m)}")
                    send(".")
            elif verb == "RETR":
                with LOCK:
                    box = list(MAILBOXES.get(user, []))
                i = int(arg) if arg.isdigit() else 0
                if 1 <= i <= len(box):
                    send(f"+OK {len(box[i-1])} octets")
                    raw = box[i-1].decode("utf-8", "replace")
                    for l in raw.split("\n"):
                        l = l.rstrip("\r")
                        if l.startswith("."): l = "." + l   # byte-stuffing
                        send(l)
                    send(".")
                else:
                    send("-ERR no existe ese mensaje")
            elif verb == "UIDL":
                with LOCK:
                    box = list(MAILBOXES.get(user, []))
                send(f"+OK {len(box)} messages")
                for i in range(1, len(box)+1):
                    send(f"{i} msg{i}")
                send(".")
            elif verb == "DELE":
                send("+OK (lab: no se borra nada)")
            elif verb == "NOOP":
                send("+OK")
            elif verb == "RSET":
                send("+OK")
            elif verb == "QUIT":
                send("+OK bye"); break
            else:
                send("-ERR comando no reconocido")
    except Exception:
        pass
    finally:
        try: conn.close()
        except: pass

def serve(port, handler):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", port)); s.listen(50)
    while True:
        conn, addr = s.accept()
        threading.Thread(target=handler, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    threading.Thread(target=serve, args=(SMTP_PORT, smtp_client), daemon=True).start()
    threading.Thread(target=serve, args=(POP3_PORT, pop3_client), daemon=True).start()
    print(f"mailserver: SMTP :{SMTP_PORT}  POP3 :{POP3_PORT}", flush=True)
    while True: time.sleep(3600)
