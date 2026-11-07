# Cheatsheet: correo (SMTP, POP3, MIME y formato)

Recetas de parciales: [smtp-pop3-base64_1c2026.md](smtp-pop3-base64_1c2026.md) · [smtp-multipart-negrita_recu2026.md](smtp-multipart-negrita_recu2026.md) · [smtp-variantes-mime.md](smtp-variantes-mime.md) · [smtp-pop3-mision-catedra.md](smtp-pop3-mision-catedra.md) · práctica con corrector: [lab-correo/](../lab-correo/).

---

## 1. Lo básico

| Protocolo | Puerto | Para qué |
|---|---|---|
| SMTP | **25** | servidor ↔ servidor (recepción, MX). Sin auth; solo acepta destinatarios de **sus** dominios |
| SMTP submission | **587** | cliente → su servidor para mandar **afuera**. Exige `AUTH` (y normalmente `STARTTLS`) |
| SMTPS | 465 | submission con TLS desde el inicio |
| POP3 | **110** | leer / bajar / borrar del buzón |
| POP3S | 995 | POP3 con TLS |
| IMAP / IMAPS | 143 / 993 | leer dejando en el servidor, carpetas |

**Sobre vs. carta**
- **Sobre** (comandos SMTP): `MAIL FROM:<…>` y `RCPT TO:<…>`. Dice **a quién se entrega** de verdad.
- **Carta** (después de `DATA`): headers `From:`, `To:`, `Cc:`, `Subject:`… + línea vacía + cuerpo. Es **lo que ve** el MUA.
- Pueden no coincidir: el correo llega a los `RCPT TO`, aunque el `To:` diga otra cosa (así funciona Bcc).

**Conectarse a mano**
~~~bash
nc -C mail.protos.foo 25          # -C: cada Enter manda CR+LF (SMTP lo exige)
telnet mail.protos.foo 25         # alternativa (ya manda CRLF)
openssl s_client -starttls smtp -crlf -connect host:587   # con STARTTLS
openssl s_client -crlf -connect host:465                   # SMTPS
openssl s_client -crlf -connect host:995                   # POP3S
~~~
Esperá el saludo (`220` / `+OK`) antes de escribir. Escribí **un comando y esperá la respuesta**.

---

## 2. SMTP: comandos

| Comando | Qué hace | Respuesta OK |
|---|---|---|
| `EHLO tu-nombre` (o `HELO`) | saludo; **obligatorio antes de MAIL FROM**. `EHLO` lista extensiones | `250` |
| `MAIL FROM:<remitente@dom>` | remitente del sobre (a dónde vuelven los rebotes). **Con `< >`** | `250` |
| `RCPT TO:<destino@dom>` | destinatario del sobre. **Uno por línea; repetir para cada uno** (To + Cc + Bcc) | `250` / `251` |
| `DATA` | empieza la carta | `354` |
| *(headers, línea vacía, cuerpo)* | la carta | — |
| `.` solo en una línea | termina la carta | `250 … queued` ← **este es el que confirma** |
| `QUIT` | cierra | `221` |
| `RSET` | descarta el mensaje en curso (vuelve a después del EHLO) | `250` |
| `NOOP` | no hace nada (mantener viva) | `250` |
| `VRFY usuario` | ¿existe el usuario? (casi siempre deshabilitado) | `250` / `252` |
| `AUTH PLAIN <base64>` | login en un solo paso | `235` |
| `AUTH LOGIN` | login en dos pasos (usuario y clave en base64) | `334` … `235` |
| `STARTTLS` | pasa a TLS (después hay que repetir `EHLO`) | `220` |

### AUTH
~~~bash
# PLAIN = base64( \0usuario\0clave )
printf '\0usuario\0clave' | base64          # → AUTH PLAIN AHVzdWFyaW8AY2xhdmU=
# LOGIN = cada cosa por separado
echo -n 'usuario' | base64                  # → dXN1YXJpbw==
echo -n 'clave'   | base64
~~~
~~~text
AUTH LOGIN
334 VXNlcm5hbWU6        (= "Username:")
dXN1YXJpbw==
334 UGFzc3dvcmQ6        (= "Password:")
Y2xhdmU=
235 Authentication successful
~~~
Base64 **no cifra**: sin TLS la clave viaja legible.

