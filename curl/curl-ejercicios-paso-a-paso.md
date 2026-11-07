# curl acumulativo: tres ejercicios resueltos paso a paso

Los tres ejercicios tienen el mismo patrón: **el servidor responde algo, esa respuesta dice qué le falta al pedido, y vos agregás una sola cosa al comando**. En cada paso vas a ver (1) el comando completo, (2) lo que imprime, (3) cómo leerlo y (4) por qué el comando siguiente agrega lo que agrega. Cada comando conserva todo lo del anterior.

Versión para leer con diseño, más 24 variantes y autoevaluación: [Guia_curl_acumulativo.pdf](Guia_curl_acumulativo.pdf). Receta del parcial real del 1C 2026: [socks5h-acumulativo_1c2026.md](socks5h-acumulativo_1c2026.md).

## Antes de empezar

### Las opciones de curl que se usan
| Opción | Qué hace |
|---|---|
| `-i` | imprime los headers de la **respuesta** antes del cuerpo (ahí están las pistas) |
| `-v` | modo verboso: `>` = lo que enviás, `<` = lo que recibís, `*` = info de curl |
| `-L` | sigue las redirecciones (`3xx` + `Location`) |
| `-H "Nombre: valor"` | agrega un header a la petición |
| `-X POST` | cambia el método HTTP |
| `-d 'texto'` | manda un cuerpo (y ya implica POST) |
| `-u user:clave` | autenticación HTTP Basic |
| `-b "a=b"` / `-b archivo` | manda una cookie / las cookies de un archivo |
| `-A "texto"` | fija el header `User-Agent` |
| `-x socks5h://IP:PUERTO` | pasa por un proxy SOCKS5 que resuelve el nombre |

### Cómo se lee un código de estado
| Código | Significa | Qué hacer |
|---|---|---|
| `302` + `Location: /x` | te mandan a otra ruta | pedir `/x` (o `-L`) |
| `400` | al pedido le falta algo | leer headers/cuerpo: dicen qué |
| `401` + `WWW-Authenticate` | falta autenticarte | `-u user:clave` |
| `403` | te rechazan por quién sos | cambiar `User-Agent` u otro header de identidad |
| `404` | esa ruta/método no existe | revisar la ruta o el método |
| `406` | no pueden darte lo que aceptás | revisar `Accept-Language` / `Accept` |
| `418` | (humor del servidor) leé el cuerpo, trae la pista | — |
| `200` | funcionó | — |

Si curl falla **antes** de imprimir `HTTP/1.1 ...` (por ejemplo `curl: (6)`, `(7)`, `(97)`), no es un problema de headers: es red, proxy o DNS.

> **Sobre las salidas:** las líneas `Server:` y `Date:` se omiten para acortar. Las salidas del Ej 3 son del lab real (`bash lab/lab-protos.sh tesoro`). Las de los Ej 1 y 2 se obtuvieron de un servidor de práctica que replica lo que respondió el de la cátedra; los textos largos del cuerpo del servidor real aparecen resumidos con `...`.

---

# Ejercicio 1 — Reparar `/debugger`

## Enunciado
> El servidor `http` en `192.168.0.238` puerto `2604` necesita ser depurado. Utilizando `curl`, conseguí que el servidor dé el ejercicio por aprobado. **Pista del servidor:** el ejercicio es acumulativo: al final tenés que dejar **un solo comando curl** que reúna todo lo que fue pidiendo.
>
> Datos: servidor `192.168.0.238:2604` · tu legajo (en la práctica: `63051`; en el examen, el tuyo) · usuario/clave que aparezcan en las respuestas.


### Paso 1 — Primer pedido: mirar los headers

**Comando:**

~~~bash
curl -i http://192.168.0.238:2604
~~~

**Lo que muestra:**

~~~text
HTTP/1.1 302 Found
Location: /debugger
X-Tip-Parcial: El ejercicio es acumulativo...
Content-Type: text/plain; charset=utf-8
Content-Length: 36

El servidor necesita ser depurado...
~~~

