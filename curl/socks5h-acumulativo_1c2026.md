# Protocolos de Comunicación — 1C 2026, ejercicio 3

## Enunciado (textual)

*Fuente: 1C 2026, Ejercicio 3.*

⁠El administrador de su empresa necesita ayuda navegando el servidor `http` en `ejercicio3.protos.foo:3126` usando curl. 

**Dato** la red no rutea paquetes hacia el host `ejercicio3.protos.foo`, pero este es accesible mediante un proxy <`socks5h://proxy.protos.foo:1080`>

*Nota*: si no sabe como hacer un request http utilizando un proxy sock v5 puede obtener ayuda sobre como hacerlo, pero con una penalización de 0.5 puntos

---
## Resultado y alcance
Práctica del 26/10/2026, ejecutada por el estudiante en su VM. La conexión al proxy real no se estableció; se completó un recorrido equivalente local con SOCKS5, redirección, headers, idioma, POST, JSON y Basic auth.

Los datos 12345, alumno y protos son ficticios. No se descubrieron requisitos reales del servidor del parcial: habrá que leer sus respuestas cuando esté disponible.

## ⭐ RECETA PARA EL PARCIAL (leer esto primero)

> Todo lo que está después de esta sección es **práctica con un servidor inventado** (puerto 13126, `/completar`, `{"confirmar":true}`, `alumno:protos`). **No copiar esos datos al parcial.** Lo que sí se copia es el método y las tablas de las secciones 8 y 9.

### Qué pidió el servidor real del 1C 2026
Fuente: apuntes de otro alumno (github.com/keodubo/Apuntes-Protos, "2026 1C.md"). **Es de un tercero: verificar leyendo cada respuesta con `-v`.**

| Intento | Qué respondió el servidor | Dónde estaba la pista | Qué se agregó |
|---|---|---|---|
| 1 | "¡Que bueno que estas aca! ... ¿podrias ayudarme?" | cuerpo | `-v` para ver headers |
| 2 | `302` con `Location: /debugger` y `X-Tip-Parcial: el ejercicio es acumulativo...` | header `Location` | la ruta `/debugger` en la URL |
| 3 | "¿donde estan los logs?" | header `X-Error_Message: Missing header "X-legajo"` | `-H "X-legajo: <legajo>"` |
| 4 | texto en ruso | header `Content-Language: ru` | `-H "Accept-Language: es"` |
| 5 | "ya se arreglo el GET, pero el POST aun falla" | cuerpo | `-X POST` |
| 6 | "Proba mandar este JSON: {"fix":"yes"}" | cuerpo | `-H "Content-Type: application/json" -d '{"fix":"yes"}'` |
| 7 | "te falta sudo ... usuario admin, contraseña admin" | cuerpo | `-u admin:admin` |
| 8 | "¡Te doy el ejercicio por aprobado!" | cuerpo | — |

**Clave:** varias pistas vinieron en **headers de respuesta** (`Location`, `X-Error_Message`, `Content-Language`), no en el cuerpo. Por eso `-v` va desde el primer intento: sin él no ves las líneas `<` y te quedás sin saber qué falta.

### Comando final (con mi legajo)
~~~bash
curl -v -x socks5h://proxy.protos.foo:1080 \
  -H "X-legajo: 63051" \
  -H "Accept-Language: es" \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"fix":"yes"}' \
  -u admin:admin \
  http://ejercicio3.protos.foo:3126/debugger
~~~

| Parte | Por qué está |
|---|---|
| `-v` | ver la petición (`>`) y los headers de respuesta (`<`), donde vienen las pistas |
| `-x socks5h://proxy.protos.foo:1080` | la red no rutea al host; el proxy SOCKS5 sí llega. La `h` hace que **el proxy** resuelva `ejercicio3.protos.foo`, nombre que mi máquina no conoce |
| `-H "X-legajo: 63051"` | header que exige el servidor (`X-Error_Message`) |
| `-H "Accept-Language: es"` | sin él responde en ruso (`Content-Language: ru`) |
| `-X POST` | pide POST. Con `-d` es redundante (ya implica POST), pero lo dejo explícito porque el servidor lo pidió en un paso aparte |
| `-H "Content-Type: application/json"` | `-d` manda `application/x-www-form-urlencoded` por defecto; hay que declarar JSON |
| `-d '{"fix":"yes"}'` | el cuerpo JSON que pidió. Comillas simples afuera (para la terminal), dobles adentro (del JSON) |
| `-u admin:admin` | Basic auth: curl arma `Authorization: Basic YWRtaW46YWRtaW4=` (base64 de `admin:admin`, **no es cifrado**) |
| `.../debugger` | se pide **directo la ruta del `Location`**: así el POST no pasa por el 302 y no hace falta `-L` ni `--post302` |