### Códigos de respuesta SMTP
| Código | Significa | Qué hacer |
|---|---|---|
| `220` | servidor listo (saludo) / listo para TLS | empezar |
| `221` | cerrando | — |
| `235` | autenticado | seguir con MAIL FROM |
| `250` | OK | siguiente comando |
| `251` | usuario no local, lo reenvía | — |
| `252` | no puede verificar (VRFY) pero acepta | — |
| `334` | esperando dato de AUTH (base64) | mandar usuario/clave en base64 |
| `354` | escribí la carta, terminá con `.` | headers + línea vacía + cuerpo + `.` |
| `421` | servicio no disponible, cierra | reintentar |
| `450` / `451` / `452` | error temporal (buzón ocupado, greylisting, sin espacio) | reintentar más tarde |
| `500` | comando no reconocido | ¿falta `-C`? ¿mal escrito? |
| `501` | error de sintaxis en los argumentos | **faltan `< >`** en la dirección, espacio de más |
| `502` | comando no implementado | otro comando |
| `503` | **orden equivocado** | ¿falta `EHLO`? ¿`DATA` sin `RCPT`? ¿`MAIL FROM` sin `AUTH`? |
| `504` | parámetro no implementado | otro mecanismo de AUTH |
| `530` | **autenticación requerida** | `AUTH` (puerto 587) |
| `535` | credenciales incorrectas | revisar base64 (`\0`), usuario/clave |
| `550` | buzón no existe / rechazado | dirección mal escrita |
| `551` | usuario no local | — |
| `552` | mensaje demasiado grande | — |
| `553` | dirección inválida | revisar formato |
| `554` | **transacción fallida / relay denied** | ese servidor no recibe para ese dominio: usar el MX correcto, o submission+AUTH |

Regla: **2xx OK · 3xx seguí mandando · 4xx temporal · 5xx permanente (corregí vos)**.

---

## 3. Headers del mensaje

### Obligatorios / buenas prácticas
| Header | Ejemplo | Nota |
|---|---|---|
| `From:` | `From: Juana Pérez <jperez@itba.edu.ar>` | **obligatorio**. Nombre con tildes → encoded-word (sección 5) |
| `Date:` | `Date: Sat, 07 Nov 2026 13:00:00 -0300` | **obligatorio** (RFC 5322). `date -R` lo genera |
| `To:` | `To: <63051@mail.protos.foo>` | destinatarios visibles |
| `Subject:` | `Subject: Hola` | con tildes → encoded-word |
| `Message-ID:` | `Message-ID: <20261107130000.63051@itba.edu.ar>` | identificador único, con `< >` y `@` |
| `MIME-Version:` | `MIME-Version: 1.0` | **siempre que haya Content-Type** |
| `Content-Type:` | `text/plain; charset=UTF-8` | tipo y charset del cuerpo |
| `Content-Transfer-Encoding:` | `base64` / `quoted-printable` / `8bit` / `7bit` | cómo viaja el cuerpo |

### Otros que te pueden pedir
| Header | Para qué | Ejemplo |
|---|---|---|
| `Cc:` | copia visible | `Cc: <ayudante@dom>` (+ su `RCPT TO`) |
| `Bcc:` | copia oculta | **no se escribe** en DATA: solo `RCPT TO` |
| `Reply-To:` | a dónde va la respuesta | `Reply-To: <otra@dom>` |
| `Sender:` | quién lo envió en nombre del From | — |
| `In-Reply-To:` | respuesta a un mensaje | `In-Reply-To: <id-original@dom>` |
| `References:` | hilo completo | `References: <id-original@dom>` |
| `X-Algo:` (propio) | lo que pida el enunciado | `X-Parcial: 2026/2C` (**copiar exacto**) |
| `X-Priority:` / `Importance:` | prioridad | `X-Priority: 1` · `Importance: high` |
| `Disposition-Notification-To:` | pedir acuse de lectura | `Disposition-Notification-To: <yo@dom>` |
| `Return-Path:` | lo pone el servidor (= MAIL FROM) | no escribirlo |
| `Received:` | lo agrega cada servidor | no escribirlo |
| `Content-Language:` | idioma del contenido | `Content-Language: es` |
| `Keywords:` / `Comments:` | metadatos | — |