**Cómo leerlo:** `302 Found` es una redirección y `Location: /debugger` dice adónde ir. El header `X-Tip-Parcial` avisa que el ejercicio es acumulativo (hay que terminar con un solo comando). curl **no** sigue redirecciones por sí solo: te muestra la respuesta de `/` y listo.

**Por qué el próximo comando agrega eso:** la pista está en `Location`: pedimos directamente esa ruta, `/debugger`. (No hace falta ninguna opción nueva; ver la nota sobre `-L` más abajo.)

### Paso 2 — Ir a la ruta que indicó el Location

**Comando:**

~~~bash
curl -i http://192.168.0.238:2604/debugger
~~~

**Lo que muestra:**

~~~text
HTTP/1.1 400 Bad Request
X-Error-Message: Missing header "X-Legajo"
Content-Type: text/plain; charset=utf-8
Content-Length: 25

¿Dónde están los logs?
~~~

**Cómo leerlo:** Llegamos a `/debugger`, pero responde `400 Bad Request` y el header `X-Error-Message` dice exactamente qué falta: el header `X-Legajo`. La frase "¿Dónde están los logs?" es relato; la pista útil es el header de error.

**Por qué el próximo comando agrega eso:** agregamos el header que pide, con `-H "X-Legajo: 63051"` (nombre, dos puntos, espacio, valor).

### Paso 3 — Identificarse con el legajo

**Comando:**

~~~bash
curl -i \
  -H "X-Legajo: 63051" \
  http://192.168.0.238:2604/debugger
~~~

**Lo que muestra:**

~~~text
HTTP/1.1 418 I'm a Teapot
Content-Language: ru
Content-Type: text/plain; charset=utf-8
Content-Length: 43

Странно, язык изменился
~~~

**Cómo leerlo:** Pasó el `400`: el servidor ya reconoce el legajo. Ahora responde `418` con `Content-Language: ru` y un texto en ruso ("qué raro, el idioma cambió"). `Content-Language` **describe** el idioma de lo que recibiste; no es algo que le mandes vos.

**Por qué el próximo comando agrega eso:** el idioma se **pide** con `Accept-Language`. Agregamos `-H "Accept-Language: es"`. (`Content-*` describe el contenido; `Accept-*` es lo que pedís.)

### Paso 4 — Pedir español

**Comando:**

~~~bash
curl -i \
  -H "X-Legajo: 63051" \
  -H "Accept-Language: es" \
  http://192.168.0.238:2604/debugger
~~~

**Lo que muestra:**

~~~text
HTTP/1.1 200 OK
X-Tip-Parcial: Hacé un POST al mismo endpoint _sin body_
Content-Language: es
Content-Type: text/plain; charset=utf-8
Content-Length: 67

Genial, parece que ya se arregló el GET
Pero el POST aún falla...
~~~

**Cómo leerlo:** `200 OK`, `Content-Language: es`: el GET ya anda. El cuerpo dice que el POST aún falla y `X-Tip-Parcial` da la instrucción: hacer un **POST al mismo endpoint, sin body**.

**Por qué el próximo comando agrega eso:** agregamos `-X POST`. Ojo con *cuál* endpoint: el mismo donde anduvo el GET, `/debugger`, y no la raíz (se ve en el paso siguiente).

### Paso 5a — POST a la raíz (falla)

**Comando:**

~~~bash
curl -i -X POST \
  -H "X-Legajo: 63051" \
  -H "Accept-Language: es" \
  http://192.168.0.238:2604
~~~

**Lo que muestra:**

~~~text
HTTP/1.1 404 Not Found
Content-Type: text/plain; charset=utf-8
Content-Length: 13

Cannot POST /
~~~

**Cómo leerlo:** `404 Not Found`, `Cannot POST /`. La redirección de `/` a `/debugger` era para el GET; para POST no existe `/`, así que no hay a dónde ir. "El mismo endpoint" era `/debugger`, la ruta donde anduvo el GET.

