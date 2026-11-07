# Cheatsheet: SSH (claves, passphrase, túneles, proxy)

Recetas de parciales: [tunel-tail-pampero_1c2026.md](tunel-tail-pampero_1c2026.md) · [clave-publica-persistir-acceso_recu2026.md](clave-publica-persistir-acceso_recu2026.md) · [internet-sin-nat_2c2021.md](internet-sin-nat_2c2021.md) · [pem-enunciado.md](pem-enunciado.md) · práctica: [lab-ssh/](../lab-ssh/).

---

## 1. Lo que hay que tener claro

### Hay DOS pares de claves distintos
| Par | De quién | Dónde está la privada | Dónde está la pública | Para qué |
|---|---|---|---|---|
| **Host key** | del **servidor** | `/etc/ssh/ssh_host_*_key` (en el server) | la recibe el cliente al conectar; se guarda en `~/.ssh/known_hosts` | que **vos** sepas que el servidor es el verdadero |
| **User key** | del **usuario** | en el cliente: `~/.ssh/id_ed25519`, `id_rsa`, o el `.pem` que te den | en el server: `~/.ssh/authorized_keys` del usuario | que el **servidor** sepa que sos vos (sin contraseña) |

- La **privada nunca se manda**: se usa para firmar. La pública se puede copiar a cualquier lado.
- **Passphrase** = contraseña que **cifra el archivo** de la clave privada en tu disco. No viaja al servidor y no es la contraseña del usuario remoto. Se pide **antes** de conectar, para poder usar la clave.
- **Contraseña del usuario** = la que pide el servidor si no hay clave aceptada (`user@host's password:`).

### Cómo se lee un prompt
| Ves | Qué te pide | Qué significa |
|---|---|---|
| `Enter passphrase for key 'x':` | la passphrase **del archivo** | ssh va a usar tu clave; falta descifrarla |
| `user@host's password:` | la contraseña **del usuario remoto** | ninguna clave fue aceptada (o no se usó la que creías) |
| `Are you sure you want to continue connecting (yes/no)?` | aceptar la host key | primera vez con ese server: se guarda en `known_hosts` |
| `Permission denied (publickey)` | — | el server solo acepta claves y la tuya no está en `authorized_keys` |
| `Permission denied (publickey,password)` | — | falló todo lo que se probó |

### Formato del comando
~~~bash
ssh [opciones] usuario@host [comando]
ssh -p 2222 -i clave.pem -o IdentitiesOnly=yes alumno@10.0.0.5 'date'
~~~
Sin `comando` abre una shell; con `comando` lo ejecuta y vuelve.

---

## 2. Opciones de `ssh`

### Conectarse
| Opción | Qué hace | Cuándo |
|---|---|---|
| `-p PUERTO` | puerto del servidor (por defecto 22) | "SSH escucha en el puerto 2222", "el legajo es el puerto" |
| `-l usuario` | usuario (igual que `usuario@`) | — |
| `-i archivo` | clave privada a usar | te dan un `.pem` / `id_rsa` |
| `-o IdentitiesOnly=yes` | usa **solo** la `-i` (no las de `~/.ssh` ni del agente) | **siempre que uses `-i`**: si no, puede entrar con otra clave y no te enterás |
| `-o PubkeyAuthentication=no` | no usa claves | probar entrar solo con contraseña |
| `-o PreferredAuthentications=password` | fuerza contraseña | idem |
| `-o PasswordAuthentication=no` | no pide contraseña | probar que la clave anda sola |
| `-o StrictHostKeyChecking=no` | no pregunta por la host key | máquinas de laboratorio que se reinstalan |
| `-o UserKnownHostsFile=/dev/null` | no guarda host keys | junto con el anterior |
| `-o HostKeyAlgorithms=+ssh-rsa` / `-o PubkeyAcceptedAlgorithms=+ssh-rsa` | habilita RSA/SHA1 viejo | server viejo: `no matching host key type found` |
| `-o KexAlgorithms=+diffie-hellman-group1-sha1` | kex viejo | `no matching key exchange method` |
| `-v` / `-vv` | modo verboso | ver qué clave prueba y por qué falla |
| `-t` | fuerza una terminal | comando interactivo remoto (`ssh -t host top`, `sudo`) |
| `-q` | silencioso | — |
| `-C` | comprime | enlaces lentos |
| `-X` / `-Y` | reenvío X11 | abrir una ventana gráfica remota |
| `-J salto` | entra pasando por otro host (ProxyJump) | "solo se llega desde el bastión" |
| `-A` | reenvía tu agente | usar tu clave desde el host intermedio |

