# SSH — Ejercicio 3: host virtual, token DNS y proxy

Práctica del 8 de noviembre de 2026. **Resultado: ingreso por SSH confirmado con mykey3 y la passphrase obtenida del panel interno.**

## 1. Qué pedía el ejercicio

La consigna combina tres condiciones:

1. La clave privada mykey3 se sirve por HTTP en el puerto 8060, pero el pedido debe identificar el host virtual archivos.lab.
2. La passphrase se obtiene en /clave mediante el proxy secrethost del puerto 8061. Esa ruta exige un parámetro token.
3. El token está publicado como registro TXT de token.internal.lab en el DNS de referencia.

Hay que obtener la clave, consultar el token, pedir la passphrase y entrar por SSH, dejando la cadena de comandos en orden.

## 2. Datos usados

| Dato | Valor |
|---|---|
| Carpeta de trabajo | ~/Documents/protoslaboratorios/labSSH |
| Servidor HTTP de archivos | 127.0.0.1:8060 |
| Host virtual de archivos | archivos.lab |
| Recurso de la clave | /mykey3 |
| Archivo local | mykey3 |
| Proxy | 127.0.0.1:8061 |
| Host esperado por el proxy | secrethost |
| Ruta del panel | /clave |
| DNS de referencia | 127.0.0.1:5360, UDP |
| Nombre TXT | token.internal.lab |
| Token obtenido | zorro-plateado |
| Passphrase obtenida | clave-tras-doble-salto |
| Cuenta SSH | jerodileo |
| Destino SSH | localhost, puerto 22 |

El laboratorio corre en la misma máquina y usa al usuario local, según el README. No se deducen la cuenta ni el servidor SSH del nombre de la clave.

## 3. Pedir la clave usando el host virtual correcto

Se ejecutó:

```bash
curl -i -H "Host: archivos.lab" 127.0.0.1:8060/mykey3
```

| Parte | Función |
|---|---|
| curl | Realiza el pedido HTTP. |
| -i | Muestra encabezados HTTP junto con el cuerpo. |
| -H "Host: archivos.lab" | Indica el sitio virtual que se solicita. |
| 127.0.0.1:8060 | Dirección y puerto de la conexión HTTP. |
| /mykey3 | Recurso solicitado. |

La URL determina a dónde conectar; Host indica qué sitio queremos dentro de ese servidor. No fue necesario resolver archivos.lab por DNS ni editar /etc/hosts, porque nos conectamos por IP y declaramos Host explícitamente.

Aunque se omitió http://, curl usó HTTP en esta URL. Puede escribirse también http://127.0.0.1:8060/mykey3.

Encabezados reales recibidos:

```text
HTTP/1.0 200 OK
Server: BaseHTTP/0.6 Python/3.14.4
Date: Sun, 08 Nov 2026 21:06:09 GMT
Content-Type: application/octet-stream
Content-Length: 444
```

El cuerpo tenía estos delimitadores; aquí se omiten los datos interiores de la clave privada:

```text
-----BEGIN OPENSSH PRIVATE KEY-----
[contenido de la clave privada]
-----END OPENSSH PRIVATE KEY-----
```

### Interpretación y siguiente paso

El 200 confirma que el servidor entregó el recurso. application/octet-stream describe datos genéricos; los delimitadores del cuerpo permiten reconocer el formato de clave privada OpenSSH. Content-Length indica 444 bytes.

Ya podíamos ver la clave, pero para usarla con SSH había que guardarla en un archivo que no incluyera los encabezados HTTP.

No se registró un intento sin Host correcto: la respuesta 404 para ese caso estaba indicada en la consigna, pero no fue una salida medida durante esta resolución.

## 4. Guardar la clave

Se ejecutó:

```bash
curl -H "Host: archivos.lab" 127.0.0.1:8060/mykey3 -o mykey3
```

Se mantuvo Host porque seguía siendo necesario para obtener el archivo. Se quitó -i para que el archivo local contuviera solo el cuerpo. -o mykey3 eligió el nombre local, dentro de la carpeta actual.

La descarga informó 444 bytes recibidos, coincidentes con Content-Length. La tabla de progreso se mostró en la terminal y no quedó incluida en el archivo guardado.

## 5. Revisar y restringir permisos

Se ejecutó:

```bash
ls -l mykey3
```

Salida real:

```text
-rw-rw-r-- 1 jerodileo jerodileo 444 Nov  8 18:06 mykey3
```

El archivo podía ser leído por otros usuarios y leído/escrito por el grupo. Para una clave privada se restringió el acceso:

```bash
chmod 600 mykey3
ls -l mykey3
```

Salida real después del cambio:

```text
-rw------- 1 jerodileo jerodileo 444 Nov  8 18:06 mykey3
```

| Dígito | Categoría | Permisos |
|---|---|---|
| 6 = 4 + 2 | Dueño | Lectura y escritura |
| 0 | Grupo | Ninguno |
| 0 | Otros | Ninguno |

