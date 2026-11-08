# C1 — SMTP y verificación por POP3, paso a paso

Práctica realizada el 8 de noviembre de 2026. Resultado real del corrector: **13/13 verificaciones aprobadas**.

## 1. Consigna original

Lucía, legajo 50122 y cuenta `lsosa@itba.edu.ar`, debía enviar un correo cumpliendo estándares y buenas prácticas:

1. Header `X-Parcial: 2026/2C`.
2. Subject `¡Buenos días!`.
3. Remitente con nombre, apellido y cuenta ITBA.
4. Cuerpo exactamente `¡Hola mundo!`.
5. Entrega a `50122@mail.protos.foo`.
6. Legible por clientes de correo que no soporten quoted-printable.
7. Verificación por POP3.

El diálogo que había que analizar era:

```text
$ nc mail.protos.foo 25
220 mail.protos.foo ESMTP
MAIL FROM:<lsosa@itba.edu.ar>
RCPT TO:<lsosa@itba.edu.ar>
DATA
X-Parcial: 2026/2
Subject: ¡Buenos días!
From: <lsosa@itba.edu.ar>
To: <50122@mail.protos.foo>
MIME-Version: 1.0
Content-Type: text/plain
Content-Transfer-Encoding: base64

PGI+wqFIb2xhIG11bmRvITwvYj4=
.
^C
```

Se pide identificar errores, determinar si se entregó y reescribir el diálogo correcto, enviándolo al buzón propio del laboratorio.

## 2. Errores del diálogo y sus efectos

| Problema | Regla o requisito | Efecto y corrección |
|---|---|---|
| `nc` sin `-C` en la variante OpenBSD usada | SMTP delimita líneas con CRLF (RFC 5321). | El Enter habitual produce LF; usar `nc -C` convierte los finales a CRLF. Otros programas o variantes de netcat pueden necesitar otra opción. |
| Falta `HELO`/`EHLO` | La sesión SMTP requiere presentación antes de la transacción (RFC 5321). | El lab rechaza `MAIL FROM` con `503 5.5.1 Error: send HELO/EHLO first`. Presentarse primero y comprobar la respuesta. |
| `RCPT TO` apunta a la cuenta ITBA de Lucía | La consigna pide entregar al buzón `50122@mail.protos.foo`. | `RCPT TO` determina la entrega real. `To:` es un encabezado del mensaje y no sustituye al destinatario del sobre. |
| No se muestran respuestas intermedias | Hay que respetar la secuencia y comprobar la aceptación. | Debe esperarse `250` después de los comandos del sobre y `354` antes de enviar el contenido. El transcript no permite saber qué aceptó el servidor. |
| `X-Parcial: 2026/2` | La consigna exige `2026/2C`. | Falta la `C`; corregir el valor exacto. |
| Asunto con UTF-8 directo | En el formato tradicional de encabezados se usa ASCII; los encabezados internacionalizados requieren soporte específico. | Para esta práctica usar encoded-word de RFC 2047: `=?UTF-8?B?wqFCdWVub3MgZMOtYXMh?=`. `8BITMIME` por sí solo no autoriza UTF-8 en encabezados. |
| `From:` sin nombre y apellido | Requisito de la consigna. | La dirección sola puede ser válida, pero no cumple lo pedido. Agregar el nombre. |
| Falta `Date:` | Campo obligatorio de origen según RFC 5322. | Agregar fecha con zona horaria, por ejemplo con `date -R`. |
| Falta `Message-ID:` | RFC 5322 recomienda que cada mensaje tenga uno. | Agregar un identificador único. No tiene la misma obligatoriedad que `Date:`. |
| Falta `charset=UTF-8` | El texto MIME necesita declarar cómo interpretar los bytes no ASCII. | En `text/plain`, el charset predeterminado es US-ASCII. Declarar UTF-8 para representar correctamente `¡`. |
| El cuerpo base64 contiene etiquetas HTML | La consigna pide exactamente `¡Hola mundo!`, y se declaró `text/plain`. | El base64 decodifica a `<b>¡Hola mundo!</b>`; un lector de texto plano mostraría las etiquetas. Codificar solo el texto solicitado. |
| Termina con Ctrl+C | `QUIT` permite cerrar ordenadamente SMTP. | Si el servidor ya aceptó el mensaje después del punto, cortar no revierte esa aceptación. Usar `QUIT` y esperar `221`. |
| No verifica por POP3 | Requisito explícito de la consigna. | Conectarse al buzón, autenticarse, listar y recuperar el correo. |

