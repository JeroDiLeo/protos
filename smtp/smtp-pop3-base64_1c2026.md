# SMTP a mano + POP3 con base64 (1C 2026, ej 5)

## Enunciado (textual)

*Fuente: 1C 2026, Ejercicio 5.*

Envíe un correo electrónico cumpliendo todos los estándares y buenas prácticas que cumpla con los siguientes requisitos:

1. Contenga el header `X-Parcial` con el valor `2024/2`.
2. Contenga un título (subject): `¡Buenos días!`
3. Contenga como remitente su nombre, apellido y cuenta de correo del ITBA.
4. Contenga el texto:

```text
¡Hola mundo!
```

5. El correo debe entregarse a la dirección `{legajo}@mail.sebikul.com` donde `{legajo}` es número de legajo. Por ejemplo si su legajo 40123 entonces deberá entregar el correo a la dirección `40123@mail.sebikul.com`.
6. Debe poder ser leído por MUAs que no soporten la codificación quoted printable.

Debe verificar su recepción utilizando el protocolo POP3. Para ello dispone de un servidor POP3 en el host `mail.sebikul.com`. El nombre de usuario es `{legajo}@mail.sebikul.com`, donde `{legajo}` debe reemplazarse por su número de legajo, y la password será el mismo valor que el usuario.

Por ejemplo, si su legajo fuese `0123`, el nombre usuario POP3 sería `0123@mail.sebikul.com` y la contraseña `0123@mail.sebikul.com`.

---

## ⭐ RECETA PARA EL PARCIAL (leer esto primero)

> Abajo, en "PRÁCTICA", está lo que corriste contra Postfix/Dovecot **locales** (`jerodileo@localhost`, `RETR 8`). En el parcial **no** se usa nada de eso: se usan el servidor y las credenciales del enunciado. Esta receta ya tiene todo con los datos del parcial.

### Paso 0 — De la consigna a cada línea del mail
| La consigna dice | Va en | Cómo se escribe |
|---|---|---|
| header `X-Parcial` con `2024/2` | cabecera | `X-Parcial: 2024/2` (copiar el valor **exacto**, aunque el año no coincida) |
| subject `¡Buenos días!` | cabecera | tiene `¡` y `í` → encoded-word `=?UTF-8?B?<base64>?=` |
| remitente con mi nombre y cuenta ITBA | sobre **y** cabecera | `MAIL FROM:<cuenta@itba.edu.ar>` y `From: =?UTF-8?B?<base64 del nombre>?= <cuenta@itba.edu.ar>` |
| cuerpo `¡Hola mundo!` | cuerpo | en **base64** |
| entregar a `{legajo}@mail.sebikul.com` | sobre **y** cabecera | `RCPT TO:<63051@mail.sebikul.com>` y `To: 63051@mail.sebikul.com` |
| "MUAs que no soporten quoted-printable" | cabeceras MIME | `Content-Transfer-Encoding: base64` (**nunca** quoted-printable) |
| verificar por POP3 | otra conexión | puerto 110, `RETR` del mensaje |

**Credenciales POP3 (están en el enunciado completo, apuntes del tercero):** usuario `{legajo}@mail.sebikul.com` y contraseña **igual al usuario**. Para mí: `63051@mail.sebikul.com` / `63051@mail.sebikul.com`.

### Paso 1 — Comprobar que llego al servidor (10 segundos)
~~~bash
dig +short MX mail.sebikul.com     # ¿hay MX? si sale un host, el SMTP es ese
dig +short A mail.sebikul.com      # si no hay MX, se entrega al A del dominio
nc -vz mail.sebikul.com 25         # -z: solo prueba si el puerto abre, sin hablar
nc -vz mail.sebikul.com 110
~~~
- El correo para `x@dominio` se entrega al servidor que dice el **MX de ese dominio**. Si no hay MX, al A del propio dominio. En el 1C 2026, según los apuntes, se habló directo con `mail.sebikul.com` en el 25 y el 110.
- Si `nc -vz` dice `succeeded`, sigo. Si no resuelve o rechaza, no es un problema del mail: es de red o DNS.

