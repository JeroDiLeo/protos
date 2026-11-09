# Simulacro 2026-2C · Ejercicio 1 · HTTP y proxy SOCKS5

Práctica del 9 de noviembre de 2026. **Ejercicio resuelto.** El nodo interno respondió por SOCKS5 y devolvió `FLAG{ej1-socks5-tunel-ctos-ok}`.

## 1. Qué pedía la consigna

Consultar al contacto inicial por HTTP en `http://172.30.0.11:3126/`, usando modo verboso para leer las pistas en los encabezados. Después, pedir el contenido de `http://secrets.ct.os/` a través del proxy SOCKS5 en `172.30.0.12:1080`. El enunciado indica que el proxy puede resolver el nombre del nodo interno.

| Elemento | Valor | Función |
|---|---|---|
| Contacto inicial | `http://172.30.0.11:3126/` | Entrega las pistas. |
| Proxy SOCKS5 | `172.30.0.12:1080` | Abre la conexión al destino solicitado. |
| URL del nodo interno | `http://secrets.ct.os/` | Recurso HTTP que devuelve la flag. |

## 2. Consultar al contacto inicial

Se ejecutó:

```bash
curl -i -v http://172.30.0.11:3126/
```

| Parte | Función |
|---|---|
| `curl` | Hace el pedido HTTP. Como no especificamos otro método, envía GET. |
| `-i` | Incluye los encabezados de respuesta en la salida normal, junto con el cuerpo. |
| `-v` | Muestra el diagnóstico de la conexión y del intercambio HTTP. Las líneas con `>` indican lo enviado y las de `<`, lo recibido. |
| `http://172.30.0.11:3126/` | Conecta al puerto 3126 del contacto inicial y pide la ruta raíz. |

Fragmentos de la salida real:

```text
* Established connection to 172.30.0.11 (172.30.0.11 port 3126) from 172.30.0.1 port 35956
> GET / HTTP/1.1
> Host: 172.30.0.11:3126
< HTTP/1.0 200 OK
< Server: ctOS-edge/1.0 Python/3.12.16
< Content-Type: application/json; charset=utf-8
< X-CTOS-Proxy: 172.30.0.12:1080 socks5
< X-CTOS-Target: http://secrets.ct.os/
< X-Wrench: usa curl --socks5-hostname para que el DNS lo resuelva el proxy
```

El `200 OK` confirma que respondió el contacto inicial. El cuerpo JSON contiene el mensaje de Wrench. Para construir el siguiente pedido, cada encabezado aporta un dato distinto:

| Encabezado | Dato que aporta |
|---|---|
| `X-CTOS-Proxy` | Dirección y puerto del proxy, y protocolo SOCKS5. |
| `X-CTOS-Target` | URL completa del nodo interno. |
| `X-Wrench` | El proxy debe resolver el nombre del nodo interno. |

Con `-i` y `-v` juntos los encabezados aparecieron dos veces en la terminal. Una copia salió por la salida normal con `-i` y otra por el diagnóstico con `-v`. Fue una sola respuesta HTTP.

## 3. Primer intento a través del proxy

```bash
curl -i -v -x socks5://172.30.0.12:1080 http://172.30.0.11:3126/
```

`-x` indica a curl qué proxy usar. La URL final conserva el contacto inicial como destino.

Salida real relevante:

```text
*   Trying 172.30.0.12:1080...
* Opened SOCKS connection from 172.30.0.1 port 42896 to 172.30.0.11 port 3126 (via 172.30.0.12 port 1080)
> GET / HTTP/1.1
> Host: 172.30.0.11:3126
< HTTP/1.0 200 OK
< Server: ctOS-edge/1.0 Python/3.12.16
< X-CTOS-Target: http://secrets.ct.os/
```

El túnel funcionó y abrió una conexión hacia `172.30.0.11:3126`. Ese destino explica por qué se recibió el mismo mensaje de Wrench. El próximo paso era cambiar el destino de la conexión SOCKS.

## 4. Segundo intento con el nombre en la ruta

```bash
curl -i -v -x socks5://172.30.0.12:1080 http://172.30.0.11:3126/secrets.ct.os
```

Salida real relevante:

```text
* Opened SOCKS connection from 172.30.0.1 port 53358 to 172.30.0.11 port 3126 (via 172.30.0.12 port 1080)
> GET /secrets.ct.os HTTP/1.1
> Host: 172.30.0.11:3126
< HTTP/1.0 200 OK
< Server: ctOS-edge/1.0 Python/3.12.16
```

En la URL que usamos, `172.30.0.11:3126` seguía siendo el destino y `/secrets.ct.os` era la ruta HTTP. El `GET /secrets.ct.os` y el encabezado `Host` lo muestran por separado. El servidor inicial volvió a responder con las pistas.

El valor de `X-CTOS-Target`, `http://secrets.ct.os/`, ubica `secrets.ct.os` en la parte de host de la URL. Eso indica al proxy a qué nodo conectarse.

## 5. Delegar la resolución del nombre al proxy

| Esquema en `-x` | Dónde se resuelve el nombre del destino |
|---|---|
| `socks5://` | En la máquina que ejecuta curl. |
| `socks5h://` | En el proxy. Curl le pasa el nombre del destino. |

La pista `X-Wrench` menciona `--socks5-hostname`. Usar `-x socks5h://...` expresa el mismo comportamiento. En los intentos previos, el destino era una IP, por lo que esos pedidos no requerían resolver su nombre. En el intento final, el destino es `secrets.ct.os` y la consigna requiere resolverlo desde el proxy.

## 6. Comando final y evidencia

Comando exacto ejecutado:

```bash
curl -v -x socks5h://172.30.0.12:1080 http://secrets.ct.os
```

| Parte | Función |
|---|---|
| `-v` | Permite verificar el destino del túnel, la petición y los encabezados recibidos. |
| `-x socks5h://172.30.0.12:1080` | Conecta al proxy por SOCKS5 y le delega la resolución del destino. |
| `http://secrets.ct.os` | Indica el host HTTP final. HTTP usa el puerto 80 por defecto y curl pide `/`. |

Salida real relevante:

```text
*   Trying 172.30.0.12:1080...
* Opened SOCKS connection from 172.30.0.1 port 35922 to secrets.ct.os port 80 (via 172.30.0.12 port 1080)
* Established connection to 172.30.0.12 (172.30.0.12 port 1080) from 172.30.0.1 port 35922
> GET / HTTP/1.1
> Host: secrets.ct.os
< HTTP/1.1 200 OK
< Server: nginx/1.31.8
< Content-Type: text/html
```

La línea del túnel identifica tanto el destino, `secrets.ct.os:80`, como el intermediario, `172.30.0.12:1080`. El encabezado HTTP `Host: secrets.ct.os` corresponde al nodo interno. El `200 OK` vino acompañado de HTML que incluía:

```text
ctOS :: nodo interno secrets.ct.os
----------------------------------
Llegaste atravesando el proxy SOCKS5. Bien hecho.

Llaves maestras para voltear a Bloom:

    FLAG{ej1-socks5-tunel-ctos-ok}
```

