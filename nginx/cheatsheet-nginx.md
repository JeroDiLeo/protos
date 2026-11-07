# Cheatsheet: nginx (sitios, proxy inverso, variantes)

Recetas de parciales: [proxy-metadata-headers_1c2026.md](proxy-metadata-headers_1c2026.md) · [proxy-publico-url-sin-cambiar_2c2025.md](proxy-publico-url-sin-cambiar_2c2025.md) · [proxy-gzip_2c2021.md](proxy-gzip_2c2021.md) · todas las variantes con prueba: [nginx-variantes-extra.md](nginx-variantes-extra.md).

---

## 1. Procedimiento (siempre igual)

~~~bash
sudo systemctl status nginx                                   # 1. estado inicial (lo piden en el video)
sudo apt install nginx                                        #    si no está
sudo nano /etc/nginx/sites-available/SITIO                    # 2. escribir el sitio
sudo ln -s /etc/nginx/sites-available/SITIO /etc/nginx/sites-enabled/   # 3. habilitarlo
sudo rm /etc/nginx/sites-enabled/default                      #    si choca con el default (opcional)
echo "127.0.0.1 nombre.local" | sudo tee -a /etc/hosts        # 4. si el nombre es inventado
sudo nginx -t                                                 # 5. "syntax is ok / test is successful"
sudo systemctl restart nginx                                  # 6. (o: sudo systemctl reload nginx)
curl -i http://nombre.local/                                  # 7. demostrar
~~~
Si algo falla: `sudo nginx -t`, `sudo journalctl -u nginx -e`, `sudo tail -f /var/log/nginx/error.log`.

### Archivos
| Ruta | Qué es |
|---|---|
| `/etc/nginx/nginx.conf` | configuración principal (bloque `http { … }`, incluye los sitios) |
| `/etc/nginx/sites-available/` | sitios escritos |
| `/etc/nginx/sites-enabled/` | sitios activos (symlinks a los de available) |
| `/etc/nginx/conf.d/*.conf` | otra forma de agregar config (se incluye sola) |
| `/var/www/html/` | raíz por defecto |
| `/var/log/nginx/access.log` / `error.log` | logs |

---

## 2. Anatomía de un sitio

~~~nginx
server {
    listen 80;                         # puerto (y opcional IP: listen 10.0.0.5:80;)
    server_name nombre.local www.nombre.local;   # a qué Host responde

    location / {                       # para qué rutas
        proxy_pass http://backend:8080;   # o root/index, o return
    }
}
~~~
- Cada directiva termina en **`;`**. Los bloques van entre `{ }`.
- `server` elige por **puerto + `Host`** (`server_name`). Si ninguno coincide → el `default_server` de ese puerto (o el primero).
- `location` elige por **ruta**.
- Comentarios con `#`.

### Cómo elige el `location`
| Forma | Significa | Prioridad |
|---|---|---|
| `location = /exacta` | solo esa ruta exacta | 1ª |
| `location ^~ /prefijo/` | prefijo, y no mira regex | 2ª |
| `location ~ \.php$` | regex (distingue mayúsculas) | 3ª (la primera que coincida, en orden) |
| `location ~* \.(jpg\|png)$` | regex sin distinguir mayúsculas | 3ª |
| `location /prefijo/` | prefijo (gana el más largo) | 4ª |
| `location /` | todo lo demás | última |

---

## 3. Directivas

### Servir archivos
| Directiva | Qué hace |
|---|---|
| `root /var/www/sitio;` | carpeta base: `/a/b.html` → `/var/www/sitio/a/b.html` |
| `alias /otra/carpeta/;` | (dentro de un location) reemplaza el prefijo del location |
| `index index.html;` | archivo por defecto de una carpeta |
| `try_files $uri $uri/ =404;` | probar archivo, carpeta, y si no 404 |
| `autoindex on;` | listado de la carpeta |
| `default_type text/plain;` | tipo si no se reconoce la extensión |

### Responder directo
| Directiva | Qué hace |
|---|---|
| `return 200 "texto\n";` | responde ese texto (con `default_type text/plain;` o `add_header Content-Type`) |
| `return 301 https://otro/$request_uri;` | redirección permanente (la URL **cambia**) |
| `return 302 /otra;` | redirección temporal |
| `return 403;` / `return 404;` | error |
| `rewrite ^/viejo/(.*)$ /nuevo/$1 last;` | cambia la ruta internamente (`redirect`/`permanent` = redirige al cliente) |

⚠ `return` se ejecuta **antes** que `auth_basic` y `allow/deny`: si los combinás, entra sin pedir nada. Con auth/IP, servir con `root` o `proxy_pass`.