Headers: `Nombre: valor`, uno por línea. Una línea que **empieza con espacio o tab** continúa el header anterior (folding). **La primera línea vacía separa headers del cuerpo**: no puede haber líneas vacías entre headers.

---

## 4. Codificar el cuerpo (Content-Transfer-Encoding)

| CTE | Cuándo | Cómo se ve |
|---|---|---|
| `7bit` | solo ASCII | texto tal cual |
| `8bit` | UTF-8 crudo (el server tiene que anunciar `8BITMIME`) | `¡Hola!` tal cual — **no** sirve para "MUAs viejos" |
| `quoted-printable` | texto casi ASCII con algunos acentos | `=C2=A1Hola mundo!` |
| `base64` | binarios, o "debe leerse en MUAs que **no** soporten quoted-printable" | `wqFIb2xhIG11bmRvIQ==` |

**Charset**: si hay algo no ASCII, `Content-Type: text/plain; charset=UTF-8` **siempre**, codifiques como codifiques.

~~~bash
echo -n '¡Hola mundo!' | base64                  # wqFIb2xhIG11bmRvIQ==   (-n: sin salto final)
echo -n '<b>¡Hola mundo!</b>' | base64           # PGI+wqFIb2xhIG11bmRvITwvYj4=
base64 -w 76 archivo.png                         # adjuntos: líneas de 76
python3 -c "import quopri,sys;print(quopri.encodestring(sys.argv[1].encode()).decode())" '¡Hola mundo!'
# → =C2=A1Hola mundo!
echo 'wqFIb2xhIG11bmRvIQ==' | base64 -d          # verificar
~~~

**Quoted-printable a mano:** cada byte no ASCII → `=XX` (hex del byte UTF-8). `=` literal → `=3D`. Línea > 76 → cortar con `=` al final (soft break). Espacio al final de línea → `=20`.

**Errores típicos:**
- base64 **de algo que ya estaba en QP** (o al revés) → doble codificación (`=3D`, `=C2=A1` visibles en el mail).
- `echo` sin `-n` → el salto de línea queda codificado.
- Declarar `base64` y escribir el texto en claro (o al revés).
- Codificar los **headers** con el CTE: el CTE es solo para el cuerpo; los headers van con encoded-words.

---

## 5. Headers con tildes (encoded-word, RFC 2047)

~~~text
=?UTF-8?B?<base64>?=        (B = base64)
=?UTF-8?Q?<quoted-printable>?=    (Q = QP, el espacio se escribe _)
~~~
~~~bash
echo -n '¡Buenos días!' | base64          # wqFCdWVub3MgZMOtYXMh
# Subject: =?UTF-8?B?wqFCdWVub3MgZMOtYXMh?=
echo -n 'Juana Pérez' | base64            # SnVhbmEgUMOpcmV6
# From: =?UTF-8?B?SnVhbmEgUMOpcmV6?= <jperez@itba.edu.ar>
# o en Q:  From: =?UTF-8?Q?Juana_P=C3=A9rez?= <jperez@itba.edu.ar>
python3 -c "from email.header import Header;print(Header('¡Buenos días!','utf-8').encode())"
~~~
- Solo se codifica el **nombre**, nunca la dirección `<…>`.
- Una encoded-word no puede tener más de 75 caracteres: si es larga, partirla en varias separadas por espacio.
- Sin codificar, un header con bytes no ASCII rompe RFC 5322 (algunos servers lo aceptan igual con SMTPUTF8, pero no es lo correcto).

---

## 6. Formato: negrita, subrayado, colores… (HTML)

Para cualquier formato el cuerpo tiene que ser **HTML**: `Content-Type: text/html; charset=UTF-8`. Si piden que **también** lo lean MUAs sin HTML → `multipart/alternative` (sección 7).