**Por qué el próximo comando agrega eso:** mismo comando, pero apuntando directamente a `/debugger`.

### Paso 5b — POST sin cuerpo a la ruta correcta

**Comando:**

~~~bash
curl -i -X POST \
  -H "X-Legajo: 63051" \
  -H "Accept-Language: es" \
  http://192.168.0.238:2604/debugger
~~~

**Lo que muestra:**

~~~text
HTTP/1.1 418 I'm a Teapot
Content-Type: text/plain; charset=utf-8
Content-Length: 41

Probá mandarle este JSON:
{"fix": "yes"}
~~~

**Cómo leerlo:** Llegó: `418` y el cuerpo pide un JSON: `{"fix": "yes"}`. Lo único que cambió respecto del 5a fue la ruta.

**Por qué el próximo comando agrega eso:** hay que mandar ese cuerpo. `-d` envía el cuerpo y hay que **declarar su formato** con `Content-Type: application/json` (si no, curl declara `application/x-www-form-urlencoded`).

### Paso 6 — Enviar el JSON

**Comando:**

~~~bash
curl -i -X POST \
  -H "X-Legajo: 63051" \
  -H "Accept-Language: es" \
  -H "Content-Type: application/json" \
  -d '{"fix": "yes"}' \
  http://192.168.0.238:2604/debugger
~~~

**Lo que muestra:**

~~~text
HTTP/1.1 401 Unauthorized
Content-Type: text/plain; charset=utf-8
Content-Length: 70

Necesitás ser sudo. El usuario es admin, y la contraseña es admin...
~~~

**Cómo leerlo:** `401 Unauthorized`: el JSON fue aceptado y ahora falta autenticación. El cuerpo da las credenciales: usuario `admin`, contraseña `admin` ("necesitás ser sudo" es parte del relato, no tiene que ver con permisos de Linux). Las comillas simples alrededor del JSON son de la shell: protegen las dobles y no viajan.

**Por qué el próximo comando agrega eso:** `-u admin:admin` arma el header `Authorization: Basic ...` (base64 de `admin:admin`, que **no cifra**).

### Paso 7 — Comando final (el que aprueba)

**Comando:**

~~~bash
curl -i -X POST \
  -u admin:admin \
  -H "X-Legajo: 63051" \
  -H "Accept-Language: es" \
  -H "Content-Type: application/json" \
  -d '{"fix": "yes"}' \
  http://192.168.0.238:2604/debugger
~~~

**Lo que muestra:**

~~~text
HTTP/1.1 200 OK
Content-Type: text/plain; charset=utf-8
Content-Length: 36

... te doy el ejercicio por aprobado
~~~

**Cómo leerlo:** `200 OK`: el servidor da el ejercicio por aprobado. Este es el **único comando** que reúne todo lo que fue pidiendo.

### Nota: ¿y `-L`?
`-L` hace que curl **siga solo** las redirecciones (`3xx` + `Location`). Acá no hizo falta porque pedimos directamente la ruta que indicaba el `Location`. Con `curl -i -L http://192.168.0.238:2604` hubieras visto las dos respuestas seguidas (el `302` de `/` y el `400` de `/debugger`), y agregarlo a los comandos de arriba no los rompe. Cuidado: con un **POST**, si el servidor responde `301`/`302`, curl al seguir la redirección lo convierte en **GET** (para mantener el POST: `--post301` / `--post302`). Por eso conviene pedir directo la URL final.


### Qué hace cada pieza del comando final
| Pieza | Para qué |
|---|---|
| `-i` | ver headers de respuesta (donde estaban las pistas) |
| `-X POST` | pedir POST; con `-d` es redundante, pero el servidor lo pidió aparte |
| `-u admin:admin` | Basic auth (paso 6) |
| `-H "X-Legajo: 63051"` | identificación (paso 3) |
| `-H "Accept-Language: es"` | idioma español (paso 4) |
| `-H "Content-Type: application/json"` | declara que el cuerpo es JSON |
| `-d '{"fix": "yes"}'` | el cuerpo que pidió el servidor |
| `.../debugger` | ruta final del POST |

