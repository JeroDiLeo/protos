# Protocolos — Recu 2026, ejercicio 2: acceso SSH por clave
## Objetivo y resultado real
Configurar autenticación por clave en la cuenta del laboratorio para entrar aunque cambie su contraseña.

El servidor parcial.protos.foo no respondió al descubrimiento de Nmap; el intento con -Pn fue interrumpido. No se determinó su puerto ni se modificó ese servidor.
Se practicó en un sshd local independiente, 127.0.0.1:2222, usuario parcial, contraseña inicial holamundo.

Resultado comprobado por el estudiante:
1. Se instaló su clave pública con ssh-copy-id.
2. Entró por clave con contraseña y keyboard-interactive desactivados.
3. Cambió la contraseña.
4. La contraseña vieja dio Permission denied.
5. La misma clave siguió entrando en una conexión nueva.
6. Se verificaron permisos 700 y 600.
7. Se retiró el laboratorio: sshd detenido, puerto libre, cuenta y configuración eliminadas.

## ⭐ RECETA PARA EL PARCIAL (leer esto primero)

> El tema es **autenticación por clave pública de SSH**, un mecanismo estándar. La idea del ejercicio: la clave pública en `~/.ssh/authorized_keys` y la contraseña son **dos métodos de autenticación independientes**, así que una conexión por clave sigue entrando aunque cambie la contraseña de la cuenta.
>
> Lo probaste contra un sshd local en `127.0.0.1:2222` (toda la parte de abajo). Según los apuntes del tercero, en el parcial real el SSH estaba en el **puerto 22**. **Averiguá el puerto con nmap antes de copiar nada.**

### Datos que pueden cambiar
| Dato | En esta práctica | En el parcial (apuntes 3ro) |
|---|---|---|
| Host | `127.0.0.1` | `parcial.protos.foo` |
| Puerto | `2222` | `22` (verificar con nmap) |
| Usuario | `parcial` | `parcial` |
| Contraseña inicial | `holamundo` | `holamundo` |
| Mi clave pública | `~/.ssh/id_ed25519_e100.pub` | la que tengas; si no, generala |

### Los 3 pasos
~~~bash
# 1. Averiguar el puerto de SSH (puede no ser el 22)
nmap -sV parcial.protos.foo

# 2. Instalar mi clave pública en la cuenta (pide la contraseña holamundo UNA vez)
ssh-copy-id -p 22 -i ~/.ssh/id_ed25519.pub parcial@parcial.protos.foo

# 3. Demostrar que entro SIN contraseña, solo con la clave
ssh -p 22 -i ~/.ssh/id_ed25519 -o PasswordAuthentication=no parcial@parcial.protos.foo
~~~

Si no tenés par de claves todavía, antes del paso 2:
~~~bash
ssh-keygen -t ed25519 -C "protos" -f ~/.ssh/id_ed25519
~~~

### Cómo se demuestra que "sigue entrando aunque cambien la contraseña"
~~~bash
# dentro de la cuenta parcial, simular que el admin cambia la contraseña:
passwd
# desde tu máquina, forzar contraseña con la vieja → Permission denied:
ssh -p 22 -o PubkeyAuthentication=no -o PreferredAuthentications=password parcial@parcial.protos.foo
# repetir el paso 3 (por clave) → entra igual
ssh -p 22 -i ~/.ssh/id_ed25519 -o PasswordAuthentication=no parcial@parcial.protos.foo
~~~

### Por qué funciona (para el video)
- `ssh-copy-id` agrega mi clave **pública** al archivo `~/.ssh/authorized_keys` de la cuenta remota. La clave **privada** nunca sale de mi máquina.
- Al conectarme, mi cliente firma un desafío con la privada y el servidor lo verifica con la pública autorizada. No viaja ninguna contraseña.
- La contraseña de la cuenta y la lista de claves autorizadas son cosas separadas: cambiar una no toca la otra. Por eso la clave sigue sirviendo.

### Si no está `ssh-copy-id`, el paso 2 a mano
~~~bash
cat ~/.ssh/id_ed25519.pub | ssh -p 22 parcial@parcial.protos.foo \
  'mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys'