| Te piden… | HTML |
|---|---|
| **negrita** | `<b>texto</b>` o `<strong>texto</strong>` |
| *cursiva* | `<i>texto</i>` o `<em>texto</em>` |
| subrayado | `<u>texto</u>` |
| tachado | `<s>texto</s>` o `<del>texto</del>` |
| negrita + subrayado + cursiva | `<b><u><i>texto</i></u></b>` |
| color de texto | `<span style="color:red">texto</span>` (o `#ff0000`) |
| color de fondo / resaltado | `<span style="background-color:yellow">texto</span>` o `<mark>texto</mark>` |
| tamaño | `<span style="font-size:24px">texto</span>` |
| fuente | `<span style="font-family:Courier New, monospace">texto</span>` |
| título | `<h1>Título</h1>` … `<h6>` |
| centrado | `<p style="text-align:center">texto</p>` (o `<div align="center">`) |
| link | `<a href="https://www.itba.edu.ar">ITBA</a>` |
| link de mail | `<a href="mailto:x@dom">escribime</a>` |
| salto de línea | `<br>` (en HTML un Enter **no** hace salto) |
| párrafo | `<p>texto</p>` |
| lista con viñetas | `<ul><li>uno</li><li>dos</li></ul>` |
| lista numerada | `<ol><li>uno</li><li>dos</li></ol>` |
| tabla | `<table border="1"><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></tr></table>` |
| línea horizontal | `<hr>` |
| superíndice / subíndice | `<sup>2</sup>` / `<sub>2</sub>` |
| código / monoespaciado | `<code>texto</code>` / `<pre>bloque</pre>` |
| cita | `<blockquote>texto</blockquote>` |
| imagen dentro del cuerpo | `<img src="cid:logo1">` + parte con `Content-ID: <logo1>` (sección 7.3) |
| imagen remota | `<img src="https://…/x.png">` (muchos MUAs la bloquean) |
| caracteres especiales | `&lt;` `&gt;` `&amp;` `&nbsp;` (o escribir UTF-8 con charset) |

Cuerpo HTML mínimo (no hace falta `<html>`, pero es prolijo):
~~~html
<html><body><p><b>¡Hola mundo!</b></p></body></html>
~~~
**Sin quoted-printable** → codificar el HTML en base64. Ojo: en QP el `=` de `style="…"` se escribe `=3D`.

**Texto plano no tiene formato.** Convenciones si piden "algo" en text/plain: `*negrita*`, `_subrayado_`, `/cursiva/` (algunos MUAs lo muestran), pero **no es formato real**.

---

## 7. Multipart (varias partes)

Estructura común:
~~~text
Content-Type: multipart/<subtipo>; boundary="SEP"      ← en los headers del mensaje

--SEP                                                    ← abre cada parte
Content-Type: …                                          ← headers de la parte
Content-Transfer-Encoding: …
                                                         ← línea vacía
contenido de la parte
--SEP--                                                  ← cierre final (dos guiones al final)
~~~
- El `boundary` es cualquier texto que **no aparezca** en el contenido. Entre comillas en el header.
- Cada separador es `--` + boundary. El último lleva `--` también al final.
- Cada parte tiene **sus propios** headers + línea vacía + contenido.
- `MIME-Version: 1.0` va una sola vez, en los headers del mensaje.

| Subtipo | Para qué | Orden de las partes |
|---|---|---|
| `multipart/alternative` | **la misma** información en varios formatos; el MUA muestra **la mejor que soporte** | de la más simple a la más rica: **text/plain primero, text/html último** |
| `multipart/mixed` | cuerpo + **adjuntos** | primero el cuerpo, después los adjuntos |
| `multipart/related` | HTML + **recursos incrustados** (imágenes con `cid:`) | primero el HTML, después las imágenes |

### 7.1 Negrita con versión de texto plano (alternative)
~~~text
From: Juana =?UTF-8?Q?P=C3=A9rez?= <jperez@itba.edu.ar>
To: <63051@mail.protos.foo>
Subject: =?UTF-8?B?wqFCdWVub3MgZMOtYXMh?=
Date: Sat, 07 Nov 2026 13:00:00 -0300
Message-ID: <20261107.63051@itba.edu.ar>
X-Parcial: 2026/1R
MIME-Version: 1.0
Content-Type: multipart/alternative; boundary="SEP"

--SEP
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: base64