### Paso 2 — Generar los base64 (en una terminal normal, NO dentro de nc)
~~~bash
printf '%s' '¡Buenos días!'            | base64 -w0; echo   # subject
printf '%
---

# Protocolos — 1C 2026, ejercicio 5: SMTP manual y POP3
## Datos y resultado
Nombre: Jerónimo Di Leo Muntaner.
Cuenta ITBA: jdileomuntaner@itba.edu.ar.
Legajo: 63051.
Consigna A: X-Parcial: 2024/2; asunto ¡Buenos días!; cuerpo ¡Hola mundo!; destinatario 63051@mail.sebikul.com; sin quoted-printable; verificar POP3.

El nombre mail.sebikul.com no resolvió en la VM. Se usaron los servicios ya instalados: Postfix SMTP en 127.0.0.1:25 y Dovecot POP3 en 127.0.0.1:110. Se entregó a jerodileo@localhost, no a la dirección externa del enunciado.
Éxito real: Postfix aceptó el mensaje como B70BD36338B; POP3 RETR 8 devolvió ese mismo identificador, cabeceras y cuerpo. No se probó entrega en el dominio externo.

> ### ⭐ EN EL PARCIAL (datos reales del enunciado, no los de esta práctica local)
> - **Servidor:** se habla directo con `mail.sebikul.com` tanto para enviar (puerto 25) como para leer (puerto 110). No hay que montar nada: `nc -C mail.sebikul.com 25` y `nc -C mail.sebikul.com 110`.
> - **Credenciales POP3:** el enunciado las fija. Usuario = `{legajo}@mail.sebikul.com` y **contraseña = el mismo valor que el usuario**. Para mí: `USER 63051@mail.sebikul.com` / `PASS 63051@mail.sebikul.com`. (En esta práctica de abajo quedó `USER jerodileo` porque fue contra el buzón local; en el parcial usar lo de acá.)
> - **Sobre y cabecera, los dos al dominio real:** `RCPT TO:<63051@mail.sebikul.com>` y `To: 63051@mail.sebikul.com`.
> - **Número de RETR:** con `LIST` fijate el número del mensaje recién entregado (no asumas 8); ese buzón arranca vacío, así que suele ser `RETR 1`.
> - **El resto del diálogo** (EHLO, MAIL FROM, DATA, las cabeceras MIME y el cuerpo en base64) es idéntico al de la práctica de abajo. Lo único que cambia son esas líneas.

## 1. Descubrimiento del entorno
~~~bash
nc -v -w 5 mail.sebikul.com 25
~~~
nc abre TCP; -v muestra conexión; -w 5 limita conexión/inactividad en la variante de Ubuntu; último argumento puerto SMTP. Falló getaddrinfo: no obtuvo IP, no hubo diálogo SMTP.

~~~bash
sudo ss -ltnp '( sport = :2525 or sport = :110 )'
~~~
sudo permite ver procesos; ss sockets; -l escucha; -t TCP; -n numérico; -p proceso. Filtro selecciona puertos locales.
110 estaba ocupado por Dovecot. Se eligió aprovecharlo.
~~~bash
sudo ss -ltnp '( sport = :25 or sport = :587 )'
~~~
Se detectó master escuchando en 25. El saludo SMTP luego confirmó Postfix. No se necesitó crear otro servidor.

~~~bash
postconf mydestination home_mailbox mailbox_command
~~~
Consulta sin modificar configuración de Postfix.
Resultado:
~~~text
mydestination = $myhostname, foo.pdc.lab, jerOS, localhost.localdomain, localhost
home_mailbox =
mailbox_command =
~~~
mydestination incluye dominios de entrega local; los otros parámetros no personalizaban ruta dentro del home ni programa de entrega. Se seleccionó una cuenta local existente: jerodileo@localhost. La lectura real por Dovecot confirmó que esa entrega funcionó.