~~~
Es `>>` (agrega), no `>` (que pisaría el archivo). Los permisos 700 en `~/.ssh` y 600 en `authorized_keys` son necesarios: con `StrictModes` activado, el servidor ignora la clave si el directorio o el archivo tienen permisos de más.

### Explicación para el video
"La contraseña y las claves públicas autorizadas son métodos independientes. Instalo mi clave pública con `ssh-copy-id` usando la contraseña filtrada una vez, y demuestro que una conexión nueva entra solo con la clave. Al cambiar la contraseña, la clave sigue funcionando porque el servidor la verifica contra `authorized_keys`, que no se modificó."

### Checklist si algo falla
| Síntoma | Causa | Arreglo |
|---|---|---|
| `nmap` dice "Host seems down" | el host no responde a ping | `nmap -Pn -sV parcial.protos.foo` |
| SSH no está en el 22 | puerto no convencional | `nmap -Pn -sV -p- parcial.protos.foo` y usar ese puerto en `-p` |
| la clave no entra y pide contraseña | permisos de `~/.ssh` o `authorized_keys` mal | `chmod 700 ~/.ssh` y `chmod 600 ~/.ssh/authorized_keys` en la cuenta remota |
| `ssh-copy-id` no pide la contraseña | la clave ya estaba instalada | seguir al paso 3 directamente |

---

# PRÁCTICA (detalle de lo que se ejecutó en el sshd local)

## 1. Encontrar el puerto
~~~bash
nmap -sV parcial.protos.foo
~~~
nmap explora el host; -sV identifica servicios/versiones en puertos abiertos. Por defecto examina los 1000 puertos TCP más habituales. Resultado: Host seems down; no se escanearon sus puertos.
~~~bash
nmap -Pn -sV parcial.protos.foo
~~~
-Pn omite descubrimiento previo del host; no demuestra que esté activo. Puede tardar si no hay respuestas. Se interrumpió con Ctrl+C.
Para buscar SSH fuera de puertos habituales, cuando el host sea accesible:
~~~bash
nmap -Pn -sV -p- parcial.protos.foo
~~~
-p- selecciona todos los puertos TCP del 1 al 65535. No se ejecutó completo en esta práctica.

## 2. Preparar el sshd local equivalente
### Comprobaciones
~~~bash
command -v sshd
~~~
command -v busca el ejecutable; sshd es servidor, ssh es cliente. Estaba instalado.
~~~bash
sudo ss -ltnp 'sport = :2222'
~~~
sudo permite ver procesos; ss muestra sockets; -l escucha; -t TCP; -n numérico; -p proceso; filtro de puerto local 2222. Estaba libre.
~~~bash
getent passwd parcial
~~~
getent consulta bases del sistema; passwd selecciona cuentas, no sus contraseñas. Se comprobó antes de crear el usuario.

### Cuenta
~~~bash
sudo useradd -m -s /bin/bash parcial
~~~
useradd crea cuenta; -m crea home; -s fija shell. Se creó para el laboratorio.
~~~bash
sudo passwd parcial
~~~
passwd establece la contraseña de la cuenta indicada; se ingresó holamundo dos veces. sudo actúa como administrador. No se cambió la contraseña de jerodileo.

### Configuración independiente
~~~bash
sudo nano /etc/ssh/sshd_config_practica
~~~
nano edita el archivo indicado. Contenido usado:
~~~text
Port 2222
ListenAddress 127.0.0.1
HostKey /etc/ssh/ssh_host_ed25519_key
PidFile /run/sshd-practica.pid

PermitRootLogin no
AllowUsers parcial

PasswordAuthentication yes
PubkeyAuthentication yes
KbdInteractiveAuthentication no
AuthenticationMethods any
AuthorizedKeysFile .ssh/authorized_keys
StrictModes yes
UsePAM yes
~~~
Port y ListenAddress seleccionan puerto e interfaz local. HostKey identifica al servidor, no al usuario. PidFile fija archivo de PID. PermitRootLogin y AllowUsers limitan cuentas.
PasswordAuthentication y PubkeyAuthentication habilitan los dos métodos que compararemos; KbdInteractiveAuthentication desactiva la alternativa interactiva.
AuthenticationMethods any permite un método habilitado, sin exigir contraseña y clave juntas. AuthorizedKeysFile es relativo al home remoto. StrictModes controla propietarios/permisos. UsePAM habilita controles PAM, incluidos cuenta y sesión.
Esta configuración se cargó explícitamente, sin editar la habitual.