wqFIb2xhIG11bmRvIQ==
--SEP
Content-Type: text/html; charset=UTF-8
Content-Transfer-Encoding: base64

PGI+wqFIb2xhIG11bmRvITwvYj4=
--SEP--
.
~~~
Para subrayado/cursiva/color: cambiar solo la parte HTML (`<u>…</u>`, etc.) y recodificarla.

### 7.2 Adjuntar un archivo (mixed)
~~~text
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="MIX"

--MIX
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 7bit

Adjunto el logo.
--MIX
Content-Type: image/png; name="logo.png"
Content-Disposition: attachment; filename="logo.png"
Content-Transfer-Encoding: base64

<salida de: base64 -w 76 logo.png>
--MIX--
.
~~~
Tipos: `image/png`, `image/jpeg`, `application/pdf`, `text/plain`, `application/zip`, `application/octet-stream` (genérico). Saber el tipo: `file --mime-type archivo`.

### 7.3 Imagen dentro del cuerpo (related)
~~~text
MIME-Version: 1.0
Content-Type: multipart/related; boundary="REL"

--REL
Content-Type: text/html; charset=UTF-8
Content-Transfer-Encoding: 7bit

<p>Este es el logo:</p><img src="cid:logo1">
--REL
Content-Type: image/png
Content-ID: <logo1>
Content-Disposition: inline; filename="logo.png"
Content-Transfer-Encoding: base64

<salida de: base64 -w 76 logo.png>
--REL--
.
~~~
`cid:logo1` en el HTML (sin `< >`) ↔ `Content-ID: <logo1>` en la parte (con `< >`).

### 7.4 Todo junto (texto + HTML con imagen + adjunto)
~~~text
multipart/mixed
├── multipart/alternative
│   ├── text/plain
│   └── multipart/related
│       ├── text/html   (con <img src="cid:logo1">)
│       └── image/png   (Content-ID: <logo1>)
└── application/pdf     (Content-Disposition: attachment)
~~~
Cada nivel tiene su **propio boundary** (distinto). Una parte multipart lleva solo `Content-Type: multipart/…; boundary="…"` + línea vacía + sus partes.

---

## 8. Dot-stuffing y fin del mensaje
- El mensaje termina con una línea que tiene **solo un punto**.
- Si una línea del cuerpo **empieza con `.`**, al escribirla a mano se pone **`..`** (el servidor saca uno).
- Con el cuerpo en base64 no pasa (base64 no tiene puntos). Con texto plano o QP, sí.
- `curl` y los MUAs hacen el dot-stuffing solos; con `nc` lo hacés vos.

---

## 9. El enunciado dice → qué hacer

| El enunciado dice… | Hacés |
|---|---|
| "header `X-Parcial: …`" | copiarlo **exacto** (mayúsculas, espacios, valor) |
| "subject con tildes / signos" (`¡Buenos días!`) | `Subject: =?UTF-8?B?…?=` |
| "remitente con nombre, apellido y cuenta" | `From: Nombre =?UTF-8?…?= <cuenta@itba.edu.ar>` (nombre codificado si tiene tildes) |
| "cumpliendo los estándares / buenas prácticas" | `From`, `Date`, `Message-ID`, `MIME-Version`, charset, encoded-words, EHLO, QUIT |
| "entregado a `X@dom`" | `RCPT TO:<X@dom>` (y `To:` coherente) |
| "legible por MUAs que **no** soporten quoted-printable" | cuerpo en **base64** + `charset=UTF-8` |
| "sin usar base64" | `quoted-printable` (o `8bit` si el server anuncia `8BITMIME`) |
| "el cuerpo en negrita / subrayado / cursiva / color" | `text/html` con la etiqueta |
| "…y que se pueda leer en MUAs sin HTML / conservar texto plano" | `multipart/alternative` (plain primero, html después) |
| "adjunte el archivo / la imagen" | `multipart/mixed` + `Content-Disposition: attachment` |
| "la imagen dentro del cuerpo / embebida / inline" | `multipart/related` + `cid:` |
| "con copia a Y" | `Cc: <Y>` + `RCPT TO:<Y>` |
| "con copia oculta a Z" | **solo** `RCPT TO:<Z>` (no escribir `Bcc:`) |
| "a varios destinatarios" | un `RCPT TO` por cada uno; `To:` con todos separados por coma |
| "que las respuestas vayan a W" | `Reply-To: <W>` |
| "responda en el mismo hilo" | `Subject: Re: …` + `In-Reply-To:` y `References:` con el `Message-ID` original |
| "con prioridad alta" | `X-Priority: 1` + `Importance: high` |
| "con acuse de lectura" | `Disposition-Notification-To: <vos>` |
| "a un dominio sin registro A" / "descubra el servidor" | `dig D MX` → menor prioridad → conectar a ese |
| "mande afuera / a otro dominio" | puerto **587** con `AUTH` (el 25 da `554 Relay denied`) |
| "verifique por POP3" | `curl --user U pop3://host/` y `/N` |
| "lea el mensaje y responda con la clave" | POP3 `RETR` → decodificar → SMTP con el CTE correcto |
| "borre el mensaje" | POP3 `DELE N` + **`QUIT`** |
| "sin descargar el cuerpo" | POP3 `TOP N 0` |
| "un texto que empieza con punto" | dot-stuffing (`..`) o base64 |

