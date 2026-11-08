# C6 — Imagen dentro del HTML: SMTP, MIME related y POP3

Práctica del 8 de noviembre de 2026. **Resultado real del corrector: 16/16, aprobado.** La entrega también se verificó por POP3.

## 1. Consigna

Enviar al buzón propio un correo con:

- `X-Parcial: LAB-C6`.
- Asunto `Logo en el cuerpo`.
- Un cuerpo HTML que muestre la imagen `logo.png` dentro del mensaje mediante `cid:`.

## 2. Datos usados

| Dato | Valor |
|---|---|
| Carpeta de trabajo del usuario | ~/Documents/protoslaboratorios/labcorreo |
| Archivo de imagen | /home/jerodileo/lab-correo/adjuntos/logo.png |
| SMTP del lab | 127.0.0.1:2525 |
| POP3 del lab | 127.0.0.1:2110 |
| Remitente | Jeronimo Muntaner <jdileomuntaner@itba.edu.ar> |
| Buzón | 63051@mail.protos.lab |
| Usuario y contraseña POP3 | Ambos 63051@mail.protos.lab en este lab |
| Cola SMTP | 8B11ED5E69 |
| Message-ID | <63051.20261108.133057.c6@mail.protos.lab> |

## 3. Encontrar la imagen

Primero se probó desde la carpeta de trabajo:

```bash
ls -lh adjuntos/logo.png
```

Salida real:

```text
ls: cannot access 'adjuntos/logo.png': No such file or directory
```

Era una ruta relativa: buscaba dentro de la carpeta actual. El archivo estaba en otra instalación/carpeta del laboratorio. Se comprobó:

```bash
ls -lh ~/lab-correo/adjuntos/logo.png
```

Salida real:

```text
-rw-rw-r-- 1 jerodileo jerodileo 982 Nov  8 12:21 /home/jerodileo/lab-correo/adjuntos/logo.png
```

- ls lista el archivo.
- -l muestra detalles.
- -h usa unidades legibles para tamaños cuando corresponde.
- ~ se expande al directorio personal del usuario.

No se necesitó mover ni regenerar la imagen.

## 4. Preparar fecha y base64

Se ejecutó en bash:

```bash
date -R
base64 ~/lab-correo/adjuntos/logo.png
```

Fecha real:

```text
Sun, 08 Nov 2026 13:30:57 -0300
```

El base64 completo se conserva en el mensaje de la sección 7.

date -R produce una fecha apta para Date con zona horaria. base64 lee los bytes del archivo y los representa mediante caracteres ASCII; no modifica el PNG ni lo cifra. No se usa echo para leer un archivo binario.

## 5. Elegir la estructura MIME

Usamos multipart/related porque el HTML y la imagen son partes relacionadas de una misma presentación.

| Elemento | Relación |
|---|---|
| HTML: src="cid:logoC6" | Referencia un recurso incluido en el correo. |
| Imagen: Content-ID: <logoC6> | Identifica la parte que satisface esa referencia. |
| Content-Disposition: inline | Indica la intención de mostrarla dentro del mensaje. |
| filename="logo.png" | Proporciona un nombre al recurso. |

En el HTML se escribe cid:logoC6; en Content-ID se escribe <logoC6>. Los delimitadores son distintos, pero el identificador debe coincidir.

Comparación con ejercicios anteriores:

| Tipo MIME | Cuándo usarlo |
|---|---|
| multipart/alternative | Versiones alternativas del mismo contenido, por ejemplo texto plano y HTML (C3). |
| multipart/related | HTML y recursos que utiliza, por ejemplo una imagen referenciada con cid (C6). |
| multipart/mixed | Conjunto de partes independientes, por ejemplo cuerpo y archivos adjuntos. |

No basta con indicar una ruta de la computadora en src: el destinatario no tiene acceso a ese archivo local. La imagen viaja en su propia parte MIME.

## 6. Abrir SMTP y declarar el sobre

En bash:

```bash
nc -C 127.0.0.1 2525
```

