# LabRecu2026 · Ejercicio 4 · Acceso SSH con clave

El enunciado da el servidor `parcial.protos.foo`, el usuario `parcial` y su contraseña inicial. Pide demostrar que se puede volver a entrar aunque cambie esa contraseña. La resolución usa el acceso inicial para autorizar una clave pública en la cuenta remota. Después prueba el inicio de sesión con el par de claves antes y después del cambio.

## 1. Identificar el servicio y el puerto

Desde `root@alumno`:

```bash
nmap -n -sV parcial.protos.foo
```

`-sV` interroga los puertos abiertos para identificar los servicios y sus versiones. `-n` evita las búsquedas DNS inversas. Como el destino se escribió por nombre, Nmap igual tuvo que resolverlo para conectarse.

Salida relevante:

```text
Nmap scan report for parcial.protos.foo (192.168.60.90)
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 9.6p1 Ubuntu 3ubuntu13.20 (Ubuntu Linux; protocol 2.0)
```

De esta fila sacamos el **puerto 22** y el protocolo **SSH**. Como 22 es el puerto predeterminado de SSH, podemos omitir `-p 22`.

## 2. Entrar con la contraseña del enunciado

```bash
ssh parcial@parcial.protos.foo
```

Antes de la arroba va el usuario remoto y después el host. Ante el pedido `(parcial@parcial.protos.foo) Password:`, se ingresó la contraseña inicial indicada por el enunciado. Dentro de la sesión, se comprobó la identidad:

```text
parcial@4a71e8b44596:~$ whoami
parcial
```

En la primera conexión, SSH mostró la huella de **la clave del servidor**. Al aceptarla, quedó registrada en `~/.ssh/known_hosts` de `alumno`. Esa huella sirve para reconocer al servidor en conexiones futuras. La clave que vamos a generar en el paso siguiente sirve para identificar al cliente. Conviene conservar abierta la sesión inicial mientras se hacen las pruebas desde otra terminal de `alumno`.

## 3. Generar el par de claves en alumno

```bash
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_recu4 -C "recu4-62815"
```

| Parte | Qué hace y por qué se usó |
|---|---|
| `ssh-keygen` | Genera el par de claves localmente en `alumno`. |
| `-t ed25519` | Elige Ed25519 como algoritmo de firma. |
| `-f ~/.ssh/id_ed25519_recu4` | Define la ruta de la clave privada. El programa usa esa ruta con sufijo `.pub` para la pública. En este caso, `~` es `/root`. |
| `-C "recu4-62815"` | Agrega un comentario para identificar la clave del ejercicio y el legajo de práctica. |

Salida relevante:

```text
Generating public/private ed25519 key pair.
Enter passphrase (empty for no passphrase):
Enter same passphrase again:
Your identification has been saved in /root/.ssh/id_ed25519_recu4
Your public key has been saved in /root/.ssh/id_ed25519_recu4.pub
The key fingerprint is:
SHA256:9AoCWTAFJ+UFLIwWXbPja7FbcTRoeXRLa+ptCRvUA1c recu4-62815
```

| Elemento | Dónde se usa | Para qué sirve |
|---|---|---|
| Pública `id_ed25519_recu4.pub` | En el paso 4 se copia al `~/.ssh/authorized_keys` de `parcial`. | El servidor la usa para verificar la firma del cliente y decidir si esa identidad puede entrar en la cuenta. |
| Privada `id_ed25519_recu4` | Queda en `alumno`. En el paso 5 se indica con `ssh -i`. | El cliente firma una prueba de autenticación sin enviar el archivo privado al servidor. |
| Passphrase | Se ingresa al generar el par y cuando SSH pide desbloquear la privada. | Protege el archivo privado en disco. El cliente la usa localmente para abrirlo y firmar. |
| Contraseña de `parcial` | Se ingresa ante el prompt de la cuenta remota. | Permite el acceso inicial y la instalación de la pública. `passwd` cambia esta credencial. |

La huella SHA256 es un identificador corto de la clave pública. En el paso 5 la comparamos con la huella del log para identificar la clave que aceptó el servidor.

## 4. Autorizar la clave pública en el servidor

Desde `alumno`:

```bash
ssh-copy-id -i ~/.ssh/id_ed25519_recu4.pub parcial@parcial.protos.foo
```

`ssh-copy-id` prepara el acceso por clave. Con `-i` se le indica qué identidad instalar. Acá se selecciona el archivo `.pub` porque su contenido se agrega al `authorized_keys` de la cuenta remota. Ese archivo es la lista de claves públicas con acceso permitido para el usuario `parcial`.

```text
/usr/bin/ssh-copy-id: INFO: Source of key(s) to be installed: "/root/.ssh/id_ed25519_recu4.pub"
/usr/bin/ssh-copy-id: INFO: attempting to log in with the new key(s), to filter out any that are already installed
/usr/bin/ssh-copy-id: INFO: 1 key(s) remain to be installed -- if you are prompted now it is to install the new keys
(parcial@parcial.protos.foo) Password:

Number of key(s) added: 1
```

