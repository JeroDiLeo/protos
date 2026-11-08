# Lab SimilParcial20262c — Consignas

> Protocolos de Comunicación · práctico tipo parcial 2026-2C
> Temática *Watch Dogs* (es solo ambientación; todo es HTTP, SOCKS5, nginx, SSH, SMTP/IMAP y DNS).

Levantá el lab con `./levantar.sh`. Estás en Linux, así que podés pegarle directo a las IP de cada contenedor (`172.30.0.x`). Si preferís, cada servicio también está publicado en `127.0.0.1` (ver el mapa que imprime `levantar.sh`).

No mires `solucion/` hasta haber intentado. Cada ejercicio tiene una `FLAG{...}` que confirma que lo resolviste.

---

## Ejercicio 1 — HTTP + proxy SOCKS5

Pertenecés a un grupo que necesita entrar al sistema de ctOS. Conectate al contacto inicial en:

```
http://172.30.0.11:3126/
```

a) Hacé el pedido HTTP y leé el mensaje. **Activá el modo verboso**: el contacto dejó pistas en los *headers* de la respuesta (no se ven en el body).

b) Hay un servidor oculto en `http://secrets.ct.os/` cuya IP está detrás de un **proxy SOCKS5** que corre en `172.30.0.12:1080`. Tunelizá a través del proxy y traé el contenido de `secrets.ct.os`. Ojo: el nombre `secrets.ct.os` **sólo lo resuelve el proxy**, no tu máquina.

**Entregá:** el comando exacto que usaste y la `FLAG` que devuelve el servidor oculto.

---

## Ejercicio 2 — nginx mal configurado + clave SSH

El host `172.30.0.20` corre **nginx** con dos `server` blocks:

- uno en `listen 80;` con `root /var/www;`
- otro en `listen 81;` con `server_name secrethost;` que hace `proxy_pass` a un servicio interno en `127.0.0.1:8080`.

Además corre **OpenSSH**, que sólo acepta login del usuario `pepito` y **sólo con clave privada**. Sabemos que esa clave privada quedó guardada (por error) en `/var/www/sec/mykey`, pero `pepito` le puso **passphrase**.

a) Aprovechá la mala config de nginx (puerto 80) para **mirar qué hay en `/sec/`** y descargá la clave privada. Fijate que el directorio tiene el listado abierto: además de la clave hay una pista.

b) El `server` del puerto 81 (`secrethost`) expone un **panel interno** vía `proxy_pass`. Accedé a ese panel **sin** estar dentro del host (pista: nginx elige el `server` por el header `Host:`). Traé su `FLAG`.

c) Averiguá la **passphrase** de la clave siguiendo las pistas. No hay que "adivinarla": está a la vista si sabés dónde mirar en la respuesta HTTP del panel. **Activá el modo verboso** y acordate de cómo viajan las credenciales en *Basic auth*.

d) Con la passphrase, hacé **login por SSH** como `pepito` y leé `~/flag.txt`.

**Entregá:** los comandos, cómo obtuviste la passphrase, y las dos `FLAG` (panel 81 y SSH).

---

## Ejercicio 3 — SMTP (a mano) + verificación por IMAP

El servidor de correo es `172.30.0.30` (dominio `pdc.lab`). Tu usuario y contraseña son **tu legajo** (lo configurás en `.env`, por defecto `62345`).

### Parte (a) — marcá los errores

Un compañero intentó mandarte un mail con `nc` pero se equivocó al escribir el protocolo. **Marcá todos los errores** de esta sesión (hay varios) y escribí la versión correcta:

```
ubuntu> nc 172.30.0.30 143
HELLO localhost
MAIL FROM:<friend@pdc.lab>
MAIL TO: <you>
DATA
Subject: Hola
Como estas?
QUIT
```

> Pista: fijate el **puerto**, el **comando de saludo**, cómo se indica el **destinatario**, y **cómo se cierra el cuerpo** del mensaje antes de `QUIT`.

### Parte (b) — confirmá que llegó