### Proxy inverso
| Directiva | Qué hace |
|---|---|
| `proxy_pass http://IP:PUERTO;` | manda el pedido al backend (la URL del cliente **no cambia**) |
| `proxy_set_header Host $host;` | le pasa al backend el Host que pidió el cliente |
| `proxy_set_header Host backend.foo;` | le manda un Host fijo (backend con vhosts) |
| `proxy_set_header X-Real-IP $remote_addr;` | IP real del cliente |
| `proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;` | cadena de IPs |
| `proxy_set_header X-Forwarded-Proto $scheme;` | http/https original |
| `proxy_set_header Nombre "valor";` | **header que exige el backend** |
| `proxy_set_header Accept-Encoding "";` | que el backend no comprima (lo hace nginx) |
| `proxy_hide_header X-Algo;` | ocultar un header de la respuesta del backend |
| `proxy_redirect http://backend/ /;` | reescribe `Location` del backend |
| `proxy_http_version 1.1;` | HTTP/1.1 al backend (websockets, keepalive) |
| `proxy_connect_timeout 5s;` / `proxy_read_timeout 60s;` | timeouts |
| `proxy_ssl_server_name on;` | backend **https** con SNI |
| `resolver 8.8.8.8;` | si `proxy_pass` usa una variable/nombre a resolver en runtime |

### ⚠ La barra al final de `proxy_pass`
| Config | Pedido `/api/users` llega al backend como |
|---|---|
| `location /api/ { proxy_pass http://b:8080; }` | `/api/users` (pasa la ruta **tal cual**) |
| `location /api/ { proxy_pass http://b:8080/; }` | `/users` (**saca** el prefijo `/api/`) |
| `location /api/ { proxy_pass http://b:8080/v2/; }` | `/v2/users` (reemplaza el prefijo) |

Regla: **si `proxy_pass` tiene ruta (aunque sea solo `/`), reemplaza la parte que coincidió con el `location`.**

### Headers de respuesta
| Directiva | Qué hace |
|---|---|
| `add_header X-Algo "valor" always;` | agrega un header a la respuesta (`always` = también en errores) |
| `add_header Content-Type text/plain;` | — (mejor `default_type`) |
| `server_tokens off;` | oculta la versión de nginx en `Server:` |
| `expires 1h;` | `Cache-Control`/`Expires` |

`add_header` en un `location` **anula** los del `server` (no se suman): repetirlos.

### Compresión (gzip)
~~~nginx
gzip on;
gzip_types text/plain text/css application/json application/javascript text/xml;
gzip_vary on;              # agrega Vary: Accept-Encoding
gzip_proxied any;          # comprimir también lo que viene de proxy_pass
gzip_min_length 20;        # por defecto 20 bytes; respuestas chicas no se comprimen
proxy_set_header Accept-Encoding "";   # el backend manda sin comprimir, comprime nginx
~~~
`text/html` se comprime siempre que `gzip on`; no hace falta ponerlo en `gzip_types`.

### Acceso
| Directiva | Qué hace |
|---|---|
| `auth_basic "Zona";` + `auth_basic_user_file /etc/nginx/.htpasswd;` | usuario y contraseña |
| `allow 10.0.0.0/24; deny all;` | solo esa red (se evalúan **en orden**) |
| `deny 10.0.0.5; allow all;` | bloquear una IP |
| `satisfy any;` | alcanza con IP **o** contraseña (por defecto `all`: las dos) |
| `limit_except GET { deny all; }` | solo GET (y HEAD); el resto `403` |
| `if ($request_method !~ ^(GET\|HEAD)$) { return 405; }` | idem con 405 |
| `client_max_body_size 10m;` | tamaño máximo del cuerpo (si no, `413`) |
| `limit_req_zone …` / `limit_req zone=… ;` | rate limit (`503`/`429`) |

Crear usuarios:
~~~bash
sudo apt install apache2-utils
sudo htpasswd -c /etc/nginx/.htpasswd usuario       # -c solo la primera vez (crea el archivo)
# sin apache2-utils:
printf 'usuario:%s\n' "$(openssl passwd -apr1 'clave')" | sudo tee /etc/nginx/.htpasswd
~~~