Equivalentes de `-u admin:admin` que también funcionaron según los apuntes:
- usuario en la URL: `http://admin:admin@ejercicio3.protos.foo:3126/debugger`
- header a mano: `-H "Authorization: Basic YWRtaW46YWRtaW4="` (verificar: `printf 'admin:admin' | base64`)

### Procedimiento si cambian las pistas
1. `curl -v -x socks5h://<proxy>:<puerto> http://<host>:<puerto>` y leer **status + headers `<` + cuerpo**.
2. Agregar **una sola** opción según lo que falte (tabla de la sección 8).
3. Repetir con el comando acumulado completo, sin sacar nada de lo anterior.
4. Si hay `302`/`301`: preferir pedir directo la URL del `Location`. Si usás `-L` con un POST, curl lo cambia a GET (usar `--post302`/`--post301`).
5. Si curl falla **antes** de cualquier línea `< HTTP`: es un problema de proxy/DNS/conexión, no un requisito HTTP. Revisar el esquema (`socks5h`) y el puerto del proxy.

### Para el video
"La red no rutea al host, así que uso el proxy SOCKS5 con `socks5h` para que resuelva el nombre. Con `-v` leo en cada respuesta qué falta (redirección, header, idioma, método, JSON, autenticación) y lo voy acumulando hasta que el servidor da el ejercicio por aprobado."

---

# PRÁCTICA (detalle de lo que se ejecutó)

## 1. Intento directo
~~~bash
curl --noproxy '*' --connect-timeout 5 -v http://ejercicio3.protos.foo:3126
~~~
- curl hace GET por defecto.
- --noproxy '*' evita todos los proxies, incluidos los configurados en el entorno. Las comillas protegen * de expansión por la terminal.
- --connect-timeout 5 limita la fase de conexión, incluida resolución, a cinco segundos.
- -v muestra diagnóstico (*), petición (>), estado y headers de respuesta (<). El cuerpo aparece sin esos prefijos. No equivale a una captura independiente del lado del servidor.
- La URL especifica HTTP, destino y puerto 3126; sin ruta se pide /.

Resultado real: ejercicio3.protos.foo resolvió a 127.0.0.1; se rechazó la conexión local al puerto 3126. No hubo intercambio HTTP. Esto no demuestra cómo rutea la red hacia el destino real ni que solo se habilite durante el examen.

## 2. Intento por el proxy real
~~~bash
curl -v --connect-timeout 5 -x socks5h://proxy.protos.foo:1080 http://ejercicio3.protos.foo:3126
~~~
-x selecciona el proxy. Se retiró --noproxy '*', que impediría usarlo.
El proxy resolvió a 192.168.0.135; la conexión a 1080 expiró a los cinco segundos. No se llegó a negociar SOCKS ni a contactar el destino.

| Esquema | Quién resuelve el destino |
|---|---|
| socks5:// | curl en la máquina cliente |
| socks5h:// | El proxy SOCKS5 |

La h indica hostname resuelto por el proxy. La máquina cliente aún necesita resolver el nombre del propio proxy. Una resolución local distinta, o inexistente, del destino no impide usar socks5h si el proxy sí puede resolverlo y alcanzarlo.

## 3. Entorno reutilizable de práctica
Archivo descargado en ~/Downloads/ejercicio3_practica.py, por elección del estudiante:
~~~bash
python3 ~/Downloads/ejercicio3_practica.py
~~~
python3 ejecuta el archivo; ~ representa el directorio personal. Mantener esa terminal abierta y usar otra para curl. Ctrl+C detiene HTTP y SOCKS5; conservar el archivo permite repetir.

