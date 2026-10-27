# SMTP: todas las variantes de formato y MIME

Complemento de `smtp-pop3-base64_1c2026.md` (texto simple) y `smtp-multipart-negrita_recu2026.md` (negrita). El diálogo SMTP y la verificación POP3 son **siempre iguales**; lo que cambia de un parcial a otro es **lo que va dentro de DATA**. Acá está cada caso, con mensajes completos que pasaron el parser MIME de Python sin errores.

---

## ⭐ Regla rápida (leer primero)

| El enunciado pide… | Estructura | Ver |
|---|---|---|
| Solo texto (con o sin acentos) | `text/plain` + base64 | `smtp-pop3-base64_1c2026.md` |
| **Negrita**, *cursiva*, <u>subrayado</u>, color, link, lista, título | `multipart/alternative` (texto plano + HTML) | A |
| Una **imagen adjunta** (o cualquier archivo) | `multipart/mixed` | B |
| Una **imagen dentro del cuerpo** (que se vea en el mensaje) | `multipart/related` + `cid:` | C |
| Imagen en el cuerpo **y** un adjunto | `mixed` → `related` → `alternative` | D |
| "Codifique con quoted-printable" | `Content-Transfer-Encoding: quoted-printable` | E |
| "MUAs que no soporten quoted-printable" | **base64** en cada parte de texto | todas |
| Varios destinatarios, CC, BCC, Reply-To | sobre (`RCPT TO`) + headers | F |
| Nombre del remitente con tildes | encoded-word en `From:` | G |

**Árbol mental:** `mixed` = "acá hay adjuntos"; `related` = "estas partes van juntas (HTML + sus imágenes)"; `alternative` = "es el mismo contenido en dos formatos, mostrá el mejor". De afuera hacia adentro: **mixed ⊃ related ⊃ alternative**. Solo se usa el nivel que haga falta.

### Reglas que valen en todos los casos
1. Headers de arriba (siempre): `From`, `To`, `Subject`, `Date`, `Message-ID`, `MIME-Version: 1.0`, el `X-...` que pidan y el `Content-Type` del nivel más externo.
2. **Línea en blanco** entre headers y cuerpo, en el mensaje y en **cada parte**.
3. Cada boundary: `--nombre` para abrir una parte, `--nombre--` para cerrar el contenedor. Boundaries distintos en cada nivel.
4. Base64 se aplica a las **hojas** (texto, HTML, imagen), nunca al contenedor `multipart`.
5. Los base64 se generan **antes**, en otra terminal, y se pegan:
   ~~~bash
   printf '%s' 'TEXTO' | base64 -w0; echo        # texto corto
   printf '%s\r\n' 'TEXTO' | base64 -w0; echo     # con salto de línea final
   base64 -w 76 imagen.png                         # archivo, en líneas de 76
   ~~~
6. `Date` y `Message-ID` (buena práctica que suelen pedir):
   ~~~bash
   date -R                                         # Date: Tue, 27 Oct 2026 12:00:00 -0300
   echo "<$(date +%s).$RANDOM@itba.edu.ar>"        # Message-ID
   ~~~
7. Si una línea del cuerpo empieza con `.`, se escribe `..` (dot-stuffing). En base64 no pasa nunca.

---

## A. Formato de texto: negrita, cursiva, subrayado, color, link

En texto plano no existe el formato, así que se manda **las dos versiones** en `multipart/alternative`: una `text/plain` (con la convención de marcas) y una `text/html` (con el formato real). El cliente muestra la HTML; uno viejo muestra la plana.

| Piden | HTML (parte text/html) | Texto plano (convención) |
|---|---|---|
| Negrita | `<b>¡Hola mundo!</b>` | `*¡Hola mundo!*` |
| Cursiva | `<i>¡Hola mundo!</i>` | `/¡Hola mundo!/` |
| Subrayado | `<u>¡Hola mundo!</u>` | `_¡Hola mundo!_` |
| Tachado | `<s>¡Hola mundo!</s>` | `-¡Hola mundo!-` |
| Color | `<span style="color:red">¡Hola mundo!</span>` | `¡Hola mundo!` |
| Tamaño / título | `<h1>¡Hola mundo!</h1>` | `¡Hola mundo!` |
| Link | `<a href="https://www.itba.edu.ar">ITBA</a>` | `ITBA <https://www.itba.edu.ar>` |
| Lista | `<ul><li>uno</li><li>dos</li></ul>` | `- uno` / `- dos` |
| Negrita y subrayado | `<b><u>¡Hola mundo!</u></b>` | `*_¡Hola mundo!_*` |