### Varios backends
~~~nginx
upstream backs {
    server 10.0.0.10:8080;
    server 10.0.0.11:8080 weight=2;
    server 10.0.0.12:8080 backup;
    # least_conn;  ip_hash;
}
server { listen 80; location / { proxy_pass http://backs; } }
~~~

### HTTPS
~~~nginx
server {
    listen 443 ssl;
    server_name nombre.local;
    ssl_certificate     /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    location / { proxy_pass http://127.0.0.1:8080; }
}
server { listen 80; server_name nombre.local; return 301 https://$host$request_uri; }
~~~
~~~bash
sudo mkdir -p /etc/nginx/ssl
sudo openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
  -keyout /etc/nginx/ssl/key.pem -out /etc/nginx/ssl/cert.pem -subj "/CN=nombre.local"
curl -k https://nombre.local/          # -k: certificado autofirmado
~~~

### Páginas de error y otros
| Directiva | Qué hace |
|---|---|
| `error_page 404 /404.html;` + `location = /404.html { internal; }` | página propia |
| `error_page 500 502 503 504 /50x.html;` | idem para 5xx |
| `proxy_intercept_errors on;` | usar tus `error_page` también para errores del backend |
| `access_log /var/log/nginx/sitio.log;` / `access_log off;` | log propio |
| `proxy_cache_path …` + `proxy_cache zona;` | caché (ver variantes) |

### Variables útiles
`$host` (Host pedido) · `$remote_addr` (IP cliente) · `$request_uri` (ruta + query original) · `$uri` (ruta normalizada) · `$args` / `$arg_nombre` (query) · `$http_NOMBRE` (header del pedido, en minúscula y `_`: `$http_accept_language`, `$http_x_legajo`) · `$scheme` · `$server_name` · `$request_method` · `$cookie_nombre`.

---

## 4. El enunciado dice → qué poner

| El enunciado dice… | Directiva |
|---|---|
| "que `http://X/` sirva el contenido de `http://Y/`" | `server_name X;` + `proxy_pass http://Y;` |
| "sin que se modifique la URL" / "sin redirección" | `proxy_pass` (**no** `return 301`) |
| "que sí redirija" / "que la URL cambie" | `return 301 http://Y$request_uri;` |
| "el backend exige el header H con valor V" | `proxy_set_header H "V";` |
| "el backend tiene vhosts / espera el Host Y" | `proxy_set_header Host Y;` |
| "la respuesta debe incluir el header H" | `add_header H "V" always;` |
| "cualquier otro nombre debe ver 'What?'" | otro `server { listen 80 default_server; return 200 "What?\n"; }` |
| "contenido comprimido de forma transparente" | `gzip on; gzip_types …; gzip_proxied any; gzip_vary on;` |
| "escuche en el puerto N" | `listen N;` |
| "el backend está en el puerto N" | `proxy_pass http://IP:N;` |
| "solo `/api` va al backend" | `location /api/ { proxy_pass …; }` (barra según si saca el prefijo) |
| "sin el prefijo /api" | `proxy_pass http://b/;` (con `/` final) |
| "pedir usuario y contraseña" | `auth_basic` + `htpasswd` |
| "solo desde la IP/red X" | `allow X; deny all;` |
| "bloquear la IP X" | `deny X; allow all;` |
| "solo GET" | `limit_except GET { deny all; }` |
| "servir los archivos de /carpeta" | `root /carpeta;` + `index index.html;` |
| "mostrar el listado de archivos" | `autoindex on;` |
| "página de error propia" | `error_page 404 /404.html;` |
| "repartir entre dos servidores" | `upstream` |
| "que el backend vea la IP real del cliente" | `proxy_set_header X-Real-IP $remote_addr;` + `X-Forwarded-For` |
| "responder según el idioma" | `map $http_accept_language $idioma { … }` o `if ($http_accept_language ~* ^es)` |
| "HTTPS" | `listen 443 ssl;` + certificado; `return 301 https://…` en el 80 |
| "ocultar la versión" | `server_tokens off;` |
| "solo las opciones estrictamente necesarias" (en curl) | probar con `curl http://X/` sin flags (o `-i` para mostrar) |
| "mostrar que nginx no está corriendo al inicio" | `systemctl status nginx` antes; `stop` si estaba |

---

## 5. Errores de `nginx -t`

| Mensaje | Causa | Arreglo |
|---|---|---|
| `unexpected "}"` / `unexpected end of file, expecting ";" or "}"` | falta un `;` o una llave | revisar la línea anterior a la indicada |
| `unknown directive "X"` | directiva mal escrita, o fuera de lugar | ortografía; módulo instalado |
| `"X" directive is not allowed here` | directiva en un bloque que no corresponde | moverla (`upstream` y `map` van en `http`, fuera de `server`) |
| `duplicate listen options for 0.0.0.0:80` / `a duplicate default server` | dos `default_server` en el mismo puerto | dejar uno (ojo con `sites-enabled/default`) |
| `conflicting server name "X" on 0.0.0.0:80, ignored` (warning) | dos sitios con el mismo `server_name` | sacar uno |
| `host not found in upstream "X"` | `proxy_pass` a un nombre que no resuelve | IP, `/etc/hosts`, o `resolver` |
| `open() "/etc/nginx/.htpasswd" failed` | archivo inexistente (sale en runtime → `500`) | crearlo |
| `cannot load certificate` | ruta del certificado mal | revisar `ssl_certificate` |
| `bind() to 0.0.0.0:80 failed (98: Address already in use)` | otro proceso usa el puerto (apache, otro nginx) | `sudo ss -tlnp \| grep :80` y pararlo |
| `invalid number of arguments in "X"` | sobran/faltan valores | comillas en textos con espacios |

---

## 6. Lo que ves con curl → qué está pasando

| Ves | Significa | Qué revisar |
|---|---|---|
| `curl: (6) Could not resolve host` | el nombre no está en DNS ni `/etc/hosts` | agregar a `/etc/hosts`, o `--resolve` / `-H "Host:"` |
| `curl: (7) Connection refused` | nginx no está escuchando ahí | `systemctl status nginx`, `listen`, `ss -tlnp` |
| responde la página **"Welcome to nginx!"** | cayó en el sitio `default` | `server_name` mal, symlink faltante, falta `/etc/hosts`, no recargaste |
| `301`/`302` cuando pedían "sin cambiar la URL" | usaste `return`/`rewrite … redirect` o el backend redirige | `proxy_pass`; `proxy_redirect`; `proxy_set_header Host` |
| `400 Bad Request` del backend | le falta un header | `proxy_set_header` |
| `401` | `auth_basic` activo | `curl -u usuario:clave` |
| `403 Forbidden` | `deny`, `limit_except`, sin `index` y sin `autoindex`, permisos de archivos | `allow`, `index`, `chmod o+r`, `chmod o+x` en carpetas |
| `404 Not Found` | `root` mal, `location` no coincide, barra de `proxy_pass` | `root`/`alias`, barra final |
| `405 Not Allowed` | POST a archivo estático, o tu regla de métodos | — |
| `413 Request Entity Too Large` | cuerpo grande | `client_max_body_size` |
| `500 Internal Server Error` | bucle de `rewrite`, htpasswd inexistente | `error.log` |
| `502 Bad Gateway` | nginx no pudo conectar con el backend (caído, puerto mal, nombre mal) | `curl` directo al backend; `error.log` dice `connect() failed` |
| `504 Gateway Timeout` | el backend no respondió a tiempo | backend, red, `proxy_read_timeout` |
| sin `Content-Encoding: gzip` | no pediste gzip, tipo no listado, respuesta < `gzip_min_length`, falta `gzip_proxied` | `curl -H "Accept-Encoding: gzip" -i` |
| cambié la config y no cambia nada | no recargaste / editaste el archivo no habilitado | `nginx -t && systemctl reload nginx`; revisar `sites-enabled` |

### Comandos para demostrar
~~~bash
curl -i http://nombre.local/                                   # status + headers + contenido
curl -I http://nombre.local/                                   # solo headers
curl -i -H "Host: nombre.local" http://127.0.0.1/              # sin /etc/hosts
curl -i --resolve nombre.local:80:127.0.0.1 http://nombre.local/
curl -i -H "Accept-Encoding: gzip" http://nombre.local/ -o /dev/null -D -   # ver Content-Encoding
curl --compressed http://nombre.local/                         # descomprime
curl -i -u usuario:clave http://nombre.local/privado/
curl -i -X POST http://nombre.local/                           # probar "solo GET"
curl -i http://otro.local/                                     # probar el default ("What?")
curl -i http://IP_BACKEND:PUERTO/                              # comparar con el backend directo
diff <(curl -s http://nombre.local/) <(curl -s http://backend/) && echo IGUALES
~~~

---

## 7. Plantillas

### Proxy transparente con header al backend + default "What?"
~~~nginx
server {
    listen 80;
    server_name publico.protos.foo;
    location / {
        proxy_pass http://10.0.0.20:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header Metadata "valor-que-pide";
    }
}
server {
    listen 80 default_server;
    server_name _;
    default_type text/plain;
    return 200 "What?\n";
}
~~~

### Archivos con contraseña y solo una red
~~~nginx
server {
    listen 80;
    server_name privado.local;
    root /var/www/privado;
    index index.html;
    location / {
        satisfy all;
        allow 192.168.0.0/24;
        deny all;
        auth_basic "Privado";
        auth_basic_user_file /etc/nginx/.htpasswd;
        try_files $uri $uri/ =404;
    }
}
~~~

### Qué decir en el video
«Defino un `server` con `server_name` para que responda a ese Host; con `proxy_pass` nginx le pide el contenido al backend y se lo devuelve al cliente, así la URL no cambia (no es una redirección). Con `proxy_set_header` le paso al backend los headers que exige, valido con `nginx -t`, recargo y lo demuestro con `curl -i`.»
