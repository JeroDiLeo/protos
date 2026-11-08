# SOLUCIONES — SimilParcial20262c

Spoilers. Intentá cada ejercicio antes de leer.
Todos los comandos asumen que le pegás a las IP de contenedor (Linux). Entre paréntesis queda la variante por `127.0.0.1`.

---

## Ejercicio 1 — HTTP + SOCKS5

**a) Modo verboso / headers.** Las pistas van en los *response headers*, así que `-v` (o `-i`):

```bash
curl -v http://172.30.0.11:3126/
#   (o: curl -v http://127.0.0.1:3126/)
```
En la salida aparecen:
```
< X-CTOS-Proxy: 172.30.0.12:1080 socks5
< X-CTOS-Target: http://secrets.ct.os/
< X-Wrench: usa curl --socks5-hostname ...
```
Para practicar `-H` (el server te hace eco):
```bash
curl -v -H "X-You: jerodileo" http://172.30.0.11:3126/
# < X-Wrench-Reply: te escucho, jerodileo
```

**b) Tunelizar por el SOCKS5.** La clave es que `secrets.ct.os` lo resuelve **el proxy**, no vos. Por eso `--socks5-hostname` (equivalente a `socks5h://`), que manda el *nombre* al proxy en vez de resolverlo localmente:

```bash
curl --socks5-hostname 172.30.0.12:1080 http://secrets.ct.os/
#   o:  curl -x socks5h://172.30.0.12:1080 http://secrets.ct.os/
#   o:  curl -x socks5h://127.0.0.1:1080  http://secrets.ct.os/
```
Devuelve:
```
FLAG{ej1-socks5-tunel-ctos-ok}
```

> Si usaras `--socks5` (sin `-hostname`) curl intentaría resolver `secrets.ct.os` en tu máquina y fallaría: ahí está la gracia del ejercicio (socks5 vs socks5h).
> Alternativa con **proxychains**: poné `socks5 172.30.0.12 1080` en `/etc/proxychains.conf` y corré `proxychains curl http://secrets.ct.os/`.

---

## Ejercicio 2 — nginx + clave SSH

La passphrase **no se crackea**: se arma una cadena de pistas con protocolos de la materia
(listing de directorio en HTTP → virtual host por `Host:` → header que sólo ves con `-v` → base64 como en Basic auth).

**a) Mirar `/sec/` y bajar la clave (misconfig de nginx, puerto 80).**
El directorio tiene `autoindex on`, así que el listado está abierto:
```bash
curl http://172.30.0.20/sec/
#   (o: curl http://127.0.0.1:2280/sec/)
# -> aparecen  mykey  y  pista.txt
curl http://172.30.0.20/sec/pista.txt      # leé la pista
curl http://172.30.0.20/sec/mykey -o mykey
chmod 600 mykey
head -1 mykey   # -----BEGIN OPENSSH PRIVATE KEY-----
```
La `pista.txt` te manda al panel del puerto 81 y te recuerda "Basic auth / modo verboso".

**b) Panel interno vía puerto 81 (vhost `secrethost`).** nginx elige el `server` por el header `Host`. El panel sólo responde si pedís con `Host: secrethost` al puerto 81. Pedilo en **modo verboso** para ver los headers:
```bash
curl -v -H "Host: secrethost" http://172.30.0.20:81/
#   (o: curl -v -H "Host: secrethost" http://127.0.0.1:2281/)
```
En el body está la flag del panel:
```
FLAG{ej2-vhost-secrethost-proxy-ok}
```
y en los **headers** aparece la passphrase codificada (igual que `user:pass` en Basic auth):
```
< X-Passphrase-B64: Ymxvb21DYWUyMDI2
```

**c) Decodificar la passphrase (base64).** Lo mismo que hace el navegador con las credenciales de Basic auth, pero al revés:
```bash
echo Ymxvb21DYWUyMDI2 | base64 -d ; echo
# -> bloomCae2026
```
La passphrase es **`bloomCae2026`**.

> Para aislar el header sin leer todo a ojo:
> ```bash
> curl -s -D - -o /dev/null -H "Host: secrethost" http://172.30.0.20:81/ \
>   | awk -F': ' '/X-Passphrase-B64/{print $2}' | tr -d "\r" | base64 -d; echo
> ```

