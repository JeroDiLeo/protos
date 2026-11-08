# C5 — Imagen adjunta: envío SMTP, lectura POP3 y extracción

Práctica del 8 de noviembre de 2026. **Resultado real: 20/20 verificaciones, aprobado.** El PNG extraído también se comparó con el original mediante cmp, sin diferencias.

## 1. Consigna

Enviar al buzón propio un correo con:

1. X-Parcial: LAB-C5.
2. Asunto: Logo del laboratorio.
3. Cuerpo de texto: Adjunto el logo del laboratorio.
4. La imagen ~/lab-correo/adjuntos/logo.png como adjunto descargable.
5. Verificar por POP3 que la parte de la imagen llegó y mostrar cómo extraerla.

## 2. Datos del entorno

| Dato | Valor |
|---|---|
| Carpeta de trabajo | ~/Documents/protoslaboratorios/labcorreo |
| Archivo original | ~/lab-correo/adjuntos/logo.png |
| SMTP | 127.0.0.1:2525 |
| POP3 | 127.0.0.1:2110 |
| Nombre del remitente | Jeronimo Muntaner |
| Cuenta ITBA | jdileomuntaner@itba.edu.ar |
| Buzón propio | 63051@mail.protos.lab |
| Usuario y contraseña POP3 | Ambos 63051@mail.protos.lab en este lab |
| Message-ID enviado | <63051.20261108.134554.c5@mail.protos.lab> |
| Identificador de cola | 6916551095 |
| Archivo extraído | logo_recibido.png, dentro de la carpeta de trabajo |

## 3. Elegir la estructura del mensaje

Usamos multipart/mixed para agrupar una parte de texto y un archivo adjunto.

| Campo | Función |
|---|---|
| Content-Type: multipart/mixed | Declara que el cuerpo contiene varias partes independientes. |
| boundary="limiteC5" | Define el separador literal entre las partes. |
| --limiteC5 | Inicia una parte. |
| Content-Type: text/plain | La primera parte es el texto del correo. |
| Content-Type: image/png | La segunda parte es una imagen PNG. |
| Content-Disposition: attachment | Indica que se presenta como adjunto. |
| filename="logo.png" | Proporciona el nombre del archivo adjunto. |
| --limiteC5-- | Cierra el conjunto multipart. |

No necesitamos cid ni Content-ID: el texto no hace referencia a una imagen colocada dentro del HTML.

Comparación de las variantes practicadas:

| Tipo | Uso |
|---|---|
| multipart/alternative (C3) | Versiones del mismo contenido, por ejemplo texto plano y HTML. |
| multipart/related (C6) | HTML y recursos que utiliza mediante cid. |
| multipart/mixed (C5) | Cuerpo y archivos adjuntos independientes. |

## 4. Preparar fecha e imagen

Se confirmó que el archivo existía en la ruta del laboratorio. Se ejecutó en bash:

```bash
date -R
base64 ~/lab-correo/adjuntos/logo.png
```

Fecha real:

```text
Sun, 08 Nov 2026 13:45:54 -0300
```

La salida base64 completa está incluida en el mensaje de la sección 6.

- date -R genera una fecha apta para Date, incluyendo zona horaria.
- base64 lee los bytes binarios del archivo y los representa como ASCII; no cifra ni modifica el original.
- ~ representa el directorio personal del usuario.

## 5. Abrir SMTP y declarar el sobre

En bash:

```bash
nc -C 127.0.0.1 2525
```

nc establece una conexión TCP; -C usa CRLF en la variante de netcat de esta práctica. 2525 es el puerto SMTP del lab; el estándar de recepción SMTP es 25.

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
RCPT TO:<63051@mail.protos.lab>
250 2.1.5 Ok
DATA
354 End data with <CR><LF>.<CR><LF>
```

Las líneas 220, 250 y 354 son respuestas, no comandos para copiar.

EHLO presenta al cliente y descubre extensiones. El guion tras 250 indica que siguen más líneas; el espacio indica la última.

MAIL FROM declara el remitente del sobre y RCPT TO determina la entrega real. Los encabezados From y To son parte del mensaje visible y no sustituyen estos comandos.

Cada respuesta positiva permitió continuar. DATA solicita transmitir el mensaje y 354 autoriza a escribirlo; la aceptación final llega después del punto.

## 6. Mensaje completo enviado

Después de recibir 354 se pegó:

```text
Date: Sun, 08 Nov 2026 13:45:54 -0300
Message-ID: <63051.20261108.134554.c5@mail.protos.lab>
From: Jeronimo Muntaner <jdileomuntaner@itba.edu.ar>
To: <63051@mail.protos.lab>
X-Parcial: LAB-C5
Subject: Logo del laboratorio
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="limiteC5"

