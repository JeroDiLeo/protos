# SSH — Ejercicio 2: clave escondida y passphrase en DNS

Práctica del 8 de noviembre de 2026. **Resultado: ingreso por SSH confirmado usando mykey2 y la passphrase obtenida del DNS.**

## 1. Qué pedía el ejercicio

El servidor HTTP del puerto 8060 publica una clave privada cuya ruta no se conoce inicialmente. El administrador creyó que bastaba con no enlazarla para ocultarla.

La consigna también indica que la passphrase es la dirección IP del nombre `llave.internal.lab`, consultable en el DNS de referencia.

Hay que descubrir la ubicación de la clave, descargarla, consultar la passphrase por DNS e ingresar por SSH. Debe explicarse qué pista permitió encontrar el archivo.

## 2. Datos del entorno

| Dato | Valor |
|---|---|
| Carpeta de trabajo | ~/Documents/protoslaboratorios/labSSH |
| HTTP de archivos | 127.0.0.1:8060 |
| DNS de referencia | 127.0.0.1, puerto UDP 5360 |
| Nombre DNS solicitado | llave.internal.lab |
| Ruta finalmente encontrada | /privado/respaldo/id_rsa |
| Nombre local elegido | mykey2 |
| Passphrase obtenida | 203.0.113.47 |
| Usuario SSH | jerodileo |
| Destino SSH | 127.0.0.1:22 |

La IP del registro DNS es la passphrase porque así lo establece el enunciado. No es el destino al que hay que conectar por SSH. En el lab, el usuario y destino SSH salen del README: la cuenta local del alumno en localhost.

## 3. Explorar la raíz del servidor HTTP

Se ejecutó:

```bash
curl -i 127.0.0.1:8060
```

curl hizo el pedido HTTP a la raíz del sitio. Al no indicar otro protocolo en esta URL, usó HTTP; también puede escribirse explícitamente `http://127.0.0.1:8060/`.

-i muestra encabezados y cuerpo para poder interpretar tanto el estado como el contenido.

Salida real:

```text
HTTP/1.0 200 OK
Server: BaseHTTP/0.6 Python/3.14.4
Date: Sun, 08 Nov 2026 20:46:39 GMT
Content-Type: text/html; charset=utf-8
Content-Length: 101

<html><body>Servidor de archivos.
<!-- no hay nada publico aca; revisa /robots.txt --></body></html>
```

### Qué nos dijo y qué hicimos después

200 OK confirma que la raíz respondió. El cuerpo HTML contiene un comentario que indica revisar `/robots.txt`.

Los comentarios HTML pueden no verse en la página renderizada de un navegador, pero sí aparecen al leer el cuerpo con curl. Esa fue la pista concreta que motivó la siguiente consulta.

Las fechas HTTP están en GMT; el usuario trabaja en Argentina, UTC−3. La diferencia de tres horas es normal.

## 4. Consultar robots.txt

Se ejecutó:

```bash
curl -i 127.0.0.1:8060/robots.txt
```

Se mantuvieron la IP y el puerto del servidor y se cambió la ruta siguiendo la pista.

Salida real:

```text
HTTP/1.0 200 OK
Server: BaseHTTP/0.6 Python/3.14.4
Date: Sun, 08 Nov 2026 20:46:48 GMT
Content-Type: text/plain; charset=utf-8
Content-Length: 43

User-agent: *
Disallow: /privado/respaldo/
```

| Línea | Significado |
|---|---|
| User-agent: * | Las instrucciones se dirigen a los rastreadores en general. |
| Disallow: /privado/respaldo/ | Pide a los rastreadores que no rastreen esa ruta. |

**robots.txt no es un control de acceso.** Publicar Disallow no impide que un cliente solicite esa URL; en este caso, además, revela un directorio interesante.

La pista aporta el directorio, no el nombre exacto del archivo. El siguiente intento del usuario fue `id_rsa`, un nombre habitual para una clave SSH RSA. Fue una hipótesis que se confirmó mediante la respuesta HTTP, no un dato garantizado solo por robots.txt.

## 5. Probar el archivo candidato

Se ejecutó:

```bash
curl -i 127.0.0.1:8060/privado/respaldo/id_rsa
```

Encabezados reales:

```text
HTTP/1.0 200 OK
Server: BaseHTTP/0.6 Python/3.14.4
Date: Sun, 08 Nov 2026 20:47:14 GMT
Content-Type: application/octet-stream
Content-Length: 1856
```

El cuerpo tenía estos delimitadores; se omiten aquí los datos interiores de la clave privada:

