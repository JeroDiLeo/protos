# Protocolos — Recu 2026, ejercicio 1: SMTP, multipart y POP3

## Enunciado (textual)

*Fuente: Recuperatorio 2026, Ejercicio 1.*

Envie un correo electronico cumpliendo todos los estandares y buenas practicas, con los siguientes requisitos:

1. Contenga el header `X-Parcial` con el valor `2026/1R`.
2. Contenga un titulo (`Subject`): `¡Buenos días!`.
3. Contenga como remitente su nombre, apellido y cuenta de correo del ITBA.
4. Contenga el texto: `¡Hola mundo!` en negrita
5. El correo debe entregarse a la direccion `{legajo}@mail.protos.foo`, donde `{legajo}` es su numero de legajo.
6. Debe poder ser leido por MUAs que no soporten la codificacion quoted-printable.

Debe verificar su recepcion utilizando el protocolo POP3. Para ello dispone de un servidor POP3 en el host `mail.protos.foo`. El nombre de usuario es `{legajo}@mail.protos.foo` y la password tiene el mismo valor que el usuario.

---
## Consigna y alcance de la práctica
Nombre: Jerónimo Di Leo Muntaner.
Cuenta ITBA: jdileomuntaner@itba.edu.ar.
Legajo: 63051.
X-Parcial: 2026/1R.
Asunto: ¡Buenos días!
Destinatario del parcial: 63051@mail.protos.foo.
Cuerpo: ¡Hola mundo! en negrita, con alternativa de texto simple y sin quoted-printable.

Se usaron Postfix y Dovecot locales ya instalados en la VM: SMTP 127.0.0.1:25, POP3 127.0.0.1:110 y buzón jerodileo@localhost. Se comprobó previamente que localhost figura en mydestination de Postfix.
No se verificó disponibilidad de mail.protos.foo ni entrega al destinatario externo de esta variante. La práctica local se completó con éxito.
Postfix: queued as 7131336338B.
POP3: RETR 9 recuperó el mensaje de 910 octetos con el mismo identificador, las cabeceras correctas y las dos partes.

> ### ⭐ EN EL PARCIAL (datos reales del enunciado, no los de esta práctica local)
> - **A qué servidor conectarse:** el correo para `@mail.protos.foo` se entrega al MX de ese dominio. Averigualo con `dig +short MX mail.protos.foo` → da el host (en el recu real fue `mx1.protos.foo`). Entonces: `nc -C mx1.protos.foo 25`.
> - **Entrega:** `RCPT TO:<63051@mail.protos.foo>` y `To: 63051@mail.protos.foo`. `X-Parcial: 2026/1R`.
> - **Dos cabeceras que conviene agregar a mano:** en el recu real el servidor (GreenMail) esperaba un mensaje completo, así que se pusieron `Date:` y `Message-ID:` antes de la línea en blanco:
>   ~~~text
>   Date: <salida de `date -R`>
>   Message-ID: <63051@mail.protos.foo>
>   ~~~
>   Postfix las agrega solo, pero otros servidores no: ponerlas no molesta y evita un rechazo.
> - **Sobre el "en negrita":** la solución del tercero usó un solo `text/plain` con los asteriscos (`*¡Hola mundo!*`) porque en texto plano la negrita no existe de verdad. Tu versión multipart/alternative (texto + HTML `<b>`) es **más completa** y también válida: la dejo porque cubre el cliente que sí renderiza HTML. Cualquiera de las dos da el ejercicio por bueno; si querés ir a lo mínimo y seguro, alcanza con el `text/plain` de asteriscos en base64.
> - **El resto del diálogo** (EHLO, MAIL FROM, DATA, cabeceras, cuerpo base64, POP3) es igual al de abajo. Para POP3 usar el host y las credenciales que dé la cátedra; por analogía con el 1C, probar usuario `63051@mail.protos.foo` con esa misma cadena de contraseña.

## 1. Preparar las codificaciones en una terminal normal
~~~bash
printf '%s' '*¡Hola mundo!*' | base64
~~~
Resultado: KsKhSG9sYSBtdW5kbyEq
~~~bash
printf '%s' '<b>¡Hola mundo!</b>' | base64
~~~
Resultado: PGI+wqFIb2xhIG11bmRvITwvYj4=
~~~bash
printf '%s' '¡Buenos días!' | base64
~~~
Resultado: wqFCdWVub3MgZMOtYXMh
~~~bash
printf '%s' 'Jerónimo Di Leo Muntaner' | base64
~~~
Resultado: SmVyw7NuaW1vIERpIExlbyBNdW50YW5lcg==

