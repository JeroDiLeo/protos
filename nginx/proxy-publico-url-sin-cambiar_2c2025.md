# 2C 2025 — Ejercicio IV: nginx como proxy inverso

## Enunciado (textual)

*Fuente: 2C 2025, Ejercicio IV.*

El servidor en `parcial.protos.foo` está corriendo un servidor HTTP. Usted desea publicar ese mismo contenido bajo el nombre `publico.protos.foo`, también mediante HTTP. Configure lo necesario para que al acceder a `http://publico.protos.foo` con un cliente HTTP —Firefox, Google Chrome, Curl— se sirva el contenido devuelto por `parcial.protos.foo`.

**Requisito:**  
No se debe ver modificada la URL ingresada en el browser. Es decir, el cliente debe seguir viendo `http://publico.protos.foo`, no una redirección hacia `parcial.protos.foo`.

Si se utiliza `curl`, no se permiten otras opciones. Se recomienda verificar con:


```
curl http://publico.protos.foo
```

---

## Resultado y alcance de la práctica

Consigna: publicar http://parcial.protos.foo bajo http://publico.protos.foo, conservando el nombre público en el cliente. Verificación obligatoria: `curl http://publico.protos.foo`, sin opciones.

Se verificó en la VM jerOS:
- nginx estaba activo.
- El backend real no respondió: timeout de conexión.
- Se usó un backend Python de práctica en 127.0.0.1:8081.
- El comando exacto de la consigna imprimió el HTML a través de nginx.
- /redir devolvió un 302 cuyo Location fue reescrito al nombre público.
- Un enlace absoluto del HTML se reescribió con sub_filter.
- El navegador mostró el contenido con el alias publico.protos.test, conservando ese nombre incluso en /destino.
- Una ruta temporal /prueba-301 demostró la alternativa incorrecta: 301 con Location al backend. Después se retiró.

Esto demuestra la configuración con un backend equivalente. La conexión al backend real queda pendiente de su disponibilidad. No se afirma haber publicado el contenido real.

## ⭐ RECETA PARA EL PARCIAL (leer esto primero)

> Todo lo de abajo ("PRÁCTICA") usó un backend Python en 127.0.0.1:8081, el alias publico.protos.test y sub_filter. **En el parcial no hace falta nada de eso.** Esta es la solución con los datos reales del enunciado.

### Pasos
~~~bash
systemctl status nginx                          # 1. mostrar estado inicial
curl -i http://parcial.protos.foo               # 2. ver qué sirve el backend (status, si trae Location)
getent hosts publico.protos.foo                 # 3. ¿a dónde resuelve hoy el nombre público?
sudo nano /etc/hosts                            # 4. agregar: 127.0.0.1 publico.protos.foo
getent hosts publico.protos.foo                 #    ahora debe dar 127.0.0.1
sudo nano /etc/nginx/sites-available/publico.protos.foo   # 5. el bloque de abajo
sudo ln -s /etc/nginx/sites-available/publico.protos.foo /etc/nginx/sites-enabled/
sudo nginx -t                                   # 6. validar
sudo systemctl reload nginx                     #    aplicar solo si -t pasa
curl http://publico.protos.foo                  # 7. la verificación EXACTA de la consigna, sin opciones
curl -i http://publico.protos.foo               #    200 directo, sin Location → la URL no cambia
~~~

~~~nginx
server {
    listen 80;
    server_name publico.protos.foo;

    location / {
        proxy_pass http://parcial.protos.foo;
        proxy_set_header Host parcial.protos.foo;
        proxy_redirect http://parcial.protos.foo/ http://publico.protos.foo/;
    }
}
~~~
- `proxy_pass`: nginx busca el contenido en el backend y se lo entrega al cliente. El cliente nunca ve `parcial.protos.foo` → **la URL no cambia**. (Un `return 301` sí la cambiaría: no cumple.)
- `proxy_set_header Host parcial.protos.foo`: el backend recibe su propio nombre, por si es un virtual host. Con `proxy_pass` a un nombre ya es el valor por defecto; escribirlo deja explícito el porqué.
- `proxy_redirect`: si el backend respondiera un redirect con `Location: http://parcial.protos.foo/...`, lo reescribe al nombre público para que el cliente no "se escape" al backend. Si el backend no redirige, no molesta.
- `/etc/hosts`: hace que en esta máquina `publico.protos.foo` apunte a nginx. `hosts` decide la IP; `server_name` decide qué sitio de nginx responde.