La clave no necesita ejecución. chmod no cambia los bytes ni la passphrase del archivo: modifica los permisos. OpenSSH puede rechazar claves privadas accesibles por otros usuarios.

## 6. Consultar el panel sin token e interpretar el error

Se ejecutó:

```bash
curl -i -H "Host: secrethost" 127.0.0.1:8061/clave
```

Ahora el Host es secrethost y el puerto 8061 porque estamos consultando otro sitio: el proxy del panel, no el servidor de archivos.

Salida real:

```text
HTTP/1.0 400 Bad Request
Server: BaseHTTP/0.6 Python/3.14.4
Date: Sun, 08 Nov 2026 21:10:46 GMT
Content-Type: text/plain; charset=utf-8
Content-Length: 39

Falta o es invalido el parametro token
```

### Qué aprendimos de esta respuesta

El error es concreto: el pedido a /clave necesita token. No es un error de conexión ni un 404 que indique recurso inexistente. La respuesta del servicio nos permitió identificar qué dato faltaba antes de repetir la consulta.

La consigna indicaba dónde obtenerlo: un registro TXT del DNS de referencia.

## 7. Buscar el token en DNS

Se ejecutó:

```bash
dig @127.0.0.1 -p 5360 token.internal.lab TXT
```

| Parte | Función |
|---|---|
| dig | Consulta DNS. |
| @127.0.0.1 | Servidor DNS al que se pregunta. |
| -p 5360 | Puerto indicado por el laboratorio. |
| token.internal.lab | Nombre consultado. |
| TXT | Tipo de registro solicitado: texto. |

A diferencia del ejercicio 2, no se busca una IPv4 mediante A: se busca un texto mediante TXT. El puerto estándar DNS es 53, pero el lab usa 5360 por configuración.

Salida real, con espaciado de columnas normalizado:

```text
; <<>> DiG 9.20.24-1ubuntu0.5-Ubuntu <<>> @127.0.0.1 -p 5360 token.internal.lab TXT
; (1 server found)
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 59790
;; flags: qr rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 0

;; QUESTION SECTION:
;token.internal.lab.            IN      TXT

;; ANSWER SECTION:
token.internal.lab.     60      IN      TXT     "zorro-plateado"

;; Query time: 1 msec
;; SERVER: 127.0.0.1#5360(127.0.0.1) (UDP)
;; WHEN: Sun Nov 08 18:10:52 -03 2026
;; MSG SIZE  rcvd: 63
```

NOERROR confirma que no se informó error DNS. ANSWER: 1 indica un registro de respuesta. El 60 es el TTL en segundos, no parte del token.

El contenido del TXT es:

```text
zorro-plateado
```

Las comillas de dig delimitan su representación; no forman parte del valor que se envía al panel.

## 8. Agregar el token como parámetro de URL

Un parámetro de consulta tiene la estructura:

```text
/ruta?nombre=valor
```

Para este panel: ruta /clave, nombre token y valor zorro-plateado. Se ejecutó:

```bash
curl -i -H "Host: secrethost" "127.0.0.1:8061/clave?token=zorro-plateado"
```

Se mantuvieron el Host y el puerto del proxy. Se agregó ?token=zorro-plateado a la ruta. Las comillas protegen la URL frente a interpretaciones especiales del shell; resultan especialmente útiles si una consulta contiene caracteres como &.

Salida real:

```text
HTTP/1.0 200 OK
Server: BaseHTTP/0.6 Python/3.14.4
Date: Sun, 08 Nov 2026 21:11:32 GMT
Content-Type: text/plain; charset=utf-8
Content-Length: 51

La passphrase de mykey3 es: clave-tras-doble-salto
```

### Qué cambió respecto del pedido anterior

El mismo servicio que antes devolvió 400 ahora devolvió 200 porque se aportó el token correcto. El cuerpo reveló la passphrase:

```text
clave-tras-doble-salto
```

El token y la passphrase tienen funciones diferentes: el token permite consultar el panel; la passphrase desbloquea la clave privada para SSH.

## 9. Cómo interviene el proxy

El cliente hace HTTP a 127.0.0.1:8061 con Host secrethost. El proxy consulta el servicio interno en 127.0.0.1:9061 y devuelve la respuesta.

En una infraestructura con un cliente remoto, el 127.0.0.1 del backend es el loopback del servidor del proxy, no el del cliente. Aquí todo corre en la misma máquina; la implementación del lab simula la restricción del backend mediante una marca interna que agrega el proxy. Esa simulación no equivale por sí sola a un aislamiento de red.

No se necesitó un túnel SSH ni ProxyJump para resolver este ejercicio. El “doble salto” del título describe la cadena de servicios y pistas; el comando SSH final conecta directamente a localhost.

## 10. Elegir el comando SSH

El usuario propuso inicialmente:

```bash
ssh -i mykey3 -o IndentitiesOnly=yes jerodileo@localhost
```

La opción estaba mal escrita: corresponde IdentitiesOnly, sin la n adicional después de la I. No se pegó una salida de error de ese comando; se documenta el error de escritura observado.

