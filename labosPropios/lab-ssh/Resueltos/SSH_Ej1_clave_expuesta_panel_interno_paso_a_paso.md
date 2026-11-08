# SSH — Ejercicio 1: clave expuesta y panel interno

Práctica del 8 de noviembre de 2026. **Resultado: ingreso por SSH confirmado con la clave descargada `mykey1` y su passphrase.**

## 1. Qué pedía el ejercicio

El enunciado presenta dos bloques de configuración:

```nginx
server {
    listen 8060;
    root /var/www;
    location / { try_files $uri $uri/ =404; }
}

server {
    listen 8061;
    server_name secrethost;
    location / { proxy_pass http://127.0.0.1:9061/; }
}
```

Además, hay un servidor OpenSSH. Sabemos que una clave privada quedó en `/var/www/sec/mykey1`, protegida con una passphrase que puede obtenerse por algún servicio del entorno.

Se pide:

1. Obtener la clave privada expuesta.
2. Averiguar su passphrase.
3. Hacer login por SSH.
4. Justificar cómo se accede al servicio interno a través del proxy.

La resolución se divide en tres piezas: HTTP entrega el archivo de la clave; el proxy permite consultar el panel con la passphrase; SSH usa la clave para autenticarnos.

## 2. Datos del laboratorio

| Dato | Valor usado |
|---|---|
| Carpeta de trabajo | `~/Documents/protoslaboratorios/labSSH` |
| Servidor HTTP de archivos | `127.0.0.1:8060` |
| Archivo del enunciado | `/var/www/sec/mykey1` |
| Ruta HTTP correspondiente | `/sec/mykey1` |
| Proxy | `127.0.0.1:8061` |
| Nombre de sitio esperado | `secrethost` |
| Servicio interno | `127.0.0.1:9061` |
| Usuario SSH | `jerodileo` |
| Destino SSH | `127.0.0.1`, puerto `22` |
| Archivo local descargado | `mykey1` |
| Passphrase obtenida | `secrethost-abierto-2026` |

En esta práctica, el README indica usar el usuario local y localhost: el script prepara la cuenta para aceptar las claves de práctica. En un parcial real, el usuario y el host SSH deben obtenerse del enunciado; no se deducen del contenido de la clave privada.

El laboratorio reproduce con servidores Python los comportamientos de HTTP y proxy descritos por los bloques de nginx. Los encabezados HTTP reales identifican a Python; eso no cambia el razonamiento de rutas y Host.

## 3. Interpretar root para construir la URL

El servidor de archivos tiene:

```nginx
listen 8060;
root /var/www;
```

`listen 8060` indica el puerto. `root /var/www` es la carpeta base donde se buscan los archivos solicitados por HTTP.

Para esta configuración:

| Pedido HTTP | Archivo correspondiente |
|---|---|
| `/foto.png` | `/var/www/foto.png` |
| `/sec/mykey1` | `/var/www/sec/mykey1` |

Como el archivo está dentro del root web, la URL no incluye nuevamente `/var/www`.

Con protocolo, IP, puerto y ruta:

```text
http://127.0.0.1:8060/sec/mykey1
```

No fue necesario usar traversal ni adivinar directorios: el enunciado daba la ubicación y la configuración permitía calcular la ruta publicada.

## 4. Explorar la respuesta HTTP

Se ejecutó:

```bash
curl -i http://127.0.0.1:8060/sec/mykey1
```

| Elemento | Función |
|---|---|
| `curl` | Hace el pedido HTTP y muestra el cuerpo de la respuesta. |
| `-i` | Incluye también los encabezados HTTP en la salida. |
| `http://` | Protocolo utilizado. |
| `127.0.0.1` | Máquina donde corre el servicio del lab. |
| `:8060` | Puerto del servidor de archivos. |
| `/sec/mykey1` | Recurso solicitado dentro del sitio. |

Encabezados reales recibidos:

```text
HTTP/1.0 200 OK
Server: BaseHTTP/0.6 Python/3.14.4
Date: Sun, 08 Nov 2026 20:28:35 GMT
Content-Type: application/octet-stream
Content-Length: 444
```

