# C8 — Descubrir el servidor por MX y entregar por SMTP

Práctica del 8 de noviembre de 2026. **Resultado real: 13/13 verificaciones, aprobado.**

## 1. Consigna

Entregar un correo a `ventas@empresa.lab`, con `X-Parcial: LAB-C8` y asunto `Pedido de presupuesto`. El dominio `empresa.lab` no tiene registro A según la consigna: hay que descubrir el servidor de correo mediante MX y consultar su dirección.

## 2. Consultar el MX

Comando ejecutado en bash:

```bash
dig @127.0.0.1 -p 5361 MX empresa.lab
```

| Parámetro | Función |
|---|---|
| dig | Consulta DNS. |
| @127.0.0.1 | Servidor DNS al que se pregunta. |
| -p 5361 | Puerto DNS indicado por el laboratorio. |
| MX | Tipo de registro solicitado: servidores que reciben correo. |
| empresa.lab | Dominio destinatario. |

Respuesta real relevante:

```text
status: NOERROR
flags: qr aa rd
empresa.lab. 300 IN MX 10 mx.empresa.lab.
empresa.lab. 300 IN MX 20 mx-backup.empresa.lab.
WARNING: recursion requested but not available
```

Se elige primero el MX con menor número: prioridad 10, `mx.empresa.lab`. El de prioridad 20 es una alternativa si el preferido no permite la entrega. El 300 es el TTL del registro en segundos.

NOERROR indica que no hubo error DNS. `aa` indica respuesta autoritativa. La advertencia señala que se pidió recursión y el servidor no la ofrece; no impidió obtener estos registros propios del lab.

## 3. Obtener la IP del MX elegido

```bash
dig @127.0.0.1 -p 5361 A mx.empresa.lab
```

Respuesta real:

```text
mx.empresa.lab. 300 IN A 127.0.0.3
```

MX proporciona el nombre del servidor; A proporciona su dirección IPv4. El destinatario sigue siendo `ventas@empresa.lab`, no una dirección con el dominio del MX.

### ¿Por qué no conectar directamente con el nombre?

Sería válido usar `nc -C mx.empresa.lab 2525` si el sistema pudiera resolver ese nombre a la IP correcta. Pero `dig @127.0.0.1 -p 5361` consulta explícitamente al DNS del lab: no configura la resolución de nombres del sistema ni garantiza que nc use ese DNS. Usar la IP obtenida evita esa dependencia.

### ¿De dónde salen los puertos?

Los puertos del lab se conocen por su configuración y consignas; no se deducen de las IP ni del MX.

| Servicio | Puerto estándar relevante | Puerto del lab |
|---|---:|---:|
| DNS | 53 | 5361 |
| SMTP para entrega al servidor destinatario | 25 | 2525 |
| POP3 sin TLS implícito | 110 | 2110 |

El MX no contiene el puerto. En una entrega SMTP normal se usa 25; aquí se indicó 2525.

## 4. Preparar la fecha

En otra terminal se ejecutó:

```bash
date -R
```

Salida real:

```text
Sun, 08 Nov 2026 16:25:11 -0300
```

-R produce una fecha apta para Date con zona horaria. En futuros envíos obtener una fecha nueva y usar un Message-ID nuevo.

## 5. Abrir SMTP y declarar el sobre

```bash
nc -C 127.0.0.3 2525
```

nc abre TCP y -C usa CRLF en la variante de netcat de esta práctica.

Diálogo real:

```text
220 mx.empresa.lab ESMTP LabProtos ready
EHLO cliente.lab
250-mx.empresa.lab Hello cliente.lab
250-SIZE 10240000
250-8BITMIME
250 HELP
MAIL FROM:<jdileomuntaner@itba.edu.ar>
250 2.1.0 Ok
RCPT TO:<ventas@empresa.lab>
250 2.1.5 Ok
DATA
354 End data with <CR><LF>.<CR><LF>
```

Las líneas numéricas son respuestas del servidor. Esperar cada respuesta antes de avanzar.

- 220: servicio listo. El saludo corresponde al MX esperado.
- EHLO: presenta al cliente y descubre extensiones. 250- indica continuación; 250 con espacio es la última línea.
- MAIL FROM: remitente del sobre.
- RCPT TO: destino real de entrega. No se reemplaza empresa.lab por el nombre del MX.
- DATA: solicita transmitir el mensaje.
- 354: autoriza a escribir el mensaje; aún falta la aceptación final.

## 6. Mensaje completo enviado

Después del 354:

```text
Date: Sun, 08 Nov 2026 16:25:11 -0300
Message-ID: <63051.20261108.162511.c8@mail.protos.lab>
From: Jeronimo Muntaner <jdileomuntaner@itba.edu.ar>
To: <ventas@empresa.lab>
X-Parcial: LAB-C8
Subject: Pedido de presupuesto
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 7bit

Solicito un presupuesto para sus servicios.
.
```