`-o` es la forma de pasar **cualquier opción de configuración** (las mismas de `~/.ssh/config`) desde la línea de comandos.

### Túneles
| Opción | Qué hace | Cuándo |
|---|---|---|
| `-L [bind:]PL:destino:PD` | **local**: tu `127.0.0.1:PL` → (por el server) → `destino:PD` | querés usar desde **tu** máquina un servicio que solo ve el server |
| `-R [bind:]PR:destino:PD` | **remoto**: el `PR` del **server** → (por vos) → `destino:PD` | que el **server** llegue a algo que solo ves vos |
| `-D [bind:]PL` | **dinámico**: SOCKS5 en tu `PL` que sale por el server | navegar "como si fueras el server" a muchos destinos |
| `-R PR` (sin destino) | SOCKS **remoto**: proxy SOCKS en el server que sale por vos | darle internet a un host sin NAT |
| `-N` | no ejecuta comando (solo túnel) | túneles |
| `-f` | se va a segundo plano después de autenticar | `ssh -fN -L …` |
| `-g` | permite que otros usen tu puerto local de `-L` | compartir el túnel en la red |
| `-o ExitOnForwardFailure=yes` | falla si no puede abrir el túnel | que no quede una sesión "sin túnel" |
| `-o ServerAliveInterval=30` | keepalive | túneles largos que se cortan |

---

## 3. Túneles: cómo pensarlos

**Regla:** `-L` abre el puerto **en tu máquina**; `-R` abre el puerto **en el servidor**. Lo que va después (`destino:PD`) se resuelve **desde el otro extremo**.

~~~text
-L 8080:interno:80  user@salto
   tu máquina:8080 ──SSH──▶ salto ──▶ interno:80
   ("interno" lo resuelve SALTO)

-R 9000:localhost:3000  user@server
   server:9000 ──SSH──▶ tu máquina ──▶ localhost:3000 (el TUYO)
   ("localhost" es tu máquina)

-D 1080  user@salto
   tu máquina:1080 (SOCKS) ──SSH──▶ salto ──▶ cualquier destino
~~~

### `-L` (local)
~~~bash
ssh -N -L 8080:10.0.0.20:80 alumno@salto       # usar: curl http://127.0.0.1:8080/
ssh -N -L 5432:localhost:5432 alumno@db         # el "localhost" es el DE db
ssh -N -L 8080:intra.lab:80 -L 2525:mail:25 alumno@salto   # varios a la vez
~~~
- `localhost` en el destino = **el servidor SSH**, no vos.
- Puerto local < 1024 requiere root: usá uno alto (8080, 10022…).
- Por defecto escucha solo en `127.0.0.1`. Para que lo usen otros: `-L 0.0.0.0:8080:…` o `-g`.

### `-R` (remoto)
~~~bash
ssh -N -R 9000:localhost:3000 alumno@server    # en el server: curl http://localhost:9000
ssh -N -R 63051:localhost:22 alumno@pampero    # el server entra a TU ssh por su puerto 63051
~~~
- `localhost` en el destino = **tu máquina**.
- En el server escucha solo en `127.0.0.1` salvo que `sshd_config` tenga `GatewayPorts yes` (o `clientspecified` y pidas `-R 0.0.0.0:9000:…`).
- Si el puerto ya está usado en el server: `Warning: remote port forwarding failed for listen port N` → elegí otro (por eso usan el legajo como puerto).

### `-D` (SOCKS dinámico)
~~~bash
ssh -N -D 1080 alumno@salto
curl -x socks5h://127.0.0.1:1080 http://intra.lab/      # el nombre lo resuelve salto
~~~

