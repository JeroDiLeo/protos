# C3 — Cuerpo en negrita con alternativa de texto plano

Práctica del 8 de noviembre de 2026. **Resultado real: 17/17 verificaciones, aprobado.**

## 1. Consigna

Igual que C2, pero con `X-Parcial: 2026/1R`. El cuerpo `¡Hola mundo!` debe verse en negrita en los clientes de correo con formato, conservando una versión de texto plano para los que no lo soporten. Sin quoted-printable.

Se mantienen: asunto `¡Buenos días!`, remitente con nombre/apellido/cuenta ITBA, entrega al buzón propio y verificación por POP3.

## 2. Datos usados

| Dato | Valor |
|---|---|
| SMTP del lab | `127.0.0.1:2525` |
| POP3 del lab | `127.0.0.1:2110` |
| Nombre | `Jeronimo Muntaner` |
| Cuenta ITBA | `jdileomuntaner@itba.edu.ar` |
| Destinatario | `63051@mail.protos.lab` |
| Usuario y contraseña POP3 | Ambos `63051@mail.protos.lab` |
| Message-ID | `<63051.20261108.131231.c3@mail.protos.lab>` |
| Identificador de cola | `26DB0A003E` |

Los puertos estándar son 25 para recepción SMTP y 110 para POP3 sin TLS implícito. El laboratorio usa 2525 y 2110.

## 3. Por qué usamos multipart/alternative

Hay dos representaciones del mismo contenido:

| Parte | Contenido decodificado | Uso |
|---|---|---|
| text/plain | `¡Hola mundo!` | Lectores de texto plano. |
| text/html | `<b>¡Hola mundo!</b>` | Lectores con formato, que muestran negrita. |

`multipart/alternative` permite que el cliente elija una representación que soporte. Se coloca primero la versión simple y después la más rica. No se pretende mostrar ambas una debajo de la otra.

Usar solo HTML no cumpliría la alternativa de texto plano. Poner etiquetas HTML dentro de text/plain mostraría las etiquetas como texto, sin aplicar negrita.

Ambas partes usan UTF-8 y base64. Los encabezados del mensaje se codifican por separado cuando lo necesitan.

## 4. Abrir SMTP

Comando ejecutado en bash:

```bash
nc -C 127.0.0.1 2525
```

- nc establece la conexión TCP.
- -C usa finales de línea CRLF en la variante de netcat usada.
- 127.0.0.1 apunta a la máquina local donde corre el lab.
- 2525 es el puerto SMTP del lab.

Respuesta real:

```text
220 mx1.protos.lab ESMTP LabProtos ready
```

220 indica que el servicio está listo. A partir de aquí se escriben comandos SMTP dentro de netcat.

## 5. Presentarse

```text
EHLO cliente.lab
```

Respuesta real:

```text
250-mx1.protos.lab Hello cliente.lab
250-SIZE 10240000
250-8BITMIME
250 HELP
```

EHLO presenta al cliente y descubre extensiones. El guion después de 250 anuncia más líneas; el espacio marca la última. SIZE anuncia el máximo de bytes. 8BITMIME permite negociar cuerpos de ocho bits; no habilita por sí solo UTF-8 en encabezados. Usamos base64 en el cuerpo y encoded-word en Subject.

Como el saludo fue aceptado, continuamos con el sobre.

## 6. Remitente y destinatario reales

Se envió:

```text
MAIL FROM:<jdileomuntaner@itba.edu.ar>
250 2.1.0 Ok
RCPT TO:<63051@mail.protos.lab>
250 2.1.5 Ok
DATA
354 End data with <CR><LF>.<CR><LF>
```

Las líneas 250 y 354 son respuestas del servidor, no comandos para escribir.

MAIL FROM declara el remitente del sobre, usado para notificaciones de fallo. RCPT TO determina dónde se entrega la copia; To es un encabezado visible y no reemplaza este comando.

Los dos 250 permitieron avanzar. DATA solicita transmitir el contenido; el 354 autoriza a escribirlo. Aún falta terminar DATA y recibir aceptación.

## 7. Preparar fecha y HTML en otra terminal

Se dejó abierta la conexión esperando el mensaje y se ejecutó en otra terminal:

```bash
date -R
```

Salida real:

```text
Sun, 08 Nov 2026 13:12:31 -0300
```

-R genera una fecha adecuada para Date. -0300 expresa la zona horaria. Para otro envío, obtener una fecha nueva.

Después:

```bash
echo -n '<b>¡Hola mundo!</b>' | base64
```

