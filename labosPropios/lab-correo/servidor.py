#!/usr/bin/env python3
"""Servidores del lab de correo: SMTP (recepcion y envio autenticado), POP3 y un DNS minimo.

Todo escucha en loopback. Los buzones son carpetas en ~/lab-correo/mail/<direccion>/,
un archivo .eml por mensaje, asi el corrector puede leerlos.
"""
import asyncio, base64, email.utils, json, os, re, socket, struct, sys, time, uuid

BASE = os.environ.get("LABC", os.path.expanduser("~/lab-correo"))
MAILDIR = os.path.join(BASE, "mail")
LOGDIR = os.path.join(BASE, "logs")
os.makedirs(MAILDIR, exist_ok=True)
os.makedirs(LOGDIR, exist_ok=True)
CONF = json.load(open(os.path.join(BASE, "config.json")))
LEGAJO = CONF["legajo"]
SUBMIT_PASS = "protos2026"


# ----------------------------------------------------------------- utilidades
def mbox(addr):
    d = os.path.join(MAILDIR, addr.strip().lower())
    os.makedirs(d, exist_ok=True)
    return d


def deliver(rcpts, mail_from, helo, raw, host, proto, auth_user=None):
    qid = uuid.uuid4().hex[:10].upper()
    date = email.utils.formatdate(localtime=True)
    for r in rcpts:
        rec = f"Received: from {helo or 'unknown'} (localhost [127.0.0.1])\r\n\tby {host} with {proto} id {qid}"
        if auth_user:
            rec += f"\r\n\t(authenticated sender: {auth_user})"
        rec += f"\r\n\tfor <{r}>; {date}\r\n"
        top = f"Return-Path: <{mail_from}>\r\n" + rec
        fn = os.path.join(mbox(r), f"{time.time_ns()}-{qid}.eml")
        with open(fn, "wb") as f:
            f.write(top.encode() + raw)
    return qid


class Log:
    def __init__(self, kind, peer):
        self.f = open(os.path.join(LOGDIR, f"{kind}.log"), "a", encoding="utf-8")
        self.f.write(f"\n===== {time.strftime('%Y-%m-%d %H:%M:%S')} conexion {kind} desde {peer} =====\n")

    def c(self, s):
        self.f.write("C: " + s + "\n"); self.f.flush()

    def s(self, s):
        self.f.write("S: " + s + "\n"); self.f.flush()