## 2. Base64: comandos exactos
Ejecutar en una terminal normal, no dentro de nc:
~~~bash
printf '%s' '¡Hola mundo!' | base64
~~~
Resultado: wqFIb2xhIG11bmRvIQ==
~~~bash
printf '%s' '¡Buenos días!' | base64
~~~
Resultado: wqFCdWVub3MgZMOtYXMh
~~~bash
printf '%s' 'Jerónimo Di Leo Muntaner' | base64
~~~
Resultado: SmVyw7NuaW1vIERpIExlbyBNdW50YW5lcg==

printf '%s' escribe literalmente sin agregar salto de línea; comillas simples protegen texto; | pasa bytes a base64. La terminal debe producir UTF-8. Base64 representa bytes usando ASCII; no cifra.
Para textos extensos, MIME Base64 limita las líneas a 76 caracteres; base64 de GNU usa ese ancho por defecto.

El cuerpo usa Content-Transfer-Encoding: base64. El lector debe admitir MIME/Base64; no depende de quoted-printable.
El asunto y nombre visible usan encoded-word:
~~~text
=?UTF-8?B?BASE64?=
~~~
UTF-8 identifica charset, B indica Base64. No se usa esta envoltura alrededor del cuerpo ni de la dirección email.
Los headers tradicionales son ASCII; SMTPUTF8 permite UTF-8 bajo sus condiciones. Se eligió encoded-word por compatibilidad, sin requerir esa extensión.

## 3. Sobre y cabeceras
| Elemento | Papel |
|---|---|
| MAIL FROM:<dirección> | Remitente del sobre, dirección de retorno para notificaciones |
| RCPT TO:<dirección> | Destinatario real de entrega |
| From: nombre <dirección> | Autor visible dentro del mensaje |
| To: dirección | Destinatario visible dentro del mensaje |

Pueden ser distintos porque el sobre pertenece al protocolo de transporte y las cabeceras forman parte del contenido. La entrega no se decide leyendo To:. Escribir From: no autentica esa identidad. Reenvíos y listas pueden justificar diferencias legítimas; controles del servidor pueden rechazar otras.

## 4. Conexión y diálogo real de la práctica
~~~bash
nc -C -v 127.0.0.1 25
~~~
-C convierte fin de línea enviado a CRLF en netcat de Ubuntu; -v muestra conexión; 127.0.0.1 es esta VM; 25 SMTP. Sin -w breve para poder escribir con calma. Esperar 220.

Comandos del cliente, limpios. Copiar línea por línea y esperar las respuestas de SMTP antes de continuar; tras DATA/354, las cabeceras y cuerpo se envían como un bloque sin esperar respuesta por cada línea:
~~~text
EHLO [127.0.0.1]
MAIL FROM:<jdileomuntaner@itba.edu.ar>
RCPT TO:<jerodileo@localhost>
DATA
From: =?UTF-8?B?SmVyw7NuaW1vIERpIExlbyBNdW50YW5lcg==?= <jdileomuntaner@itba.edu.ar>
To: jerodileo@localhost
Subject: =?UTF-8?B?wqFCdWVub3MgZMOtYXMh?=
X-Parcial: 2024/2
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: base64

wqFIb2xhIG11bmRvIQ==
.
QUIT
~~~

| Línea o respuesta | Significado |
|---|---|
| 220 | Servicio preparado |
| EHLO [127.0.0.1] | Saludo de cliente con dirección literal |
| 250-... y última 250 ... | Capacidades; guion continúa y espacio finaliza |
| MAIL FROM | Inicia transacción y declara retorno |
| 250 2.1.0 Ok | Remitente aceptado |
| RCPT TO | Agrega receptor del sobre |
| 250 2.1.5 Ok | Destinatario aceptado |
| DATA | Pide enviar contenido |
| 354 | Puede comenzar el contenido |
| From / To / Subject | Autor, destinatario visible y asunto |
| X-Parcial | Dato exacto pedido: 2024/2, aunque el ejercicio sea de 2026 |
| MIME-Version: 1.0 | Declara uso de MIME |
| Content-Type: text/plain; charset=UTF-8 | Texto simple cuyos bytes originales son UTF-8 |
| Content-Transfer-Encoding: base64 | Cómo recuperar los bytes del cuerpo |
| Línea vacía | Separa cabeceras y cuerpo; no debe llevar espacios |
| Cuerpo Base64 | Representa ¡Hola mundo! |
| Punto solo | Termina DATA; no se guarda como parte del cuerpo |
| 250 ... queued as B70BD36338B | Mensaje aceptado en cola; falta comprobar entrega |
| QUIT y 221 | Cierre SMTP |