Base64 ya calculados (con `\r\n` final):

| Contenido | Base64 |
|---|---|
| `*¡Hola mundo!*` | `KsKhSG9sYSBtdW5kbyEqDQo=` |
| `<p><b>¡Hola mundo!</b></p>` | `PHA+PGI+wqFIb2xhIG11bmRvITwvYj48L3A+DQo=` |
| `_¡Hola mundo!_` | `X8KhSG9sYSBtdW5kbyFfDQo=` |
| `<p><u>¡Hola mundo!</u></p>` | `PHA+PHU+wqFIb2xhIG11bmRvITwvdT48L3A+DQo=` |
| `/¡Hola mundo!/` | `L8KhSG9sYSBtdW5kbyEvDQo=` |
| `<p><i>¡Hola mundo!</i></p>` | `PHA+PGk+wqFIb2xhIG11bmRvITwvaT48L3A+DQo=` |
| `¡Hola mundo!` | `wqFIb2xhIG11bmRvIQ0K` |
| Subject `¡Buenos días!` | `=?UTF-8?B?wqFCdWVub3MgZMOtYXMh?=` |

Generarlos uno mismo (para cualquier otro texto):
~~~bash
printf '%s\r\n' '<p><u>¡Hola mundo!</u></p>' | base64 -w0; echo
~~~

Estructura (cambiar solo las dos líneas de base64):
~~~text
Content-Type: multipart/alternative; boundary="alt-1"

--alt-1
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: base64

X8KhSG9sYSBtdW5kbyFfDQo=
--alt-1
Content-Type: text/html; charset=UTF-8
Content-Transfer-Encoding: base64

PHA+PHU+wqFIb2xhIG11bmRvITwvdT48L3A+DQo=
--alt-1--
~~~
**Orden:** primero la plana y último la HTML. El cliente elige la **última** que entiende, así que la "mejor" va al final.

> Si el enunciado dice "solo HTML", alcanza con un único `Content-Type: text/html; charset=UTF-8` + base64, sin `alternative`. Mandar las dos es la buena práctica.

---

## B. Imagen (o archivo) adjunta

`multipart/mixed`: la primera parte es el cuerpo, las siguientes son los adjuntos.

~~~bash
base64 -w 76 imagen.png > imagen.b64      # en otra terminal; después pegar su contenido
file imagen.png                           # para saber el tipo: image/png, image/jpeg...
~~~

Mensaje completo (validado):
~~~text
From: =?UTF-8?B?SmVyw7NuaW1vIERpIExlbyBNdW50YW5lcg==?= <jdileomuntaner@itba.edu.ar>
To: 63051@mail.protos.foo
Subject: =?UTF-8?B?wqFCdWVub3MgZMOtYXMh?=
X-Parcial: 2026/1R
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="mix-1"

--mix-1
Content-Type: multipart/alternative; boundary="alt-1"

--alt-1
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: base64

KsKhSG9sYSBtdW5kbyEqDQo=
--alt-1
Content-Type: text/html; charset=UTF-8
Content-Transfer-Encoding: base64

PHA+PGI+wqFIb2xhIG11bmRvITwvYj48L3A+DQo=
--alt-1--
--mix-1
Content-Type: image/png; name="logo.png"
Content-Transfer-Encoding: base64
Content-Disposition: attachment; filename="logo.png"

iVBORw0KGgoAAAANSUhEUgAAAAQAAAAECAIAAAAmkwkpAAAAEElEQVR4nGP4z8AARwzEcQCukw/x
0F8jngAAAABJRU5ErkJggg==
--mix-1--
~~~
- Si el cuerpo es solo texto plano, la primera parte de `mixed` es directamente un `text/plain` (sin el `alternative`).
- Otros tipos: `image/jpeg`, `application/pdf`, `text/plain` (un .txt), `application/octet-stream` (cualquier binario).
- `Content-Disposition: attachment` → se muestra como adjunto; `filename` es el nombre sugerido.

---

## C. Imagen dentro del cuerpo (inline, con `cid:`)

El HTML referencia la imagen con `src="cid:IDENTIFICADOR"` y la parte de la imagen lleva `Content-ID: <IDENTIFICADOR>`. Las dos van juntas en `multipart/related`.

