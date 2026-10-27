# nginx: todas las variantes (mapa + las que faltaban)

Las tres recetas de nginx del repo ya cubren lo que salió en los parciales. Este archivo hace dos cosas:
1. **Mapa:** para cada cosa que te pueden pedir, en qué receta está.
2. **Lo que faltaba:** usuario y contraseña, permitir o bloquear por IP, redirección 301 a propósito, contenido distinto por ruta, rewrite, sitio con listado de archivos, solo GET, página de error propia, varios backends, caché, CORS, ocultar la versión, idioma.

Todo lo de la parte 2 se probó en un nginx 1.24 aislado con `curl`; las salidas de abajo son reales.

---

## ⭐ Regla rápida (leer primero)

| El enunciado pide… | Directiva clave | Dónde está |
|---|---|---|
| Varios sitios; cualquier otro nombre ve "What?" | `server_name`, `listen 80 default_server`, `return 200` | `proxy-metadata-headers_1c2026.md` §A |
| Servir el contenido de otro host **sin cambiar la URL** | `proxy_pass` + `proxy_set_header Host` | `proxy-publico-url-sin-cambiar_2c2025.md` |
| Lo anterior + **comprimido** (gzip) | `gzip on; gzip_types; gzip_vary` | `proxy-gzip_2c2021.md` |
| El backend exige un header | `proxy_set_header Nombre valor;` | `proxy-metadata-headers_1c2026.md` |
| Agregar un header en la **respuesta** al cliente | `add_header Nombre valor always;` | `proxy-metadata-headers_1c2026.md` §D |
| Servir archivos propios (index.html) | `root`, `index` | `proxy-metadata-headers_1c2026.md` §E |
| HTTPS, certificado, mkcert, redirigir a HTTPS | `listen 443 ssl; ssl_certificate` | `proxy-metadata-headers_1c2026.md` §F y `proxy-gzip_2c2021.md` |
| Solo una ruta al backend (`/api/`), con o sin prefijo | `location /api/ { proxy_pass http://x/; }` | `proxy-publico-url-sin-cambiar_2c2025.md` + 4 abajo |
| Escuchar en otro puerto / backend en otro puerto | `listen 8080;` / `proxy_pass http://x:8080;` | las tres recetas |
| **Usuario y contraseña** | `auth_basic` + `htpasswd` | **1** |
| **Solo desde cierta IP** / bloquear una IP | `allow` / `deny` | **2** |
| **Redirigir** a otra URL (que sí cambie) | `return 301 URL;` | **3** |
| **Distinto contenido según la ruta** | varios `location` | **4** |
| Cambiar la ruta (`/viejo/x` → `/nuevo/x`) | `rewrite` | **5** |
| Listado de archivos de una carpeta | `autoindex on;` | **6** |
| Solo permitir GET | `limit_except GET { deny all; }` | **7** |
| Página de error propia | `error_page 404 /404.html;` | **8** |
| **Dos backends / balanceo** | `upstream` | **9** |
| Pasarle al backend la IP real del cliente | `X-Real-IP`, `X-Forwarded-For` | **9** |
| Cachear lo del backend | `proxy_cache` | **10** |
| CORS | `add_header Access-Control-Allow-Origin` | **11** |
| Ocultar la versión de nginx | `server_tokens off;` | **11** |
| Responder según el idioma del cliente | `$http_accept_language` | **12** |

### ⚠️ Trampa confirmada en la prueba: `return` se saltea la autenticación
Si en un `location` ponés `auth_basic` (o `allow`/`deny`) **y** `return 200 "..."`, nginx responde **sin pedir contraseña**. Lo probé: con `return`, entró sin clave y desde una IP bloqueada. Es así porque `return` se ejecuta antes de la fase de acceso. **Con auth o allow/deny, servir archivos (`root`/`index`) o hacer `proxy_pass`, nunca `return`.**

### Procedimiento fijo (siempre igual)
~~~bash
sudo systemctl status nginx                           # mostrar estado inicial
sudo nano /etc/nginx/sites-available/SITIO
sudo ln -s /etc/nginx/sites-available/SITIO /etc/nginx/sites-enabled/
echo "127.0.0.1 nombre.local" | sudo tee -a /etc/hosts   # si el nombre es inventado
sudo nginx -t                                         # tiene que decir "test is successful"
sudo systemctl restart nginx
curl -i http://nombre.local/                          # -i muestra status y headers
~~~

