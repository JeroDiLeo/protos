#!/usr/bin/env bash
# =====================================================================
#  Lab de practica: clave SSH expuesta + passphrase que hay que AVERIGUAR
#  (estilo parcial, sin romper nada por diccionario)
#
#  Montas en tu propia VM los "servidores del otro lado". Vos corres los
#  comandos del cliente (curl, dig, ssh) para: bajar una clave privada que
#  quedo expuesta, averiguar su passphrase a partir de una pista, y hacer
#  login por SSH. Todo es localhost: no toca internet ni la red real.
#
#  USALO COMO TU USUARIO (no 'sudo bash'). Pide sudo solo cuando hace falta.
# =====================================================================
set -u

LAB="$HOME/lab-ssh"
WEB="$LAB/web"
MARK="lab-ssh"                      # marca para limpiar authorized_keys

# puertos (altos, para no chocar con el otro lab ni con servicios reales)
STATIC=8060                        # servidor HTTP estatico (sirve las claves)
PROXY=8061                         # reverse proxy (server_name secrethost)
INTERNAL=9061                      # servicio interno: SOLO se llega por el proxy
DNS=5360                           # DNS de referencia (A y TXT)

# passphrases de cada clave (el alumno NO las ve; las descubre resolviendo)
P1="secrethost-abierto-2026"       # Ej1: la devuelve el servicio interno
P2="203.0.113.47"                  # Ej2: es la IP de un nombre en el DNS
P3="clave-tras-doble-salto"        # Ej3: detras del proxy, con token de DNS
TOKEN="zorro-plateado"             # Ej3: token publicado en un TXT del DNS

say(){ printf '  %s\n' "$*"; }
hr(){ printf '%s\n' "----------------------------------------------------------------"; }

# ------------------------------------------------------------------ keys
gen_keys(){
  mkdir -p "$WEB/sec" "$WEB/privado/respaldo" "$LAB/keys"
  # Ej1: ed25519, se sirve en /sec/mykey1
  [ -f "$LAB/keys/key1" ] || ssh-keygen -q -t ed25519 -N "$P1" -f "$LAB/keys/key1" -C "$MARK-1"
  # Ej2: rsa (estilo .pem), se sirve en una ruta oculta
  [ -f "$LAB/keys/key2" ] || ssh-keygen -q -t rsa -b 2048 -N "$P2" -f "$LAB/keys/key2" -C "$MARK-2"
  # Ej3: ed25519, se sirve solo con el Host correcto
  [ -f "$LAB/keys/key3" ] || ssh-keygen -q -t ed25519 -N "$P3" -f "$LAB/keys/key3" -C "$MARK-3"
  # copias "expuestas" por HTTP, con permisos abiertos a proposito (644)
  cp -f "$LAB/keys/key1" "$WEB/sec/mykey1"
  cp -f "$LAB/keys/key2" "$WEB/privado/respaldo/id_rsa"
  cp -f "$LAB/keys/key3" "$LAB/keys/key3.serve"
  chmod 644 "$WEB/sec/mykey1" "$WEB/privado/respaldo/id_rsa" "$LAB/keys/key3.serve"
}

authorize(){
  mkdir -p "$HOME/.ssh"; touch "$HOME/.ssh/authorized_keys"; chmod 700 "$HOME/.ssh"; chmod 600 "$HOME/.ssh/authorized_keys"
  if ! grep -q "$MARK" "$HOME/.ssh/authorized_keys" 2>/dev/null; then
    cat "$LAB/keys/key1.pub" "$LAB/keys/key2.pub" "$LAB/keys/key3.pub" >> "$HOME/.ssh/authorized_keys"
    say "autorice las 3 claves de practica en tu cuenta (se sacan con 'down')"
  fi
}

