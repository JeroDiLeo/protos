# Protocolos de Comunicación — 1C 2026, ejercicio 2

## Consigna y resultado
Configurar nginx para que «curl http://metadata.local», sin opciones adicionales, obtenga el contenido de http://metadata.protos.foo. El backend exige Metadata: true y responde JSON.

Práctica del 26/10/2026. Los comandos se ejecutaron en la VM del estudiante, quien compartió sus salidas. El backend real resolvía a 35.211.115.38, pero no se obtuvo una respuesta HTTP válida: conexión rechazada desde la VM y conexión reiniciada desde Pampero, incluso enviando Metadata: true. No conocemos la causa exacta.

Se verificó el funcionamiento completo con un backend local equivalente en 127.0.0.1:8081. Luego se retiró ese backend, se dejó proxy_pass apuntando al backend del enunciado y se deshabilitó el sitio para continuar con otros ejercicios. No se verificó éxito contra el backend real.

## 1. Estado inicial
~~~bash
systemctl status nginx
~~~
systemctl administra servicios; status consulta el estado; nginx identifica el servicio. Estaba activo. q permite salir del paginador. enabled significa habilitado para arrancar, no necesariamente activo.

## 2. Consultas directas al backend real
~~~bash
curl -i http://metadata.protos.foo
~~~
curl envía GET por defecto; -i muestra headers de respuesta y cuerpo. HTTP usa puerto 80 si no se indica otro; sin ruta se pide /.
En la VM no conectó. Se diagnosticó con:
~~~bash
curl -v http://metadata.protos.foo
~~~
-v muestra resolución, intentos de conexión y headers enviados/recibidos si llega a establecerse HTTP. Se observó «Connection refused» al conectar a 35.211.115.38:80.
En Pampero se estableció TCP, se envió GET / con Host: metadata.protos.foo y Accept: */*, y luego se recibió «Connection reset by peer».

~~~bash
curl -i -H "Metadata: true" http://metadata.protos.foo
~~~
-H agrega un header de petición; las comillas mantienen nombre y valor como un argumento. En Pampero también terminó con reset. Cambiar un header no corrige por sí mismo una conexión TCP rechazada.

## 3. Backend temporal, exclusivamente para practicar
Se comprobó el puerto:
~~~bash
sudo ss -ltnp 'sport = :8081'
~~~
sudo da permisos administrativos; ss muestra sockets; -l selecciona escucha; -t TCP; -n salida numérica; -p procesos; el filtro selecciona puerto local 8081. El estudiante confirmó que estaba libre.

Se creó el archivo:
~~~bash
nano /tmp/metadata-practica.py
~~~
nano abre el editor; el argumento es la ruta temporal. Sin sudo porque /tmp permite crear archivos del usuario.
~~~python
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

class MetadataHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        autorizado = self.headers.get("Metadata") == "true"
        if autorizado:
            estado = 200
            contenido = {"mensaje": "Backend de practica", "metadata": True}
        else:
            estado = 403
            contenido = {"error": "Falta el header Metadata: true"}
        cuerpo = (json.dumps(contenido) + "\n").encode("utf-8")
        self.send_response(estado)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

HTTPServer(("127.0.0.1", 8081), MetadataHandler).serve_forever()
~~~
do_GET procesa GET. headers.get lee Metadata. json.dumps serializa; encode convierte a bytes. send_response fija estado; send_header agrega headers de respuesta; end_headers finaliza headers; wfile.write envía cuerpo. HTTPServer escucha localmente; serve_forever mantiene el servidor activo.

Guardar con Ctrl+O, Enter; salir con Ctrl+X.
~~~bash
python3 /tmp/metadata-practica.py
~~~
python3 ejecuta el archivo. Queda en primer plano: mantener esa terminal abierta y usar otra para las pruebas.

## 4. Comprobar Metadata y Accept por separado
| Comando | Resultado real |
|---|---|
| curl -i http://127.0.0.1:8081 | 403 Forbidden, JSON de error |
| curl -i -H "Metadata: true" http://127.0.0.1:8081 | 200 OK, JSON exitoso |
| curl -i -H "Metadata: true" -H "Accept: application/json" http://127.0.0.1:8081 | Mismo 200 y mismo JSON |

La URL con :8081 selecciona ese puerto. Se puede repetir -H para enviar varios headers.
- Metadata: true habilita la respuesta exitosa.
- Accept: application/json expresa qué representación acepta el cliente.
- Content-Type: application/json, en la respuesta, informa el formato enviado.
- Accept no convierte el contenido ni obliga al servidor a producir JSON. En este backend es opcional: las pruebas con y sin él dieron lo mismo.
- El servidor real no se pudo evaluar; no atribuirle resultados del backend simulado.

Cuerpo exitoso real de práctica:
~~~json
{"mensaje": "Backend de practica", "metadata": true}
~~~

## 5. Resolver el nombre local
~~~bash
sudo nano /etc/hosts
~~~
sudo permite editar un archivo del sistema; nano es el editor. Se agregó:
~~~text
127.0.0.1 metadata.local
~~~
Esto asocia el nombre con la máquina que ejecuta nginx. No lleva esquema ni puerto. server_name no registra nombres en DNS: hace falta una resolución local o DNS por separado. La entrada afecta ese nombre, no los demás dominios. En esta VM funcionó mediante /etc/hosts, aunque .local suele usarse también para mDNS.

## 6. Crear el sitio
~~~bash
sudo nano /etc/nginx/sites-available/metadata.local
~~~
Archivo guardado en sites-available; el nombre del archivo es una convención, el nombre HTTP se declara con server_name.

### Configuración final preparada para el parcial
~~~nginx
server {
    listen 80;
    server_name metadata.local;

    location / {
        proxy_pass http://metadata.protos.foo;
        proxy_set_header Host metadata.protos.foo;
        proxy_set_header Metadata true;
        proxy_set_header Accept application/json;
    }
}
~~~
Para la prueba exitosa se usó, en cambio:
~~~nginx
proxy_pass http://127.0.0.1:8081;
~~~
El resto del bloque fue igual.

| Directiva | Función |
|---|---|
| server { ... } | Configuración de un sitio |
| listen 80; | Puerto de recepción |
| server_name metadata.local; | Nombre que debe coincidir con Host |
| location / { ... } | Reglas para las rutas bajo / |
| proxy_pass URL; | Destino del reenvío |
| proxy_set_header nombre valor; | Fija un header en la petición al backend |
| proxy_set_header Metadata true; | Cumple el requisito sin pedir opciones al cliente |
| proxy_set_header Accept application/json; | Solicita JSON explícitamente; opcional en la práctica |

Los puntos y coma cierran directivas; las llaves delimitan bloques.

### Dos peticiones y dos nombres
curl → nginx usa Host: metadata.local. Nginx selecciona el bloque según dirección/puerto y Host; si no hay coincidencia usa el servidor predeterminado de ese socket. Otro server_name no hace coincidir metadata.local automáticamente.

nginx → backend usa Host: metadata.protos.foo por nuestra directiva. Por defecto se usa $proxy_host, derivado del destino proxy_pass: en la prueba habría sido 127.0.0.1:8081; con el destino real sería metadata.protos.foo. La línea explícita Host es redundante con el destino real, pero clara y útil si se conecta por IP a un backend con virtual hosts. Usar $host aquí enviaría normalmente metadata.local y podría seleccionar otro sitio en el backend.

## 7. Habilitar, validar y aplicar
~~~bash
sudo ln -s /etc/nginx/sites-available/metadata.local /etc/nginx/sites-enabled/metadata.local
~~~
ln crea un enlace; -s lo hace simbólico; primera ruta es el archivo de destino y segunda la ubicación del enlace. En la configuración habitual de Ubuntu, nginx incluye sites-enabled. No duplicar un server_name ya habilitado para el mismo socket.

~~~bash
sudo nginx -t
~~~
-t comprueba sintaxis y acceso a archivos referenciados; no aplica cambios ni prueba que el backend funcione. Se confirmó que pasó.
~~~bash
sudo systemctl reload nginx
~~~
reload relee configuración e incorpora nuevos trabajadores, dejando terminar a los antiguos. restart detiene y vuelve a iniciar el servicio y puede interrumpir conexiones. Validar antes de recargar.

## 8. Verificación por nginx — resultados reales
~~~bash
curl http://metadata.local
~~~
Sin opciones: mostró el JSON exitoso. /etc/hosts llevó a 127.0.0.1:80 y nginx agregó el header requerido al reenviar a 8081.
~~~bash
curl -i http://metadata.local
~~~
Resultado:
~~~http
HTTP/1.1 200 OK
Server: nginx/1.28.3 (Ubuntu)
Content-Type: application/json
Content-Length: 53
Connection: keep-alive

{"mensaje": "Backend de practica", "metadata": true}
~~~
-i fue diagnóstico; la consigna ya se había probado sin opciones.
-I (i mayúscula) pide HEAD, sin cuerpo; no equivale a -i. Nuestro backend temporal solo implementa GET, por lo que HEAD no es la prueba adecuada.

## 9. proxy_pass con y sin barra final
Para un location de prefijo simple:
| Dentro de location /api/ | Petición /api/datos enviada al backend |
|---|---|
| proxy_pass http://backend; | /api/datos |
| proxy_pass http://backend/; | /datos |

Sin URI se conserva la ruta en este caso; con URI / se sustituye el prefijo coincidente. En nuestro location /, pedir / da / con ambas formas. No confundir estos ejemplos con configuraciones que usan rewrite, variables o locations regex: requieren analizar sus reglas.

## 10. Logs y diagnóstico de 404 / 502
~~~bash
sudo tail -n 10 /var/log/nginx/access.log
~~~
tail muestra el final; -n 10 limita a diez líneas. Se vieron:
~~~text
127.0.0.1 ... "GET / HTTP/1.1" 200 53 "-" "curl/8.18.0"
~~~
127.0.0.1 es cliente; GET / HTTP/1.1 es la petición; 200 el estado al cliente; 53 los bytes del cuerpo; "-" ausencia de Referer; al final User-Agent. Las primeras entradas 200 6 coincidían en tamaño con What? más salto de línea, pero ese log no prueba quién generó tal cuerpo.

~~~bash
sudo tail -n 10 /var/log/nginx/error.log
~~~
Mismos parámetros, distinto archivo. No mostró líneas: no había errores registrados allí.

| Situación | Cómo investigar |
|---|---|
| 502 y connect() failed ... while connecting to upstream | Verificar proceso, puerto y accesibilidad del backend |
| 502 y upstream prematurely closed connection / reset | El backend o un intermediario cerró sin respuesta válida |
| 404 y open() ... failed para un archivo local | Revisar selección de server/location y si se intentó servir un archivo |
| 404 sin mensaje de error | Puede proceder del backend; probar directamente con el mismo Host, header y ruta |
| No aparece la petición | Revisar IP, puerto, virtual host y si usa otro access_log |

Un 502 también puede venir del propio backend. El access.log predeterminado no distingue todos los orígenes. Para diagnosticar, puede definirse en contexto http:
~~~nginx
log_format protos '$host "$request" status=$status upstream=$upstream_addr upstream_status=$upstream_status';
~~~
Y dentro del server:
~~~nginx
access_log /var/log/nginx/metadata.access.log protos;
~~~
log_format da nombre y formato; access_log elige ruta y formato. $host identifica nombre, $request petición, $status estado final, $upstream_addr destino y $upstream_status respuesta upstream. Un 404 upstream registrado indica que ese upstream lo devolvió; ausencia de upstream sugiere respuesta local en esta configuración simple. Para fallos de conexión combinar siempre con error.log.

## 11. Variantes: qué cambia y qué línea tocar
Son ejemplos para estudiar, no cambios aplicados.

| Cambio | Línea exacta de nginx | Ubicación / ajuste adicional |
|---|---|---|
| Otro nombre local | server_name otro.local; | server; agregar 127.0.0.1 otro.local a hosts |
| Otro backend | proxy_pass http://otro.protos.foo; | location; revisar también Host |
| Host del nuevo backend | proxy_set_header Host otro.protos.foo; | location |
| Header Authorization | proxy_set_header Authorization "Bearer TOKEN_DE_PRACTICA"; | location; reemplaza o complementa Metadata según consigna |
| Header X-Algo | proxy_set_header X-Algo "valor"; | location |
| Puerto backend 9000 | proxy_pass http://metadata.protos.foo:9000; | location; puerto destino, no listen |
| Puerto de recepción 8080 | listen 8080; | server; cliente debe usar :8080 |
| Quitar Accept opcional | # proxy_set_header Accept application/json; | Comentar la línea en location |
| Activar gzip | gzip on; | server |
| Comprimir JSON | gzip_types application/json; | server |
| Permitir JSON pequeño en prueba gzip | gzip_min_length 1; | server; umbral en bytes |
| Señalar variación por compresión | gzip_vary on; | server; agrega Vary: Accept-Encoding |
| Agregar HTTPS sin retirar HTTP | listen 443 ssl; | server; conservar listen 80 |
| Certificado HTTPS | ssl_certificate /etc/nginx/certs/metadata.local.pem; | server |
| Clave privada HTTPS | ssl_certificate_key /etc/nginx/certs/metadata.local-key.pem; | server |

Gzip: activar gzip y el tipo JSON; el cliente debe anunciar gzip. Prueba opcional:
~~~bash
curl --compressed -i http://metadata.local
~~~
--compressed solicita compresión compatible y descomprime automáticamente el cuerpo; -i permite ver Content-Encoding. No es parte del curl sin opciones de la consigna. El JSON de práctica tenía 53 bytes; configuraciones con umbral mayor no lo comprimirán. gzip_proxied depende de Via en la petición entrante: no es obligatorio solo por usar proxy_pass.

### Variante HTTPS con mkcert
Requiere mkcert instalado. Ejecutar como el usuario que hará las pruebas:
~~~bash
mkcert -install
~~~
-install crea/instala la CA local de desarrollo en los almacenes de confianza disponibles.
~~~bash
mkcert -cert-file metadata.local.pem -key-file metadata.local-key.pem metadata.local
~~~
-cert-file fija archivo del certificado; -key-file fija archivo de clave; metadata.local es el nombre que cubrirá.
~~~bash
sudo mkdir -p /etc/nginx/certs
~~~
mkdir crea directorios; -p crea padres faltantes y acepta existentes.
~~~bash
sudo cp metadata.local.pem metadata.local-key.pem /etc/nginx/certs/
~~~
cp copia los dos archivos al directorio de destino.
~~~bash
sudo chmod 600 /etc/nginx/certs/metadata.local-key.pem
~~~
chmod cambia permisos; 600 da lectura/escritura al propietario y nada al resto.
Configurar propietario apropiado para que el master de nginx pueda leer la clave; en la instalación habitual Ubuntu con master root:
~~~bash
sudo chown root:root /etc/nginx/certs/metadata.local-key.pem
~~~
chown cambia propietario:grupo a root:root.

Agregar las tres líneas HTTPS de la tabla, validar y recargar. Probar:
~~~bash
curl https://metadata.local
~~~
HTTPS usa 443 por defecto. El cliente debe confiar en la CA de mkcert y el nombre debe resolver. No usar -k para ocultar fallos de confianza. mkcert no configura nginx por sí mismo. Mantener listen 80 si sigue siendo exigible la URL HTTP original. No se ejecutó esta variante durante la práctica.

### Otras variantes que ya cayeron en parciales de nginx
Las de arriba son cambios de datos sobre ESTE ejercicio. Estas son otras consignas de nginx que aparecieron en parciales anteriores (2021, 2022, 2025 2C). Probadas en un nginx 1.24 aislado, salvo donde se aclara.

| Tipo de consigna | Qué piden | Dónde mirar abajo |
|---|---|---|
| Varios sitios en el mismo servidor | "hosting" de varios nombres; cualquier otro nombre muestra "What?" | A |
| Proxy sin cambiar la URL | el usuario entra a `publico.protos.foo` y ve el contenido de `parcial.protos.foo` | B |
| Proxy con compresión transparente | el cliente pide gzip y recibe comprimido aunque el backend no comprima | C |
| Headers extra | agregar uno hacia el backend, o uno hacia el cliente | D |
| Servir archivos propios | un sitio con su carpeta e `index.html` | E |
| HTTPS | redirigir HTTP a HTTPS, o hablar HTTPS con el backend | F |

#### A. Varios sitios y un `default_server` que responde "What?"
~~~nginx
server {
    listen 80 default_server;
    return 200 "What?\n";
}
server {
    listen 80;
    server_name a.protos.local;
    location / { proxy_pass http://127.0.0.1:9101; }
}
~~~
- nginx elige el bloque comparando el header `Host` de la petición con cada `server_name`. Si ninguno coincide, usa el que tenga `default_server`.
- `return 200 "What?\n";` responde directamente desde nginx, sin archivos ni backend.
- Solo puede haber UN `default_server` por cada par IP:puerto. Si hay dos, `nginx -t` falla con `a duplicate default server for 0.0.0.0:80`.
- Resultado probado: `curl http://127.0.0.1:8101/` (Host que no coincide con ningún sitio) → `What?`.

#### B. Proxy "sin cambiar la URL": proxy, no redirección
Si piden que la URL del navegador se mantenga, la solución es `proxy_pass`. Con una redirección el cliente ve cambiar la URL, y no cumple.
~~~nginx
# CORRECTO: la URL del cliente no cambia
location / { proxy_pass http://parcial.protos.foo; }

# INCORRECTO para esta consigna: el cliente recibe 301 y la URL cambia
return 301 http://parcial.protos.foo$request_uri;
~~~
- Probado con `curl -i`: la redirección devuelve `HTTP/1.1 301 Moved Permanently` y `Location: http://backend.test/x`. El proxy devuelve directamente `200` con el contenido.
- Si el backend es un virtual host, agregá `proxy_set_header Host parcial.protos.foo;` (ver "Dos peticiones y dos nombres").

#### C. Compresión transparente (gzip) delante de un backend
~~~nginx
server {
    listen 80;
    server_name publico.local;
    gzip on;
    gzip_types application/json text/plain text/html;
    gzip_min_length 1;
    location / { proxy_pass http://127.0.0.1:9101; }
}
~~~
Verificar que comprime solo cuando el cliente lo pide:
~~~bash
curl -s -D - -o /dev/null -H "Accept-Encoding: gzip" http://publico.local     # debe verse Content-Encoding: gzip
curl -s -D - -o /dev/null -H "Accept-Encoding: identity" http://publico.local # no debe aparecer Content-Encoding
curl -s --compressed http://publico.local                                      # curl descomprime solo
~~~
- Es "transparente" porque el cliente no hace nada especial: nginx comprime solo si el cliente anuncia `Accept-Encoding: gzip`.
- En mi prueba con un JSON de 2172 bytes, la respuesta con gzip fue de 76 bytes y sin gzip, 2172.
- `gzip_types`: por defecto nginx solo comprime `text/html`. Si el backend devuelve JSON o texto plano, hay que listarlo o no comprime.
- `gzip_min_length`: las respuestas más chicas que ese umbral (por defecto 20 bytes) no se comprimen. Con respuestas chicas de práctica, ponerlo en 1.
- `-D -` muestra los headers de respuesta en pantalla y `-o /dev/null` descarta el cuerpo (que es binario si está comprimido).

#### D. Dos tipos de header, no confundirlos
| Directiva | Hacia dónde va | Ejemplo |
|---|---|---|
| `proxy_set_header` | la petición que nginx le manda al **backend** | `proxy_set_header Metadata true;` |
| `add_header` | la respuesta que nginx le manda al **cliente** | `add_header X-Via-Proxy si always;` |

- `always` hace que el header se agregue también en respuestas de error (404, 500).
- Probado: el backend registró `Metadata=true` y el cliente vio `X-Via-Proxy: si`.
- Para pedirle al backend otro idioma o formato: `proxy_set_header Accept-Language es;`.
- En el parcial, dejá la línea `Accept: application/json` aunque en la práctica fuera opcional: no cuesta nada y cubre el caso de que el backend real sí la exija.

#### E. Servir archivos propios (sitio estático)
~~~nginx
server {
    listen 80;
    server_name sitio.local;
    root /var/www/sitio;
    index index.html;
}
~~~
- `root` es la carpeta base y `index` el archivo que se sirve para `/`.
- Error típico: **403 Forbidden**. El worker de nginx corre como `www-data` y necesita permiso de lectura en el archivo y de **entrada (x)** en cada carpeta del camino. Probado: con `root` dentro de una carpeta privada dio 403; con una carpeta legible, 200.
- Solución: `sudo chmod -R a+rX /var/www/sitio` y revisar el camino completo con `namei -l /var/www/sitio/index.html`.

#### F. HTTPS: redirigir y hablar con un backend HTTPS
~~~nginx
# Redirigir HTTP a HTTPS (probado: devuelve 301 con Location: https://<host><ruta>)
server {
    listen 80;
    server_name metadata.local;
    return 301 https://$host$request_uri;
}

# Backend que habla HTTPS (solo se validó la sintaxis con nginx -t; no se probó contra un backend real)
location / {
    proxy_pass https://otro.protos.foo;
    proxy_ssl_server_name on;
    proxy_set_header Host otro.protos.foo;
}
~~~
- `$host` es el nombre que pidió el cliente y `$request_uri` la ruta con sus parámetros: así la redirección conserva a dónde iba el usuario.
- `proxy_ssl_server_name on;` hace que nginx envíe el nombre del backend en el saludo TLS (SNI). Sin esto, un backend con varios certificados puede devolver el equivocado.
- Si `curl https://metadata.local` falla por certificado y usaste mkcert: `curl --cacert "$(mkcert -CAROOT)/rootCA.pem" https://metadata.local`. Sirve para demostrar que el problema es de confianza y no de nginx. No uses `-k` para taparlo.

#### Probar vhosts sin editar /etc/hosts
~~~bash
curl -H "Host: a.protos.local" http://127.0.0.1/
curl --resolve a.protos.local:80:127.0.0.1 http://a.protos.local/
~~~
- `-H "Host: ..."` cambia solo el header Host y va a la IP que indiques. Sirve para ver qué `server` de nginx responde.
- `--resolve nombre:puerto:IP` hace que curl use esa IP para ese nombre en esta invocación, sin tocar `/etc/hosts`. Probado: funciona con la URL con el nombre completo.
- Para la consigna "curl sin opciones" igual necesitás la entrada en `/etc/hosts`; estas dos opciones son para tus pruebas.

#### Errores de `nginx -t` que conviene reconocer
| Mensaje | Causa | Arreglo |
|---|---|---|
| `host not found in upstream "x"` | nginx resuelve el nombre del backend al validar/arrancar y no lo encontró | Revisar el nombre, agregar `/etc/hosts` o usar la IP más `proxy_set_header Host` |
| `a duplicate default server for 0.0.0.0:80` | dos `default_server` en el mismo puerto | Dejar uno solo |
| `unknown directive "xyz"` | directiva mal escrita o módulo ausente | Revisar ortografía |
| `unexpected "}"` / `directive is not terminated by ";"` | falta `;` o `{` | Revisar la línea que marca el error |
| 403 al servir archivos | permisos de `www-data` | Ver E |

`sudo nginx -T` (T mayúscula) valida y además **imprime toda la configuración efectiva**, incluidos los `include`. Sirve para mostrar en el video qué está cargando nginx realmente.

#### Receta corta para cualquier ejercicio de nginx
1. `systemctl status nginx`: mostrar el estado inicial.
2. Entender qué piden: ¿vhost, proxy, compresión, header, HTTPS? Mirar la tabla del principio.
3. Probar el backend directo con `curl -i` (qué exige, qué devuelve).
4. Escribir el sitio en `sites-available`, enlazar en `sites-enabled`.
5. `sudo nginx -t` y `sudo systemctl reload nginx`.
6. Probar con el cliente exacto que pide la consigna y mostrar los logs si algo falla.

## 12. Limpieza realizada y estado final
El usuario pidió retirar el backend temporal y evitar interferencias con ejercicios futuros.
1. Se indicó Ctrl+C en la terminal Python para detenerlo.
2. Se eliminó el archivo:
~~~bash
rm /tmp/metadata-practica.py
~~~
rm elimina ese archivo.
3. Se cambió proxy_pass al backend real en sites-available.
4. Se comentó la entrada de /etc/hosts:
~~~text
# 127.0.0.1 metadata.local
~~~
5. Se retiró el enlace:
~~~bash
sudo rm /etc/nginx/sites-enabled/metadata.local
~~~
Borra el enlace, conserva sites-available/metadata.local.
6. Se indicó nginx -t y luego systemctl reload nginx con sudo; el estudiante confirmó finalización.

Ahora el sitio está deshabilitado, la entrada hosts inactiva y el backend temporal retirado. La configuración de solución permanece guardada. No se espera que curl metadata.local siga funcionando tras limpiar.

Para repetir: descomentar hosts, habilitar el enlace, validar y recargar; usar backend real disponible o recrear el temporal.

## Justificación breve para el parcial
“Resuelvo metadata.local hacia esta máquina y nginx actúa como proxy inverso: reenvía la petición al backend agregando Metadata: true, de modo que el cliente obtiene el JSON con curl sin opciones.”

En nuestra práctica, aclarar que el éxito se verificó contra un backend equivalente, porque el del enunciado no estaba accesible.

## Guardar el apunte en la VM
Descargar 26.1-2.md. Si queda en ~/Descargas:
~~~bash
mkdir -p ~/protos/soluciones
~~~
mkdir y -p crean el directorio con sus padres; ~ es tu directorio personal.
~~~bash
cp ~/Descargas/26.1-2.md ~/protos/soluciones/26.1-2.md
~~~
cp copia desde la primera ruta a la segunda. Ajustar la carpeta de descarga si difiere. El asistente no escribió directamente en la VM.

## Referencias oficiales para ampliar
- [Proxy, headers y rutas](https://nginx.org/en/docs/http/ngx_http_proxy_module.html)
- [Formato de logs](https://nginx.org/en/docs/http/ngx_http_log_module.html)
- [Gzip](https://nginx.org/en/docs/http/ngx_http_gzip_module.html)
- [HTTPS en nginx](https://nginx.org/en/docs/http/configuring_https_servers.html)
- [mkcert](https://github.com/FiloSottile/mkcert)