Primero prueba si la clave ya permite entrar, para evitar duplicarla. Como quedó una por instalar, pidió la contraseña vigente de `parcial` para poder escribir en su cuenta. `Number of key(s) added: 1` confirma que la instalación se hizo. La prueba de que se puede autenticar con ella viene a continuación.

## 5. Probar la clave antes de cambiar la contraseña

Desde `alumno`:

```bash
ssh -v -i ~/.ssh/id_ed25519_recu4 \
  -o IdentitiesOnly=yes \
  -o PreferredAuthentications=publickey \
  -S none \
  parcial@parcial.protos.foo whoami
```

| Parte | Qué demuestra o controla |
|---|---|
| `-v` | Muestra la clave ofrecida, la aceptada y el método con el que se completó la autenticación. |
| `-i ~/.ssh/id_ed25519_recu4` | Selecciona el archivo privado local para que SSH pueda firmar. |
| `-o IdentitiesOnly=yes` | Limita el cliente a las identidades seleccionadas explícitamente o configuradas. La huella en el log permite comprobar cuál se usó. |
| `-o PreferredAuthentications=publickey` | Limita esta prueba a la autenticación por clave pública. |
| `-S none` | Deshabilita la reutilización de una conexión SSH multiplexada. Esta ejecución tiene que autenticar de nuevo. |
| `whoami` | Ejecuta un comando en el servidor. Si imprime `parcial`, confirma con qué usuario se ejecutó. |

Salida relevante del primer intento con la clave:

```text
debug1: Offering public key: /root/.ssh/id_ed25519_recu4 ED25519 SHA256:9AoCWTAFJ+UFLIwWXbPja7FbcTRoeXRLa+ptCRvUA1c explicit
debug1: Server accepts key: /root/.ssh/id_ed25519_recu4 ED25519 SHA256:9AoCWTAFJ+UFLIwWXbPja7FbcTRoeXRLa+ptCRvUA1c explicit
Enter passphrase for key '/root/.ssh/id_ed25519_recu4':
Authenticated to parcial.protos.foo ([192.168.60.90]:22) using "publickey".
parcial
debug1: Exit status 0
```

`Offering public key` dice qué clave propuso el cliente. `Server accepts key` muestra que el servidor reconoce la pública con la misma huella del paso 3. El cliente desbloqueó la privada con la passphrase y firmó la prueba. La línea `Authenticated ... using "publickey"` confirma que la autenticación se completó.

## 6. Cambiar la contraseña y repetir la prueba

En la sesión remota abierta como `parcial`, ejecutar:

```bash
passwd
```

El comando pide la contraseña actual y la nueva dos veces. Cambia la contraseña de la cuenta del usuario que lo ejecuta. El mensaje `password updated successfully` es la confirmación esperada.

Volver a `alumno` y repetir exactamente el comando SSH del paso 5. Si SSH muestra `Enter passphrase for key`, ingresar la passphrase de la clave privada. Ese prompt puede seguir apareciendo después del cambio de contraseña porque la clave privada sigue protegida localmente.

**Resultado informado al repetir la prueba**: `whoami` devolvió `parcial`. El log detallado incluido arriba corresponde a la prueba anterior al cambio. Para la defensa, la evidencia completa se puede mostrar con la confirmación de `passwd` seguida de `Authenticated ... using "publickey"` y `parcial` en la conexión posterior.

La razón por la que funciona es que el cambio de contraseña y la lista de claves autorizadas se gestionan por separado. Mientras la pública siga autorizada, la cuenta esté habilitada y el servidor permita ese método, el cliente puede entrar firmando con su privada.

## Variantes de parcial

| Si cambia el enunciado | Qué cambia en la resolución |
|---|---|
| SSH escucha en otro puerto | Usar `-p PUERTO` en `ssh` y en `ssh-copy-id`. Si el escaneo inicial no muestra el servicio, `nmap -n -p- --open parcial.protos.foo` revisa todos los puertos TCP. Después, `nmap -n -sV -p PUERTO parcial.protos.foo` identifica el servicio en el puerto encontrado. |
| Piden verificar la pública instalada | En `alumno`, usar `ssh-keygen -lf ~/.ssh/id_ed25519_recu4.pub`. En el servidor, como `parcial`, usar `ssh-keygen -lf ~/.ssh/authorized_keys` y buscar la misma huella. `-l` muestra huellas y `-f` indica el archivo. |
| Piden revocar el acceso de esa clave | Quitar su entrada específica de `authorized_keys` y repetir la prueba con una conexión nueva. La huella permite identificar la entrada aunque su comentario haya cambiado. |
