# Simulacro 2026-2C · Ejercicio 3 · SMTP, IMAP y variante POP3

Práctica del 9 de noviembre de 2026. Postfix aceptó el correo de prueba con el identificador `A6313381E51`. Por IMAP se recuperó el mensaje precargado con `FLAG{ej3-imap-fetch-ok}`.

## 1. Qué pide la consigna

1. Identificar y corregir los errores del diálogo SMTP que muestra el enunciado.
2. Conectarse por IMAP a la casilla del legajo, listar los buzones y leer el mensaje con la flag.

Los tres protocolos usan el mismo contenedor. Cambia el puerto y cambia el conjunto de comandos.

| Protocolo | Función | IP y puerto directos | Puerto publicado en tu máquina |
|---|---|---|---|
| SMTP | Enviar correo | `172.30.0.30:25` | `127.0.0.1:2525` |
| IMAP | Consultar el correo y sus buzones en el servidor | `172.30.0.30:143` | `127.0.0.1:1143` |
| POP3 | Listar y recuperar mensajes del buzón | `172.30.0.30:110` | `127.0.0.1:1110` |

En este simulacro el usuario y la contraseña de IMAP y POP3 son el legajo configurado en `.env`. Usamos `63051` en ambos campos. La dirección de correo es `63051@pdc.lab`.

## 2. Diagnosticar la sesión del compañero

El enunciado muestra este intento:

```text
nc 172.30.0.30 143
HELLO localhost
MAIL FROM:<friend@pdc.lab>
MAIL TO: <you>
DATA
Subject: Hola
Como estas?
QUIT
```

| Qué pasó | Cómo se corrige |
|---|---|
| Abrió el puerto 143, que en este lab habla IMAP. | Para enviar por SMTP, conectarse al puerto 25. |
| Usó `HELLO`. | Saludar con `EHLO localhost`. `HELO` también existe, aunque no devuelve la lista de extensiones de ESMTP. |
| Usó `MAIL TO` con un destinatario incompleto. | Indicar el destinatario real del sobre con `RCPT TO:<63051@pdc.lab>`. |
| Pasó de `Subject:` al texto sin una línea vacía. | Separar encabezados y cuerpo con una línea vacía. Incluir también `Date:` y `From:` para formar el mensaje. |
| Escribió `QUIT` sin terminar DATA. | Enviar una línea que contenga solo un punto, esperar el `250` final y luego cerrar con `QUIT`. |

En la variante de netcat que usamos, `-C` convierte el salto de línea de la entrada en `CRLF`. Usamos esa opción al escribir los comandos por terminal. Si un cliente ya envía `CRLF`, ese requisito se cumple de otra forma.

El intento que muestra la consigna no pudo entregar un correo por SMTP. El simulacro crea un mensaje precargado para que la lectura de la flag pueda practicarse por separado.

## 3. Enviar la versión corregida

```bash
nc -C 172.30.0.30 25
```

`nc` abre una conexión TCP. La IP selecciona el contenedor y `25` selecciona SMTP. Esta es la sesión real:

```text
220 pdc.lab ESMTP ready
EHLO localhost
250-pdc.lab
250-PIPELINING
250-SIZE 10240000
250-VRFY
250-ETRN
250-STARTTLS
250-ENHANCEDSTATUSCODES
250-8BITMIME
250-DSN
250-SMTPUTF8
250 CHUNKING
MAIL FROM:<friend@pdc.lab>
250 2.1.0 Ok
RCPT TO:<63051@pdc.lab>
250 2.1.5 Ok
DATA
354 End data with <CR><LF>.<CR><LF>
Date: Mon, 09 Nov 2026 09:47:29 -0300
From: friend@pdc.lab
To: 63051@pdc.lab
Subject: Hola

Como estas?
.
250 2.0.0 Ok: queued as A6313381E51
QUIT
221 2.0.0 Bye
```

