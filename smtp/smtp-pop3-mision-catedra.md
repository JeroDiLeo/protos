# SMTP + POP3 + base64: la "misión" de la cátedra, resuelta paso a paso

Ejercicio de correo de la cátedra: se entra a un buzón por POP3, se lee un mensaje con una clave en base64, se responde por SMTP devolviendo esa clave bien codificada y se borra el mensaje original. Acá está el enunciado completo, cada comando con **lo que muestra** y **por qué sigue el siguiente**.

Para practicar este mismo tipo con un corrector automático: [lab-correo/](../lab-correo/) (ejercicio C4 y las otras variantes). Variantes MIME (negrita, adjuntos, Cc/Bcc): [smtp-variantes-mime.md](smtp-variantes-mime.md).

## Enunciado
> En el servidor `192.168.0.238` tenés el buzón del agente **5** (cuenta `5@imf.com`). Hay un correo de `secretary@usa.com` con una misión. Leelo, descubrí qué te piden y respondé **a esa cuenta, usando SMTP en la misma IP**, con la codificación apropiada para que la respuesta llegue intacta. Después **borrá el mensaje original** del servidor.

**Datos:**
| Dato | Valor |
|---|---|
| Servidor | `192.168.0.238` |
| POP3 (leer/borrar) | puerto `110` |
| SMTP (enviar) | puerto `25` |
| Usuario del buzón | `5` |
| Contraseña del buzón | la de tu cuenta del laboratorio (distinta de la clave del acertijo; en los comandos va como `TU_CONTRASENA`) |
| Cuenta del agente | `5@imf.com` |
| Remitente de la misión y destinatario de la respuesta | `secretary@usa.com` |

> Los datos son los de la práctica; en el examen cambian, el método no.

> **Sobre las salidas:** los pasos 1 a 3 (POP3 y base64) son lo que apareció en la sesión real con el servidor de la cátedra (un GreenMail). Para los pasos 5 y 6 (respuestas de SMTP y del borrado POP3) no se guardó la salida del servidor de la cátedra, así que se muestran capturas del **lab local** ([lab-correo/](../lab-correo/)), con sus direcciones (`mision.lab`, `mail.protos.lab`) en lugar de las del examen: los **códigos** (250, 354, 221, +OK) son los mismos.

---

## Paso 1 — Listar los correos del buzón
~~~bash
curl -v --user "5" pop3://192.168.0.238:110/
~~~
curl pide la contraseña (no se ve al escribirla).

**Lo que muestra (parte relevante):**
~~~text
< +OK POP3 GreenMail Server v2.1.15 ready
> CAPA
< +OK
< UIDL
< SASL PLAIN XOAUTH2
< .
> AUTH PLAIN
< +
> [credenciales codificadas]
< +OK
> LIST
< +OK
1 955
~~~

**Cómo leerlo:**
| Pieza | Qué es |
|---|---|
| `-v` | modo verboso: `>` lo que envía curl, `<` lo que responde el servidor, `*` info de conexión |
| `--user "5"` | el usuario; al omitir la contraseña, curl la pide |
| `pop3://` | usa POP3 en vez de HTTP |
| `192.168.0.238:110` | IP y puerto del servidor |
| `/` final | sin número de mensaje, curl pide `LIST` |
| `+OK` / `-ERR` | la operación salió bien / mal |
| `CAPA` | consulta las capacidades del servidor |
| `AUTH PLAIN` + `+` | curl elige autenticación PLAIN; el `+` pide que mande las credenciales; el `+OK` posterior las acepta |
| `1 955` | formato de `LIST`: **número de mensaje, tamaño en bytes** → mensaje 1, 955 bytes |

PLAIN usa base64, que **no cifra**: la contraseña viaja legible (por eso existen POP3S/995 y STARTTLS).

**Por qué el próximo comando es ese:** el `LIST` dice que existe el mensaje número 1. El número no se adivina: sale de esa lista. Para leerlo se pide `/1`.

## Paso 2 — Leer el mensaje 1
~~~bash
curl -v --user "5" pop3://192.168.0.238:110/1
~~~
Las opciones son las mismas; `/1` hace que curl envíe `RETR 1` (recuperar el mensaje 1).

**Lo que muestra (parte relevante):**
~~~text
> RETR 1
< +OK
Return-Path: <secretary@usa.com>
From: secretary@usa.com
To: Agent 5 <5@imf.com>
Subject: Mission: Impossible
~~~
y a continuación (separado por una línea vacía) el cuerpo, que es un bloque en base64.

**Cómo leerlo:** `From` = quién lo envía; `To` = a quién va; `Subject` = asunto; `Return-Path` = dirección de retorno del **sobre** (para devoluciones); `Received` = lo que agregan los servidores en el camino. Una línea vacía separa los headers del cuerpo. **Leer con `RETR` no borra el mensaje.**

**Por qué el próximo comando es ese:** el cuerpo es un bloque de letras y números terminado en `=`: es base64 (múltiplo de 4, solo `A-Za-z0-9+/=`). Hay que decodificarlo para saber qué piden.