El cuerpo comenzaba y terminaba así; aquí se omiten los datos interiores de la clave:

```text
-----BEGIN OPENSSH PRIVATE KEY-----
[contenido de la clave privada]
-----END OPENSSH PRIVATE KEY-----
```

### Qué concluimos y por qué seguimos

- `200 OK`: la ruta existía y el servidor entregó el recurso.
- `application/octet-stream`: se entrega como datos genéricos. Ese encabezado no es lo que prueba que sea una clave SSH.
- Los delimitadores del cuerpo identifican el formato de clave privada OpenSSH.
- `Content-Length: 444`: el cuerpo ocupa 444 bytes.

Ya encontramos el archivo correcto, pero solo lo vimos en pantalla. SSH necesita leerlo desde un archivo local. El siguiente paso fue descargarlo sin mezclarle los encabezados HTTP.

La fecha HTTP está en GMT; las horas locales del usuario son de Argentina, UTC−3. Es normal ver tres horas de diferencia.

## 5. Guardar la clave privada

Comando realmente ejecutado:

```bash
curl http://127.0.0.1:8060/sec/mykey1 -o mykey1
```

Se quitó `-i` porque el archivo de identidad debe contener solamente la clave, sin encabezados como `HTTP/1.0 200 OK`.

`-o mykey1` guarda el cuerpo en el archivo local `mykey1`, dentro de la carpeta actual. Si ya existiera un archivo con ese nombre, lo reemplazaría.

La tabla de progreso mostró esta fila real:

```text
100    444 100    444   0      0  24447      0                              0
```

Se recibieron 444 bytes, coincidentes con el Content-Length anterior. El progreso es información de curl en la terminal; no se incorpora a la clave guardada con `-o`.

Ahora tenemos el archivo, pero todavía falta conocer la passphrase que lo desbloquea.

## 6. Restringir los permisos de la clave

También se aplicó:

```bash
chmod 600 mykey1
```

El usuario confirmó que fue necesario restringir los permisos de la clave descargada. No se pegó una salida de este comando; normalmente no imprime nada si tiene éxito.

### Qué significa 600

`chmod` modifica permisos. En la forma numérica hay un dígito para el dueño, otro para el grupo y otro para los demás:

| Categoría | Dígito | Permisos |
|---|---:|---|
| Dueño | 6 = 4 + 2 | Lectura y escritura |
| Grupo | 0 | Ninguno |
| Otros | 0 | Ninguno |

El resultado para un archivo regular se representa como:

```text
-rw-------
```

La clave privada no necesita permiso de ejecución. OpenSSH puede rechazar una clave privada accesible por otros usuarios; limitar sus permisos evita esa exposición.

**Este comando cambia quién puede acceder al archivo. No descifra la clave ni cambia su passphrase.**

## 7. Interpretar el proxy para buscar la passphrase

El segundo bloque dice:

```nginx
listen 8061;
server_name secrethost;
location / {
    proxy_pass http://127.0.0.1:9061/;
}
```

Leemos dos niveles:

- El cliente se conecta al proxy en el puerto `8061`.
- El proxy reenvía el pedido al backend en `127.0.0.1:9061`.

`server_name secrethost` indica el nombre del sitio esperado. Para pedir ese sitio mientras conectamos por IP, podemos enviar explícitamente el encabezado HTTP Host.

No hace falta cambiar el DNS ni editar `/etc/hosts` para este pedido: la IP de la URL determina la conexión y el encabezado Host informa el sitio solicitado.

En este lab el proxy exige ese Host. En una configuración nginx general, la conducta con un Host diferente también depende de qué servidor sea el predeterminado para ese puerto; no basta con ver server_name para asumir siempre un rechazo.

## 8. Consultar el panel interno a través del proxy

Comando realmente ejecutado:

```bash
curl -i -H "Host: secrethost" http://127.0.0.1:8061/
```

| Elemento | Función |
|---|---|
| `-i` | Muestra estado y encabezados HTTP además del cuerpo. |
| `-H "Host: secrethost"` | Envía ese encabezado para seleccionar el sitio del proxy. |
| `127.0.0.1:8061` | Dirección y puerto a los que se conecta curl. |
| `/` | Ruta solicitada, que el proxy reenvía al servicio interno. |