El programa solo usa biblioteca estándar de Python y escucha en loopback:
- HTTP: 127.0.0.1:13126.
- SOCKS5: 127.0.0.1:11080.
- Nombre ficticio reconocido por el proxy: ejercicio3.practica.invalid.
- No requiere modificar /etc/hosts, nginx, BIND ni variables persistentes.
- El proxy solo permite el destino de práctica; no es un proxy abierto.
- Limitación: HTTP también es accesible directamente por 127.0.0.1:13126. Se simula la resolución del nombre del lado del proxy, no una red realmente inaccesible sin él.

## 4. Recorrido acumulativo, con comandos completos
En todos los pasos: -v muestra intercambio; -x selecciona proxy; socks5h delega resolución; los -H agregan headers. Cada intento conserva los requisitos anteriores.

### Paso A: pedir la raíz por SOCKS5
~~~bash
curl -v -x socks5h://127.0.0.1:11080 http://ejercicio3.practica.invalid:13126
~~~
Respuesta real:
~~~http
HTTP/1.1 302 Found
Location: /completar
~~~
El cuerpo indicó continuar en Location. Esa ruta conserva esquema, host y puerto: http://ejercicio3.practica.invalid:13126/completar.
Podemos usar esa URL a mano o seguir automáticamente.

### Paso B: seguir la redirección
~~~bash
curl -v -L -x socks5h://127.0.0.1:11080 http://ejercicio3.practica.invalid:13126
~~~
-L sigue Location. Se observaron GET / y GET /completar.
Respuesta final: 400 Bad Request; cuerpo: «Falta X-legajo con un numero. Usar 12345 en esta practica.»
El código 400 solo no identifica el dato faltante: leer el cuerpo.

### Paso C: agregar legajo
~~~bash
curl -v -L -x socks5h://127.0.0.1:11080 -H "X-legajo: 12345" http://ejercicio3.practica.invalid:13126
~~~
-H recibe nombre: valor como un argumento, protegido con comillas.
Se observó > X-legajo: 12345 en ambas peticiones.
Respuesta: 406 Not Acceptable; cuerpo: «Please request Spanish with Accept-Language: es.»

### Paso D: pedir español
~~~bash
curl -v -L -x socks5h://127.0.0.1:11080 -H "X-legajo: 12345" -H "Accept-Language: es" http://ejercicio3.practica.invalid:13126
~~~
Accept-Language expresa preferencia de idioma; no traduce. El servidor decide si la atiende. Sin él, nuestro servidor pide en inglés que se solicite español.
Respuesta real:
~~~http
HTTP/1.1 405 Method Not Allowed
Allow: POST
~~~
Cuerpo: «Este recurso requiere el metodo POST.» Se había enviado GET /completar.

### Paso E: agregar cuerpo y observar POST convertido en GET
~~~bash
curl -v -L -x socks5h://127.0.0.1:11080 -H "X-legajo: 12345" -H "Accept-Language: es" -d '{}' http://ejercicio3.practica.invalid:13126
~~~
-d envía datos y selecciona POST. -X POST sería redundante para seleccionar el método inicial.
Se observó:
~~~text
> POST / HTTP/1.1
> Content-Type: application/x-www-form-urlencoded
< HTTP/1.1 302 Found
> GET /completar HTTP/1.1
< HTTP/1.1 405 Method Not Allowed
~~~
Con -L, curl cambió el POST a GET tras 302 y no reenvió el cuerpo. Este intento permitió ver esa diferencia.

### Paso F: conservar POST frente al 302
~~~bash
curl -v -L --post302 -x socks5h://127.0.0.1:11080 -H "X-legajo: 12345" -H "Accept-Language: es" -d '{}' http://ejercicio3.practica.invalid:13126
~~~
--post302 conserva POST y cuerpo al seguir ese código; no reemplaza a -L.
Ahora llegó POST /completar, pero respondió 415 Unsupported Media Type.
Cuerpo: «Se requiere Content-Type: application/json.»
Otra solución válida sería enviar directamente el POST a la URL de Location.

### Paso G: declarar el tipo JSON
~~~bash
curl -v -L --post302 -x socks5h://127.0.0.1:11080 -H "X-legajo: 12345" -H "Accept-Language: es" -H "Content-Type: application/json" -d '{}' http://ejercicio3.practica.invalid:13126
~~~
-H Content-Type reemplaza el valor predeterminado de -d. Declarar JSON no cambia ni valida el cuerpo.
Se observó > Content-Type: application/json y Content-Length: 2.
Respuesta: 400; cuerpo: «El JSON debe contener "confirmar": true.»