## Paso 3 — Decodificar el cuerpo base64
Se copia el bloque del cuerpo (las líneas juntas, sin saltos) y se decodifica:
~~~bash
echo "TG9zIG1pc2lsZXMgbnVjbGVhcmVzIHlhIGVzdMOhbiBsaXN0b3MgcGFyYSBkaXNwYXJhciwgcGVybyBwb3Igc2kgdGUgYXJyZXBlbnTDrXMgYWPDoSBlc3TDoSBsYSBjb250cmFzZcOxYSBwYXJhIGRlc2FjdGl2YXJsb3M6Cgouw7HDocOpw7PCocK/CgpFcyB0YW4gc2VndXJhIHF1ZSBubyBzZSBwdWVkZSBlbnZpYXIgcG9yIG1haWwgc2luIHNhYmVyIGPDs21vIGZ1bmNpb25hIGVsIHByb3RvY29sby4=" | base64 -d
~~~
- `echo "..."` imprime el texto entre comillas.
- `|` (pipe) le pasa esa salida a `base64 -d`, que **decodifica**.
- Si el bloque salió en varias líneas, se puede pegar igual: `base64 -d` ignora los saltos de línea dentro del texto.

**Lo que muestra:**
~~~text
Los misiles nucleares ya están listos para disparar, pero por si te arrepentís acá está la contraseña para desactivarlos:

.ñáéó¡¿

Es tan segura que no se puede enviar por mail sin saber cómo funciona el protocolo.
~~~

**Cómo leerlo:** la consigna del acertijo es devolver, **exactamente**, la cadena `.ñáéó¡¿`. No es una contraseña para iniciar sesión: es el contenido que hay que **responder**. Tiene caracteres que no son ASCII (`ñ á é ó ¡ ¿`) y empieza con un punto, y ambas cosas importan para enviarla.

**Por qué el próximo paso es codificarla:** el correo viaja por SMTP, que históricamente es un protocolo de texto ASCII. Para que los caracteres no ASCII lleguen intactos, MIME permite declarar `charset=UTF-8` y un `Content-Transfer-Encoding: base64`: el cuerpo viaja como ASCII seguro. (Además, un cuerpo que empieza con `.` en una línea sola generaría el problema del *dot-stuffing*, que base64 evita.)

## Paso 4 — Codificar la clave
~~~bash
echo -n '.ñáéó¡¿' | base64
~~~
**Lo que muestra:**
~~~text
LsOxw6HDqcOzwqHCvw==
~~~

- `echo -n` escribe el texto **sin el salto de línea final** (`-n` = no newline). Sin `-n`, el salto de línea también se codificaría y la respuesta ya no sería exactamente la clave.
- Las comillas simples conservan los caracteres tal cual.
- `| base64` (sin `-d`) **codifica**.

Comprobación (decodificar lo generado debe devolver la clave original):
~~~bash
echo 'LsOxw6HDqcOzwqHCvw==' | base64 -d
~~~
~~~text
.ñáéó¡¿
~~~

Se codifica **solo el cuerpo**. Los headers MIME siguen escritos en claro.

**Por qué el próximo paso es abrir SMTP:** ya tenemos el cuerpo listo; falta mandarlo, y se hace en el puerto 25.

## Paso 5 — Enviar la respuesta por SMTP

### 5.1 Conectarse
~~~bash
nc -C 192.168.0.238 25
~~~
- `nc` (netcat) escribe directamente sobre la conexión TCP.
- `-C` (en netcat-openbsd) convierte cada fin de línea a **CR+LF**, que SMTP exige. Sin `-C` el servidor puede no entender las líneas.
- Esperá el saludo `220` antes de escribir. Los comandos siguientes se escriben **dentro de netcat**, no en Bash, de a uno, esperando cada respuesta.

### 5.2 El diálogo completo
(captura del lab local; mismas respuestas en forma, otras direcciones)
~~~text
220 mx1.protos.lab ESMTP LabProtos ready
> EHLO localhost
250-mx1.protos.lab Hello localhost
250-SIZE 10240000
250-8BITMIME
250 HELP
> MAIL FROM:<5@imf.com>
250 2.1.0 Ok
> RCPT TO:<secretaria@mision.lab>
250 2.1.5 Ok
> DATA
354 End data with <CR><LF>.<CR><LF>
> From: 5@imf.com
> To: secretaria@mision.lab
> Subject: Re: Mission: Impossible
> MIME-Version: 1.0
> Content-Type: text/plain; charset=UTF-8
> Content-Transfer-Encoding: base64
>
> LsOxw6HDqcOzwqHCvw==
> .
250 2.0.0 Ok: queued as F6B9B681D3
> QUIT
221 2.0.0 Bye
~~~
(Las líneas con `>` las escribís vos; las demás las contesta el servidor.) En el examen el destinatario es `secretary@usa.com`.