### Validar e iniciar
~~~bash
sudo /usr/sbin/sshd -t -f /etc/ssh/sshd_config_practica
~~~
-t valida configuración y claves del servidor, no inicia; -f selecciona archivo. Pasó sin salida.
~~~bash
sudo /usr/sbin/sshd -D -e -f /etc/ssh/sshd_config_practica
~~~
-D mantiene primer plano; -e envía mensajes a la terminal; -f carga configuración. No confundir sshd -D con ssh -D (SOCKS). Se mantuvo esta terminal abierta.

Desde otra terminal:
~~~bash
nmap -sV -p 2222 127.0.0.1
~~~
-p limita a ese puerto; dirección loopback selecciona esta máquina.
Resultado real:
~~~text
2222/tcp open ssh OpenSSH 10.2p1 Ubuntu 2ubuntu3.8
~~~

## 3. Revisar claves existentes
Desde jerodileo:
~~~bash
ls -la ~/.ssh
~~~
ls lista; -l muestra permisos/propietario; -a incluye nombres con punto; ~ es home del usuario actual.
Existían id_ed25519_e100 y su .pub, además de id_ed25519_e100_protegida y su .pub. Se reutilizó el primer par, sin generar ni sobrescribir claves.
Privada: permiso 600. Pública: permiso 644. El nombre protegida no prueba por sí solo que haya passphrase.

Si no hubiera claves, generar un par en una ruta nueva:
~~~bash
ssh-keygen -t ed25519 -C "protos-parcial" -f ~/.ssh/id_ed25519_parcial
~~~
-t elige algoritmo; -C agrega comentario identificatorio; -f fija el nombre de la privada, con pública en el mismo nombre más .pub. No aceptar sobrescribir una clave previa.
La passphrase protege la privada almacenada localmente. Vacía evita esa protección: quien obtenga el archivo puede usarlo. No es la contraseña del usuario remoto. No se generó este par durante la práctica porque ya existía uno.

## 4. Instalar la pública
~~~bash
ssh-copy-id -i ~/.ssh/id_ed25519_e100.pub -p 2222 parcial@127.0.0.1
~~~
-i elige pública; -p el puerto SSH; usuario@host el destino. La privada permanece local.
La primera conexión preguntó por la identidad del servidor; se aceptó y se registró [127.0.0.1]:2222 en known_hosts. En uso real, contrastar la huella con una fuente confiable. No es una pregunta sobre la clave del usuario.
Se ingresó holamundo para instalar la pública. Resultado:
~~~text
Number of key(s) added: 1
~~~
ssh-copy-id prueba claves para filtrar las ya instaladas; autentica por SSH y agrega las restantes al authorized_keys de la cuenta remota, preparando directorio y permisos.
No copia la privada ni modifica el authorized_keys local de jerodileo.

## 5. Probar exclusivamente con clave
Desde jerodileo:
~~~bash
ssh -i ~/.ssh/id_ed25519_e100 -o IdentitiesOnly=yes -o PasswordAuthentication=no -o KbdInteractiveAuthentication=no -p 2222 parcial@127.0.0.1
~~~
-i selecciona privada, sin .pub; -o pasa una opción de cliente.
IdentitiesOnly limita identidades explícitas/configuradas; PasswordAuthentication=no y KbdInteractiveAuthentication=no impiden recurrir a esos métodos. -p selecciona puerto.
Resultado real: prompt parcial@jerOS:~$.

La privada firma una prueba del protocolo; no se envía al servidor. La pública autorizada permite verificarla.
Si pide passphrase for key, es para desbloquear la privada local, no para autenticar con la contraseña de la cuenta remota.

## 6. Cambiar contraseña y contrastar métodos
Dentro de parcial:
~~~bash
passwd
~~~
Sin argumentos cambia la contraseña propia. Se ingresó actual holamundo y una nueva, confirmada. La política local puede rechazar contraseñas débiles; atender al mensaje real de passwd. No hay que revelar la nueva contraseña en el chat.

