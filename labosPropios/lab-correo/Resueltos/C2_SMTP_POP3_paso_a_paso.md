# C2 — Texto simple sin quoted-printable: paso a paso

## Estado de este apunte

Se decidió pasar directamente al C3 porque C2 reproduce el envío de texto plano ya practicado en C1, cambiando el encabezado X-Parcial. **C2 no se ejecutó en esta conversación.** Este documento es una guía reproducible: las respuestas indicadas son esperadas y no resultados medidos de C2. No se atribuye una aprobación del corrector.

## 1. Consigna

Enviar un correo bien formado, entregado al buzón propio, con:

1. `X-Parcial: 2024/2`.
2. Asunto `¡Buenos días!`.
3. Remitente con nombre, apellido y cuenta ITBA.
4. Cuerpo exactamente `¡Hola mundo!`.
5. Legible por clientes de correo (MUA) sin soporte de quoted-printable.

Verificar por POP3 que llegó.

## 2. Datos del laboratorio

| Dato | Valor |
|---|---|
| SMTP | `127.0.0.1:2525` |
| POP3 | `127.0.0.1:2110` |
| Remitente | `Jeronimo Muntaner <jdileomuntaner@itba.edu.ar>` |
| Buzón destino | `63051@mail.protos.lab` |
| Usuario y contraseña POP3 | Ambos son `63051@mail.protos.lab` en este lab |

Ejecutar los comandos desde la carpeta del laboratorio. Si ya está funcionando, no hace falta reiniciarlo. `reset` borra los buzones; no usarlo para continuar esta práctica.

## 3. Elegir formato y codificación

El cuerpo solo necesita texto plano: `Content-Type: text/plain; charset=UTF-8`.
Como contiene `¡`, representamos sus bytes UTF-8 en base64. Así no usamos quoted-printable.

El asunto también tiene caracteres no ASCII. Se codifica con un encoded-word, por separado del cuerpo:

```text
Subject: =?UTF-8?B?wqFCdWVub3MgZMOtYXMh?=
```

`UTF-8` declara el juego de caracteres; `B` indica base64; `?=` cierra el bloque. Declarar base64 para el cuerpo no codifica automáticamente el asunto.

## 4. Preparar los datos en bash

```bash
date -R
echo -n '¡Buenos días!' | base64
echo -n '¡Hola mundo!' | base64
```

- `date -R`: produce una fecha apta para el encabezado Date, incluyendo la zona horaria. Usar la salida actual al enviar.
- `echo -n`: imprime el texto sin agregar un salto de línea.
- Las comillas simples conservan el texto literal.
- `|`: conecta la salida de echo con la entrada de base64.
- `base64`: representa bytes con caracteres ASCII; no cifra.

Resultados esperados de las codificaciones:

```text
wqFCdWVub3MgZMOtYXMh
wqFIb2xhIG11bmRvIQ==
```

También se puede usar `printf '%s' '¡Hola mundo!' | base64`.

## 5. Abrir SMTP y presentarse

En bash:

```bash
nc -C 127.0.0.1 2525
```

`nc` abre una conexión TCP; `-C` usa CRLF en la variante de netcat de esta práctica; la IP es local y 2525 es el puerto SMTP del lab. El puerto estándar de recepción SMTP es 25.

Esperar un saludo `220`. Dentro de netcat:

```text
EHLO cliente.lab
```

Respuesta esperada en este lab:

```text
250-mx1.protos.lab Hello cliente.lab
250-SIZE 10240000
250-8BITMIME
250 HELP
```

EHLO presenta al cliente y descubre extensiones. El guion tras 250 indica que siguen más líneas; el espacio indica la última. Esperar toda la respuesta antes de continuar. Aunque anuncie 8BITMIME, eso no autoriza por sí solo UTF-8 en encabezados; usamos encoded-word.

## 6. Declarar el sobre SMTP

Enviar uno por uno:

```text
MAIL FROM:<jdileomuntaner@itba.edu.ar>
```

Esperar `250 2.1.0 Ok`. Luego:

```text
RCPT TO:<63051@mail.protos.lab>
```

Esperar `250 2.1.5 Ok`. Luego:

```text
DATA
```

Esperar `354 End data with <CR><LF>.<CR><LF>`.

MAIL FROM declara el remitente del sobre. RCPT TO determina el destinatario real de la entrega. Los encabezados From y To son parte del mensaje visible y no sustituyen a esos comandos.

