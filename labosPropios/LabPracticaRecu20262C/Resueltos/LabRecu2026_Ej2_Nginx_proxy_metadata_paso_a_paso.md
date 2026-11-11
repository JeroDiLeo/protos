# LabRecu2026 · Ejercicio 2 · Proxy nginx para metadata

## Qué pide la consigna

Hacer que `curl http://metadata.local` devuelva el JSON de `http://metadata.protos.foo`. El cliente usa el comando tal cual. Nginx agrega el encabezado que exige el backend cuando le reenvía el pedido.

## 1. Aislar los dos problemas

La primera prueba falló al resolver el nombre que queremos publicar:

```text
root@alumno:~# curl http://metadata.local
curl: (6) Could not resolve host: metadata.local
```

El error aparece al buscar la IP. La conexión a nginx viene después de ese paso.

Después probamos el backend de dos maneras:

```bash
curl -i http://metadata.protos.foo
curl -i -H 'Metadata: true' http://metadata.protos.foo
```

`-i` muestra los encabezados y el cuerpo de la respuesta. `-H` agrega un encabezado al pedido. La comparación permite atribuir el cambio de respuesta a `Metadata: true`. Extracto de las salidas reales:

```text
HTTP/1.1 403 Forbidden
Content-Type: text/html
```

```text
HTTP/1.1 200 OK
Content-Type: application/json

{"instance-id": "i-0acf00ba6699", "local-ipv4": "192.168.60.85", "token": "s3cr3t-metadata-token"}
```

## 2. Asociar metadata.local con el proxy

En `/etc/hosts` del contenedor `alumno` agregamos:

```text
127.0.0.1 metadata.local
```

En esta práctica `curl` y nginx corren dentro del mismo contenedor. Por eso el loopback `127.0.0.1` alcanza para que el cliente llegue al proxy. `metadata.protos.foo` es el destino del segundo pedido, el que nginx hace al backend.

Podés usar `getent hosts metadata.local` para comprobar la resolución que usa el sistema. Con esta entrada, la salida esperada es `127.0.0.1 metadata.local`. El cambio en `/etc/hosts` se aplica al resolver el siguiente pedido.

## 3. Configurar nginx y arrancarlo

En `/etc/nginx/conf.d/metadata.conf`:

```nginx
server {
    listen 80;
    server_name metadata.local;

    location / {
        proxy_pass http://metadata.protos.foo;
        proxy_set_header Metadata true;
    }
}
```

| Directiva | Qué decide |
|---|---|
| `listen 80` | En qué puerto espera nginx la conexión HTTP. |
| `server_name metadata.local` | Qué bloque selecciona nginx al recibir un pedido para ese nombre. |
| `location /` | Aplica estas reglas a la raíz y a los demás caminos que coincidan con el prefijo. |
| `proxy_pass http://metadata.protos.foo` | A qué servidor reenvía el pedido. |
| `proxy_set_header Metadata true` | Agrega el encabezado al pedido de nginx hacia el backend. Equivale al `-H` que usamos para diagnosticarlo. |

La resolución del nombre ocurre antes de llegar a nginx. `server_name` se usa una vez que el pedido HTTP llega al proxy. [Cómo nginx procesa una solicitud](https://nginx.org/en/docs/http/request_processing.html) · [Encabezados enviados por el proxy](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_set_header)

Salida real:

```text
root@alumno:~# nginx -t && systemctl start nginx
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
root@alumno:~# curl http://metadata.local
curl: (6) Could not resolve host: metadata.local
```

`nginx -t` valida la configuración y `&&` ejecuta `systemctl start nginx` si la validación termina bien. En este lab nginx viene instalado y el alumno lo arranca. En la sesión, el primer intento tras iniciar nginx todavía dio error de resolución. La corrección fue hacer que `metadata.local` resolviera hacia el contenedor.

## 4. Verificar el comando exacto

```text
root@alumno:~# curl http://metadata.local
{"instance-id": "i-0acf00ba6699", "local-ipv4": "192.168.60.85", "token": "s3cr3t-metadata-token"}
```

Es el mismo JSON que devolvió el backend al recibir `Metadata: true`. El campo `local-ipv4` describe la IP del backend en el lab. La conexión inicial del cliente llega al proxy por el nombre `metadata.local`.

## Si no pudieras editar /etc/hosts

**Para conservar el comando exacto**, podés publicar un registro DNS A para `metadata.local` en el servidor que consulta el cliente. El registro tiene que devolver una IP alcanzable del proxy. En esta red, `192.168.60.20` es la IP de `alumno` y sería un valor apropiado para clientes del lab que puedan alcanzarla. Verificá el resultado desde el cliente con `getent hosts metadata.local`. `.local` tiene un tratamiento especial en sistemas que usan mDNS, así que para esta alternativa también importa qué mecanismo consulta el sistema para ese sufijo. [RFC 6762, nombres .local](https://www.rfc-editor.org/rfc/rfc6762.html#section-3)

**Para una prueba puntual**, `--resolve` permite indicar la IP dentro de un comando curl:

```bash
curl --resolve metadata.local:80:127.0.0.1 http://metadata.local
```

Los tres valores son nombre, puerto e IP. Con esa opción, curl se conecta a `127.0.0.1:80` y conserva `metadata.local` como nombre de la URL. Sirve para probar el proxy de forma aislada. La prueba de entrega de este ejercicio exige `curl http://metadata.local` sin opciones. [Manual de curl sobre --resolve](https://curl.se/docs/manpage.html#--resolve)
