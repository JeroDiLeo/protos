# 2C 2021 — Ejercicio 2: SSH con llave y passphrase obtenida de una MAC

## RECETA PARA EL PARCIAL

**Datos de la consigna:** SSH en parcial.leak.com.ar:2222, usuario remoto pdc, llave en http://parcial.leak.com.ar/llave.pem. La passphrase es la MAC de bd1, consultada desde pampero.itba.edu.ar. Tu usuario de pampero es jdileomuntaner.

Hay TRES fuentes posibles de la passphrase, según la edición: la MAC de bd1 vista desde pampero (esta receta), la MAC de la interfaz ens3 de pampero (Ejercicio III), o la MAC del gateway de pampero (recuperatorio 2020). No confundirlas: solo cambia cómo se obtiene la MAC; la descarga, los permisos y la conexión SSH son iguales.

### 1. En tu VM: entrar a pampero

~~~bash
ssh jdileomuntaner@pampero.itba.edu.ar
~~~

Ingresar la contraseña de pampero.

### 2. En pampero: obtener IPv4 de bd1 y generar tráfico

~~~bash
getent ahostsv4 bd1
ping -4 -c 1 -W 2 bd1
~~~

Anotar la IPv4 que devuelve. El ping puede no obtener respuesta ICMP; aun así puede haber generado la resolución ARP.

### 3. En pampero: consultar la MAC de esa IP

En las siguientes líneas, reemplazar IP_BD1 por la IPv4 recién obtenida; no copiar literalmente ese marcador:

~~~bash
ip route get IP_BD1
ip neigh show to IP_BD1
~~~

En la salida de vecinos, copiar los seis pares hexadecimales que aparecen después de lladdr. Ejemplo de formato:

~~~text
IP_BD1 dev eth0 lladdr aa:bb:cc:dd:ee:ff REACHABLE
~~~

La passphrase sería aa:bb:cc:dd:ee:ff **solo si eso es lo observado ahora**. Son 17 caracteres, incluidos los cinco dos puntos, sin espacios.

Si no está disponible ip, usar:

~~~bash
arp -n IP_BD1
~~~

Si bd1 no resuelve, probar el nombre completo indicado por el entorno, por ejemplo bd1.itba.edu.ar. La captura histórica muestra ese sufijo; no garantiza que siga siendo el mismo.

### 4. Volver a tu VM

~~~bash
exit
~~~

### 5. En tu VM: descargar la llave y restringir sus permisos

~~~bash
mkdir -p ~/protos/practica/21.2-2
cd ~/protos/practica/21.2-2
wget --timeout=10 --tries=1 -O llave.pem http://parcial.leak.com.ar/llave.pem
chmod 600 llave.pem
~~~

No sobrescribir una llave propia preexistente: esta carpeta es específica del ejercicio. Si falla la descarga, no continuar suponiendo que el archivo obtenido es una llave válida.

### 6. Conectarse al usuario solicitado

~~~bash
ssh -i ./llave.pem -o IdentitiesOnly=yes -p 2222 pdc@parcial.leak.com.ar
~~~

Verificar la identidad del servidor con el fingerprint de referencia si está disponible. En el primer acceso, SSH pide aceptar su clave de host.

Cuando aparezca Enter passphrase for key, escribir la MAC obtenida en pampero. La passphrase no se ve al escribirla.

### 7. Demostrar la shell

Ya dentro del servidor:

~~~bash
whoami
hostname
date
~~~

whoami debe indicar pdc; hostname identifica el servidor; date demuestra ejecución de un comando. El prompt puede variar. Salir con exit.

**Estado de esta resolución:** receta preparada a partir de las imágenes. No se realizaron conexiones ni se consultó una MAC actual desde aquí. Las IP y MAC del ejemplo histórico no son resultados actuales.

---

## Enunciado interpretado

Hay una llave privada autorizada para entrar como pdc al servidor SSH parcial.leak.com.ar, puerto 2222. Se entrega mediante HTTP y está cifrada con una passphrase que debe obtenerse investigando una dirección MAC.

Se pide mostrar:
1. Todos los pasos para encontrar la passphrase.
2. La descarga de la llave y la conexión.
3. Un comando ejecutado dentro de la shell remota.

