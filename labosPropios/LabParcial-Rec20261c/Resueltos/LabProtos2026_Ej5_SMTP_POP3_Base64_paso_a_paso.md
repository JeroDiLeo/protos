# LabProtos2026 · Ejercicio 5 · Enviar por SMTP y verificar por POP3

## Qué pide el ejercicio

Enviar a `63051@mail.sebikul.com` un correo con tu nombre y dirección del ITBA como remitente, asunto **¡Buenos días!**, cuerpo **¡Hola mundo!** y encabezado `X-Parcial: 2024/2`. Debe poder leerse en clientes que no soportan quoted-printable. Al final se verifica que el mensaje quedó en el buzón usando POP3.

| Etapa | Servidor y puerto en el laboratorio | Qué queremos comprobar |
|---|---|---|
| Envío por SMTP | `mail.sebikul.com:25` | El servidor recibe el mensaje para la dirección indicada en `RCPT TO`. |
| Recuperación por POP3 | `mail.sebikul.com:110` | El mensaje está en el buzón y conserva los encabezados y el cuerpo pedidos. |

## 1. Preparar la fecha y los textos

```bash
date -R
echo -n '¡Buenos días!' | base64
echo -n '¡Hola mundo!' | base64
echo -n 'Jerónimo Di Leo Muntaner' | base64
```

`date -R` genera la fecha con el formato usado en el encabezado `Date`. `echo -n` evita agregar un salto de línea al texto que codificamos. El pipe lleva la salida de `echo` a `base64`.

| Dato | Valor usado |
|---|---|
| Fecha de la workstation | `Mon, 09 Nov 2026 21:47:27 +0000` |
| Asunto en Base64 | `wqFCdWVub3MgZMOtYXMh` |
| Cuerpo en Base64 | `wqFIb2xhIG11bmRvIQ==` |
| Nombre visible en Base64 | `SmVyw7NuaW1vIERpIExlbyBNdW50YW5lcg==` |

### Qué significa que un MUA no soporte quoted-printable

Un **MUA** (*Mail User Agent*) es el programa con el que leés y redactás el correo. Quoted-printable y Base64 son dos formas de representar los bytes del cuerpo usando ASCII. En quoted-printable, `¡Hola mundo!` se escribiría como `=C2=A1Hola mundo!`. `C2 A1` son los dos bytes UTF-8 de `¡`. Un cliente que entiende la codificación interpreta esos bytes y muestra el texto original. Uno que no la soporta podría mostrar los códigos tal cual.

En este ejercicio elegimos **Base64** para cumplir con la restricción. Las tildes siguen el mismo proceso que `¡`. Primero el texto se representa en UTF-8 y después se codifican los bytes. En el cuerpo, `charset=UTF-8` dice cómo leer los bytes recuperados y `Content-Transfer-Encoding: base64` dice cómo recuperarlos.

## 2. Abrir SMTP y declarar el sobre

Desde la workstation:

```bash
nc -C mail.sebikul.com 25
```

`nc` abre una conexión TCP a `mail.sebikul.com` en el puerto `25`, donde el lab ofrece SMTP. En la versión de `nc` instalada en la workstation, `-C` termina las líneas que escribís con CRLF (`\r\n`), el delimitador de línea de SMTP. El servidor empieza con un saludo `220`, que indica que está listo para el diálogo. A partir de ahí ingresá cada comando y esperá su respuesta antes de pasar al siguiente.

```text
EHLO cliente.lab
MAIL FROM:<jdileomuntaner@itba.edu.ar>
RCPT TO:<63051@mail.sebikul.com>
DATA
```

| Comando | Qué le estás diciendo al servidor | Qué respuesta esperás |
|---|---|---|
| `EHLO cliente.lab` | «Soy el cliente `cliente.lab`». El nombre lo elegimos para la práctica. El servidor puede listar las extensiones SMTP que ofrece. | `250`, posiblemente en una respuesta de varias líneas. |
| `MAIL FROM:<jdileomuntaner@itba.edu.ar>` | «Empiezo un envío. Esta es la dirección del remitente del sobre». Es la dirección que SMTP puede usar para devolver un aviso de entrega fallida. | `250` si acepta el remitente. |
| `RCPT TO:<63051@mail.sebikul.com>` | «Entregá este mensaje a este buzón». El servidor del lab usa esa dirección para ubicar el buzón que después abrimos por POP3. Si hubiera más destinatarios, se enviaría un `RCPT TO` por cada uno. | `250` si acepta ese destinatario. |
| `DATA` | «Ya declaré el sobre. Ahora quiero enviar los encabezados y el cuerpo». | `354` indica que ya podés pegar el contenido. |