printf '%s' imprime sin salto extra; las comillas simples protegen el texto y no se envían. | pasa los bytes a base64. Se supone terminal UTF-8. No ejecutar estos comandos dentro de nc en estado DATA: serían contenido del mensaje.
Para textos largos, mantener líneas Base64 MIME de hasta 76 caracteres. GNU base64 usa ese ancho por defecto.

## 2. Cómo se representa la negrita y qué significa alternative
text/plain contiene *¡Hola mundo!*: asteriscos visibles como énfasis textual, no una orden estándar de negrita.
text/html contiene <b>¡Hola mundo!</b>: un cliente que renderice HTML puede mostrarlo en negrita.
multipart/alternative ofrece representaciones del mismo contenido: el cliente elige la que soporta. Se puso texto simple primero y HTML después. Un cliente sin HTML puede elegir texto simple.
La compatibilidad sin quoted-printable requiere que el cliente admita MIME y Base64; no significa compatibilidad con cualquier lector sin soporte MIME.

El parámetro boundary="alt-63051" define el separador, sin los dos guiones iniciales. En el cuerpo:
- --alt-63051 abre cada parte.
- Una línea vacía separa cabeceras de cada parte y sus datos.
- --alt-63051-- cierra el multipart.
El valor debe evitar colisiones con contenido y ser idéntico en todos los delimitadores. El contenedor no se codifica completo en Base64: cada parte tiene su Content-Transfer-Encoding.

## 3. Sobre SMTP y cabeceras
MAIL FROM y RCPT TO pertenecen al sobre, usado por el servidor para retorno y entrega.
From, To y Subject pertenecen al mensaje que recibe el lector.
Escribir otra cabecera From no cambia MAIL FROM. Cambiar To no cambia RCPT TO. Pueden ser distintos por diseño; las políticas de autenticación y antisuplantación pueden limitarlo.
La dirección de ITBA escrita en el sobre y en From no demuestra control de esa cuenta.

Subject y nombre visible se codifican como encoded-word:
~~~text
=?UTF-8?B?BASE64?=
~~~
UTF-8 señala charset; B Base64. La dirección ASCII no se codifica así. Los headers tradicionales no admiten UTF-8 crudo; SMTPUTF8 permite internacionalización bajo sus condiciones. Esta solución no depende de esa extensión.

## 4. Conectar al servidor local
~~~bash
nc -C -v 127.0.0.1 25
~~~
nc abre TCP; -C envía finales de línea CRLF en netcat Ubuntu; -v muestra la conexión; dirección loopback selecciona esta VM; 25 es SMTP.
CRLF es el fin de línea del protocolo. No usar un límite de inactividad de cinco segundos para escribir con calma.

El servidor real de la práctica saludó:
~~~text
220 jerOS.tail52d97a.ts.net ESMTP Postfix (Ubuntu)
~~~

## 5. Diálogo SMTP limpio — local, realmente ejecutado
Esperar respuesta a cada comando hasta DATA. Tras 354, pegar cabeceras y cuerpo conservando líneas vacías. Esperar el 250 final antes de QUIT.
~~~text
EHLO [127.0.0.1]
MAIL FROM:<jdileomuntaner@itba.edu.ar>
RCPT TO:<jerodileo@localhost>
DATA
From: =?UTF-8?B?SmVyw7NuaW1vIERpIExlbyBNdW50YW5lcg==?= <jdileomuntaner@itba.edu.ar>
To: jerodileo@localhost
Subject: =?UTF-8?B?wqFCdWVub3MgZMOtYXMh?=
X-Parcial: 2026/1R
MIME-Version: 1.0
Content-Type: multipart/alternative; boundary="alt-63051"

--alt-63051
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: base64

KsKhSG9sYSBtdW5kbyEq
--alt-63051
Content-Type: text/html; charset=UTF-8
Content-Transfer-Encoding: base64

PGI+wqFIb2xhIG11bmRvITwvYj4=
--alt-63051--
.
QUIT
~~~