Tu compañero jura que el mensaje "tuvo que llegar". **Confirmalo** conectándote por **IMAP** al mismo servidor `172.30.0.30` con usuario `[legajo]` y contraseña `[legajo]`. Listá la casilla y leé el mensaje.

**Entregá:** la transcripción SMTP corregida (part a) y los comandos IMAP + la `FLAG` del mensaje (part b).

---

## Ejercicio 4 — restaurar zona DNS (bind9) desde un pcap

Alguien borró los archivos de config de la zona DNS y el cron de backups no corre desde 2018. Por suerte quedó una **captura pcap** con *queries* y *replies* del nameserver:

```
http://172.30.0.40:8000/backup.pcapng
```

a) Descargá la captura y **reconstruí la configuración original** de la zona (`named.conf.local` + archivo de zona) a partir de los registros que ves en el pcap. Levantala en **bind9** (contenedor `ej4-bind`, `172.30.0.41:53`).

b) Agregá además un **record TXT** en el dominio raíz de la zona que diga `cachito hola`.

c) Verificá con `dig` que la zona responde (SOA, NS, los A, el MX, el CNAME y tu TXT nuevo).

> Cómo editás bind: los archivos de `/etc/bind` del contenedor están *montados* en `ej4/bind/etc-bind/` de tu disco. Editás ahí y hacés `docker compose restart ej4-bind`.

**Entregá:** el archivo de zona reconstruido y la salida de `dig` mostrando el TXT `cachito hola`.

---
---

# ⭐ EJERCICIOS EXTRA (no estaban en el parcial)

> Los dos de abajo **no** forman parte del parcial 2026-2C. Los agregué para
> que practiques DHCP y una variante del Ej2. Mismo criterio: todo con cosas
> vistas en la materia / la guía.

## Ejercicio 5 (EXTRA) — DHCP: analizar el handshake

Se capturó el arranque de un cliente pidiendo IP por DHCP. Bajá la captura:

```
http://172.30.0.60:8000/dhcp.pcapng     (o 127.0.0.1:8010)
```

Abrila en Wireshark (o `tshark`) y respondé, **para el cliente `cliente-dedsec`** (MAC `02:42:ac:1e:00:aa`):

a) ¿Qué mensajes DHCP aparecen y en qué orden? ¿Cómo se llama ese intercambio?
b) ¿Qué **IP** le terminó asignando el servidor?
c) ¿Cuál es la **IP del servidor DHCP** (¿en qué opción viaja)?
d) ¿Cuánto dura el **lease**? ¿Cuál es la **máscara**, el **gateway**, el **DNS** y el **dominio** ofrecidos?
e) ¿Cuál es el **transaction id (xid)** de esa transacción?
f) En el DISCOVER y el REQUEST, ¿por qué la IP de origen es `0.0.0.0` y van a **broadcast** (`255.255.255.255`)? ¿En qué puertos UDP trabaja DHCP?

> Ojo: en la captura hay **dos** clientes distintos (dos xid). Asegurate de mirar el correcto.

**Entregá:** las respuestas (a–f) y el filtro/dato de Wireshark de dónde sacaste cada una.

## Ejercicio 6 (EXTRA) — variante del Ej2: la passphrase está en un pcap

Igual que el Ej2 (nginx `172.30.0.70` con la clave de `pepito` expuesta por HTTP y login SSH sólo por clave), **pero** esta vez la passphrase no está en ningún header: quedó **sniffeada en una captura de red**.

a) Entrá a `http://172.30.0.70/sec/` (listado abierto) y bajá `mykey` y `captura.pcapng`.
b) Abrí `captura.pcapng` en Wireshark, **seguí el TCP stream** de la sesión HTTP y encontrá el header `Authorization`. Está en **base64** (como en *Basic auth*): decodificalo para obtener `usuario:passphrase`.
c) Con esa passphrase, hacé **login SSH** como `pepito` (`172.30.0.70`, puerto 22 / `2622`) y leé `~/flag.txt`.

**Entregá:** cómo seguiste el stream, el valor decodificado y la `FLAG`.