### Dos trampas que encontraste en la práctica
1. **El navegador con `.foo` fuerza HTTPS.** El dominio `.foo` está en la lista HSTS preload: Firefox/Chrome convierten `http://publico.protos.foo` en `https://` y dan error de certificado, **aunque nginx esté bien**. Por eso la prueba que vale es la que pide la consigna: `curl http://publico.protos.foo`. Si te preguntan por el navegador, explicá esto.
2. **Si `nginx -t` dice `host not found in upstream "parcial.protos.foo"`:** nginx resuelve el nombre del backend al validar. No es un error de tu bloque: es que desde tu VM ese nombre no resuelve (red o DNS). Comprobalo con `getent hosts parcial.protos.foo`.

### Si algo falla
| Ves | Significa | Mirar |
|---|---|---|
| `What?` o la página default de nginx | el Host no coincidió con tu `server_name` (otro sitio respondió) | ortografía del `server_name`, que el enlace esté en sites-enabled y que hiciste reload |
| `502 Bad Gateway` | nginx no pudo hablar con el backend | `sudo tail /var/log/nginx/error.log`, `curl -i http://parcial.protos.foo` directo |
| `504 Gateway Timeout` | el backend no contestó a tiempo | igual que 502 |
| `301/302` con `Location` a parcial | el backend redirige con su nombre | revisar `proxy_redirect` |
| `Could not resolve host: publico.protos.foo` | falta la línea en /etc/hosts | paso 4 |

### Para el video
"Configuré nginx como proxy inverso: `/etc/hosts` lleva `publico.protos.foo` a esta máquina, el `server_name` selecciona mi sitio y `proxy_pass` trae el contenido de `parcial.protos.foo`. Como nginx hace la petición por el cliente, la URL que ve el cliente no cambia; con `curl -i` se ve un 200 directo, sin redirección."

---

# PRÁCTICA (detalle de lo que se ejecutó con el backend local)

## 1. Estado inicial

```bash
systemctl status nginx
```

systemctl administra servicios; status consulta su estado; nginx es el servicio. Se observó active (running). Si aparece un visor, q lo cierra.

## 2. Probar el backend directo

```bash
curl -i --connect-timeout 5 --max-time 10 http://parcial.protos.foo
```

curl hace una petición HTTP; -i muestra cabeceras de respuesta junto con el cuerpo; --connect-timeout 5 limita la fase de conexión a 5 segundos; --max-time 10 limita toda la operación a 10 segundos. Sin otro método ni datos, se solicita GET /.

Resultado observado: curl (28), Connection timed out tras aproximadamente 5 segundos. No hubo status HTTP, Content-Type ni Location: no se llegó a obtener una respuesta HTTP.

## 3. Backend local de práctica

Guardar este código en /tmp/publico-backend.py:

```python
from http.server import BaseHTTPRequestHandler, HTTPServer

class Backend(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/redir":
            self.send_response(302)
            self.send_header("Location", "http://parcial.protos.foo/destino")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        cuerpo = """<!doctype html>
<html lang="es">
<meta charset="utf-8">
<title>Backend de práctica</title>
<h1>Contenido del backend de práctica</h1>
<p>Esta página se sirve desde Python.</p>
<a href="/redir">Probar redirección</a>
<a href="http://parcial.protos.foo/destino">Enlace absoluto</a>
</html>
""".encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

HTTPServer(("127.0.0.1", 8081), Backend).serve_forever()
```

HTTPServer escucha solo en loopback, puerto 8081. do_GET procesa GET; /redir genera una redirección absoluta, y las demás rutas entregan HTML. encode produce los bytes UTF-8; Content-Length cuenta esos bytes. El servidor es exclusivamente de práctica.

Primero verificar que el puerto esté libre:

```bash
sudo ss -ltnp 'sport = :8081'
```

sudo ejecuta con privilegios; ss consulta sockets; -l muestra listeners, -t TCP, -n direcciones y puertos numéricos, -p procesos; el filtro selecciona el puerto local 8081. No había listener.

Levantarlo en una terminal que quede abierta:

```bash
python3 /tmp/publico-backend.py
```

python3 ejecuta el archivo. Que no vuelva el prompt es normal: está atendiendo conexiones. Ctrl+C lo detiene.

Desde otra terminal:

```bash
curl -i http://127.0.0.1:8081/
curl -i http://127.0.0.1:8081/redir
```

Se observó 200 OK, Content-Type text/html; charset=utf-8 y el HTML en la primera. En la segunda: 302 Found, Location http://parcial.protos.foo/destino y cuerpo vacío. La ruta /destino también entrega el HTML en este servidor simple.

## 4. Resolver el nombre público a nginx

