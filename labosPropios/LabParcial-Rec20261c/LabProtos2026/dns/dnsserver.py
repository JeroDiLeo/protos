#!/usr/bin/env python3
"""
DNS autoritativo mínimo para el lab (reemplaza dnsmasq para que sea
reproducible y testeable). Responde A, AAAA, CNAME, MX, TXT, SOA, NS
para las zonas del lab. Lo desconocido -> NXDOMAIN (no hace forwarding,
igual que dnsmasq con no-resolv).

Escucha UDP y TCP en :53.
"""
import socket, struct, threading, os

PORT = int(os.environ.get("PORT", "53"))

# ------------------------------- zona del lab -------------------------------
A = {
    "bar.protos.foo":        "123.123.123.123",   # Ej1: IP para el registro A
    "mail.protos.foo":       "172.28.0.25",
    "mx1.protos.foo":        "172.28.0.25",
    "mx2.protos.foo":        "172.28.0.25",
    "mail.sebikul.com":      "172.28.0.25",
    "metadata.protos.foo":   "172.28.0.20",
    "proxy.protos.foo":      "172.28.0.40",
    "pampero.itba.edu.ar":   "172.28.0.60",
    "parcial.protos.foo":    "172.28.0.72",
    "ejercicio3.protos.foo": "172.29.0.30",   # vive en la red oculta
}
MX = {                                        # Ej1: MX de mail.protos.foo
    "mail.protos.foo": [(5, "mx2.protos.foo"), (10, "mx1.protos.foo")],
}
TXT = {}
CNAME = {}

TYPES = {"A": 1, "NS": 2, "CNAME": 5, "SOA": 6, "MX": 15, "TXT": 16, "AAAA": 28}
RTYPE = {v: k for k, v in TYPES.items()}

def enc_name(name):
    out = b""
    for lbl in name.rstrip(".").split("."):
        out += bytes([len(lbl)]) + lbl.encode()
    return out + b"\x00"

def dec_name(data, off):
    labels = []
    while True:
        l = data[off]
        if l & 0xC0 == 0xC0:                  # puntero de compresion
            ptr = struct.unpack(">H", data[off:off+2])[0] & 0x3FFF
            off += 2
            sub, _ = dec_name(data, ptr)
            labels.append(sub); break
        off += 1
        if l == 0: break
        labels.append(data[off:off+l].decode()); off += l
    return ".".join([x for x in labels if x]), off

def build_rr(name, rtype, rdata, ttl=3600):
    return enc_name(name) + struct.pack(">HHIH", rtype, 1, ttl, len(rdata)) + rdata

def handle_query(data):
    if len(data) < 12: return None
    tid, flags, qd, an, ns, ar = struct.unpack(">HHHHHH", data[:12])
    qname, off = dec_name(data, 12)
    qtype, qclass = struct.unpack(">HH", data[off:off+4]); off += 4
    key = qname.rstrip(".").lower()

    answers = b""; ancount = 0; rcode = 0
    tname = RTYPE.get(qtype, "")

    def add(rr):
        nonlocal answers, ancount
        answers += rr; ancount += 1

    if tname == "A" and key in A:
        add(build_rr(qname, 1, socket.inet_aton(A[key])))
    elif tname == "MX" and key in MX:
        for pref, host in MX[key]:
            add(build_rr(qname, 15, struct.pack(">H", pref) + enc_name(host)))
    elif tname == "TXT" and key in TXT:
        for t in TXT[key]:
            add(build_rr(qname, 16, bytes([len(t)]) + t.encode()))
    elif tname == "CNAME" and key in CNAME:
        add(build_rr(qname, 5, enc_name(CNAME[key])))
    elif tname == "AAAA":
        pass                                  # sin IPv6 en el lab: respuesta vacia
    else:
        # existe el nombre pero no ese tipo -> NOERROR vacio; si no existe -> NXDOMAIN
        known = key in A or key in MX or key in TXT or key in CNAME
        if not known:
            rcode = 3                         # NXDOMAIN

    resp_flags = 0x8400 | rcode               # QR=1, AA=1
    header = struct.pack(">HHHHHH", tid, resp_flags, 1, ancount, 0, 0)
    question = enc_name(qname) + struct.pack(">HH", qtype, qclass)
    return header + question + answers

def serve_udp():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", PORT))
    while True:
        try:
            data, addr = s.recvfrom(4096)
            resp = handle_query(data)
            if resp: s.sendto(resp, addr)
        except Exception:
            pass

def serve_tcp():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", PORT)); s.listen(50)
    while True:
        try:
            conn, _ = s.accept()
            ln = struct.unpack(">H", conn.recv(2))[0]
            data = conn.recv(ln)
            resp = handle_query(data)
            if resp: conn.sendall(struct.pack(">H", len(resp)) + resp)
            conn.close()
        except Exception:
            try: conn.close()
            except: pass

if __name__ == "__main__":
    threading.Thread(target=serve_tcp, daemon=True).start()
    print(f"dns server (A/MX/CNAME/TXT) en :{PORT}", flush=True)
    serve_udp()