El **sobre SMTP** son las direcciones declaradas con `MAIL FROM` y `RCPT TO`. Son datos para transportar y entregar el correo. En cambio, `From` y `To` son parte del **mensaje** que queda guardado y que ve el cliente de correo. En este ejercicio usamos las mismas direcciones en ambos lugares. [Flujo de una transacción SMTP](https://www.rfc-editor.org/rfc/rfc5321.html#section-3.3)

## 3. Enviar encabezados y cuerpo

Cuando el servidor responda `354`, enviá este bloque. Es el mensaje que después recuperamos por POP3.

```text
Date: Mon, 09 Nov 2026 21:47:27 +0000
Message-ID: <63051.20261109.214727.ej5@cliente.lab>
From: =?UTF-8?B?SmVyw7NuaW1vIERpIExlbyBNdW50YW5lcg==?= <jdileomuntaner@itba.edu.ar>
To: <63051@mail.sebikul.com>
Subject: =?UTF-8?B?wqFCdWVub3MgZMOtYXMh?=
X-Parcial: 2024/2
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: base64

wqFIb2xhIG11bmRvIQ==
.
```

### Qué hace cada línea de DATA

| Línea | Qué significa y por qué la ponemos |
|---|---|
| `Date: Mon, 09 Nov 2026 21:47:27 +0000` | Indica la fecha y hora de origen que declara quien prepara el mensaje. `+0000` es el desplazamiento respecto de UTC que devolvió la workstation. |
| `Message-ID: <63051.20261109.214727.ej5@cliente.lab>` | Identifica este correo concreto. Sirve para reconocerlo en `RETR` y para referenciarlo en una respuesta. Abajo se explica cómo elegimos el valor. |
| `From: … <jdileomuntaner@itba.edu.ar>` | Declara quién escribió el mensaje. Antes de la dirección está tu nombre visible codificado, que el cliente decodifica al mostrar el remitente. |
| `To: <63051@mail.sebikul.com>` | Declara el destinatario visible. Usamos la misma dirección que en `RCPT TO`, que es el comando que dirige la entrega. |
| `Subject: =?UTF-8?B?wqFCdWVub3MgZMOtYXMh?=` | Declara el asunto visible. El *encoded-word* permite que el cliente reconstruya `¡Buenos días!`, incluidos el signo de apertura y la tilde. |
| `X-Parcial: 2024/2` | Es el encabezado personalizado que exige la consigna. Su valor identifica el parcial y se puede comprobar tal cual en `RETR`. |
| `MIME-Version: 1.0` | Indica que el mensaje usa MIME para describir el contenido. Lo ponemos una vez en los encabezados del mensaje. |
| `Content-Type: text/plain; charset=UTF-8` | `text/plain` dice que el cuerpo es texto plano. `charset=UTF-8` dice cómo convertir los bytes del texto en caracteres una vez decodificado el cuerpo. |
| `Content-Transfer-Encoding: base64` | Le indica al cliente que tiene que decodificar el cuerpo de Base64 antes de interpretar sus bytes como UTF-8. Este encabezado se aplica al cuerpo. El asunto y el nombre llevan su propio `?B?` dentro de sus encabezados. |
| Línea vacía | Separa los encabezados del cuerpo. Todo lo que sigue, hasta el terminador SMTP, se envía como cuerpo. |
| `wqFIb2xhIG11bmRvIQ==` | Es el cuerpo que viaja. Al decodificarlo se obtienen los bytes UTF-8 de `¡Hola mundo!`. |
| `.` en una línea propia | Es el terminador del diálogo SMTP para `DATA`. El servidor lo consume al terminar de leer el mensaje. |

Después del punto, un `250` confirma que SMTP aceptó el mensaje. `QUIT` cierra la sesión. En esta práctica conservamos la recuperación por POP3 como evidencia de entrega al buzón. [Formato del mensaje](https://www.rfc-editor.org/rfc/rfc5322.html) · [MIME y codificación del cuerpo](https://www.rfc-editor.org/rfc/rfc2045.html)

### Por qué ese Message-ID

El `Message-ID` identifica un correo concreto con la forma `<identificador@dominio>`. Lo construimos a mano para este ejercicio:

| Parte | Por qué está |
|---|---|
| `63051` | Legajo. |
| `20261109.214727` | Fecha y hora de envío en UTC según la workstation. |
| `ej5` | Etiqueta para reconocer este ejercicio. |
| `cliente.lab` | Nombre de práctica que elegimos para el cliente, igual al que usamos en `EHLO`. |

Esos componentes fueron una elección para obtener un identificador único y fácil de reconocer. Al redactar otro mensaje se genera otro identificador. En una respuesta, `In-Reply-To` puede referenciar el `Message-ID` original para vincular ambos mensajes.

### Por qué el From y el Subject se ven codificados

En `From` hay dos piezas. El nombre visible **Jerónimo Di Leo Muntaner** está en un *encoded-word* para conservar la tilde. La dirección `<jdileomuntaner@itba.edu.ar>` va fuera de esa codificación.

- En `=?UTF-8?B?…?=`, `UTF-8` indica la codificación de caracteres y `B` indica Base64. Los delimitadores marcan dónde empieza y termina el texto codificado.
- En `Subject` codificamos todo **¡Buenos días!**, incluidos `¡` e `í`. [Sintaxis de encoded-word en encabezados MIME](https://www.rfc-editor.org/rfc/rfc2047.html)

## 4. Recuperar el mensaje por POP3

Abrimos una conexión nueva al puerto POP3. En este lab se usa la dirección completa del buzón como usuario y contraseña.

```bash
nc -C mail.sebikul.com 110
```

Sesión real

```text
+OK LabProtos POP3 server ready
USER 63051@mail.sebikul.com
+OK usuario aceptado
PASS 63051@mail.sebikul.com
+OK logueado
LIST
+OK 1 messages
1 388
.
RETR 1
+OK 388 octets
Date: Mon, 09 Nov 2026 21:47:27 +0000
Message-ID: <63051.20261109.214727.ej5@cliente.lab>
From: =?UTF-8?B?SmVyw7NuaW1vIERpIExlbyBNdW50YW5lcg==?= <jdileomuntaner@itba.edu.ar>
To: <63051@mail.sebikul.com>
Subject: =?UTF-8?B?wqFCdWVub3MgZMOtYXMh?=
X-Parcial: 2024/2
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: base64

wqFIb2xhIG11bmRvIQ==

.
```

- `USER` identifica el buzón y `PASS` completa el acceso.
- `LIST` muestra un mensaje. En `1 388`, `1` es el número del mensaje y `388` es su tamaño en octetos.
- `RETR 1` recupera el mensaje completo. Si hubiera varios, el `Message-ID` permite identificar el que corresponde a este envío.
- El punto que aparece después de `LIST` o `RETR` lo manda el servidor POP3 para terminar una respuesta de varias líneas. En SMTP lo habíamos escrito nosotros para terminar `DATA`.
- Podés cerrar la sesión POP3 con `QUIT`.

## 5. Decodificar y verificar el cuerpo

Copiamos el cuerpo Base64 de `RETR 1` y lo decodificamos desde la shell.

```bash
echo 'wqFIb2xhIG11bmRvIQ==' | base64 -d
echo
```

Salida real

```text
¡Hola mundo!
```

`base64 -d` recupera el texto. El segundo `echo` agrega un salto de línea en la terminal para separar el resultado del prompt. Al decodificar el contenido Base64 de `Subject` se obtiene **¡Buenos días!** y al decodificar el nombre visible de `From` se obtiene **Jerónimo Di Leo Muntaner**. La copia recuperada conserva además `X-Parcial: 2024/2` y el `Message-ID` esperado.