# ------------------------------------------------------------------ servers
write_servers(){
  mkdir -p "$LAB"
  # ---- servidor HTTP estatico (sirve claves + pistas), con vhost para Ej3
  cat > "$LAB/static.py" <<'PY'
import http.server, os
WEB=os.environ["WEB"]; KEY3=os.environ["KEY3_SERVE"]
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def txt(self,c,s,ct="text/plain; charset=utf-8"):
        b=s.encode() if isinstance(s,str) else s
        self.send_response(c); self.send_header("Content-Type",ct)
        self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b)
    def sendfile(self,path):
        try:
            with open(path,"rb") as f: data=f.read()
        except OSError: return self.txt(404,"Not Found\n")
        self.txt(200,data,"application/octet-stream")
    def do_GET(self):
        host=self.headers.get("Host",""); p=self.path.split("?")[0]
        if p=="/": return self.txt(200,"<html><body>Servidor de archivos.\n<!-- no hay nada publico aca; revisa /robots.txt --></body></html>\n","text/html; charset=utf-8")
        if p=="/robots.txt": return self.txt(200,"User-agent: *\nDisallow: /privado/respaldo/\n")
        if p=="/sec/mykey1": return self.sendfile(os.path.join(WEB,"sec/mykey1"))
        if p=="/privado/respaldo/id_rsa": return self.sendfile(os.path.join(WEB,"privado/respaldo/id_rsa"))
        if p=="/mykey3":
            if not host.startswith("archivos.lab"): return self.txt(404,"Not Found (vhost incorrecto)\n")
            return self.sendfile(KEY3)
        self.txt(404,"Not Found\n")
http.server.HTTPServer(("127.0.0.1",int(os.environ["STATIC"])),H).serve_forever()
PY

  # ---- servicio INTERNO: solo responde si el pedido viene por el proxy
  cat > "$LAB/internal.py" <<'PY'
import http.server, os, urllib.parse as up
P1=os.environ["P1"]; P3=os.environ["P3"]; TOKEN=os.environ["TOKEN"]
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def txt(self,c,s):
        b=(s+"\n").encode(); self.send_response(c)
        self.send_header("Content-Type","text/plain; charset=utf-8")
        self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        if self.headers.get("X-Internal-Gate")!="1":
            return self.txt(403,"Servicio interno: solo se accede a traves del proxy")
        u=up.urlparse(self.path); q=up.parse_qs(u.query)
        if u.path=="/":
            return self.txt(200,"Bienvenido al panel interno. La passphrase de mykey1 es: "+P1)
        if u.path=="/clave":
            if q.get("token",[""])[0]!=TOKEN:
                return self.txt(400,"Falta o es invalido el parametro token")
            return self.txt(200,"La passphrase de mykey3 es: "+P3)
        self.txt(404,"no existe esa ruta interna")
http.server.HTTPServer(("127.0.0.1",int(os.environ["INTERNAL"])),H).serve_forever()
PY

  # ---- reverse proxy: server_name secrethost -> reenvia al interno
  cat > "$LAB/proxy.py" <<'PY'
import http.server, http.client, os
INT=int(os.environ["INTERNAL"])
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def txt(self,c,s):
        b=(s+"\n").encode(); self.send_response(c)
        self.send_header("Content-Type","text/plain; charset=utf-8")
        self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        if "secrethost" not in self.headers.get("Host",""):
            return self.txt(404,"No existe ningun sitio con ese nombre en este servidor")
        try:
            c=http.client.HTTPConnection("127.0.0.1",INT,timeout=5)
            c.request("GET",self.path,headers={"X-Internal-Gate":"1"})
            r=c.getresponse(); body=r.read()
            self.send_response(r.status)
            self.send_header("Content-Type","text/plain; charset=utf-8")
            self.send_header("Content-Length",str(len(body))); self.end_headers(); self.wfile.write(body)
        except Exception as e:
            self.txt(502,"proxy no pudo contactar el backend")
http.server.HTTPServer(("127.0.0.1",int(os.environ["PROXY"])),H).serve_forever()
PY

  # ---- DNS de referencia minimo (A y TXT) sobre UDP
  cat > "$LAB/dns.py" <<'PY'
import socket, struct, os
P2=os.environ["P2"]; TOKEN=os.environ["TOKEN"]
REC={ ("llave.internal.lab",1):("A",P2),
      ("token.internal.lab",16):("TXT",TOKEN) }
def rdname(d,o):
    out=[]
    while True:
        n=d[o]
        if n==0: o+=1; break
        out.append(d[o+1:o+1+n].decode()); o+=1+n
    return ".".join(out),o