La variante principal pide la MAC de bd1 accesible desde pampero. Otra variante pide directamente la MAC de la interfaz ens3 de pampero. En el recuperatorio 2020 se pide la MAC del gateway de pampero; se obtiene de su ruta por defecto y su tabla de vecinos.

## Por qué se entra primero a pampero

ARP relaciona direcciones IPv4 con direcciones de enlace de vecinos del mismo enlace de red. No permite averiguar arbitrariamente la MAC de cualquier servidor de Internet.

La consigna sitúa bd1 en un entorno donde pampero puede consultar ese dato. Desde tu VM podrías ver únicamente vecinos de la red de la VM, como su gateway; no serían la MAC de bd1.

ip route get permite revisar esa condición:
- Si aparece destino dev INTERFAZ sin un salto via, es compatible con un destino directamente conectado.
- Si aparece via GATEWAY, normalmente se resuelve la MAC del gateway para enviar el paquete, no la del host final.
- Si aparece una ruta local, el destino es la propia máquina; consultar su interfaz con ip link.

No tomar la MAC del gateway como passphrase de bd1. Un proxy ARP u otra particularidad de la red también puede requerir interpretar el dato; seguir la topología y aclaraciones de la consigna.

## Cada comando y parámetro

### ssh para entrar a pampero

~~~bash
ssh jdileomuntaner@pampero.itba.edu.ar
~~~

ssh es el cliente de shell segura. El texto antes de @ es el usuario remoto y el posterior es el servidor. Sin -p se usa el puerto 22. La contraseña solicitada aquí es la del usuario de pampero, no la passphrase de la llave descargada.

### Resolución del nombre

~~~bash
getent ahostsv4 bd1
~~~

getent consulta las bases de nombres configuradas por el sistema, como hosts y DNS. ahostsv4 pide direcciones IPv4. Puede repetir la misma IP con etiquetas STREAM, DGRAM y RAW: no son necesariamente hosts distintos.

DNS o la resolución local aportan la IP; no dan la MAC por sí mismos.

### Generar tráfico y leer vecinos

~~~bash
ping -4 -c 1 -W 2 bd1
~~~

- ping envía ICMP Echo Request.
- -4 obliga a usar IPv4, para trabajar con ARP.
- -c 1 envía un solo pedido.
- -W 2 limita a dos segundos la espera de respuesta en la implementación de Linux.
- bd1 es el destino.

El intento de envío puede poblar la tabla de vecinos. Que el ping no responda no implica por sí solo que no exista una entrada ARP.

~~~bash
ip route get IP_BD1
ip neigh show to IP_BD1
~~~

ip administra y consulta la red. route get consulta la ruta que se usaría. neigh show lista vecinos; to limita la búsqueda al destino indicado. Ninguno de estos comandos modifica rutas.

Leer lladdr. REACHABLE indica un vecino confirmado recientemente; STALE indica una entrada existente que requiere reconfirmación al utilizarla, no necesariamente una MAC incorrecta. INCOMPLETE o FAILED sin lladdr no ofrecen una MAC utilizable.

Alternativa antigua:

~~~bash
arp -n IP_BD1
~~~

arp consulta la tabla ARP; -n evita convertir IP en nombres. La dirección MAC suele aparecer en HWaddress. Puede faltar porque arp pertenece a net-tools y no siempre está instalado; ip neigh es la alternativa habitual.

La solución histórica de las imágenes utilizaba ping y después arp filtrado por la IP. Se puede hacer, pero consultar directamente la entrada evita coincidencias accidentales de texto. La MAC histórica 00:16:3e:7b:30:31 es un ejemplo de aquella ejecución, no un dato para reutilizar sin verificar.

### Preparar el directorio y descargar

~~~bash
mkdir -p ~/protos/practica/21.2-2
cd ~/protos/practica/21.2-2
wget --timeout=10 --tries=1 -O llave.pem http://parcial.leak.com.ar/llave.pem
~~~