| Paso | Explicación y respuesta |
|---|---|
| EHLO [127.0.0.1] | Presenta al cliente; respuesta 250 multilínea anuncia capacidades |
| MAIL FROM:<...> | Dirección del remitente del sobre; 250 2.1.0 Ok |
| RCPT TO:<...> | Entrega al usuario local; 250 2.1.5 Ok |
| DATA | Solicita enviar contenido; 354 |
| From | Nombre visible codificado y dirección del autor |
| To | Destinatario visible de práctica |
| Subject | Encoded-word del asunto |
| X-Parcial | Valor exacto del recuperatorio |
| MIME-Version | Declara MIME 1.0 |
| Content-Type global | Contenedor y boundary |
| Línea vacía | Termina cabeceras globales |
| Cabeceras de cada parte | Tipo y charset originales, más codificación de transferencia |
| Base64 de cada parte | Representación del contenido original |
| Cierre --alt-63051-- | Final del multipart |
| Punto solo | Final de DATA, distinto del cierre MIME |
| 250 ... queued as 7131336338B | Postfix aceptó el mensaje en cola |
| QUIT | Cierre; respuesta 221 |

Una respuesta 250 tras DATA confirma aceptación en cola, no lectura por el receptor. POP3 comprueba entrega al buzón. Postfix agregó Message-Id y Date en esta instalación; se pueden incluir manualmente antes de la línea vacía si se requiere un mensaje completo sin esa asistencia.

## 6. Adaptar al servidor del enunciado
Cuando mail.protos.foo esté disponible:
~~~bash
nc -C -v mail.protos.foo 25
~~~
Mantener el diálogo del apartado 5 con estas dos sustituciones:
~~~text
RCPT TO:<63051@mail.protos.foo>
To: 63051@mail.protos.foo
~~~
Para que quede completo y listo para copiar:
~~~text
EHLO [127.0.0.1]
MAIL FROM:<jdileomuntaner@itba.edu.ar>
RCPT TO:<63051@mail.protos.foo>
DATA
From: =?UTF-8?B?SmVyw7NuaW1vIERpIExlbyBNdW50YW5lcg==?= <jdileomuntaner@itba.edu.ar>
To: 63051@mail.protos.foo
Subject: =?UTF-8?B?wqFCdWVub3MgZMOtYXMh?=
X-Parcial: 2026/1R
MIME-Version: 1.0
Content-Type: multipart/alternative; boundary="alt-63051"

--alt-63051
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: base64

KsKhSG9sYSBtdW5kbyEq
--alt-63051
Content-Type: text/html; charset=UTF-8
Content-Transfer-Encoding: base64

PGI+wqFIb2xhIG11bmRvITwvYj4=
--alt-63051--
.
QUIT
~~~
Para un servidor externo, presentar en EHLO un nombre del cliente o una dirección literal apropiados al entorno; [127.0.0.1] fue el valor utilizado localmente. Respetar las políticas del servidor.

## 7. Verificación POP3 real
~~~bash
nc -C -v 127.0.0.1 110
~~~
110 es POP3; -C y -v cumplen las mismas funciones. Saludo +OK Dovecot ready.
~~~text
USER jerodileo
PASS CONTRASEÑA_LOCAL
STAT
LIST
RETR 9
QUIT
~~~
El marcador de contraseña se reemplaza solo en la terminal. Se usó la cuenta local; no la contraseña ITBA. No guardar ni publicar credenciales.
USER identifica buzón; PASS autentica; respuestas +OK éxito y -ERR error.
STAT real:
~~~text
+OK 9 89507
~~~
Nueve mensajes, tamaño total 89507 octetos.
LIST real: 9 910 para el último mensaje; la respuesta multilínea termina con punto.
RETR 9 recuperó 910 octetos y mostró:
- Received con id 7131336338B.
- X-Parcial: 2026/1R.
- multipart/alternative; boundary="alt-63051".
- Parte text/plain en Base64: KsKhSG9sYSBtdW5kbyEq.
- Parte text/html en Base64: PGI+wqFIb2xhIG11bmRvITwvYj4=.
- Cierre --alt-63051--.
QUIT respondió +OK Logging out. No se usó DELE: no se borraron mensajes.
RETR muestra el mensaje crudo; nc no lo renderiza ni decodifica. Haber recuperado ambas partes prueba la estructura y entrega, no una captura de un cliente gráfico mostrando negrita.

En otra sesión elegir el número actual de LIST, no asumir 9. Para el servidor del parcial usar el host y las credenciales POP3 que indique la cátedra.

