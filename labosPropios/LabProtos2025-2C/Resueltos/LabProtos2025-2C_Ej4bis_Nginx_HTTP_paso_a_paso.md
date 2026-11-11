# LabProtos2025-2C · Ejercicio IV-bis · Proxy reverso HTTP

## Qué pide el extra

Publicar en `http://publico.protos.foo` el contenido que devuelve `http://parcial.protos.foo`. La prueba se hace con `curl http://publico.protos.foo`, tal cual. El cliente le pide la página a nginx en `alumno` y ese nginx obtiene el contenido con una segunda conexión HTTP al backend.

## 1. Resolver el nombre del proxy

En `/etc/hosts` de `alumno`, agregá:

```text
192.168.50.20 publico.protos.foo
```

`192.168.50.20` es la IPv4 de `eth1` en la máquina donde escucha el proxy. Se puede identificar con `ip -br -4 addr`. Para comprobar la asociación antes de probar HTTP, `getent hosts publico.protos.foo` consulta la resolución local del sistema. El resultado esperado es `192.168.50.20 publico.protos.foo`.

El backend es `parcial.protos.foo`. Su dirección es `192.168.50.90` en este lab y se puede averiguar con `dig +short A parcial.protos.foo`.

## 2. Configurar el sitio HTTP de nginx

En `/etc/nginx/conf.d/publico.protos.foo.conf`:

```nginx
server {
    listen 80;
    server_name publico.protos.foo;

    location / {
        proxy_pass http://192.168.50.90;
        proxy_set_header Host parcial.protos.foo;
    }
}
```

| Directiva | Qué decide |
|---|---|
| `listen 80` | En qué puerto espera la conexión HTTP del cliente. |
| `server_name publico.protos.foo` | Qué bloque atiende el pedido que llega con `Host: publico.protos.foo`. |
| `location /` | Qué solicitudes del sitio se manejan con las reglas de este bloque. El prefijo `/` incluye la ruta raíz. |
| `proxy_pass http://192.168.50.90` | A qué dirección se conecta nginx para obtener el contenido. |
| `proxy_set_header Host parcial.protos.foo` | Qué encabezado `Host` ve el backend en ese segundo pedido. |

En el diagnóstico del Ejercicio IV, el backend devolvió `What?` cuando lo consultamos por IP y devolvió el contenido esperado al enviar `Host: parcial.protos.foo`. Por eso fijamos ese encabezado en el proxy. El cliente sigue pidiendo `http://publico.protos.foo` mientras nginx se ocupa de la segunda conexión. [Procesamiento de solicitudes en nginx](https://nginx.org/en/docs/http/request_processing.html) · [Módulo proxy](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_set_header)

## 3. Validar, recargar y probar

Salida real:

```text
root@alumno:~# nginx -t && systemctl reload nginx
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
root@alumno:~# curl http://publico.protos.foo
Contenido servido por parcial.protos.foo via HTTP inseguro. Este es el backend que luego vamos a exponer por HTTPS usando seguro.protos.foo.
```

`nginx -t` comprueba la configuración y `&&` ejecuta la recarga solo si esa comprobación termina bien. El `curl` final confirma que el nombre público llega al proxy y que este devuelve el contenido de `parcial.protos.foo`. La mención de `seguro.protos.foo` está dentro del texto que escribió el backend.