- mkdir crea carpetas; -p crea los padres necesarios y permite que ya existan.
- ~ se expande a tu home.
- cd cambia el directorio de trabajo.
- wget descarga el recurso HTTP.
- --timeout=10 establece un timeout de diez segundos para operaciones de red; no es un límite global absoluto de toda la ejecución.
- --tries=1 evita reintentos repetidos.
- -O llave.pem elige el archivo de salida; es O mayúscula y puede sobrescribirlo.
- La URL es el recurso de la consigna; HTTP sin puerto explícito utiliza 80.

Alternativa de descarga:

~~~bash
curl -f --connect-timeout 5 --max-time 15 -o llave.pem http://parcial.leak.com.ar/llave.pem
~~~

-f hace fallar curl ante estados HTTP de error; --connect-timeout limita la conexión; --max-time toda la operación; -o, con o minúscula, fija el archivo de salida. Usar una sola de las alternativas.

Si se sospecha una descarga incorrecta:

~~~bash
file llave.pem
head -n 1 llave.pem
~~~

file identifica el tipo aproximado. head -n 1 muestra solo la primera línea; suele ser BEGIN OPENSSH PRIVATE KEY o BEGIN RSA PRIVATE KEY, entre otros formatos. La extensión .pem no garantiza el formato. Una página HTML de error no es una llave.

No publicar ni pegar el contenido de una llave privada en el apunte o en un video. Basta mostrar la descarga y el uso.

### Permisos de la llave

~~~bash
chmod 600 llave.pem
~~~

chmod cambia permisos. 600 significa:
- Propietario: lectura y escritura, 6 = 4 + 2.
- Grupo: sin acceso, 0.
- Otros: sin acceso, 0.

OpenSSH rechaza claves privadas accesibles por terceros. Esto corrige el error UNPROTECTED PRIVATE KEY FILE / permissions are too open.

Para ver el resultado:

~~~bash
ls -l llave.pem
~~~

ls -l muestra detalles; se espera -rw------- y que el propietario sea tu usuario. Es preferible descargar sin sudo para que el archivo sea tuyo.

La captura propone chmod og-wr llave.pem: o son otros, g grupo, - retira permisos, w escritura y r lectura. chmod 600 expresa de forma más directa los permisos finales deseados.

### SSH con la llave

~~~bash
ssh -i ./llave.pem -o IdentitiesOnly=yes -p 2222 pdc@parcial.leak.com.ar
~~~

- -i indica la llave privada que utilizará el cliente; no se pasa la .pub.
- ./llave.pem es el archivo en el directorio actual.
- -o pasa una opción de configuración.
- IdentitiesOnly=yes limita las identidades a las configuradas explícitamente, evitando ofrecer indiscriminadamente otras del agente.
- -p 2222 elige el puerto SSH del enunciado.
- pdc es el usuario destino; no es tu usuario de pampero.
- parcial.leak.com.ar es el servidor destino.

La passphrase descifra la llave privada localmente. No es la contraseña de la cuenta pdc y no se envía como contraseña de usuario al servidor. SSH demuestra posesión de la clave mediante una firma; no envía la llave privada.

Para forzar una demostración de acceso por clave, deshabilitando métodos de contraseña:

~~~bash
ssh -i ./llave.pem -o IdentitiesOnly=yes -o PasswordAuthentication=no -o KbdInteractiveAuthentication=no -p 2222 pdc@parcial.leak.com.ar
~~~

PasswordAuthentication=no desactiva contraseña y KbdInteractiveAuthentication=no la autenticación interactiva de teclado. Estas opciones no eliminan la petición local de passphrase de la llave cifrada.

Si aparece pdc@servidor's password en lugar de Enter passphrase for key, no asumir que corresponde escribir la MAC: podría haberse pasado a otro método porque no se aceptó la clave.

## Variante: la passphrase es la MAC de ens3 de pampero

En lugar de buscar bd1, entrar a pampero y ejecutar:

~~~bash
ip link show dev ens3
~~~

ip link consulta interfaces; show muestra datos; dev ens3 selecciona esa interfaz. Leer los seis pares después de link/ether.

Alternativa exacta en Linux:

~~~bash
cat /sys/class/net/ens3/address
~~~

cat muestra el contenido del archivo que expone la MAC de ens3.