Salida real:

```text
HTTP/1.0 200 OK
Server: BaseHTTP/0.6 Python/3.14.4
Date: Sun, 08 Nov 2026 20:31:09 GMT
Content-Type: text/plain; charset=utf-8
Content-Length: 81

Bienvenido al panel interno. La passphrase de mykey1 es: secrethost-abierto-2026
```

### Qué nos dijo el resultado

El 200 confirmó que el pedido fue atendido y el cuerpo publicó explícitamente la passphrase de mykey1:

```text
secrethost-abierto-2026
```

No la obtuvimos mediante fuerza bruta: consultamos el servicio accesible en el entorno del ejercicio.

Ahora teníamos las dos piezas necesarias del lado cliente: el archivo de clave privada y la frase para desbloquearlo.

## 9. Por qué el servicio interno se consulta mediante el proxy

El destino `127.0.0.1:9061` de proxy_pass se interpreta **desde la máquina del proxy**. En una infraestructura con un cliente remoto, esa dirección loopback pertenece al servidor: el cliente no llega al backend usando su propio 127.0.0.1.

En este laboratorio todos los servicios y el cliente corren en la misma máquina. Para simular la restricción de acceso, el backend exige una marca interna que agrega el proxy. Por eso el recorrido previsto es entrar por `8061` con Host secrethost, y dejar que el proxy consulte `9061`.

No se hizo una prueba directa al puerto 9061 durante nuestra resolución: la justificación anterior surge de la configuración y la implementación suministradas.

La protección simulada usa un encabezado interno; no equivale a un aislamiento de red que por sí solo impida toda conexión al puerto. Esta distinción permite explicar correctamente qué reproduce el laboratorio y qué significaría loopback con un cliente en otra máquina.

## 10. Elegir usuario y destino SSH

La clave descargada no nos indica por sí sola a qué cuenta entrar. Esos datos salen del README del lab:

| Parte | Valor | Motivo |
|---|---|---|
| Usuario | `jerodileo` | Se usa la cuenta local del alumno. |
| Destino | `127.0.0.1` | El servidor SSH corre en la misma máquina. |
| Puerto | `22` | Puerto donde se comprobó que escuchaba OpenSSH. |
| Archivo de identidad | `mykey1` | Es la clave privada que descargamos. |

Para usar el puerto 22 no hace falta escribir `-p 22`: es el predeterminado de SSH.

## 11. Entrar y verificar que se utilizó mykey1

Comando del ingreso confirmado:

```bash
ssh -v -i mykey1 -o IdentitiesOnly=yes jerodileo@127.0.0.1
```

| Elemento | Para qué lo usamos |
|---|---|
| `ssh` | Abre la conexión segura al servidor SSH. |
| `-v` | Muestra diagnóstico para comprobar conexión y autenticación. |
| `-i mykey1` | Selecciona el archivo de identidad privado descargado. |
| `-o IdentitiesOnly=yes` | Limita las identidades ofrecidas a las seleccionadas por opciones o configuración, evitando otras claves ajenas a esa selección que ofrezca el agente. |
| `jerodileo@` | Indica la cuenta destino en el servidor. |
| `127.0.0.1` | Indica la dirección del servidor. |

En nuestra ejecución, el diagnóstico confirmó que la identidad ofrecida y aceptada fue mykey1. IdentitiesOnly no significa que cualquier configuración posible deje una sola identidad: pueden existir otras IdentityFile configuradas. La evidencia relevante aquí es la clave concreta aceptada en el log.

### Fragmentos reales del ingreso exitoso

Del verbose completo se seleccionan las líneas que prueban cada paso; no se reproduce todo el intercambio criptográfico:

```text
debug1: Connecting to 127.0.0.1 [127.0.0.1] port 22.
debug1: Connection established.
debug1: loaded pubkey from mykey1: ED25519 SHA256:8+uKVPzvjAh02VcpGHrDw8JfGWl5cDuheoy0n/Hj3pE
debug1: Authenticating to 127.0.0.1:22 as 'jerodileo'
debug1: Host '127.0.0.1' is known and matches the ED25519 host key.
debug1: Offering public key: mykey1 ED25519 SHA256:8+uKVPzvjAh02VcpGHrDw8JfGWl5cDuheoy0n/Hj3pE explicit
debug1: Server accepts key: mykey1 ED25519 SHA256:8+uKVPzvjAh02VcpGHrDw8JfGWl5cDuheoy0n/Hj3pE explicit
Enter passphrase for key 'mykey1':
Authenticated to 127.0.0.1 ([127.0.0.1]:22) using "publickey".
debug1: Entering interactive session.
```

Ante el pedido de passphrase se ingresó la obtenida del panel. No se muestran caracteres al escribirla; es normal.

El final de la salida incluyó:

```text
Welcome to Ubuntu 26.04.1 LTS (GNU/Linux 7.0.0-43-generic x86_64)
```

Y apareció el prompt:

```text
jerodileo@jerOS:~$
```

Aunque el nombre de máquina sea el mismo, ahora estamos en una sesión SSH hacia esa misma máquina. La prueba más clara de la autenticación es la línea `Authenticated ... using "publickey"`, junto con la aceptación de mykey1.

Para salir de esa sesión se puede usar `exit`. No se pegó una ejecución de ese cierre al completar el ejercicio.

## 12. Passphrase y contraseña de usuario no son lo mismo

| Dato | Qué protege | Dónde se usa |
|---|---|---|
| Passphrase de mykey1 | La clave privada cifrada guardada en el archivo local | El cliente la solicita para desbloquear la clave y firmar. |
| Contraseña del usuario remoto | El acceso a la cuenta mediante autenticación por contraseña | Solo corresponde si se usa ese método de autenticación. |

En el ingreso correcto se pidió:

```text
Enter passphrase for key 'mykey1':
```

Y luego se confirmó autenticación por clave pública. La passphrase permite usar la clave privada; no es una contraseña que el panel haya establecido para la cuenta jerodileo.

`Server accepts key` indica que el servidor reconoce esa clave pública como candidata autorizada. La autenticación completa se confirma después de que el cliente demuestra que posee la clave privada, mediante una firma.

El log también verifica la clave del host del servidor contra known_hosts. Esa clave identifica al servidor y es distinta de mykey1, que identifica al cliente para autenticarse.

## 13. Cadena de comandos para repetir el procedimiento

Con el lab ya iniciado y SSH activo, desde la carpeta donde se quiera guardar la clave:

```bash
curl -i http://127.0.0.1:8060/sec/mykey1
curl http://127.0.0.1:8060/sec/mykey1 -o mykey1
chmod 600 mykey1
curl -i -H "Host: secrethost" http://127.0.0.1:8061/
ssh -v -i mykey1 -o IdentitiesOnly=yes jerodileo@127.0.0.1
```

El primer curl es exploratorio: permite ver qué entrega la ruta. El segundo descarga solamente el cuerpo. El tercero restringe permisos. La consulta al proxy obtiene la passphrase y el último comando abre SSH usando la identidad descargada.

No se escribe la passphrase como argumento: se introduce cuando SSH la solicita.

## 14. Cómo reconocer las pistas del enunciado

| Pista | Razonamiento |
|---|---|
| root /var/www y archivo /var/www/sec/mykey1 | La ruta publicada es /sec/mykey1. |
| listen 8060 | La descarga HTTP va al puerto 8060. |
| server_name secrethost | El pedido al proxy debe identificar ese sitio mediante Host. |
| proxy_pass hacia 127.0.0.1:9061 | El proxy consulta el backend desde su propia máquina. |
| Clave privada con passphrase | Descargarla no alcanza: falta obtener la frase para poder usarla. |
| Login por clave | SSH necesita un archivo de identidad y una cuenta destino. |
| Archivo privado descargado | Restringir permisos con chmod 600. |

**Resultado observado:** archivo descargado, passphrase obtenida por HTTP a través del proxy e ingreso autenticado con mykey1.

