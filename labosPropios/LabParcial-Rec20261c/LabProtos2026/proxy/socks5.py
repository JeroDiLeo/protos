#!/usr/bin/env python3
"""
Proxy SOCKS5 mínimo para el lab (Ej3). Soporta el método no-auth y el comando
CONNECT con destino IPv4, IPv6 o NOMBRE (ATYP=3). La resolución del nombre la
hace ESTE proceso (por eso el alumno usa socks5h:// y funciona aunque el host
destino no sea ruteable desde el workstation).
"""
import socket, struct, threading, select, os

LISTEN_PORT = int(os.environ.get("PORT", "1080"))

def pipe(a, b):
    try:
        while True:
            r, _, _ = select.select([a, b], [], [], 60)
            if not r: break
            for s in r:
                data = s.recv(65536)
                if not data:
                    return
                (b if s is a else a).sendall(data)
    except Exception:
        pass
    finally:
        for s in (a, b):
            try: s.close()
            except: pass

def handle(cli):
    try:
        # saludo: VER, NMETHODS, METHODS...
        ver = cli.recv(1)
        if ver != b"\x05":
            cli.close(); return
        nm = cli.recv(1)[0]
        cli.recv(nm)                      # ignoramos la lista, elegimos no-auth
        cli.sendall(b"\x05\x00")

        # request: VER CMD RSV ATYP ...
        hdr = cli.recv(4)
        if len(hdr) < 4:
            cli.close(); return
        ver, cmd, _, atyp = hdr[0], hdr[1], hdr[2], hdr[3]
        if atyp == 1:                     # IPv4
            host = socket.inet_ntoa(cli.recv(4))
        elif atyp == 3:                   # nombre de dominio
            ln = cli.recv(1)[0]; host = cli.recv(ln).decode()
        elif atyp == 4:                   # IPv6
            host = socket.inet_ntop(socket.AF_INET6, cli.recv(16))
        else:
            cli.sendall(b"\x05\x08\x00\x01\x00\x00\x00\x00\x00\x00"); cli.close(); return
        port = struct.unpack(">H", cli.recv(2))[0]

        if cmd != 1:                      # solo CONNECT
            cli.sendall(b"\x05\x07\x00\x01\x00\x00\x00\x00\x00\x00"); cli.close(); return

        try:
            remote = socket.create_connection((host, port), 10)
        except Exception:
            cli.sendall(b"\x05\x05\x00\x01\x00\x00\x00\x00\x00\x00"); cli.close(); return

        # respuesta OK (BND.ADDR/PORT en 0, los clientes lo aceptan)
        cli.sendall(b"\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00")
        pipe(cli, remote)
    except Exception:
        try: cli.close()
        except: pass

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", LISTEN_PORT)); s.listen(100)
    print(f"socks5 proxy en :{LISTEN_PORT}", flush=True)
    while True:
        cli, _ = s.accept()
        threading.Thread(target=handle, args=(cli,), daemon=True).start()

if __name__ == "__main__":
    main()