```text
-----BEGIN OPENSSH PRIVATE KEY-----
[contenido de la clave privada]
-----END OPENSSH PRIVATE KEY-----
```

200 confirma que el recurso existe. application/octet-stream describe datos genéricos; los delimitadores del cuerpo son la evidencia del formato de clave privada OpenSSH. Content-Length indica 1856 bytes.

Que el archivo se llame id_rsa no significa que su envoltura de texto deba decir BEGIN RSA PRIVATE KEY: una clave RSA también puede guardarse en el formato privado OpenSSH, como ocurrió aquí.

## 6. Descargar la clave sin encabezados HTTP

Se ejecutó:

```bash
curl 127.0.0.1:8060/privado/respaldo/id_rsa -o mykey2
```

-o mykey2 guarda el cuerpo en un archivo local de ese nombre, en la carpeta actual. Se quitó -i para no incorporar encabezados HTTP al archivo que SSH debe interpretar.

La descarga informó un total de 1856 bytes recibidos, coincidente con el Content-Length anterior. La tabla de progreso de curl se mostró en la terminal y no formó parte del archivo descargado.

El nombre remoto es id_rsa y el local es mykey2: -o permite elegir cómo guardarlo sin cambiar el contenido.

Ahora teníamos el archivo, pero aún necesitábamos la passphrase que lo desbloquea.

## 7. Consultar la passphrase en DNS

El enunciado dice que es la dirección IP de llave.internal.lab. Para obtener una IPv4 consultamos un registro A.

Comando ejecutado:

```bash
dig @127.0.0.1 -p 5360 A llave.internal.lab
```

| Parte | Función |
|---|---|
| dig | Cliente de consultas DNS. |
| @127.0.0.1 | Servidor DNS que recibe la consulta. |
| -p 5360 | Puerto del DNS de este laboratorio. |
| A | Tipo de registro solicitado: dirección IPv4. |
| llave.internal.lab | Nombre cuya dirección buscamos. |

El puerto 5360 viene del README del lab; no se deduce del nombre ni de la IP. El puerto DNS estándar es 53.

Salida real:

```text
; <<>> DiG 9.20.24-1ubuntu0.5-Ubuntu <<>> @127.0.0.1 -p 5360 A llave.internal.lab
; (1 server found)
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 11023
;; flags: qr rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 0

;; QUESTION SECTION:
;llave.internal.lab.             IN      A

;; ANSWER SECTION:
llave.internal.lab.      60      IN      A       203.0.113.47

;; Query time: 3 msec
;; SERVER: 127.0.0.1#5360(127.0.0.1) (UDP)
;; WHEN: Sun Nov 08 17:48:29 -03 2026
;; MSG SIZE  rcvd: 52
```

El espaciado de las columnas se presenta normalizado, conservando los valores de la salida.

### Interpretación

- NOERROR: la consulta no informó un error DNS.
- ANSWER: 1: recibimos un registro de respuesta.
- A 203.0.113.47: dirección IPv4 del nombre consultado.
- 60: TTL del registro, en segundos; no forma parte de la passphrase.
- SERVER confirma que respondió el DNS local en el puerto 5360 por UDP.

Como la consigna define esa dirección como passphrase, la frase exacta es:

```text
203.0.113.47
```

Se conserva como texto con sus puntos. No se hace SSH a esa IP: el destino de la práctica sigue siendo 127.0.0.1.

## 8. Restringir permisos del archivo privado

Se ejecutó:

```bash
chmod 600 mykey2
```

La clave descargada tenía inicialmente permisos 0664 y OpenSSH advirtió:

```text
WARNING: UNPROTECTED PRIVATE KEY FILE!
Permissions 0664 for 'mykey2' are too open.
It is required that your private key files are NOT accessible by others.
This private key will be ignored.
```

chmod 600 restringe el acceso al propietario:

| Categoría | Permisos |
|---|---|
| Dueño | Lectura y escritura: 6 = 4 + 2 |
| Grupo | Ninguno: 0 |
| Otros | Ninguno: 0 |

El resultado corresponde a `-rw-------`. La clave no necesita ejecución. El comando normalmente no imprime salida cuando tiene éxito.

Cambiar permisos no descifra la clave ni cambia su passphrase; limita quién puede leerla o modificarla.

## 9. Ingresar por SSH

Comando del ingreso confirmado:

```bash
ssh -v -i mykey2 -o IdentitiesOnly=yes jerodileo@127.0.0.1
```