Date y Message-ID identifican fecha y mensaje. From y To son encabezados visibles, diferentes del sobre SMTP. X-Parcial marca el ejercicio.

MIME-Version declara MIME. Content-Type indica texto plano y UTF-8. La línea vacía separa encabezados y cuerpo. El punto solo termina DATA y no pertenece al texto entregado.

No necesitamos multipart porque hay una sola parte de texto. El asunto y el nombre son ASCII y no necesitan encoded-word.

## 7. ¿Por qué Content-Transfer-Encoding: 7bit?

Indica cómo está representado el cuerpo para transportarlo. Aquí el texto usa únicamente ASCII y puede enviarse directamente, respetando los límites de línea del formato. Declarar charset=UTF-8 es compatible con un texto que solo contiene ASCII.

| Valor | Uso |
|---|---|
| 7bit | Contenido ASCII directo, con límites de línea y formato adecuados. |
| base64 | Representa bytes mediante ASCII; útil para binarios y también texto. |
| quoted-printable | Conserva mucho texto legible y representa ciertos bytes como =XX. |
| 8bit | Permite bytes no ASCII directos; por SMTP requiere soporte y negociación de 8BITMIME. |

También podríamos codificar este texto en base64, pero entonces habría que cambiar tanto el encabezado como la representación efectiva del cuerpo. Escribir base64 en el encabezado no codifica automáticamente nada.

Con base64 y charset=UTF-8, el lector primero decodifica base64 y luego interpreta los bytes como UTF-8. Son funciones diferentes.

## 8. Aceptación y cierre reales

```text
250 2.0.0 Ok: queued as 5E56DF1947
QUIT
221 2.0.0 Bye
```

El 250 posterior al punto confirma la aceptación. 5E56DF1947 es el identificador de cola, distinto del Message-ID. QUIT cierra ordenadamente la sesión, no es el comando que envía el correo.

## 9. Corrector

En bash, desde la carpeta del lab:

```bash
bash lab-correo.sh corregir C8
```

Salida real:

```text
== Corrección C8 (servidor descubierto por MX) ==
  [OK] ventas@empresa.lab recibió tu correo
  [OK] X-Parcial: LAB-C8
  [OK] Subject = Pedido de presupuesto
  [OK] Subject codificado en ASCII (encoded-word)
  [OK] From con tu cuenta ITBA (jdileomuntaner@itba.edu.ar)
  [OK] From con nombre y apellido (Jeronimo Muntaner)
  [OK] From en ASCII (si hay tildes, encoded-word)
  [OK] To: ventas@empresa.lab
  [OK] MIME-Version: 1.0
  [OK] Date válido
  [OK] Message-ID con formato <algo@dominio>
  [OK] Ninguna parte en quoted-printable
  [OK] Entregado por mx.empresa.lab (prioridad 10)

  Resultado: 13/13 verificaciones bien.  ¡Aprobado!
```

El asunto enviado fue ASCII directo; la etiqueta del corrector menciona encoded-word de forma genérica y no significa que lo hayamos usado.

No se realizó una lectura POP3 del buzón de ventas: el corrector confirmó su recepción y el servidor usado.

## 10. Por qué bash funciona y ./ da Permission denied

Después de aprobar se probó:

```bash
./lab-correo.sh corregir C8
```

Salida real:

```text
bash: ./lab-correo.sh: Permission denied
```

La causa habitual es que el archivo no tenga permiso de ejecución. No se inspeccionaron sus permisos en esta sesión, por lo que queda como explicación probable.

| Forma | Qué hace |
|---|---|
| bash lab-correo.sh corregir C8 | Ejecuta bash, que lee e interpreta el archivo. No exige el permiso de ejecución del script. |
| ./lab-correo.sh corregir C8 | Solicita ejecutar directamente el archivo de la carpeta actual. Necesita permiso de ejecución y un intérprete indicado correctamente en su primera línea (shebang). |

Para comprobarlo se puede usar:

```bash
ls -l lab-correo.sh
```

Si falta el permiso de ejecución para el dueño, se puede agregar con:

```bash
chmod u+x lab-correo.sh
./lab-correo.sh corregir C8
```

u+x agrega ejecución al propietario; no requiere sudo si el archivo es suyo. Estos comandos de inspección y cambio son sugeridos: no se registró su ejecución. Se puede seguir usando bash sin cambiar permisos.

Si ya hubiera permiso x y continuara el error, habría que revisar permisos de los directorios o restricciones del montaje, como noexec.

## 11. Secuencia para recordar

1. Consultar MX del dominio destinatario.
2. Elegir el de menor preferencia numérica.
3. Resolver A o AAAA de ese servidor.
4. Conectar por SMTP a su dirección y puerto correspondiente.
5. Mantener la dirección original del destinatario en RCPT TO y To.
6. Enviar el mensaje, esperar el 250 final y cerrar con QUIT.
7. Verificar la entrega con las herramientas disponibles; aquí, el corrector.