**Un fallo que puede aparecer:** `curl: (7) Failed to connect ... Couldn't connect to server`. Pasa **antes** de tener respuesta HTTP, así que no es un `400`/`401`/`404` ni significa que los headers estén mal: el servidor estaba caído un momento. `--connect-timeout 5` evita esperar de más.

---

# Ejercicio 2 — El juego de Alzara

## Enunciado
> En `192.168.0.238` puerto `2504` hay un juego de tres desafíos. Superalos usando `curl`. **Pista del servidor:** usá el modo verboso (`-v`).
>
> Datos: servidor `192.168.0.238:2504`.


### Paso 1 — Entrada al juego

**Comando:**

~~~bash
curl -i http://192.168.0.238:2504
~~~

**Lo que muestra:**

~~~text
HTTP/1.1 302 Found
Location: /translation
Content-Type: text/plain; charset=utf-8
Content-Length: 50

Supera los 3 desafíos...
... usa el modo verboso.
~~~

**Cómo leerlo:** `302` con `Location: /translation`. El cuerpo avisa que son 3 desafíos y sugiere el modo verboso.

**Por qué el próximo comando agrega eso:** vamos a la ruta del `Location` y usamos `-v` para ver lo que se envía y lo que se recibe.

### Paso 2 — Ir a /translation en modo verboso

**Comando:**

~~~bash
curl -v http://192.168.0.238:2504/translation
~~~

**Lo que muestra:**

~~~text
> GET /translation HTTP/1.1
> Host: 192.168.0.238:2504
> User-Agent: curl/8.5.0
> Accept: */*
> 
< HTTP/1.1 404 Not Found
< Content-Language: en
< Content-Type: text/plain; charset=utf-8
< Content-Length: 76
< 
Great, you have passed the first challenge.
... the spanish (es) version ...
~~~

**Cómo leerlo:** Con `-v`: las líneas `>` son lo que **enviás**, las `<` lo que **recibís**; el cuerpo aparece sin prefijo. Responde `404` con `Content-Language: en`. El cuerpo, en inglés, felicita (primer desafío superado) y orienta a pedir la versión en español (`es`). Es un 404 de la versión inglesa, no una ruta mal escrita.

**Por qué el próximo comando agrega eso:** el idioma se pide con `Accept-Language: es`.

### Paso 3 — Pedir español

**Comando:**

~~~bash
curl -v \
  -H "Accept-Language: es" \
  http://192.168.0.238:2504/translation
~~~

**Lo que muestra:**

~~~text
> GET /translation HTTP/1.1
> Host: 192.168.0.238:2504
> User-Agent: curl/8.5.0
> Accept: */*
> Accept-Language: es
> 
< HTTP/1.1 200 OK
< Content-Language: es
< Content-Type: text/plain; charset=utf-8
< Content-Length: 79
< 
... Has superado ... la segunda prueba.
Procede a la última prueba en /win ...
~~~

**Cómo leerlo:** `200 OK`, `Content-Language: es`: segunda prueba superada. La siguiente ruta, `/win`, aparece **en el cuerpo**, no en un header `Location`: ninguna opción de curl la seguiría sola, hay que escribirla vos.

**Por qué el próximo comando agrega eso:** cambiamos la URL a `/win`.

### Paso 4 — Consultar /win

**Comando:**

~~~bash
curl -v \
  -H "Accept-Language: es" \
  http://192.168.0.238:2504/win
~~~

**Lo que muestra:**

