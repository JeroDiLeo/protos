# LabProtos2026 · Ejercicio 3 · curl acumulativo por SOCKS5

## Qué pide el ejercicio

Desde la workstation, acceder al servidor HTTP `ejercicio3.protos.foo:3126` y seguir las pistas hasta que apruebe el ejercicio. La workstation puede llegar al proxy `proxy.protos.foo:1080`, que a su vez puede llegar al servidor HTTP en la red interna. Las pistas son acumulativas. En cada pedido conservamos los requisitos ya descubiertos y ajustamos lo que indica la última respuesta.

| Componente | Dirección | Función |
|---|---|---|
| Proxy SOCKS5 | `proxy.protos.foo:1080` | Recibe la conexión de curl y abre la conexión hacia el destino. |
| Servidor HTTP | `ejercicio3.protos.foo:3126` | Devuelve las pistas y la aprobación. |
| Ruta de trabajo | `/debugger` | La descubrimos en la primera respuesta HTTP. |

## 1. Entrar por el proxy y leer la redirección

```bash
curl -i -x socks5h://proxy.protos.foo:1080 http://ejercicio3.protos.foo:3126
```

- `-i` muestra los encabezados de la respuesta HTTP y el cuerpo. En este ejercicio las pistas aparecen en ambos.
- `-x` selecciona el proxy. Con `socks5h://`, curl le pasa el nombre del **destino** al proxy para que lo resuelva. La workstation igual tiene que poder encontrar y alcanzar al propio proxy.
- Sin una opción que cambie el método o agregue un cuerpo, este comando hace un GET a `/`.

Con `socks5://`, curl resolvería el nombre del destino en la workstation antes de pedirle la conexión al proxy. Con `socks5h://`, la resolución queda del lado del proxy. Resolución y conectividad son dos pasos distintos. Aunque la workstation pudiera obtener la IP del destino, la consigna indica que la red interna solo es alcanzable desde el proxy.

Salida real

```http
HTTP/1.0 302 Found
Server: ctOS-debugger/0.1 Python/3.12.16
Date: Mon, 09 Nov 2026 20:39:24 GMT
Content-Type: text/plain; charset=utf-8
Content-Length: 109
Location: /debugger
X-Tip-Parcial: el ejercicio es acumulativo asi solo te queda un comando para correr

¡Que bueno que estas aca!

Mi servidor http esta fallando, pero no se como debugearlo.

¿podrias ayudarme?
```

El `302 Found` viene con `Location: /debugger`. Como el valor es un camino relativo al mismo sitio, conservamos el host y el puerto y cambiamos la URL a `http://ejercicio3.protos.foo:3126/debugger`. En la práctica seguimos la redirección a mano, lo que dejó la URL de trabajo explícita para los pedidos siguientes.

## 2. Leer el requisito del legajo

```bash
curl -i -x socks5h://proxy.protos.foo:1080 http://ejercicio3.protos.foo:3126/debugger
```

Salida real

```http
HTTP/1.0 200 OK
Server: ctOS-debugger/0.1 Python/3.12.16
Date: Mon, 09 Nov 2026 20:39:43 GMT
Content-Type: text/plain; charset=utf-8
Content-Length: 98
X-Error_Message: Missing header "X-legajo"

¡Oh wow no sabia que http tenia headers!

Pero parece que aun esta roto

¿donde estan los logs?
```

El código `200 OK` confirma que llegó una respuesta HTTP, pero la pista del ejercicio está en `X-Error_Message`. El servidor espera que **el pedido** incluya `X-legajo`. Para agregarlo usamos `-H "X-legajo: 62815"`, con el legajo de práctica usado en esta sesión.

## 3. Detectar el idioma y pedir español

```bash
curl -i -H "X-legajo: 62815" -x socks5h://proxy.protos.foo:1080 http://ejercicio3.protos.foo:3126/debugger
```

Salida real

