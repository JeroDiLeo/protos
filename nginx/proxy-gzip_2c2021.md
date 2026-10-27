# 2C 2021 — Ejercicio 1: proxy inverso y compresión transparente

## Objetivo y resultado

Publicar http://foo.leak.com.ar/ bajo http://foo.example.org/, conservando el nombre público y pasando cualquier ruta al backend. Comprimir las representaciones cuando el cliente lo solicite. El ejercicio de 2C 2022 conserva el proxy y no exige compresión.

El backend real no resolvió en la VM. Se practicó con Python en 127.0.0.1:8082, sin compresión propia. Resultados observados:
- HTML sin gzip: 13284 bytes.
- HTML con gzip: 189 bytes (aproximadamente 98,6 % menos).
- curl --compressed mostró HTML legible.
- Los archivos descargados sin gzip y con descompresión automática fueron idénticos: cmp no imprimió nada.
- JSON y CSS llegaron con Content-Encoding: gzip.
- /chico.txt, de 5 bytes, no se comprimió con gzip_min_length 1000.
- JSON dejó de comprimirse al excluirlo temporalmente de gzip_types y se restauró la lista después.
- El backend real sigue sin verificarse; esta evidencia corresponde al entorno de práctica.

## ⭐ RECETA PARA EL PARCIAL (leer esto primero)

> Lo de abajo ("PRÁCTICA") usó un backend Python en 127.0.0.1:8082. En el parcial el backend es `foo.leak.com.ar` y no hace falta Python. **La compresión es la mitad del puntaje: hay que configurarla Y demostrarla.**

### Pasos
~~~bash
systemctl status nginx                     # 1. mostrar estado (el video pide arrancar mostrando que no corre)
sudo systemctl stop nginx
curl -i http://foo.leak.com.ar/            # 2. ver qué sirve el backend
sudo nano /etc/hosts                       # 3. agregar: 127.0.0.1 foo.example.org
sudo nano /etc/nginx/sites-available/foo.example.org     # 4. el bloque de abajo
sudo ln -s /etc/nginx/sites-available/foo.example.org /etc/nginx/sites-enabled/
sudo nginx -t                              # 5. validar
sudo systemctl start nginx                 #    levantar
~~~

~~~nginx
server {
    listen 80;
    server_name foo.example.org;

    gzip on;
    gzip_types *;
    gzip_min_length 0;
    gzip_vary on;

    location / {
        proxy_pass http://foo.leak.com.ar;
        proxy_set_header Host foo.leak.com.ar;
        proxy_set_header Accept-Encoding "";
        proxy_redirect http://foo.leak.com.ar/ http://foo.example.org/;
    }
}
~~~
Probado en nginx 1.24 contra un backend que no comprime: HTML, JSON y una respuesta de 5 bytes salieron todos con `Content-Encoding: gzip` al pedirlo, y sin comprimir al no pedirlo.

| Línea | Por qué |
|---|---|
| `proxy_pass http://foo.leak.com.ar;` (sin `/` final) | pasa **cualquier ruta** tal cual (`/datos.json` sigue siendo `/datos.json`): la nota dice que pueden pedir cualquier recurso |
| `proxy_set_header Host foo.leak.com.ar;` | el backend recibe su propio nombre. **No usar `$host`**: mandaría `foo.example.org` y un virtual host podría responder otra cosa (error de los apuntes del tercero para 2022) |
| `proxy_set_header Accept-Encoding "";` | le pide al backend contenido **sin comprimir**, para que comprima nginx. Así sé y puedo demostrar quién comprime |
| `gzip on;` | activa la compresión. Solo comprime si el cliente manda `Accept-Encoding: gzip` → eso es lo "transparente" |
| `gzip_types *;` | por defecto **solo se comprime text/html**. Con `*` se comprime cualquier tipo (CSS, JSON, JS…): el backend puede cambiar sus representaciones |
| `gzip_min_length 0;` | no saltea respuestas chicas (por defecto, menos de 20 bytes no se comprimen) |
| `gzip_vary on;` | agrega `Vary: Accept-Encoding`: avisa a las cachés que hay versión comprimida y sin comprimir |
| `proxy_redirect` | si el backend redirige con su nombre, lo reescribe al público → la URL no cambia |

