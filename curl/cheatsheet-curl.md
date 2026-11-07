# Cheatsheet: curl acumulativo

Para ejercicios donde el servidor pide cosas de a una y hay que terminar con **un solo comando**. Ejercicios resueltos: [curl-ejercicios-paso-a-paso.md](curl-ejercicios-paso-a-paso.md) · PDF: [Guia_curl_acumulativo.pdf](Guia_curl_acumulativo.pdf).

---

## 1. Método (siempre igual)

1. Primer pedido **mirando todo**: `curl -i URL` (o `-v` si querés ver también lo que mandás).
2. Leer las **tres** partes de la respuesta: **código**, **headers** (`Location`, `X-…`, `Set-Cookie`, `WWW-Authenticate`, `Content-Language`, `Allow`) y **cuerpo**.
3. Agregar **una sola** cosa (tablas 3 y 4).
4. Repetir el comando **completo**: no se saca nada de lo anterior.
5. Si el error **cambió**, pasaste el escalón. Si volvió uno anterior, sacaste algo sin querer.
6. Si curl falla **antes** de imprimir `HTTP/…` (`curl: (N) …`), no es un tema de headers: es red, proxy, DNS o TLS (tabla 6).

### Esqueleto del comando final
~~~bash
curl -i \
  -x socks5h://PROXY:1080 \            # si hay proxy
  -X POST \                            # método (si no es GET)
  -u usuario:clave \                   # autenticación
  -A "Mozilla/5.0" \                   # User-Agent
  -H "X-Legajo: 63051" \               # headers propios
  -H "Accept-Language: es" \           # idioma
  -b "cookie=valor" \                  # cookies
  -H "Content-Type: application/json" \
  -d '{"clave":"valor"}' \             # cuerpo
  "http://host:puerto/ruta?param=valor"   # URL entre comillas
~~~
El orden de las opciones no importa; la URL puede ir en cualquier lado (por costumbre, al final). Después de cada `\` no puede haber espacios.

---

## 2. Opciones de curl

### Ver y diagnosticar
| Opción | Qué hace | Cuándo |
|---|---|---|
| `-i` | muestra headers de respuesta + cuerpo | **siempre**: las pistas viajan en headers |
| `-v` | `>` lo que enviás, `<` lo que recibís, `*` info de curl | para comprobar que tu header/cookie/auth **salió**; si el enunciado dice "modo verboso" |
| `-I` | pide solo headers (método **HEAD**) | ver headers rápido. Algunos servers responden distinto a HEAD; si dudás, usá `-i` |
| `-s` | sin barra de progreso | al usar `\|` o `-o` |
| `-o archivo` / `-O` | guarda el cuerpo (con nombre propio / el de la URL) | descargar un archivo, una clave, un binario |
| `-D -` | imprime headers aparte | con `-s -o /dev/null -D -`: solo headers, con GET |
| `-w '%{http_code}\n'` | imprime el código al final | scripts, comparar rápido |
| `--connect-timeout 5` / `-m 10` | límite para conectar / total | que no se quede colgado |

### Ruta, método y redirecciones
| Opción | Qué hace | Cuándo |
|---|---|---|
| (ruta en la URL) | `http://host:puerto/ruta` | el `Location` o el cuerpo te dice otra ruta: **pedila directo** |
| `-L` | sigue solo los `3xx` | opcional: muestra todas las respuestas encadenadas |
| `-X MÉTODO` | `POST`, `PUT`, `DELETE`, `PATCH`, `OPTIONS` | "probá con POST", `405`, "el POST aún falla" |
| `--post301` / `--post302` | con `-L`, mantiene POST tras 301/302 | si usás `-L` con POST (sin esto curl pasa a GET) |
| `"URL?a=1&b=2"` | parámetros de query | "falta el parámetro token". **Comillas siempre** |
| `-G -d 'a=1'` | arma la query con `-d` (GET) | muchos parámetros |
| `-G --data-urlencode 'q=hola mundo'` | query con espacios/símbolos codificados | valores con espacios, `&`, `ñ` |
| `--path-as-is` | no normaliza `../` en la ruta | "path traversal", la pista dice `/../secreto` |
| `-g` | no interpreta `[]` `{}` en la URL | URL con corchetes (o IPv6 sin escapar) |