```http
HTTP/1.0 200 OK
Server: ctOS-debugger/0.1 Python/3.12.16
Date: Mon, 09 Nov 2026 20:40:25 GMT
Content-Type: text/plain; charset=utf-8
Content-Length: 44
Content-Language: ru

Странно, язык изменился
```

`Content-Language: ru` describe el idioma de la respuesta que recibimos. Para pedir español usamos `Accept-Language: es` en el próximo pedido. Antes hicimos la misma consulta con `-v` para ver cómo viajaba.

```bash
curl -v -H "X-legajo: 62815" -x socks5h://proxy.protos.foo:1080 http://ejercicio3.protos.foo:3126/debugger
```

Extracto de la salida real

```text
*   Trying 172.28.0.40:1080...
* Connected to proxy.protos.foo (172.28.0.40) port 1080 (#0)
* SOCKS5 connect to ejercicio3.protos.foo:3126 (remotely resolved)
* SOCKS5 request granted.
* Connected to proxy.protos.foo (172.28.0.40) port 1080 (#0)
> GET /debugger HTTP/1.1
> Host: ejercicio3.protos.foo:3126
> User-Agent: curl/7.88.1
> Accept: */*
> X-legajo: 62815
>
* HTTP 1.0, assume close after body
< HTTP/1.0 200 OK
< Server: ctOS-debugger/0.1 Python/3.12.16
< Date: Mon, 09 Nov 2026 20:41:00 GMT
< Content-Type: text/plain; charset=utf-8
< Content-Length: 44
< Content-Language: ru
<
Странно, язык изменился
* Closing connection 0
```

Con `-v`, `*` muestra el diagnóstico de la conexión, `>` lo que envía curl y `<` lo que recibe. La línea `remotely resolved` verifica que el nombre del servidor HTTP se resolvió del lado del proxy. La línea `Trying 172.28.0.40:1080` muestra a qué IP y puerto se conectó curl para entrar al proxy. `-i` alcanzaba para seguir leyendo las pistas del servidor.

Ahora sí agregamos la preferencia de idioma.

```bash
curl -i -H "Accept-Language: es" -H "X-legajo: 62815" -x socks5h://proxy.protos.foo:1080 http://ejercicio3.protos.foo:3126/debugger
```

Salida real

```http
HTTP/1.0 200 OK
Server: ctOS-debugger/0.1 Python/3.12.16
Date: Mon, 09 Nov 2026 20:41:25 GMT
Content-Type: text/plain; charset=utf-8
Content-Length: 63

Genial aprece que ya se arreglo el GET

Pero el POST aun falla
```

El cuerpo confirma que el GET quedó resuelto y pide seguir con POST. Eso determina el próximo cambio.

## 4. Probar POST sin cuerpo

```bash
curl -i -X POST -H "Accept-Language: es" -H "X-legajo: 62815" -x socks5h://proxy.protos.foo:1080 http://ejercicio3.protos.foo:3126/debugger
```

`-X POST` cambia el método a POST. Conservamos la ruta, el proxy y los encabezados. En este intento todavía no pasamos datos, para ver qué cuerpo pide el servidor.

Salida real

```http
HTTP/1.0 200 OK
Server: ctOS-debugger/0.1 Python/3.12.16
Date: Mon, 09 Nov 2026 20:44:51 GMT
Content-Type: text/plain; charset=utf-8
Content-Length: 118

Ok ya se que hacer
Llevo semanas desarrollando un fix para todos los problemas
Proba mandar este JSON:

{"fix":"yes"}
```

El servidor ya indicó el cuerpo exacto. En el siguiente pedido vamos a enviar esos datos e indicar que están en JSON.

## 5. Mandar el JSON que pidió el servidor

```bash
curl -i -X POST -H "Accept-Language: es" -H "X-legajo: 62815" -H "Content-Type: application/json" -d '{"fix":"yes"}' -x socks5h://proxy.protos.foo:1080 http://ejercicio3.protos.foo:3126/debugger
```