```bash
sudo nano /etc/hosts
```

nano edita el archivo. Agregar sin borrar otras entradas:

```text
127.0.0.1 publico.protos.foo publico.protos.test
```

127.0.0.1 es esta misma máquina. El cliente necesita convertir el nombre público en la dirección de nginx. La entrada es local: no crea un registro DNS para otras máquinas. Si el navegador corre en otra máquina, debe resolver hacia la IP de la VM accesible desde ella.

publico.protos.test es un alias de práctica para el navegador. .foo está en HSTS preload y los navegadores que aplican esa lista fuerzan HTTPS; por eso se observó un error de certificado al intentar navegar al nombre .foo. Esto no fue una redirección de nuestra configuración HTTP. La prueba obligatoria por curl con .foo sí funcionó.

## 5. Sitio nginx de práctica

```bash
sudo nano /etc/nginx/sites-available/publico.protos.foo
```

Contenido usado al finalizar las pruebas:

```nginx
server {
    listen 80;
    server_name publico.protos.foo publico.protos.test;

    location / {
        proxy_pass http://127.0.0.1:8081;
        proxy_set_header Host parcial.protos.foo;
        proxy_redirect http://parcial.protos.foo/ http://$host/;

        # Opcional: reescribir enlaces absolutos en HTML.
        proxy_set_header Accept-Encoding "";
        sub_filter 'http://parcial.protos.foo/' 'http://$host/';
        sub_filter_once off;
    }
}
```

Qué hace cada parte:
- server agrupa un servidor virtual; las llaves delimitan bloques y cada directiva simple termina con punto y coma.
- listen 80 atiende HTTP en el puerto 80.
- server_name reconoce los nombres del header Host que manda el cliente. Deben figurar ambos alias si se usan ambos.
- location / abarca las rutas bajo /, salvo que otra location tenga prioridad.
- proxy_pass indica a qué servidor nginx le solicita el contenido. No devuelve al cliente una instrucción para visitar ese servidor.
- proxy_set_header modifica o agrega una cabecera en la petición hacia el backend.
- Host parcial.protos.foo hace que el backend reciba su nombre esperado, aunque la conexión TCP sea a una IP de práctica. Es relevante si distingue sitios por Host.
- Por defecto, el Host del proxy se basa en $proxy_host, el destino de proxy_pass: aquí 127.0.0.1:8081. Con el backend real sería parcial.protos.foo. $host, en cambio, representa el nombre solicitado a nginx: publico.protos.foo o el alias .test. Mandar ese nombre al backend puede seleccionar un virtual host incorrecto.
- proxy_redirect reemplaza el prefijo indicado en Location y Refresh de la respuesta. No transforma el status 302 en 200 ni modifica el HTML.
- La variante con $host conserva el alias usado por el cliente. Para el nombre único de la consigna puede escribirse exactamente:
  `proxy_redirect http://parcial.protos.foo/ http://publico.protos.foo/;`
- proxy_set_header Accept-Encoding "" omite esa cabecera hacia el backend para pedir una respuesta sin compresión. No descomprime por sí misma una respuesta que el backend comprima de todos modos.
- sub_filter sustituye la cadena del backend por la pública en el cuerpo HTML. No es un analizador completo de enlaces, CSS o JavaScript.
- sub_filter_once off repite el reemplazo para todas las apariciones. El valor predeterminado on reemplaza una vez por cadena configurada. El tipo text/html se procesa por defecto.

proxy_redirect default está activo por defecto y deriva su correspondencia de location y proxy_pass. Con proxy_pass al nombre real puede reescribir redirects que coincidan con ese origen. En esta práctica el destino TCP era 127.0.0.1:8081 y el Location mencionaba parcial.protos.foo: por eso se configuró explícitamente esa correspondencia.

## 6. Habilitar, validar y aplicar

```bash
sudo ln -s /etc/nginx/sites-available/publico.protos.foo /etc/nginx/sites-enabled/publico.protos.foo
sudo nginx -t
sudo systemctl reload nginx
```

ln crea un enlace; -s lo hace simbólico. Primer argumento: archivo existente; segundo: enlace a crear. No repetir si el enlace ya existe.

nginx -t comprueba la sintaxis y trata de abrir los archivos referenciados. No comprueba que todo el comportamiento HTTP del backend sea correcto. Se observaron syntax is ok y test is successful.

Ejecutar reload solo si la validación pasa. reload carga la configuración con nuevos workers y permite terminar las conexiones de los anteriores. restart detiene y vuelve a iniciar el servicio, por lo que puede interrumpir conexiones. sudo aporta permisos para estas operaciones.