### Internet para un host sin NAT (proxy SOCKS remoto)
~~~bash
# desde TU máquina (que sí tiene internet), conectándote al host aislado:
ssh -N -R 1080 alumno@aislado
# en el host aislado:
curl -x socks5h://127.0.0.1:1080 http://example.com/
export ALL_PROXY=socks5h://127.0.0.1:1080      # para que otros programas lo usen
~~~
`-R` sin destino (OpenSSH ≥ 7.6) crea un SOCKS en el server que sale por vos.

### Saltar por un bastión
~~~bash
ssh -J alumno@bastion usuario@interno
ssh -J alumno@bastion:2222 -p 22 usuario@10.0.0.20
ssh -o ProxyCommand="ssh -W %h:%p alumno@bastion" usuario@interno   # equivalente viejo
~~~

### Verificar un túnel
~~~bash
ss -tlnp | grep 8080          # ¿está escuchando el puerto local?
curl -v http://127.0.0.1:8080/
ssh -O check host             # si usás ControlMaster
~~~
Cerrar un túnel en segundo plano: `pkill -f "ssh -fN -L 8080"` o `kill <pid>`.

---

## 4. Claves: comandos

### Generar / ver / verificar
| Comando | Qué hace |
|---|---|
| `ssh-keygen -t ed25519 -f ~/.ssh/mi_clave` | genera un par (`mi_clave` + `mi_clave.pub`); pide passphrase (Enter = sin) |
| `ssh-keygen -t rsa -b 4096 -f clave` | par RSA |
| `ssh-keygen -y -f clave` | **saca la pública** de la privada (pide la passphrase si tiene) |
| `ssh-keygen -y -P 'frase' -f clave` | verifica una passphrase **sin conectarte** (si es correcta imprime la pública; si no: `incorrect passphrase supplied`) |
| `ssh-keygen -p -f clave` | cambia / saca la passphrase |
| `ssh-keygen -l -f clave.pub` | huella (fingerprint) de una clave |
| `ssh-keygen -l -f /etc/ssh/ssh_host_ed25519_key.pub` | huella de la host key (para comparar con la que te muestra el cliente) |
| `ssh-keygen -R host` | borra la host key vieja de `known_hosts` |
| `ssh-keyscan -p 22 host` | baja la host key de un server |
| `ssh-keygen -e -f clave.pub` / `-i` | exportar/importar a formato RFC4716 |
| `ssh-keygen -p -m PEM -f clave` | convertir la privada a formato PEM |

### ¿Qué tipo de archivo tengo?
| Primera línea | Es |
|---|---|
| `-----BEGIN OPENSSH PRIVATE KEY-----` | privada formato OpenSSH (puede tener passphrase o no) |
| `-----BEGIN RSA PRIVATE KEY-----` | privada RSA PEM; si tiene `Proc-Type: 4,ENCRYPTED` tiene passphrase |
| `-----BEGIN PRIVATE KEY-----` / `ENCRYPTED PRIVATE KEY` | PKCS#8 (sin / con passphrase) |
| `ssh-ed25519 AAAA… comentario` | **pública** (va en `authorized_keys`) |
| `ssh-rsa AAAA…` | pública RSA |

### Instalar tu pública en el server (entrar sin contraseña)
~~~bash
ssh-copy-id -i ~/.ssh/mi_clave.pub -p 22 alumno@host
# a mano (si no hay ssh-copy-id):
cat ~/.ssh/mi_clave.pub | ssh alumno@host 'mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys'
~~~
Después: `ssh -i ~/.ssh/mi_clave -o IdentitiesOnly=yes alumno@host` → no pide contraseña (si tiene passphrase, pide **la passphrase**). Sirve para "seguir entrando aunque cambien la contraseña".

### Permisos (si no, ssh ignora la clave o el server la rechaza)
| Archivo | Permiso | Comando |
|---|---|---|
| clave privada | `600` (o `400`) | `chmod 600 clave.pem` |
| `~/.ssh/` | `700` | `chmod 700 ~/.ssh` |
| `~/.ssh/authorized_keys` | `600` (o `644`) | `chmod 600 ~/.ssh/authorized_keys` |
| `~` (home) | sin escritura para grupo/otros | `chmod go-w ~` |
| clave pública | `644` | — |

El dueño también importa: `chown -R usuario:usuario ~/.ssh`.

