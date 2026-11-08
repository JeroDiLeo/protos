# C9 — Envío SMTP autenticado con AUTH PLAIN

Práctica del 8 de noviembre de 2026. **Resultado real: 13/13 verificaciones, aprobado.**

## 1. Consigna

Enviar un correo a `profe@externo.lab`, con `X-Parcial: LAB-C9` y asunto `Entrega TP`. El servidor de recepción del lab rechaza relay a dominios ajenos; para este ejercicio se usa submission con autenticación.

| Dato | Valor |
|---|---|
| Submission del lab | 127.0.0.1:2587 |
| Usuario AUTH | 63051 |
| Contraseña AUTH del lab | protos2026 |
| Cuenta remitente | jdileomuntaner@itba.edu.ar |
| Destinatario | profe@externo.lab |
| Message-ID preparado | <63051.20261108.164224.c9@mail.protos.lab> |

## 2. Recepción SMTP y submission

El servidor de recepción acepta correo para los dominios que atiende. No tiene por qué aceptar que cualquier cliente lo use para enviar a otros dominios: eso sería relay.

El servidor de submission acepta envíos de usuarios autorizados. En este laboratorio exige AUTH antes de permitir el envío externo.

| Servicio | Puerto usual | Puerto del lab |
|---|---:|---:|
| SMTP de recepción/transferencia | 25 | 2525 |
| Submission | 587 | 2587 |

Los puertos del laboratorio están indicados por su configuración. La autenticación se hace en la sesión SMTP, antes del sobre y de DATA; no se agrega la contraseña en los encabezados del correo.

## 3. Abrir submission y descubrir AUTH

En bash:

```bash
nc -C 127.0.0.1 2587
```

nc abre una conexión TCP. -C utiliza CRLF en la variante de netcat usada. 2587 es el puerto del servidor de submission del lab.

Diálogo real:

```text
220 smtp.protos.lab ESMTP LabProtos ready
EHLO cliente.lab
250-smtp.protos.lab Hello cliente.lab
250-SIZE 10240000
250-8BITMIME
250-AUTH PLAIN LOGIN
250 HELP
```

220 indica servicio listo. EHLO presenta al cliente y descubre extensiones. 250- anuncia más líneas; 250 con espacio es la última.

AUTH PLAIN LOGIN anuncia dos mecanismos disponibles: PLAIN y LOGIN. Elegimos PLAIN.

## 4. Estructura de AUTH PLAIN

PLAIN lleva tres campos separados por bytes nulos:

```text
identidad de autorización + NUL + identidad de autenticación + NUL + contraseña
```

En esta práctica dejamos vacía la identidad de autorización, por eso los bytes son:

```text
NUL + 63051 + NUL + protos2026
```

NUL es el byte de valor cero: no es un espacio ni los caracteres visibles de la palabra NUL. Después se representa toda la secuencia en base64.

## 5. Preparar las credenciales con echo: error y corrección

Se propuso inicialmente printf, pero el usuario prefirió echo. El primer comando con echo fue ambiguo:

```bash
echo -ne '\063051\0protos2026' | base64
```

Salida real incorrecta:

```text
mDUxAHByb3RvczIwMjY=
```

El problema es que `\063` se interpreta como una secuencia octal: consume dígitos del usuario en lugar de producir un NUL seguido de 63051. No sirve como autenticación del usuario previsto.

Se corrigió usando el escape hexadecimal `\x00`:

```bash
echo -ne '\x0063051\x00protos2026' | base64
```

Salida real correcta:

```text
ADYzMDUxAHByb3RvczIwMjY=
```

| Elemento | Función |
|---|---|
| echo | Produce los bytes a codificar. |
| -n | Evita agregar un salto final a las credenciales. |
| -e | Interpreta escapes en el echo de bash usado. |
| \x00 | Produce un NUL; el escape hexadecimal consume como máximo dos dígitos. |
| Comillas simples | Conservan los escapes para que los interprete echo. |
| Tubería | Pasa los bytes a base64. |
| base64 | Representa esos bytes como texto ASCII. |

Base64 no cifra ni protege la contraseña. La sesión mostrada usó netcat contra el laboratorio local y no negoció TLS. En un servicio real, AUTH PLAIN necesita un canal protegido como TLS para mantener confidenciales las credenciales.

## 6. Autenticarse

Dentro de la conexión SMTP que ya respondió a EHLO:

```text
AUTH PLAIN ADYzMDUxAHByb3RvczIwMjY=
```

Respuesta real:

```text
235 2.7.0 Authentication successful
```

235 confirma que el servidor aceptó las credenciales. La respuesta base64 se envió en el mismo comando AUTH, por lo que no fue necesario un intercambio adicional con un desafío 334.

## 7. Declarar el sobre y pedir DATA

Después de autenticarse se indicó enviar uno por uno:

```text
MAIL FROM:<jdileomuntaner@itba.edu.ar>
RCPT TO:<profe@externo.lab>
DATA
```