Salida real:

```text
PGI+wqFIb2xhIG11bmRvITwvYj4=
```

- Las etiquetas b indican negrita en HTML.
- Las comillas simples conservan el contenido literal, incluidos los signos < y >.
- echo -n evita agregar un salto al texto original.
- La tubería pasa los bytes a base64.
- Base64 representa bytes con ASCII; no cifra ni convierte por sí mismo texto plano en HTML.

Para la parte de texto plano se reutilizó:

```text
wqFIb2xhIG11bmRvIQ==
```

Corresponde a `¡Hola mundo!`. Para volver a generarlo:

```bash
echo -n '¡Hola mundo!' | base64
```

Este último comando se da como referencia; no se volvió a ejecutar en el tramo registrado de C3.

El asunto usa el encoded-word ya preparado:

```text
Subject: =?UTF-8?B?wqFCdWVub3MgZMOtYXMh?=
```

UTF-8 es el juego de caracteres, B significa base64 y ?= cierra la envoltura. El nombre Jeronimo Muntaner se usó sin tilde, por lo que es ASCII.

## 8. Mensaje completo enviado

En la conexión que había respondido 354:

```text
Date: Sun, 08 Nov 2026 13:12:31 -0300
Message-ID: <63051.20261108.131231.c3@mail.protos.lab>
From: Jeronimo Muntaner <jdileomuntaner@itba.edu.ar>
To: <63051@mail.protos.lab>
X-Parcial: 2026/1R
Subject: =?UTF-8?B?wqFCdWVub3MgZMOtYXMh?=
MIME-Version: 1.0
Content-Type: multipart/alternative; boundary="limiteC3"

--limiteC3
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: base64

wqFIb2xhIG11bmRvIQ==

--limiteC3
Content-Type: text/html; charset=UTF-8
Content-Transfer-Encoding: base64

PGI+wqFIb2xhIG11bmRvITwvYj4=
--limiteC3--
.
```

### Cómo interpretar la estructura

| Elemento | Función |
|---|---|
| Date | Fecha de creación del mensaje. |
| Message-ID | Identificador del mensaje, elegido por el emisor; usar uno nuevo para cada mensaje nuevo. |
| From / To | Autor y destinatario visibles. |
| X-Parcial | Identifica este ejercicio con el valor exacto solicitado. |
| MIME-Version: 1.0 | Declara MIME. |
| multipart/alternative | El cuerpo contiene versiones alternativas del mismo contenido. |
| boundary="limiteC3" | Define el texto separador; las comillas no forman parte de ese texto. |
| --limiteC3 | Abre una parte MIME. |
| charset=UTF-8 | Indica cómo interpretar los bytes después de decodificar base64. |
| Content-Transfer-Encoding: base64 | Codificación de esa parte; se declara en cada una. |
| --limiteC3-- | Cierra el conjunto multipart. |
| Punto solo | Termina DATA en SMTP. |

Hay una línea vacía entre los encabezados generales y el cuerpo multipart. Dentro de cada parte, otra línea vacía separa sus encabezados del contenido base64. Mantenerlas.

El encabezado general no declara base64 para todo el multipart: los separadores deben seguir siendo reconocibles. La codificación se aplica a cada parte individual.

## 9. Aceptación SMTP y cierre

Respuesta real al punto final:

```text
250 2.0.0 Ok: queued as 26DB0A003E
```

Este 250 confirma la aceptación. 26DB0A003E es el identificador de cola del servidor, distinto del Message-ID que elegimos.

Se indicó cerrar SMTP:

```text
QUIT
```

La respuesta exacta al cierre no fue pegada en el chat; se espera 221 y desconexión. QUIT no es el comando que envía el correo: el servidor ya lo había aceptado.

## 10. Abrir POP3 y autenticarse

Se indicó ejecutar desde bash:

```bash
nc -C 127.0.0.1 2110
```

Esperar +OK y enviar uno por uno:

```text
USER 63051@mail.protos.lab
PASS 63051@mail.protos.lab
LIST
```

El usuario pegó la respuesta de LIST; no copió el saludo ni las respuestas individuales a USER y PASS. El acceso posterior al buzón confirma que la sesión estaba autenticada.

USER identifica el buzón, PASS autentica. Que ambos valores coincidan es una configuración del lab.

## 11. Listar mensajes

Salida real:

```text
+OK 4 messages:
1 915
2 629
3 563
4 770
.
```