def resp(d):
    tid=d[:2]; name,o=rdname(d,12)
    qtype,qclass=struct.unpack(">HH",d[o:o+4]); o+=4; q=d[12:o]
    k=(name.lower(),qtype); an=b""; anc=0; flags=0x8183
    if k in REC:
        _,val=REC[k]
        if qtype==1: rdata=socket.inet_aton(val)
        else: b=val.encode(); rdata=bytes([len(b)])+b
        an=b"\xc0\x0c"+struct.pack(">HHIH",qtype,1,60,len(rdata))+rdata; anc=1; flags=0x8180
    return tid+struct.pack(">HHHHH",flags,1,anc,0,0)+q+an
s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
s.bind(("127.0.0.1",int(os.environ["DNS"])))
while True:
    try:
        d,a=s.recvfrom(512); s.sendto(resp(d),a)
    except Exception: pass
PY
}

launch(){
  export WEB STATIC PROXY INTERNAL DNS P1 P2 P3 TOKEN
  export KEY3_SERVE="$LAB/keys/key3.serve"
  for n in static internal proxy dns; do
    pgrep -f "$LAB/$n.py" >/dev/null || { nohup python3 "$LAB/$n.py" >/dev/null 2>&1 & }
  done
  sleep 1
}

start_sshd(){
  if command -v systemctl >/dev/null 2>&1; then
    if ! timeout 5 systemctl is-active --quiet ssh 2>/dev/null; then
      timeout 8 sudo systemctl start ssh 2>/dev/null && say "sshd iniciado" || say "no pude iniciar sshd (instalalo: sudo apt install openssh-server)"
    else
      say "sshd ya estaba corriendo"
    fi
  fi
}

# ------------------------------------------------------------------ up/status/down
up(){
  hr; say "LAB CLAVE+PASSPHRASE  -  levantando el entorno"; hr
  gen_keys
  write_servers
  launch
  authorize
  start_sshd
  hr
  say "Entorno listo. Servidores (todos en 127.0.0.1):"
  say "  HTTP estatico .... puerto $STATIC"
  say "  Reverse proxy .... puerto $PROXY   (server_name secrethost)"
  say "  Servicio interno . puerto $INTERNAL  (solo via proxy)"
  say "  DNS referencia ... puerto $DNS   (UDP; usa: dig @127.0.0.1 -p $DNS ...)"
  say ""
  say "Las consignas estan en consignas.md. Para entrar vas a usar tu propio"
  say "usuario: ssh -i <clave> $USER@localhost  (en el parcial el usuario te lo dan)."
  hr
}

status(){
  hr; say "ESTADO"; hr
  for pp in "static.py:$STATIC" "proxy.py:$PROXY" "internal.py:$INTERNAL" "dns.py:$DNS"; do
    f="${pp%%:*}"; prt="${pp##*:}"
    if pgrep -f "$LAB/$f" >/dev/null; then say "[on ] $f  (puerto $prt)"; else say "[off] $f  (puerto $prt)"; fi
  done
  if grep -q "$MARK" "$HOME/.ssh/authorized_keys" 2>/dev/null; then say "[on ] claves de practica autorizadas en tu cuenta"; else say "[off] claves de practica NO autorizadas"; fi
  if command -v systemctl >/dev/null 2>&1 && timeout 5 systemctl is-active --quiet ssh 2>/dev/null; then say "[on ] sshd"; else say "[off] sshd (o no se pudo consultar)"; fi
  hr
}

down(){
  hr; say "APAGANDO y limpiando"; hr
  for n in static internal proxy dns; do pkill -f "$LAB/$n.py" 2>/dev/null && say "corte $n"; done
  if grep -q "$MARK" "$HOME/.ssh/authorized_keys" 2>/dev/null; then
    sed -i "/$MARK/d" "$HOME/.ssh/authorized_keys" && say "saque las claves de practica de authorized_keys"
  fi
  say "listo. (las claves generadas quedan en $LAB/keys por si queres repetir; borralas con: rm -rf $LAB)"
  hr
}

case "${1:-}" in
  up)     up ;;
  status) status ;;
  down)   down ;;
  *) echo "uso: bash lab-ssh.sh {up|status|down}" ;;
esac
