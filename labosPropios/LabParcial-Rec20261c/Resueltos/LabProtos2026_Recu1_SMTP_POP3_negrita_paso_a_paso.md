# LabProtos2026 · Recuperatorio 1 · Correo en negrita por SMTP

## Qué pide el ejercicio

Enviar a `63051@mail.protos.foo` un correo con el asunto **¡Buenos días!**, el cuerpo **¡Hola mundo!** en negrita y el encabezado `X-Parcial: 2026/1R`. Se conserva el remitente del Ejercicio 5 y el requisito de que el mensaje pueda leerse sin soporte de quoted-printable. Se elige el servidor SMTP consultando los MX del dominio y se comprueba la entrega por POP3.

## 1. Elegir el servidor SMTP con DNS

Consulta y salida real en la workstation

```text
root@workstation:/# dig MX mail.protos.foo +noall +answer
mail.protos.foo.    3600    IN    MX    5 mx2.protos.foo.
mail.protos.foo.    3600    IN    MX    10 mx1.protos.foo.
```

`MX` pide los servidores que reciben correo para el dominio. `+noall +answer` deja solo las respuestas. El número después de `MX` es la preferencia. El menor valor tiene prioridad, así que **usamos `mx2.protos.foo` con preferencia `5`**. `3600` es el TTL en segundos. La pista del enunciado muestra `mx1` como ejemplo, mientras que la respuesta DNS del lab da preferencia a `mx2`.

## 2. Preparar la fecha y la parte HTML

Para que el texto se vea en negrita, usamos `<b>¡Hola mundo!</b>`. Guardamos también una versión en texto plano con el mismo contenido para los clientes que elijan esa versión. Las dos se codifican en Base64.

```bash
date -R
echo -n '<b>¡Hola mundo!</b>' | base64
```

Valores observados

```text
Mon, 09 Nov 2026 22:54:04 +0000
PGI+wqFIb2xhIG11bmRvITwvYj4=
```

`echo -n` evita agregar un salto de línea antes de codificar. El Base64 incluye el fragmento completo, con las etiquetas `<b>` y `</b>`. Reutilizamos los valores del Ejercicio 5 para el nombre visible, el asunto y el texto plano, porque esos textos son los mismos.

## 3. Enviar por SMTP

Sesión real desde la workstation

```text
root@workstation:/# nc -C mx2.protos.foo 25
220 mail.protos.foo ESMTP LabProtos ready
EHLO cliente.lab
250-mail.protos.foo saluda a cliente.lab
250-PIPELINING
250 8BITMIME
MAIL FROM:<jdileomuntaner@itba.edu.ar>
250 OK
RCPT TO:<63051@mail.protos.foo>
250 OK
DATA
354 Start mail input; end with <CRLF>.<CRLF>
Date: Mon, 09 Nov 2026 22:54:04 +0000
Message-ID: <63051.20261109.225404.recu1@cliente.lab>
From: =?UTF-8?B?SmVyw7NuaW1vIERpIExlbyBNdW50YW5lcg==?= <jdileomuntaner@itba.edu.ar>
To: <63051@mail.protos.foo>
Subject: =?UTF-8?B?wqFCdWVub3MgZMOtYXMh?=
X-Parcial: 2026/1R
MIME-Version: 1.0
Content-Type: multipart/alternative; boundary="limiteRecu1"

--limiteRecu1
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: base64

wqFIb2xhIG11bmRvIQ==
--limiteRecu1
Content-Type: text/html; charset=UTF-8
Content-Transfer-Encoding: base64

PGI+wqFIb2xhIG11bmRvITwvYj4=
--limiteRecu1--
.
250 OK message queued
QUIT
221 mail.protos.foo Service closing transmission channel
```

### Del saludo al comienzo de DATA

- `nc -C mx2.protos.foo 25` se conecta al MX elegido y envía líneas terminadas en CRLF. `mail.protos.foo` es el nombre que el servicio anuncia en el saludo.
- `EHLO cliente.lab` presenta el nombre del cliente. El servidor anuncia sus extensiones en la respuesta de varias líneas.
- `MAIL FROM` y `RCPT TO` establecen las direcciones del sobre. `RCPT TO` indica el buzón de entrega. `From` y `To` dentro de `DATA` son los encabezados visibles del mensaje.
- `DATA` inicia el envío de encabezados y cuerpo cuando el servidor responde `354`. Después del terminador, `250 OK message queued` confirma que SMTP aceptó el mensaje. `QUIT` cierra el diálogo con `221`.