### Headers (petición)
| Opción | Arma el header | Cuándo |
|---|---|---|
| `-H "Nombre: valor"` | cualquiera | header propio (`X-…`) o estándar |
| `-A "Mozilla/5.0"` | `User-Agent:` | `403` "solo navegadores", "cliente no soportado" |
| `-e URL` | `Referer:` | "venís de otra página", "acceso solo desde /panel" |
| `-H "Nombre;"` | header **vacío** | piden un header presente pero sin valor |
| `-H "Nombre:"` | **borra** un header que curl pone solo | ej. `-H "User-Agent:"`, `-H "Accept:"` |

### Cuerpo
| Opción | Qué manda | Cuándo |
|---|---|---|
| `-d 'a=1&b=2'` | formulario (`application/x-www-form-urlencoded`), implica POST | "mandá usuario y clave por formulario" |
| `-H "Content-Type: application/json" -d '{"k":"v"}'` | JSON | "mandá este JSON". Comillas **simples** afuera, dobles adentro |
| `--json '{"k":"v"}'` | JSON + `Content-Type` y `Accept` json (curl ≥ 7.82) | atajo del anterior |
| `-d @archivo` / `--data-binary @archivo` | cuerpo desde archivo (`--data-binary` conserva saltos de línea) | cuerpo largo o binario |
| `-F 'campo=valor' -F 'archivo=@foto.png'` | `multipart/form-data`, implica POST | "subí un archivo", formulario con archivo |
| `-T archivo` | sube con **PUT** | "subí el archivo con PUT" |
| `-d ''` | POST con cuerpo vacío (manda `Content-Length: 0`) | `411 Length Required` |

### Autenticación
| Opción | Qué hace | Cuándo |
|---|---|---|
| `-u user:clave` | Basic (`Authorization: Basic base64(user:clave)`) | `401` + `WWW-Authenticate: Basic` |
| `-u user:clave --digest` | Digest | `401` + `WWW-Authenticate: Digest` |
| `-H "Authorization: Bearer TOKEN"` (o `--oauth2-bearer TOKEN`) | token | `401` + `WWW-Authenticate: Bearer`, "usá el token que te dio /login" |
| `-H "X-API-Key: K"` | API key en header | "falta la API key" (el nombre lo dice el server) |
| `http://user:clave@host/` | Basic en la URL | equivalente a `-u` |
| `-u user` (sin clave) | curl pide la clave sin mostrarla | si no querés que quede en el historial |

### Cookies
| Opción | Qué hace | Cuándo |
|---|---|---|
| `-b "a=1; b=2"` | manda `Cookie:` | la respuesta trajo `Set-Cookie: a=1` |
| `-c archivo` | guarda las `Set-Cookie` recibidas | login que te da sesión |
| `-b archivo` | manda las cookies guardadas | siguiente pedido de la sesión |
| `-L -c c.txt -b c.txt` | guarda y reenvía en un solo comando | server pone cookie y redirige |

`-b` con `=` es una cookie literal; sin `=` es un archivo.

### Llegar al servidor
| Opción | Qué hace | Cuándo |
|---|---|---|
| `-x socks5h://IP:1080` | proxy SOCKS5, **el proxy** resuelve el nombre | "solo accesible por proxy SOCKS", nombre interno |
| `-x socks5://IP:1080` | SOCKS5, **tu máquina** resuelve | solo si te piden `socks5` y tenés la IP |
| `-x http://IP:3128` | proxy HTTP | "proxy HTTP/web" (3128, 8080) |
| `-x socks5h://user:clave@IP:1080` o `--proxy-user u:c` | proxy con login | `407`, "el proxy pide credenciales" |
| `--resolve nombre:puerto:IP` | fija nombre → IP sin tocar `/etc/hosts` | vhost por nombre, nombre que tu DNS no conoce |
| `-H "Host: nombre"` + URL con IP | cambia el `Host` | "virtual host", misma IP sirve otro sitio |
| `--connect-to nombre:80:IP:8080` | redirige la conexión, conserva nombre | nombre real pero el server está en otro puerto/IP |
| `http://[::1]:8080/` | IPv6 entre corchetes | dirección IPv6 |
| `-4` / `-6` | fuerza IPv4 / IPv6 | "solo responde por IPv6" |
| `-k` | ignora certificado TLS inválido | `https` con certificado propio (`curl: (60)`) |
| `--http1.0` / `--http2` | versión de HTTP | "el servidor solo habla HTTP/1.0" |
| `--compressed` | pide gzip y lo descomprime | cuerpo ilegible, `Content-Encoding: gzip` |
| `-r 0-99` | `Range: bytes=0-99` | "pedí solo los primeros 100 bytes" (`206`) |