| Línea | Para qué sirvió |
|---|---|
| `220 pdc.lab ESMTP ready` | Confirmó que el servicio SMTP estaba listo. |
| `EHLO localhost` | Identificó al cliente y permitió ver las extensiones. Las líneas `250-` continúan la respuesta y `250 CHUNKING` la termina. |
| `MAIL FROM:<friend@pdc.lab>` | Declaró el remitente del sobre SMTP. |
| `RCPT TO:<63051@pdc.lab>` | Declaró la dirección a la que el servidor debía entregar el correo. |
| `DATA` | Solicitó enviar el mensaje. El `354` indicó que el servidor esperaba encabezados y cuerpo. |
| `Date:`, `From:`, `To:`, `Subject:` | Formaron los encabezados del mensaje. `To:` es el destinatario visible y `RCPT TO` determina la entrega. |
| Línea vacía | Separó los encabezados del cuerpo `Como estas?`. |
| `.` | Cerró DATA. El servidor devolvió `250` y asignó el identificador de cola `A6313381E51`. |
| `QUIT` | Cerró la sesión SMTP. El servidor contestó `221`. |

Para repetir el envío, se puede obtener una fecha nueva con `date -R` en otra terminal. El `250` final confirma la aceptación del correo por Postfix. Verlo dentro del buzón es una comprobación posterior.

## 4. Conectarse por IMAP

```bash
nc -C 172.30.0.30 143
```

Se reutiliza la IP del contenedor y se cambia al puerto IMAP. El servidor respondió con un saludo `* OK ... Dovecot (Debian) ready.`

En IMAP, cada comando comienza con una **etiqueta elegida por el cliente**. Usamos `a1`, `a2`, etc. La respuesta con la misma etiqueta marca el final de ese comando. Las líneas que empiezan con `*` traen datos del servidor, como el nombre de un buzón o el contenido recuperado.

### a1 LOGIN 63051 63051

```text
a1 LOGIN 63051 63051
a1 OK [CAPABILITY ...] Logged in
```

`LOGIN` recibe el usuario y la contraseña en ese orden. `a1 OK` confirma que la autenticación funcionó. `CAPABILITY` enumera las funciones que anuncia Dovecot.

### a2 LIST "" "*"

```text
a2 LIST "" "*"
* LIST (\HasNoChildren) "." INBOX
a2 OK List completed (0.024 + 0.000 + 0.023 secs).
```

`LIST` lista **buzones o carpetas**. El primer argumento, `""`, indica una referencia vacía y el segundo, `"*"`, coincide con todos los nombres de buzón. En la respuesta, `INBOX` es el nombre, `"." ` indica el separador jerárquico y `\HasNoChildren` indica que no tiene subcarpetas.

En POP3, un `LIST` enumera mensajes del buzón con sus tamaños. Esa diferencia explica por qué en IMAP hicimos un paso adicional para abrir `INBOX`.

### a3 EXAMINE INBOX

```text
a3 EXAMINE INBOX
* FLAGS (\Answered \Flagged \Deleted \Seen \Draft)
* OK [PERMANENTFLAGS ()] Read-only mailbox.
* 2 EXISTS
* 2 RECENT
* OK [UNSEEN 1] First unseen.
* OK [UIDVALIDITY 1794228589] UIDs valid
* OK [UIDNEXT 3] Predicted next UID
a3 OK [READ-ONLY] Examine completed (0.009 + 0.000 + 0.008 secs).
```

`EXAMINE INBOX` abre la bandeja de entrada **en modo de solo lectura**. `SELECT INBOX` es el comando habitual cuando también se quieren hacer cambios en el buzón.

