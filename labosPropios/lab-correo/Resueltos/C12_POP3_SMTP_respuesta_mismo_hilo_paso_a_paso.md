# C12 — Responder un correo conservando el hilo

Práctica del 8 de noviembre de 2026. **Resultado real: 13/13 verificaciones, aprobado.**

## 1. Consigna

En el buzón propio hay un correo de `atorres@mail.protos.lab`, con asunto `Consulta sobre la entrega`. Responder a esa dirección confirmando el legajo en el cuerpo, con asunto de respuesta y encabezados que enlacen el mensaje al hilo original.

## 2. Datos utilizados

| Dato | Valor |
|---|---|
| POP3 del lab | 127.0.0.1:2110 |
| SMTP del lab | 127.0.0.1:2525 |
| Buzón propio | 63051@mail.protos.lab |
| Usuario y contraseña POP3 | Ambos 63051@mail.protos.lab en este lab |
| Cuenta remitente | jdileomuntaner@itba.edu.ar |
| Profesora | Prof. Ana Torres <atorres@mail.protos.lab> |
| Message-ID original | <consulta-7731@mail.protos.lab> |
| Message-ID nuevo preparado | <63051.20261108.165807.c12@mail.protos.lab> |
| Legajo confirmado | 63051 |

## 3. Abrir POP3 y autenticar

En bash:

```bash
nc -C 127.0.0.1 2110
```

nc establece TCP y -C utiliza CRLF en la variante de netcat de esta práctica. El puerto POP3 del lab es 2110; el estándar sin TLS implícito es 110.

Diálogo real:

```text
+OK POP3 LabProtos ready
USER 63051@mail.protos.lab
+OK
PASS 63051@mail.protos.lab
+OK Logged in. 7 messages
LIST
+OK 7 messages:
1 629
2 563
3 770
4 2203
5 2116
6 623
7 677
.
```

USER identifica el buzón y PASS autentica. La contraseña igual al usuario es una configuración del lab. LIST muestra números y tamaños en octetos, no asuntos. El punto termina la respuesta multilínea.

## 4. Identificar el correo por sus encabezados

Se ejecutó:

```text
TOP 1 0
```

TOP recibe el número de mensaje y la cantidad de líneas del cuerpo; cero pide solo encabezados.

Respuesta real:

```text
+OK
Return-Path: <semilla@protos.lab>
Received: from semilla (localhost [127.0.0.1])
	by mx1.protos.lab with ESMTP id SEED0002
	for <63051@mail.protos.lab>; Sun, 08 Nov 2026 12:21:32 -0300
From: Prof. Ana Torres <atorres@mail.protos.lab>
To: <63051@mail.protos.lab>
Subject: Consulta sobre la entrega
Date: Sun, 08 Nov 2026 12:21:32 -0300
Message-ID: <consulta-7731@mail.protos.lab>
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: base64

.
```

Se reconoció el mensaje por From y Subject. Se guardó su Message-ID, que identifica el mensaje original y será usado para enlazar la respuesta.

El número POP3 1 sirve dentro de esta sesión; no es el identificador del hilo ni reemplaza al Message-ID. Los números pueden cambiar entre sesiones.

## 5. Leer la consulta

Se ejecutó:

```text
RETR 1
```

El servidor respondió +OK 629 octets y devolvió los mismos encabezados, seguidos de este cuerpo:

```text
SG9sYS4gwr9NZSBjb25maXJtw6FzIHR1IG7Dum1lcm8gZGUgbGVnYWpvIHJlc3BvbmRpZW5kbyBl
c3RlIGNvcnJlbz8gVGllbmUgcXVlIHF1ZWRhciBlbiBlbCBtaXNtbyBoaWxvLgo=
```

RETR recupera el mensaje sin borrarlo. POP3 no interpreta MIME ni decodifica el cuerpo. El punto que termina su respuesta no forma parte del base64.

Se indicó cerrar con QUIT, sin usar DELE. No se pegó la respuesta exacta al cierre; no se solicitó borrar el original.

## 6. Decodificar y obtener la fecha

Comando ejecutado en bash:

```bash
echo 'SG9sYS4gwr9NZSBjb25maXJtw6FzIHR1IG7Dum1lcm8gZGUgbGVnYWpvIHJlc3BvbmRpZW5kbyBl
c3RlIGNvcnJlbz8gVGllbmUgcXVlIHF1ZWRhciBlbiBlbCBtaXNtbyBoaWxvLgo=' | base64 -d
```

Salida real:

```text
Hola. ¿Me confirmás tu número de legajo respondiendo este correo? Tiene que quedar en el mismo hilo.
```

Las comillas simples conservan el bloque. La tubería entrega el texto a base64 y -d indica decodificar. El decodificador admite los saltos de línea de la representación base64.

Después:

```bash
date -R
```

Salida real:

```text
Sun, 08 Nov 2026 16:58:07 -0300
```

-R genera una fecha apta para Date con zona horaria.

## 7. Cómo vincular la respuesta con el original

| Encabezado en la respuesta | Valor usado | Función |
|---|---|---|
| Message-ID | <63051.20261108.165807.c12@mail.protos.lab> | Identifica el mensaje nuevo. |
| In-Reply-To | <consulta-7731@mail.protos.lab> | Identifica el mensaje al que respondemos. |
| References | <consulta-7731@mail.protos.lab> | Registra la referencia al original dentro del hilo. |
| Subject | Re: Consulta sobre la entrega | Presenta visualmente el asunto como respuesta. |