### Cómo está armado el mensaje

`Date` lleva la fecha generada en la workstation. El `Message-ID` combina el legajo, la fecha y hora, la etiqueta `recu1` y el nombre del cliente para identificar este envío. `From` y `Subject` usan `=?UTF-8?B?…?=` para preservar el nombre **Jerónimo Di Leo Muntaner** y el asunto **¡Buenos días!**. La `B` indica Base64 dentro de un encabezado. `X-Parcial: 2026/1R` identifica el recuperatorio y `MIME-Version: 1.0` declara el uso de MIME.

| Elemento | Qué significa |
|---|---|
| `Content-Type: multipart/alternative; boundary="limiteRecu1"` | El cuerpo contiene versiones alternativas del mismo mensaje. `limiteRecu1` es el nombre del separador que elegimos. |
| Primera línea vacía | Termina los encabezados generales y da paso al cuerpo multipart. |
| `--limiteRecu1` | Abre una parte. Se escribe el nombre del boundary precedido por dos guiones. |
| `Content-Type: text/plain; charset=UTF-8` | Identifica la primera versión como texto plano en UTF-8. |
| `Content-Type: text/html; charset=UTF-8` | Identifica la segunda versión como HTML en UTF-8. Ahí se interpreta la etiqueta `<b>`. |
| `Content-Transfer-Encoding: base64` | Cada parte declara cómo recuperar los bytes de su propio cuerpo. Después de decodificarlos, el `charset` indica cómo interpretarlos. |
| Línea vacía dentro de cada parte | Separa los encabezados de esa parte de sus datos Base64. |
| `--limiteRecu1--` | Cierra el multipart. Los dos guiones finales marcan que ya no hay otra parte. |
| `.` en una línea propia | Termina el diálogo `DATA` de SMTP después de que cerramos el multipart. |

Ponemos **texto plano primero y HTML después**. El cliente elige una de las alternativas que puede mostrar. En HTML, `<b>` le da la negrita al texto.

## 4. Verificar la entrega por POP3

Sesión real en el servidor POP3 indicado por la consigna

```text
root@workstation:/# nc -C mail.protos.foo 110
+OK LabProtos POP3 server ready
USER 63051@mail.protos.foo
+OK usuario aceptado
PASS 63051@mail.protos.foo
+OK logueado
LIST
+OK 1 messages
1 607
.
RETR 1
+OK 607 octets
Date: Mon, 09 Nov 2026 22:54:04 +0000
Message-ID: <63051.20261109.225404.recu1@cliente.lab>
From: =?UTF-8?B?SmVyw7NuaW1vIERpIExlbyBNdW50YW5lcg==?= <jdileomuntaner@itba.edu.ar>
To: <63051@mail.protos.foo>
Subject: =?UTF-8?B?wqFCdWVub3MgZMOtYXMh?=
X-Parcial: 2026/1R
MIME-Version: 1.0
Content-Type: multipart/alternative; boundary="limiteRecu1"

--limiteRecu1
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: base64

wqFIb2xhIG11bmRvIQ==
--limiteRecu1
Content-Type: text/html; charset=UTF-8
Content-Transfer-Encoding: base64

PGI+wqFIb2xhIG11bmRvITwvYj4=
--limiteRecu1--

.
```

`USER` identifica el buzón y en este lab `PASS` usa la misma dirección. `LIST` mostró un solo mensaje, de 607 octetos, por eso usamos `RETR 1`. El `Message-ID` coincide con el del envío. El punto final de la salida lo manda POP3 para delimitar la respuesta.

## 5. Comprobar qué contienen las dos partes

A partir del Base64 que devolvió `RETR`, se puede repetir la verificación desde la shell:

```bash
echo 'wqFIb2xhIG11bmRvIQ==' | base64 -d
echo
echo 'PGI+wqFIb2xhIG11bmRvITwvYj4=' | base64 -d
echo
```

La decodificación de los valores recuperados da:

```text
¡Hola mundo!
<b>¡Hola mundo!</b>
```

POP3 recuperó el mensaje crudo y ambas alternativas conservan el texto. La segunda contiene las etiquetas que hacen que **¡Hola mundo!** se vea en negrita al mostrarla como HTML.