## 8. Variantes: qué cambia y qué línea tocar
| Cambio | Línea/acción |
|---|---|
| Otro destinatario real | RCPT TO:<otro@dominio> |
| Otro destinatario visible | To: otro@dominio |
| Otro X-Parcial | X-Parcial: 2024/2 |
| Asunto solo ASCII | Subject: Buenos dias |
| Asunto no ASCII | Subject: =?UTF-8?B?BASE64_DEL_ASUNTO?= |
| Remitente de sobre distinto | MAIL FROM:<otra@direccion> |
| Autor visible distinto | From: Nombre <otra@direccion> |
| Otro boundary | Cambiar el parámetro y TODOS los delimitadores |
| Solo texto simple | Content-Type global text/plain, CTE base64 y quitar contenedor/partes |
| Adjunto | multipart/mixed externo, con alternative anidado como primera parte |

Un From distinto no es autenticación ni cambia el sobre; el servidor puede aplicar políticas antisuplantación. Un asunto ASCII no necesita encoded-word.

### Adjunto sin perder las alternativas
Cabecera global:
~~~text
Content-Type: multipart/mixed; boundary="mix-63051"
~~~
Dentro del cuerpo usar esta estructura, sustituyendo los marcadores por contenido real:
~~~text
--mix-63051
Content-Type: multipart/alternative; boundary="alt-63051"

[AQUI LAS DOS PARTES COMPLETAS DEL APARTADO 5]
--mix-63051
Content-Type: application/octet-stream
Content-Disposition: attachment; filename="archivo.bin"
Content-Transfer-Encoding: base64

[BASE64 DEL ARCHIVO]
--mix-63051--
~~~
El bloque alternative incluido termina con --alt-63051-- antes del siguiente separador mix. No pegar los marcadores.
Content-Disposition identifica attachment y nombre sugerido; application/octet-stream es tipo binario genérico.
En terminal normal:
~~~bash
base64 archivo.bin
~~~
Pegar su salida como cuerpo de la parte adjunta. Ni mixed ni alternative se codifican enteros en Base64; se codifican las hojas.

### AUTH LOGIN
Solo si EHLO anuncia LOGIN. En servicios con credenciales reales, negociar TLS antes de autenticar; Base64 no cifra.
Una conexión con STARTTLS puede abrirse con:
~~~bash
openssl s_client -starttls smtp -connect servidor:587 -servername servidor -verify_hostname servidor -verify_return_error -crlf
~~~
s_client abre TLS; -starttls smtp negocia elevación SMTP; -connect selecciona host y puerto; -servername envía SNI; -verify_hostname valida nombre; -verify_return_error aborta verificación fallida; -crlf convierte saltos a CRLF. Reemplazar servidor por el nombre real y disponer de CA confiable.
Tras TLS repetir EHLO. Generar usuario y clave de práctica con:
~~~bash
printf '%s' 'USUARIO_DE_PRACTICA' | base64
printf '%s' 'CLAVE_DE_PRACTICA' | base64
~~~
Diálogo:
~~~text
AUTH LOGIN
BASE64_DEL_USUARIO
BASE64_DE_LA_CLAVE
~~~
Esperar 334 antes de cada valor; 235 indica éxito y 535 fallo. Luego MAIL FROM/RCPT TO/DATA. No pegar marcadores literales.
Esta variante no se ejecutó: el Postfix local no anunció AUTH en el EHLO observado.

## 9. Repetir y cerrar
No se creó un servidor adicional ni se modificaron Postfix/Dovecot. Usar los servicios existentes; consultar systemctl status postfix y systemctl status dovecot si no responden. systemctl consulta/administra servicios; status no modifica. sudo systemctl start NOMBRE inicia el servicio correspondiente si se decide levantarlo.
Las sesiones SMTP y POP3 ya se cerraron con QUIT. No hay un proceso nc pendiente por estas sesiones. Los correos de práctica permanecen en el buzón; no hace falta desinstalar ni detener servicios preexistentes.

## Frase para justificar
“Envío el mensaje como multipart/alternative con texto simple y HTML en Base64, codifico el asunto y verifico por POP3 las dos representaciones, incluida la HTML con negrita.”

## Guardar en la VM
Descargar el archivo, luego:
~~~bash
mkdir -p ~/protos/soluciones
~~~
mkdir crea directorios; -p crea padres faltantes.
~~~bash
cp ~/Downloads/26.r-1.md ~/protos/soluciones/26.r-1.md
~~~
cp copia origen a destino; ~ representa home local.

## Referencias
- [MIME](https://www.rfc-editor.org/rfc/rfc2045)
- [Multipart y alternative](https://www.rfc-editor.org/rfc/rfc2046)
- [Encoded-word](https://www.rfc-editor.org/rfc/rfc2047)
- [POP3](https://www.rfc-editor.org/rfc/rfc1939)