| Parte | Función |
|---|---|
| ssh | Cliente de conexión segura. |
| -v | Muestra diagnóstico para verificar qué identidad se ofrece y acepta. |
| -i mykey2 | Selecciona la clave privada descargada. |
| -o IdentitiesOnly=yes | Limita las identidades ofrecidas a las seleccionadas por opciones o configuración, evitando otras identidades del agente ajenas a esa selección. |
| jerodileo | Cuenta destino indicada por la preparación del lab. |
| 127.0.0.1 | Servidor SSH local. |

No se escribió -p porque SSH usa el puerto 22 por defecto. El puerto 8060 era de HTTP y 5360 era del DNS: cada servicio tiene su dirección y puerto.

IdentitiesOnly no elimina posibles IdentityFile definidos por configuración. En este ingreso, la evidencia concreta del verbose confirma que se usó mykey2.

### Fragmentos reales del ingreso exitoso

Se seleccionan las líneas relevantes del verbose completo:

```text
debug1: Connecting to 127.0.0.1 [127.0.0.1] port 22.
debug1: Connection established.
debug1: loaded pubkey from mykey2: RSA SHA256:b8ehI9L4zrMHxw6VE8YgQdrVvHi5R1yzG6VNFh/8pDE
debug1: Authenticating to 127.0.0.1:22 as 'jerodileo'
debug1: Host '127.0.0.1' is known and matches the ED25519 host key.
debug1: Offering public key: mykey2 RSA SHA256:b8ehI9L4zrMHxw6VE8YgQdrVvHi5R1yzG6VNFh/8pDE explicit
debug1: Server accepts key: mykey2 RSA SHA256:b8ehI9L4zrMHxw6VE8YgQdrVvHi5R1yzG6VNFh/8pDE explicit
Enter passphrase for key 'mykey2':
Authenticated to 127.0.0.1 ([127.0.0.1]:22) using "publickey".
debug1: Entering interactive session.
```

En el pedido de passphrase se utilizó la obtenida del DNS. No se muestran caracteres al escribirla; es normal.

El final incluyó:

```text
Welcome to Ubuntu 26.04.1 LTS (GNU/Linux 7.0.0-43-generic x86_64)
```

Y apareció:

```text
jerodileo@jerOS:~$
```

La secuencia Server accepts key → pedido de passphrase → Authenticated using publickey confirma el ingreso con la identidad del ejercicio.

La clave del host ED25519 que se verifica en known_hosts identifica al servidor. No debe confundirse con la clave RSA mykey2 que utilizamos para autenticarnos como cliente.

## 10. Passphrase y contraseña del usuario

La passphrase desbloquea el archivo privado local. Es distinta de la contraseña de la cuenta remota.

| Pedido de SSH | Qué solicita |
|---|---|
| Enter passphrase for key 'mykey2': | La frase de la clave: 203.0.113.47. |
| jerodileo@127.0.0.1's password: | La contraseña del usuario remoto, si se intenta ese método. |

En el ingreso exitoso se pidió la passphrase de mykey2 y se confirmó autenticación por clave pública.

## 11. Cadena de comandos de resolución

Con el lab preparado y SSH activo:

```bash
curl -i 127.0.0.1:8060
curl -i 127.0.0.1:8060/robots.txt
curl -i 127.0.0.1:8060/privado/respaldo/id_rsa
curl 127.0.0.1:8060/privado/respaldo/id_rsa -o mykey2
dig @127.0.0.1 -p 5360 A llave.internal.lab
chmod 600 mykey2
ssh -v -i mykey2 -o IdentitiesOnly=yes jerodileo@127.0.0.1
```

La passphrase se ingresa cuando SSH la solicita, no como argumento del comando.

Para salir de la sesión SSH se puede usar exit. No se pegó una ejecución de ese cierre al terminar el ejercicio.

## 12. Pistas que conectaron los pasos

| Resultado observado | Próxima decisión |
|---|---|
| Comentario HTML que menciona robots.txt | Consultar ese archivo. |
| Disallow: /privado/respaldo/ | Investigar un archivo candidato en ese directorio. |
| 200 y delimitadores de clave privada | Descargar el cuerpo con -o, sin -i. |
| Consigna: la passphrase es una dirección IP | Consultar el registro A del nombre indicado. |
| Respuesta A 203.0.113.47 | Usar ese texto como passphrase. |
| Permisos demasiado abiertos | Restringirlos con chmod 600. |
| Server accepts key y Authenticated using publickey | Confirmar que se ingresó con mykey2. |

**Resultado observado:** clave descubierta mediante pistas HTTP, passphrase obtenida por DNS e ingreso SSH confirmado con mykey2.
