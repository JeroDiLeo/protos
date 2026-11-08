#!/usr/bin/env python3
"""
Genera captura.pcapng (pcap clasico): una sesion HTTP sobre TCP donde el
cliente manda  Authorization: Basic base64(pepito:<PASSPHRASE>).
El alumno hace "Follow TCP Stream" en Wireshark, ve el header y decodifica base64.

PASSPHRASE debe coincidir con la que cifra la clave SSH del contenedor ej6-host.
Si la cambias alla, volve a correr:  python3 gen_capture.py <PASSPHRASE>
"""
import struct, socket, base64, sys

PASSPHRASE = sys.argv[1] if len(sys.argv) > 1 else "wr3nchKey2026"
CRED = f"pepito:{PASSPHRASE}"
B64  = base64.b64encode(CRED.encode()).decode()

CLI_MAC = bytes.fromhex("0242ac1e004d"); SRV_MAC = bytes.fromhex("0242ac1e0046")
CLI_IP, SRV_IP = "172.30.0.77", "172.30.0.70"
CLI_PORT, SRV_PORT = 44444, 80

def cksum(b):
    if len(b) % 2: b += b"\x00"
    s=0
    for i in range(0,len(b),2): s += (b[i]<<8)+b[i+1]
    s=(s>>16)+(s&0xffff); s+=(s>>16)
    return (~s)&0xffff

def tcp(src_ip,dst_ip,sport,dport,seq,ack,flags,payload=b""):
    off=(5<<4)
    hdr=struct.pack(">HHIIBBHHH",sport,dport,seq,ack,off,flags,65535,0,0)
    pseudo=socket.inet_aton(src_ip)+socket.inet_aton(dst_ip)+bytes([0,6])+struct.pack(">H",len(hdr)+len(payload))
    c=cksum(pseudo+hdr+payload)
    hdr=hdr[:16]+struct.pack(">H",c)+hdr[18:]
    return hdr+payload

def ipv4(src,dst,payload):
    total=20+len(payload)
    hdr=struct.pack(">BBHHHBBH4s4s",0x45,0,total,0x4000&0,0,64,6,0,
                    socket.inet_aton(src),socket.inet_aton(dst))
    hdr=hdr[:10]+struct.pack(">H",cksum(hdr))+hdr[12:]
    return hdr+payload

def eth(dst,src,payload): return dst+src+b"\x08\x00"+payload

pkts=[]; t=500.0
def push(frame):
    global t; pkts.append((t,frame)); t+=0.02

C0=1000; S0=77000
# 3-way handshake
push(eth(SRV_MAC,CLI_MAC, ipv4(CLI_IP,SRV_IP, tcp(CLI_IP,SRV_IP,CLI_PORT,SRV_PORT,C0,0,0x02))))            # SYN
push(eth(CLI_MAC,SRV_MAC, ipv4(SRV_IP,CLI_IP, tcp(SRV_IP,CLI_IP,SRV_PORT,CLI_PORT,S0,C0+1,0x12))))         # SYN-ACK
push(eth(SRV_MAC,CLI_MAC, ipv4(CLI_IP,SRV_IP, tcp(CLI_IP,SRV_IP,CLI_PORT,SRV_PORT,C0+1,S0+1,0x10))))       # ACK

req = (f"GET /panel/ HTTP/1.1\r\n"
       f"Host: secrethost\r\n"
       f"Authorization: Basic {B64}\r\n"
       f"User-Agent: dedsec-cli/1.0\r\n"
       f"Accept: */*\r\n\r\n").encode()
push(eth(SRV_MAC,CLI_MAC, ipv4(CLI_IP,SRV_IP, tcp(CLI_IP,SRV_IP,CLI_PORT,SRV_PORT,C0+1,S0+1,0x18,req))))    # PSH-ACK (request)
push(eth(CLI_MAC,SRV_MAC, ipv4(SRV_IP,CLI_IP, tcp(SRV_IP,CLI_IP,SRV_PORT,CLI_PORT,S0+1,C0+1+len(req),0x10)))) # ACK

body=b"<html><body>ok, credenciales aceptadas. nada mas que ver aca.</body></html>"
resp=(f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: {len(body)}\r\n\r\n").encode()+body
push(eth(SRV_MAC,CLI_MAC, ipv4(SRV_IP,CLI_IP, tcp(SRV_IP,CLI_IP,SRV_PORT,CLI_PORT,S0+1,C0+1+len(req),0x18,resp)))) # PSH-ACK (resp)
push(eth(CLI_MAC,SRV_MAC, ipv4(CLI_IP,SRV_IP, tcp(CLI_IP,SRV_IP,CLI_PORT,SRV_PORT,C0+1+len(req),S0+1+len(resp),0x10)))) # ACK

with open("host/captura.pcapng","wb") as f:
    f.write(struct.pack("<IHHiIII",0xa1b2c3d4,2,4,0,0,65535,1))
    for ts,p in pkts:
        sec=int(ts); usec=int((ts-sec)*1_000_000)
        f.write(struct.pack("<IIII",sec,usec,len(p),len(p))); f.write(p)
print(f"OK host/captura.pcapng  ({len(pkts)} paquetes)")
print(f"   cred en claro: {CRED}")
print(f"   header capturado: Authorization: Basic {B64}")