### Paso H: completar el JSON
~~~bash
curl -v -L --post302 -x socks5h://127.0.0.1:11080 -H "X-legajo: 12345" -H "Accept-Language: es" -H "Content-Type: application/json" -d '{"confirmar":true}' http://ejercicio3.practica.invalid:13126
~~~
Las comillas simples externas son de la terminal y no se envían. Las dobles internas forman parte del JSON. true es booleano; "true" sería texto.
Content-Length pasó a 18 bytes.
Respuesta:
~~~http
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Basic realm="Practica Protos"
~~~
Cuerpo: «Se requiere Basic auth. Usuario de practica: alumno; clave: protos.»
401 pide autenticación válida; WWW-Authenticate identifica Basic y su ámbito.

### Paso I: credenciales — éxito
~~~bash
curl -v -L --post302 -x socks5h://127.0.0.1:11080 -H "X-legajo: 12345" -H "Accept-Language: es" -H "Content-Type: application/json" -d '{"confirmar":true}' -u alumno:protos http://ejercicio3.practica.invalid:13126
~~~
-u recibe usuario:clave del servidor HTTP; no del proxy. Para Basic, curl construye Authorization con Base64 de esos datos.
Se observó:
~~~text
> Authorization: Basic YWx1bW5vOnByb3Rvcw==
> POST /completar HTTP/1.1
< HTTP/1.1 200 OK

Ejercicio completado. Legajo de practica: 12345
~~~
El método se imprime antes de los headers en la salida real; arriba se agrupan las evidencias clave.
Éxito del entorno simulado; no atribuirlo al servicio real del parcial.

## 5. Comando final y explicación en orden
> ⚠️ Este es el comando final **del servidor de práctica**. El del parcial está en la RECETA del principio.

~~~bash
curl -v -L --post302 \
  -x socks5h://127.0.0.1:11080 \
  -H "X-legajo: 12345" \
  -H "Accept-Language: es" \
  -H "Content-Type: application/json" \
  -d '{"confirmar":true}' \
  -u alumno:protos \
  http://ejercicio3.practica.invalid:13126
~~~
Las barras invertidas al final permiten continuar el comando en la siguiente línea; no dejar espacios después de ellas.

| Parte | Propósito |
|---|---|
| curl | Cliente HTTP |
| -v | Ver petición, respuesta y conexión |
| -L | Seguir redirecciones |
| --post302 | Mantener POST y cuerpo ante 302 |
| -x socks5h://127.0.0.1:11080 | Proxy local y resolución del destino por el proxy |
| -H "X-legajo: 12345" | Legajo ficticio |
| -H "Accept-Language: es" | Pedir español |
| -H "Content-Type: application/json" | Declarar formato del cuerpo enviado |
| -d '{"confirmar":true}' | Enviar cuerpo y seleccionar POST |
| -u alumno:protos | Autenticación Basic con datos ficticios |
| URL | Destino de práctica |

En el parcial, empezar por el proxy y URL reales y leer cada requisito. No trasladar automáticamente cuerpo, idioma o credenciales ficticios al servidor real.

## 6. Demostrar que Base64 no es cifrado
~~~bash
printf '%s' 'YWx1bW5vOnByb3Rvcw==' | base64 --decode
~~~
printf escribe el texto; %s lo trata como cadena; | conecta salida con entrada; base64 --decode revierte la codificación.
Resultado real: alumno:protos. El prompt quedó pegado por faltar salto de línea.
Basic no cifra; HTTPS protege el transporte HTTP. SOCKS5 por sí solo no agrega cifrado.

## 7. Comparación de redirecciones, verificada en la VM
Laboratorio separado: /redir/CODIGO redirige a /eco, que muestra método y cuerpo.
~~~bash
curl -v -L -x socks5h://127.0.0.1:11080 -d 'prueba' http://ejercicio3.practica.invalid:13126/redir/307
~~~
~~~bash
curl -v -L -x socks5h://127.0.0.1:11080 -d 'prueba' http://ejercicio3.practica.invalid:13126/redir/308
~~~
~~~bash
curl -v -L -x socks5h://127.0.0.1:11080 -d 'prueba' http://ejercicio3.practica.invalid:13126/redir/301
~~~
-v, -L y -x mantienen sus funciones; -d 'prueba' selecciona POST inicial con ese cuerpo; la ruta selecciona el código.

