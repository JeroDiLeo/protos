#!/usr/bin/env python3
"""
DNS del laboratorio (192.168.60.53).

- Autoritativo para protos.foo y para los datos de referencia del Ej3 (DNS).
- Lo que no conoce de esas zonas -> NXDOMAIN.
- Reverse (in-addr.arpa) -> NXDOMAIN inmediato (nmap/traceroute no se cuelgan).
- Todo lo demas se reenvia al resolver de Docker (apt/curl a Internet siguen
  funcionando desde la VM del alumno).
"""
import socket, struct, threading, os

PORT = int(os.environ.get("PORT", "53"))

# A records del lab
A = {
    "mail.protos.foo":        "192.168.60.70",
    "mx1.protos.foo":         "192.168.60.70",
    "mx2.protos.foo":         "192.168.60.70",
    "ejercicio2.protos.foo":  "192.168.60.80",
    "metadata.protos.foo":    "192.168.60.85",
    "parcial.protos.foo":     "192.168.60.90",
    # --- datos de referencia para el Ej3 (DNS): el alumno los copia a su zona ---
    "bar.protos.foo":         "93.184.216.34",
}
# MX de mail.protos.foo (el Ej3 pide "los mismos servidores que atienden mail.protos.foo")
MX = {
    "mail.protos.foo": [(10, "mx1.protos.foo"), (20, "mx2.protos.foo")],
}

ZONE_SUFFIXES = (".protos.foo",)
ZONE_NAMES = ("protos.foo",)

def upstream():
    try:
        for line in open("/etc/resolv.conf"):
            p = line.split()
            if len(p) >= 2 and p[0] == "nameserver" and p[1] not in ("127.0.0.1",):
                return p[1]
    except Exception:
        pass
    return "127.0.0.11"

UPSTREAM = upstream()

def enc_name(name):
    out = b""
    for lbl in name.rstrip(".").split("."):
        if lbl:
            out += bytes([len(lbl)]) + lbl.encode()
    return out + b"\x00"

def dec_name(data, off):
    labels = []
    while True:
        l = data[off]
        if l & 0xC0 == 0xC0:
            ptr = struct.unpack(">H", data[off:off+2])[0] & 0x3FFF
            sub, _ = dec_name(data, ptr)
            labels.append(sub)
            return ".".join(x for x in labels if x), off + 2
        off += 1
        if l == 0:
            return ".".join(x for x in labels if x), off
        labels.append(data[off:off+l].decode(errors="replace")); off += l

def is_ours(key):
    if key in ("protos.foo",) or key.endswith(".protos.foo"):
        return True
    return False

def local_answer(data):
    tid, flags, qd = struct.unpack(">HHH", data[:6])
    qname, off = dec_name(data, 12)
    qtype, qclass = struct.unpack(">HH", data[off:off+4])
    key = qname.rstrip(".").lower()
    question = data[12:off+4]
    rd = flags & 0x0100

    if key.endswith(".in-addr.arpa") or key.endswith(".ip6.arpa"):
        rcode, answers, an = 3, b"", 0
    elif is_ours(key):
        answers, an, rcode = b"", 0, 0
        if qtype in (1, 255) and key in A:            # A
            answers += enc_name(qname) + struct.pack(">HHIH", 1, 1, 300, 4) + socket.inet_aton(A[key]); an += 1
        if qtype in (15, 255) and key in MX:          # MX
            for pref, host in MX[key]:
                rd_mx = struct.pack(">H", pref) + enc_name(host)
                answers += enc_name(qname) + struct.pack(">HHIH", 15, 1, 300, len(rd_mx)) + rd_mx; an += 1
        if an == 0 and not (key in A or key in MX):
            rcode = 3                                  # NXDOMAIN
    else:
        return None
    hdr = struct.pack(">HHHHHH", tid, 0x8400 | 0x0080 | rd | rcode, 1, an, 0, 0)
    return hdr + question + answers

def forward(data):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.settimeout(3)
        s.sendto(data, (UPSTREAM, 53))
        resp, _ = s.recvfrom(4096)
        return resp
    except Exception:
        qname, off = dec_name(data, 12)
        return data[:2] + struct.pack(">HHHHH", 0x8182, 1, 0, 0, 0) + data[12:off+4]

def resolve(data):
    if len(data) < 12:
        return None
    try:
        r = local_answer(data)
    except Exception:
        return None
    return r if r is not None else forward(data)

def serve_udp():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("0.0.0.0", PORT))
    while True:
        data, addr = s.recvfrom(4096)
        threading.Thread(target=lambda d=data, a=addr: (lambda r: r and s.sendto(r, a))(resolve(d)), daemon=True).start()

def serve_tcp():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", PORT)); s.listen(50)
    while True:
        conn, _ = s.accept()
        def work(c=conn):
            try:
                c.settimeout(5)
                ln = struct.unpack(">H", c.recv(2))[0]
                d = b""
                while len(d) < ln:
                    chunk = c.recv(ln - len(d))
                    if not chunk: break
                    d += chunk
                r = resolve(d)
                if r:
                    c.sendall(struct.pack(">H", len(r)) + r)
            except Exception:
                pass
            finally:
                c.close()
        threading.Thread(target=work, daemon=True).start()

if __name__ == "__main__":
    threading.Thread(target=serve_tcp, daemon=True).start()
    print(f"dns del lab en :{PORT} (upstream {UPSTREAM})", flush=True)
    serve_udp()