Cada fila contiene número de mensaje y tamaño en octetos. El punto cierra la respuesta multilínea. El 4 era candidato por ser el último, pero LIST por sí solo no identifica el contenido ni prueba que sea C3.

Por eso recuperamos el mensaje para comprobar sus encabezados.

## 12. Recuperar el mensaje 4

Comando y respuesta reales:

```text
RETR 4
+OK 770 octets
Return-Path: <jdileomuntaner@itba.edu.ar>
Received: from cliente.lab (localhost [127.0.0.1])
	by mx1.protos.lab with ESMTP id 26DB0A003E
	for <63051@mail.protos.lab>; Sun, 08 Nov 2026 13:13:39 -0300
Date: Sun, 08 Nov 2026 13:12:31 -0300
Message-ID: <63051.20261108.131231.c3@mail.protos.lab>
From: Jeronimo Muntaner <jdileomuntaner@itba.edu.ar>
To: <63051@mail.protos.lab>
X-Parcial: 2026/1R
Subject: =?UTF-8?B?wqFCdWVub3MgZMOtYXMh?=
MIME-Version: 1.0
Content-Type: multipart/alternative; boundary="limiteC3"

--limiteC3
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: base64

wqFIb2xhIG11bmRvIQ==

--limiteC3
Content-Type: text/html; charset=UTF-8
Content-Transfer-Encoding: base64

PGI+wqFIb2xhIG11bmRvITwvYj4=
--limiteC3--
.
```

La identidad se confirmó por X-Parcial, Message-ID y el identificador 26DB0A003E en Received, que coincide con la aceptación SMTP.

Return-Path deriva del remitente del sobre. Received registra el paso por el servidor y la hora de recepción. Las líneas indentadas continúan el mismo encabezado.

RETR recupera sin borrar. POP3 no interpreta HTML ni decodifica MIME; devuelve el mensaje para que lo procese el cliente. El punto final es el terminador POP3, no una parte del correo.

Se indicó cerrar con QUIT; su respuesta exacta no se pegó. No se pidió DELE, por lo que no se solicitó borrar el mensaje.

## 13. Decodificar HTML

Comandos ejecutados en bash:

```bash
echo 'PGI+wqFIb2xhIG11bmRvITwvYj4=' | base64 -d
echo
```

Resultado real:

```text
<b>¡Hola mundo!</b>
```

-d significa decodificar. El segundo echo agrega un salto para que el prompt no quede pegado. El texto original no tenía salto final porque se generó con echo -n.

Que la terminal muestre las etiquetas es correcto: imprime texto. Un cliente de correo que elija la parte text/html las interpreta y muestra la negrita.

## 14. Corrector

Desde la carpeta del lab:

```bash
bash lab-correo.sh corregir C3
```

bash ejecuta el script; corregir elige la acción; C3 identifica el ejercicio. Este es un comando local, no SMTP ni POP3.

Salida real:

```text
== Corrección C3 (negrita) ==
  corrigiendo: <63051.20261108.131231.c3@mail.protos.lab>  ·  Subject: '¡Buenos días!'
  [OK] X-Parcial: 2026/1R
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
  [OK] Estructura multipart/alternative
  [OK] Hay una parte text/plain
  [OK] Texto = ¡Hola mundo!
  [OK] Hay una parte text/html
  [OK] ¡Hola mundo! en <b> o <strong>
  [OK] Orden: text/plain primero, text/html último

  Resultado: 17/17 verificaciones bien.  ¡Aprobado!
```

## 15. Cómo reconocer esta variante en un examen

Si piden formato y compatibilidad con lectores sin formato, preparar multipart/alternative, con texto plano primero y HTML después. Si además prohíben quoted-printable, base64 permite transportar los bytes UTF-8 de cada parte.

Separar tres niveles: SMTP entrega el mensaje; MIME organiza sus versiones y codificaciones; HTML aplica el formato en la versión que lo declara.

## 16. Errores frecuentes

- Usar solo HTML y omitir la versión de texto plano.
- Usar multipart/mixed para representar alternativas del mismo contenido.
- Escribir las etiquetas b en una parte declarada text/plain.
- Cambiar el boundary del encabezado sin cambiar sus delimitadores.
- Omitir los dos guiones finales del cierre multipart.
- Confundir --limiteC3-- con el punto que termina DATA.
- Codificar todo el multipart en base64 en lugar del contenido de cada parte.
- Omitir líneas vacías o declarar una codificación distinta de la usada.
- Confundir el 354 con aceptación final: esperar el 250 posterior al punto y verificar por POP3.