El comando del ingreso exitoso fue:

```bash
ssh -v -i mykey3 -o IdentitiesOnly=yes jerodileo@localhost
```

| Parte | Función |
|---|---|
| ssh | Inicia la conexión segura. |
| -v | Muestra diagnóstico para comprobar la autenticación. |
| -i mykey3 | Selecciona la clave privada descargada. |
| -o IdentitiesOnly=yes | Limita las identidades a las seleccionadas por opciones o configuración, evitando ofrecer otras identidades del agente ajenas a esa selección. |
| jerodileo | Usuario destino de este laboratorio. |
| localhost | Servidor SSH local. En el log se resolvió a 127.0.0.1. |

El puerto predeterminado es 22, por eso no hace falta escribir -p 22. HTTP y DNS usaron otros puertos porque son servicios distintos.

IdentitiesOnly puede coexistir con otras IdentityFile configuradas. En esta ejecución, lo decisivo es que el verbose mostró la aceptación de mykey3.

## 11. Evidencia del ingreso exitoso

Fragmentos reales seleccionados del verbose completo:

```text
debug1: Connecting to localhost [127.0.0.1] port 22.
debug1: Connection established.
debug1: loaded pubkey from mykey3: ED25519 SHA256:agRz+NI2HoUJqbeUVzwtxX5PVAwE848hINjaXSjFULU
debug1: Authenticating to localhost:22 as 'jerodileo'
debug1: Host 'localhost' is known and matches the ED25519 host key.
debug1: Offering public key: mykey3 ED25519 SHA256:agRz+NI2HoUJqbeUVzwtxX5PVAwE848hINjaXSjFULU explicit
debug1: Server accepts key: mykey3 ED25519 SHA256:agRz+NI2HoUJqbeUVzwtxX5PVAwE848hINjaXSjFULU explicit
Enter passphrase for key 'mykey3':
Authenticated to localhost ([127.0.0.1]:22) using "publickey".
debug1: Entering interactive session.
```

Ante el pedido de passphrase se utilizó la obtenida del panel. El ingreso de la frase no muestra caracteres en pantalla; es normal.

Después se recibió:

```text
Welcome to Ubuntu 26.04.1 LTS (GNU/Linux 7.0.0-43-generic x86_64)
```

Y apareció:

```text
jerodileo@jerOS:~$
```

Server accepts key confirma que el servidor reconoció la clave pública candidata. Authenticated using publickey confirma que el cliente completó la demostración de posesión de la clave privada.

La passphrase no es la contraseña del usuario. El pedido correcto para la frase de este ejercicio es Enter passphrase for key 'mykey3', distinto de jerodileo@localhost's password.

La clave del host verificada contra known_hosts identifica al servidor. Es diferente de mykey3, que se usa para autenticarnos como cliente.

## 12. Cadena de resolución en orden

Con el laboratorio preparado y el servidor SSH activo:

```bash
curl -i -H "Host: archivos.lab" 127.0.0.1:8060/mykey3
curl -H "Host: archivos.lab" 127.0.0.1:8060/mykey3 -o mykey3
ls -l mykey3
chmod 600 mykey3
ls -l mykey3
curl -i -H "Host: secrethost" 127.0.0.1:8061/clave
dig @127.0.0.1 -p 5360 token.internal.lab TXT
curl -i -H "Host: secrethost" "127.0.0.1:8061/clave?token=zorro-plateado"
ssh -v -i mykey3 -o IdentitiesOnly=yes jerodileo@localhost
```

La consulta sin token se conserva porque fue parte de la resolución real y su error permitió comprobar el requisito. La passphrase se escribe cuando SSH la pide, no como argumento.

## 13. Cómo cada resultado determinó el siguiente paso

| Resultado | Decisión |
|---|---|
| 200 con Host archivos.lab y delimitadores de clave | Descargar solo el cuerpo con -o. |
| Archivo con permisos -rw-rw-r-- | Restringir acceso con chmod 600. |
| 400 que menciona token | Conseguir el valor indicado por la consigna. |
| TXT con zorro-plateado | Usarlo como parámetro token de la URL. |
| 200 con la passphrase | Usarla para desbloquear mykey3 al conectar por SSH. |
| Server accepts key: mykey3 y Authenticated using publickey | Confirmar el ingreso con la identidad del ejercicio. |

## 14. Cierre del laboratorio

Una vez terminada la práctica, para salir de la sesión SSH se usa:

```bash
exit
```

Luego, desde la terminal local y la carpeta del script, el README indica:

```bash
bash lab-ssh.sh down
```

El script apaga los servicios de práctica y retira las autorizaciones marcadas por este laboratorio. No equivale a detener el servicio SSH general del sistema.

Estos comandos de cierre se dejan como instrucciones; no se registró su ejecución al completar este apunte.

**Resultado observado:** clave obtenida mediante el host virtual correcto, token obtenido por DNS, passphrase recuperada a través del proxy e ingreso SSH confirmado con mykey3.