HTML (antes de pasarlo a base64):
~~~html
<p><b>¡Hola mundo!</b></p>
<p><img src="cid:imagen1"></p>
~~~

Mensaje completo (validado):
~~~text
From: =?UTF-8?B?SmVyw7NuaW1vIERpIExlbyBNdW50YW5lcg==?= <jdileomuntaner@itba.edu.ar>
To: 63051@mail.protos.foo
Subject: =?UTF-8?B?wqFCdWVub3MgZMOtYXMh?=
X-Parcial: 2026/1R
MIME-Version: 1.0
Content-Type: multipart/related; boundary="rel-1"

--rel-1
Content-Type: multipart/alternative; boundary="alt-1"

--alt-1
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: base64

KsKhSG9sYSBtdW5kbyEqDQo=
--alt-1
Content-Type: text/html; charset=UTF-8
Content-Transfer-Encoding: base64

PHA+PGI+wqFIb2xhIG11bmRvITwvYj48L3A+DQo8cD48aW1nIHNyYz0iY2lkOmltYWdlbjEiPjwvcD4NCg==
--alt-1--
--rel-1
Content-Type: image/png; name="logo.png"
Content-Transfer-Encoding: base64
Content-ID: <imagen1>
Content-Disposition: inline; filename="logo.png"

iVBORw0KGgoAAAANSUhEUgAAAAQAAAAECAIAAAAmkwkpAAAAEElEQVR4nGP4z8AARwzEcQCukw/x
0F8jngAAAABJRU5ErkJggg==
--rel-1--
~~~
- `cid:imagen1` en el HTML ↔ `Content-ID: <imagen1>` en la parte (con `<>` en el header, sin `<>` en el HTML).
- Es lo mismo que se ve en `parcial-correo.pcap`: `src="cid:ii_ka5xvnoa0"` y `Content-ID: <ii_ka5xvnoa0>` (ver `pcap/pcap.md`, B2).

---

## D. Imagen en el cuerpo + archivo adjunto

Se anidan los tres niveles. Esqueleto (rellenar con los bloques de C y B):
~~~text
Content-Type: multipart/mixed; boundary="mix-1"

--mix-1
Content-Type: multipart/related; boundary="rel-1"

--rel-1
Content-Type: multipart/alternative; boundary="alt-1"

[parte text/plain]
[parte text/html con <img src="cid:imagen1">]
--alt-1--
--rel-1
[parte image/png con Content-ID: <imagen1>]
--rel-1--
--mix-1
[parte del adjunto con Content-Disposition: attachment]
--mix-1--
~~~
Cada contenedor se cierra (`--x--`) **antes** de seguir con el boundary del nivel de afuera.

---

## E. Si piden quoted-printable

Es el caso opuesto al de los parciales ("MUAs que **no** soporten quoted-printable" → base64). Si lo piden explícitamente:
~~~bash
printf '%s' '¡Hola mundo!' | python3 -c "import quopri,sys;sys.stdout.write(quopri.encodestring(sys.stdin.buffer.read()).decode())"; echo
# =C2=A1Hola mundo!
~~~
~~~text
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: quoted-printable

=C2=A1Hola mundo!
~~~
- Cada byte no ASCII se escribe `=XX` en hexadecimal (`¡` en UTF-8 son 2 bytes: `C2 A1`).
- Si piden **ISO-8859-1** (Latin-1): `printf '%s' '¡Hola!' | iconv -f UTF-8 -t ISO-8859-1 | base64` y `charset=ISO-8859-1`. En Latin-1, `¡` es un solo byte (`=A1`).
- Subject en quoted-printable: `=?UTF-8?Q?=C2=A1Buenos_d=C3=ADas!?=` (los espacios se escriben `_`).

---

## F. Destinatarios: varios, CC, BCC, Reply-To

| Piden | Sobre (diálogo SMTP) | Headers (dentro de DATA) |
|---|---|---|
| Dos destinatarios | dos líneas `RCPT TO:<a@x>` y `RCPT TO:<b@x>` | `To: a@x, b@x` |
| Con copia | `RCPT TO:` también para el de CC | `Cc: c@x` |
| Copia oculta | `RCPT TO:` para el de BCC | **ningún header** (si aparece, deja de ser oculta) |
| Responder a otra dirección | nada | `Reply-To: otra@x` |
| Remitente visible distinto del real | `MAIL FROM:<real@x>` | `From: Otro <otro@x>` |
| Rebotes a otra dirección | `MAIL FROM:<rebotes@x>` | (el servidor pone `Return-Path`) |
| Prioridad alta | nada | `X-Priority: 1` y `Importance: high` |
| Pedir confirmación de lectura | nada | `Disposition-Notification-To: yo@x` |