El 354 autoriza a transmitir el mensaje; todavía no lo acepta definitivamente.

## 7. Escribir el mensaje

El siguiente bloque usa una **fecha e identificador de ejemplo**, no una ejecución real de C2. Para repetir el ejercicio, reemplazar Date por la salida actual de `date -R` y usar un Message-ID nuevo.

Pegar en la conexión que respondió 354, conservando la línea vacía:

```text
Date: Sun, 08 Nov 2026 13:12:31 -0300
Message-ID: <63051.20261108.131231.c2@mail.protos.lab>
From: Jeronimo Muntaner <jdileomuntaner@itba.edu.ar>
To: <63051@mail.protos.lab>
X-Parcial: 2024/2
Subject: =?UTF-8?B?wqFCdWVub3MgZMOtYXMh?=
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: base64

wqFIb2xhIG11bmRvIQ==
.
```

| Campo | Para qué sirve |
|---|---|
| Date | Fecha de creación del mensaje con zona horaria. |
| Message-ID | Identifica el mensaje; debe ser único para cada envío nuevo. |
| From | Autor visible con nombre y cuenta ITBA. El nombre usado es ASCII, sin tilde. |
| To | Destinatario visible. |
| X-Parcial | Marca exacta de este ejercicio. |
| Subject | Asunto con encoded-word para los caracteres no ASCII. |
| MIME-Version | Declara MIME 1.0. |
| Content-Type | Texto plano cuyos bytes decodificados se interpretan como UTF-8. |
| Content-Transfer-Encoding | Indica cómo decodificar el cuerpo: base64. |
| Línea vacía | Separa encabezados y cuerpo. |
| Punto solo | Termina DATA; no pertenece al mensaje entregado. |

Esperar un `250` final de aceptación, normalmente con `queued as` y un identificador de cola. No hay un identificador real registrado para C2.

Luego enviar:

```text
QUIT
```

Esperar el cierre con 221. El correo se acepta al responder al punto final, no al ejecutar QUIT.

## 8. Verificar la entrega por POP3

En bash:

```bash
nc -C 127.0.0.1 2110
```

Esperar `+OK` y enviar cada comando esperando su respuesta:

```text
USER 63051@mail.protos.lab
PASS 63051@mail.protos.lab
LIST
```

USER identifica el buzón; PASS autentica. Que la contraseña sea igual al usuario es una configuración del lab, no una regla de POP3.

LIST devuelve números de mensaje y tamaños en octetos. La respuesta multilínea termina con un punto. El número depende del estado actual del buzón: no asumir que C2 sea el 4 ni atribuirle el número usado en C3.

Para recuperar el candidato, sustituir N por su número:

```text
RETR N
```

Confirmar:

- `X-Parcial: 2024/2`.
- El Message-ID utilizado para C2.
- Direcciones correctas y cuerpo base64 `wqFIb2xhIG11bmRvIQ==`.

RETR lee sin borrar. POP3 devuelve el contenido MIME sin decodificarlo. El servidor puede agregar Return-Path y Received. El identificador de cola en Received permite relacionarlo con la aceptación SMTP.

Cerrar con:

```text
QUIT
```

## 9. Decodificar y corregir

En bash:

```bash
echo 'wqFIb2xhIG11bmRvIQ==' | base64 -d
echo
```

Resultado esperado:

```text
¡Hola mundo!
```

`-d` decodifica. El segundo echo agrega un salto visual para separar el prompt; no modifica el correo.

Desde la carpeta del laboratorio:

```bash
bash lab-correo.sh corregir C2
```

`bash` ejecuta el script, `corregir` elige la acción y `C2` el ejercicio. Comprobar todos los ítems que informe. **No se ejecutó este corrector para C2 en la sesión registrada.**

## 10. Errores frecuentes

- Cambiar To pero dejar otro RCPT TO: la entrega sigue el sobre.
- Copiar `X-Parcial: 2026/2C` de C1: C2 exige `2024/2`.
- Poner base64 suelto en Subject: falta la envoltura encoded-word.
- Omitir charset: base64 no declara cómo interpretar los bytes decodificados.
- Omitir la línea vacía: se pierde la separación entre encabezados y cuerpo.
- Mandar texto antes del 354 o continuar después de una respuesta de error.
- Confundir aceptación SMTP con verificación de llegada al buzón: comprobar también por POP3.

