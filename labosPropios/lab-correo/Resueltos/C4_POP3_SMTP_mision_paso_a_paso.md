# C4 — Misión por POP3: lectura, respuesta y borrado

Práctica del 8 de noviembre de 2026. **Resultado real: 10/10 verificaciones, aprobado.**

## 1. Consigna

En el buzón hay un correo de `secretaria@mision.lab`, asunto `Misión: Imposible`. Hay que:

1. Leerlo por POP3 y obtener una clave con caracteres no ASCII.
2. Responder a esa dirección, con asunto de respuesta (Re:) y cuerpo que contenga exactamente la clave.
3. Borrar el mensaje original del servidor.

## 2. Datos utilizados

| Dato | Valor |
|---|---|
| SMTP | 127.0.0.1:2525 |
| POP3 | 127.0.0.1:2110 |
| Buzón del agente | 63051@mail.protos.lab |
| Usuario y contraseña POP3 | Ambos 63051@mail.protos.lab en este laboratorio |
| Remitente de la respuesta | Jeronimo Muntaner <jdileomuntaner@itba.edu.ar> |
| Destino de la respuesta | secretaria@mision.lab |
| Message-ID original | <seed-mision@mision.lab> |
| Clave exacta | «Ñandú-42¿» |
| Message-ID de respuesta | <63051.20261108.132146.c4@mail.protos.lab> |
| Cola SMTP de respuesta | 4FB928CF2D |

La clave incluye los signos « y ». Son parte del contenido, no comillas que deban quitarse.

## 3. Abrir POP3 y autenticar

En bash:

```bash
nc -C 127.0.0.1 2110
```

- nc abre una conexión TCP.
- -C usa CRLF en la variante de netcat de esta práctica.
- 127.0.0.1 es la máquina local donde corre el lab.
- 2110 es el puerto POP3 del laboratorio; el estándar sin TLS implícito es 110.

Diálogo real:

```text
+OK POP3 LabProtos ready
USER 63051@mail.protos.lab
+OK
PASS 63051@mail.protos.lab
+OK Logged in. 4 messages
LIST
+OK 4 messages:
1 915
2 629
3 563
4 770
.
```

USER identifica el buzón y PASS autentica. La contraseña igual al usuario es una configuración del lab.

LIST muestra número de mensaje y tamaño en octetos, no asuntos. El punto final termina la respuesta multilínea. +OK significa éxito; -ERR indicaría un error.

Necesitábamos identificar el correo de la misión antes de descargarlo o borrarlo.

## 4. Inspeccionar los encabezados

Comando ejecutado dentro de POP3:

```text
TOP 1 0
```

TOP recibe el número de mensaje y la cantidad de líneas del cuerpo. TOP 1 0 devuelve los encabezados del mensaje 1 y cero líneas del cuerpo.

Respuesta real:

```text
+OK
Return-Path: <semilla@protos.lab>
Received: from semilla (localhost [127.0.0.1])
	by mx1.protos.lab with ESMTP id SEED0001
	for <63051@mail.protos.lab>; Sun, 08 Nov 2026 12:21:32 -0300
From: =?UTF-8?Q?Secretar=C3=ADa_IMF?= <secretaria@mision.lab>
To: Agente 63051 <63051@mail.protos.lab>
Subject: =?UTF-8?B?TWlzacOzbjogSW1wb3NpYmxl?=
Date: Sun, 08 Nov 2026 12:21:32 -0300
Message-ID: <seed-mision@mision.lab>
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: base64

.
```

Reconocimos la misión por el remitente y el asunto. Su Message-ID permite identificarla de nuevo en otra sesión.

### Las codificaciones de los encabezados

- El nombre usa un encoded-word con Q: `=?UTF-8?Q?Secretar=C3=ADa_IMF?=`. Representa “Secretaría IMF”; el guion bajo representa un espacio en este formato.
- El asunto usa un encoded-word con B: `=?UTF-8?B?TWlzacOzbjogSW1wb3NpYmxl?=`. Representa “Misión: Imposible”.
- La codificación del nombre no determina la del cuerpo. El cuerpo declara por separado Content-Transfer-Encoding: base64.
- charset=UTF-8 indica cómo interpretar los bytes una vez decodificados.

## 5. Recuperar el cuerpo completo

```text
RETR 1
```

El servidor respondió `+OK 915 octets` y devolvió los mismos encabezados, seguidos de este cuerpo:

```text
QWdlbnRlIDYzMDUxOgoKTG9zIHBsYW5vcyB5YSBlc3TDoW4gZW4gY2FtaW5vLiBQYXJhIGNvbmZp
cm1hciBxdWUgcmVjaWJpw7MgZXN0ZSBtZW5zYWplLCByZXNwb25kYSBhIGVzdGEgbWlzbWEgZGly
ZWNjacOzbiBjb24gbGEgY2xhdmUgZGUgdmVyaWZpY2FjacOzbiBleGFjdGEsIHNpbiBhZ3JlZ2Fy
bGUgbmFkYToKCsKrw5FhbmTDui00MsK/wrsKClRlbmdhIGVuIGN1ZW50YSBxdWUgbGEgY2xhdmUg
bm8gZXMgQVNDSUkuIFVuYSB2ZXogbGXDrWRvLCBib3JyZSBlc3RlIG1lbnNhamUgZGVsIHNlcnZp
ZG9yLgo=
```

RETR recupera el mensaje sin borrarlo. POP3 no decodifica MIME: devuelve los bytes del correo. El punto final de la respuesta POP3 no forma parte del cuerpo y no se pasa a base64.

## 6. Decodificar en otra terminal

Comando realmente ejecutado en bash:

```bash
echo -n 'QWdlbnRlIDYzMDUxOgoKTG9zIHBsYW5vcyB5YSBlc3TDoW4gZW4gY2FtaW5vLiBQYXJhIGNvbmZp
cm1hciBxdWUgcmVjaWJpw7MgZXN0ZSBtZW5zYWplLCByZXNwb25kYSBhIGVzdGEgbWlzbWEgZGly
ZWNjacOzbiBjb24gbGEgY2xhdmUgZGUgdmVyaWZpY2FjacOzbiBleGFjdGEsIHNpbiBhZ3JlZ2Fy
bGUgbmFkYToKCsKrw5FhbmTDui00MsK/wrsKClRlbmdhIGVuIGN1ZW50YSBxdWUgbGEgY2xhdmUg
bm8gZXMgQVNDSUkuIFVuYSB2ZXogbGXDrWRvLCBib3JyZSBlc3RlIG1lbnNhamUgZGVsIHNlcnZp
ZG9yLgo=
' | base64 -d
```

Las comillas simples conservan el bloque literal, incluidos los saltos. -n evita que echo agregue otro salto al final; base64 -d admite los saltos de línea de la representación codificada. La tubería conecta ambos comandos.

Salida real:

```text
Agente 63051:

Los planos ya están en camino. Para confirmar que recibió este mensaje, responda a esta misma dirección con la clave de verificación exacta, sin agregarle nada:

«Ñandú-42¿»

Tenga en cuenta que la clave no es ASCII. Una vez leído, borre este mensaje del servidor.
```

La respuesta debe llevar solo la clave, sin copiar el saludo ni las instrucciones.

## 7. Preparar cuerpo, asunto y fecha

Comandos ejecutados en bash:

```bash
echo -n '«Ñandú-42¿»' | base64
echo -n 'Re: Misión: Imposible' | base64
date -R
```

Salidas reales, en el mismo orden:

```text
wqvDkWFuZMO6LTQywr/Cuw==
UmU6IE1pc2nDs246IEltcG9zaWJsZQ==
Sun, 08 Nov 2026 13:21:46 -0300
```

echo -n evita incorporar un salto a la clave exacta. Base64 transporta los bytes UTF-8 mediante caracteres ASCII; no cifra. date -R obtiene una fecha para Date con zona horaria. Para repetir el envío, usar fecha y Message-ID nuevos.

## 8. Abrir SMTP y declarar el sobre

En bash:

```bash
nc -C 127.0.0.1 2525
```

Diálogo real:

```text
220 mx1.protos.lab ESMTP LabProtos ready
EHLO cliente.lab
250-mx1.protos.lab Hello cliente.lab
250-SIZE 10240000
250-8BITMIME
250 HELP
MAIL FROM:<jdileomuntaner@itba.edu.ar>
250 2.1.0 Ok
RCPT TO:<secretaria@mision.lab>
250 2.1.5 Ok
DATA
354 End data with <CR><LF>.<CR><LF>
```

- 220: servicio listo.
- EHLO: presentación y descubrimiento de extensiones. En respuestas multilínea, 250- indica continuación y 250 con espacio es la última línea.
- MAIL FROM: remitente del sobre.
- RCPT TO: destino real; aquí es la secretaria, no el buzón del agente.
- DATA: solicita transmitir el mensaje.
- 354: autoriza a transmitirlo; todavía no confirma aceptación final.

Se esperó la respuesta positiva de cada comando antes de continuar. Los 250 y 354 son respuestas del servidor, no comandos para copiar.

## 9. Mensaje enviado y aceptación

```text
Date: Sun, 08 Nov 2026 13:21:46 -0300
Message-ID: <63051.20261108.132146.c4@mail.protos.lab>
From: Jeronimo Muntaner <jdileomuntaner@itba.edu.ar>
To: <secretaria@mision.lab>
Subject: =?UTF-8?B?UmU6IE1pc2nDs246IEltcG9zaWJsZQ==?=
In-Reply-To: <seed-mision@mision.lab>
References: <seed-mision@mision.lab>
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: base64

wqvDkWFuZMO6LTQywr/Cuw==
.
```