SSH como proxy (si te dan acceso SSH a una máquina que sí llega):
~~~bash
ssh -D 1080 user@salto        # SOCKS local → curl -x socks5h://127.0.0.1:1080 URL
ssh -L 8080:destino:80 user@salto   # túnel → curl http://127.0.0.1:8080/
~~~

---

## 3. Lo que dice el enunciado → qué agregar

| El enunciado dice… | Agregás |
|---|---|
| "solo accesible por proxy SOCKS en X:1080", "la red no rutea" | `-x socks5h://X:1080` |
| "proxy HTTP en X:3128" | `-x http://X:3128` |
| "el ejercicio es acumulativo", "un solo comando" | repetir todo cada vez; entregar el último |
| "usá el modo verboso" | `-v` |
| "con su legajo" / "identifíquese" | `-H "X-Legajo: <tu legajo>"` (o el header que diga) |
| "en castellano/español" | `-H "Accept-Language: es"` |
| "como un navegador", "Firefox/Chrome" | `-A "Mozilla/5.0 ..."` |
| "en formato JSON" (que **te** devuelva JSON) | `-H "Accept: application/json"` |
| "mandale este JSON" | `-H "Content-Type: application/json" -d '{…}'` |
| "complete el formulario" | `-d 'campo=valor&campo2=valor'` |
| "suba el archivo X" | `-F 'archivo=@X'` (o `-T X` si dice PUT) |
| "usuario X, contraseña Y" | `-u X:Y` |
| "sin modificar /etc/hosts" con un nombre | `--resolve nombre:puerto:IP` o `-H "Host: nombre"` |
| "el host virtual X" | `-H "Host: X"` |
| "contenido comprimido" | `--compressed` |
| "venga desde la página Z" | `-e Z` |
| "desde la red interna / IP 10.x" | `-H "X-Forwarded-For: 10.x.x.x"` (si el server confía en ese header) |
| "https con certificado autofirmado" | `-k` |
| "guarde la respuesta en un archivo" | `-o archivo` |
| "solo las opciones estrictamente necesarias" | sacá `-v`, `-L`, `-X POST` redundante; dejá lo que cambia la respuesta |

---

## 4. Lo que responde el servidor → qué agregar

| Ves… | Significa | Agregás |
|---|---|---|
| `301`/`302`/`303`/`307`/`308` + `Location: /x` | está en otro lado | pedir `/x` directo (o `-L`) |
| `Location: http://otro:puerto/x` | otro host/puerto | cambiar la URL entera |
| ruta en el **cuerpo** ("andá a /win") | — | cambiar la URL a mano (`-L` no la sigue) |
| `400` + "falta header X" / `X-Error-Message: Missing header "X"` | falta un header | `-H "X: valor"` |
| `400` + "falta el parámetro p" | falta query | `"URL?p=valor"` |
| `400` + "JSON inválido" | cuerpo mal formado | revisar comillas: `-d '{"k":"v"}'` |
| `401` + `WWW-Authenticate: Basic realm="…"` | falta login Basic | `-u user:clave` |
| `401` + `WWW-Authenticate: Digest` | login Digest | `-u user:clave --digest` |
| `401` + `WWW-Authenticate: Bearer` | token | `-H "Authorization: Bearer TOKEN"` |
| `403` "solo navegadores" | mira tu `User-Agent` (`curl/8.x`) | `-A "Mozilla/5.0"` |
| `403` "solo desde la red interna / localhost" | mira tu IP | `-H "X-Forwarded-For: 127.0.0.1"` o `X-Real-IP`, o ir por proxy/túnel |
| `403` "acceso solo desde /panel" | mira `Referer` | `-e http://host/panel` |
| `403` "token incorrecto" | llegó el parámetro con otro valor | revisar el valor (espacios, `token=token=`) |
| `404` "Cannot POST /" | ruta no existe **para ese método** | cambiar la ruta (la del GET) |
| `405 Method Not Allowed` + `Allow: GET, PUT` | método equivocado | `-X` con uno de los de `Allow` |
| `406` + "prefiero español" | idioma | `-H "Accept-Language: es"` |
| `406` + "formato no soportado" | tipo de respuesta | `-H "Accept: application/json"` (o el que diga) |
| `407 Proxy Authentication Required` | el **proxy** pide login | `-x proto://user:clave@IP:P` o `--proxy-user` |
| `411 Length Required` | POST sin cuerpo ni longitud | `-d ''` |
| `415 Unsupported Media Type` | `Content-Type` del cuerpo incorrecto | `-H "Content-Type: application/json"` |
| `418 I'm a teapot` | broma del servidor | **leer el cuerpo y los headers**: ahí está la pista |
| `429 Too Many Requests` + `Retry-After: N` | demasiados pedidos | esperar N segundos |
| `Content-Language: ru` (idioma raro) | te respondió en otro idioma | `-H "Accept-Language: es"` |
| `Content-Encoding: gzip` / cuerpo ilegible | comprimido | `--compressed` |
| `Set-Cookie: a=b` | quiere que la devuelvas | `-b "a=b"` |
| `X-Pista` / `X-Tip` / `X-Hint: dG9r…` | pista codificada | decodificar (sección 8) |
| `Vary: Accept-Language` | la respuesta cambia según ese header | jugar con ese header |
| `ETag` / `Last-Modified` + "¿cambió?" | caché condicional | `-H 'If-None-Match: "etag"'` → `304` |
| cuerpo JSON con `"token": "…"` | te dio un token | usarlo en el siguiente pedido (Bearer, header o query) |