| Opción agregada | Efecto en el pedido |
|---|---|
| `-d '{"fix":"yes"}'` | Envía el JSON en el cuerpo. Las comillas simples preservan las comillas dobles para que Bash se las pase a curl. |
| `-H "Content-Type: application/json"` | Le indica al servidor cómo interpretar el cuerpo recibido. |

En este comando, `-d` ya seleccionaría POST por defecto. Conservamos `-X POST` para que el método quede explícito, igual que en el paso anterior.

Salida real

```http
HTTP/1.0 401 Unauthorized
Server: ctOS-debugger/0.1 Python/3.12.16
Date: Mon, 09 Nov 2026 20:46:26 GMT
Content-Type: text/plain; charset=utf-8
Content-Length: 126
WWW-Authenticate: Basic realm="sudo"

Ups me olvide de decirte que te falta sudo, no te preocupes te presto mi cuenta, el usuario es admin y la contrasena es admin
```

El `401` y `WWW-Authenticate: Basic` indican que falta autenticación HTTP Basic. `realm="sudo"` es el nombre del área protegida que eligió el servidor. El cuerpo aporta el usuario y la contraseña de práctica. El cambio siguiente es pasárselos a curl con `-u admin:admin`.

## 6. Agregar las credenciales y verificar la aprobación

```bash
curl -i -X POST -H "Accept-Language: es" -H "X-legajo: 62815" -H "Content-Type: application/json" -d '{"fix":"yes"}' -u admin:admin -x socks5h://proxy.protos.foo:1080 http://ejercicio3.protos.foo:3126/debugger
```

`-u` recibe `usuario:contraseña`. Para HTTP Basic, curl codifica ese par en Base64 y construye el encabezado `Authorization: Basic ...` del pedido HTTP. Las credenciales corresponden al servidor HTTP del ejercicio.

Salida real

```http
HTTP/1.0 200 OK
Server: ctOS-debugger/0.1 Python/3.12.16
Date: Mon, 09 Nov 2026 20:47:39 GMT
Content-Type: text/plain; charset=utf-8
Content-Length: 36

¡Te doy el ejercicio por aprobado!
```

## Tabla de consulta rápida

| Pista que veo | Cambio que hago |
|---|---|
| `302` con `Location: /debugger` | Agrego `/debugger` a la URL. |
| `X-Error_Message: Missing header "X-legajo"` | Agrego `-H "X-legajo: 62815"`. |
| `Content-Language: ru` y cuerpo en ruso | Agrego `-H "Accept-Language: es"`. |
| El cuerpo dice que falta arreglar el POST | Agrego `-X POST` y mantengo la ruta. |
| El cuerpo pide `{"fix":"yes"}` | Agrego `-d '{"fix":"yes"}'` y `-H "Content-Type: application/json"`. |
| `401`, `WWW-Authenticate: Basic` y credenciales en el cuerpo | Agrego `-u usuario:contraseña` con los valores del ejercicio. |
| `200 OK` con el texto de aprobación | El servidor confirmó el ejercicio. |

## Variantes de parcial · Cambiar el cuerpo o los encabezados

Estos ejemplos son hipotéticos. En la práctica de arriba, el servidor pidió JSON y aprobó ese pedido. Para una variante, conservá el proxy, la ruta y los requisitos que el servidor ya confirmó. Reemplazá el formato anterior por el nuevo si el servidor te pide otro cuerpo.

### Si el servidor pide que mandes HTML en el POST

Supongamos que el cuerpo de la pista dice «mandá `<p>Hola mundo</p>` como HTML». El cambio afecta dos partes del pedido. El cuerpo pasa a ser el fragmento HTML y su `Content-Type` pasa a ser `text/html`.

```bash
curl -i -X POST \
  -H "Accept-Language: es" \
  -H "X-legajo: 62815" \
  -H "Content-Type: text/html" \
  --data-binary '<p>Hola mundo</p>' \
  -u admin:admin \
  -x socks5h://proxy.protos.foo:1080 \
  http://ejercicio3.protos.foo:3126/debugger
```