**d) Login SSH como pepito.**
```bash
ssh -i mykey -p 22 pepito@172.30.0.20       # passphrase: bloomCae2026
#   (o: ssh -i mykey -p 2222 pepito@127.0.0.1)
cat flag.txt
# FLAG{ej2-ssh-login-pepito-ok}
```

---

## Ejercicio 3 — SMTP + IMAP

### Parte (a) — errores de la sesión SMTP

Errores en la transcripción del compañero:

| Línea | Error | Correcto |
|------|-------|----------|
| `nc ... 143` | 143 es **IMAP**, no SMTP | puerto **25** (`nc 172.30.0.30 25`) |
| `HELLO localhost` | comando inexistente | `HELO localhost` (o `EHLO`) |
| `MAIL TO: <you>` | no existe `MAIL TO` | `RCPT TO:<62345@pdc.lab>` |
| destinatario `<you>` | no es una dirección válida | una casilla real, p.ej. `<62345@pdc.lab>` |
| cuerpo → `QUIT` | falta cerrar el `DATA` | una línea con **solo un punto** `.` antes de `QUIT` |

Sesión SMTP correcta (podés tipearla y mandártela de verdad):
```bash
nc 172.30.0.30 25        # (o: nc 127.0.0.1 2525)
EHLO localhost
MAIL FROM:<friend@pdc.lab>
RCPT TO:<62345@pdc.lab>
DATA
Subject: Hola

Como estas?
.
QUIT
```
(Reemplazá `62345` por tu legajo. La línea en blanco separa headers del cuerpo; el `.` solo cierra el `DATA`.)

### Parte (b) — confirmar por IMAP

```bash
nc 172.30.0.30 143        # (o: nc 127.0.0.1 1143)
a login 62345 62345
b select INBOX
c fetch 1 body[]
d logout
```
Vas a ver el mensaje con:
```
FLAG{ej3-imap-fetch-ok}
```
> También podés usar POP3 (puerto 110): `USER 62345` / `PASS 62345` / `LIST` / `RETR 1`.
> O verlo cómodo con openssl/mutt. Hay un mensaje **pre-cargado**, así que (b) anda aunque no hayas hecho (a).

---

## Ejercicio 4 — restaurar zona DNS

**a) Leer el pcap.** Descargalo y miralo:
```bash
curl http://172.30.0.40:8000/backup.pcapng -o backup.pcapng
tshark -r backup.pcapng -Y "dns.flags.response==1" -T fields \
       -e dns.qry.name -e dns.resp.type -e dns.a -e dns.ns -e dns.cname -e dns.txt
# o abrilo en Wireshark y filtra:  dns
```
Registros que se recuperan:
```
protos.lab        SOA   ns1.protos.lab. admin.protos.lab. (serial 2018010101)
protos.lab        NS    ns1.protos.lab.
ns1.protos.lab    A     172.30.0.41
www.protos.lab    A     172.30.0.50
mail.protos.lab   A     172.30.0.51
protos.lab        MX    10 mail.protos.lab.
ftp.protos.lab    CNAME www.protos.lab.
protos.lab        TXT   "v=protos1"
```

**b) Escribir la zona + agregar el TXT nuevo.** Editá `ej4/bind/etc-bind/`:

`zones/db.protos.lab`:
```zone
$TTL 3600
@   IN  SOA ns1.protos.lab. admin.protos.lab. (
            2018010101  ; serial
            3600        ; refresh
            1800        ; retry
            604800      ; expire
            86400 )     ; minimum
@       IN  NS    ns1.protos.lab.
@       IN  MX 10 mail.protos.lab.
@       IN  TXT   "v=protos1"
@       IN  TXT   "cachito hola"      ; <-- record pedido en (b)
ns1     IN  A     172.30.0.41
www     IN  A     172.30.0.50
mail    IN  A     172.30.0.51
ftp     IN  CNAME www.protos.lab.
```

Descomentá la zona en `named.conf.local`:
```
zone "protos.lab" {
    type master;
    file "/etc/bind/zones/db.protos.lab";
};
```