---

## 5. Códigos HTTP

| Código | Nombre | Qué significa | Qué hacer |
|---|---|---|---|
| `200` | OK | salió bien | leer el cuerpo: ¿es el final o otra pista? |
| `201` | Created | creó el recurso (POST/PUT) | — |
| `204` | No Content | OK sin cuerpo | mirar headers |
| `206` | Partial Content | devolvió un rango (`-r`) | — |
| `301` | Moved Permanently | movido para siempre | ruta del `Location` |
| `302` | Found | redirección temporal | ruta del `Location` |
| `303` | See Other | "andá a ver esto con GET" | GET a `Location` |
| `304` | Not Modified | no cambió (pediste con `If-None-Match`/`If-Modified-Since`) | ya tenés la versión vigente |
| `307` / `308` | Temporary / Permanent Redirect | como 302/301 pero **conserva el método** | repetir el mismo método en `Location` |
| `400` | Bad Request | al pedido le falta algo o está mal | leer cuerpo y headers `X-…` |
| `401` | Unauthorized | falta autenticarte | ver `WWW-Authenticate` → `-u` / `--digest` / Bearer |
| `403` | Forbidden | sabe quién sos y no te deja | cambiar identidad: UA, IP, Referer, token |
| `404` | Not Found | no existe (esa ruta o ese método) | revisar ruta, mayúsculas, `/` final, método |
| `405` | Method Not Allowed | método no permitido | header `Allow` → `-X` |
| `406` | Not Acceptable | no puede darte lo que pedís en `Accept-*` | ajustar `Accept` / `Accept-Language` |
| `407` | Proxy Auth Required | el proxy pide credenciales | credenciales en `-x` |
| `408` | Request Timeout | tardaste en mandar | reintentar |
| `409` | Conflict | choca con el estado actual | leer cuerpo |
| `410` | Gone | ya no existe | buscar la nueva ruta en pistas |
| `411` | Length Required | falta `Content-Length` | `-d ''` |
| `412` / `428` | Precondition Failed / Required | condiciones `If-*` | `If-Match` / `If-None-Match` con el ETag |
| `413` | Payload Too Large | cuerpo muy grande | mandar menos |
| `414` | URI Too Long | URL muy larga | pasar datos al cuerpo (`-d`) |
| `415` | Unsupported Media Type | tipo de cuerpo no aceptado | `Content-Type` correcto |
| `416` | Range Not Satisfiable | rango fuera del archivo | ajustar `-r` |
| `418` | I'm a teapot | broma | leer pista |
| `426` | Upgrade Required | pide otro protocolo | ver header `Upgrade` (ej. `--http2`, https) |
| `429` | Too Many Requests | rate limit | esperar `Retry-After` |
| `431` | Header Fields Too Large | headers demasiado grandes | revisar cookies/headers repetidos |
| `451` | Unavailable For Legal Reasons | bloqueado | — |
| `500` | Internal Server Error | el server falló (a veces por tu cuerpo mal formado) | revisar el cuerpo/JSON |
| `501` | Not Implemented | método desconocido | otro método |
| `502` | Bad Gateway | el proxy/nginx no pudo hablar con el backend | backend caído / mal configurado |
| `503` | Service Unavailable | sobrecargado o en mantenimiento | `Retry-After`, reintentar |
| `504` | Gateway Timeout | el backend no respondió a tiempo | backend lento o inalcanzable |