### 5.3 Qué hace cada línea
| Línea | Qué es | Respuesta esperada |
|---|---|---|
| `EHLO localhost` | saludo; el servidor lista sus capacidades | `250` (una o varias líneas) |
| `MAIL FROM:<5@imf.com>` | remitente del **sobre** | `250`: aceptó el remitente |
| `RCPT TO:<secretary@usa.com>` | destinatario del **sobre** | `250`: aceptó el destinatario |
| `DATA` | "ahora viene la carta" | `354`: espera headers + cuerpo |
| `From:` / `To:` / `Subject:` | headers **visibles** de la carta | — |
| `MIME-Version: 1.0` | el mensaje usa MIME | — |
| `Content-Type: text/plain; charset=UTF-8` | cuerpo de texto en UTF-8 | — |
| `Content-Transfer-Encoding: base64` | el receptor debe decodificar el cuerpo | — |
| *(línea vacía)* | separa headers de cuerpo: **no la omitas** | — |
| `LsOxw6HDqcOzwqHCvw==` | la clave codificada | — |
| `.` (solo, en su línea) | fin del mensaje; no es parte del contenido | `250 ... queued`: aceptó el mensaje |
| `QUIT` | cierra la sesión | `221` |

**Sobre vs. carta:** `MAIL FROM` / `RCPT TO` son el **sobre** (por dónde se rutea). `From` / `To` dentro de `DATA` son lo que muestra el mail. Son cosas distintas y se escriben en momentos distintos.

**Los cuatro códigos que se confunden:** `250` tras `MAIL FROM` (aceptó el remitente), `250` tras `RCPT TO` (aceptó el destinatario), `354` tras `DATA` (espera la carta) y `250` **después del punto** (aceptó el mensaje completo). El último es el que confirma el envío, pero solo dice que SMTP lo aceptó; no que alguien lo haya leído.

**Si el servidor rechaza algo:** leé la respuesta antes de seguir. Por ejemplo `554 Relay denied` = el destinatario es de un dominio que ese servidor no recibe (probar el servidor correcto, o submission con AUTH); `503` = comandos en orden equivocado (por ejemplo `MAIL FROM` antes del saludo).

**Por qué el próximo paso es volver a POP3:** el envío está hecho; falta lo último que pide la consigna: borrar el original. Eso se hace por POP3, no por SMTP.

## Paso 6 — Borrar el mensaje original (POP3)
Antes de borrar, conviene verificar qué mensaje es. Los números pueden cambiar entre sesiones: **confirmá el contenido con `RETR`**.
~~~bash
nc -C 192.168.0.238 110
~~~
Dentro de la conexión, un comando por vez:
~~~text
+OK POP3 ... ready
> USER 5
+OK
> PASS TU_CONTRASENA
+OK Logged in. 2 messages
> LIST
+OK 2 messages:
1 899
2 621
.
> RETR 1
(... verificás que sea la misión ...)
> DELE 1
+OK Marked to be deleted.
> LIST
+OK 1 messages:
2 621
.
> QUIT
+OK LabProtos POP3 signing off (1 messages deleted)
~~~
(captura del lab local; allá hay más de un mensaje en el buzón.)

**Cómo leerlo:**
- `USER` / `PASS`: acá la contraseña **sí se ve** al escribirla. Es la del buzón, no la del acertijo.
- `LIST`: el listado termina con un punto solo (respuesta de varias líneas).
- `RETR 1`: ver el mensaje antes de borrarlo (leer no borra).
- `DELE 1`: **solo marca** el mensaje para borrar. Por eso el segundo `LIST` ya no lo muestra, pero todavía no se eliminó.
- `QUIT`: acá el servidor **aplica** el borrado (`1 messages deleted`). Si cerrás la terminal abruptamente, no se borra.
- `RSET` (antes del `QUIT`): deshace todas las marcas de borrado de la sesión. Útil si marcaste el mensaje equivocado.

**Verificación posterior:**
~~~bash
curl -v --user "5" pop3://192.168.0.238:110/
~~~
Si era el único mensaje, el listado queda vacío. Si hay otros, los números se **renumeran**: identificá la misión por su contenido, no solo por el número.

---

## Resumen para recordar
- **POP3:** `LIST` → `RETR` → `DELE` → `QUIT` (LIST lista, RETR lee, DELE marca, QUIT confirma).
- **Base64:** `base64 -d` decodifica, `base64` codifica; `echo -n` (con `-n`) para no agregar el salto de línea.
- **SMTP:** `EHLO` → `MAIL FROM` → `RCPT TO` → `DATA` → carta → `.` → `QUIT`. El `250` después del punto confirma la aceptación.
- Leer y enviar usan conexiones distintas: **POP3 en 110, SMTP en 25**.
- La clave del acertijo va en el **cuerpo**; no reemplaza la contraseña de acceso al buzón.

## Qué decir en el video
«Leí el buzón por POP3 con LIST y RETR y decodifiqué el cuerpo en base64. Para responder usé SMTP separando sobre (MAIL FROM / RCPT TO) y carta (DATA); como la clave tiene caracteres no ASCII, declaré `charset=UTF-8` y `Content-Transfer-Encoding: base64` y codifiqué solo el cuerpo. El 250 posterior al punto confirmó la aceptación, y borré el original con DELE + QUIT.»