nc abre TCP; -C usa CRLF en la variante de netcat de esta práctica; 2525 es el puerto SMTP del lab. El puerto estándar de recepción SMTP es 25.

Diálogo real antes del mensaje:

```text
220 mx1.protos.lab ESMTP LabProtos ready
EHLO cliente.lab
250-mx1.protos.lab Hello cliente.lab
250-SIZE 10240000
250-8BITMIME
250 HELP
MAIL FROM:<jdileomuntaner@itba.edu.ar>
250 2.1.0 Ok
RCPT TO:<63051@mail.protos.lab>
250 2.1.5 Ok
DATA
354 End data with <CR><LF>.<CR><LF>
```

Las líneas numéricas son respuestas del servidor. Se espera una respuesta positiva antes de seguir.

- 220: servicio listo.
- EHLO: presentación y descubrimiento de extensiones. El guion en 250- indica continuación; 250 con espacio marca la última línea.
- MAIL FROM: remitente del sobre.
- RCPT TO: destinatario real de entrega.
- DATA: solicita transmitir el mensaje.
- 354: permite escribir el contenido, pero todavía no confirma aceptación.

From y To dentro del mensaje son encabezados visibles; no sustituyen MAIL FROM y RCPT TO.

## 7. Mensaje completo enviado

Este bloque contiene los encabezados, las partes MIME, la imagen y el punto final SMTP. Se pegó después del 354.

```text
Date: Sun, 08 Nov 2026 13:30:57 -0300
Message-ID: <63051.20261108.133057.c6@mail.protos.lab>
From: Jeronimo Muntaner <jdileomuntaner@itba.edu.ar>
To: <63051@mail.protos.lab>
X-Parcial: LAB-C6
Subject: Logo en el cuerpo
MIME-Version: 1.0
Content-Type: multipart/related; boundary="limiteC6"

--limiteC6
Content-Type: text/html; charset=UTF-8
Content-Transfer-Encoding: 7bit

<html><body><p>Logo del laboratorio:</p><img src="cid:logoC6" alt="Logo del laboratorio"></body></html>
--limiteC6
Content-Type: image/png
Content-Transfer-Encoding: base64
Content-ID: <logoC6>
Content-Disposition: inline; filename="logo.png"

iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAIAAABvFaqvAAADnUlEQVR4nBXUqxpFERSF0Z1lWZZl
WZZlWZZlWf6zLMuyLHuO43iA8VmXub7vQ3zID/WhP8yH/XAf/iN8xI/0kT/KR/1oH3z0j/ExP9bH
/jgf9+P7BEIgBUqgBUZgBU7gBUEQBUmQBUVQBU2AoAuGYAqWYAuO4IoHSYRESpRES4zESpzES4Ik
SpIkS4qkSpoESZcMyZQsyZYcyZUPUgiFVCiFVhiFVTiFVwRFVCRFVhRFVTQFiq4YiqlYiq04iqse
pBEaqVEarTEaq3EarwmaqEmarCmaqmkaNF0zNFOzNFtzNFc/yCAM0qAM2mAM1uAM3hAM0ZAM2VAM
1dAMGLphGKZhGbbhGK55kEVYpEVZtMVYrMVZvCVYoiVZsqVYqqVZsHTLsEzLsmzLsVz7IIdwSIdy
aIdxWIdzeEdwREdyZEdxVEdz4OiO4ZiO5diO47juQR7hkR7l0R7jsR7n8Z7giZ7kyZ7iqZ7mwdM9
wzM9y7M9x3P9gwIiIAMqoAMmYAMu4AMhEAMpkAMlUAMtQKAHRmAGVmAHTuCGB0VEREZUREdMxEZc
xEdCJEZSJEdKpEZahEiPjMiMrMiOnMiND0qIhEyohE6YhE24hE+EREykRE6URE20BImeGImZWImd
OImbHpQRGZlRGZ0xGZtxGZ8JmZhJmZwpmZppGTI9MzIzszI7czI3P6ggCrKgCrpgCrbgCr4QCrGQ
CrlQCrXQChR6YRRmYRV24RRueVBFVGRFVXTFVGzFVXwlVGIlVXKlVGqlVaj0yqjMyqrsyqnc+qCG
aMiGauiGadiGa/hGaMRGauRGadRGa9DojdGYjdXYjdO47UH/w/Ai/cL4YvQC8Fb3Ld1blzfoN6LX
3NeWV9D7ykP+r8OACQs2HLjvTH0d0ZEd1dEd07Ed1/Gd0Imd1Mmd0qmd1v9M74zO7KzO7pzO7Q8a
iIEcqIEemIEduIEfhEEcpEEelEEdtPH/TB+MwRyswR6cwR0PmoiJnKiJnpiJnbiJn4RJnKRJnpRJ
nbT5L6lPxmRO1mRPzuTOBy3EQi7UQi/Mwi7cwi/CIi7SIi/Koi7a+jemL8ZiLtZiL87irgdtxEZu
1EZvzMZu3MZvwiZu0iZvyqZu2v63t2/GZm7WZm/O5u4HHcRBHtRBH8zBHtzBH8IhHtIhH8qhHtr5
D6kfxmEe1mEfzuGeB13ERV7URV/MxV7cxV/CJV7SJV/KpV7a/Y+6X8ZlXtZlX87lXn7fPm2u+adQ
jgAAAABJRU5ErkJggg==
--limiteC6--
.
```

