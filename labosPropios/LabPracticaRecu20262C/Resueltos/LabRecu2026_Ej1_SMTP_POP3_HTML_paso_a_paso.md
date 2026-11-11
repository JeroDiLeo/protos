# LabRecu2026 · Ejercicio 1 · Correo en negrita por SMTP y POP3

## Qué pide la consigna

Enviar a `62815@mail.protos.foo` un correo con `X-Parcial: 2026/2R`, asunto **¡Buenos días!**, tu nombre y cuenta del ITBA como remitente, y el cuerpo **¡Hola mundo!** en negrita. El mensaje debe poder leerse en clientes sin soporte para *quoted-printable*. La entrega se verifica por POP3. `62815` es el legajo de práctica que fija este lab.

## 1. Averiguar a qué servidor se envía el correo

```text
root@alumno:~# dig MX mail.protos.foo +noall +answer
mail.protos.foo.     300 IN MX 10 mx1.protos.foo.
mail.protos.foo.     300 IN MX 20 mx2.protos.foo.
```

Consultamos el dominio que viene después de `@` en el destinatario. El tipo `MX` devuelve los nombres de los servidores de correo. `+noall +answer` deja visible solo la respuesta. El valor `300` es el TTL en segundos. Elegimos `mx1.protos.foo` porque la preferencia `10` es menor que `20`.

## 2. Preparar la fecha y los textos que llevan caracteres UTF-8

```bash
date -R
echo -n 'Jerónimo Di Leo Muntaner' | base64
echo -n '¡Buenos días!' | base64
echo -n '¡Hola mundo!' | base64
echo -n '<b>¡Hola mundo!</b>' | base64
```

`date -R` genera la fecha con el formato que usamos en el encabezado `Date`. `echo -n` evita incluir un salto de línea en el texto que entra a `base64`. Para la negrita codificamos todo el fragmento HTML, incluidas las etiquetas. Estos son los valores usados:

| Dato | Resultado |
|---|---|
| Fecha de la sesión | `Wed, 11 Nov 2026 19:40:31 +0000` |
| Nombre visible | `SmVyw7NuaW1vIERpIExlbyBNdW50YW5lcg==` |
| Asunto | `wqFCdWVub3MgZMOtYXMh` |
| Cuerpo en texto plano | `wqFIb2xhIG11bmRvIQ==` |
| Cuerpo en HTML | `PGI+wqFIb2xhIG11bmRvITwvYj4=` |