No requiere ping ni ARP: estás consultando una interfaz propia de pampero. Si ens3 no existe:

~~~bash
ip -br link
~~~

-br produce un resumen. Identificar las interfaces disponibles y confirmar qué nombre corresponde según la consigna. No reemplazar ens3 por cualquier interfaz sin explicar la discrepancia.

Los pasos de descarga, chmod y ssh siguen iguales; solo cambia de dónde sale la passphrase.

## Variante: la passphrase es la MAC del gateway de pampero

En el recuperatorio 2020 la passphrase es la MAC del gateway de pampero. Todos estos pasos se hacen **dentro de pampero**, después de entrar con:

~~~bash
ssh jdileomuntaner@pampero.itba.edu.ar
~~~

### 1. Identificar el gateway y la interfaz de salida

~~~bash
ip -4 route show default
~~~

- ip consulta la configuración de red.
- -4 limita la consulta a IPv4, cuya resolución de vecinos usa ARP.
- route selecciona las rutas.
- show las muestra sin modificarlas.
- default filtra las rutas por defecto, usadas cuando no hay una ruta más específica.

Ejemplo ilustrativo, no resultado actual de pampero:

~~~text
default via 192.0.2.1 dev ens3 proto dhcp metric 100
~~~

La IP después de via, aquí 192.0.2.1, es el gateway. El nombre después de dev, aquí ens3, es la interfaz local utilizada para llegar a él. proto dhcp indica el origen de la ruta; metric 100 es su preferencia relativa. **La IP del gateway todavía no es la passphrase:** falta consultar su MAC.

Anotar ambos datos. En los comandos siguientes reemplazar IP_GATEWAY e INTERFAZ por esos valores reales; no copiar literalmente los marcadores ni el ejemplo.

Si aparecen varias rutas por defecto, no elegir una al azar: comparar métricas y la ruta efectiva. Si hay reglas de enrutamiento o no aparece una ruta por defecto en la tabla principal, se puede inspeccionar:

~~~bash
ip -4 route get 1.1.1.1
ip -4 rule show
ip -4 route show table all
~~~

route get consulta qué camino usaría el kernel hacia esa IP de referencia, sin enviar paquetes ni modificar rutas; no hace falta que 1.1.1.1 responda. rule show muestra las reglas que eligen tablas y table all incluye todas las tablas. No usar 1.1.1.1 como IP del gateway: leer el salto después de via y cotejarlo con la topología del enunciado. Si sigue habiendo ambigüedad sobre cuál gateway pide la consigna, explicarla.

### 2. Generar tráfico hacia el gateway

~~~bash
ping -4 -c 1 -W 2 IP_GATEWAY
~~~

- ping envía un ICMP Echo Request al gateway.
- -4 utiliza IPv4.
- -c 1 envía un solo pedido.
- -W 2 espera hasta dos segundos por la respuesta en Linux.
- IP_GATEWAY es la IP obtenida en el paso anterior.

El intento de comunicación puede generar ARP y poblar la tabla de vecinos. Si el gateway bloquea ICMP, el ping puede fallar y aun así haberse aprendido su MAC.

### 3. Consultar la MAC del gateway en el enlace correcto

~~~bash
ip neigh show to IP_GATEWAY dev INTERFAZ
~~~

- neigh selecciona la tabla de vecinos.
- show muestra las entradas.
- to IP_GATEWAY filtra por la IP del gateway.
- dev INTERFAZ limita la búsqueda a su interfaz de salida, importante si hay varios enlaces.

Ejemplo ilustrativo:

~~~text
192.0.2.1 dev ens3 lladdr aa:bb:cc:dd:ee:ff REACHABLE
~~~

Copiar la MAC después de lladdr, con los dos puntos y el formato pedido: xx:xx:xx:xx:xx:xx, 17 caracteres. No copiar la IP ni la MAC de la interfaz propia de pampero. Una entrada con lladdr en estado STALE puede ser utilizable; INCOMPLETE o FAILED sin lladdr no da una passphrase.

Alternativa si está instalado net-tools:

~~~bash
arp -n IP_GATEWAY
~~~