Desde otra terminal jerodileo, forzar contraseña:
~~~bash
ssh -o PubkeyAuthentication=no -o KbdInteractiveAuthentication=no -o PreferredAuthentications=password -o NumberOfPasswordPrompts=1 -p 2222 parcial@127.0.0.1
~~~
PubkeyAuthentication=no impide entrar con claves; PreferredAuthentications=password selecciona contraseña; NumberOfPasswordPrompts=1 limita a un intento solicitado.
Se ingresó holamundo: Permission denied.

Luego se repitió el comando por clave del apartado 5. Entró de nuevo como parcial.
Conclusión: cambiar contraseña no borra authorized_keys. Son métodos independientes en esta configuración; controles de cuenta pueden afectar ambos.

## 7. Permisos y ubicación
Dentro de parcial:
~~~bash
ls -ld ~/.ssh ~/.ssh/authorized_keys
~~~
-d muestra el directorio en sí; -l muestra detalles. ~ ahora significa /home/parcial.
Salida real:
~~~text
drwx------ parcial parcial ... /home/parcial/.ssh
-rw------- parcial parcial ... /home/parcial/.ssh/authorized_keys
~~~
700 en directorio y 600 en archivo; propietario parcial. Solo el dueño puede acceder al directorio y modificar el archivo. StrictModes comprueba modos y propietarios relevantes, incluido home. No implica que únicamente la combinación exacta 700/600 sea siempre válida: el punto es evitar escritura no autorizada.

## 8. Alternativa manual — también ejecutada
Ejecutar desde jerodileo, donde existe la pública:
~~~bash
cat ~/.ssh/id_ed25519_e100.pub | ssh -p 2222 parcial@127.0.0.1 'mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys'
~~~
- cat local lee la pública de jerodileo.
- | la pasa por entrada estándar a SSH.
- El comando entre comillas se ejecuta como parcial; sus ~ apuntan a /home/parcial.
- mkdir -p crea directorio y acepta existente.
- chmod cambia permisos; 700 en directorio y 600 en archivo.
- && continúa solo si tuvo éxito la instrucción previa.
- cat remoto lee la clave recibida; >> agrega al archivo. > lo vaciaría, eliminando otras claves.

Se ejecutó después de ssh-copy-id y terminó sin errores, sin contraseña: pudo autenticar con la clave ya instalada. Agregó otra copia de la misma pública; duplicado innecesario que no impedía entrar. No repetirlo para “verificar”, ya que modifica el archivo. La copia manual no deduplica como intenta hacer ssh-copy-id.

## 9. Resumen operativo para el servidor del parcial
Sustituir PUERTO por el número real encontrado, no copiar literalmente:
~~~bash
nmap -sV parcial.protos.foo
ssh-copy-id -i ~/.ssh/id_ed25519_e100.pub -p PUERTO parcial@parcial.protos.foo
ssh -i ~/.ssh/id_ed25519_e100 -o IdentitiesOnly=yes -o PasswordAuthentication=no -o KbdInteractiveAuthentication=no -p PUERTO parcial@parcial.protos.foo
~~~
Resultados esperados: servicio SSH abierto; clave instalada con contraseña inicial; entrada sin contraseña de cuenta. No se validaron contra el host real inaccesible.

## 10. Variantes: qué cambia y qué línea tocar
| Cambio | Sintaxis |
|---|---|
| Otro usuario | ssh -i ~/.ssh/id_ed25519_e100 -p 2222 otro@127.0.0.1 |
| Otro puerto | ssh -i ~/.ssh/id_ed25519_e100 -p 2200 parcial@host |
| Otra contraseña inicial | Ingresarla en el prompt de ssh-copy-id; no cambia el comando |
| Otra pública | ssh-copy-id -i ~/.ssh/otra.pub -p 2222 parcial@host |
| Otra privada | ssh -i ~/.ssh/otra -p 2222 parcial@host |
| Ed25519 nuevo | ssh-keygen -t ed25519 -C "protos" -f ~/.ssh/id_ed25519_parcial |
| RSA nuevo | ssh-keygen -t rsa -b 3072 -C "protos" -f ~/.ssh/id_rsa_parcial |
| Alias | Bloque Host de abajo en ~/.ssh/config |
| Privada .pem | chmod 600 ~/Downloads/llave.pem, luego ssh -i ~/Downloads/llave.pem -p PUERTO usuario@host |