~~~text
> GET /win HTTP/1.1
> Host: 192.168.0.238:2504
> User-Agent: curl/8.5.0
> Accept: */*
> Accept-Language: es
> 
< HTTP/1.1 400 Bad Request
< Set-Cookie: winner=true
< Content-Type: text/plain; charset=utf-8
< Content-Length: 52
< 
Has llegado tan lejos, pero aún no has terminado...
~~~

**Cómo leerlo:** `400 Bad Request` y, en los headers de respuesta, `Set-Cookie: winner=true`. La pista es el header: el servidor te entrega una cookie y espera que se la devuelvas. curl **no guarda** cookies entre comandos si no se lo pedís.

**Por qué el próximo comando agrega eso:** agregamos `-b "winner=true"`, que hace que la petición salga con `Cookie: winner=true`.

### Paso 5 — Comando final (devolver la cookie)

**Comando:**

~~~bash
curl -v \
  -H "Accept-Language: es" \
  -b "winner=true" \
  http://192.168.0.238:2504/win
~~~

**Lo que muestra:**

~~~text
> GET /win HTTP/1.1
> Host: 192.168.0.238:2504
> User-Agent: curl/8.5.0
> Accept: */*
> Cookie: winner=true
> Accept-Language: es
> 
< HTTP/1.1 200 OK
< Content-Type: text/plain; charset=utf-8
< Content-Length: 68
< 
¡Felicidades! Has superado todas las pruebas
y has ganado el juego.
~~~

**Cómo leerlo:** En la parte `>` se ve `Cookie: winner=true` saliendo, y la respuesta es `200 OK` con la victoria.

**No confundir las direcciones:** `Set-Cookie` lo manda el **servidor**; el **cliente** manda `Cookie`. Poner `-H "Set-Cookie: ..."` en tu petición no sirve. `-b "winner=true"` equivale a `-H "Cookie: winner=true"`.

**Alternativa guardando las cookies en un archivo:**
~~~bash
curl -v -H "Accept-Language: es" -c cookies.txt http://192.168.0.238:2504/win   # -c guarda las que recibe
curl -v -H "Accept-Language: es" -b cookies.txt http://192.168.0.238:2504/win   # -b archivo las envía
~~~
curl distingue `-b "winner=true"` de `-b cookies.txt` porque el primero tiene un `=`. En un solo comando, si el servidor pone la cookie y además redirige: `curl -L -c c.txt -b c.txt URL` (acá `-L` sí sirve, para que la cookie se guarde y se reenvíe en el salto siguiente).

---

# Ejercicio 3 — El tesoro detrás del proxy SOCKS

## Enunciado
> Un contacto le avisa que hay un servidor con información importante accesible en `http://tesoro.lab/`, pero la red no rutea paquetes hacia ese host: solo se llega a través de un **proxy SOCKS** que corre en `127.0.0.1:1080`. El servidor, además, es exigente y va pidiendo las cosas de a una; conviene ir observando con el modo verboso qué responde en cada paso e ir ajustando el pedido.
>
> Utilizando curl, consiga llegar hasta la respuesta final del servidor y explique por qué `socks5://` no funcionaría y `socks5h://` sí.
>
> Datos: proxy `127.0.0.1:1080` · destino `http://tesoro.lab/` · legajo `63051` (fijo en el lab; en el examen real usás el tuyo).
>
> Se levanta con `bash lab/lab-protos.sh tesoro`.

## Primero: cómo viaja el pedido
~~~text
tu curl  ──SOCKS──▶  proxy 127.0.0.1:1080  ──HTTP──▶  tesoro.lab:80
~~~
Tu curl **no le habla al destino**: le habla al proxy y le dice "conectame con tesoro.lab puerto 80". El proxy abre esa conexión y pasa los bytes. El HTTP viaja intacto por adentro: todo lo que sabés de headers y códigos sigue igual, solo se agrega `-x` para indicar el proxy.

### Por qué `socks5h` y no `socks5`
| Esquema | Quién resuelve el nombre `tesoro.lab` | Resultado |
|---|---|---|
| `socks5://` | **tu máquina** (DNS, `/etc/hosts`) y le pasa una IP al proxy | falla si tu máquina no conoce el nombre |
| `socks5h://` | **el proxy** (la `h` es de *hostname*) | funciona: el nombre solo existe del otro lado |

Lo vemos de verdad:

~~~bash
curl -i http://tesoro.lab/
~~~

~~~text
curl: (6) Could not resolve host: tesoro.lab
~~~