--limiteC5
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 7bit

Adjunto el logo del laboratorio.
--limiteC5
Content-Type: image/png
Content-Transfer-Encoding: base64
Content-Disposition: attachment; filename="logo.png"

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
--limiteC5--
.
```

Para repetir el envío, obtener fecha actual y un Message-ID nuevo.

### Cómo leerlo

El Content-Type general describe todo el cuerpo como multipart/mixed. Los Content-Type interiores describen cada pieza, por lo que no se contradicen.

La línea vacía después de los encabezados generales separa esos encabezados del cuerpo multipart. Dentro de cada parte, otra línea vacía separa sus encabezados del contenido. Hay que conservarlas.

MIME-Version: 1.0 declara el uso de MIME y va una vez en los encabezados generales.

El texto es ASCII, aunque declare charset=UTF-8, y por eso usa 7bit. El PNG es binario y se transporta en base64. La codificación se aplica por parte; no se codifica todo el multipart, porque sus separadores deben permanecer reconocibles.

El asunto y el nombre usados son ASCII y no requieren encoded-word.

El cierre --limiteC5-- termina el multipart. El punto solo termina DATA en SMTP. Son delimitadores de niveles diferentes.

## 7. Aceptación SMTP

Respuesta real al punto final:

```text
250 2.0.0 Ok: queued as 6916551095
```

Este 250 confirma la aceptación del mensaje. 6916551095 es el identificador de cola del servidor, distinto del Message-ID elegido por el emisor.

Se indicó cerrar SMTP con QUIT; no se pegó su respuesta exacta. La esperada es 221 y cierre. QUIT no es el comando que envía el mensaje: el servidor ya lo aceptó al finalizar DATA.

## 8. Conectarse por POP3 y encontrar el correo

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
+OK Logged in. 5 messages
LISST
-ERR Unknown command
LIST
+OK 5 messages:
1 629
2 563
3 770
4 2203
5 2116
.
```

USER identifica el buzón y PASS autentica. La contraseña igual al usuario es una configuración de este lab.

LISST fue un error de escritura. El servidor respondió -ERR Unknown command y se corrigió con LIST sin necesidad de reiniciar la sesión.

LIST muestra número y tamaño en octetos. El punto cierra la respuesta multilínea. El mensaje 5 era candidato por ser el último; su identidad se confirmó recuperándolo.

## 9. Recuperar el mensaje 5

Se ejecutó:

```text
RETR 5
```

Inicio real de la respuesta:

```text
+OK 2116 octets
Return-Path: <jdileomuntaner@itba.edu.ar>
Received: from cliente.lab (localhost [127.0.0.1])
	by mx1.protos.lab with ESMTP id 6916551095
	for <63051@mail.protos.lab>; Sun, 08 Nov 2026 13:48:59 -0300
```

A continuación se recibieron todos los encabezados y el contenido MIME de la sección 6, con el mismo base64. La respuesta terminó con el punto propio de POP3.

Se confirmó la identidad mediante:

- Message-ID: <63051.20261108.134554.c5@mail.protos.lab>.
- X-Parcial: LAB-C5.
- Identificador de cola 6916551095 en Received.
- Parte image/png, base64, con Content-Disposition: attachment; filename="logo.png".

Return-Path deriva del remitente del sobre y Received registra el paso por el servidor. Las líneas indentadas continúan el mismo encabezado.

RETR recupera sin borrar ni decodificar MIME. Los números de mensaje pueden cambiar entre sesiones; identificarlos por sus encabezados.