## 7. Pruebas y lectura de resultados

| Comando | Resultado observado / qué mirar |
| --- | --- |
| curl http://publico.protos.foo | HTML del backend, sin opciones adicionales. El enlace absoluto quedó con publico.protos.foo. |
| curl -i http://publico.protos.foo/ | 200 OK; Content-Type text/html; sin Location en esta respuesta. |
| curl -i http://publico.protos.foo/redir | 302 Found; Location: http://publico.protos.foo/destino. |
| curl http://publico.protos.test | Mismo HTML, con enlaces al alias .test. |
| Navegar a http://publico.protos.test/redir | El navegador siguió a /destino y conservó publico.protos.test en la barra. |

Prueba adicional que se puede repetir:

```bash
curl -i -L http://publico.protos.foo/redir
```

-L sigue Location. -i permite ver las cabeceras de las respuestas. Se espera el 302 al nombre público seguido del 200 de /destino mientras el backend de práctica siga activo.

200 es el resultado de nuestra página inicial, no una garantía universal de proxy_pass: nginx también puede transmitir otros estados que entregue el backend.

### Demostración de la alternativa incorrecta

Se agregó temporalmente, como hermana de location /:

```nginx
location = /prueba-301 {
    return 301 http://parcial.protos.foo/;
}
```

= significa coincidencia exacta. return termina la petición con ese código y destino. Tras validar y recargar:

```bash
curl -i http://publico.protos.test/prueba-301
```

Se observó 301 Moved Permanently y Location: http://parcial.protos.foo/. El cliente recibe la orden de ir al backend y, si la sigue, cambia el nombre visible. Tampoco cumple una regla como `rewrite ^ http://parcial.protos.foo/ redirect;`: redirect genera una redirección externa temporal. No confundirla con una reescritura interna.

Al principio esa ruta devolvió 200 porque no estaba agregada la location exacta: el GET pasó por location / al Python, que devuelve HTML para las rutas generales. Después de agregar el bloque se verificó el 301. El bloque temporal se retiró al terminar.

### Corrección del alias .test

Se observó What? y luego 404 de nginx cuando se usó .test sin agregarlo a server_name. La entrada en hosts ya dirigía a la VM, pero nginx no reconocía ese Host y seleccionaba otro servidor. Agregar el alias a server_name y recargar solucionó la selección. hosts decide la IP; server_name decide el sitio dentro de nginx.

Para errores reales:

```bash
sudo tail -n 20 /var/log/nginx/access.log
sudo tail -n 20 /var/log/nginx/error.log
```

tail muestra el final de un archivo; -n 20 selecciona las últimas 20 líneas. access.log registra peticiones y estados; error.log aporta detalles como conexión rechazada al upstream. Un 502 suele indicar problemas al obtener una respuesta válida del backend; un 504 puede ser timeout. Un 404 puede generarlo nginx o el backend: comparar con curl directo al mismo path y revisar los logs. El header Server por sí solo no identifica el origen del error detrás de un proxy.

## 8. Configuración para el servidor real del parcial

Cuando el backend esté disponible, usar:

```nginx
server {
    listen 80;
    server_name publico.protos.foo;

    location / {
        proxy_pass http://parcial.protos.foo;
        proxy_set_header Host parcial.protos.foo;
        proxy_redirect http://parcial.protos.foo/ http://publico.protos.foo/;
    }
}
```

Esta es la solución base; para el HTML de práctica se agregaron las tres directivas opcionales de sub_filter del bloque anterior. Se mantiene en hosts `127.0.0.1 publico.protos.foo` si nginx corre en la misma máquina del cliente. Después de editar: nginx -t, reload y curl a secas.

No detener Python mientras siga habilitado proxy_pass hacia 127.0.0.1:8081 si se quiere continuar probando: al detenerlo dejará de existir ese backend.

## Diferencias con el ejercicio de metadata

| Elemento | metadata | Este ejercicio |
| --- | --- | --- |
| Nombre local | metadata.local | publico.protos.foo; alias .test para navegador |
| server_name | metadata.local | publico.protos.foo |
| proxy_pass real | http://metadata.protos.foo | http://parcial.protos.foo |
| Host al backend | metadata.protos.foo | parcial.protos.foo |
| Header obligatorio | proxy_set_header Metadata true; | No se exige |
| Accept | application/json, opcional si siempre responde JSON | No hace falta forzarlo |
| Respuesta | JSON | HTML en la práctica |
| Redirects y enlaces | No fueron el eje de la prueba | proxy_redirect; sub_filter opcional |
| Estructura | hosts, server, location, enlace, -t y reload | Se conserva |

