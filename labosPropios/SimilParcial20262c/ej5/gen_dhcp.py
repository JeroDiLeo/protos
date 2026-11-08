#!/usr/bin/env python3
"""
Genera dhcp.pcapng (pcap clasico) con un handshake DHCP completo (DORA):
  DISCOVER -> OFFER -> REQUEST -> ACK   (cliente DEDSEC)
Mas una segunda transaccion de OTRO cliente (xid distinto) como "ruido",
para que haya que identificar la transaccion correcta por xid / MAC.

Sin scapy: BOOTP/DHCP sobre UDP 67/68 a mano.
"""
import struct, socket

def mac(s): return bytes.fromhex(s.replace(":", ""))
BCAST_MAC = b"\xff\xff\xff\xff\xff\xff"

MAGIC = b"\x63\x82\x53\x63"

def opt(code, data=b""):
    return bytes([code, len(data)]) + data
def opt_ip(code, ip): return opt(code, socket.inet_aton(ip))
def opt_u32(code, v):  return opt(code, struct.pack(">I", v))

def dhcp(op, xid, chaddr, yiaddr, options, ciaddr="0.0.0.0", flags=0x8000):
    pkt  = struct.pack(">BBBB", op, 1, 6, 0)          # op htype hlen hops
    pkt += struct.pack(">I", xid)
    pkt += struct.pack(">HH", 0, flags)               # secs flags
    pkt += socket.inet_aton(ciaddr)                   # ciaddr
    pkt += socket.inet_aton(yiaddr)                   # yiaddr
    pkt += socket.inet_aton("0.0.0.0")                # siaddr
    pkt += socket.inet_aton("0.0.0.0")                # giaddr
    pkt += mac(chaddr) + b"\x00"*10                   # chaddr (16)
    pkt += b"\x00"*64                                 # sname
    pkt += b"\x00"*128                                # file
    pkt += MAGIC
    for o in options: pkt += o
    pkt += b"\xff"                                    # end
    return pkt

def udp(sport, dport, payload):
    return struct.pack(">HHHH", sport, dport, 8+len(payload), 0) + payload

def ipv4(src, dst, payload):
    total = 20 + len(payload)
    hdr = struct.pack(">BBHHHBBH4s4s", 0x45,0,total,0,0,64,17,0,
                      socket.inet_aton(src), socket.inet_aton(dst))
    s=0
    for i in range(0,len(hdr),2): s += (hdr[i]<<8)+hdr[i+1]
    s=(s>>16)+(s&0xffff); s+=(s>>16); cks=(~s)&0xffff
    return hdr[:10]+struct.pack(">H",cks)+hdr[12:]+payload

def eth(dst,src,payload): return dst+src+b"\x08\x00"+payload

packets=[]; t=1000.0
def push(ethframe):
    global t; packets.append((t, ethframe)); t+=0.08

SRV_MAC="02:42:ac:1e:00:01"; SRV_IP="172.30.0.1"
def dora(client_mac, xid, offered, hostname):
    # DISCOVER (cliente -> broadcast)
    o=[opt(53,b"\x01"), opt(12,hostname.encode()),
       opt(55, bytes([1,3,6,15,51]))]              # param request list
    push(eth(BCAST_MAC, mac(client_mac),
         ipv4("0.0.0.0","255.255.255.255",
         udp(68,67, dhcp(1,xid,client_mac,"0.0.0.0",o)))))
    # OFFER (server -> broadcast)
    o=[opt(53,b"\x02"), opt_ip(54,SRV_IP), opt_u32(51,86400),
       opt_ip(1,"255.255.255.0"), opt_ip(3,SRV_IP),
       opt_ip(6,"172.30.0.41"), opt(15,b"protos.lab")]
    push(eth(mac(client_mac), mac(SRV_MAC),
         ipv4(SRV_IP,"255.255.255.255",
         udp(67,68, dhcp(2,xid,client_mac,offered,o)))))
    # REQUEST (cliente -> broadcast, pide la IP ofrecida)
    o=[opt(53,b"\x03"), opt_ip(50,offered), opt_ip(54,SRV_IP),
       opt(12,hostname.encode())]
    push(eth(BCAST_MAC, mac(client_mac),
         ipv4("0.0.0.0","255.255.255.255",
         udp(68,67, dhcp(3,xid,client_mac,"0.0.0.0",o)))))
    # ACK (server -> broadcast)
    o=[opt(53,b"\x05"), opt_ip(54,SRV_IP), opt_u32(51,86400),
       opt_ip(1,"255.255.255.0"), opt_ip(3,SRV_IP),
       opt_ip(6,"172.30.0.41"), opt(15,b"protos.lab")]
    push(eth(mac(client_mac), mac(SRV_MAC),
         ipv4(SRV_IP,"255.255.255.255",
         udp(67,68, dhcp(5,xid,client_mac,offered,o)))))

# transaccion principal: cliente DEDSEC
dora("02:42:ac:1e:00:aa", 0xDED5EC01, "172.30.0.123", "cliente-dedsec")
# ruido: otro cliente, otro xid, otra IP
dora("02:42:ac:1e:00:bb", 0x0BADF00D, "172.30.0.150", "otra-pc")

with open("http/dhcp.pcapng","wb") as f:
    f.write(struct.pack("<IHHiIII",0xa1b2c3d4,2,4,0,0,65535,1))
    for ts,p in packets:
        sec=int(ts); usec=int((ts-sec)*1_000_000)
        f.write(struct.pack("<IIII",sec,usec,len(p),len(p))); f.write(p)
print(f"OK http/dhcp.pcapng  ({len(packets)} paquetes = 2 DORA)")