### ¿Cuándo comprimir y cuándo no? (mi nginx.conf tiene `gzip on;` global)
| La consigna... | Qué hago | Por qué |
|---|---|---|
| pide compresión ("comprimido", "transparente", "gzip") | las directivas `gzip` **dentro de mi `server`**, como arriba | no dependo de lo que tenga el nginx.conf de la VM |
| **no dice nada** de compresión (2C 2022, publico.protos.foo, metadata) | **nada**: no deshabilito el `gzip on;` global | el `curl` sin opciones no manda `Accept-Encoding: gzip` → no se comprime; y si un navegador lo pide, el contenido y la URL son los mismos |
| dice explícitamente "no comprimir" | en **mi `server`**: `gzip off;` y en el location `proxy_set_header Accept-Encoding "";` | lo del `server` pisa lo del bloque `http`; la segunda línea evita que el **backend** mande comprimido (gzip off solo frena a nginx) |

No editar el `gzip on;` de `/etc/nginx/nginx.conf`: afecta a **todos** los sitios. Para ver qué rige de verdad:
~~~bash
grep -n gzip /etc/nginx/nginx.conf      # lo global (las líneas con # no rigen)
sudo nginx -T | grep -n gzip            # la configuración efectiva completa, con mis sitios
~~~

### Demostración (las DOS pruebas, si no no se ve que es "transparente")
~~~bash
curl --compressed http://foo.example.org/                                    # A. lo que pide la consigna: negocia gzip y curl lo descomprime
curl -s -D - -o /dev/null -H "Accept-Encoding: gzip" http://foo.example.org/ # B. pidiéndolo → debe aparecer Content-Encoding: gzip
curl -s -D - -o /dev/null http://foo.example.org/                            # C. sin pedirlo → NO debe aparecer Content-Encoding
curl -s -o /dev/null -w '%{size_download}\n' http://foo.example.org/                            # tamaño sin gzip
curl -s -o /dev/null -w '%{size_download}\n' -H "Accept-Encoding: gzip" http://foo.example.org/ # tamaño con gzip (menor)
curl --compressed http://foo.example.org/<otra-ruta>                         # D. cualquier recurso, no solo /
~~~
- `--compressed`: curl anuncia que acepta compresión y descomprime solo. Es "la opción necesaria para negociar" que permite la consigna.
- `-D -` imprime los headers de respuesta; `-o /dev/null` descarta el cuerpo (que comprimido es binario); `-w '%{size_download}'` imprime los bytes recibidos.

### Si algo falla
| Ves | Significa | Arreglo |
|---|---|---|
| `What?` o una respuesta de **6 bytes** | respondió el `default_server` (`"What?\n"` son 6 bytes): tu sitio no está cargado | revisar el enlace en sites-enabled y hacer `sudo nginx -t && sudo systemctl reload nginx`. Esto mismo te pasó en la práctica (sección 7) |
| HTML ok pero sin `Content-Encoding` al pedir gzip | `gzip` no aplica a ese tipo o tamaño | `gzip_types *;` y `gzip_min_length 0;` |
| CSS/JSON sin comprimir | `gzip_types` por defecto solo cubre text/html | `gzip_types *;` |
| `host not found in upstream "foo.leak.com.ar"` en `nginx -t` | tu VM no resuelve el backend | `getent hosts foo.leak.com.ar`; es red/DNS, no tu bloque |
| `502 Bad Gateway` | nginx no llega al backend | `sudo tail /var/log/nginx/error.log` |

### Para el video
"Con `/etc/hosts` llevo `foo.example.org` a nginx y con `proxy_pass` traigo cualquier ruta de `foo.leak.com.ar` sin redirigir, así que la URL no cambia. La compresión es transparente: si el cliente manda `Accept-Encoding: gzip`, nginx responde con `Content-Encoding: gzip` y un cuerpo más chico; si no lo pide, responde sin comprimir. Lo muestro con las dos pruebas y con `curl --compressed`."