Regla rápida: **4xx = arreglás vos el pedido**, **5xx = problema del servidor** (o del backend detrás de un proxy), **3xx = andá a otro lado**.

---

## 6. Errores de curl (antes de que haya HTTP)

| Error | Significa | Qué hacer |
|---|---|---|
| `(1) Unsupported protocol` | esquema mal escrito (`htp://`) | corregir el esquema |
| `(1) Received HTTP/0.9 when not allowed` | le hablaste HTTP a algo que no es HTTP (ej. al proxy SOCKS como URL) | el proxy va en `-x`; la URL es el destino |
| `(3) URL malformed` | URL rota (espacios, falta `http://`) | comillas, revisar la URL |
| `(5) Could not resolve proxy` | no resuelve el nombre del proxy | IP del proxy o DNS |
| `(6) Could not resolve host` | tu máquina no conoce el nombre | ¿falta `-x`? usar `socks5h`, `--resolve`, `dig` |
| `(7) Failed to connect / Connection refused` | llegás a la IP pero no hay nada en ese puerto | puerto equivocado o servicio caído |
| `(7) No route to host` | no llegás a esa red | proxy/túnel, ruta |
| `(28) Timed out` | nadie responde (firewall, red) | proxy/túnel, IP correcta |
| `(35) SSL connect error` | falló el TLS (ej. `https://` a un puerto http) | revisar esquema/puerto |
| `(47) Maximum redirects` | bucle de redirecciones | ver la cadena con `-v`; tal vez falta una cookie |
| `(52) Empty reply from server` | conectó y cerró sin responder | protocolo equivocado (http vs https), proxy |
| `(56) Recv failure: Connection reset` | el otro lado cortó | protocolo equivocado, proxy |
| `(60) SSL certificate problem` | certificado no confiable | `-k` (o `--cacert`) |
| `(97) Could not resolve host` (con proxy) | usaste `socks5://` y tu máquina no conoce el nombre | `socks5h://` |
| `(97) … SOCKS` / handshake failed | el proxy no es SOCKS o rechazó | probar `-x http://…`, revisar puerto/credenciales |

---

## 7. Headers de petición (qué hace cada uno)

| Header | Opción | Para qué | Pista típica |
|---|---|---|---|
| `Host` | automático / `-H` / `--resolve` | qué sitio pedís en esa IP (vhost) | "host virtual", nginx `server_name` |
| `User-Agent` | `-A` | qué cliente sos | `403` navegadores |
| `Accept` | `-H` | formato que aceptás (`application/json`, `text/html`) | `406` formato |
| `Accept-Language` | `-H` | idioma que querés (`es`, `es-AR`, `en;q=0.5`) | `406`, `Content-Language` raro |
| `Accept-Encoding` | `--compressed` | compresión que aceptás | gzip |
| `Content-Type` | `-H` | formato del cuerpo que **mandás** | `415`, "mandá JSON" |
| `Content-Length` | automático con `-d` | tamaño del cuerpo | `411` |
| `Authorization` | `-u`, `--digest`, `-H "…Bearer…"` | credenciales | `401` |
| `Cookie` | `-b` | devolver cookies | `Set-Cookie` previo |
| `Referer` | `-e` | de qué página venís | "solo desde /panel" |
| `Origin` | `-H` | origen (CORS) | "solo desde http://sitio" |
| `X-Forwarded-For` / `X-Real-IP` | `-H` | IP "original" del cliente detrás de un proxy | "solo red interna" |
| `X-Requested-With: XMLHttpRequest` | `-H` | simula pedido AJAX | "solo pedidos AJAX" |
| `If-None-Match` / `If-Modified-Since` | `-H` | pedido condicional | `ETag`, `304` |
| `Range` | `-r` | parte del recurso | `206` |
| `Cache-Control: no-cache` | `-H` | saltear caché | respuesta vieja |
| `X-Algo` (propio) | `-H` | lo que invente el servidor | `400 Missing header` |