### Agente (no tipear la passphrase cada vez)
~~~bash
eval "$(ssh-agent -s)"
ssh-add clave.pem            # pide la passphrase una vez
ssh-add -l                   # claves cargadas
ssh-add -D                   # descargar todas
~~~
Ojo: con claves en el agente, `ssh` puede entrar con **otra** clave. Por eso `-o IdentitiesOnly=yes`.

---

## 5. Copiar archivos y ejecutar remoto

| Comando | Qué hace |
|---|---|
| `scp -P 2222 -i clave archivo user@host:/ruta/` | sube (ojo: `-P` **mayúscula** en scp) |
| `scp user@host:/ruta/archivo .` | baja |
| `scp -r carpeta user@host:` | carpeta entera |
| `scp -J bastion archivo user@interno:` | pasando por un salto |
| `sftp -P 2222 user@host` | sesión interactiva (`get`, `put`, `ls`) |
| `rsync -avz -e "ssh -p 2222 -i clave" dir/ user@host:dir/` | sincronizar |
| `ssh user@host 'tail -f /var/log/syslog'` | ejecuta y muestra en vivo (Ctrl+C corta) |
| `ssh user@host 'cat archivo' > local.txt` | traer la salida a un archivo local |
| `ssh user@host 'bash -s' < script.sh` | correr un script local en el server |
| `tar czf - dir \| ssh user@host 'tar xzf -'` | copiar por pipe |

---

## 6. El enunciado dice → qué hacer

| El enunciado dice… | Qué agregás / hacés |
|---|---|
| "el servidor SSH escucha en el puerto N" | `-p N` (en scp/sftp `-P N`) |
| "use su legajo como puerto" | `-p LEGAJO`, o `-L LEGAJO:…` / `-R LEGAJO:…` según el caso |
| "le dejamos una clave privada (.pem) en …" | descargarla (`curl -o` / `scp`), `chmod 600`, `ssh -i clave -o IdentitiesOnly=yes` |
| "la clave está protegida con una passphrase" | la passphrase es **un dato a descubrir** (no se adivina): mirar el enunciado/pistas |
| "la passphrase es la IP de X" | `dig +short X @DNS` (registro A) |
| "la passphrase es la MAC de X" | `arp -n` / `ip neigh` tras un `ping`, o la captura/DHCP; formato `aa:bb:cc:dd:ee:ff` |
| "la passphrase es un texto publicado en DNS" | `dig +short TXT nombre @DNS \| tr -d '"'` |
| "la passphrase la da un servicio interno / detrás de un proxy" | curl con lo que pida (`-H "Host: …"`, `-x`, token) |
| "verifique la passphrase sin conectarse" | `ssh-keygen -y -P 'frase' -f clave` |
| "pueda seguir entrando aunque cambien la contraseña" | generar par y poner la **pública** en `~/.ssh/authorized_keys` del server |
| "sin que le pida contraseña" | idem; probar con `-o PasswordAuthentication=no` |
| "el host no es accesible directamente, solo desde X" | `-J usuario@X`, o `-L` por X |
| "acceda desde su máquina al servicio web interno 10.0.0.20:80" | `ssh -N -L 8080:10.0.0.20:80 user@salto` + `curl http://127.0.0.1:8080` |
| "que el servidor pueda acceder a un servicio de su máquina" | `ssh -N -R PR:localhost:PL user@server` |
| "el host no tiene NAT / no tiene internet" | `ssh -N -R 1080 user@aislado` y en el aislado `-x socks5h://127.0.0.1:1080` |
| "use un proxy SOCKS a través de SSH" | `ssh -N -D 1080 user@salto` + `curl -x socks5h://127.0.0.1:1080 …` |
| "vea en vivo el archivo X del servidor" | `ssh user@host 'tail -f X'` (o por túnel si el enunciado lo exige) |
| "copie el archivo X a / desde el servidor" | `scp` |
| "verifique la identidad del servidor" | comparar `ssh-keygen -l -f /etc/ssh/ssh_host_*.pub` con el fingerprint del primer acceso |
| "el servidor cambió / se reinstaló" | `ssh-keygen -R host` y volver a aceptar |
| "solo las opciones estrictamente necesarias" | sacar `-v`, `-o StrictHostKeyChecking=no`; dejar `-p`, `-i`, túneles |
| "muestre que está adentro" | ejecutar algo visible: `hostname`, `whoami`, `date`, `ip a` |