---

# PRÁCTICA (detalle de lo que se ejecutó con el backend local)

## 1. Mostrar el estado inicial y detener nginx

~~~bash
systemctl status nginx
sudo systemctl stop nginx
systemctl status nginx
~~~

systemctl administra servicios; status consulta el estado; stop lo detiene; nginx es el nombre del servicio; sudo da permisos administrativos. Si status abre un visor, salir con q. Inicialmente estaba activo. Para la demostración se indicó detenerlo y mostrar inactive (dead); no se recibió una salida pegada de ese estado. Detenerlo interrumpe temporalmente los sitios de nginx sin borrar configuraciones.

## 2. Consultar el backend real

~~~bash
curl -i --connect-timeout 5 --max-time 10 http://foo.leak.com.ar/
~~~

curl realiza la petición; -i muestra cabeceras y cuerpo; --connect-timeout 5 limita la fase de conexión; --max-time 10 limita toda la operación. Ambos tiempos se expresan en segundos.

Se reportó que no pudo resolver el host. Es un fallo de resolución de nombres, anterior a una respuesta HTTP; no es un 404 ni un problema de gzip.

## 3. Backend equivalente de práctica

Verificar puerto libre:

~~~bash
sudo ss -ltnp 'sport = :8082'
~~~

ss consulta sockets; -l selecciona listeners; -t TCP; -n números sin resolver nombres; -p procesos; sport filtra puerto local 8082. Solo encabezados indicaron puerto libre.

Crear el archivo:

~~~bash
nano ~/Downloads/gzip_backend.py
~~~

nano edita; ~ es el home. En una instalación que use Descargas, ajustar el directorio. Guardar con Ctrl+O, Enter; salir con Ctrl+X.

~~~python
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlsplit
import json

class Backend(BaseHTTPRequestHandler):
    def do_GET(self):
        ruta = urlsplit(self.path).path

        if ruta == "/":
            tipo = "text/html"
            contenido = (
                "<!doctype html><html><meta charset='utf-8'>"
                "<h1>Backend de practica: HTML</h1>"
                + "<p>Contenido para probar la compresion.</p>\n" * 300
                + "</html>"
            )
        elif ruta == "/estilo.css":
            tipo = "text/css"
            contenido = "/* CSS de practica */\n" * 400
        elif ruta == "/datos.json":
            tipo = "application/json"
            contenido = json.dumps({"datos": ["practica gzip"] * 400})
        elif ruta == "/texto.txt":
            tipo = "text/plain"
            contenido = "Texto para probar compresion transparente.\n" * 400
        elif ruta == "/app.js":
            tipo = "application/javascript"
            contenido = "// JavaScript de practica\n" * 400
        elif ruta == "/chico.txt":
            tipo = "text/plain"
            contenido = "Hola\n"
        else:
            self.send_error(404, "Recurso inexistente")
            return

        cuerpo = contenido.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", tipo + "; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

print("BACKEND DE PRACTICA: http://127.0.0.1:8082", flush=True)
print("No comprime. Ctrl+C para detener.", flush=True)
HTTPServer(("127.0.0.1", 8082), Backend).serve_forever()
~~~

do_GET procesa GET; urlsplit permite seleccionar la ruta sin la query; json.dumps genera JSON. encode convierte el texto a bytes UTF-8. Se cuenta su longitud en Content-Length y se escribe el cuerpo. No hay algoritmo de compresión en este código. Las repeticiones producen contenido grande, fácil de comprimir. Los recursos desconocidos devuelven 404, como un backend normal.

Levantarlo:

~~~bash
python3 ~/Downloads/gzip_backend.py
~~~

python3 ejecuta el archivo; queda atendiendo en primer plano. Mantener esa terminal abierta; Ctrl+C lo detiene. Solo escucha en la propia VM, puerto 8082.

En otra terminal, pedir gzip directamente:

~~~bash
curl -s -D - -o /dev/null -H "Accept-Encoding: gzip" http://127.0.0.1:8082/
~~~

- -s: modo silencioso, oculta progreso y errores; para diagnóstico puede usarse -sS para conservar errores.
- -D -: vuelca las cabeceras de respuesta a la salida estándar; el guion es el destino.
- -o /dev/null: descarta el cuerpo.
- -H: agrega una cabecera de petición.
- Accept-Encoding: gzip: el cliente declara que puede recibir gzip; no fuerza al servidor.

Se observó HTTP/1.0 200 OK, text/html; charset=utf-8, Content-Length: 13284 y ningún Content-Encoding. Python entregó el HTML sin comprimir incluso cuando se solicitó gzip.

## 4. Revisar gzip en la configuración principal

~~~bash
grep -n -A 18 'gzip on' /etc/nginx/nginx.conf
~~~

grep busca texto; -n muestra números de línea; -A 18 incluye las 18 líneas posteriores. En esta VM se observó:

~~~nginx
gzip on;
gzip_vary on;
gzip_proxied any;
gzip_min_length 100;
gzip_comp_level 6;
# gzip_buffers 16 8k;
# gzip_http_version 1.1;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
~~~

Es la configuración actual de esta máquina, posiblemente modificada por prácticas anteriores; no afirmar que ese es el archivo original de todo Ubuntu. En el ejemplo habitual del paquete, gzip on aparece activo y varias opciones gzip_* aparecen comentadas. Una línea con # no se ejecuta; en su lugar rigen el valor predeterminado del módulo o la herencia.

Elegimos configurar el server del ejercicio sin modificar los demás sitios.

| Directiva | Significado |
| --- | --- |
| gzip on | Activa el filtro gzip, sujeto a negociación y condiciones de respuesta. |
| gzip_types | Selecciona Content-Type adicionales a text/html. Sin ampliación, solo HTML. * permite cualquier MIME. No decide según extensión del archivo. |
| gzip_min_length | Umbral evaluado a partir del Content-Length de la respuesta, no un conteo previo de todo el stream. |
| gzip_vary on | Permite emitir Vary: Accept-Encoding para distinguir representaciones en cachés. No tiene por qué aparecer en todas las respuestas descartadas tempranamente, como la muy pequeña observada. |
| gzip_comp_level 6 | Nivel 1 a 9: más esfuerzo de CPU puede reducir más el tamaño; 6 fue suficiente para la práctica. |
| gzip_proxied any | Permite comprimir peticiones identificadas por el header entrante Via. No significa “es necesario por usar proxy_pass”. No hace falta para nuestro curl directo sin Via. |
| gzip_buffers | Ajusta cantidad y tamaño de buffers de compresión. Se dejó comentado. |
| gzip_http_version | Versión HTTP mínima del cliente; por defecto 1.1. La versión HTTP/1.0 usada por Python en su respuesta no es la versión del cliente a nginx. |

## 5. Resolver el nombre público hacia nginx

~~~bash
sudo nano /etc/hosts
~~~

Agregar o corregir una entrada existente:

~~~text
127.0.0.1 foo.example.org
~~~

El cliente necesita resolver el nombre a la IP de nginx. Aquí ambos corren en la VM. No duplicar entradas contradictorias. En prácticas anteriores BIND resolvía ese nombre a 123.123.123.123; la entrada local permite dirigir las consultas del cliente a nginx sin cambiar aquella zona.

Si el cliente corre en otra máquina, usar la IP alcanzable de la VM en su resolución local o DNS. El destino de proxy_pass es independiente de la resolución del nombre público.

## 6. Archivo del sitio: configuración probada

~~~bash
sudo nano /etc/nginx/sites-available/foo.example.org
~~~

~~~nginx
server {
    listen 80;
    server_name foo.example.org;

    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/javascript;
    gzip_min_length 1000;
    gzip_vary on;
    gzip_comp_level 6;

    location / {
        proxy_pass http://127.0.0.1:8082;
        proxy_set_header Host foo.leak.com.ar;
        proxy_set_header Accept-Encoding "";
        proxy_redirect http://foo.leak.com.ar/ http://foo.example.org/;
    }
}
~~~