### ¿Se entregó el correo de Lucía?

**El diálogo original no permite afirmarlo.** No muestra respuestas a `MAIL FROM`, `RCPT TO`, `DATA` ni al punto final. El `220` inicial solo confirma que el servidor estaba listo.

En el servidor estricto del lab, sin `HELO`/`EHLO`, se rechaza la transacción y no se acepta el correo de esa secuencia. Además, un servidor puede rechazar el destinatario ITBA por relay no autorizado.

Si un servidor tolerante aceptara la transacción y respondiera positivamente al final de DATA, el destinatario del sobre sería `lsosa@itba.edu.ar`, no el buzón del header `To:`. El cuerpo decodificado sería `<b>¡Hola mundo!</b>`, tratado como texto plano.

### Advertencia sobre la solución escrita incluida en el lab

El texto de `solucion C1` en el archivo suministrado tiene dos inconsistencias: afirma que el cuerpo es quoted-printable envuelto en base64, y que hubo un `250` final en el diálogo de Lucía. El base64 publicado realmente contiene HTML, y el transcript original no incluye ese `250`. Este apunte utiliza el contenido efectivo de la consigna. En nuestra ejecución corregida sí obtuvimos un `250` final real.

## 3. Datos usados en nuestra ejecución

| Dato | Valor |
|---|---|
| SMTP del laboratorio | `127.0.0.1:2525` |
| POP3 del laboratorio | `127.0.0.1:2110` |
| Nombre configurado | `Jeronimo Muntaner` |
| Cuenta ITBA | `jdileomuntaner@itba.edu.ar` |
| Buzón destino | `63051@mail.protos.lab` |
| Contraseña POP3 del lab | Igual a la dirección completa del buzón |

El puerto estándar de recepción SMTP es 25; el de POP3 sin TLS implícito es 110. Este lab usa 2525 y 2110 para evitar puertos privilegiados y conflictos. El protocolo y sus comandos son los mismos.

Si fuera necesario iniciar el lab, desde su carpeta se usa `bash lab-correo.sh up`. No usar `reset` para iniciarlo: vacía los buzones y recrea los mensajes iniciales.

## 4. Abrir SMTP

En la terminal del usuario:

```bash
nc -C 127.0.0.1 2525
```

- `nc`: establece una conexión TCP.
- `-C`: usa finales de línea CRLF, adecuados para SMTP y POP3.
- `127.0.0.1`: la máquina donde está corriendo el lab. Si está en una VM, es esa VM.
- `2525`: puerto donde escucha SMTP en este lab.

Respuesta real:

```text
220 mx1.protos.lab ESMTP LabProtos ready
```

El `220` indica que el servicio está listo. A partir de aquí escribimos comandos SMTP dentro de netcat, no comandos de bash.

## 5. Presentarnos con EHLO

```text
EHLO cliente.lab
```

`cliente.lab` identifica al cliente que está iniciando la conversación; no es el destinatario. `EHLO` hace la presentación y permite descubrir extensiones. `HELO` es el saludo básico.

Respuesta real:

```text
250-mx1.protos.lab Hello cliente.lab
250-SIZE 10240000
250-8BITMIME
250 HELP
```

El código `250` es positivo. El guion después del código indica que siguen más líneas; un espacio indica la última línea. `SIZE` anuncia un máximo de 10.240.000 bytes y `8BITMIME` permite negociar cuerpos de ocho bits. No anuncia `SMTPUTF8`: para los encabezados con acentos usamos encoded-word. No necesitamos usar ocho bits en el cuerpo porque lo codificamos en base64.

Como el servidor aceptó la presentación, podemos declarar el remitente del sobre.

## 6. Remitente del sobre

```text
MAIL FROM:<jdileomuntaner@itba.edu.ar>
```

