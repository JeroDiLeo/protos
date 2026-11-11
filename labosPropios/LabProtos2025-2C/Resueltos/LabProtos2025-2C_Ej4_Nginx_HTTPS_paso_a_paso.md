# LabProtos2025-2C · Ejercicio IV · Proxy reverso HTTPS con nginx

## Qué pide el ejercicio

Publicar en `https://seguro.protos.foo` el contenido del servidor HTTP `parcial.protos.foo`. El cliente conserva la URL pública y tiene que poder usar el comando `curl https://seguro.protos.foo` tal cual.

El cliente establece HTTPS con el nginx que configuramos en `alumno`. Ese nginx abre su propia conexión HTTP con el backend y devuelve el contenido al cliente.

## 1. Averiguar qué IP corresponde a cada lado

| Qué buscamos | Cómo lo averiguamos | Resultado en el lab |
|---|---|---|
| La IP de `parcial.protos.foo`, el backend que ya existe | `dig +short A parcial.protos.foo` consulta al DNS por la IPv4 del nombre. `+short` muestra solo la respuesta. El mapa del `README.md` también indica la dirección en este lab. | `192.168.50.90`. Es el destino de `proxy_pass`. |
| La IP para el nombre nuevo `seguro.protos.foo` | En la máquina donde va a correr nginx, `ip -br -4 addr` muestra las IPv4 en formato breve. Elegimos una IP que el cliente pueda alcanzar. | `192.168.50.20`, la IPv4 de `eth1` en `alumno`. |

El enunciado da los nombres. Si tenés que repetirlo en otro entorno, consultá la IP del backend por DNS y revisá las interfaces de la máquina donde vas a instalar el proxy. Si el cliente corre en otra máquina, esa máquina debe poder resolver el nombre nuevo y alcanzar la IP del proxy.

En el lab agregamos esta línea a `/etc/hosts` de `alumno`:

```text
192.168.50.20 seguro.protos.foo
```

Antes, `curl -i https://seguro.protos.foo` devolvió `Could not resolve host: seguro.protos.foo`. Después verificamos la resolución que usa el sistema con `getent hosts`, que tiene en cuenta `/etc/hosts`.

```text
root@alumno:~# getent hosts seguro.protos.foo
192.168.50.20   seguro.protos.foo
```

## 2. Comprobar qué Host espera el backend

Usamos `curl -i` en el diagnóstico para ver el estado, los encabezados y el cuerpo. Estos son extractos de las salidas reales.

```text
root@alumno:~# curl -i http://parcial.protos.foo
HTTP/1.1 200 OK
Server: nginx/1.24.0 (Ubuntu)

Contenido servido por parcial.protos.foo via HTTP inseguro. Este es el backend que luego vamos a exponer por HTTPS usando seguro.protos.foo.

root@alumno:~# curl -i http://192.168.50.90
HTTP/1.1 200 OK
Server: nginx/1.24.0 (Ubuntu)

What?

root@alumno:~# curl -i -H 'Host: parcial.protos.foo' http://192.168.50.90/
HTTP/1.1 200 OK
Server: nginx/1.24.0 (Ubuntu)

Contenido servido por parcial.protos.foo via HTTP inseguro. Este es el backend que luego vamos a exponer por HTTPS usando seguro.protos.foo.
```

Los dos pedidos por IP llegan a la misma dirección. Con `-H` cambiamos el encabezado HTTP `Host`. Al pedir `parcial.protos.foo`, el backend eligió el sitio correcto. Esto justifica usar la IP en `proxy_pass` y fijar el nombre del sitio en `proxy_set_header Host`. La prueba final contra el nombre público usa el comando exacto de la consigna. [Módulo proxy de nginx](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_set_header)

## 3. Generar la clave privada y el certificado

```bash
openssl req -x509 -newkey rsa:2048 -noenc -days 30 \
  -keyout /etc/ssl/private/seguro.protos.foo.key \
  -out /etc/ssl/certs/seguro.protos.foo.crt \
  -subj '/CN=seguro.protos.foo' \
  -addext 'subjectAltName=DNS:seguro.protos.foo'
```

