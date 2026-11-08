# C10 — Quoted-printable, remitente con tildes y dot-stuffing

Práctica del 8 de noviembre de 2026. **Resultado real: 9/9 verificaciones, aprobado.**

## 1. Consigna

Enviar al buzón propio un mensaje con:

- X-Parcial: LAB-C10.
- Remitente visible: Pingüino Ñandú, usando la cuenta ITBA del usuario.
- Asunto: Prueba de codificación.
- Cuerpo en quoted-printable, con estas tres líneas:

```text
Canción de prueba: ¿cómo están?
.esta línea empieza con punto
fin
```

## 2. Datos usados

| Dato | Valor |
|---|---|
| SMTP del lab | 127.0.0.1:2525 |
| Cuenta remitente | jdileomuntaner@itba.edu.ar |
| Buzón destino | 63051@mail.protos.lab |
| Nombre visible solicitado | Pingüino Ñandú |
| Message-ID | <63051.20261108.164513.c10@mail.protos.lab> |
| Cola SMTP | 1CA9BAED51 |

## 3. ¿Qué cambia al usar quoted-printable?

Content-Transfer-Encoding indica cómo se representan los bytes del cuerpo para transportarlos. Quoted-printable y base64 permiten transportar bytes no ASCII mediante caracteres ASCII; no cifran el contenido.

| Texto original | Codificación | Representación |
|---|---|---|
| ¡Hola mundo! | base64 | wqFIb2xhIG11bmRvIQ== |
| ¡Hola mundo! | quoted-printable | =C2=A1Hola mundo! |

Base64 transforma el contenido completo. Quoted-printable conserva muchos caracteres legibles y representa otros bytes mediante =XX, con XX en hexadecimal.

Por ejemplo, ó tiene los bytes C3 B3 en UTF-8: se representa como =C3=B3. No se codifica simplemente una letra como un único número: se representan sus bytes.

| Carácter | Bytes UTF-8 | Quoted-printable |
|---|---|---|
| ó | C3 B3 | =C3=B3 |
| ¿ | C2 BF | =C2=BF |
| á | C3 A1 | =C3=A1 |
| í | C3 AD | =C3=AD |

Quoted-printable suele ser útil en texto mayormente ASCII con algunos caracteres adicionales. Base64 sirve para binarios y también texto. En C10 usamos quoted-printable porque lo pide la consigna; en ejercicios anteriores lo prohibían y elegimos base64.

El cliente que soporte ambas codificaciones muestra el mismo texto original. Cambia su representación durante el transporte.

### Encabezado y contenido deben coincidir

Escribir Content-Transfer-Encoding: quoted-printable no convierte automáticamente el texto: hay que enviar el cuerpo efectivamente codificado.

```text
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: quoted-printable
```

El lector primero decodifica quoted-printable y luego interpreta los bytes obtenidos como texto UTF-8. Content-Type y Content-Transfer-Encoding cumplen funciones distintas.

Otras reglas útiles de quoted-printable: el signo igual literal se representa como =3D; las líneas codificadas tienen un máximo de 76 caracteres y un igual al final puede indicar continuación suave, sin salto en el texto decodificado. Estas reglas adicionales no requirieron cambios en nuestro cuerpo breve.

## 4. Preparar nombre, asunto y fecha

Comandos ejecutados en bash:

```bash
echo -n 'Pingüino Ñandú' | base64
echo -n 'Prueba de codificación' | base64
date -R
```

Salidas reales:

```text
UGluZ8O8aW5vIMORYW5kw7o=
UHJ1ZWJhIGRlIGNvZGlmaWNhY2nDs24=
Sun, 08 Nov 2026 16:45:13 -0300
```

- echo -n imprime sin agregar un salto final.
- Las comillas simples conservan el texto literal.
- La tubería pasa los bytes a base64.
- date -R produce una fecha apta para Date con zona horaria.

Estos base64 son para encoded-words de los encabezados. El cuerpo usa quoted-printable de manera independiente.

```text
From: =?UTF-8?B?UGluZ8O8aW5vIMORYW5kw7o=?= <jdileomuntaner@itba.edu.ar>
Subject: =?UTF-8?B?UHJ1ZWJhIGRlIGNvZGlmaWNhY2nDs24=?=
```

UTF-8 indica el juego de caracteres, B base64 y ?= cierra el encoded-word. Se codifica el nombre visible, conservando la dirección fuera del bloque. El remitente del sobre SMTP seguirá siendo la cuenta ITBA.

## 5. Abrir SMTP y declarar el sobre

En bash:

```bash
nc -C 127.0.0.1 2525
```

nc abre TCP; -C usa CRLF en la variante de netcat de esta práctica. El puerto SMTP del lab es 2525; el estándar para recepción SMTP es 25.

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

Las líneas numéricas son respuestas del servidor. Se espera cada respuesta positiva antes de avanzar.