Respuesta real:

```text
250 2.1.0 Ok
```

`MAIL FROM` inicia la transacción y declara el remitente del sobre SMTP, usado para las notificaciones de fallo. Los signos `<...>` delimitan la dirección; el lab los exige. No es el encabezado `From:` que mostrará el lector.

El `250` permite continuar con los destinatarios.

## 7. Destinatario real

```text
RCPT TO:<63051@mail.protos.lab>
```

Respuesta real:

```text
250 2.1.5 Ok
```

`RCPT TO` indica dónde debe entregarse una copia. Para varios destinatarios se repite este comando. El dominio es `.lab` en nuestro entorno, aunque el ejercicio en papel use `.foo`.

Como el servidor aceptó el destinatario, podemos solicitar la transmisión del mensaje.

## 8. Iniciar DATA

```text
DATA
```

Respuesta real:

```text
354 End data with <CR><LF>.<CR><LF>
```

El código `354` es una respuesta intermedia: autoriza a enviar el mensaje. Todavía no confirma que el correo fue aceptado. Desde ahora se escriben encabezados y cuerpo. Una línea que solo contiene `.` termina DATA.

## 9. Preparar fecha y base64 en otra terminal

Dejamos abierta la conexión que está esperando DATA y usamos otra terminal para los comandos de bash.

### Fecha

```bash
date -R
```

Salida real:

```text
Sun, 08 Nov 2026 12:43:29 -0300
```

`-R` genera una fecha adecuada para el encabezado del correo. `-0300` indica tres horas menos que UTC. En futuras ejecuciones obtener una fecha nueva.

### Asunto

Comando ejecutado:

```bash
printf '%s' '¡Buenos días!' | base64
```

Alternativa equivalente para este texto, elegida para continuar:

```bash
echo -n '¡Buenos días!' | base64
```

Salida:

```text
wqFCdWVub3MgZMOtYXMh
```

`echo -n` no agrega un salto de línea al texto. `printf '%s'` también imprime el texto sin agregarlo. Las comillas simples conservan el texto literal. `|` conecta la salida del primer comando con la entrada de `base64`. Base64 representa bytes mediante caracteres ASCII; no cifra.

El resultado va dentro de un encoded-word:

```text
Subject: =?UTF-8?B?wqFCdWVub3MgZMOtYXMh?=
```

`UTF-8` indica el juego de caracteres, `B` indica base64 y `?=` cierra el bloque. No basta con poner el base64 suelto en el asunto: hace falta indicar al lector cómo interpretarlo.

### Cuerpo

```bash
echo -n '¡Hola mundo!' | base64
```

La primera ejecución se hizo con `printf '%s'`, con el mismo resultado:

```text
wqFIb2xhIG11bmRvIQ==
```

El cuerpo necesita transportar la `¡`, que no es ASCII. Base64 permite hacerlo sin quoted-printable, cumpliendo la consigna.

### Nombre

También se ejecutó:

```bash
echo -n 'Jeronimo Muntaner' | base64
```

Salida real:

```text
SmVyb25pbW8gTXVudGFuZXI=
```

No fue necesario usarla: `Jeronimo Muntaner` está escrito sin tilde y contiene solo ASCII. Por eso se dejó el nombre directamente en `From:`. Si se escribe un nombre con tildes, en este formato de correo se puede usar un encoded-word para el nombre, conservando la dirección fuera del bloque codificado.

## 10. Escribir el mensaje y terminar DATA

En la terminal de netcat que había respondido `354`, se envió:

```text
Date: Sun, 08 Nov 2026 12:43:29 -0300
Message-ID: <63051.20261108.124329.c1@mail.protos.lab>
From: Jeronimo Muntaner <jdileomuntaner@itba.edu.ar>
To: <63051@mail.protos.lab>
X-Parcial: 2026/2C
Subject: =?UTF-8?B?wqFCdWVub3MgZMOtYXMh?=
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: base64

wqFIb2xhIG11bmRvIQ==
.
```