- server agrupa el sitio; listen 80 escucha HTTP.
- server_name selecciona el virtual host por el nombre enviado en Host.
- location / cubre las rutas del sitio.
- proxy_pass sin URI adicional conserva la ruta y query al consultar el backend. /datos.json no se convierte en /.
- Host fijo indica el sitio del backend. $host enviaría el nombre público y podría elegir un virtual host incorrecto.
- Por defecto nginx usa $proxy_host para Host: aquí sería 127.0.0.1:8082; con el destino real sería foo.leak.com.ar.
- Accept-Encoding "" omite esa cabecera hacia el backend: se pide contenido plano para comprimirlo en nginx. No elimina la negociación del cliente con nginx.
- proxy_redirect adapta Location y Refresh que coincidan con el prefijo; no genera por sí mismo una redirección al backend ni reescribe enlaces dentro del HTML.
- No usamos sub_filter aquí: la representación puede cambiar y el proxy debe transportarla. Si aparecen URLs absolutas que escapan al backend, analizarlas por separado.

Las cabeceras se modifican dentro de la petición que nginx genera hacia el backend. El cliente continúa pidiendo el nombre público.

## 7. Habilitar, validar y arrancar

~~~bash
sudo ln -s /etc/nginx/sites-available/foo.example.org /etc/nginx/sites-enabled/foo.example.org
sudo nginx -t
sudo systemctl start nginx
~~~