**Clave para el video:** el **sobre** (`MAIL FROM`, `RCPT TO`) decide a quién se entrega; los **headers** (`From`, `To`, `Cc`) son solo lo que muestra el cliente. Por eso BCC funciona: está en el sobre y no en los headers.

---

## G. Nombre con tildes en el remitente

~~~bash
printf '%s' 'Jerónimo Di Leo Muntaner' | base64 -w0; echo
# SmVyw7NuaW1vIERpIExlbyBNdW50YW5lcg==
~~~
~~~text
From: =?UTF-8?B?SmVyw7NuaW1vIERpIExlbyBNdW50YW5lcg==?= <jdileomuntaner@itba.edu.ar>
~~~
La dirección entre `<>` **no** se codifica, solo el nombre. Sin tildes alcanza con `From: Juan Perez <juan@x>`.

---

## Plan B: armar el mensaje en un archivo y mandarlo de una

Tipear un MIME largo dentro de `nc` es fácil de romper. Se puede escribir todo en un archivo con el editor y después mandarlo con pausas, para que el servidor conteste cada comando:

~~~bash
nano mail.txt          # pegar el mensaje completo (headers + cuerpo), SIN la línea final "."
{ printf 'EHLO itba.edu.ar\r\n'; sleep 1
  printf 'MAIL FROM:<jdileomuntaner@itba.edu.ar>\r\n'; sleep 1
  printf 'RCPT TO:<63051@mail.protos.foo>\r\n'; sleep 1
  printf 'DATA\r\n'; sleep 1
  sed 's/$/\r/' mail.txt; printf '.\r\n'; sleep 1
  printf 'QUIT\r\n'; } | nc mail.protos.foo 25
~~~
- `printf '...\r\n'`: manda cada comando con CRLF, como exige SMTP.
- `sleep 1`: espera la respuesta del servidor antes del próximo comando.
- `sed 's/$/\r/'`: convierte los saltos del archivo a CRLF.
- Las respuestas (`250`, `354`, `250 OK`) se ven en pantalla igual. Si alguna es `5xx`, leer el error y corregir.

Para el video conviene mostrar el diálogo a mano (es lo que evalúan). Usá esto si el MIME es muy largo, como con una imagen, y explicá qué hace cada línea.

---

## Verificar por POP3 (igual en todos los casos)
~~~bash
nc -C mail.protos.foo 110
USER 63051@mail.protos.foo
PASS 63051@mail.protos.foo
LIST
RETR <n>
QUIT
~~~
Para mostrar que la parte decodifica bien: copiar el base64 de la parte y `echo 'BASE64' | base64 -d`. Para una imagen: `base64 -d > recibida.png` y `xdg-open recibida.png`.

---

## Si algo falla

| Ves | Causa | Arreglo |
|---|---|---|
| El cliente muestra el código MIME crudo | Falta `MIME-Version: 1.0` o falta la línea en blanco después de los headers | Agregarlos |
| Se ve el texto plano y no el HTML | La parte HTML va antes que la plana | Plana primero, HTML último |
| La imagen aparece como adjunto y no dentro del mensaje | Usaste `mixed` en vez de `related`, o el `cid` no coincide | `related` + `cid:X` ↔ `Content-ID: <X>` |
| Partes "pegadas" o vacías | Boundary mal escrito o contenedor sin cerrar | Revisar `--b` / `--b--` y que cada nivel tenga el suyo |
| Imagen corrupta | Base64 incompleto o con texto extra | Regenerar con `base64 -w 76` y pegar completo |
| Tildes rotas (Ã¡) | charset no coincide con los bytes | `charset=UTF-8` si generaste con `printf` en una terminal UTF-8 |
| `554` / `550` al dar RCPT | Destinatario no aceptado por ese servidor | Revisar dominio y `dig MX` del destino |
| El mensaje se corta | Una línea que era solo `.` dentro del cuerpo | Dot-stuffing: escribir `..` |