| Campo o elemento | Función |
|---|---|
| `Date` | Fecha de creación del mensaje. Puede diferir de la fecha de recepción. |
| `Message-ID` | Identificador único del mensaje; usar otro para cada mensaje nuevo. El dominio aquí es parte del identificador, no una instrucción de entrega. |
| `From` | Autor visible: nombre y cuenta ITBA solicitados. |
| `To` | Destinatario visible. La entrega ya se declaró con `RCPT TO`. |
| `X-Parcial` | Encabezado personalizado con el valor exacto exigido. |
| `Subject` | Asunto codificado para representar sus caracteres no ASCII. |
| `MIME-Version: 1.0` | Declara el uso de MIME. |
| `Content-Type: text/plain` | El contenido es texto plano, no HTML. |
| `charset=UTF-8` | Una vez decodificado el cuerpo, sus bytes representan texto UTF-8. |
| `Content-Transfer-Encoding: base64` | El cuerpo está representado en base64. No codifica automáticamente los encabezados. |
| Línea vacía | Separa los encabezados del cuerpo. Es indispensable. |
| Punto solo | Termina la transmisión de DATA; no pertenece al cuerpo entregado. |

Respuesta real al punto final:

```text
250 2.0.0 Ok: queued as B5F0C9BFAA
```

**Este es el momento en que el servidor acepta el mensaje.** `B5F0C9BFAA` es el identificador de cola asignado por el servidor. Es distinto de nuestro `Message-ID` y luego permite reconocer el paso por ese servidor en `Received:`.

## 11. Cerrar SMTP

```text
QUIT
```

Se indicó cerrar la sesión con este comando. La respuesta exacta no se pegó en el chat; la esperada es una respuesta `221` y el cierre de conexión. El correo ya estaba aceptado: `QUIT` no es el comando que lo envía.

## 12. Conectarse por POP3

En bash:

```bash
nc -C 127.0.0.1 2110
```

Respuesta real:

```text
+OK POP3 LabProtos ready
```

La IP es la misma, pero el puerto corresponde a POP3. SMTP se usó para enviar; POP3 permite recuperar los mensajes del buzón. En POP3, `+OK` indica éxito y `-ERR` indica un error.

## 13. Autenticarse

```text
USER 63051@mail.protos.lab
```

El usuario confirmó una respuesta positiva, sin copiar el texto completo. `USER` identifica el buzón; aún falta la contraseña.

```text
PASS 63051@mail.protos.lab
```

Respuesta real:

```text
+OK Logged in. 3 messages
```

En este laboratorio la contraseña es igual a la dirección del buzón. No es una regla de POP3. La respuesta confirma la autenticación y que hay tres mensajes.

## 14. Listar mensajes sin descargar sus cuerpos

```text
LIST
```

Salida pegada por el usuario:

```text
+OK 3 messages:
1 915
2 629
3 563
```

Cada fila muestra número de mensaje y tamaño en octetos. No es el asunto ni un identificador permanente. Una respuesta multilínea POP3 termina con un punto solo; el usuario no lo incluyó en este fragmento de LIST.

Como acabábamos de enviar un mensaje, probamos con el número 3, probablemente el último. No se puede identificar un correo con certeza solo por el tamaño o la posición: se confirman sus encabezados al leerlo.

## 15. Recuperar el mensaje 3

```text
RETR 3
```

`RETR` recupera el mensaje completo correspondiente a ese número. Leerlo no lo borra.

Respuesta real:

```text
+OK 563 octets
Return-Path: <jdileomuntaner@itba.edu.ar>
Received: from cliente.lab (localhost [127.0.0.1])
	by mx1.protos.lab with ESMTP id B5F0C9BFAA
	for <63051@mail.protos.lab>; Sun, 08 Nov 2026 12:52:27 -0300
Date: Sun, 08 Nov 2026 12:43:29 -0300
Message-ID: <63051.20261108.124329.c1@mail.protos.lab>
From: Jeronimo Muntaner <jdileomuntaner@itba.edu.ar>
To: <63051@mail.protos.lab>
X-Parcial: 2026/2C
Subject: =?UTF-8?B?wqFCdWVub3MgZMOtYXMh?=
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: base64

wqFIb2xhIG11bmRvIQ==
.
```