Se indicó cerrar POP3 con QUIT antes de volver a bash. No se pegó la respuesta exacta al cierre. No se solicitó DELE ni borrar el correo C5.

## 10. Extraer el adjunto con echo

Se propusieron formas de entrada con EOF y Ctrl+D, pero el usuario prefirió echo con una tubería, como en los ejercicios anteriores. El comando realmente ejecutado fue:

```bash
echo 'iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAIAAABvFaqvAAADnUlEQVR4nBXUqxpFERSF0Z1lWZZl
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
jgAAAABJRU5ErkJggg==' | base64 -d > logo_recibido.png
```

- Las comillas simples conservan el texto literal, incluidos sus saltos de línea.
- echo entrega el base64 al siguiente comando mediante la tubería.
- base64 -d decodifica; los saltos de línea de la representación base64 son admitidos.
- > guarda los bytes resultantes en logo_recibido.png, en la carpeta actual. Si el archivo ya existe, lo sobrescribe.
- Se copia solo el base64 del adjunto: no los encabezados, el boundary ni el punto POP3.

El comando terminó sin mensajes y volvió al prompt porque la salida fue al archivo, no a la pantalla. El Ctrl+C que se pulsó después de volver al prompt no afectó al archivo ya creado.

## 11. Identificar y comparar el archivo

Comandos ejecutados:

```bash
file logo_recibido.png
cmp ~/lab-correo/adjuntos/logo.png logo_recibido.png
```

Salida real de file:

```text
logo_recibido.png: PNG image data, 24 x 24, 8-bit/color RGB, non-interlaced
```

cmp no mostró ninguna salida. Los archivos eran idénticos byte por byte. Esto comprueba que la codificación, el transporte y la extracción conservaron el original.

file identifica el tipo del archivo; cmp compara directamente su contenido. No son equivalentes: reconocer un PNG no prueba por sí solo que sea idéntico al original.

## 12. Corrector: salida real

Desde la carpeta del lab:

```bash
bash lab-correo.sh corregir C5
```

bash ejecuta el script, corregir elige la acción y C5 selecciona el ejercicio.

```text
== Corrección C5 (imagen adjunta) ==
  corrigiendo: <63051.20261108.134554.c5@mail.protos.lab>  ·  Subject: 'Logo del laboratorio'
  [OK] X-Parcial: LAB-C5
  [OK] Subject = Logo del laboratorio
  [OK] Subject codificado en ASCII (encoded-word)
  [OK] From con tu cuenta ITBA (jdileomuntaner@itba.edu.ar)
  [OK] From con nombre y apellido (Jeronimo Muntaner)
  [OK] From en ASCII (si hay tildes, encoded-word)
  [OK] To: 63051@mail.protos.lab
  [OK] MIME-Version: 1.0
  [OK] Date válido
  [OK] Message-ID con formato <algo@dominio>
  [OK] Ninguna parte en quoted-printable
  [OK] Estructura multipart/mixed
  [OK] Hay una parte text/plain
  [OK] Texto = Adjunto el logo del laboratorio.
  [OK] Hay una parte image/*
  [OK] Content-Type: image/png
  [OK] Imagen en base64
  [OK] Content-Disposition: attachment
  [OK] filename="logo.png"
  [OK] La imagen decodificada es idéntica a logo.png

  Resultado: 20/20 verificaciones bien.  ¡Aprobado!
```

La etiqueta del corrector menciona encoded-word, pero nuestro Subject es ASCII directo y no necesita esa envoltura.

## 13. Errores frecuentes

- Usar multipart/related cuando se pide cuerpo más adjunto independiente.
- Omitir attachment o el nombre de archivo solicitado.
- Copiar una ruta de la computadora en lugar de incluir los bytes del archivo.
- Omitir líneas vacías entre encabezados de parte y contenido.
- Confundir el cierre multipart con el punto de SMTP.
- Decodificar también los separadores en lugar de solo el base64.
- Pensar que la ausencia de salida significa que no se creó el archivo: la redirección > lo guarda.
- Identificar un correo únicamente por su número POP3 sin confirmar sus encabezados.