---

## 10. Plantilla completa (texto con tildes, sin QP)
~~~text
$ nc -C mail.protos.foo 25
220 …
EHLO itba.edu.ar
250 …
MAIL FROM:<jperez@itba.edu.ar>
250 …
RCPT TO:<63051@mail.protos.foo>
250 …
DATA
354 …
X-Parcial: 2026/2C
From: Juana =?UTF-8?Q?P=C3=A9rez?= <jperez@itba.edu.ar>
To: <63051@mail.protos.foo>
Subject: =?UTF-8?B?wqFCdWVub3MgZMOtYXMh?=
Date: Sat, 07 Nov 2026 13:00:00 -0300
Message-ID: <20261107130000.63051@itba.edu.ar>
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: base64

wqFIb2xhIG11bmRvIQ==
.
250 … queued
QUIT
221 …
~~~
Fecha actual en formato correcto: `date -R`. Escribí el mensaje en un archivo antes y pegalo, así no te equivocás en vivo.

### Mandar con curl (alternativa a nc)
~~~bash
curl smtp://mail.protos.foo:25 \
  --mail-from 'jperez@itba.edu.ar' \
  --mail-rcpt '63051@mail.protos.foo' \
  --upload-file mensaje.eml
# submission con auth y STARTTLS:
curl smtp://host:587 --ssl-reqd --user 'usuario:clave' \
  --mail-from 'yo@dom' --mail-rcpt 'otro@externo' -T mensaje.eml
# varios destinatarios: repetir --mail-rcpt
~~~
`mensaje.eml` = headers + línea vacía + cuerpo (sin el `.` final). curl hace el dot-stuffing y el `QUIT`.

---

## 11. POP3

| Comando | Qué hace | Respuesta |
|---|---|---|
| `USER usuario` | usuario | `+OK` |
| `PASS clave` | contraseña | `+OK` (logueado) / `-ERR` |
| `STAT` | cantidad y tamaño total | `+OK 3 1820` |
| `LIST` | número y tamaño de cada mensaje | `+OK` … `1 955` … `.` |
| `LIST N` | tamaño de uno | `+OK N 955` |
| `UIDL` | id único de cada mensaje (no cambia entre sesiones) | `1 abc123` … |
| `RETR N` | mensaje completo (headers + cuerpo) | `+OK` … `.` |
| `TOP N L` | headers + primeras L líneas del cuerpo (`TOP N 0` = solo headers) | `+OK` … `.` |
| `DELE N` | **marca** para borrar | `+OK` |
| `RSET` | desmarca todo | `+OK` |
| `NOOP` | nada | `+OK` |
| `CAPA` | capacidades | lista |
| `QUIT` | cierra y **aplica los borrados** | `+OK` |

- `+OK` = bien, `-ERR` = error (usuario/clave mal, mensaje inexistente, ya marcado).
- Respuestas de varias líneas terminan con un `.` solo.
- **DELE no borra hasta QUIT.** Si cortás con Ctrl+C, no se borra. Después del QUIT los números se **renumeran**.
- Un mensaje marcado con DELE ya no aparece en LIST ni se puede RETR en esa sesión.