Si el texto sin Base64 tuviera líneas que empiezan con punto, se duplicaría el primer punto para transporte SMTP (dot-stuffing). Nuestra línea Base64 no tiene ese problema.
Postfix anunció también STARTTLS, 8BITMIME y SMTPUTF8; no se necesitaron estas dos últimas para el mensaje ASCII transmitido.

## 5. Diálogo para la consigna original
Solo usar cuando el servidor real esté disponible:
~~~bash
nc -C -v mail.sebikul.com 25
~~~
~~~text
EHLO [127.0.0.1]
MAIL FROM:<jdileomuntaner@itba.edu.ar>
RCPT TO:<63051@mail.sebikul.com>
DATA
From: =?UTF-8?B?SmVyw7NuaW1vIERpIExlbyBNdW50YW5lcg==?= <jdileomuntaner@itba.edu.ar>
To: 63051@mail.sebikul.com
Subject: =?UTF-8?B?wqFCdWVub3MgZMOtYXMh?=
X-Parcial: 2024/2
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: base64

wqFIb2xhIG11bmRvIQ==
.
QUIT
~~~
En un host no local identificar al cliente en EHLO mediante su nombre completo o literal de dirección apropiado; aquí se conserva el literal de la práctica como ejemplo. El servidor puede imponer políticas propias.

## 6. POP3 real: verificar recepción
~~~bash
nc -C -v 127.0.0.1 110
~~~
Mismas opciones; 110 es POP3. Saludo: +OK Dovecot ready.
~~~text
USER jerodileo
PASS CONTRASEÑA_LOCAL
STAT
LIST
RETR 8
QUIT
~~~
Reemplazar el marcador de contraseña solo en la terminal; no guardarla en el apunte. nc puede mostrarla al escribir. USER identifica cuenta; PASS autentica. Se usó la contraseña de la VM, no la del ITBA.
STAT real: +OK 8 88597 → ocho mensajes, 88597 octetos.
LIST real: ocho entradas; la 8 tenía 700 octetos. LIST sin argumento lista números/tamaños, termina con punto.
RETR 8 devolvió mensaje completo, incluidas estas evidencias:
~~~text
Return-Path: <jdileomuntaner@itba.edu.ar>
Delivered-To: jerodileo@localhost
Received: ... Postfix ... B70BD36338B ...
Subject: =?UTF-8?B?wqFCdWVub3MgZMOtYXMh?=
X-Parcial: 2024/2
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: base64

wqFIb2xhIG11bmRvIQ==
~~~
Return-Path refleja el sobre recibido. Postfix agregó Message-Id y Date en esta instalación. Para un mensaje completo independiente de ese comportamiento se pueden agregar esas cabeceras antes de la línea vacía.
QUIT dio +OK Logging out. No se usó DELE: no se solicitó borrar mensajes.
RETR no decodifica MIME en nc; se ve Base64. Para comprobar el texto:
~~~bash
printf '%s' 'wqFIb2xhIG11bmRvIQ==' | base64 --decode
~~~
--decode revierte Base64.
En futuras sesiones elegir el número de LIST real, no asumir 8. POP3 usa +OK/-ERR, no códigos numéricos SMTP. Para el servidor real usar host, usuario POP3 y contraseña proporcionados por la cátedra; no se conocen en esta práctica.

