#!/usr/bin/env python3
# Healthcheck del DNS: consulta A mail.protos.foo a 127.0.0.1:53 y
# sale 0 solo si hay al menos una respuesta.
import socket, struct, sys

def enc(n):
    o = b""
    for l in n.split("."):
        o += bytes([len(l)]) + l.encode()
    return o + b"\x00"

pkt = struct.pack(">HHHHHH", 0x4242, 0x0100, 1, 0, 0, 0) + enc("mail.protos.foo") + struct.pack(">HH", 1, 1)
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.settimeout(2)
    s.sendto(pkt, ("127.0.0.1", 53))
    d, _ = s.recvfrom(4096)
    ancount = struct.unpack(">H", d[6:8])[0]
    sys.exit(0 if ancount >= 1 else 1)
except Exception:
    sys.exit(1)