arp consulta ARP; -n conserva direcciones numéricas. Leer HWaddress y verificar que la interfaz corresponda a la ruta elegida.

### 4. Usar esa MAC y demostrar el acceso

Volver con exit a tu VM y continuar la receta desde la descarga de llave.pem: wget, chmod 600 y ssh -i con el usuario y puerto del enunciado de esa edición. Escribir la MAC del gateway cuando se solicite la passphrase; dentro ejecutar whoami y date.

**Diferencia con bd1:** cuando se pide la MAC de bd1, una ruta via GATEWAY no autoriza a usar la MAC del gateway como si fuera la de bd1. En esta variante, en cambio, el gateway es exactamente el vecino cuya MAC se necesita. Tampoco es lo mismo que la MAC propia de ens3: ens3 es la interfaz de pampero; el gateway es el equipo vecino.

**Qué mostrar en el video:**
1. La shell de pampero y la ruta por defecto, señalando IP del gateway e interfaz.
2. El intento de ping y la consulta ARP/vecinos que muestra la MAC del gateway.
3. La descarga de la llave y sus permisos.
4. La conexión SSH con esa passphrase y la ejecución de whoami y date.

## Variantes: qué cambia y qué línea tocar

| Dato o variante | Cambio exacto |
| --- | --- |
| Otro usuario de pampero | ssh OTRO@pampero.itba.edu.ar |
| MAC de otro host vecino | getent ahostsv4 OTRO; ping -4 -c 1 -W 2 OTRO; consultar su IP con ip neigh |
| MAC de otra interfaz propia | ip link show dev NOMBRE_INTERFAZ |
| MAC del gateway de pampero (recuperatorio 2020) | En pampero: ip -4 route show default; ping -4 -c 1 -W 2 IP_GATEWAY; ip neigh show to IP_GATEWAY dev INTERFAZ. Usar la MAC después de lladdr. |
| Otro usuario destino | Cambiar pdc@ por USUARIO@ en ssh |
| Otro puerto SSH | Cambiar -p 2222 por -p PUERTO |
| Otra URL de descarga | Cambiar la URL de wget; mantener un nombre local coherente con -i |
| Otro nombre local de llave | wget -O otra.pem URL; chmod 600 otra.pem; ssh -i ./otra.pem ... |
| Archivo de llave ya entregado | Omitir descarga; corregir permisos y usar -i con su ruta |
| Destino solo accesible a través de pampero | ssh -J jdileomuntaner@pampero.itba.edu.ar -i ./llave.pem -o IdentitiesOnly=yes -p 2222 pdc@parcial.leak.com.ar |
| Depurar conexión | Agregar -v al ssh; -vv o -vvv aumentan el detalle |
| Probar llave cifrada sin conectarse | ssh-keygen -y -f ./llave.pem |
| MAC en mayúsculas | Usar el formato exacto requerido; el enunciado especifica hexadecimales en minúsculas. La passphrase distingue mayúsculas. |

-J agrega un salto SSH; conserva la llave privada en tu VM en lugar de copiarla a pampero. Sin puerto en el salto, pampero usa 22; -p 2222 se aplica al destino final. Las resoluciones y conectividad deben ser posibles desde el salto.

ssh-keygen -y lee la llave privada y muestra su pública; -f selecciona el archivo. Si la descifra con la MAC, la passphrase es válida, aunque eso todavía no demuestra autorización en el servidor.

## Si algo falla