- 220: servicio listo.
- EHLO: presenta al cliente y descubre extensiones. El guion en 250- indica continuación; el espacio indica la última línea.
- MAIL FROM: remitente del sobre.
- RCPT TO: destino real.
- DATA: solicita transmitir el contenido.
- 354: autoriza a escribirlo; no confirma todavía la aceptación final.

From y To dentro del mensaje son encabezados visibles y no sustituyen al sobre SMTP.

## 6. Mensaje completo enviado

Después del 354 se envió:

```text
Date: Sun, 08 Nov 2026 16:45:13 -0300
Message-ID: <63051.20261108.164513.c10@mail.protos.lab>
From: =?UTF-8?B?UGluZ8O8aW5vIMORYW5kw7o=?= <jdileomuntaner@itba.edu.ar>
To: <63051@mail.protos.lab>
X-Parcial: LAB-C10
Subject: =?UTF-8?B?UHJ1ZWJhIGRlIGNvZGlmaWNhY2nDs24=?=
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: quoted-printable

Canci=C3=B3n de prueba: =C2=BFc=C3=B3mo est=C3=A1n?
..esta l=C3=ADnea empieza con punto
fin
.
```

Para otro envío, obtener una fecha nueva y usar otro Message-ID.

| Campo o elemento | Función |
|---|---|
| Date | Fecha de creación con zona horaria. |
| Message-ID | Identificador del mensaje. |
| From | Nombre solicitado mediante encoded-word y cuenta ITBA visible. |
| To | Destinatario visible. |
| X-Parcial | Marca exacta de C10. |
| Subject | Asunto con encoded-word. |
| MIME-Version: 1.0 | Declara uso de MIME. |
| Content-Type | Texto plano en UTF-8. |
| Content-Transfer-Encoding | El cuerpo está en quoted-printable. |
| Línea vacía | Separa encabezados del cuerpo. |
| Punto solo | Termina DATA, sin pertenecer al cuerpo. |

No hace falta multipart: hay una única parte de texto.

## 7. ¿Por qué escribimos dos puntos en ..esta?

Esto es dot-stuffing de SMTP, no quoted-printable.

Durante DATA, una línea con un punto solo termina el mensaje. Para permitir líneas de contenido que empiezan con punto, SMTP exige agregar un punto extra al principio de esas líneas. El servidor quita el extra al recibirlas.

| Momento | Línea |
|---|---|
| Texto original | .esta línea empieza con punto |
| Cuerpo MIME en quoted-printable | .esta l=C3=ADnea empieza con punto |
| Envío manual por SMTP DATA | ..esta l=C3=ADnea empieza con punto |
| Después de retirar dot-stuffing | .esta l=C3=ADnea empieza con punto |
| Texto mostrado al decodificar MIME | .esta línea empieza con punto |

Netcat es una conexión de bajo nivel: en esta práctica agregamos nosotros el punto extra. Un cliente SMTP que construye la transacción puede encargarse automáticamente de ello.

La línea final con un punto solo cumple otra función: cerrar DATA. No debe duplicarse si lo que queremos es terminar el mensaje.

## 8. Aceptación y cierre

Respuesta real:

```text
250 2.0.0 Ok: queued as 1CA9BAED51
```

Ese 250 confirma que el servidor aceptó el mensaje. 1CA9BAED51 es un identificador de cola y difiere del Message-ID.

Se indicó cerrar con QUIT; su respuesta exacta no se pegó en el chat. Se espera 221 y cierre. QUIT no es el comando que envía el correo: ya estaba aceptado tras el punto.

## 9. Corrector y resultado real

En bash, desde la carpeta del laboratorio:

```bash
bash lab-correo.sh corregir C10
```

bash ejecuta el script, corregir elige la acción y C10 selecciona el ejercicio.

Salida real:

```text
== Corrección C10 (quoted-printable y tildes en el remitente) ==
  corrigiendo: <63051.20261108.164513.c10@mail.protos.lab>  ·  Subject: 'Prueba de codificación'
  [OK] X-Parcial: LAB-C10
  [OK] Nombre del remitente = Pingüino Ñandú
  [OK] Dirección del From = tu cuenta ITBA
  [OK] From codificado (encoded-word)
  [OK] Subject = Prueba de codificación
  [OK] Subject codificado
  [OK] Parte text/plain
  [OK] Content-Transfer-Encoding: quoted-printable
  [OK] El texto llegó exacto (incluida la línea con punto)

  Resultado: 9/9 verificaciones bien.  ¡Aprobado!
```

No se realizó una lectura POP3 adicional en este tramo. El corrector confirmó el texto exacto y la línea con punto.

## 10. Qué recordar

1. La codificación de los encabezados es independiente de la del cuerpo.
2. Encoded-word permite nombres y asuntos con caracteres no ASCII.
3. Quoted-printable representa bytes con =XX y deja gran parte del texto legible.
4. Declarar la codificación no transforma automáticamente el contenido.
5. Dot-stuffing es una regla de SMTP DATA, independiente de MIME.
6. Si una línea transmitida empieza con punto, en esta conexión manual agregamos otro delante.
7. Esperar el 250 final y comprobar el resultado con el corrector.