| Opción | Qué significa |
|---|---|
| `openssl req` | Trabaja con solicitudes de certificado y también permite emitir un certificado directamente. |
| `-x509` | Hace que OpenSSL produzca un certificado. En este comando queda autofirmado con la clave que generamos. |
| `-newkey rsa:2048` | Crea una clave RSA de 2048 bits. |
| `-noenc` | Deja el archivo de clave privada sin cifrar en disco, para que nginx lo pueda leer al iniciar sin pedir una frase de contraseña. Esta opción se aplica al archivo de clave. TLS cifra la conexión con el cliente. |
| `-days 30` | Define la vigencia de 30 días, elegida para la práctica. |
| `-keyout ...key` | Escribe la clave privada en la ruta que nginx va a usar en `ssl_certificate_key`. |
| `-out ...crt` | Escribe el certificado público en la ruta que nginx va a usar en `ssl_certificate`. |
| `-subj '/CN=seguro.protos.foo'` | Carga el nombre común del titular desde la línea de comandos. |
| `-addext 'subjectAltName=DNS:seguro.protos.foo'` | Agrega el nombre DNS al SAN. Ese nombre debe corresponder al que aparece en la URL del cliente. |

Las barras invertidas al final de línea permiten escribir un comando largo en varias líneas. Los `+` que se vieron en la terminal corresponden al progreso de la generación de la clave. [Manual de openssl req](https://docs.openssl.org/3.0/man1/openssl-req/) · [Identidad del servicio en TLS](https://www.rfc-editor.org/rfc/rfc9525.html)

Comprobación real del SAN:

```text
root@alumno:~# openssl x509 -in /etc/ssl/certs/seguro.protos.foo.crt -noout -ext subjectAltName
X509v3 Subject Alternative Name:
    DNS:seguro.protos.foo
```

`openssl x509` permite inspeccionar un certificado. `-in` elige el archivo, `-noout` omite su representación PEM completa y `-ext subjectAltName` muestra esa extensión. [Manual de openssl x509](https://docs.openssl.org/3.0/man1/openssl-x509/)

### Qué cambiar si la consigna varía

- Si cambia el nombre de la URL, usá ese nombre en el SAN, en el `CN`, en `server_name` y en la resolución local. Si la URL contiene una IP literal, el SAN se expresa como `IP:192.168.50.20`, con la dirección correspondiente.
- Si te dan una vigencia concreta, ajustá `-days` al generar el autofirmado. Si te dan una clave existente, la leés con `-key ruta/a/la/clave.key` y usás esa ruta en nginx.
- Si piden que firme una autoridad certificadora, generás una solicitud CSR con `openssl req -new` y le enviás esa solicitud a la autoridad. Nginx presenta el certificado que emite la autoridad. El cliente confía en la CA que respalda esa cadena. [Manual de openssl req](https://docs.openssl.org/3.0/man1/openssl-req/) · [Verificación TLS en curl](https://curl.se/docs/sslcerts.html)

## 4. Configurar nginx para presentar el certificado

Guardamos este bloque en `/etc/nginx/conf.d/seguro.protos.foo.conf`:

```nginx
server {
    listen 443 ssl;
    server_name seguro.protos.foo;

    ssl_certificate     /etc/ssl/certs/seguro.protos.foo.crt;
    ssl_certificate_key /etc/ssl/private/seguro.protos.foo.key;

    location / {
        proxy_pass http://192.168.50.90;
        proxy_set_header Host parcial.protos.foo;
    }
}
```

- `listen 443 ssl` activa TLS en el puerto HTTPS. `server_name` identifica el sitio publicado.
- `ssl_certificate` indica qué certificado presenta nginx al cliente. `ssl_certificate_key` indica la clave privada que nginx usa para demostrar que posee la clave correspondiente.
- `location /` aplica el proxy a las solicitudes del sitio. `proxy_pass` configura el destino HTTP y `proxy_set_header Host` reproduce el encabezado que devolvió el contenido correcto en el diagnóstico. [HTTPS en nginx](https://nginx.org/en/docs/http/configuring_https_servers.html) · [Módulo proxy de nginx](https://nginx.org/en/docs/http/ngx_http_proxy_module.html)

```text
root@alumno:~# nginx -t && systemctl reload nginx
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

`nginx -t` valida la configuración. `&&` hace que `systemctl reload nginx` solo se ejecute si esa prueba sale bien. La recarga aplica el bloque al nginx que ya corre en el lab.

## 5. Hacer que el cliente confíe en el certificado

Durante HTTPS, `curl` verifica que el certificado **corresponda al nombre** y que **sea de confianza**. El SAN cubre el primer punto. Como generamos un autofirmado para el lab, incorporamos su certificado al almacén de confianza de `alumno`, que es donde ejecutamos `curl`. [Verificación TLS en curl](https://curl.se/docs/sslcerts.html)

```bash
cp /etc/ssl/certs/seguro.protos.foo.crt \
   /usr/local/share/ca-certificates/seguro.protos.foo.crt

update-ca-certificates
```

**`cp` copia el archivo.** El primer argumento es el origen, el certificado que generamos y que nginx presenta. El segundo es la copia que colocamos en `/usr/local/share/ca-certificates/`, el directorio que Ubuntu lee para incorporar certificados de confianza locales. La extensión `.crt` y el formato PEM permiten que la herramienta lo incluya. Copiamos solo el certificado público. La privada sigue en `/etc/ssl/private/` para que la use nginx.

**`update-ca-certificates` actualiza el almacén.** Lee los certificados locales, prepara sus entradas individuales en `/etc/ssl/certs/` y actualiza el archivo conjunto `/etc/ssl/certs/ca-certificates.crt`. Así el cliente puede usar su verificación habitual con el certificado que acabamos de registrar. Si la prueba se ejecuta desde otra máquina, la confianza se configura en la máquina que ejecuta el cliente. [Manual de update-ca-certificates de Ubuntu](https://manpages.ubuntu.com/manpages/noble/man8/update-ca-certificates.8.html)

Salida real:

```text
Updating certificates in /etc/ssl/certs...
rehash: warning: skipping ca-certificates.crt,it does not contain exactly one certificate or CRL
rehash: warning: skipping duplicate certificate in seguro.protos.foo.pem
1 added, 0 removed; done.
Running hooks in /etc/ca-certificates/update.d...
done.
```

| Mensaje | Cómo interpretarlo |
|---|---|
| `skipping ca-certificates.crt` | El archivo conjunto contiene varios certificados. `rehash` arma índices para archivos individuales y omite ese archivo al indexarlos. |
| `skipping duplicate certificate` | `rehash` encontró el mismo certificado al recorrer más de un archivo. En este montaje, el original ya estaba en `/etc/ssl/certs/` y agregamos el mismo certificado por el directorio de confianza local. |
| `1 added, 0 removed` | La actualización incorporó una entrada de confianza. El `curl` final permite verificar que la aplicación la aceptó. |

[Cómo indexa archivos OpenSSL rehash](https://docs.openssl.org/3.0/man1/openssl-rehash/) · [Almacén de certificados de Ubuntu](https://manpages.ubuntu.com/manpages/noble/man8/update-ca-certificates.8.html)

## 6. Verificar con el comando exacto

```text
root@alumno:~# curl https://seguro.protos.foo
Contenido servido por parcial.protos.foo via HTTP inseguro. Este es el backend que luego vamos a exponer por HTTPS usando seguro.protos.foo.
```

El resultado reúne las tres comprobaciones del ejercicio. El cliente resolvió el nombre hacia `alumno`, aceptó el certificado presentado por nginx y recibió el contenido del backend que nginx consultó con `Host: parcial.protos.foo`. La frase «via HTTP inseguro» forma parte del texto que devuelve el backend y describe el tramo entre nginx y ese backend. La URL usada por el cliente es HTTPS.
