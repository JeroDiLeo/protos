# SOLUCIONES — LabProtos2026

Spoilers. Todos los comandos se corren **dentro del workstation** (`docker compose exec workstation bash`). `LEGAJO=62815`.

---

## Ejercicio 1 — BIND / DNS

**Datos que da el lab por DNS:**
```bash
dig +short A bar.protos.foo          # -> 123.123.123.123   (va en el registro A)
dig +noall +answer MX mail.protos.foo
#   mail.protos.foo. ... MX 5 mx2.protos.foo.
#   mail.protos.foo. ... MX 10 mx1.protos.foo.
```

**`/etc/bind/named.conf.local`** (agregar):
```
zone "foo.example.org" {
    type master;
    file "/etc/bind/db.foo.example.org";
};
```

**`/etc/bind/db.foo.example.org`:**
```zone
$ORIGIN foo.example.org.
$TTL 1w
@   IN  SOA ns.foo.example.org. example\.admin.foo.com.ar. (
        2026060201 ; serial
        1h ; refresh
        15m ; retry
        1w ; expire
        1h ) ; negative cache TTL
@       1w  IN  NS    ns.foo.example.org.
ns      1w  IN  A     127.0.0.1
@       1h  IN  A     123.123.123.123          ; punto 3 (TTL 1h)
www     1w  IN  CNAME foo.example.org.         ; punto 4
@       1w  IN  MX 5  mx2.protos.foo.          ; punto 5 (mismo orden)
@       1w  IN  MX 10 mx1.protos.foo.
@       1w  IN  TXT   "v=spf1 ip4:1.2.3.4 -all" ; punto 6 (SPF)
```

**Validar y arrancar:**
```bash
sudo named-checkconf
sudo named-checkzone foo.example.org /etc/bind/db.foo.example.org   # -> OK
sudo named -c /etc/bind/named.conf        # arranca el daemon (sin systemd)
# recargar tras un cambio:  sudo rndc reload

dig @127.0.0.1 foo.example.org SOA +noall +answer
dig @127.0.0.1 foo.example.org A   +noall +answer    # 123.123.123.123
dig @127.0.0.1 www.foo.example.org CNAME +noall +answer
dig @127.0.0.1 foo.example.org MX  +noall +answer    # 5 mx2 / 10 mx1
dig @127.0.0.1 foo.example.org TXT +noall +answer    # v=spf1 ip4:1.2.3.4 -all
```

---

## Ejercicio 2 — proxy nginx a metadata

Primero confirmás que directo da 403:
```bash
curl http://metadata.protos.foo        # 403 Forbidden (nginx)
```

`/etc/hosts` (agregar):
```
127.0.0.1 metadata.local
```

`/etc/nginx/sites-available/metadata-local` (o un `conf.d/*.conf`):
```nginx
server {
    listen 80;
    server_name metadata.local;
    location / {
        proxy_pass http://metadata.protos.foo;
        proxy_set_header Metadata true;
        proxy_set_header Accept   "application/json";
    }
}
```

Habilitar, validar y arrancar:
```bash
sudo ln -s /etc/nginx/sites-available/metadata-local /etc/nginx/sites-enabled/metadata-local
sudo nginx -t
sudo nginx            # (o: sudo nginx -s reload si ya estaba corriendo)

curl http://metadata.local
# {"hola": "mundo", "vmName": "who_cares", "credentials": "superdupersecrettoken"}
```
Sin otras opciones de curl: el header lo agrega nginx (`proxy_set_header Metadata true`).

---

## Ejercicio 3 — HTTP a través de SOCKS5 (acumulativo)

```bash
B="http://ejercicio3.protos.foo:3126"
P="socks5h://proxy.protos.foo:1080"

curl -x $P $B/ -v                        # 302 -> Location: /debugger (+ X-Tip-Parcial)
curl -x $P $B/debugger -v                # X-Error_Message: Missing header "X-legajo"
curl -x $P $B/debugger -v -H x-legajo:62815                 # Content-Language: ru (ruso)
curl -x $P $B/debugger -v -H x-legajo:62815 -H accept-language:es        # GET ok, falta POST
curl -x $P $B/debugger -v -H x-legajo:62815 -H accept-language:es -XPOST # pide el JSON
curl -x $P $B/debugger -v -H x-legajo:62815 -H accept-language:es -XPOST \
     -H content-type:application/json -d '{"fix":"yes"}'                 # 401: admin/admin
curl -x $P $B/debugger -v -H x-legajo:62815 -H accept-language:es -XPOST \
     -H content-type:application/json -d '{"fix":"yes"}' -u admin:admin  # ¡APROBADO!
```
Clave: `socks5h` (con `h`) hace que el **proxy** resuelva `ejercicio3.protos.foo`; por eso funciona aunque desde el workstation ese host no sea ruteable.

---

## Ejercicio 4 — túnel SSH + netcat

Usá tu legajo como puerto (`62815`). Cuatro terminales (todas en el workstation salvo donde se indica):

