import socket, struct, sys
q = struct.pack(">HHHHHH",1,0x0100,1,0,0,0)+b"\x04mail\x06protos\x03foo\x00"+struct.pack(">HH",1,1)
try:
    s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.settimeout(2)
    s.sendto(q,("127.0.0.1",53)); d,_=s.recvfrom(512)
    sys.exit(0 if struct.unpack(">H",d[6:8])[0]>=1 else 1)
except Exception: sys.exit(1)