### POP3 con curl
~~~bash
curl --user 'usuario:clave' pop3://host:110/          # LIST
curl --user 'usuario:clave' pop3://host:110/1         # RETR 1
curl --user 'usuario' pop3://host/1                   # pide la clave
curl --user 'u:c' pop3://host/ -X 'TOP 1 0'           # solo headers del 1
curl --user 'u:c' pop3://host/ -X 'UIDL'
curl --user 'u:c' pop3://host/1 -X 'DELE 1' -I        # borrar (curl manda QUIT al final)
curl --user 'u:c' pop3s://host:995/1                  # con TLS
curl -v …                                             # ver el diálogo (> y <)
~~~

### Leer lo que bajaste
~~~bash
curl -s --user u:c pop3://host/1 > msg.eml
python3 - <<'PY'
import email; from email import policy
m = email.message_from_file(open('msg.eml'), policy=policy.default)
print(m['From'], '|', m['Subject'])           # decodifica encoded-words
for p in m.walk():
    print(p.get_content_type(), p.get_filename())
    if p.get_content_maintype() == 'text': print(p.get_content())
PY
# extraer un adjunto a mano: copiar el bloque base64 y
base64 -d > logo.png
~~~

---

## 12. Problemas típicos

| Pasa | Causa | Arreglo |
|---|---|---|
| el server no responde a los comandos / `500` raro | falta `-C` (manda solo LF) | `nc -C` o `telnet` |
| `503 … send HELO/EHLO first` | arrancaste con MAIL FROM | `EHLO` primero |
| `501 Syntax` en MAIL/RCPT | faltan `< >` o hay espacio después de `:` | `MAIL FROM:<x@y>` |
| `554 Relay access denied` | destinatario de un dominio ajeno a ese server | MX del dominio, o 587 + AUTH |
| `530 Authentication required` | submission sin AUTH | `AUTH PLAIN`/`LOGIN` |
| `535` | base64 de la credencial mal (`echo` sin `-n`, falta `\0`) | `printf '\0u\0c' \| base64` |
| el mensaje no termina | no pusiste `.` solo en una línea (o tiene espacios) | `.` + Enter |
| desapareció una línea que empezaba con punto | no hiciste dot-stuffing | `..` |
| llega `Â¡Hola` / `Ã©` | falta `charset=UTF-8` (o se declaró otro) | declarar charset |
| llega `=C2=A1` o base64 visible | CTE mal declarado / doble codificación | un solo CTE, coherente |
| headers en el cuerpo | línea vacía antes de tiempo | sin líneas vacías entre headers |
| cuerpo pegado a los headers / headers raros | falta la línea vacía | una línea vacía antes del cuerpo |
| el MUA muestra el HTML como texto | `text/plain` en vez de `text/html` | Content-Type correcto |
| muestra solo texto plano en un alternative | el HTML va **primero** | plain primero, html último |
| el adjunto no aparece | falta el `--SEP--` final, boundary mal escrito, o falta `Content-Disposition` | revisar separadores |
| la imagen inline no se ve | `cid:` no coincide con `Content-ID`, o no es `related` | `cid:x` ↔ `Content-ID: <x>` |
| Bcc visible para todos | escribiste `Bcc:` en DATA | solo `RCPT TO` |
| el mensaje sigue en el buzón | DELE sin QUIT | `QUIT` |
| `-ERR` en PASS | usuario/clave (a veces el usuario es la dirección completa) | probar `usuario` y `usuario@dom` |

---

## 13. Qué decir en el video
«Me conecto con `nc -C` porque SMTP exige CRLF, saludo con EHLO y separo el sobre (MAIL FROM / RCPT TO, que deciden la entrega) de la carta (DATA). Pongo los headers obligatorios (From, Date) y los de buenas prácticas (Message-ID, MIME-Version, charset); los headers con tildes van como encoded-word y el cuerpo con el Content-Transfer-Encoding que pide el enunciado. Para formato uso HTML, y si tiene que verse también en texto plano, multipart/alternative con el plano primero. El 250 después del punto confirma la aceptación, y verifico por POP3 con LIST y RETR.»