## 7. Variantes: qué cambia y qué línea tocar
| Cambio | Línea o acción |
|---|---|
| Otro receptor real | RCPT TO:<otro@dominio> |
| Receptor visible | To: otro@dominio |
| Otro X-Parcial | X-Parcial: 2026/1R |
| Asunto ASCII | Subject: Buenos dias |
| Asunto con acentos | Encoded-word con Base64 UTF-8 |
| Remitente de sobre distinto | MAIL FROM:<otra@direccion> |
| Autor visible distinto | From: Nombre <otra@direccion> |
| Cuerpo HTML | Content-Type: text/html; charset=UTF-8 y Base64 de HTML |
| Adjuntar archivo | Contenedor multipart/mixed y parte attachment, como abajo |

Un asunto que sea solo ASCII no necesita encoded-word. Correo con From distinto no cambia automáticamente MAIL FROM ni demuestra control de esa dirección; políticas SPF/DKIM/DMARC y del servicio pueden afectar aceptación/entrega.

### Adjunto
Cabecera global:
~~~text
Content-Type: multipart/mixed; boundary="mix-63051"
~~~
Tras línea vacía, una parte de texto y otra de archivo, cerrando el boundary:
~~~text
--mix-63051
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: base64

wqFIb2xhIG11bmRvIQ==
--mix-63051
Content-Type: application/octet-stream
Content-Disposition: attachment; filename="archivo.bin"
Content-Transfer-Encoding: base64

BASE64_DEL_ARCHIVO
--mix-63051--
~~~
En una terminal normal generar con:
~~~bash
base64 archivo.bin
~~~
No pegar el marcador BASE64_DEL_ARCHIVO; pegar su salida. Base64 se declara en cada parte, no sobre el contenedor multipart. Si hay alternative y adjunto, anidar alternative como primera parte de mixed usando boundaries distintos.

### AUTH LOGIN
Solo si el servidor anuncia y permite LOGIN. Primero usar TLS cuando se transmiten credenciales reales. nc sin TLS no cifra. Un diálogo STARTTLS no se continúa con texto nc después de 220: se requiere handshake TLS. Se puede conectar con:
~~~bash
openssl s_client -starttls smtp -connect servidor:587 -servername servidor -crlf -verify_return_error
~~~
s_client es cliente TLS; -starttls smtp negocia elevación SMTP; -connect fija host/puerto; -servername envía SNI; -crlf transforma finales de línea; -verify_return_error aborta ante errores de verificación de certificado. Reemplazar servidor por nombre real y verificar también su identidad. Repetir EHLO bajo TLS.
Generar codificaciones de usuario/clave de práctica con printf '%s' 'VALOR' | base64.
Diálogo:
~~~text
AUTH LOGIN
BASE64_DEL_USUARIO
BASE64_DE_LA_CLAVE
~~~
Esperar challenge 334 antes de cada valor y éxito 235 al final; 535 indica fallo. Luego MAIL FROM, RCPT TO y DATA. No pegar marcadores literalmente. Base64 no es cifrado y los desafíos no son las credenciales. El servicio local probado no anunció AUTH; esta variante no se ejecutó.

## 8. Cómo repetir
Usa Postfix y Dovecot ya instalados y activos; no se modificó su configuración. Repetir nc local y diálogos. Si están detenidos, consultar primero systemctl status postfix y systemctl status dovecot; iniciar únicamente el necesario con sudo systemctl start NOMBRE. No se dejó un script servidor adicional porque no fue necesario.

## Frase para justificar
“Envío el correo mediante el diálogo SMTP, codifico el asunto y el cuerpo sin quoted-printable y verifico por POP3 las cabeceras y el contenido del mensaje entregado.”

## Guardar en la VM
Descargar el apunte y copiarlo desde Downloads:
~~~bash
mkdir -p ~/protos/soluciones
~~~
mkdir crea directorio; -p padres faltantes.
~~~bash
cp ~/Downloads/26.1-5.md ~/protos/soluciones/26.1-5.md
~~~
cp copia origen a destino; ~ es home local.

## Referencias
- [MIME](https://www.rfc-editor.org/rfc/rfc2045)
- [Encoded-word](https://www.rfc-editor.org/rfc/rfc2047)
- [Multipart](https://www.rfc-editor.org/rfc/rfc2046)
- [POP3](https://www.rfc-editor.org/rfc/rfc1939)