ln -s crea un enlace simbólico: primer camino, archivo existente; segundo, enlace a crear. No copia el contenido. En esta VM nginx.conf incluye sites-enabled/*; guardar solo en sites-available no habilita el sitio. Si ya existe el enlace correcto no repetirlo.

nginx -t valida sintaxis y acceso a archivos referenciados. Si falla, corregir antes de iniciar o recargar. start inicia un servicio detenido; no recarga uno ya activo. reload aplica cambios con sustitución gradual de workers; restart detiene y vuelve a iniciar.

Para aplicar cambios posteriores:

~~~bash
sudo nginx -t && sudo systemctl reload nginx
~~~

&& ejecuta el reload únicamente si la validación termina correctamente.

### Corrección realizada durante la práctica

La primera respuesta pública tenía Content-Length: 6, Last-Modified y ETag, sin gzip. No correspondía al HTML de 13284 bytes. El archivo del sitio era correcto.

Se inspeccionaron habilitación y coincidencias:

~~~bash
ls -l /etc/nginx/sites-enabled/
sudo grep -R -n 'foo.example.org' /etc/nginx/sites-enabled/ /etc/nginx/conf.d/
~~~

ls -l muestra los enlaces y su destino; grep -R recorre siguiendo enlaces y -n indica líneas. El enlace existía y no se encontró otro nombre igual en esas carpetas. Tras validar y recargar, apareció el HTML correcto con gzip. La evidencia es consistente con configuración anterior aún en memoria; no se cambió gzip para solucionar ese síntoma.

Si persiste un sitio incorrecto: revisar resolución, dirección/puerto de escucha, configuración efectiva con sudo nginx -T (valida y vuelca los archivos cargados) y los logs. No confundir selección de sitio con compresión.

## 8. Tres pruebas obligatorias de negociación

### a) Pedir gzip y comprobar cabecera

~~~bash
curl -s -D - -o /dev/null -H "Accept-Encoding: gzip" http://foo.example.org/
~~~

Resultado observado:
- 200 OK.
- Content-Type: text/html; charset=utf-8.
- Vary: Accept-Encoding.
- Content-Encoding: gzip.
- Transfer-Encoding: chunked.

chunked delimita bloques de transferencia; no es un algoritmo de compresión. La compresión se identifica por Content-Encoding. Python no comprimía, así que en este entorno la agregó nginx.

### b) No pedir compresión

~~~bash
curl -s -D - -o /dev/null http://foo.example.org/
~~~

Resultado: 200 OK, Content-Length: 13284, sin Content-Encoding. Vary siguió apareciendo.

### c) Negociación y descompresión automática

~~~bash
curl --compressed http://foo.example.org/
~~~

Es la demostración con solo la opción de negociación permitida por la consigna. --compressed anuncia algoritmos soportados por esa compilación de curl y descomprime la respuesta antes de mostrarla. Se observó HTML legible.

Agregar Accept-Encoding manualmente con -H no activa por sí solo la descompresión automática. Un cliente puede mostrar bytes binarios si pide gzip manualmente y no los decodifica.

## 9. Tamaño y equivalencia del contenido

Comandos de diagnóstico, adicionales a la demostración mínima:

~~~bash
curl -s -o /dev/null -w 'Sin gzip: %{size_download} bytes\n' http://foo.example.org/
curl -s -o /dev/null -H "Accept-Encoding: gzip" -w 'Con gzip: %{size_download} bytes\n' http://foo.example.org/
~~~

-w imprime datos al finalizar; size_download cuenta bytes del cuerpo descargado, sin cabeceras; \n agrega salto de línea. Sin --compressed en la segunda medición se mide el cuerpo comprimido recibido.

Resultados: 13284 y 189 bytes; ahorro = (1 - 189/13284) × 100 ≈ 98,6 %. Ese porcentaje depende del contenido: aquí hay muchas repeticiones, no es una expectativa para cualquier sitio.

~~~bash
curl -s -o /tmp/foo-plano.html http://foo.example.org/
curl -s --compressed -o /tmp/foo-descomprimido.html http://foo.example.org/
cmp /tmp/foo-plano.html /tmp/foo-descomprimido.html
~~~

-o guarda el cuerpo en el archivo; cmp compara bytes y no imprime si son idénticos. Se reportó silencio en los tres comandos. En este backend fijo eso demuestra equivalencia. En uno dinámico, diferencias entre dos pedidos también podrían deberse a cambios legítimos de la representación.

## 10. Cualquier ruta, tipos y respuestas pequeñas

~~~bash
curl -s -D - -o /dev/null -H "Accept-Encoding: gzip" http://foo.example.org/datos.json
curl -s -D - -o /dev/null -H "Accept-Encoding: gzip" http://foo.example.org/estilo.css
curl -s -D - -o /dev/null -H "Accept-Encoding: gzip" http://foo.example.org/chico.txt
~~~

Observado: JSON y CSS con 200 y Content-Encoding: gzip; chico.txt con Content-Length: 5 y sin Content-Encoding, por el mínimo de 1000.

También se pueden probar /texto.txt y /app.js con los mismos comandos o curl --compressed URL; no se recibieron sus salidas durante esta práctica.

Para demostrar el filtro por tipo se cambió temporalmente a:

~~~nginx
gzip_types text/plain;
~~~

La lista del server reemplaza la heredada. Tras -t y reload, /datos.json siguió entregando JSON con 200, Content-Length: 6811 y sin gzip. Se restauró la lista completa, se validó y recargó; luego CSS volvió a verificarse comprimido. HTML sigue siendo elegible aunque no se enumere.

Para demostrar específicamente CSS excluido se puede repetir el mismo ensayo con /estilo.css; no se pegó esa salida durante la exclusión.

## 11. Backend que ya comprime: cómo distinguirlo

Normalmente nginx reenvía Accept-Encoding al backend. Si este responde con Content-Encoding: gzip, nginx puede transmitirlo sin volver a comprimirlo; ver gzip del lado público, por sí solo, no prueba quién lo produjo.

En esta práctica sí conocemos el origen porque:
1. El pedido directo a Python con Accept-Encoding: gzip devolvió plano.
2. El código de Python no comprime.
3. nginx pide plano mediante proxy_set_header Accept-Encoding "".
4. El cliente público recibe gzip cuando lo acepta.

En un servidor real comparar pedidos directos al backend con y sin Accept-Encoding, y revisar las cabeceras que devuelve. Como diagnóstico más concluyente pueden registrarse $upstream_http_content_encoding y $gzip_ratio en un log_format dentro de http: el primero indica qué codificación envió el upstream; el segundo la razón calculada cuando gzip de nginx actúa. No se configuró ese log en esta práctica.

¿Es obligatorio borrar Accept-Encoding hacia el backend? No, si el backend ya negocia correctamente y se garantiza el resultado de la consigna. Es útil para hacer que nginx controle y demuestre la compresión. No descomprime una respuesta si el backend ignora la petición de contenido plano.

## 12. Ajuste final para interpretar “cualquier representación” literalmente

La configuración probada comprime los tipos de texto enumerados y permite omitir respuestas menores a 1000 bytes. Es una política habitual, pero el enunciado no enumera MIME ni tamaños: para evitar depender de ellos, la configuración propuesta para entregar en el parcial usa gzip_types * y gzip_min_length 0.

Este ajuste no se aplicó en la VM, pero se probó después en un nginx 1.24 aparte, con un backend que no comprime: con Accept-Encoding: gzip, HTML (3300 → 57 bytes), JSON (1400 → 39) y una respuesta de 5 bytes salieron con Content-Encoding: gzip. La de 5 bytes creció a 25: comprimir respuestas mínimas no ahorra, pero cumple la consigna literal.

~~~nginx
server {
    listen 80;
    server_name foo.example.org;

    gzip on;
    gzip_types *;
    gzip_min_length 0;
    gzip_vary on;
    gzip_comp_level 6;
    gzip_proxied any;

    location / {
        proxy_pass http://foo.leak.com.ar;
        proxy_set_header Host foo.leak.com.ar;
        proxy_set_header Accept-Encoding "";
        proxy_redirect http://foo.leak.com.ar/ http://foo.example.org/;
    }
}
~~~

* permite cualquier MIME; 0 elimina el descarte por tamaño conocido. gzip_proxied any también permite peticiones entrantes con Via. Para seguir practicando localmente, mantener proxy_pass http://127.0.0.1:8082; en lugar del backend real que no resuelve.

Con ese ajuste, /chico.txt también debería comprimirse si cumple las demás condiciones. Para respuestas pequeñas puede aumentar el tamaño: aquí se prioriza la interpretación literal de la consigna. gzip no convierte en comprimibles respuestas sin cuerpo u otros casos excluidos por el protocolo/filtro.

No usar una copia estática, wget seguido de root, ni gzip_static como única solución para contenido dinámico: las representaciones y rutas del backend pueden cambiar. proxy_pass consulta al origen para cada petición salvo que se configure caché explícitamente, que aquí no se hizo.

## Diferencias con 25.2-4 (publico.protos.foo)

| Elemento | Antes | Ahora |
| --- | --- | --- |
| server_name | publico.protos.foo | foo.example.org |
| Backend real | parcial.protos.foo | foo.leak.com.ar |
| Backend de práctica | 127.0.0.1:8081 | 127.0.0.1:8082 |
| Host al backend | parcial.protos.foo | foo.leak.com.ar |
| proxy_redirect | Prefijos anterior/público | Prefijos foo.leak.com.ar/foo.example.org |
| location / y proxy_pass sin URI | Se usaban | Se conservan para todas las rutas |
| Compresión | No era el objetivo | gzip, types, mínimo, vary, nivel y verificación |
| Accept-Encoding "" | Se usó para sub_filter | Aquí deja que comprima nginx |
| sub_filter | Opcional para enlaces HTML | No se necesita para comprimir ni para transportar cualquier representación |
| Estructura Ubuntu | hosts, available, enabled, -t, reload | Igual |

## Variantes: qué cambia y qué línea tocar

| Variante | Cambio |
| --- | --- |
| Otro nombre público | server_name nuevo.example.org; y su entrada en hosts; adaptar destino de proxy_redirect. |
| Otro backend | proxy_pass http://otro.example.org; y proxy_set_header Host otro.example.org; ajustar origen de proxy_redirect. |
| Backend en otro puerto | proxy_pass http://foo.leak.com.ar:8080; ajustar Host con puerto si lo exige el virtual host. |
| 2C 2022 sin exigir compresión | Basta la estructura de proxy. Si se quiere demostrar sin gzip: gzip off; manteniendo Accept-Encoding "" hacia el backend. Quitar solo gzip on no basta si se hereda on. |
| Agregar JSON o JS a una lista restringida | gzip_types text/plain text/css application/json application/javascript text/javascript; |
| Cualquier MIME | gzip_types *; |
| Nivel más liviano o más fuerte | gzip_comp_level 1; o gzip_comp_level 9; |
| Mínimo habitual | gzip_min_length 1000; |
| Sin excluir por tamaño | gzip_min_length 0; |
| Header obligatorio del backend | proxy_set_header X-Algo "valor"; dentro de location. |
| Cliente pide solo br o deflate | El módulo gzip estándar no genera esas codificaciones. Si acepta identity, se puede responder sin comprimir; habilitar gzip no implementa Brotli ni deflate. Para br se necesita soporte adicional o backend que lo negocie. |
| Cliente acepta br y gzip | nginx puede elegir gzip si está aceptado; no necesita generar br. |
| HTTPS hacia el cliente | listen 443 ssl; ssl_certificate /etc/nginx/certs/foo.example.org.pem; ssl_certificate_key /etc/nginx/certs/foo.example.org-key.pem; |
| Mantener HTTP además de HTTPS | Conservar listen 80; y agregar listen 443 ssl; con un certificado confiable que cubra el nombre. proxy_pass puede seguir usando HTTP. |

Para HTTPS de práctica, generar e instalar un certificado de confianza, por ejemplo con mkcert, y colocar sus archivos en las rutas indicadas antes de nginx -t. Esas directivas no crean el certificado. La prueba pasa a curl --compressed https://foo.example.org/; se debe confiar en su CA. No se configuró HTTPS durante esta resolución.

## Comandos finales para demostrar

Con backend disponible y configuración aplicada:

~~~bash
curl --compressed http://foo.example.org/
curl --compressed http://foo.example.org/datos.json
curl -s -D - -o /dev/null -H "Accept-Encoding: gzip" http://foo.example.org/
curl -s -D - -o /dev/null http://foo.example.org/
~~~

Los dos primeros son la navegación con solo la opción de negociación. Los dos últimos son diagnóstico de cabeceras: con gzip debe verse Content-Encoding: gzip; sin pedirlo debe faltar. Puede demostrarse la barra del navegador en http://foo.example.org/; este nombre no está bajo .foo, a diferencia del ejercicio anterior.

## Frase de cierre

“nginx publica cualquier ruta del backend bajo foo.example.org sin redirigir al cliente y ofrece compresión transparente: negocia gzip con Accept-Encoding y entrega el mismo contenido una vez descomprimido.”

## Limpieza opcional, después de terminar

No se ejecutó automáticamente:
- Ctrl+C en la terminal Python detiene el backend.
- sudo rm /etc/nginx/sites-enabled/foo.example.org deshabilita el enlace, conserva el archivo de available.
- Comentar solo la entrada de foo.example.org en hosts devuelve la resolución previa.
- sudo nginx -t && sudo systemctl reload nginx aplica la deshabilitación.
- rm /tmp/foo-plano.html /tmp/foo-descomprimido.html elimina los archivos de comparación.
- Conservar ~/Downloads/gzip_backend.py permite repetir la práctica.

## Guardar el apunte en la VM

Este archivo se entrega para descargar; no implica acceso automático a la VM. Una vez descargado:

~~~bash
mkdir -p ~/protos/soluciones
cp ~/Downloads/21.2-1.md ~/protos/soluciones/21.2-1.md
~~~

mkdir -p crea padres faltantes y acepta directorios existentes; cp copia del origen al destino. Ajustar Downloads por Descargas si corresponde.

## Referencias técnicas

- https://nginx.org/en/docs/http/ngx_http_gzip_module.html
- https://nginx.org/en/docs/http/ngx_http_proxy_module.html
- https://curl.se/docs/manpage.html