**Terminal A** — abrir el túnel y, ya dentro de pampero, publicar el archivo:
```bash
ssh -L 62815:127.0.0.1:62815 alumno@pampero.itba.edu.ar
# (ya dentro de pampero:)
tail -F /tmp/parcial-20261 | nc -l 127.0.0.1 62815
```

**Terminal B** — recibir el flujo en el workstation:
```bash
docker compose exec workstation bash
: > archivo.log
nc 127.0.0.1 62815 > archivo.log
```

**Terminal C** — el comando que pide el enunciado:
```bash
docker compose exec workstation bash
tail -f archivo.log
```

El archivo late solo (una línea cada ~15s), así que en C van apareciendo líneas. Para probar a mano, **Terminal D** en pampero:
```bash
ssh alumno@pampero.itba.edu.ar 'echo "prueba $(date)" >> /tmp/parcial-20261'
```
El `nc -l` corre en **pampero**, no en el workstation. El puerto debe coincidir en `ssh -L`, `nc -l` y `nc`.

---

## Ejercicio 5 — SMTP + POP3 (MIME base64)

Subject y cuerpo tienen UTF-8; el enunciado pide no depender de quoted-printable → base64.
```bash
printf '%s' '¡Buenos días!' | base64 -w0      # wqFCdWVub3MgZMOtYXMh
printf '%s\r\n' '¡Hola mundo!' | base64 -w0    # wqFIb2xhIG11bmRvIQ0K
```

Enviar:
```bash
nc -C mail.sebikul.com 25
```
```smtp
EHLO ws
MAIL FROM:<kdubovitsky@itba.edu.ar>
RCPT TO:<62815@mail.sebikul.com>
DATA
Date: Thu, 04 Jun 2026 15:30:00 -0300
Message-ID: <62815-20260604@itba.edu.ar>
From: Keoni Dubovitsky <kdubovitsky@itba.edu.ar>
To: 62815@mail.sebikul.com
Subject: =?UTF-8?B?wqFCdWVub3MgZMOtYXMh?=
X-Parcial: 2024/2
MIME-Version: 1.0
Content-Type: text/plain; charset="UTF-8"
Content-Transfer-Encoding: base64

wqFIb2xhIG11bmRvIQ0K
.
QUIT
```

Verificar por POP3:
```bash
nc -C mail.sebikul.com 110
```
```pop3
USER 62815@mail.sebikul.com
PASS 62815@mail.sebikul.com
STAT
LIST
RETR 1
QUIT
```
El cuerpo decodifica a `¡Hola mundo!` (`printf wqFIb2xhIG11bmRvIQ0K | base64 -d`).

---

## recu-1 — variante con cuerpo en negrita a `mail.protos.foo`

El dominio `mail.protos.foo` no tiene A directo para mandar: se mira el MX.
```bash
dig mail.protos.foo MX +short        # 5 mx2.protos.foo / 10 mx1.protos.foo
nc -C mx1.protos.foo 25
```
"Negrita" en un mail de texto plano se hace con `*asteriscos*` (convención de MUAs). El cuerpo `*¡Hola mundo!*` en base64:
```bash
printf '%s\n' '*¡Hola mundo!*' | base64 -w0     # KsKhSG9sYSBtdW5kbyEqCg==
```
```smtp
EHLO ws
MAIL FROM:<kdubovitsky@itba.edu.ar>
RCPT TO:<62815@mail.protos.foo>
DATA
MIME-Version: 1.0
Date: Tue, 9 Jun 2026 16:20:00 -0300
Message-ID: <62815@mail.protos.foo>
X-Parcial: 2026/1R
Subject: =?UTF-8?B?wqFCdWVub3MgZMOtYXMh?=
From: Keoni Dubovitsky <kdubovitsky@itba.edu.ar>
To: <62815@mail.protos.foo>
Content-Type: text/plain; charset="UTF-8"
Content-Transfer-Encoding: base64

<pegar aca el base64 del cuerpo>
.
QUIT
```
Verificar por POP3 en `mail.protos.foo:110` con `USER/PASS 62815@mail.protos.foo`.

---

## recu-2 — persistir acceso SSH

```bash
# 1) reconocimiento
nmap -sV parcial.protos.foo
#   22/tcp   ssh      OpenSSH
#   80/tcp   http     nginx
#   8000/tcp http     SimpleHTTPServer (Python)

# 2) entrar con la contraseña filtrada
ssh parcial@parcial.protos.foo        # password: holamundo
exit

# 3) dejar autorizada tu clave publica (persistencia)
ssh-copy-id -i ~/.ssh/id_ed25519.pub parcial@parcial.protos.foo   # pide holamundo una vez

# 4) ahora entrás SIN contraseña, aunque el admin cambie la de 'parcial'
ssh -i ~/.ssh/id_ed25519 -o PasswordAuthentication=no parcial@parcial.protos.foo
```
La clave pública en `~parcial/.ssh/authorized_keys` sobrevive a cualquier cambio de contraseña: ahí está la persistencia.