La respuesta no reutiliza el Message-ID original como identificador propio: son dos mensajes diferentes.

Poner solo Re: no establece esa relación explícita mediante identificadores. Los clientes pueden usar otras heurísticas, pero estos encabezados expresan el vínculo entre los mensajes.

Aquí el original no tenía References. En una conversación más larga, normalmente se conservan las referencias anteriores y se agrega el Message-ID del mensaje al que se responde. Esa ampliación no fue necesaria en este ejercicio.

## 8. Abrir SMTP y declarar el sobre

Se indicó ejecutar en bash:

```bash
nc -C 127.0.0.1 2525
```

Esperar 220 y enviar cada comando esperando su respuesta:

```text
EHLO cliente.lab
MAIL FROM:<jdileomuntaner@itba.edu.ar>
RCPT TO:<atorres@mail.protos.lab>
DATA
```

Esperar 250 después de EHLO, MAIL FROM y RCPT TO; después de DATA, esperar 354 antes de pegar el mensaje.

- EHLO presenta al cliente y descubre extensiones.
- MAIL FROM declara el remitente del sobre.
- RCPT TO determina a quién se entrega realmente el correo.
- DATA solicita transmitir el contenido.
- 354 autoriza a escribirlo; no es aceptación final.

Los encabezados From y To son parte del mensaje visible y no sustituyen al sobre SMTP. 2525 es el puerto del lab; el estándar de recepción SMTP es 25.

El usuario no pegó el transcript SMTP de esta fase. Se documenta la secuencia indicada; el corrector posterior confirmó la entrega y los encabezados requeridos.

## 9. Mensaje preparado para enviar

Después del 354:

```text
Date: Sun, 08 Nov 2026 16:58:07 -0300
Message-ID: <63051.20261108.165807.c12@mail.protos.lab>
From: Jeronimo Muntaner <jdileomuntaner@itba.edu.ar>
To: <atorres@mail.protos.lab>
Subject: Re: Consulta sobre la entrega
In-Reply-To: <consulta-7731@mail.protos.lab>
References: <consulta-7731@mail.protos.lab>
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 7bit

Mi numero de legajo es 63051.
.
```

Para repetir el envío, obtener fecha nueva y usar otro Message-ID propio.

Date indica la fecha de creación. MIME-Version declara MIME. Content-Type indica texto plano en UTF-8; 7bit es adecuado porque el cuerpo preparado usa solo ASCII, sin tilde en numero. El asunto y el nombre también son ASCII y no necesitan encoded-word.

No se necesita multipart: hay una única parte de texto. Tampoco se pidió X-Parcial para C12, por lo que no se agregó.

La línea vacía separa encabezados y cuerpo. El punto solo termina DATA y no pertenece al contenido entregado.

## 10. Aceptación y cierre

Se indicó esperar el 250 posterior al punto y cerrar con:

```text
QUIT
```

No se pegó el identificador de cola ni la respuesta exacta al cierre; no se inventan. La respuesta esperada al cierre es 221. La entrega quedó confirmada por el corrector.

## 11. Corrector: ejecución y salida reales

El usuario ejecutó con el identificador en minúscula:

```bash
bash lab-correo.sh corregir c12
```

El script aceptó c12 y seleccionó C12. bash ejecuta el script y corregir selecciona la acción.

```text
== Corrección C12 (respuesta en el mismo hilo) ==
  [OK] La profesora recibió tu respuesta
  [OK] Subject = Re: Consulta sobre la entrega
  [OK] Subject codificado en ASCII (encoded-word)
  [OK] From con tu cuenta ITBA (jdileomuntaner@itba.edu.ar)
  [OK] From con nombre y apellido (Jeronimo Muntaner)
  [OK] From en ASCII (si hay tildes, encoded-word)
  [OK] To: atorres@mail.protos.lab
  [OK] MIME-Version: 1.0
  [OK] Date válido
  [OK] Message-ID con formato <algo@dominio>
  [OK] In-Reply-To: <consulta-7731@mail.protos.lab>
  [OK] References incluye <consulta-7731@mail.protos.lab>
  [OK] El cuerpo tiene tu legajo

  Resultado: 13/13 verificaciones bien.  ¡Aprobado!
```

El corrector menciona encoded-word de forma genérica, pero el Subject usado es ASCII directo y no necesitó esa envoltura.

## 12. Qué recordar

1. Identificar el correo original por sus encabezados, no solo por el número POP3.
2. Leer el cuerpo antes de responder y respetar la codificación declarada.
3. Crear un Message-ID nuevo para la respuesta.
4. Copiar el Message-ID original en In-Reply-To.
5. Construir References con la cadena de referencias pertinente; en este caso solo el original.
6. Usar el asunto Re: solicitado y contestar al destinatario correcto.
7. No borrar el original si la consigna no lo pide.

## 13. Estado final de la práctica completa

Se recorrieron todas las variantes C1 a C12. C2 quedó como guía de respuestas esperadas, sin ejecución independiente, porque repetía el envío de texto plano de C1 con otro X-Parcial. Los demás ejercicios se ejecutaron y sus correctores aprobaron en la conversación.