---

## 1. Usuario y contraseña (HTTP Basic)

~~~bash
sudo apt install apache2-utils                 # trae htpasswd
sudo htpasswd -c /etc/nginx/.htpasswd admin    # -c crea el archivo; pide la clave
# sin apache2-utils:
printf 'admin:%s\n' "$(openssl passwd -apr1 secreto)" | sudo tee /etc/nginx/.htpasswd
~~~
~~~nginx
server {
    listen 80;
    server_name privado.local;
    root /var/www/privado;
    location / {
        auth_basic "Zona privada";                  # texto que muestra el navegador
        auth_basic_user_file /etc/nginx/.htpasswd;  # usuarios y hashes
    }
}
~~~
Con proxy: misma idea, `proxy_pass` dentro del `location` en vez de `root`.

Prueba real:
~~~text
curl -i http://privado.local/                    → 401 Unauthorized + WWW-Authenticate: Basic realm="Zona privada"
curl -i -u admin:secreto http://privado.local/   → 200 OK  contenido privado
curl -i -u admin:mal http://privado.local/       → 401 Unauthorized
~~~
Para el video: "Basic manda usuario:clave en base64, que no es cifrado; por eso en serio se usa con HTTPS."

## 2. Permitir o bloquear por IP

~~~nginx
location / {
    allow 192.168.50.0/24;   # se evalúan en orden; gana la primera que coincide
    allow 127.0.0.1;
    deny  all;               # el resto: 403
}
~~~
Bloquear una sola: `deny 10.0.0.5; allow all;`.

Prueba real (permitido solo 127.0.0.2): desde 127.0.0.1 → `403 Forbidden`; desde 127.0.0.2 → `200 OK`.

## 3. Redirección (cuando SÍ quieren que cambie la URL)

~~~nginx
server {
    listen 80;
    server_name viejo.local;
    return 301 http://nuevo.local$request_uri;   # $request_uri conserva ruta y query
}
~~~
Prueba real: `curl -i http://viejo.local/algo?x=1` → `301 Moved Permanently` y `Location: http://nuevo.local/algo?x=1`.
- `301` = permanente; `302` = temporal (`return 302 ...`).
- Es lo **contrario** del proxy: con redirect el navegador cambia la URL; con `proxy_pass` no.
- `curl -L` sigue la redirección.

## 4. Contenido distinto según la ruta