- Las comillas simples alrededor del fragmento protegen los signos `<` y `>` de la interpretación de Bash.
- `-H "Content-Type: text/html"` le dice al servidor que el cuerpo contiene HTML.
- En el ejemplo conservamos `-u admin:admin` porque partimos del comando final. Si todavía estás en el paso anterior al `401`, agregá autenticación cuando la pida la variante.

Si la consigna dice «quiero que el servidor **me devuelva** HTML», la opción cambia a `-H 'Accept: text/html'`. `Accept` expresa qué formato de respuesta preferís. `Content-Type` describe el cuerpo del mensaje que lleva ese encabezado. El servidor puede elegir qué formatos de respuesta ofrece. [Manual de curl](https://curl.se/docs/manpage.html#--data-binary) · [RFC 9110 sobre Content-Type y Accept](https://www.rfc-editor.org/rfc/rfc9110.html#section-8.3)

#### Cuándo usar `-d` y cuándo usar `--data-binary`

| Cómo pasás el cuerpo | Qué manda curl |
|---|---|
| `-d '<p>¡Hola, Jerónimo!</p>'` | El fragmento literal, con la tilde incluida en los bytes que recibe de la terminal. |
| `--data-binary '<p>¡Hola, Jerónimo!</p>'` | Los mismos bytes que `-d` para este fragmento. |
| `-d @respuesta.html` | Lee el archivo y quita los retornos de carro, los saltos de línea y los bytes nulos. |
| `--data-binary @respuesta.html` | Lee el archivo y envía todos sus bytes tal cual, incluidos los saltos de línea. |

Para un fragmento corto escrito en el comando, `-d` alcanza. Usá `--data-binary @archivo` si el servidor tiene que recibir el archivo tal cual. Esto sirve también para HTML o texto plano. Las tildes, por sí solas, no obligan a cambiar de opción. [Manual de curl sobre `-d` y `--data-binary`](https://curl.se/docs/manpage.html#--data)

#### Cuándo indicar UTF-8 u otra codificación

En `Content-Type: text/html; charset=UTF-8`, **`text/html` indica el formato y `charset=UTF-8` indica cómo leer sus bytes como caracteres**. Si el texto viene de una terminal o un archivo en UTF-8 y el servidor acepta esa codificación, podés declararla explícitamente. Esto ayuda a interpretar bien letras como `ó` y signos como `¡`.

```bash
-H 'Content-Type: text/html; charset=UTF-8' -d '<p>¡Hola, Jerónimo!</p>'
```

El encabezado solo declara la codificación. Por ejemplo, `é` ocupa los bytes `C3 A9` en UTF-8 y el byte `E9` en ISO-8859-1. Cambiar la etiqueta en el encabezado deja esos bytes intactos. Si la consigna pide **ISO-8859-1** y el archivo original está en UTF-8, primero convertís el archivo y después enviás el resultado con el `charset` correspondiente.

```bash
iconv -f UTF-8 -t ISO-8859-1 respuesta.html > respuesta-latin1.html
```

En el comando `curl` usarías `-H 'Content-Type: text/html; charset=ISO-8859-1' --data-binary @respuesta-latin1.html`. La conversión requiere que los caracteres del archivo se puedan representar en ISO-8859-1.

Si la consigna exige el encabezado exacto `Content-Type: text/html`, usá ese valor. Si pide JSON como en este ejercicio, enviá el cuerpo en UTF-8 con `Content-Type: application/json`. El tipo `application/json` ya tiene definida la codificación para el intercambio abierto y no define un parámetro `charset`. [RFC 9110 sobre tipos de contenido](https://www.rfc-editor.org/rfc/rfc9110.html#section-8.3) · [RFC 8259 sobre codificación de JSON](https://www.rfc-editor.org/rfc/rfc8259.html#section-8.1)

### Si pide otro formato de cuerpo

Aplicá una sola fila según lo que pida el servidor. Conservá las opciones de proxy, la URL y los demás encabezados requeridos.

| Si pide enviar… | Content-Type del pedido | Opción de cuerpo |
|---|---|---|
| JSON con `fix=yes` | `-H 'Content-Type: application/json'` | `-d '{"fix":"yes"}'` |
| Un fragmento HTML | `-H 'Content-Type: text/html'` | `--data-binary '<p>Hola mundo</p>'` |
| Texto plano | `-H 'Content-Type: text/plain'` | `--data-binary 'Hola mundo'` |
| XML | `-H 'Content-Type: application/xml'` | `--data-binary '<fix>yes</fix>'` |
| Campos de formulario URL-encoded | curl usa `application/x-www-form-urlencoded` | `--data-urlencode 'fix=yes' --data-urlencode 'nota=Hola mundo'` |
| Un formulario multipart con archivo | curl genera `multipart/form-data` con su `boundary` | `-F 'fix=yes' -F 'archivo=@respuesta.html;type=text/html'` |
| Un archivo como cuerpo completo | `-H 'Content-Type: application/octet-stream'` si pide binario genérico | `--data-binary @respuesta.bin` |

La diferencia entre las dos últimas filas está en la forma del pedido. Con `-F` el archivo va dentro de un campo del formulario, junto con las otras partes. Con `--data-binary @archivo` el contenido del archivo ocupa todo el cuerpo. En el ejemplo de `-F`, `type=text/html` describe solo la parte del archivo. Dejá que curl genere el `Content-Type` principal y su `boundary`, el separador entre partes. [Manual de curl](https://curl.se/docs/manpage.html) · [Formularios multipart con curl](https://everything.curl.dev/http/post/multipart.html)

### Si cambia un encabezado o aparece una nueva pista

| Pista en la consigna o la respuesta | Qué agrego o cambio |
|---|---|
| «Falta `X-Legajo`», `X-Token`, `Metadata` u otro encabezado propio | `-H 'Nombre: valor'` con el valor exacto que pide el ejercicio. Se usa un `-H` por encabezado. |
| La respuesta viene en otro idioma y pide español | `-H 'Accept-Language: es'`. `Content-Language` te muestra el idioma que vino en la respuesta. |
| «Pedí que responda en JSON» | `-H 'Accept: application/json'`. Para pedir HTML en la respuesta, usá `Accept: text/html`. |
| El backend exige el host virtual `secrethost` en este ejercicio HTTP | `-H 'Host: secrethost'`. La URL y el proxy siguen determinando la conexión. |
| `401` con `WWW-Authenticate: Basic` y te dan credenciales | `-u usuario:contraseña`. `WWW-Authenticate` viene del servidor y curl arma `Authorization` en el pedido. |
| Te dan un token Bearer | `-H 'Authorization: Bearer TOKEN'` con el token de la consigna. |
| Te devuelven `Set-Cookie: winner=true` y te piden reenviar esa cookie | `-b 'winner=true'`. curl la manda como `Cookie: winner=true`. |
| Te exigen un identificador de cliente en `User-Agent` | `-A 'protos-lab/1.0'`, con el valor que te indiquen. |

Usá `-i` para leer las pistas de la respuesta. Si querés verificar qué mandó realmente curl, usá `-v` y mirá las líneas que empiezan con `>`. Un `415 Unsupported Media Type` orienta a revisar el formato del cuerpo y su `Content-Type`. Un `406 Not Acceptable` orienta a revisar las preferencias de respuesta, por ejemplo `Accept` o `Accept-Language`. Un `400 Bad Request` puede tener varias causas. Leé el cuerpo y los encabezados antes de cambiar más de una cosa. [Opciones de curl](https://curl.se/docs/manpage.html) · [Códigos de respuesta HTTP](https://www.rfc-editor.org/rfc/rfc9110.html#section-15)