Reiniciá y verificá:
```bash
docker compose restart ej4-bind

dig @172.30.0.41 protos.lab SOA +short       # (o @127.0.0.1 -p 5353)
dig @172.30.0.41 www.protos.lab A +short     # 172.30.0.50
dig @172.30.0.41 protos.lab MX +short        # 10 mail.protos.lab.
dig @172.30.0.41 ftp.protos.lab +short       # www.protos.lab. / 172.30.0.50
dig @172.30.0.41 protos.lab TXT +short       # "v=protos1" y "cachito hola"
```

Si `dig TXT` muestra `"cachito hola"`, el ejercicio está completo.
> Tip: `named-checkzone protos.lab ej4/bind/etc-bind/zones/db.protos.lab` valida la sintaxis antes de reiniciar.

---
---

# ⭐ SOLUCIONES — EJERCICIOS EXTRA

## Ejercicio 5 (EXTRA) — DHCP

```bash
curl http://172.30.0.60:8000/dhcp.pcapng -o dhcp.pcapng    # (o 127.0.0.1:8010)
```

Con `tshark` (o Wireshark, filtro `bootp` / `dhcp`):
```bash
tshark -r dhcp.pcapng -Y "dhcp" -T fields \
  -e dhcp.hw.mac_addr -e dhcp.option.dhcp -e dhcp.ip.your \
  -e dhcp.option.dhcp_server_id -e dhcp.option.ip_address_lease_time
```
Filtrando por el cliente `cliente-dedsec` (MAC `02:42:ac:1e:00:aa`, `xid = 0xded5ec01`):

| | Respuesta |
|---|---|
| **a)** mensajes | DISCOVER → OFFER → REQUEST → ACK. Es el handshake **DORA**. |
| **b)** IP asignada | **172.30.0.123** (campo `yiaddr` del OFFER/ACK) |
| **c)** server DHCP | **172.30.0.1** — viaja en la **opción 54** (DHCP Server Identifier) |
| **d)** lease / red | lease **86400 s** (opt 51), máscara **255.255.255.0** (opt 1), gateway **172.30.0.1** (opt 3), DNS **172.30.0.41** (opt 6), dominio **protos.lab** (opt 15) |
| **e)** xid | **0xded5ec01** |
| **f)** broadcast | El cliente todavía **no tiene IP**, por eso origen `0.0.0.0`; y como no sabe quién es el server, manda a **255.255.255.255** (broadcast). DHCP usa **UDP 67** (servidor) y **68** (cliente). |

> El otro cliente (`xid = 0x0badf00d`, MAC `...:bb`) es ruido: recibe `172.30.0.150`. Si contestaste con esa IP, miraste la transacción equivocada.

## Ejercicio 6 (EXTRA) — passphrase en el pcap

**a) Bajar clave y captura (listing abierto).**
```bash
curl http://172.30.0.70/sec/                       # (o 127.0.0.1:2680)
curl http://172.30.0.70/sec/mykey        -o mykey && chmod 600 mykey
curl http://172.30.0.70/sec/captura.pcapng -o captura.pcapng
```

**b) Seguir el TCP stream y decodificar.** En Wireshark: click derecho sobre un paquete de la sesión → *Follow → TCP Stream*. Vas a ver el request HTTP con:
```
Authorization: Basic cGVwaXRvOndyM25jaEtleTIwMjY=
```
Decodificá (es base64, igual que Basic auth):
```bash
echo cGVwaXRvOndyM25jaEtleTIwMjY= | base64 -d ; echo
# -> pepito:wr3nchKey2026
```
Por línea de comandos todo junto:
```bash
tshark -r captura.pcapng -Y "http.authorization" -T fields -e http.authorization \
  | awk '{print $2}' | base64 -d; echo
# -> pepito:wr3nchKey2026
```
La passphrase es **`wr3nchKey2026`** (el usuario `pepito` confirma a quién pertenece).

**c) Login SSH.**
```bash
ssh -i mykey -p 22 pepito@172.30.0.70       # passphrase: wr3nchKey2026
#   (o: ssh -i mykey -p 2622 pepito@127.0.0.1)
cat flag.txt
# FLAG{ej6-pcap-basicauth-ssh-ok}
```