# ----------------------------------------------------------------- SMTP
class SMTP:
    def __init__(self, host, domains, submission=False):
        self.host, self.domains, self.submission = host, domains, submission

    async def __call__(self, r, w):
        log = Log("smtp", w.get_extra_info("peername"))

        async def send(line):
            log.s(line)
            w.write((line + "\r\n").encode())
            await w.drain()

        async def readline():
            l = await r.readline()
            return l

        helo = mail_from = authed = None
        rcpts = []
        await send(f"220 {self.host} ESMTP LabProtos ready")
        try:
            while True:
                raw = await readline()
                if not raw:
                    break
                line = raw.decode("utf-8", "replace").rstrip("\r\n")
                log.c(line)
                up = line.upper().strip()
                if up.startswith("HELO") or up.startswith("EHLO"):
                    arg = line.strip()[4:].strip()
                    if not arg:
                        await send(f"501 5.5.4 Syntax: {up[:4]} hostname"); continue
                    helo, mail_from, rcpts = arg, None, []
                    if up.startswith("HELO"):
                        await send(f"250 {self.host}")
                    else:
                        lines = [f"{self.host} Hello {arg}", "SIZE 10240000", "8BITMIME"]
                        if self.submission:
                            lines.append("AUTH PLAIN LOGIN")
                        lines.append("HELP")
                        for i, l in enumerate(lines):
                            await send(("250 " if i == len(lines) - 1 else "250-") + l)
                elif up.startswith("MAIL FROM") or up.startswith("MAIL"):
                    if not helo:
                        await send("503 5.5.1 Error: send HELO/EHLO first")
                    elif self.submission and not authed:
                        await send("530 5.7.0 Authentication required")
                    elif mail_from is not None:
                        await send("503 5.5.1 Error: nested MAIL command")
                    else:
                        m = re.match(r"(?i)MAIL FROM:\s*<([^<>]*)>\s*(.*)$", line.strip())
                        if not m:
                            await send("501 5.5.4 Syntax: MAIL FROM:<address>")
                        else:
                            mail_from, rcpts = m.group(1), []
                            await send("250 2.1.0 Ok")
                elif up.startswith("RCPT"):
                    if mail_from is None:
                        await send("503 5.5.1 Error: need MAIL command"); continue
                    m = re.match(r"(?i)RCPT TO:\s*<([^<>]+)>\s*$", line.strip())
                    if not m:
                        await send("501 5.5.4 Syntax: RCPT TO:<address>"); continue
                    addr = m.group(1).strip()
                    if "@" not in addr:
                        await send("501 5.1.3 Bad recipient address syntax"); continue
                    dom = addr.rsplit("@", 1)[1].lower()
                    if self.submission or dom in self.domains:
                        rcpts.append(addr)
                        await send("250 2.1.5 Ok")
                    else:
                        await send(f"554 5.7.1 <{addr}>: Relay access denied")
                elif up == "DATA":
                    if not rcpts:
                        await send("503 5.5.1 Error: need RCPT command"); continue
                    await send("354 End data with <CR><LF>.<CR><LF>")
                    body = []
                    while True:
                        l = await readline()
                        if not l:
                            return
                        s = l.rstrip(b"\r\n")
                        log.c(s.decode("utf-8", "replace"))
                        if s == b".":
                            break
                        if s.startswith(b"."):  # RFC 5321 4.5.2: se saca el primer punto
                            s = s[1:]
                        body.append(s)
                    data = b"\r\n".join(body) + b"\r\n"
                    proto = "ESMTPSA" if authed else ("ESMTP" if helo else "SMTP")
                    qid = deliver(rcpts, mail_from, helo, data, self.host, proto, authed)
                    await send(f"250 2.0.0 Ok: queued as {qid}")
                    mail_from, rcpts = None, []
                elif up.startswith("AUTH"):
                    if not self.submission:
                        await send("502 5.5.1 Error: authentication not enabled"); continue
                    if not helo:
                        await send("503 5.5.1 Error: send HELO/EHLO first"); continue
                    if authed:
                        await send("503 5.5.1 Error: already authenticated"); continue
                    parts = line.split()
                    mech = parts[1].upper() if len(parts) > 1 else ""
                    user = pw = None
                    try:
                        if mech == "PLAIN":
                            if len(parts) > 2:
                                resp = parts[2]
                            else:
                                await send("334 ")
                                resp = (await readline()).decode().strip(); log.c(resp)
                            dec = base64.b64decode(resp, validate=True).split(b"\0")
                            user, pw = dec[-2].decode(), dec[-1].decode()
                        elif mech == "LOGIN":
                            if len(parts) > 2:
                                user = base64.b64decode(parts[2]).decode()
                            else:
                                await send("334 VXNlcm5hbWU6")
                                u = (await readline()).decode().strip(); log.c(u)
                                user = base64.b64decode(u, validate=True).decode()
                            await send("334 UGFzc3dvcmQ6")
                            p = (await readline()).decode().strip(); log.c(p)
                            pw = base64.b64decode(p, validate=True).decode()
                        else:
                            await send("504 5.5.4 Unrecognized authentication type"); continue
                    except Exception:
                        await send("501 5.5.2 Cannot decode response"); continue
                    if user in (LEGAJO, f"{LEGAJO}@mail.protos.lab") and pw == SUBMIT_PASS:
                        authed = user
                        await send("235 2.7.0 Authentication successful")
                    else:
                        await send("535 5.7.8 Error: authentication failed")
                elif up == "RSET":
                    mail_from, rcpts = None, []
                    await send("250 2.0.0 Ok")
                elif up == "NOOP":
                    await send("250 2.0.0 Ok")
                elif up.startswith("VRFY"):
                    await send("252 2.0.0 Cannot VRFY user")
                elif up == "QUIT":
                    await send("221 2.0.0 Bye")
                    break
                elif up == "":
                    await send("500 5.5.2 Error: bad syntax")
                else:
                    await send("502 5.5.2 Error: command not recognized")
        finally:
            w.close()