| Síntoma | Causa posible | Arreglo |
| --- | --- | --- |
| bd1 no resuelve | Nombre corto sin dominio de búsqueda o host fuera del entorno | Consultar el FQDN del ejercicio desde pampero; no adivinar IP de una captura antigua |
| Ping no responde | ICMP filtrado, host apagado o ruta incorrecta | Revisar ip route get e ip neigh; ping fallido no invalida una entrada existente |
| Vecino INCOMPLETE / FAILED | No hubo resolución de enlace | Revisar IP, enlace y disponibilidad; no inventar MAC |
| La ruta muestra via | bd1 no está directamente conectado | No confundir MAC del gateway con bd1; revisar topología del entorno |
| ens3 no existe | Nombre de interfaz distinto | ip -br link y cotejar con el enunciado |
| No aparece gateway o hay varias rutas por defecto | Otra tabla, reglas de enrutamiento o múltiples salidas | Revisar ip -4 route get 1.1.1.1, ip -4 rule show e ip -4 route show table all desde pampero; identificar el gateway pedido sin adivinar |
| Se usó la MAC propia de pampero en la variante del gateway | Se confundió ip link con la tabla de vecinos | Obtener IP e interfaz de la ruta y consultar ip neigh para el gateway, no link/ether de la interfaz local |
| wget devuelve error o baja HTML | HTTP no disponible, URL incorrecta o página de error | Revisar resultado y tipo de archivo; no usarlo como llave |
| Connection refused al 2222 | No hay listener o rechazo activo | Confirmar host/puerto; usar práctica local si no está habilitado |
| Timeout al 2222 | Ruta, firewall o servidor inaccesible | Probar acceso desde la red prevista; considerar -J si corresponde |
| UNPROTECTED PRIVATE KEY FILE | Archivo legible por otros | chmod 600 llave.pem; revisar propietario |
| Incorrect passphrase | MAC equivocada, formato incorrecto o llave distinta | Verificar host/interfaz, minúsculas y dos puntos; no agregar espacios |
| Permission denied (publickey) | Usuario, llave o autorización incorrectos | Confirmar pdc, llave descargada y puerto; revisar ssh -v |
| Pide contraseña de pdc | La llave no fue aceptada o no se usó | Revisar -i y usar opciones que desactiven fallback por contraseña |
| Host key verification failed | Clave de host no confirmada o cambió | Verificar fingerprint; no borrar known_hosts ni desactivar controles a ciegas |
| No pide passphrase | La llave puede estar ya cargada en el agente | No implica fallo; para demostrar carga explícita revisar el agente y la configuración |

## Práctica local opcional: solo si el entorno del parcial no existe

**Esto simula la autenticación con llave cifrada y descarga HTTP. No obtiene una MAC real de bd1 ni conecta al usuario pdc del parcial.** Se usa tu usuario local, un sshd dedicado y puertos solo en loopback. No modificar el sshd principal.

Requiere openssh-server y Python instalados. Los comandos siguientes se ejecutan en tu VM, no se ejecutaron al generar este documento.

### A. Preparar archivos aislados

~~~bash
mkdir -p ~/protos/practica/21.2-2-local/public
chmod 700 ~/protos/practica/21.2-2-local
cd ~/protos/practica/21.2-2-local
ip -br link
~~~

Elegir una interfaz Ethernet disponible y leer su MAC, por ejemplo:

~~~bash
cat /sys/class/net/enp0s3/address
~~~

enp0s3 es un ejemplo habitual de VM: usar el nombre real de la lista. Esa MAC será la passphrase de práctica. No usar lo, cuya dirección no representa una Ethernet normal.

### B. Generar la llave de usuario cifrada y una clave de host

~~~bash
ssh-keygen -t ed25519 -f public/llave.pem -C "practica-21.2-2"
~~~

-t elige el algoritmo; -f el archivo; -C es un comentario. Ante Enter passphrase escribir la MAC de práctica y repetirla. No dejarla vacía. Esto produce la privada y la pública; que el archivo se llame .pem no cambia el formato de OpenSSH.

~~~bash
cp public/llave.pem.pub authorized_keys
chmod 600 authorized_keys public/llave.pem
ssh-keygen -t ed25519 -f host_key -N ''
~~~

cp copia la pública al archivo de autorizaciones del laboratorio. La clave de host identifica este servidor, es distinta de la clave de usuario. -N '' deja sin passphrase únicamente esa clave de host de práctica para que sshd pueda arrancar.

Si los archivos ya existen, no sobrescribirlos sin revisar: usar una carpeta nueva de práctica.

### C. Crear un sshd dedicado

~~~bash
cat > sshd_config <<EOF
Port 2222
ListenAddress 127.0.0.1
HostKey $PWD/host_key
PidFile $PWD/sshd.pid
AuthorizedKeysFile $PWD/authorized_keys
PubkeyAuthentication yes
PasswordAuthentication no
KbdInteractiveAuthentication no
UsePAM no
AllowUsers $(id -un)
StrictModes yes
EOF
~~~