Esperar 250 después de MAIL FROM y RCPT TO, y 354 después de DATA.

Las respuestas exactas de esta fase no se pegaron. Se conserva aquí la secuencia indicada; el corrector posterior confirmó la entrega autenticada.

MAIL FROM declara el remitente del sobre. RCPT TO determina el destinatario real. DATA pide transmitir el mensaje y 354 autoriza a escribirlo; aún falta aceptación final.

## 8. Obtener la fecha

En otra terminal de bash:

```bash
date -R
```

Salida real:

```text
Sun, 08 Nov 2026 16:42:24 -0300
```

-R genera una fecha apta para Date con zona horaria. En otra ejecución obtener fecha nueva y usar un Message-ID nuevo.

## 9. Mensaje preparado para enviar

Se indicó pegar después del 354:

```text
Date: Sun, 08 Nov 2026 16:42:24 -0300
Message-ID: <63051.20261108.164224.c9@mail.protos.lab>
From: Jeronimo Muntaner <jdileomuntaner@itba.edu.ar>
To: <profe@externo.lab>
X-Parcial: LAB-C9
Subject: Entrega TP
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 7bit

Adjunto la entrega del trabajo practico.
.
```

El cuerpo dice “Adjunto”, pero este ejercicio no incluyó ningún archivo: es un mensaje de texto de ejemplo y la consigna no exigía adjunto. Esa palabra no crea una parte MIME ni adjunta nada automáticamente.

| Campo | Función |
|---|---|
| Date | Fecha de creación del mensaje. |
| Message-ID | Identificador del mensaje. |
| From / To | Autor y destinatario visibles; no sustituyen al sobre SMTP. |
| X-Parcial | Marca exacta del ejercicio. |
| Subject | Asunto ASCII; no necesita encoded-word. |
| MIME-Version | Declara MIME 1.0. |
| Content-Type | Texto plano en UTF-8. |
| Content-Transfer-Encoding: 7bit | El cuerpo usado es ASCII directo. |
| Línea vacía | Separa encabezados y cuerpo. |
| Punto solo | Termina DATA, sin pertenecer al cuerpo. |

No hace falta multipart porque solo hay una parte de texto. La contraseña no aparece en este mensaje: se usó previamente en AUTH.

## 10. Aceptación y cierre

Se indicó esperar el 250 posterior al punto y cerrar con:

```text
QUIT
```

No se pegaron el identificador de cola ni la respuesta exacta al cierre; no se inventan. La recepción final quedó confirmada por el corrector.

El 250 final acepta el mensaje; QUIT cierra la sesión y normalmente responde 221.

## 11. Corrector: ejecución y salida reales

El usuario ejecutó con el identificador en minúscula:

```bash
bash lab-correo.sh corregir c9
```

El script aceptó c9 y seleccionó C9:

```text
== Corrección C9 (envío autenticado) ==
  [OK] profe@externo.lab recibió tu correo
  [OK] X-Parcial: LAB-C9
  [OK] Subject = Entrega TP
  [OK] Subject codificado en ASCII (encoded-word)
  [OK] From con tu cuenta ITBA (jdileomuntaner@itba.edu.ar)
  [OK] From con nombre y apellido (Jeronimo Muntaner)
  [OK] From en ASCII (si hay tildes, encoded-word)
  [OK] To: profe@externo.lab
  [OK] MIME-Version: 1.0
  [OK] Date válido
  [OK] Message-ID con formato <algo@dominio>
  [OK] Ninguna parte en quoted-printable
  [OK] Enviado autenticado (ESMTPSA)

  Resultado: 13/13 verificaciones bien.  ¡Aprobado!
```

La etiqueta del corrector menciona encoded-word, pero el asunto fue ASCII directo y no necesitó esa codificación.

El corrector también usa la etiqueta ESMTPSA para el envío autenticado. El transcript real mostró autenticación por AUTH PLAIN, sin STARTTLS ni otra negociación TLS. No debe inferirse cifrado del canal a partir de esa etiqueta del laboratorio; en nomenclatura estándar, ESMTPSA incluye tanto TLS como autenticación.

El Ctrl+C posterior se pulsó con el prompt ya visible, después de terminar el corrector: no revierte el envío ni su resultado.

No se realizó una lectura POP3 adicional del buzón externo; el corrector confirmó su recepción.

## 12. Qué recordar

1. Conectar al servicio indicado: recepción SMTP y submission pueden tener reglas distintas.
2. EHLO permite descubrir los mecanismos AUTH disponibles.
3. AUTH PLAIN no es solo usuario:contraseña: usa campos separados por bytes NUL.
4. Con echo en bash, usar \x00 evita que los dígitos iniciales del usuario se consuman como escape octal.
5. No agregar salto final a las credenciales.
6. Esperar 235 antes de iniciar el envío autenticado.
7. AUTH identifica al cliente; MAIL FROM, RCPT TO y los encabezados cumplen funciones diferentes.
8. Base64 representa bytes, no cifra.