Para repetirlo en otra ocasión, obtener una fecha actual y usar un Message-ID nuevo.

## 8. Explicación de los campos y separadores

| Campo o elemento | Función |
|---|---|
| Date | Fecha de creación del mensaje. |
| Message-ID | Identificador único del mensaje. |
| From / To | Autor y destinatario visibles. |
| X-Parcial | Marca exacta del ejercicio. |
| Subject | Asunto. Aquí contiene solo ASCII y se escribió directamente. |
| MIME-Version: 1.0 | Declara uso de MIME. |
| multipart/related | Agrupa HTML y recursos relacionados. |
| boundary="limiteC6" | Define el separador; las comillas no forman parte de él. |
| --limiteC6 | Inicia una parte MIME. |
| text/html; charset=UTF-8 | Declara que la primera parte es HTML. |
| Content-Transfer-Encoding: 7bit | El HTML de esta ejecución es ASCII y se transmite directamente. |
| image/png | Identifica el tipo de la imagen. |
| Content-Transfer-Encoding: base64 | Explica cómo recuperar los bytes binarios del PNG. |
| Content-ID: <logoC6> | Permite que el HTML encuentre la imagen mediante cid. |
| Content-Disposition: inline | Sugiere mostrar el recurso dentro del mensaje. |
| --limiteC6-- | Cierra el multipart. |
| Punto solo | Termina DATA en SMTP; no forma parte del correo. |

Conservar las líneas vacías entre encabezados y cuerpo, tanto a nivel general como dentro de cada parte.

El multipart completo no se codifica en base64: sus delimitadores deben seguir siendo reconocibles. La codificación se declara por parte.

Que el HTML declare UTF-8 no exige usar caracteres no ASCII. En este caso todo su contenido es ASCII, por eso 7bit es adecuado.

## 9. Aceptación SMTP

Respuesta real al punto final:

```text
250 2.0.0 Ok: queued as 8B11ED5E69
```

El servidor aceptó el mensaje. El identificador 8B11ED5E69 es de cola y difiere del Message-ID elegido por el emisor.

Se indicó cerrar con:

```text
QUIT
```

No se pegó la respuesta exacta a QUIT en el chat. La esperada es 221 y cierre de conexión. El correo ya estaba aceptado antes del cierre.

## 10. Corrector: salida real

En bash, desde la carpeta del lab:

```bash
bash lab-correo.sh corregir C6
```

bash ejecuta el script, corregir selecciona la acción y C6 el ejercicio.

