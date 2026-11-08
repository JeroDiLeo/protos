#!/usr/bin/env python3
"""
Genera backup.pcapng (en realidad formato .pcap clasico, Wireshark lo abre igual)
con queries + replies DNS de un nameserver, para reconstruir la zona.

Zona reconstruible desde la captura:  protos.lab
  SOA  ns1.protos.lab. admin.protos.lab. (serial ...)
  NS   ns1.protos.lab.
  A    ns1   -> 172.30.0.41
  A    www   -> 172.30.0.50
  A    mail  -> 172.30.0.51
  MX   10 mail.protos.lab.
  CNAME ftp -> www.protos.lab.
  TXT  @  -> "v=protos1"     (el alumno DEBE AGREGAR ademas  TXT "cachito hola")

No usa scapy: arma Ethernet/IPv4/UDP/DNS a mano.
"""
import struct, socket, time

CLIENT_IP = "172.30.0.99"
SERVER_IP = "172.30.0.41"      # ns1
CLIENT_MAC = bytes.fromhex("0242ac1e0063")
SERVER_MAC = bytes.fromhex("0242ac1e0029")

TYPES = {"A":1,"NS":2,"CNAME":5,"SOA":6,"MX":15,"TXT":16}

def enc_name(name):
    out = b""
    for label in name.rstrip(".").split("."):
        out += bytes([len(label)]) + label.encode()
    return out + b"\x00"

def dns_question(qname, qtype):
    return enc_name(qname) + struct.pack(">HH", qtype, 1)  # class IN

def rr(name, rtype, rdata, ttl=3600):
    if isinstance(rtype, str):
        rtype = TYPES[rtype]
    return enc_name(name) + struct.pack(">HHIH", rtype, 1, ttl, len(rdata)) + rdata

def rd_a(ip):        return socket.inet_aton(ip)
def rd_name(n):      return enc_name(n)
def rd_mx(pref, n):  return struct.pack(">H", pref) + enc_name(n)
def rd_txt(s):       return bytes([len(s)]) + s.encode()
def rd_soa(mname, rname, serial, ref, ret, exp, minimum):
    return (enc_name(mname) + enc_name(rname) +
            struct.pack(">IIIII", serial, ref, ret, exp, minimum))


def dns_msg(txid, qname, qtype, answers, is_resp):
    flags = 0x8180 if is_resp else 0x0100   # resp: QR+RD+RA+NOERROR ; query: RD
    qd = 1
    an = len(answers) if is_resp else 0
    hdr = struct.pack(">HHHHHH", txid, flags, qd, an, 0, 0)
    body = dns_question(qname, qtype)
    if is_resp:
        for a in answers:
            body += a
    return hdr + body

def udp(src_ip, dst_ip, sport, dport, payload):
    length = 8 + len(payload)
    # checksum 0 (valido para UDP/IPv4) para no complicar
    return struct.pack(">HHHH", sport, dport, length, 0) + payload

def ipv4(src_ip, dst_ip, payload, proto=17):
    ver_ihl = 0x45
    total = 20 + len(payload)
    ident = 0
    ttl = 64
    hdr = struct.pack(">BBHHHBBH4s4s", ver_ihl, 0, total, ident, 0, ttl, proto, 0,
                      socket.inet_aton(src_ip), socket.inet_aton(dst_ip))
    # checksum
    s = 0
    for i in range(0, len(hdr), 2):
        s += (hdr[i] << 8) + hdr[i+1]
    s = (s >> 16) + (s & 0xffff); s += (s >> 16)
    cks = (~s) & 0xffff
    hdr = hdr[:10] + struct.pack(">H", cks) + hdr[12:]
    return hdr + payload

def eth(dst_mac, src_mac, payload):
    return dst_mac + src_mac + b"\x08\x00" + payload

packets = []  # (ts, bytes)
t0 = time.time()
txid = 0x1000

def exchange(qname, qtype_s, answers):
    """un par query(cliente->sv) + reply(sv->cliente)"""
    global txid, t0
    txid += 1
    qt = TYPES[qtype_s]
    # query
    q = dns_msg(txid, qname, qt, [], False)
    pkt = eth(SERVER_MAC, CLIENT_MAC, ipv4(CLIENT_IP, SERVER_IP, udp(CLIENT_IP, SERVER_IP, 50000+txid%1000, 53, q)))
    packets.append((t0, pkt)); t0 += 0.01
    # reply
    r = dns_msg(txid, qname, qt, answers, True)
    pkt = eth(CLIENT_MAC, SERVER_MAC, ipv4(SERVER_IP, CLIENT_IP, udp(SERVER_IP, CLIENT_IP, 53, 50000+txid%1000, r)))
    packets.append((t0, pkt)); t0 += 0.05

# --- los intercambios que reconstruyen la zona ---
exchange("protos.lab", "SOA",
         [rr("protos.lab","SOA", rd_soa("ns1.protos.lab","admin.protos.lab",
             2018010101, 3600, 1800, 604800, 86400))])
exchange("protos.lab", "NS",
         [rr("protos.lab","NS", rd_name("ns1.protos.lab"))])
exchange("ns1.protos.lab", "A",   [rr("ns1.protos.lab","A", rd_a("172.30.0.41"))])
exchange("www.protos.lab", "A",   [rr("www.protos.lab","A", rd_a("172.30.0.50"))])
exchange("mail.protos.lab", "A",  [rr("mail.protos.lab","A", rd_a("172.30.0.51"))])
exchange("protos.lab", "MX",
         [rr("protos.lab","MX", rd_mx(10, "mail.protos.lab"))])
exchange("ftp.protos.lab", "CNAME",
         [rr("ftp.protos.lab","CNAME", rd_name("www.protos.lab")),
          rr("www.protos.lab","A", rd_a("172.30.0.50"))])
exchange("protos.lab", "TXT",
         [rr("protos.lab","TXT", rd_txt("v=protos1"))])
# algunas queries extra "de ruido" tambien resolubles
exchange("www.protos.lab", "A",   [rr("www.protos.lab","A", rd_a("172.30.0.50"))])
exchange("mail.protos.lab", "MX", [])  # NODATA, ruido

# --- escribir pcap clasico ---
LINKTYPE_ETHERNET = 1
with open("http/backup.pcapng", "wb") as f:
    f.write(struct.pack("<IHHiIII", 0xa1b2c3d4, 2, 4, 0, 0, 65535, LINKTYPE_ETHERNET))
    for ts, pkt in packets:
        sec = int(ts); usec = int((ts - sec) * 1_000_000)
        f.write(struct.pack("<IIII", sec, usec, len(pkt), len(pkt)))
        f.write(pkt)

print(f"OK: http/backup.pcapng  ({len(packets)} paquetes, {len(packets)//2} intercambios)")