Reconocemos nuestro correo por `Message-ID`, `X-Parcial`, las direcciones y el identificador de cola `B5F0C9BFAA` en `Received`.

El servidor agregó `Return-Path`, derivado del remitente del sobre, y `Received`, que registra este paso del mensaje y la hora de recepción. Las líneas indentadas continúan el mismo encabezado `Received`.

El cuerpo sigue en base64 porque POP3 recupera el mensaje sin interpretar MIME. Un cliente de correo usaría los encabezados para mostrar el asunto y cuerpo ya decodificados. El punto final marca el fin de la respuesta POP3, no es contenido del correo.

La respuesta anuncia 563 octetos aunque aparecen encabezados agregados: es el valor informado por este lab; no se hizo un recuento independiente del mensaje recuperado.

## 16. Cerrar POP3 y decodificar el cuerpo

Dentro de POP3 se indicó:

```text
QUIT
```

No se copió su respuesta exacta en el chat. Se volvió a la terminal normal. No se usó `DELE`, por lo que no se solicitó borrar ningún mensaje.

En bash se ejecutó:

```bash
echo 'wqFIb2xhIG11bmRvIQ==' | base64 -d
```

Resultado real:

```text
¡Hola mundo!
```

`-d` significa decodificar. Al generar base64 usamos `echo -n` para no incorporar un salto al texto; al decodificar, el salto que agrega `echo` se tolera como espacio en blanco de la representación base64.

En la terminal, el prompt apareció pegado a `¡Hola mundo!`: el texto original no terminaba con un salto de línea, justamente porque se codificó sin agregarlo. Para una presentación más cómoda, se puede ejecutar `echo` después, pero no fue necesario modificar el mensaje.

También se puede comprobar el asunto en bash:

```bash
echo 'wqFCdWVub3MgZMOtYXMh' | base64 -d
```

Resultado esperado: `¡Buenos días!`. Esta comprobación adicional no se ejecutó en la conversación; el asunto sí fue validado por el corrector.

## 17. Ejecutar el corrector

Desde la carpeta del lab:

```bash
bash lab-correo.sh corregir C1
```

`bash` ejecuta el script, `corregir` selecciona la acción y `C1` identifica el ejercicio. Es una herramienta del laboratorio, no un comando SMTP ni POP3.

Salida real:

```text
== Corrección C1 ==
  corrigiendo: <63051.20261108.124329.c1@mail.protos.lab>  ·  Subject: '¡Buenos días!'
  [OK] X-Parcial: 2026/2C
  [OK] Subject = ¡Buenos días!
  [OK] Subject codificado en ASCII (encoded-word)
  [OK] From con tu cuenta ITBA (jdileomuntaner@itba.edu.ar)
  [OK] From con nombre y apellido (Jeronimo Muntaner)
  [OK] From en ASCII (si hay tildes, encoded-word)
  [OK] To: 63051@mail.protos.lab
  [OK] MIME-Version: 1.0
  [OK] Date válido
  [OK] Message-ID con formato <algo@dominio>
  [OK] Ninguna parte en quoted-printable
  [OK] Hay una parte text/plain
  [OK] Texto = ¡Hola mundo!

  Resultado: 13/13 verificaciones bien.  ¡Aprobado!
```

## 18. Qué recordar para repetirlo

1. Abrir SMTP y esperar `220`.
2. Presentarse con `EHLO` y comprobar la respuesta `250` completa.
3. Declarar `MAIL FROM` y cada `RCPT TO`, comprobando sus respuestas.
4. Mandar `DATA` y esperar `354`.
5. Escribir encabezados, una línea vacía y el cuerpo con la codificación declarada.
6. Terminar con un punto solo y esperar el `250` final.
7. Cerrar con `QUIT`.
8. Abrir POP3, usar `USER` y `PASS`, luego `LIST` y `RETR`.
9. Confirmar que es el correo correcto, decodificar el contenido y cerrar con `QUIT`.
10. Ejecutar el corrector del lab.

Ante un error, leer su respuesta antes de continuar: un `354` autoriza a enviar datos; el `250` posterior al punto confirma su aceptación; recuperar el mensaje por POP3 confirma que está en el buzón.