| Código | Significado | POST con -d y -L, sin forzar método |
|---|---|---|
| 301 | Permanente | GET sin cuerpo |
| 302 | Temporal | GET sin cuerpo |
| 307 | Temporal | POST y cuerpo conservados |
| 308 | Permanente | POST y cuerpo conservados |

307/308 devolvieron {"metodo": "POST", "cuerpo": "prueba"}; 301 devolvió {"metodo": "GET", "cuerpo": ""}. El cambio en 302 ya se había observado en el recorrido.
--post301 y --post302 permiten conservar POST si el servicio lo requiere. No usar -X POST como sustituto general: fuerza la palabra del método y no equivale a configurar correctamente la conservación del cuerpo.

## 8. Qué respuesta del servidor → qué opción de curl agregar
| Evidencia | Acción razonable |
|---|---|
| 302 con Location | -L o cambiar manualmente a la URL resuelta de Location |
| POST cambia a GET tras 302 | Si se requiere mantenerlo, --post302 junto con -L, o pedir directamente el destino |
| 401 con WWW-Authenticate: Basic | -u usuario:clave |
| 401 solicitando Bearer | -H "Authorization: Bearer TOKEN" |
| 405 con Allow: POST | -d 'cuerpo' si hay datos; -X POST si se necesita POST sin cuerpo |
| 405 con Allow: PUT o DELETE | -X PUT o -X DELETE según la API |
| 415 y exige JSON | -H "Content-Type: application/json", con cuerpo JSON válido |
| 400 y nombra un header | -H "Nombre: valor", siguiendo el mensaje |
| 400 y nombra un campo JSON | Corregir el argumento de -d; no basta declarar Content-Type |
| Idioma inesperado / petición de idioma | -H "Accept-Language: es" u otro idioma solicitado |
| 406 y exige representación | Revisar Accept, Accept-Language y cuerpo del error |
| 304 Not Modified | No es redirección: usar copia previa o quitar condiciones de caché para pedir cuerpo |
| Error curl antes de cualquier < HTTP | Diagnosticar DNS, conexión o proxy; no inventar un requisito HTTP |
| 407 Proxy Authentication Required en un proxy HTTP | Credenciales del proxy con -U usuario:clave; no confundir con -u |

Los códigos orientan; el header y el cuerpo especifican la corrección. No existe una opción universal para cada código.

## 9. Variantes: qué cambia y qué línea tocar
Fragmentos para incorporar al comando completo; no son pruebas ejecutadas contra el servidor real.

| Cambio | Sintaxis exacta |
|---|---|
| Pedir inglés | -H "Accept-Language: en" |
| Preferencias de idioma | -H "Accept-Language: es-AR,es;q=0.9,en;q=0.5" |
| Pedir texto | -H "Accept: text/plain" |
| Pedir JSON | -H "Accept: application/json" |
| Otro legajo | -H "X-legajo: 67890" |
| Otro header | -H "X-Algo: valor" |
| PUT con JSON | -X PUT -H "Content-Type: application/json" -d '{"nombre":"Rosa"}' |
| DELETE | -X DELETE |
| Otro cuerpo | -d '{"confirmar":true,"grupo":2}' |
| Cuerpo literal con --data-raw | --data-raw '{"confirmar":true}' |
| Otras credenciales Basic | -u otro_usuario:otra_clave |
| Token Bearer | -H "Authorization: Bearer TOKEN_DE_PRACTICA" |
| Enviar cookie literal | -b "sesion=abc123" |
| Leer cookies de archivo | -b cookies.txt |
| Guardar cookies recibidas | -c cookies.txt |
| Leer y actualizar cookies | -b cookies.txt -c cookies.txt |
| ETag recibido "v1" | -H 'If-None-Match: "v1"' |
| Fecha de Last-Modified recibida | -H "If-Modified-Since: Mon, 26 Oct 2026 12:00:00 GMT" |
| Seguir redirecciones | -L |
| Conservar POST tras 301 | -L --post301 |
| Conservar POST tras 302 | -L --post302 |
| Otro puerto del destino | http://ejercicio3.practica.invalid:14000 |
| Otro puerto del proxy | -x socks5h://127.0.0.1:12080 |
| Proxy HTTP | -x http://proxy.protos.foo:8080 |

