# Soluciones — LabRecu2026

Spoilers. Todo se corre dentro de la VM (`make ws`). Legajo de ejemplo: `62815`.

---

## Ejercicio 1 — Correo (SMTP + POP3)

El `Subject` y el cuerpo llevan tildes; el punto 6 (que lo lea un MUA sin quoted-printable) obliga a codificar el cuerpo en **base64**. "Negrita" en un correo de texto plano se marca con `*asteriscos*` (convención de MUAs).

Preparar las partes codificadas:

```bash
printf '%s' '¡Buenos días!' | base64 -w0        # =?UTF-8?B?...?=  para el Subject
printf '%s\n' '*¡Hola mundo!*' | base64 -w0      # cuerpo en base64
```

Enviar hablando SMTP a mano (`-C` hace que netcat use CRLF):

```bash
nc -C mail.protos.foo 25
```
```smtp
EHLO alumno
MAIL FROM:<juan.perez@itba.edu.ar>
RCPT TO:<62815@mail.protos.foo>
DATA
From: Juan Perez <juan.perez@itba.edu.ar>
To: <62815@mail.protos.foo>
Subject: =?UTF-8?B?wqFCdWVub3MgZMOtYXMh?=
X-Parcial: 2026/2R
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: base64

KsKhSG9sYSBtdW5kbyEqCg==
.
QUIT
```

El `.` solo en una línea cierra el `DATA`. Verificar por POP3:

```bash
nc -C mail.protos.foo 110
```
```pop3
USER 62815@mail.protos.foo
PASS 62815@mail.protos.foo
STAT
RETR 1
QUIT
```

> El dominio `mail.protos.foo` también publica sus `MX` (`dig mail.protos.foo MX`): si querés, podés resolver el MX y conectarte a `mx1.protos.foo`, que apunta al mismo servidor.

---

## Ejercicio 2 — Proxy local al endpoint de metadata

El endpoint responde **403** si no viene el header `Metadata: true`, y el JSON si viene:

```bash
curl -i http://metadata.protos.foo                 # 403 Forbidden
curl -s -H "Metadata: true" http://metadata.protos.foo   # el JSON
```

La idea es un proxy reverso en tu nginx que **agregue** ese header, para después pedir con `curl http://metadata.local` sin opciones.

1. Que `metadata.local` apunte a tu VM — `/etc/hosts`:

```bash
echo "127.0.0.1 metadata.local" | sudo tee -a /etc/hosts
```

2. `/etc/nginx/sites-available/metadata-local`:

```nginx
server {
    listen 80;
    server_name metadata.local;
    location / {
        proxy_pass http://metadata.protos.foo;
        proxy_set_header Metadata true;
    }
}
```

3. Habilitar y arrancar:

```bash
sudo ln -s /etc/nginx/sites-available/metadata-local /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl start nginx        # o: sudo systemctl reload nginx

curl http://metadata.local        # devuelve el JSON, sin opciones de curl
```

---

## Ejercicio 3 — Zona `recu.protos.foo`

Primero averiguar los datos que pide el enunciado:

```bash
dig +short A bar.protos.foo        # 93.184.216.34  -> va en el A de la zona
dig +short MX mail.protos.foo      # 10 mx1.protos.foo. / 20 mx2.protos.foo.
```

Declarar la zona — `/etc/bind/named.conf.local`:

```
zone "recu.protos.foo" {
    type master;
    file "/etc/bind/db.recu.protos.foo";
};
```

`/etc/bind/db.recu.protos.foo`:

```zone
$ORIGIN recu.protos.foo.
$TTL 1w
@   IN SOA ns1.recu.protos.foo. admin.recu.protos.foo. (
        2026111101  ; serial
        1h          ; refresh
        15m         ; retry
        2w          ; expire
        1h )        ; negative cache TTL
@       1w  IN NS    ns1.recu.protos.foo.
ns1     1w  IN A     192.168.60.20
@       1h  IN A     93.184.216.34           ; punto 3: IP de bar.protos.foo, validez 1h
www     2w  IN CNAME recu.protos.foo.        ; punto 4: CNAME a la raíz, validez 2 semanas
@       1w  IN MX 10 mx1.protos.foo.         ; punto 5: mismos MX que mail.protos.foo, en orden
@       1w  IN MX 20 mx2.protos.foo.
@       1w  IN TXT   "v=spf1 ip4:1.2.3.4 -all"   ; punto 6: SPF, sólo 1.2.3.4
```

Notar los **TTL por registro** (`1h`, `2w`, `1w`): se ponen en la columna antes de `IN` y pisan el `$TTL` general, que es lo que pide cada punto.

Validar, arrancar y demostrar:

```bash
named-checkzone recu.protos.foo /etc/bind/db.recu.protos.foo     # loaded serial ... OK
sudo systemctl start bind9        # (o reload si ya estaba)

dig @localhost recu.protos.foo A      +noall +answer    # 3600  A 93.184.216.34
dig @localhost www.recu.protos.foo    +noall +answer    # 1209600 CNAME recu.protos.foo.
dig @localhost recu.protos.foo MX     +noall +answer    # 10 mx1 / 20 mx2  (TTL 604800)
dig @localhost recu.protos.foo TXT    +short            # "v=spf1 ip4:1.2.3.4 -all"
dig @localhost recu.protos.foo SOA | grep flags         # flags: qr aa rd ra  (aa = autoritativo)
```

---

## Ejercicio 4 — Persistencia de acceso SSH

Reconocer y entrar la primera vez con la contraseña filtrada:

```bash
nmap -sV parcial.protos.foo               # ver el puerto SSH
ssh parcial@parcial.protos.foo            # contraseña: holamundo
exit
```

Generar una clave propia (si no tenés) y dejarla autorizada en el servidor — así el acceso ya no depende de la contraseña:

```bash
ssh-keygen -t ed25519 -N '' -f ~/.ssh/id_ed25519      # si no existe
ssh-copy-id -i ~/.ssh/id_ed25519.pub parcial@parcial.protos.foo   # pide holamundo una vez
```

Si no estuviera `ssh-copy-id`, se hace a mano:

```bash
cat ~/.ssh/id_ed25519.pub | ssh parcial@parcial.protos.foo \
  'mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys'
```

Demostrar que ya no hace falta la contraseña (aunque el admin la cambie):

```bash
ssh -o PasswordAuthentication=no parcial@parcial.protos.foo 'whoami'   # -> parcial
```

Tu clave pública quedó en `~parcial/.ssh/authorized_keys`, que sobrevive a cualquier cambio de contraseña: ahí está la persistencia.

---

## ⭐ Ejercicio 2-bis — Negociación de contenido

El recurso `/foo/` tiene varias representaciones (HTML, JSON, texto plano) en varios idiomas. Se piden con los headers `Accept` (media type) y `Accept-Language` (idioma):

```bash
curl -H "Accept: text/plain" -H "Accept-Language: es" http://ejercicio2.protos.foo:8080/foo/
```

Sin `Accept-Language: es` el servidor responde `406 Not Acceptable` (hay texto plano, pero en varios idiomas). Un `curl` pelado trae la versión HTML.