Sin `-x`: tu máquina intenta resolver `tesoro.lab` y no puede (`(6) Could not resolve host`).

~~~bash
curl -i -x socks5://127.0.0.1:1080 http://tesoro.lab/
~~~

~~~text
curl: (97) Could not resolve host: tesoro.lab
~~~

Con `socks5://` pasa por el proxy pero resuelve **tu máquina**, que no conoce el nombre: `(97)`.

~~~bash
curl -i http://127.0.0.1:1080/
~~~

~~~text
curl: (1) Received HTTP/0.9 when not allowed
~~~

Pedirle HTTP directo al puerto del proxy tampoco: el proxy espera el saludo SOCKS y no entiende HTTP (`Received HTTP/0.9 when not allowed`). El tesoro no está *en* el 1080: está *detrás*.

### Cómo darse cuenta de que hace falta un proxy
- **En el enunciado:** "SOCKS", "túnel", "solo se llega desde...", "está detrás de...", o un `host:puerto` extra que no es el destino. Puertos típicos: 1080 (SOCKS), 9050 (Tor), 3128 y 8080 (proxy HTTP).
- **Probando directo:** `(6) Could not resolve host` = nombre interno; `(7)`/`(28)` o *No route to host* = la IP existe pero no llegás; `Connection refused` = no hay nada en ese puerto.
- **Escaneando:** `nmap -p 1080,3128,8080,9050 <ip>`; el tipo se prueba con `-x socks5h://IP:P` y con `-x http://IP:P`.
- **Si te obligan a usar `socks5://`:** necesitás la IP (`dig +short tesoro.lab @<DNS>` o una pista anterior) y `--resolve tesoro.lab:80:<IP>`, sin tocar `/etc/hosts`.

## Resolución paso a paso

### Paso 1 — Primer pedido por el proxy

**Comando:**

~~~bash
curl -i -x socks5h://127.0.0.1:1080 http://tesoro.lab/
~~~

**Lo que muestra:**

~~~text
HTTP/1.0 302 Found
Location: /pista1
Content-Type: text/plain; charset=utf-8
Content-Length: 7

Movido
~~~

**Cómo leerlo:** El proxy funcionó y el servidor contesta `302 Found` con `Location: /pista1`. Es una ruta **relativa**: se interpreta contra el mismo servidor (`tesoro.lab`), siempre por el proxy.

**Por qué el próximo comando agrega eso:** vamos a `/pista1`. (También serviría `-L`, pero ir a mano deja ver cada respuesta por separado.)

### Paso 2 — Pedir /pista1

**Comando:**

~~~bash
curl -i -x socks5h://127.0.0.1:1080 http://tesoro.lab/pista1
~~~

**Lo que muestra:**

~~~text
HTTP/1.0 403 Forbidden
Content-Type: text/plain; charset=utf-8
Content-Length: 39

Acceso solo para navegadores conocidos
~~~

**Cómo leerlo:** `403 Forbidden`: "acceso solo para navegadores conocidos". Un 403 rechaza por **quién sos**. El servidor mira el header `User-Agent`, que por defecto es `curl/8.x`; todo navegador se anuncia empezando con `Mozilla/5.0`.

**Por qué el próximo comando agrega eso:** agregamos `-A "Mozilla/5.0"`.

### Paso 3 — Hacerse pasar por un navegador

**Comando:**

~~~bash
curl -i -x socks5h://127.0.0.1:1080 \
  -A "Mozilla/5.0" \
  http://tesoro.lab/pista1
~~~

**Lo que muestra:**

~~~text
HTTP/1.0 400 Bad Request
Content-Type: text/plain; charset=utf-8
Content-Length: 41

Falta tu identificacion: header X-Legajo
~~~

**Cómo leerlo:** El error **cambió**: ahora `400` y "falta tu identificación: header X-Legajo". Eso significa que pasaste el escalón anterior. Un `400` indica que al pedido le falta algo y el cuerpo dice qué. Los headers `X-...` no son estándar: los inventa quien arma el servidor.