-b en ssh-keygen indica tamaño RSA en bits. Instalar la pública del nuevo par antes de intentar usarlo.
La extensión .pem no garantiza algoritmo ni formato compatible: debe ser una clave privada que OpenSSH pueda leer, y su pública debe estar autorizada. Su passphrase se ingresa al desbloquearla; no es la contraseña remota. chmod 600 da lectura/escritura solo al dueño.

### Clave con passphrase y ssh-agent
Desde jerodileo, en una sesión que no tenga agente utilizable:
~~~bash
eval "$(ssh-agent -s)"
~~~
ssh-agent mantiene identidades para firmar; -s imprime instrucciones de shell; $(...) captura esas instrucciones y eval las aplica al entorno de esta terminal.
Luego:
~~~bash
ssh-add ~/.ssh/id_ed25519_e100_protegida
~~~
ssh-add carga esa clave, pidiendo su passphrase si la tiene. Su pública también debe estar instalada en el destino. Las conexiones pueden usar el agente sin pedir la passphrase cada vez; no elimina la passphrase del archivo.
Para retirar esa identidad del agente:
~~~bash
ssh-add -d ~/.ssh/id_ed25519_e100_protegida
~~~
-d elimina esa identidad del agente, no borra el archivo. No se ejecutó esta variante.

### Alias de cliente
Agregar un bloque, conservando los anteriores, en ~/.ssh/config:
~~~sshconfig
Host parcial-practica
    HostName 127.0.0.1
    User parcial
    Port 2222
    IdentityFile ~/.ssh/id_ed25519_e100
    IdentitiesOnly yes
~~~
Host define alias, HostName dirección, User cuenta, Port puerto, IdentityFile privada, IdentitiesOnly limita identidades. Entonces:
~~~bash
ssh parcial-practica
~~~
No se agregó ese bloque durante esta práctica. Tras limpiar, no funcionará hasta recrear el laboratorio.

## 11. Límites
Puede fallar si se elimina/revoca la pública, se deshabilita PubkeyAuthentication, se cambia AuthorizedKeysFile o home sin trasladar claves, se alteran permisos/propietarios, se exige autenticación adicional, se bloquea/expira la cuenta según PAM/políticas o se restringe el algoritmo.
También requiere conservar la privada y, si corresponde, poder desbloquearla. No otorga inmunidad frente a controles administrativos ni equivale a cifrar la privada en el servidor.

## 12. Limpieza real
Se salió de la sesión de parcial con exit. Se detuvo la instancia sshd en primer plano con Ctrl+C.
Se consultó ss y el estudiante confirmó que 2222 no escuchaba.
Desde jerodileo:
~~~bash
sudo userdel -r parcial
~~~
userdel elimina cuenta; -r home y buzón. Avisó que /var/mail/parcial no existía: no había buzón para borrar.
~~~bash
getent passwd parcial
~~~
No imprimió nada: cuenta ausente.
~~~bash
sudo rm /etc/ssh/sshd_config_practica
~~~
rm eliminó la configuración creada para el laboratorio. No se reinició ni modificó la configuración habitual de SSH.
Las claves originales de jerodileo se conservaron. known_hosts conserva la identidad aceptada del servidor: no es un usuario ni un servicio y no abre puertos.

## Justificación breve para el parcial
“Instalo mi clave pública en authorized_keys y demuestro una conexión nueva con autenticación por clave; al cambiar la contraseña, la clave sigue funcionando porque es un método independiente.”

## Guardar en la VM
Descargar 26.r-2.md. Si quedó en Downloads:
~~~bash
mkdir -p ~/protos/soluciones
~~~
mkdir crea directorios y -p padres faltantes.
~~~bash
cp ~/Downloads/26.r-2.md ~/protos/soluciones/26.r-2.md
~~~
cp copia origen a destino; ~ es el home local.

## Fuentes oficiales
- [ssh-keygen](https://man.openbsd.org/ssh-keygen)
- [Configuración del cliente](https://man.openbsd.org/ssh_config)
- [ssh-agent](https://man.openbsd.org/ssh-agent)
- [Configuración del servidor](https://man.openbsd.org/sshd_config)

