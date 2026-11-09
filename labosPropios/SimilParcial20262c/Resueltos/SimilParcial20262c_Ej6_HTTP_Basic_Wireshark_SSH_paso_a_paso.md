# Simulacro 2026-2C · Ejercicio 6 · Basic auth en Wireshark y SSH

Práctica del 9 de noviembre de 2026. Se obtuvo la passphrase de una petición HTTP capturada y se usó la clave `mykey` para entrar como `pepito`. El archivo remoto devolvió `FLAG{ej6-pcap-basicauth-ssh-ok}`.

## 1. Qué pedía la consigna

Encontrar la clave privada y la captura que publica nginx en `172.30.0.70`. Seguir la conversación HTTP en Wireshark, recuperar el encabezado `Authorization` y decodificarlo. Después, entrar por SSH como `pepito` y leer `~/flag.txt`.

| Recurso | Dirección o nombre |
|---|---|
| HTTP de nginx | `http://172.30.0.70/` |
| Listado | `http://172.30.0.70/sec/` |
| Captura | `/sec/captura.pcapng` |
| Clave privada de práctica | `/sec/mykey` |
| Contenedor | `ej6-host` |
| SSH directo | `pepito@172.30.0.70`, puerto 22 |
| SSH por el puerto publicado | `127.0.0.1:2622` |
| Archivo de entrega | `~/flag.txt` |

## 2. Encontrar el listado y leer la pista

```bash
curl -i 172.30.0.70
curl -i 172.30.0.70/sec
curl -iL 172.30.0.70/sec
curl -iL 172.30.0.70/sec/pista.txt
```

La raíz respondió `200 OK` y el cuerpo indicó **mira /sec/ (listado abierto)**. Al pedir `/sec` sin la barra final, nginx respondió:

```text
HTTP/1.1 301 Moved Permanently
Location: http://172.30.0.70/sec/
```

`-L` hizo que curl siguiera esa redirección. El segundo estado fue `200 OK` y el listado mostró `captura.pcapng` (787 bytes), `mykey` (1856 bytes) y `pista.txt` (269 bytes).

El pedido de `pista.txt` devolvió:

```text
Guarde mi clave privada aca (mykey) con passphrase.
Tambien quedo una captura de red (captura.pcapng) de cuando me
autentique contra el panel. Abrila en Wireshark, segui el TCP stream
y fijate el header Authorization (Basic auth, esta en base64).
            -- pepito
```

### Cuándo usamos -i, -v, -L y -o

| Opción | Cuándo usarla |
|---|---|
| `-i` | Para ver el estado y los encabezados de respuesta junto con el cuerpo. En `/sec` permitió leer `Location` del 301. |
| `-v` | Para diagnosticar la conexión y ver la petición que envía curl. El diagnóstico muestra líneas con `*`, peticiones con `>` y encabezados de respuesta con `<`. |
| `-L` | Para que curl siga las redirecciones HTTP. En `/sec` siguió el 301 hacia `/sec/`. |
| `-o archivo` | Para guardar el cuerpo de la respuesta en un archivo. |

Al descargar una captura o una clave, se puede combinar `-v` con `-o` para ver el diagnóstico y guardar el cuerpo. Con `-i -o archivo`, curl incluye los encabezados HTTP en el archivo. Con `-i -v`, los encabezados de respuesta se ven en dos salidas de curl.

## 3. Guardar la captura y resolver el 403 de la clave

El primer pedido de la captura con `curl -iL 172.30.0.70/sec/captura.pcapng` recibió `200 OK`, `Content-Type: application/octet-stream` y `Content-Length: 787`. Curl avisó que imprimir contenido binario podía afectar la terminal. Para guardarla se ejecutó:

```bash
curl -L 172.30.0.70/sec/captura.pcapng -o captura.pcapng
```

La descarga recibió **787 bytes**, igual al tamaño anunciado por nginx.

El pedido de la clave con `curl -iL 172.30.0.70/sec/mykey` recibió primero `403 Forbidden`. El Dockerfile genera la clave privada como root y la copia al directorio web. Los permisos restrictivos de la clave impiden que el proceso de nginx lea el archivo, aunque su nombre aparezca en el listado.

Se ejecutó este arreglo sobre la copia publicada para el ejercicio:

```bash
docker compose exec -u 0 ej6-host chmod 644 /var/www/sec/mykey
```

`docker compose exec` ejecuta el comando dentro del servicio y `-u 0` selecciona root. `chmod 644` permite que nginx lea esa copia. El cambio se aplica al contenedor activo.

Al repetir la consulta, la salida cambió a:

```text
HTTP/1.1 200 OK
Content-Type: application/octet-stream
Content-Length: 1856
```

El cuerpo comenzaba con `-----BEGIN OPENSSH PRIVATE KEY-----`. Luego se guardaron los **1856 bytes** del cuerpo:

```bash
curl -L 172.30.0.70/sec/mykey -o mykey
```

Se reutilizó el nombre local `mykey`, lo que reemplazó el archivo del ejercicio 2 en esa carpeta. Para la copia privada local, el comando indicado fue `chmod 600 mykey`. Ese modo da lectura y escritura al propietario y quita permisos al grupo y a los demás. El modo `644` correspondía a la copia que nginx publica dentro del lab.