**Cuándo usar Base64.** Es una codificación reversible que representa los bytes con caracteres ASCII. Cualquiera puede decodificarla sin una clave. En este cuerpo, `¡` aporta bytes UTF-8 fuera de ASCII. Base64 permite transportarlos y cumple la compatibilidad pedida con clientes que carecen de soporte para *quoted-printable*. Un cuerpo simple como `Hola mundo!` puede viajar como `7bit` si cumple sus restricciones. Si el transporte admite y negocia `8BITMIME`, también existe la opción de enviar un cuerpo `8bit`. Para este lab usamos Base64 y declaramos la codificación explícitamente. [MIME y codificaciones de transferencia](https://www.rfc-editor.org/rfc/rfc2045.html) · [Extensión SMTP 8BITMIME](https://www.rfc-editor.org/rfc/rfc6152.html)

**Cómo se distingue del Base64 de los encabezados.** Para el nombre visible y el asunto usamos `=?UTF-8?B?…?=`. El `UTF-8` dice cómo interpretar los bytes y la `B` indica Base64 en ese fragmento de encabezado. En el cuerpo, esa función la cumple `Content-Transfer-Encoding: base64`. [Encoded-words en encabezados](https://www.rfc-editor.org/rfc/rfc2047.html)

## 3. Abrir SMTP y declarar el sobre

Salida real hasta el comienzo de `DATA`:

```text
root@alumno:~# nc -C mx1.protos.foo 25
220 mail.protos.foo ESMTP LabProtos ready
EHLO cliente.lab
250-mail.protos.foo saluda a cliente.lab
250-PIPELINING
250 8BITMIME
MAIL FROM:<jdileomuntaner@itba.edu.ar>
250 OK
RCPT TO:<62815@mail.protos.foo>
250 OK
DATA
354 Start mail input; end with <CRLF>.<CRLF>
```

| Línea | Por qué la escribimos |
|---|---|
| `nc -C mx1.protos.foo 25` | Abre una conexión TCP al MX preferido por el puerto SMTP. En la versión de netcat del lab, `-C` usa terminaciones de línea CRLF. |
| `EHLO cliente.lab` | Presenta el nombre de práctica del cliente. El servidor devuelve las extensiones que ofrece. |
| `MAIL FROM:<jdileomuntaner@itba.edu.ar>` | Declara la dirección del remitente del sobre. SMTP puede usarla para avisos de entrega fallida. |
| `RCPT TO:<62815@mail.protos.foo>` | Declara el destinatario del sobre. Es la dirección del buzón donde tiene que quedar el correo. |
| `DATA` | Pide permiso para enviar los encabezados y el cuerpo. La respuesta `354` habilita ese envío. |

## 4. Escribir el mensaje después de DATA

Este fue el mensaje multipart enviado y recuperado:

```text
Date: Wed, 11 Nov 2026 19:40:31 +0000
Message-ID: <62815.20261111.194031.ej1@cliente.lab>
From: =?UTF-8?B?SmVyw7NuaW1vIERpIExlbyBNdW50YW5lcg==?= <jdileomuntaner@itba.edu.ar>
To: <62815@mail.protos.foo>
Subject: =?UTF-8?B?wqFCdWVub3MgZMOtYXMh?=
X-Parcial: 2026/2R
MIME-Version: 1.0
Content-Type: multipart/alternative; boundary="limiteRecu2R"

--limiteRecu2R
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: base64

wqFIb2xhIG11bmRvIQ==
--limiteRecu2R
Content-Type: text/html; charset=UTF-8
Content-Transfer-Encoding: base64

PGI+wqFIb2xhIG11bmRvITwvYj4=
--limiteRecu2R--
.
```

| Línea o bloque | Qué hace y de dónde sale |
|---|---|
| `Date` | Declara cuándo se preparó el correo. Usamos la salida de `date -R`. |
| `Message-ID` | Identifica el mensaje. Elegimos un valor con el legajo, la fecha, la hora y una etiqueta para reconocer el envío. |
| `From` | Identifica al remitente visible, como pide la consigna. El nombre va como *encoded-word* para conservar la tilde y la dirección ITBA queda entre `< >`. |
| `To` | Identifica el destinatario visible. En este correo coincide con el destinatario del sobre declarado en `RCPT TO`. |
| `Subject` | Muestra **¡Buenos días!** una vez decodificado. El *encoded-word* conserva el signo de apertura y la tilde. |
| `X-Parcial: 2026/2R` | Es el encabezado personalizado que pide el enunciado. |
| `MIME-Version: 1.0` | Indica que el mensaje usa MIME para describir y codificar su contenido. |
| `Content-Type: multipart/alternative; boundary="limiteRecu2R"` | Declara dos versiones del mismo mensaje. El `boundary` fija el separador que el lector MIME busca en el cuerpo. |
| Línea en blanco general | Separa los encabezados del mensaje del cuerpo multipart. |
| `--limiteRecu2R` | Abre una parte. El nombre elegido en el encabezado lleva dos guiones por delante en cada delimitador. |
| `Content-Type: text/plain; charset=UTF-8` | Describe la versión plana. La ofrecemos primero como alternativa. |
| `Content-Type: text/html; charset=UTF-8` | Describe la versión con formato. El cliente puede renderizar la negrita de `<b>`. |
| `Content-Transfer-Encoding: base64` | En cada parte indica cómo recuperar sus bytes antes de interpretar el contenido según su tipo y charset. |
| Línea en blanco de cada parte | Separa los encabezados de esa parte de su Base64. |
| `--limiteRecu2R--` | Cierra el multipart. Los dos guiones finales marcan el último delimitador. |
| Punto en una línea propia | Termina `DATA` en SMTP. A partir de ahí esperamos que el servidor acepte el mensaje. |

En la sesión real, el servidor respondió `250 OK message queued` después del punto. Escribimos `QUIT` y devolvió `221 mail.protos.foo Service closing transmission channel`. [Comandos SMTP](https://www.rfc-editor.org/rfc/rfc5321.html) · [Estructura multipart](https://www.rfc-editor.org/rfc/rfc2046.html#section-5.1)

## 5. Comprobar la recepción por POP3

La consigna indica el nombre `mail.protos.foo` para POP3. En esta ejecución también respondió `mx1.protos.foo` en el puerto `110`. Este fue el extracto de la sesión real:

```text
root@alumno:~# nc -C mx1.protos.foo 110
+OK LabProtos POP3 server ready
USER 62815@mail.protos.foo
+OK usuario aceptado
PASS 62815@mail.protos.foo
+OK logueado
LIST
+OK 1 messages
1 609
.
RETR 1
+OK 609 octets
Date: Wed, 11 Nov 2026 19:40:31 +0000
Message-ID: <62815.20261111.194031.ej1@cliente.lab>
```

`USER` elige el buzón y `PASS` usa la contraseña de práctica, que es la misma dirección. `LIST` mostró un mensaje de 609 octetos. `RETR 1` devolvió el contenido completo con el mismo `Message-ID` y las dos partes del paso anterior. En POP3, el servidor pone un punto en una línea propia para cerrar la respuesta de varias líneas.

Copiamos el Base64 de la parte `text/html` y lo verificamos desde la shell:

```text
root@alumno:~# echo 'PGI+wqFIb2xhIG11bmRvITwvYj4=' | base64 -d
echo
<b>¡Hola mundo!</b>
```

`-d` decodifica Base64. El segundo `echo` agrega un salto de línea antes del prompt.

## 6. Comprobar el resultado visualmente

### Ver el correo en Thunderbird

1. De la salida de `RETR 1`, copiá desde `Date:` hasta `--limiteRecu2R--` inclusive. Conservá las líneas en blanco y los encabezados de cada parte.
2. Pegá ese bloque en un editor de texto y guardalo como `recu-negrita.eml`. Ese recorte contiene el correo y deja afuera el saludo POP3 y su punto de cierre.
3. En Thunderbird abrí **Archivo → Abrir → Mensaje guardado** y elegí el archivo. Si se muestra la alternativa de texto plano, seleccioná **Ver → Cuerpo del mensaje como → HTML original**.

Así podés revisar el asunto, el remitente y el cuerpo en un cliente gráfico usando el mensaje recuperado. El archivo local se puede abrir directamente. [Abrir un mensaje guardado en Thunderbird](https://support.mozilla.org/en-US/questions/1257035) · [Mostrar el cuerpo como HTML](https://support.mozilla.org/en-US/questions/1442320)

### Probar la parte HTML en el navegador

Ejecutá esto en una terminal del escritorio Linux. El primer comando crea un archivo con UTF-8 explícito y un texto normal para comparar. El segundo agrega el HTML decodificado. `xdg-open` abre el archivo con la aplicación asociada.

```bash
echo '<meta charset="utf-8"><p>Texto normal para comparar:</p>' > /tmp/recu-negrita.html
echo 'PGI+wqFIb2xhIG11bmRvITwvYj4=' | base64 -d >> /tmp/recu-negrita.html
xdg-open /tmp/recu-negrita.html
```

El navegador debería mostrar **¡Hola mundo!** en negrita. Si te piden otro formato, primero escribí y probá el fragmento y después codificalo. Podés usar `<i>¡Hola mundo!</i>` para cursiva o `<span style="text-decoration: underline">¡Hola mundo!</span>` para subrayado. Para enviarlo, el tipo de la parte sigue siendo `text/html; charset=UTF-8` y la codificación de transferencia puede seguir siendo Base64. [Etiqueta b en HTML](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/b) · [Subrayado con CSS](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/u)

## 7. Cuándo hace falta boundary y qué conviene para el corrector

El parámetro `boundary` es obligatorio para `multipart/alternative`. El cliente MIME lo usa para ubicar las partes. En una versión de **una sola parte HTML**, los encabezados de arriba describen directamente el cuerpo y la línea en blanco marca dónde empieza. Para el enunciado, una sola parte HTML también permite expresar la negrita. [Sintaxis multipart en MIME](https://www.rfc-editor.org/rfc/rfc2046.html#section-5.1)

El corrector de este lab intenta pasar todo lo que sigue a los encabezados generales a `base64 -d` de una sola vez. En el multipart, se encuentra primero con el delimitador. Reprodujimos esa lógica con ambos formatos. Un lector MIME pudo obtener la negrita en los dos casos y la lógica del corrector la recuperó con la versión de una sola parte. Por eso, si vas a usar `make corregir ej=1`, podés enviar este mensaje después del `354`:

```text
Date: Wed, 11 Nov 2026 19:40:31 +0000
Message-ID: <62815.20261111.194031.ej1-html@cliente.lab>
From: =?UTF-8?B?SmVyw7NuaW1vIERpIExlbyBNdW50YW5lcg==?= <jdileomuntaner@itba.edu.ar>
To: <62815@mail.protos.foo>
Subject: =?UTF-8?B?wqFCdWVub3MgZMOtYXMh?=
X-Parcial: 2026/2R
MIME-Version: 1.0
Content-Type: text/html; charset=UTF-8
Content-Transfer-Encoding: base64

PGI+wqFIb2xhIG11bmRvITwvYj4=
.
```

El `Message-ID` propio permite distinguir el segundo envío. El corrector toma el correo más reciente del buzón de práctica. La prueba documentada en la sesión real es el envío multipart, su recuperación por POP3 y la decodificación del HTML. La variante de una sola parte se comprobó con la lógica de decodificación del corrector. Queda pendiente la ejecución de `make corregir ej=1` contra ese segundo envío.
