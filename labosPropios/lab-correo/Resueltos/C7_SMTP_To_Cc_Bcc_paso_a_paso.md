# C7 — To, Cc y copia oculta: paso a paso

Práctica del 8 de noviembre de 2026. **Resultado real del corrector: 17/17 verificaciones, aprobado.**

## 1. Consigna

Enviar un correo con `X-Parcial: LAB-C7` y asunto `Reunión de cátedra`:

- Destinatario principal: `63051@mail.protos.lab`.
- Copia visible: `ayudante@mail.protos.lab`.
- Copia oculta: `jefa@mail.protos.lab`.

Los tres deben recibirlo, pero la dirección de la jefa no debe aparecer en los encabezados de ninguna copia.

## 2. La idea central: sobre y mensaje

SMTP tiene un sobre de entrega, que se declara mediante comandos, y un mensaje, que se transmite después de DATA.

| Nivel | Elemento | Función |
|---|---|---|
| Sobre SMTP | MAIL FROM | Remitente del sobre, usado para notificaciones de fallo. |
| Sobre SMTP | RCPT TO, repetido | Indica cada destinatario real de la entrega. |
| Mensaje | From | Autor visible. |
| Mensaje | To | Destinatario principal visible. |
| Mensaje | Cc | Destinatarios de copia visibles. |

Para SMTP, todos los destinatarios se declaran con el mismo comando RCPT TO. No hay comandos SMTP CC o BCC.

La copia oculta de esta práctica se consigue incluyendo a la jefa en RCPT TO y omitiendo su dirección en los encabezados del mensaje. No se envía un encabezado Bcc.

## 3. Abrir la conexión SMTP

En bash:

```bash
nc -C 127.0.0.1 2525
```

- nc abre una conexión TCP.
- -C utiliza CRLF en la variante de netcat usada en esta práctica.
- 127.0.0.1 es la máquina local del lab.
- 2525 es el puerto SMTP del lab; el estándar de recepción SMTP es 25.

Esperar el saludo 220 y presentarse:

```text
EHLO cliente.lab
```

EHLO identifica al cliente y descubre extensiones. Esperar la respuesta 250 completa. En una respuesta multilínea, el guion tras el código anuncia continuación y el espacio marca la última línea.

El usuario confirmó que los pasos de esta fase estaban correctos, sin pegar su transcript completo. Por eso los códigos de esta sección son los esperados, no una transcripción literal de sus respuestas.

## 4. Declarar el remitente y los tres destinatarios

Dentro de la conexión, enviar uno por uno:

```text
MAIL FROM:<jdileomuntaner@itba.edu.ar>
RCPT TO:<63051@mail.protos.lab>
RCPT TO:<ayudante@mail.protos.lab>
RCPT TO:<jefa@mail.protos.lab>
```

Esperar un 250 positivo después de cada comando antes de enviar el siguiente. El usuario confirmó que esta fase salió correctamente.

| Dirección declarada con RCPT TO | Qué aparecerá en el mensaje |
|---|---|
| 63051@mail.protos.lab | To |
| ayudante@mail.protos.lab | Cc |
| jefa@mail.protos.lab | No se escribe en los encabezados; es copia oculta. |

Si solo escribiéramos Cc en el mensaje, sin el RCPT TO correspondiente, ese encabezado no ordenaría por sí solo al servidor SMTP entregar esa copia.

## 5. Pedir permiso para transmitir el mensaje

```text
DATA
```

Esperar 354. Esa respuesta autoriza a escribir el contenido; aún no confirma que el correo fue aceptado. La aceptación final ocurre después del punto que termina DATA.

## 6. Preparar fecha y asunto en otra terminal

Se ejecutó en bash:

```bash
date -R
echo -n 'Reunión de cátedra' | base64
```

Salidas reales:

```text
Sun, 08 Nov 2026 16:32:41 -0300
UmV1bmnDs24gZGUgY8OhdGVkcmE=
```

- date -R genera una fecha para Date con zona horaria.
- echo -n imprime el texto sin agregar un salto final.
- Las comillas simples conservan el texto literal.
- La tubería pasa esos bytes a base64.
- base64 representa bytes mediante caracteres ASCII; no cifra.

El asunto tiene caracteres no ASCII, por lo que se usa un encoded-word:

```text
Subject: =?UTF-8?B?UmV1bmnDs24gZGUgY8OhdGVkcmE=?=
```

UTF-8 indica el juego de caracteres y B la codificación base64. El signo igual final del contenido base64 y el cierre ?= se conservan.

## 7. Mensaje completo utilizado

Se indicó pegar después del 354:

```text
Date: Sun, 08 Nov 2026 16:32:41 -0300
Message-ID: <63051.20261108.163241.c7@mail.protos.lab>
From: Jeronimo Muntaner <jdileomuntaner@itba.edu.ar>
To: <63051@mail.protos.lab>
Cc: <ayudante@mail.protos.lab>
X-Parcial: LAB-C7
Subject: =?UTF-8?B?UmV1bmnDs24gZGUgY8OhdGVkcmE=?=
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 7bit

Los invito a la proxima reunion de catedra.
.
```

El usuario confirmó que llegó a la respuesta de cola y el corrector identificó el mensaje por su Message-ID y asunto. No pegó el transcript completo de DATA ni el identificador concreto de cola.

Para repetir el envío, usar fecha actual y un Message-ID nuevo.

### Campos del mensaje

| Elemento | Función |
|---|---|
| Date | Fecha de creación del mensaje. |
| Message-ID | Identificador único del mensaje. |
| From | Autor visible, con nombre y cuenta ITBA. |
| To | Destinatario principal visible. |
| Cc | Copia visible al ayudante. |
| X-Parcial | Marca exacta del ejercicio. |
| Subject | Asunto con encoded-word. |
| MIME-Version: 1.0 | Declara uso de MIME. |
| Content-Type: text/plain; charset=UTF-8 | Texto plano que se interpreta como UTF-8. |
| Content-Transfer-Encoding: 7bit | El cuerpo usa ASCII y se transmite directamente. |
| Línea vacía | Separa encabezados y cuerpo. |
| Punto solo | Termina DATA en SMTP; no pertenece al cuerpo. |

El cuerpo se escribió deliberadamente sin tildes, por eso 7bit es adecuado. El asunto, en cambio, sí tiene tildes y fue codificado por separado. No necesitamos multipart porque solo hay una parte de texto.

## 8. ¿Por qué no escribir Bcc?

La consigna exige ocultar a la jefa en los encabezados de todas las copias. En la sesión manual con netcat enviamos el mensaje tal como lo construimos, por lo que omitimos Bcc y mantenemos a la jefa solo en el sobre SMTP.

Los clientes de correo con un campo Bcc suelen encargarse de generar los destinatarios del sobre y preparar los encabezados de las copias. Aquí hicimos ese trabajo manualmente.

La copia oculta evita que su dirección aparezca en estos encabezados; no oculta el destinatario al servidor que debe entregarle el correo.

## 9. Aceptación y cierre

El usuario indicó que el mensaje quedó en una respuesta de cola. La respuesta esperada es:

```text
250 2.0.0 Ok: queued as IDENTIFICADOR
```

Ese identificador no fue pegado en el chat, por lo que no se inventa uno. El corrector posterior confirmó las entregas.

Se indicó cerrar con:

```text
QUIT
```

Su respuesta exacta no se pegó. Se espera 221 y cierre. El mensaje ya se acepta al responder positivamente al punto final, no al enviar QUIT.

## 10. Corrector: resultado real

En bash, desde la carpeta del laboratorio:

```bash
bash lab-correo.sh corregir C7
```

bash ejecuta el script, corregir selecciona la acción y C7 el ejercicio.

Salida real:

```text
== Corrección C7 (To, Cc y Bcc) ==
  corrigiendo: <63051.20261108.163241.c7@mail.protos.lab>  ·  Subject: 'Reunión de cátedra'
  [OK] X-Parcial: LAB-C7
  [OK] Subject = Reunión de cátedra
  [OK] Subject codificado en ASCII (encoded-word)
  [OK] From con tu cuenta ITBA (jdileomuntaner@itba.edu.ar)
  [OK] From con nombre y apellido (Jeronimo Muntaner)
  [OK] From en ASCII (si hay tildes, encoded-word)
  [OK] To: 63051@mail.protos.lab
  [OK] MIME-Version: 1.0
  [OK] Date válido
  [OK] Message-ID con formato <algo@dominio>
  [OK] Ninguna parte en quoted-printable
  [OK] Cc: ayudante@mail.protos.lab
  [OK] ayudante@mail.protos.lab recibió el correo
  [OK] La copia de ayudante@mail.protos.lab no muestra Bcc
  [OK] jefa@mail.protos.lab recibió el correo
  [OK] La copia de jefa@mail.protos.lab no muestra Bcc
  [OK] jefa no aparece en To/Cc (copia oculta)

  Resultado: 17/17 verificaciones bien.  ¡Aprobado!
```

No se realizó una verificación POP3 adicional en esta práctica. La entrega y los encabezados se verificaron con el corrector.

## 11. Qué recordar

1. Todo destinatario real necesita su RCPT TO, sea principal, Cc o copia oculta.
2. To y Cc describen destinatarios visibles dentro del mensaje.
3. Para esta copia oculta manual, la jefa está en el sobre y no aparece en los encabezados.
4. Repetir RCPT TO no exige multipart: destinatarios múltiples y partes MIME múltiples son conceptos independientes.
5. Esperar respuestas positivas en cada paso y el 250 final de aceptación.