---

## 7. Mensajes de error → qué significan → qué hacer

### Antes de autenticar (red / host key)
| Mensaje | Significa | Qué hacer |
|---|---|---|
| `Could not resolve hostname X` | tu máquina no conoce el nombre | IP directa, `/etc/hosts`, `dig` |
| `Connection refused` | llegás a la IP pero no hay SSH en ese puerto | revisar `-p`; `sudo systemctl start ssh` si es tu VM |
| `Connection timed out` / `No route to host` | no llegás (firewall, red, IP mala) | revisar red, salto, IP |
| `kex_exchange_identification: Connection closed by remote host` / `read: Connection reset` | el server cortó (no es SSH ese puerto, límite de conexiones, tcp_wrappers) | revisar puerto, esperar |
| `ssh_exchange_identification` / `banner exchange` | hablaste a algo que no es SSH | puerto equivocado |
| `REMOTE HOST IDENTIFICATION HAS CHANGED!` | la host key no coincide con `known_hosts` | si es esperable (reinstalado): `ssh-keygen -R host`. Si no: posible MITM |
| `Host key verification failed.` | rechazaste o no se pudo verificar la host key | aceptar (`yes`) o `ssh-keygen -R` |
| `no matching host key type found. Their offer: ssh-rsa` | server viejo | `-o HostKeyAlgorithms=+ssh-rsa` |
| `no matching key exchange method found` | kex viejo | `-o KexAlgorithms=+…` (el que ofrezca) |
| `Unable to negotiate … no matching cipher` | cifrado viejo | `-o Ciphers=+aes128-cbc` |

### Con la clave
| Mensaje | Significa | Qué hacer |
|---|---|---|
| `WARNING: UNPROTECTED PRIVATE KEY FILE!` … `bad permissions` / `This private key will be ignored` | la clave tiene permisos abiertos (ej. 644) | `chmod 600 clave` |
| `Load key "x": No such file or directory` | ruta mal | revisar `-i` |
| `Load key "x": invalid format` | el archivo no es una clave (bajaste un HTML, faltan líneas, CRLF) | `head clave`; `dos2unix clave`; volver a descargar |
| `Load key "x": error in libcrypto` | formato roto o incompatible (a veces RSA viejo / bytes corruptos) | revisar que esté completa, convertir (`ssh-keygen -p -m PEM`), regenerar |
| `Load key "x": incorrect passphrase supplied to decrypt private key` | passphrase mal | revisar el dato (espacios, mayúsculas, formato de IP/MAC) |
| `Enter passphrase for key` que **no aparece** y entra igual | entró con **otra** clave (agente o `~/.ssh/id_*`) | `-o IdentitiesOnly=yes` |
| `Enter passphrase` y después `password:` | la clave se descifró pero el server no la acepta | la pública no está en `authorized_keys` de **ese usuario** |
| `Permission denied (publickey)` | el server solo acepta clave y ninguna sirvió | usuario correcto, clave correcta, `authorized_keys` y permisos del lado server |
| `Permission denied (publickey,password)` | falló todo | usuario/contraseña/clave |
| `Too many authentication failures` | probó demasiadas claves del agente | `-o IdentitiesOnly=yes -i clave` |
| `sign_and_send_pubkey: no mutual signature supported` | RSA/SHA1 deshabilitado | `-o PubkeyAcceptedAlgorithms=+ssh-rsa` |

### Túneles
| Mensaje | Significa | Qué hacer |
|---|---|---|
| `bind [127.0.0.1]:8080: Address already in use` | ya hay algo en tu puerto local | otro puerto o matar el túnel viejo (`ss -tlnp`) |
| `bind: Permission denied` | puerto < 1024 sin root | usar puerto alto |
| `Warning: remote port forwarding failed for listen port N` | el puerto en el server está ocupado o no permitido | otro puerto (ej. tu legajo) |
| `channel N: open failed: connect failed: Connection refused` | el túnel anda pero el **destino** no tiene nada en ese puerto | revisar `destino:PD` (recordá desde dónde se resuelve) |
| `channel N: open failed: administratively prohibited` | el server no permite forwarding | `AllowTcpForwarding yes` en `sshd_config` (no depende de vos) |
| el túnel `-R` solo responde en el server desde `localhost` | `GatewayPorts no` | `GatewayPorts yes` en el server, o usarlo desde el server |
| curl por `-D` da `(97)` | usaste `socks5://` con nombre interno | `socks5h://` |