~~~nginx
server {
    listen 80;
    server_name rutas.local;
    default_type text/plain;                      # para que return 200 salga como texto
    location = /      { return 200 "raiz\n"; }    # "=" coincide SOLO con "/"
    location /hola    { return 200 "Hola mundo\n"; }
    location /api/    { proxy_pass http://127.0.0.1:9101/; }   # /api/x → backend /x
}
~~~
Prueba real: `/` → `raiz`; `/hola` → `Hola mundo`; `/api/` → contenido del backend.

Cómo elige nginx el `location`:
1. `location = /exacto` (coincidencia exacta) gana siempre.
2. Si no, el **prefijo más largo** (`/api/` le gana a `/`).
3. Los `location ~ regex` se prueban después, en orden de aparición.

`proxy_pass http://x/;` **con barra final** saca el prefijo (`/api/foo` → `/foo`); **sin barra** lo conserva (`/api/foo` → `/api/foo`).

## 5. Reescribir la ruta

~~~nginx
location /viejo/ {
    rewrite ^/viejo/(.*)$ /nuevo/$1 permanent;   # permanent = 301; redirect = 302
}
~~~
Prueba real: `/viejo/abc` → `301` con `Location: http://rutas.local/nuevo/abc`. `$1` es lo que capturó el `(.*)`. Sin `permanent`/`redirect` (o con `last`) se reescribe **internamente**, sin que el cliente lo vea.

## 6. Listado de archivos

~~~nginx
location /files/ {
    root /var/www;        # sirve /var/www/files/...
    autoindex on;         # muestra la lista si no hay index.html
}
~~~
`root` **concatena** la ruta (`/files/a.txt` → `/var/www/files/a.txt`); `alias` la **reemplaza** (`location /files/ { alias /srv/datos/; }` → `/srv/datos/a.txt`).

Si da `403`: permisos. `sudo chmod -R o+rX /var/www`, porque nginx corre como `www-data`.

## 7. Solo GET

~~~nginx
location /solo-get {
    limit_except GET { deny all; }   # GET (y HEAD) pasan; POST, PUT, DELETE → 403
    root /var/www;
}
~~~
Prueba real: `curl -i .../solo-get/` → `200`; `curl -i -X POST .../solo-get/` → `403 Forbidden`.

## 8. Página de error propia

~~~nginx
server {
    root /var/www/sitio;
    error_page 404 /404.html;
    location = /404.html { internal; }   # no se puede pedir directamente
}
~~~
Prueba real: `/noexiste` → `404 Not Found` con el contenido de `404.html`. Varios códigos: `error_page 500 502 503 504 /50x.html;`.

## 9. Varios backends (balanceo) e IP real del cliente

~~~nginx
upstream backends {               # va en http {} (cualquier archivo de sites-enabled sirve)
    server 10.0.0.11:80;
    server 10.0.0.12:80;
    # server 10.0.0.13:80 backup;   # solo si los otros caen
    # server 10.0.0.11:80 weight=3; # recibe 3 veces más pedidos
}
server {
    listen 80;
    server_name lb.local;
    location / {
        proxy_pass http://backends;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
~~~
Prueba real: dos `curl` seguidos → `backend1`, después `backend2` (round-robin, el reparto por defecto). `ip_hash;` dentro del `upstream` manda siempre al mismo backend según la IP del cliente.

`X-Real-IP` / `X-Forwarded-For`: sin esto, el backend ve como cliente a nginx (127.0.0.1), no al usuario real.

## 10. Caché del proxy

~~~nginx
proxy_cache_path /var/cache/nginx/micache keys_zone=micache:10m;   # en http {}
server {
    location / {
        proxy_pass http://backend;
        proxy_cache micache;
        proxy_cache_valid 200 1m;
        add_header X-Cache $upstream_cache_status always;   # para demostrarlo
    }
}
~~~
Prueba real: primer pedido `X-Cache: MISS`, segundo `X-Cache: HIT`.

## 11. CORS y ocultar la versión

~~~nginx
server_tokens off;                                        # Server: nginx (sin versión)
add_header Access-Control-Allow-Origin "*" always;        # o un origen concreto
proxy_hide_header X-Powered-By;                           # saca un header que manda el backend
~~~
Prueba real: la respuesta trae `Access-Control-Allow-Origin: *` y `Server: nginx` sin número de versión.

## 12. Responder según el idioma (`Accept-Language`)

~~~nginx
location / {
    default_type text/plain;
    if ($http_accept_language ~* "^es") { return 200 "Hola\n"; }
    return 200 "Hello\n";
}
~~~
Prueba real: con `-H 'Accept-Language: es-AR,es;q=0.9'` → `Hola`; sin el header → `Hello`. Cualquier header del cliente se lee como `$http_nombre_en_minusculas_con_guiones_bajos`.

---

## Si algo falla

| Ves | Causa | Arreglo |
|---|---|---|
| Entra sin pedir contraseña | Hay un `return` en ese `location` | Servir con `root` o `proxy_pass` |
| `403` en todo un sitio | Permisos, o `deny` | `chmod -R o+rX`; revisar el orden de `allow`/`deny` |
| `401` con la clave correcta | Ruta mal en `auth_basic_user_file`, o archivo ilegible | `sudo cat /etc/nginx/.htpasswd`; permisos de lectura |
| La URL cambia y no debía | Usaste `return 301` o `rewrite ... permanent` | Para "sin cambiar la URL" es `proxy_pass` |
| `/api/x` llega mal al backend | Barra final de `proxy_pass` | Con barra saca el prefijo; sin barra lo conserva |
| `"upstream" directive is not allowed here` | `upstream` dentro de `server` | Moverlo afuera del `server` |
| `return 200` descarga un archivo | Falta el tipo | `default_type text/plain;` |
| Cambios que no se ven | No recargaste o falló `nginx -t` | `sudo nginx -t && sudo systemctl reload nginx` |