## Variantes: qué cambia y qué línea tocar

Cada fila es una adaptación; no pegar todas juntas sin ajustar las correspondencias.

| Variante | Línea exacta o bloque |
| --- | --- |
| Otro nombre público | `server_name otro.protos.test;`; hosts debe resolver ese nombre a nginx. Ajustar también el destino de proxy_redirect y sub_filter si es fijo. |
| Otro backend | `proxy_pass http://otro.protos.foo;` y `proxy_set_header Host otro.protos.foo;`. Ajustar los prefijos de reescritura a los redirects/enlaces reales. |
| Otro puerto del backend | `proxy_pass http://parcial.protos.foo:8080;`. Si el virtual host exige autoridad con puerto: `proxy_set_header Host parcial.protos.foo:8080;`. |
| Backend por IP, Host fijo | `proxy_pass http://192.168.70.10;` y `proxy_set_header Host parcial.protos.foo;`. |
| Solo /algo/, quitando prefijo | `location /algo/ { proxy_pass http://parcial.protos.foo/; }` |
| Solo /algo/, conservando prefijo | `location /algo/ { proxy_pass http://parcial.protos.foo; }` |
| Agregar compresión al cliente | En server: `gzip on;` y `gzip_vary on;`. HTML ya está entre los tipos comprimibles; depende de condiciones como tamaño y Accept-Encoding del cliente. |
| Header hacia el backend | `proxy_set_header X-Algo "valor";` |
| Header de respuesta al cliente | `add_header X-Practica "publico" always;` |

En /algo/, una petición /algo/a llega como /a con la barra final del proxy_pass indicado; sin URI en proxy_pass conserva /algo/a. Con location / y backend raíz, ambas formas suelen producir el mismo path, pero la diferencia importa al publicar un prefijo. Conservar también el Host requerido en esas variantes y ajustar redirects para no escapar del prefijo público.

Fallback que devuelve What? ante nombres sin sitio configurado:

```nginx
server {
    listen 80 default_server;
    server_name _;
    default_type text/plain;
    return 200 "What?\n";
}
```

Es un bloque separado. default_server selecciona el servidor por defecto de esa dirección y puerto; _ es un nombre convencional, no un comodín mágico. Otros server_name coincidentes siguen seleccionando su propio sitio. Si ya existe un default_server para esa dirección:puerto, editar el existente o retirar esa marca antes de agregar otro. No crear dos. listen IPv6 se configura por separado si se necesita.

## Limpieza opcional para continuar con otros ejercicios

Estos pasos se documentan para ejecutar después; no se da por hecha su ejecución.

1. En la terminal del Python, Ctrl+C detiene solo el backend de práctica.
2. Si no se usará el sitio, deshabilitar su enlace:
   `sudo rm /etc/nginx/sites-enabled/publico.protos.foo`
   rm elimina ese enlace, conserva el archivo de sites-available.
3. Comentar únicamente la entrada de estos alias en /etc/hosts, anteponiendo #.
4. Validar con `sudo nginx -t` y, solo si pasa, `sudo systemctl reload nginx`.
5. Si no se quiere conservar el Python temporal: `rm /tmp/publico-backend.py`.

Si se deja el sitio habilitado apuntando a un backend detenido, las peticiones a esos nombres fallarán. Los demás sitios con su server_name siguen siendo independientes.

## Frase para justificar la solución

“Configuré nginx como proxy inverso: el cliente consulta publico.protos.foo y nginx obtiene el contenido del backend, conservando el nombre público y reescribiendo sus redirecciones.”

## Referencias

- nginx, proxy_pass / proxy_set_header / proxy_redirect: https://nginx.org/en/docs/http/ngx_http_proxy_module.html
- nginx, sub_filter: https://nginx.org/en/docs/http/ngx_http_sub_module.html
- Google Registry, HSTS de .foo: https://www.registry.google/domains/foo/

## Guardar en la VM

Este apunte se entrega como archivo descargable. Para ubicarlo en el destino pedido, crear la carpeta y copiar el archivo descargado:

```bash
mkdir -p ~/protos/soluciones
cp ~/Downloads/25.2-4.md ~/protos/soluciones/25.2-4.md
```

mkdir crea directorios; -p crea padres faltantes y acepta que ya existan. cp copia origen a destino. ~ es el home del usuario actual. Si el navegador usa Descargas, reemplazar Downloads por Descargas; comprobar el nombre descargado antes de copiar. Estos comandos deben ejecutarse en la VM; generar el archivo aquí no modifica automáticamente su home.