| Respuesta | Qué indica |
|---|---|
| `FLAGS (...)` | Marcas de mensajes que informa el buzón. `\Seen` representa que el mensaje fue visto. |
| `PERMANENTFLAGS ()` y `READ-ONLY` | La sesión abrió el buzón sin permisos para cambiar sus marcas. |
| `2 EXISTS` | Hay dos mensajes en el buzón seleccionado. |
| `2 RECENT` | Dovecot informó dos mensajes con la marca de recientes. |
| `UNSEEN 1` | El mensaje con número de secuencia 1 es el primero sin la marca de visto. |
| `UIDVALIDITY 1794228589` | Valor que permite saber si los UIDs guardados de ese buzón siguen siendo válidos. |
| `UIDNEXT 3` | UID que el servidor prevé asignar al próximo mensaje. |

El `1` que usamos después en `FETCH` es un **número de secuencia** dentro de la bandeja abierta. Se puede pedir un UID explícitamente mediante `UID FETCH`.

### a4 FETCH 1 BODY.PEEK[]

```text
a4 FETCH 1 BODY.PEEK[]
* 1 FETCH (BODY[] {218}
From: friend@pdc.lab
To: 63051@pdc.lab
Subject: Hola
Date: Mon, 09 Nov 2026 11:35:33 +0000

Como estas? Este mensaje ya estaba en tu casilla.
Si ves esto por IMAP, la parte (b) esta OK.
FLAG{ej3-imap-fetch-ok}
)
a4 OK Fetch completed (0.012 + 0.000 + 0.011 secs).
```

`FETCH` pide datos de un mensaje. `1` elige el primer mensaje. Los corchetes vacíos de `BODY.PEEK[]` indican el mensaje completo, con encabezados y cuerpo. `PEEK` pide que la lectura no marque el mensaje como visto. Dovecot devuelve el contenido bajo `BODY[]`. `{218}` anuncia la longitud en bytes del bloque de mensaje que viene a continuación.

El cuerpo identifica este correo como el **precargado**. Ahí estaba la flag. El envío de prueba tenía otra fecha, `09:47:29 -0300`, y un cuerpo que decía solo `Como estas?`. Se observó que había dos mensajes, pero el único mensaje recuperado en la sesión fue el primero. Si se quiere comprobar el correo de prueba por separado, se puede abrir de nuevo INBOX y pedir `FETCH 2 BODY.PEEK[]` si sigue habiendo dos mensajes.

### a5 LOGOUT

```text
a5 LOGOUT
* BYE Logging out
a5 OK Logout completed (0.001 + 0.000 secs).
```

`LOGOUT` cierra la sesión. `* BYE` anuncia la desconexión y `a5 OK` completa el comando.

## 5. Cómo leerlo con POP3

El mismo laboratorio ofrece POP3 y permite consultar el correo por ese protocolo. Esta variante es para practicar. La consigna pide entregar la lectura hecha por IMAP.

Desde la terminal:

```bash
nc -C 172.30.0.30 110
```

El puerto publicado equivalente desde tu máquina es `127.0.0.1:1110`. Esperá el saludo `+OK`, luego enviá una línea por vez:

```text
USER 63051
PASS 63051
LIST
RETR 1
QUIT
```

| Comando | Qué hace |
|---|---|
| `USER 63051` | Indica la cuenta que vas a usar. |
| `PASS 63051` | Envía la contraseña del legajo y completa la autenticación. |
| `LIST` | Muestra los números y tamaños en bytes de los mensajes del buzón. Su respuesta termina con un punto solo. |
| `RETR 1` | Recupera el mensaje 1 completo. El punto en una línea propia cierra la respuesta de POP3. |
| `QUIT` | Cierra la sesión. Como no usamos `DELE`, no se solicitó borrar ningún mensaje. |

En POP3 no hacen falta etiquetas como `a1` ni elegir `INBOX`. Usá los números que devuelve su propio `LIST`. Si el primero es el correo que enviaste recién, probá `RETR 2` antes de `QUIT` para buscar el precargado. Esta secuencia POP3 quedó como alternativa explicada. La flag registrada en esta práctica salió del `FETCH` por IMAP.