*Si el 403 no cambia:* con `-A "Chrome"` o `-A "navegador"` sigue el 403, porque no acepta cualquier texto. Corré con `-v` y mirá la línea `> User-Agent:`: si dice `curl/8.x`, el `-A` no se aplicó (comillas rotas, `-a` en minúscula, un espacio después de `\`); si dice lo que pusiste, el problema es el valor.

**Por qué el próximo comando agrega eso:** agregamos `-H "X-Legajo: 63051"` **sin sacar** el `-A`.

### Paso 4 — Enviar el legajo

**Comando:**

~~~bash
curl -i -x socks5h://127.0.0.1:1080 \
  -A "Mozilla/5.0" \
  -H "X-Legajo: 63051" \
  http://tesoro.lab/pista1
~~~

**Lo que muestra:**

~~~text
HTTP/1.0 406 Not Acceptable
Content-Type: text/plain; charset=utf-8
Content-Length: 45

Prefiero hablar en espanol (Accept-Language)
~~~

**Cómo leerlo:** `406 Not Acceptable`: "prefiero hablar en español (Accept-Language)". Un 406 significa que no pueden darte lo que vos aceptás; el idioma se pide con el header estándar `Accept-Language` (`es`, o `es-AR`).

**Por qué el próximo comando agrega eso:** agregamos `-H "Accept-Language: es"`.

### Paso 5 — Pedir español

**Comando:**

~~~bash
curl -i -x socks5h://127.0.0.1:1080 \
  -A "Mozilla/5.0" \
  -H "X-Legajo: 63051" \
  -H "Accept-Language: es" \
  http://tesoro.lab/pista1
~~~

**Lo que muestra:**

~~~text
HTTP/1.0 400 Bad Request
X-Pista: dG9rZW49emFyaWd1ZXlh
Content-Type: text/plain; charset=utf-8
Content-Length: 35

Falta el parametro token en la URL
~~~

**Cómo leerlo:** `400` otra vez: falta el parámetro `token` en la URL. El cuerpo no dice el valor, pero hay un header no estándar: `X-Pista: dG9rZW49emFyaWd1ZXlh`. Tiene pinta de **base64**: solo letras y números, 20 caracteres (múltiplo de 4). Se decodifica con `base64 -d`:

~~~bash
echo 'dG9rZW49emFyaWd1ZXlh' | base64 -d
~~~

~~~text
token=zarigueya
~~~

Sale `token=zarigueya`, que **ya tiene formato `nombre=valor`**: es el parámetro completo, listo para ponerlo después de `?`. No hay que escribir `token=` dos veces.

**Por qué el próximo comando agrega eso:** la URL pasa a ser `"http://tesoro.lab/pista1?token=zarigueya"`, **entre comillas**: sin ellas la shell interpreta `?` (comodín) y `&` (segundo plano) y el pedido puede salir cortado. Si ponés un token equivocado (por ejemplo `?token=gato`) el servidor responde `403 Token incorrecto`: el parámetro llegó pero con otro valor (revisá espacios, saltos de línea o `token=token=...`).

### Paso 6 — Agregar el token

**Comando:**

~~~bash
curl -i -x socks5h://127.0.0.1:1080 \
  -A "Mozilla/5.0" \
  -H "X-Legajo: 63051" \
  -H "Accept-Language: es" \
  "http://tesoro.lab/pista1?token=zarigueya"
~~~

**Lo que muestra:**

~~~text
HTTP/1.0 401 Unauthorized
WWW-Authenticate: Basic realm="tesoro"
Content-Type: text/plain; charset=utf-8
Content-Length: 40

Ultimo paso: identificate (admin/admin)
~~~

**Cómo leerlo:** `401 Unauthorized` con `WWW-Authenticate: Basic realm="tesoro"`. Un 401 pide autenticación: el header dice el **tipo** (`Basic`); el `realm` es solo el nombre de la zona protegida. El cuerpo da las credenciales (`admin/admin`). Si no las diera, se buscan en pistas anteriores o en el enunciado.

**Por qué el próximo comando agrega eso:** agregamos `-u admin:admin`.

### Paso 7 — Comando final

**Comando:**

~~~bash
curl -i -x socks5h://127.0.0.1:1080 \
  -A "Mozilla/5.0" \
  -H "X-Legajo: 63051" \
  -H "Accept-Language: es" \
  -u admin:admin \
  "http://tesoro.lab/pista1?token=zarigueya"
~~~

**Lo que muestra:**

~~~text
HTTP/1.0 200 OK
Content-Type: text/plain; charset=utf-8
Content-Length: 43

FLAG{tesoro-encontrado-por-el-tunel-socks}
~~~

**Cómo leerlo:** `200 OK` y el FLAG. Este es el único comando que reúne todo.

### Lo mismo con `-v`: qué viaja de verdad

~~~bash
curl -v -x socks5h://127.0.0.1:1080 -A "Mozilla/5.0" -H "X-Legajo: 63051" -H "Accept-Language: es" -u admin:admin "http://tesoro.lab/pista1?token=zarigueya"
~~~

~~~text
* SOCKS5 connect to tesoro.lab:80 (remotely resolved)
* SOCKS5 request granted.
> GET /pista1?token=zarigueya HTTP/1.1
> Host: tesoro.lab
> Authorization: Basic YWRtaW46YWRtaW4=
> User-Agent: Mozilla/5.0
> Accept: */*
> X-Legajo: 63051
> Accept-Language: es
> 
< HTTP/1.0 200 OK
< Content-Type: text/plain; charset=utf-8
< Content-Length: 43
< 
FLAG{tesoro-encontrado-por-el-tunel-socks}
~~~

Se ve que el nombre se resolvió **en el proxy** (`remotely resolved`), que `-u` armó `Authorization: Basic YWRtaW46YWRtaW4=` (es el base64 de `admin:admin`; a mano sería `-H "Authorization: Basic $(echo -n admin:admin | base64)"`), y todos los headers acumulados salen en el mismo pedido.

### Qué hace cada pieza
| Pieza | Para qué |
|---|---|
| `-i` | ver `Location`, `X-Pista`, `WWW-Authenticate` |
| `-x socks5h://127.0.0.1:1080` | pasar por el proxy, que resuelve el nombre |
| `-A "Mozilla/5.0"` | User-Agent de navegador (403) |
| `-H "X-Legajo: 63051"` | header propio de identificación (400) |
| `-H "Accept-Language: es"` | pedir español (406) |
| `-u admin:admin` | HTTP Basic (401) |
| `"…/pista1?token=zarigueya"` | ruta final + parámetro sacado del `X-Pista` |

### Errores típicos
| Pasa | Causa y arreglo |
|---|---|
| `curl: (97) Could not resolve host` | usaste `socks5://`; cambiá a `socks5h://` |
| `curl: (6) Could not resolve host` | falta el `-x`: curl fue directo |
| `curl: (1) Received HTTP/0.9...` | pusiste el proxy como URL; el proxy va en `-x`, la URL es el destino |
| sigue el 403 con `-A` | el valor no tiene `Mozilla`, o el `-A` no salió (mirá con `-v`) |
| vuelve un error de un paso anterior | al agregar algo nuevo sacaste otra opción |
| `403 Token incorrecto` | valor mal copiado, falta el `?`, o `token=token=...` |
| `base64: invalid input` | no era base64, o copiaste caracteres de más |

### Con `-L` en vez de ir a `/pista1` a mano
~~~bash
curl -iL -x socks5h://127.0.0.1:1080 -A "Mozilla/5.0" -H "X-Legajo: 63051" -H "Accept-Language: es" http://tesoro.lab/
~~~

## Qué decir en el video
«La red no llega al host, así que uso el proxy SOCKS5 con `socks5h` para que el proxy resuelva el nombre. Con `-i`/`-v` leo qué falta en cada respuesta (redirección, User-Agent, header propio, idioma, token en base64, Basic) y lo voy acumulando en un solo comando.»