**`Content-*` describe lo que mandás / recibís; `Accept-*` es lo que pedís.** Para pedir español no mandes `Content-Language`: mandá `Accept-Language`.

## Headers de respuesta donde vienen las pistas
`Location` (adónde ir) · `Set-Cookie` (qué devolver) · `WWW-Authenticate` (qué auth) · `Allow` (qué métodos) · `Content-Language` (en qué idioma te respondió) · `Content-Type` (qué formato) · `Content-Encoding` (comprimido) · `Retry-After` · `ETag` · `Vary` (de qué header depende) · cualquier `X-…` (`X-Pista`, `X-Tip-Parcial`, `X-Error-Message`).

---

## 8. Decodificar pistas

| Cómo se ve | Es | Comando |
|---|---|---|
| letras, números, `+ /`, termina en `=`/`==`, largo múltiplo de 4 | base64 | `echo 'dG9rZW4=' \| base64 -d` |
| igual pero con `-` y `_` | base64url | `echo 'xx' \| tr '_-' '/+' \| base64 -d` |
| solo `0-9a-f`, largo par | hex | `echo '746f6b656e' \| xxd -r -p` (sin xxd: `python3 -c "print(bytes.fromhex('746f6b656e').decode())"`) |
| `%20`, `%C3%B1` | URL encoding | `python3 -c "import urllib.parse;print(urllib.parse.unquote('a%20b'))"` |
| letras "corridas" (`gbxra`) | ROT13 | `echo 'gbxra' \| tr 'A-Za-z' 'N-ZA-Mn-za-m'` |
| `=?UTF-8?B?…?=` | encoded-word MIME | decodificar lo del medio con base64 |
| tres partes con puntos `eyJ…` | JWT | `echo 'parte2' \| base64 -d` (el payload) |

Si lo decodificado tiene forma `nombre=valor` (ej. `token=zarigueya`), ya es el parámetro completo: va después del `?` tal cual.

Leer un campo de un JSON de respuesta: `curl -s URL | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])"` (o `jq -r .token`).

---

## 9. Errores de shell que rompen el comando

| Síntoma | Causa | Arreglo |
|---|---|---|
| la URL con `&` sale cortada, "[1] 12345" | `&` sin comillas manda a segundo plano | URL entre comillas dobles |
| `zsh: no matches found` / pedido raro con `?` | `?` es comodín | comillas |
| el JSON llega roto | comillas dobles afuera | `-d '{"k":"v"}'` (simples afuera) |
| un `-H` no aparece en `-v` | espacio después de `\` o línea cortada | sin espacios después de `\` |
| `-A` no se aplica | `-a` en minúscula (es otra opción) | `-A` |
| sale `X-Legajo:63051` sin espacio | no importa, HTTP lo acepta; pero respetá el nombre exacto | — |
| `$VAR` vacío dentro de `'…'` | las simples no expanden | comillas dobles si querés variables |

Comprobar qué salió de verdad: `-v` y mirar las líneas `>`.

---

## 10. Hacerlo acumulativo (receta)

~~~bash
# 1) arrancar
curl -i "http://H:P/"
# 2) 302 Location: /x            → cambiar la ruta
curl -i "http://H:P/x"
# 3) 403 navegadores             → + -A
curl -i -A "Mozilla/5.0" "http://H:P/x"
# 4) 400 falta X-Legajo          → + -H
curl -i -A "Mozilla/5.0" -H "X-Legajo: 63051" "http://H:P/x"
# 5) 406 / idioma raro           → + Accept-Language
curl -i -A "Mozilla/5.0" -H "X-Legajo: 63051" -H "Accept-Language: es" "http://H:P/x"
# 6) "hacé un POST"              → + -X POST
# 7) "mandá este JSON"           → + -H "Content-Type: application/json" -d '{…}'
# 8) 401 Basic                   → + -u user:clave
# 9) Set-Cookie: a=b             → + -b "a=b"
# 10) falta parámetro / X-Pista  → URL "…/x?token=valor"
~~~
Cada línea es la anterior **más una cosa**. El último comando es la respuesta.

### Qué decir en el video
«Con `-i` leo código, headers y cuerpo de cada respuesta; cada vez agrego al mismo comando lo que el servidor pidió (ruta, User-Agent, header propio, idioma, método, cuerpo, credenciales, cookie, parámetro) hasta que responde 200 con el resultado final.»