| Elemento | Función |
|---|---|
| Date | Fecha de creación con zona horaria. |
| Message-ID | Identificador nuevo de la respuesta. No se reutiliza el del original. |
| From / To | Autor y destinatario visibles. El sobre SMTP se declaró antes. |
| Subject | “Re: Misión: Imposible” mediante encoded-word UTF-8/base64. |
| In-Reply-To | Identifica el mensaje al que se responde. No se exigía en C4; se agregó para enlazar la respuesta. |
| References | Registra la referencia al mensaje original en el hilo. |
| MIME-Version | Declara MIME 1.0. |
| Content-Type | Texto plano en UTF-8, sin necesidad de multipart. |
| Content-Transfer-Encoding | El cuerpo está en base64. No codifica los encabezados automáticamente. |
| Línea vacía | Separa encabezados y cuerpo. |
| Punto solo | Finaliza DATA; no pertenece a la clave. |

No se añadió X-Parcial: la consigna de C4 no lo pedía.

Respuesta real:

```text
250 2.0.0 Ok: queued as 4FB928CF2D
QUIT
221 2.0.0 Bye
```

El 250 posterior al punto confirma que el servidor aceptó el mensaje. 4FB928CF2D es el identificador de cola, distinto de nuestro Message-ID. QUIT cierra la sesión SMTP.

## 10. Se cerró la conexión POP3: cómo retomamos

La conexión POP3 inicial se había cerrado antes de borrar. Se abrió una nueva y se autenticó de nuevo:

```bash
nc -C 127.0.0.1 2110
```

Diálogo real:

```text
+OK POP3 LabProtos ready
USER 63051@mail.protos.lab
+OK
PASS 63051@mail.protos.lab
+OK Logged in. 4 messages
LIST
+OK 4 messages:
1 915
2 629
3 563
4 770
.
TOP 1 0
```

TOP devolvió otra vez los encabezados originales, incluido:

```text
Message-ID: <seed-mision@mision.lab>
```

Así confirmamos que el número 1 seguía siendo la misión. **Los números pueden cambiar entre sesiones**, especialmente si se borran mensajes: no reutilizar un número sin comprobar la identidad.

El buzón propio seguía teniendo cuatro mensajes porque la respuesta se entregó al buzón de la secretaria.

## 11. Borrar y confirmar

En la nueva sesión POP3:

```text
DELE 1
+OK Marked to be deleted.
QUIT
+OK LabProtos POP3 signing off (1 messages deleted)
```

DELE marca el mensaje para borrado dentro de la sesión. QUIT desde la sesión autenticada entra en la fase de actualización y confirma las eliminaciones. En nuestra ejecución, la respuesta final confirmó un mensaje eliminado.

Cerrar la ventana o perder la conexión no sustituye a QUIT para confirmar el borrado. Si se marca por error y todavía no se cerró la sesión, RSET permite retirar las marcas de borrado; esto es una referencia de POP3 y no fue necesario ejecutarlo aquí.

## 12. Corrector y resultado real

En bash, desde la carpeta del laboratorio:

```bash
bash lab-correo.sh corregir C4
```

bash ejecuta el script, corregir elige la acción y C4 selecciona el ejercicio.

```text
== Corrección C4 (misión por POP3) ==
  [OK] Borraste el mensaje original (DELE + QUIT)
  [OK] La secretaria recibió tu respuesta
  [OK] From con tu cuenta ITBA (jdileomuntaner@itba.edu.ar)
  [OK] To: secretaria@mision.lab
  [OK] MIME-Version: 1.0
  [OK] Date válido
  [OK] Message-ID con formato <algo@dominio>
  [OK] Subject de respuesta (Re: Misión: Imposible)
  [OK] Cuerpo text/plain
  [OK] La clave llegó exacta
  [!]  Bien: pusiste In-Reply-To (no se pedía, suma).

  Resultado: 10/10 verificaciones bien.  ¡Aprobado!
```

El corrector confirmó tanto la recepción por la secretaria como la coincidencia exacta de la clave y el borrado del original.

## 13. Qué recordar

1. LIST enumera mensajes; TOP permite identificarlos por sus encabezados.
2. RETR recupera sin borrar ni decodificar MIME.
3. Leer Content-Transfer-Encoding y charset antes de interpretar el cuerpo.
4. Responder al remitente solicitado, con una transacción SMTP nueva y un Message-ID nuevo.
5. Si piden una clave exacta, conservar todos sus caracteres y no añadir texto ni saltos al contenido original.
6. En la respuesta, codificar el asunto y el cuerpo por separado.
7. Para borrar: comprobar la identidad, DELE y luego QUIT.
8. Si se abre otra sesión, verificar de nuevo los números antes de borrar.