```text
== Corrección C6 (imagen dentro del HTML) ==
  corrigiendo: <63051.20261108.133057.c6@mail.protos.lab>  ·  Subject: 'Logo en el cuerpo'
  [OK] X-Parcial: LAB-C6
  [OK] Subject = Logo en el cuerpo
  [OK] Subject codificado en ASCII (encoded-word)
  [OK] From con tu cuenta ITBA (jdileomuntaner@itba.edu.ar)
  [OK] From con nombre y apellido (Jeronimo Muntaner)
  [OK] From en ASCII (si hay tildes, encoded-word)
  [OK] To: 63051@mail.protos.lab
  [OK] MIME-Version: 1.0
  [OK] Date válido
  [OK] Message-ID con formato <algo@dominio>
  [OK] Ninguna parte en quoted-printable
  [OK] Hay un multipart/related
  [!]  No hay versión de texto plano (multipart/alternative): es buena práctica incluirla.
  [OK] Hay parte HTML y parte imagen
  [OK] El HTML referencia la imagen con src="cid:..."
  [OK] Content-ID <logoC6> coincide con cid:logoC6
  [OK] La imagen es logo.png

  Resultado: 16/16 verificaciones bien.  ¡Aprobado!
```

Dos aclaraciones:

- El texto del corrector dice “Subject codificado en ASCII (encoded-word)”, pero el asunto enviado es ASCII directo. No requiere encoded-word porque no tiene caracteres no ASCII.
- La ausencia de texto plano es un aviso de buena práctica, no un fallo de esta consigna. Para incorporarlo podría usarse multipart/alternative con text/plain primero y un multipart/related que contenga HTML e imagen como alternativa más rica. Esa ampliación no se ejecutó aquí.

## 11. Verificación real por POP3

En bash:

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
1 629
2 563
3 770
4 2203
.
RETR 4
+OK 2203 octets
```

USER y PASS autentican. En este lab ambos valores son la dirección completa del buzón. LIST muestra números y tamaños en octetos. RETR 4 recupera el mensaje 4 sin borrarlo.

Los mensajes previos cambiaron de número después del borrado de la misión C4. Los números POP3 no son identificadores permanentes.

El mensaje recuperado empieza con:

```text
Return-Path: <jdileomuntaner@itba.edu.ar>
Received: from cliente.lab (localhost [127.0.0.1])
	by mx1.protos.lab with ESMTP id 8B11ED5E69
	for <63051@mail.protos.lab>; Sun, 08 Nov 2026 13:33:25 -0300
```

A continuación aparecen los mismos encabezados y el cuerpo MIME completo de la sección 7, sin el punto de DATA como contenido. La respuesta POP3 termina con su propio punto.

Se confirmó:

- Cola 8B11ED5E69 en Received, igual a la respuesta SMTP.
- Message-ID del C6 y X-Parcial: LAB-C6.
- Parte text/html con src="cid:logoC6".
- Parte image/png con Content-ID: <logoC6>.
- Base64 de la imagen incluido y cierre --limiteC6--.

Return-Path deriva del remitente del sobre. Received registra el paso por el servidor; sus líneas indentadas son continuaciones del encabezado.

POP3 devuelve el mensaje MIME sin renderizarlo. Por eso se ven HTML y base64 en netcat: un cliente de correo interpreta las partes y puede mostrar la imagen.

Para cerrar esta sesión se debe enviar:

```text
QUIT
```

Al preparar este apunte todavía no se había pegado una respuesta a ese cierre. No se usó DELE ni se solicitó borrar el correo C6.

## 12. Errores frecuentes

- Buscar logo.png mediante una ruta relativa desde otra carpeta.
- Escribir src con una ruta local que no existe en la computadora del destinatario.
- Poner cid:logoC6 en HTML y otro identificador en Content-ID.
- Usar multipart/alternative para HTML e imagen como si fueran versiones del mismo contenido.
- Pegar bytes binarios directamente en vez de su base64.
- Omitir la línea vacía antes del base64 de la imagen.
- Confundir el cierre MIME --limiteC6-- con el punto que termina DATA.
- Suponer que ver base64 en POP3 significa que el correo llegó mal: POP3 no renderiza MIME.