El bloque crea un archivo nuevo de configuración. > escribe reemplazando ese archivo; <<EOF entrega las líneas como entrada; $PWD se sustituye por la carpeta actual y $(id -un) por tu usuario local. No es la configuración del servidor real.

Port y ListenAddress eligen puerto y loopback; HostKey apunta a la clave del servidor; PidFile registra su PID; AuthorizedKeysFile selecciona la pública autorizada; las opciones de autenticación permiten solo clave; AllowUsers restringe al usuario actual; StrictModes conserva las comprobaciones de propiedad/permisos.

Verificar que 2222 esté libre:

~~~bash
sudo ss -ltnp 'sport = :2222'
~~~

Si no hay listener, validar y arrancar:

~~~bash
sudo /usr/sbin/sshd -t -f "$PWD/sshd_config"
sudo mkdir -p /run/sshd
sudo /usr/sbin/sshd -D -e -f "$PWD/sshd_config"
~~~

-t valida; -f elige este archivo; -D mantiene el proceso en primer plano; -e muestra logs en stderr. /run/sshd puede ser necesario para separación de privilegios. Mantener esta terminal abierta. No se necesita detener el sshd principal si usa otro puerto.

### D. Servir la llave por HTTP local

En otra terminal:

~~~bash
cd ~/protos/practica/21.2-2-local
python3 -m http.server 8021 --bind 127.0.0.1 --directory public
~~~

-m ejecuta el módulo HTTP; 8021 es el puerto; --bind limita al loopback; --directory expone solo la carpeta public del laboratorio. La llave es privada, pero se ofrece intencionalmente en esta simulación de la consigna, accesible solo desde la máquina. No exponer esta carpeta a la red.

### E. Descargar y entrar

En una tercera terminal:

~~~bash
mkdir -p ~/protos/practica/21.2-2-local/cliente
cd ~/protos/practica/21.2-2-local/cliente
wget -O llave.pem http://127.0.0.1:8021/llave.pem
chmod 600 llave.pem
ssh -i ./llave.pem -o IdentitiesOnly=yes -p 2222 jerodileo@127.0.0.1
~~~

Usar tu usuario local real si no es jerodileo. Ingresar la MAC de práctica cuando pida la passphrase. Dentro, ejecutar whoami, hostname y date.

La misma máquina hace aquí de cliente y servidor; el usuario remoto es local y no pdc. El ejercicio real usa los datos de la receta inicial.

### F. Limpieza del laboratorio

Salir de la shell con exit. Ctrl+C en las terminales del sshd y del HTTP termina esos procesos. No hace falta modificar ni borrar las claves habituales de ~/.ssh ni usuarios del sistema.

Conservar la carpeta permite repetir la práctica; contiene una llave privada de laboratorio, no una llave personal.

## Qué mostrar al justificar el parcial

1. Identificar la máquina donde se busca la MAC.
2. Mostrar resolución/ping y tabla de vecinos, o ip link para la variante de interfaz propia.
3. Mostrar la descarga y chmod 600.
4. Conectar al usuario y puerto indicados.
5. Ejecutar whoami y date dentro.

**Frase de cierre:** “Obtuve la MAC indicada desde pampero, la usé para descifrar la llave privada y abrí una shell del usuario pdc por SSH en el puerto 2222, donde ejecuté comandos para demostrar el acceso.”

## Guardar este apunte en la VM

El archivo se entrega descargable: no se escribió automáticamente en la VM del usuario. Una vez descargado:

~~~bash
mkdir -p ~/protos/soluciones
cp ~/Downloads/21.2-2.md ~/protos/soluciones/21.2-2.md
~~~

Si el navegador guarda en Descargas, ajustar ese nombre de carpeta.

## Referencias

- Consigna e imágenes de resolución histórica adjuntadas por el usuario.
- OpenSSH: https://man.openbsd.org/ssh
- Vecinos y ARP: https://man7.org/linux/man-pages/man8/ip-neighbour.8.html
- Rutas: https://man7.org/linux/man-pages/man8/ip-route.8.html