# ----------------------------------------------------------------- POP3
async def pop3(r, w):
    log = Log("pop3", w.get_extra_info("peername"))

    async def send(line):
        log.s(line)
        w.write((line + "\r\n").encode())
        await w.drain()

    async def send_raw(b):
        w.write(b)
        await w.drain()

    user = None
    msgs = []        # lista de (ruta, bytes)
    deleted = set()
    authed = False
    await send("+OK POP3 LabProtos ready")
    try:
        while True:
            raw = await r.readline()
            if not raw:
                break
            line = raw.decode("utf-8", "replace").rstrip("\r\n")
            log.c("PASS ****" if line.upper().startswith("PASS") else line)
            parts = line.split()
            cmd = parts[0].upper() if parts else ""
            arg = parts[1:]
            if cmd == "CAPA":
                await send("+OK Capability list follows")
                for c in ("USER", "TOP", "UIDL", "RESP-CODES", "PIPELINING", "."):
                    await send(c)
            elif cmd == "QUIT":
                n = 0
                if authed:
                    for i in sorted(deleted):
                        try:
                            os.remove(msgs[i][0]); n += 1
                        except OSError:
                            pass
                await send(f"+OK LabProtos POP3 signing off ({n} messages deleted)")
                break
            elif not authed:
                if cmd == "USER" and arg:
                    user = arg[0]
                    await send("+OK")
                elif cmd == "PASS":
                    pw = line[5:] if len(line) > 5 else ""
                    if user and pw == user:
                        authed = True
                        d = mbox(user)
                        files = sorted(f for f in os.listdir(d) if f.endswith(".eml"))
                        msgs = [(os.path.join(d, f), open(os.path.join(d, f), "rb").read()) for f in files]
                        await send(f"+OK Logged in. {len(msgs)} messages")
                    else:
                        user = None
                        await send("-ERR [AUTH] Authentication failed")
                elif cmd in ("STAT", "LIST", "RETR", "DELE", "TOP", "UIDL", "RSET", "NOOP"):
                    await send("-ERR Unknown command (not authenticated)")
                elif cmd == "AUTH":
                    await send("-ERR Unsupported authentication mechanism")
                else:
                    await send("-ERR Unknown command")
            else:
                def get(n):
                    try:
                        i = int(n) - 1
                    except ValueError:
                        return None
                    if i < 0 or i >= len(msgs) or i in deleted:
                        return None
                    return i
                if cmd == "STAT":
                    live = [m for i, m in enumerate(msgs) if i not in deleted]
                    await send(f"+OK {len(live)} {sum(len(m[1]) for m in live)}")
                elif cmd == "LIST":
                    if arg:
                        i = get(arg[0])
                        await send(f"+OK {i+1} {len(msgs[i][1])}" if i is not None else "-ERR There's no message " + arg[0])
                    else:
                        live = [(i, m) for i, m in enumerate(msgs) if i not in deleted]
                        await send(f"+OK {len(live)} messages:")
                        for i, m in live:
                            await send(f"{i+1} {len(m[1])}")
                        await send(".")
                elif cmd == "UIDL":
                    def uid(m):
                        return os.path.basename(m[0]).split("-")[-1].replace(".eml", "")
                    if arg:
                        i = get(arg[0])
                        await send(f"+OK {i+1} {uid(msgs[i])}" if i is not None else "-ERR There's no message " + arg[0])
                    else:
                        await send("+OK")
                        for i, m in enumerate(msgs):
                            if i not in deleted:
                                await send(f"{i+1} {uid(m)}")
                        await send(".")
                elif cmd in ("RETR", "TOP"):
                    i = get(arg[0]) if arg else None
                    if i is None:
                        await send("-ERR There's no message " + (arg[0] if arg else "")); continue
                    data = msgs[i][1]
                    if cmd == "TOP":
                        try:
                            k = int(arg[1])
                        except (IndexError, ValueError):
                            await send("-ERR Syntax: TOP msg lines"); continue
                        head, sep, bod = data.partition(b"\r\n\r\n")
                        data = head + b"\r\n\r\n" + b"\r\n".join(bod.split(b"\r\n")[:k]) + (b"\r\n" if k else b"")
                        await send("+OK")
                    else:
                        await send(f"+OK {len(data)} octets")
                    out = []
                    for l in data.split(b"\r\n"):
                        out.append(b"." + l if l.startswith(b".") else l)
                    payload = b"\r\n".join(out)
                    if not payload.endswith(b"\r\n"):
                        payload += b"\r\n"
                    log.s(f"<{len(data)} bytes del mensaje {i+1}>")
                    await send_raw(payload + b".\r\n")
                elif cmd == "DELE":
                    i = get(arg[0]) if arg else None
                    if i is None:
                        await send("-ERR There's no message " + (arg[0] if arg else "")); continue
                    deleted.add(i)
                    await send(f"+OK Marked to be deleted.")
                elif cmd == "RSET":
                    deleted.clear()
                    await send("+OK")
                elif cmd == "NOOP":
                    await send("+OK")
                elif cmd in ("USER", "PASS"):
                    await send("-ERR Already authenticated")
                else:
                    await send("-ERR Unknown command")
    finally:
        w.close()