## 4. Elegir la petición correcta en Wireshark

Abrí la captura con `wireshark captura.pcapng` o desde **Archivo → Abrir**. El filtro inicial `http` permite ubicar las peticiones y respuestas HTTP. En la captura, la petición **`GET /panel/ HTTP/1.1`** está en el **paquete 4**. Sale del cliente `172.30.0.77:44444` hacia el servidor `172.30.0.70:80`.

Sobre el paquete 4, la ventana observada fue **Follow → HTTP Stream**. Para ver el flujo TCP de esa conexión también está **Follow → TCP Stream**. En la lista de paquetes quedó el filtro `tcp.stream eq 0`. El flujo muestra tanto el pedido del cliente como la respuesta del servidor, y permite seguir esa conversación aunque el contenido se reparta en varios segmentos.

| Paquetes | Qué se ve en la captura |
|---|---|
| 1, 2 y 3 | Handshake TCP entre el cliente y el puerto 80 del servidor. |
| 4 | Petición `GET /panel/` con `Authorization: Basic ...`. |
| 6 | Respuesta HTTP `200 OK` del servidor. |

Fragmento real de la petición reconstruida:

```http
GET /panel/ HTTP/1.1
Host: secrethost
Authorization: Basic cGVwaXRvOndyM25jaEtleTIwMjY=
User-Agent: dedsec-cli/1.0
Accept: */*
```

La respuesta del paquete 6 confirmó que el panel aceptó esas credenciales. La passphrase se recuperó del encabezado de la **petición**, enviado por el cliente.

## 5. Decodificar Basic auth

Se copió solo el valor que sigue a `Basic` y se ejecutó:

```bash
echo 'cGVwaXRvOndyM25jaEtleTIwMjY=' | base64 -d
```

`echo` escribe el valor, la tubería lo pasa a `base64` y `-d` lo decodifica. Salida real:

```text
pepito:wr3nchKey2026
```

Basic auth representa `usuario:contraseña` en Base64. En este laboratorio, la parte a la derecha de `:`, **`wr3nchKey2026`**, también es la passphrase de la clave privada. HTTP en esta captura viaja en claro, por lo que se puede leer el encabezado y decodificarlo. Base64 cambia la representación de los bytes.

## 6. Diagnosticar el primer intento SSH

```bash
ssh -i mykey -o IdentitiesOnly=yes pepito@172.30.0.70
```

SSH abrió la conexión al puerto 22 y pidió confirmar la huella de la clave **del servidor** por tratarse del primer contacto con ese host. Después de aceptar, falló la autenticación:

```text
pepito@172.30.0.70: Permission denied (publickey,keyboard-interactive).
```

La conexión al servidor y la autenticación del usuario son pasos separados. Este primer intento terminó antes de que apareciera el pedido de passphrase. Como el lab crea a `pepito` dentro del contenedor, se comprobó el estado de la cuenta:

```bash
docker compose exec -u 0 ej6-host passwd -S pepito
```

Salida real:

```text
pepito L 2026-11-09 0 99999 7 -1
```

`-S` consulta el estado de la contraseña de la cuenta y `L` significa que estaba bloqueada. Para habilitarla en este contenedor se asignó una contraseña temporal:

```bash
docker compose exec -u 0 ej6-host passwd pepito
```

```text
New password:
Retype new password:
passwd: password updated successfully
```

Esa operación habilitó la cuenta. La passphrase de `mykey` se siguió obteniendo de la captura y se usó en el cliente SSH para desbloquear la clave privada.

## 7. Confirmar la clave usada y leer la flag

```bash
ssh -v -i mykey -o IdentitiesOnly=yes pepito@172.30.0.70
```

| Argumento | Para qué sirvió |
|---|---|
| `-v` | Mostrar el diagnóstico y verificar qué clave ofreció y aceptó el servidor. |
| `-i mykey` | Indicar el archivo local de la clave privada. |
| `-o IdentitiesOnly=yes` | Limitar las identidades que SSH ofrece a las seleccionadas por opciones o configuración. |
| `pepito@172.30.0.70` | Elegir el usuario y el destino. El puerto por defecto de SSH es 22. |

Fragmento real del ingreso:

```text
debug1: Offering public key: mykey RSA SHA256:qpGoST7xW065aB2f8MtrmjfHjxtQXlXeTqb5a01xaSQ explicit
debug1: Server accepts key: mykey RSA SHA256:qpGoST7xW065aB2f8MtrmjfHjxtQXlXeTqb5a01xaSQ explicit
Enter passphrase for key 'mykey':
Authenticated to 172.30.0.70 ([172.30.0.70]:22) using "publickey".
```

El cliente ofreció la parte pública de `mykey`, el servidor la aceptó y el cliente usó la parte privada para completar la autenticación. El pedido `Enter passphrase for key 'mykey':` solicitó **`wr3nchKey2026`** para desbloquear el archivo local. La línea `using "publickey"` confirma el método de ingreso.

Con el prompt en el directorio personal de `pepito`, se ejecutó:

```text
pepito@ej6-host:~$ cat flag.txt
FLAG{ej6-pcap-basicauth-ssh-ok}
   Sacaste la passphrase de un Basic auth sniffeado en el pcap. Crack.
```