Diagnóstico general: `ssh -v …` muestra `Offering public key: …`, `Server accepts key`, `Authentications that can continue: …` y qué falla.

---

## 8. `~/.ssh/config` (para no repetir opciones)
~~~text
Host salto
    HostName 10.0.0.5
    User alumno
    Port 2222
    IdentityFile ~/clave.pem
    IdentitiesOnly yes

Host interno
    HostName 10.0.0.20
    User root
    ProxyJump salto
    LocalForward 8080 localhost:80
~~~
Después: `ssh salto`, `ssh interno`, `scp archivo interno:`. Permiso del archivo: `chmod 600 ~/.ssh/config`.

## 9. Del lado del servidor (si te piden configurar `sshd`)
| `/etc/ssh/sshd_config` | Para qué |
|---|---|
| `Port 2222` | cambiar puerto |
| `PermitRootLogin no` / `prohibit-password` | root sin contraseña / solo con clave |
| `PasswordAuthentication no` | solo claves |
| `PubkeyAuthentication yes` | aceptar claves |
| `AllowUsers alumno` | quiénes pueden entrar |
| `AllowTcpForwarding yes` | permitir túneles |
| `GatewayPorts yes` | que los `-R` escuchen en todas las interfaces |

Aplicar: `sudo sshd -t && sudo systemctl restart ssh`. Ver logs: `sudo journalctl -u ssh -f` (o `/var/log/auth.log`).

---

## 10. Recetas completas

### Clave expuesta + passphrase descubrible
~~~bash
curl -s -o clave.pem http://HOST/ruta/clave        # 1. bajarla
head -1 clave.pem                                   # 2. ¿es una clave? ¿tiene passphrase?
chmod 600 clave.pem                                 # 3. permisos
dig +short NOMBRE @DNS                              # 4. descubrir la passphrase (ej. IP)
ssh-keygen -y -P 'LA_FRASE' -f clave.pem            # 5. verificarla sin conectar
ssh -i clave.pem -o IdentitiesOnly=yes -p PUERTO usuario@HOST 'hostname; date'   # 6. entrar
~~~

### Persistir acceso (aunque cambien la contraseña)
~~~bash
ssh-keygen -t ed25519 -f ~/.ssh/parcial -N ''
ssh-copy-id -i ~/.ssh/parcial.pub usuario@HOST
ssh -i ~/.ssh/parcial -o IdentitiesOnly=yes -o PasswordAuthentication=no usuario@HOST
~~~

### Túnel local a un servicio interno
~~~bash
ssh -fN -L 8080:SERVICIO_INTERNO:80 usuario@SALTO
curl -i http://127.0.0.1:8080/
~~~

### `tail -f` en vivo de un archivo remoto por túnel (1C 2026; el legajo como puerto)
~~~bash
# TERMINAL 1 (tu máquina): túnel + shell en pampero
ssh -L LEGAJO:127.0.0.1:LEGAJO usuario@pampero.itba.edu.ar
#   ya dentro de pampero: publicar el archivo en el puerto (ANTES de conectar el paso 2)
tail -F /tmp/archivo-remoto | nc -l 127.0.0.1 LEGAJO

# TERMINAL 2 (tu máquina): recibir por el túnel
nc 127.0.0.1 LEGAJO > archivo.log

# TERMINAL 3 (tu máquina): lo que pide la consigna
tail -f archivo.log
~~~
Recorrido: tail remoto → nc remoto → túnel SSH → nc local → `archivo.log` → tail local. Detalle: [tunel-tail-pampero_1c2026.md](tunel-tail-pampero_1c2026.md).

### Qué decir en el video
«La clave pública va en `authorized_keys` del server y la privada queda en mi máquina con permisos 600; la passphrase solo descifra el archivo localmente. Con `-L` traigo a mi puerto local un servicio que solo ve el servidor; con `-R` le ofrezco al servidor un puerto que sale por mi máquina; con `-D` armo un SOCKS para salir por el servidor.»