# ----------------------------------------------------------------- DNS minimo (UDP)
DNS_RECS = {
    ("empresa.lab", 15): [("MX", (10, "mx.empresa.lab")), ("MX", (20, "mx-backup.empresa.lab"))],
    ("mx.empresa.lab", 1): [("A", "127.0.0.3")],
    ("mx-backup.empresa.lab", 1): [("A", "127.0.0.4")],
    ("mail.protos.lab", 15): [("MX", (10, "mx1.protos.lab"))],
    ("mx1.protos.lab", 1): [("A", "127.0.0.1")],
    ("smtp.protos.lab", 1): [("A", "127.0.0.1")],
    ("pop.protos.lab", 1): [("A", "127.0.0.1")],
    ("protos.lab", 16): [("TXT", "v=spf1 ip4:127.0.0.1 -all")],
}
DNS_NAMES = {k[0] for k in DNS_RECS}


def enc_name(n):
    out = b""
    for lab in n.strip(".").split("."):
        out += bytes([len(lab)]) + lab.encode()
    return out + b"\x00"


class DNS(asyncio.DatagramProtocol):
    def connection_made(self, t):
        self.t = t

    def datagram_received(self, d, addr):
        try:
            tid = d[:2]
            o, labels = 12, []
            while d[o]:
                labels.append(d[o + 1:o + 1 + d[o]].decode()); o += 1 + d[o]
            o += 1
            qtype = struct.unpack(">H", d[o:o + 2])[0]
            q = d[12:o + 4]
            name = ".".join(labels).lower()
            ans = b""
            n = 0
            for typ, val in DNS_RECS.get((name, qtype), []):
                if typ == "A":
                    rd = socket.inet_aton(val)
                elif typ == "MX":
                    rd = struct.pack(">H", val[0]) + enc_name(val[1])
                else:
                    b = val.encode(); rd = bytes([len(b)]) + b
                ans += b"\xc0\x0c" + struct.pack(">HHIH", qtype, 1, 300, len(rd)) + rd
                n += 1
            rcode = 0 if (n or name in DNS_NAMES) else 3
            flags = 0x8400 | 0x0100 | rcode   # respuesta autoritativa
            self.t.sendto(tid + struct.pack(">HHHHH", flags, 1, n, 0, 0) + q + ans, addr)
        except Exception:
            pass


# ----------------------------------------------------------------- main
async def main():
    loop = asyncio.get_running_loop()
    servers = []
    servers.append(await asyncio.start_server(SMTP("mx1.protos.lab", {"mail.protos.lab", "mision.lab"}), "127.0.0.1", 2525))
    servers.append(await asyncio.start_server(SMTP("smtp.protos.lab", set(), submission=True), "127.0.0.1", 2587))
    servers.append(await asyncio.start_server(pop3, "127.0.0.1", 2110))
    try:
        servers.append(await asyncio.start_server(SMTP("mx.empresa.lab", {"empresa.lab"}), "127.0.0.3", 2525))
    except OSError as e:
        print("aviso: no pude escuchar en 127.0.0.3:2525 (", e, ") - el ejercicio C8 no va a funcionar", file=sys.stderr)
    await loop.create_datagram_endpoint(DNS, local_addr=("127.0.0.1", 5361))
    print("servidores listos", flush=True)
    await asyncio.gather(*(s.serve_forever() for s in servers))


if __name__ == "__main__":
    asyncio.run(main())