-X fija el método. -d ya selecciona POST y usa application/x-www-form-urlencoded por defecto. --data-raw se comporta como -d pero no interpreta un @ inicial como lectura desde archivo; no fija Content-Type JSON. Reemplazar el cuerpo anterior en vez de acumular dos -d: curl los uniría con &.
Accept pide el tipo de respuesta; Content-Type describe el cuerpo enviado.
Las variantes de otros puertos requieren un servidor/proxy realmente escuchando allí. El proxy de práctica restringe el destino a su puerto configurado.

### Cookie
-b lee archivo o envía pares literales; -c guarda cookies recibidas al finalizar. Juntas permiten mantener estado entre ejecuciones. Las rutas cookies.txt son relativas al directorio actual.

### 304, ETag y fechas
Primero hacer GET sin condiciones con -i para leer ETag o Last-Modified. En la siguiente petición copiar el validador real, respetando comillas del ETag.
Si la representación no cambió, el servidor puede devolver 304 sin cuerpo: usar la copia guardada. Curl no mantiene automáticamente una caché de cuerpos. Para pedir el cuerpo otra vez, quitar If-None-Match e If-Modified-Since y cualquier condición equivalente.
Si se envían ambas condiciones, If-None-Match tiene precedencia. Estas son variantes de GET/HEAD, no un paso del POST de la práctica. Nuestro servidor no implementa validadores de caché; no esperar 304 de él.
-i muestra headers y cuerpo; -I pide HEAD y no descarga cuerpo: no confundirlos.

### Usar ALL_PROXY sin modificar la sesión
~~~bash
ALL_PROXY=socks5h://127.0.0.1:11080 curl -v http://ejercicio3.practica.invalid:13126
~~~
La asignación antes del comando solo afecta a esa ejecución; agregar el resto de requisitos cuando corresponda. Se omite -x. Variables específicas como http_proxy pueden prevalecer y NO_PROXY puede excluir el destino.
Para una prueba controlada, excluyendo variables HTTP previas y exclusiones:
~~~bash
env -u http_proxy -u HTTP_PROXY ALL_PROXY=socks5h://127.0.0.1:11080 curl --noproxy '' -v http://ejercicio3.practica.invalid:13126
~~~
env prepara el entorno del proceso; -u quita esa variable solo del proceso; ALL_PROXY se asigna para ese proceso; --noproxy '' evita exclusiones sin desactivar el proxy. No se cambiaron variables persistentes.

### Si el proxy es HTTP
Cambiar el esquema del argumento -x a http:// y usar su puerto. El proxy debe hablar HTTP: no basta renombrar el esquema de un servidor SOCKS5.
Para destino HTTP, curl envía al proxy una petición con URL absoluta y este contacta el origen; para HTTPS normalmente establece un túnel CONNECT y negocia TLS con el destino.
Credenciales del proxy se indican con -U, distintas de las del origen con -u.

## 10. Cerrar la práctica
En la terminal donde corre Python, Ctrl+C detiene ambos servicios. Mantener ~/Downloads/ejercicio3_practica.py permite reutilizarlo.
No se agregaron entradas hosts ni sitios nginx en este ejercicio. Detener el proceso libera los puertos; la existencia del archivo no mantiene ningún servidor activo.

## Justificación breve para el parcial
“Uso SOCKS5 con resolución del destino en el proxy y leo cada respuesta para acumular redirecciones, headers, método, cuerpo y autenticación hasta obtener la confirmación del servidor.”

## Guardar este documento en la VM
El asistente no accede directamente a la VM. Descargar el apunte y copiarlo:
~~~bash
mkdir -p ~/protos/soluciones
~~~
mkdir crea el directorio; -p crea padres y acepta existentes.
~~~bash
cp ~/Downloads/26.1-3.md ~/protos/soluciones/26.1-3.md
~~~
cp copia desde origen a destino. Downloads es la carpeta que el estudiante usó en esta práctica.

## Referencias oficiales
- [Opciones de curl](https://curl.se/docs/manpage.html)
- [Redirecciones](https://everything.curl.dev/http/redirects.html)
- [POST y datos](https://everything.curl.dev/http/post/simple.html)
- [Condiciones HTTP](https://everything.curl.dev/http/modify/conditionals.html)
- [Cookies](https://everything.curl.dev/http/cookies/writing.html)
- [Variables de proxy](https://everything.curl.dev/usingcurl/proxies/env.html)

