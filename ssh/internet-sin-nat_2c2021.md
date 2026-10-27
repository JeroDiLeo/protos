# 2C 2021 — Ejercicio IV: dar acceso HTTP/HTTPS a un host sin NAT mediante SSH

## ⭐ RECETA PARA EL PARCIAL

### Versión mínima (leer primero)

Si tu cliente SSH es OpenSSH 7.6 o más nuevo (`ssh -V`; Ubuntu actual trae 9.x), alcanza con **una sola conexión**, sin sshd local ni `-D`:

~~~bash
# En tu VM (cambiar llave, puerto, usuario y host por los del enunciado)
chmod 600 llave.pem
ssh -i llave.pem -p 2222 -R 63051 pdc@parcial.leak.com.ar

# Ya dentro del host sin NAT
curl --connect-timeout 5 http://api.ipify.org                      # falla: no tiene salida
export ALL_PROXY=socks5h://127.0.0.1:63051
curl http://api.ipify.org                                           # IP pública de TU VM
curl -I https://campus.itba.edu.ar/                                 # HTTPS también funciona
~~~

- `-R 63051` (solo un puerto, sin destino): abre en el host remoto un **SOCKS** en `127.0.0.1:63051`, y cada conexión que entra ahí la abre **tu VM** hacia el destino que pida curl.
- `socks5h`: la **h** hace que el nombre lo resuelva tu VM. El host sin NAT tampoco puede consultar DNS externo, así que sin la `h` falla.
- Si `curl` sigue sin usar el túnel: `unset http_proxy https_proxy all_proxy no_proxy` y repetir, o usar `curl -x socks5h://127.0.0.1:63051 URL`.

Si `-R` sin destino da error (cliente viejo) o preferís mostrar el mecanismo de los apuntes, usá la **versión clásica** de abajo (`-D` en tu VM + `-R` fijo hacia ese SOCKS). Las dos usan túneles, así que valen el puntaje completo.

**Frase para el video:** "El host no tiene NAT, así que no sale a Internet. Con `ssh -R` publiqué en su loopback un proxy SOCKS que sale por mi VM; con `ALL_PROXY=socks5h://` curl le pasa cada pedido al túnel, y por eso api.ipify.org muestra la IP de mi máquina."

### Versión clásica (paso a paso)

**Datos de la imagen y del ejercicio previo:** host parcial.leak.com.ar, usuario pdc, SSH en el puerto 2222, identidad llave.pem obtenida en el ejercicio de la llave. Se exige usar curl hacia http://api.ipify.org, https://campus.itba.edu.ar/ y cualquier otro sitio, desde el host remoto que tiene IP privada y cuyo gateway no hace NAT.

**Decisión:** solución clásica de tus apuntes S4: un SOCKS en tu VM con -D y un túnel inverso -R hacia ese SOCKS. El puerto remoto elegido es **63051**, tu legajo; esta elección evita colisiones, pero la imagen no exige expresamente usar el legajo. El puerto local del SOCKS será 9090.

No confundir los cuatro puertos:
- 22: servidor SSH local, para crear el SOCKS clásico.
- 9090: SOCKS en tu VM con salida.
- 2222: SSH del servidor del parcial.
- 63051: puerto de acceso al SOCKS en el servidor sin salida.

### 0. En tu VM: verificar que ella sí tiene salida

~~~bash
curl --noproxy '*' --connect-timeout 5 --max-time 10 http://api.ipify.org
~~~

Se espera una IP pública; el valor depende de tu conexión. No se fijó ni se obtuvo una IP real del parcial al generar este apunte.

### 1. En tu VM: disponer de un servidor SSH local

~~~bash
systemctl status ssh
sudo systemctl start ssh
~~~

Solo hace falta iniciarlo si no está corriendo. El -D clásico se conecta a este servidor; no se conecta todavía al host sin Internet. Si no está instalado, instalar openssh-server en tu VM.

### 2. En tu VM, terminal A: abrir SOCKS con salida por tu VM

~~~bash
ssh -N -o ExitOnForwardFailure=yes -D 127.0.0.1:9090 jerodileo@127.0.0.1
~~~

Autenticarse con tu usuario **local**. Dejar la terminal abierta; que no aparezca un prompt nuevo es normal por -N.

### 3. En tu VM, terminal B: llevar el SOCKS al remoto y abrir su shell

~~~bash
cd ~/protos/practica/21.2-2
chmod 600 llave.pem
ssh -i ./llave.pem -o IdentitiesOnly=yes -o ExitOnForwardFailure=yes -p 2222 -R 127.0.0.1:63051:127.0.0.1:9090 pdc@parcial.leak.com.ar
~~~

La ruta de llave.pem es la que propusimos al resolver el ejercicio anterior; cambiarla si guardaste la llave en otro lado. Ingresar la passphrase de ese ejercicio. **No agregar -N aquí:** queremos usar la shell remota para las pruebas.

### 4. Dentro de parcial.leak.com.ar: demostrar que el acceso directo falla

~~~bash
hostname
whoami
curl --noproxy '*' --connect-timeout 5 --max-time 10 http://api.ipify.org
~~~

Se espera que el curl directo falle en el escenario del enunciado. El texto concreto puede ser un error DNS, de ruta o timeout; no inventar uno determinado. Si tiene salida directa, el escenario no reproduce la restricción y debe aclararse.

### 5. En esa misma shell remota: configurar curl para usar el túnel

~~~bash
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY no_proxy NO_PROXY
export ALL_PROXY=socks5h://127.0.0.1:63051
~~~

Se limpian solo las variables de esta shell para que no prevalezcan proxies específicos u otras exclusiones. No se edita la configuración permanente del sistema.

### 6. En el remoto: demostrar HTTP, HTTPS y un destino adicional

~~~bash
curl http://api.ipify.org
curl https://campus.itba.edu.ar/
curl https://example.com/
~~~

La primera debe mostrar la IP pública de salida de tu VM; las otras deben obtener una respuesta HTTP, conservando validación TLS en HTTPS. Campus puede responder con una redirección: eso demuestra conectividad, no necesariamente una sesión autenticada. Para seguir redirecciones usar curl -L URL; para mostrar status/TLS usar las pruebas de diagnóstico de abajo.

Se puede usar cualquier host/puerto HTTP(S) que la VM de salida alcance: no hay un destino fijo en el túnel SOCKS.

**Alternativa de una sola conexión, cliente OpenSSH moderno:**

~~~bash
ssh -i ./llave.pem -o IdentitiesOnly=yes -o ExitOnForwardFailure=yes -p 2222 -R 127.0.0.1:63051 pdc@parcial.leak.com.ar
~~~

El -R sin host:puerto de destino crea un SOCKS remoto que abre conexiones desde tu VM. Mantener esta conexión abierta y repetir los pasos 4–6. No necesita -D ni sshd local. Es una alternativa a la clásica, no se ejecutan ambas a la vez en el mismo puerto.

---

## Enunciado de la imagen

El host parcial.leak.com.ar, al cual se accedió en el ejercicio anterior, tiene una única interfaz de red con una dirección IP privada y su gateway no realiza NAT. Hay que lograr que desde su línea de comandos se acceda a cualquier sitio de Internet utilizando curl; los ejemplos son http://api.ipify.org y https://campus.itba.edu.ar/.

El ejercicio depende del acceso SSH previo. Una solución sin túneles obtiene la mitad del puntaje. Por eso se prioriza un túnel SSH y no simplemente configurar un proxy externo ajeno al túnel.

## Qué se puede afirmar de esta preparación

Se revisaron tus páginas de Notion “SSH – llave con passphrase, y túneles -L / -R / -D” y “P-SSH – 5 ejercicios”, en particular S4 y S5. Se corrigió el puerto SSH de ejemplos genéricos: en esta receta es **2222**, el de la consigna previa, no el 9090 que aparece en otras versiones de los apuntes.

En este entorno:
- OpenSSH local de comprobación: 9.6p1.
- Se comprobó con ssh -G que el cliente acepta las sintaxis de -D, -R fijo y -R dinámico; esto valida interpretación de opciones, no conectividad.
- El script de laboratorio pasa bash -n.
- Intentar crear un namespace con unshare -n true devolvió Operation not permitted. Por tanto **el laboratorio de namespaces no fue ejecutado de extremo a extremo aquí**.
- No se afirma haber conectado al host real ni haber obtenido HTTP/HTTPS desde él.

El laboratorio y sus resultados esperados están preparados para ejecutarse en tu VM Ubuntu, donde tenés sudo. El apunte no muestra salidas simuladas como si fueran observaciones reales.

## Idea: resolver a nivel aplicación sin cambiar el gateway

Una IP privada no recibe normalmente respuestas desde Internet público si no existe NAT ni enrutamiento específico de retorno. Sin embargo, tu VM puede tener una ruta interna o de laboratorio al servidor SSH. Poder abrir SSH desde tu VM al host **no implica** que ese host tenga salida pública por sí solo.

La solución hace que curl hable con un proxy accesible en su propio loopback. SSH lleva ese flujo a una máquina con salida, y esa máquina abre las conexiones a Internet.

No habilitamos NAT, ip_forward ni una VPN de capa 3. Solo las aplicaciones configuradas para usar SOCKS aprovechan el túnel; ping o cualquier otro proceso no adquiere salida automáticamente. Estos túneles atienden TCP, suficiente para HTTP y HTTPS convencional; no son una salida UDP/ICMP general.

## Diagrama de recorrido

Diagrama en texto estructurado; en la versión HTML se muestra también como gráfico:

~~~mermaid
flowchart TB
    A["curl en parcial.leak.com.ar"]
    B["Loopback remoto:63051"]
    C["Tu VM · SOCKS 127.0.0.1:9090"]
    D["sshd de tu VM · localhost:22"]
    E["Sitio HTTP o HTTPS elegido"]
    A -->|"SOCKS5: nombre y puerto"| B
    B -->|"Túnel SSH -R ya establecido"| C
    C -->|"Túnel dinámico -D hacia localhost"| D
    D -->|"Resuelve DNS y abre TCP"| E
~~~

Lectura del recorrido: **curl remoto → 63051 remoto → SSH inverso → SOCKS 9090 de tu VM → SSH local → conexión del sshd local al sitio**. Las respuestas vuelven por el mismo encadenamiento.

La sesión -R se inicia desde tu VM hacia el host, aunque las nuevas conexiones a destinos salgan del curl remoto y atraviesen ese canal en sentido inverso.

## Paso a paso explicado: cada comando y parámetro

### Verificar la salida de la máquina que dará Internet

~~~bash
curl --noproxy '*' --connect-timeout 5 --max-time 10 http://api.ipify.org
~~~

- curl es el cliente HTTP.
- --noproxy '*' obliga a omitir proxies para todos los destinos; las comillas impiden que la shell expanda el asterisco a nombres de archivos.
- --connect-timeout 5 limita la fase de conexión a cinco segundos.
- --max-time 10 limita la operación entera a diez segundos.
- api.ipify.org devuelve la IP pública que ve como origen.

Si esa VM depende de un proxy corporativo para salir y el curl directo falla, no se puede asumir que los sockets TCP del sshd saldrán libremente. Elegir una máquina SSH con salida real o un proxy alcanzable que el entorno permita. No confundir una variable HTTP_PROXY de la shell con conectividad IP directa del sshd.

### Revisar y arrancar sshd local

~~~bash
systemctl status ssh
sudo systemctl start ssh
~~~

systemctl administra servicios; status consulta; start inicia si está detenido; ssh es la unidad habitual de OpenSSH Server en Ubuntu; sudo da privilegios. El cliente se llama ssh y el proceso servidor sshd.

No hace falta detener un servicio ya activo solo para este ejercicio. Si la demostración exige mostrar el arranque de un servidor nuevo, usar el sshd dedicado del laboratorio, sin cortar otros accesos existentes.

Si falta el servidor:

~~~bash
sudo apt install openssh-server
~~~

apt es el gestor de paquetes; install instala el paquete indicado. Esto se ejecuta en la VM de práctica; el host real del parcial ya tiene su SSH.

### Crear SOCKS con -D

~~~bash
ssh -N -o ExitOnForwardFailure=yes -D 127.0.0.1:9090 jerodileo@127.0.0.1
~~~

- ssh abre la conexión cifrada al servidor indicado.
- -N no ejecuta comandos ni abre shell: mantiene los forwards.
- -o introduce una opción de configuración.
- ExitOnForwardFailure=yes hace que SSH falle si no logra establecer los listeners solicitados. No garantiza que todos los sitios futuros sean alcanzables.
- -D abre un proxy SOCKS dinámico en la máquina donde se ejecuta el cliente.
- 127.0.0.1:9090 limita ese listener al loopback local y puerto 9090.
- jerodileo es tu usuario local; @ separa usuario y servidor.
- 127.0.0.1 al final es el servidor SSH al que se conecta: **tu propia VM**, puerto 22 implícito.

El SOCKS negocia el host y puerto de cada petición. Es el extremo servidor de esa sesión SSH el que abre las conexiones finales; como el servidor es tu VM, la salida también es tu VM.

**Por qué no apuntar este -D al host sin Internet:** entonces se intentaría abrir cada destino desde ese mismo host sin salida y no resolvería el problema.

### Extender el SOCKS hacia el remoto con -R

~~~bash
ssh -i ./llave.pem -o IdentitiesOnly=yes -o ExitOnForwardFailure=yes -p 2222 -R 127.0.0.1:63051:127.0.0.1:9090 pdc@parcial.leak.com.ar
~~~

- -i elige la llave privada. La passphrase la descifra localmente.
- ./ indica el directorio actual.
- IdentitiesOnly=yes limita las identidades utilizadas a las configuradas explícitamente, sin ofrecer todas las llaves del agente.
- -p 2222 es el puerto del servidor SSH **del parcial**.
- -R crea el listener en el lado servidor de esta conexión, es decir, en parcial.leak.com.ar.
- Primer 127.0.0.1: loopback **del remoto**, donde se admite la conexión de curl.
- 63051: puerto de escucha **remoto**.
- Segundo 127.0.0.1: destino abierto desde el lado **cliente SSH**, tu VM.
- 9090: puerto del SOCKS que ya existe en tu VM.
- pdc@parcial.leak.com.ar: cuenta y servidor del ejercicio.

Por defecto suele bastar con la escucha en loopback; la hacemos explícita. No se necesita GatewayPorts yes para permitir conexiones desde el propio host remoto al loopback. El servidor debe permitir remote forwarding; políticas como AllowTcpForwarding, DisableForwarding, PermitListen o restricciones de la llave pueden bloquearlo.

El puerto remoto y el local podrían ser distintos; aquí lo son para que se vea la función de cada uno. Tu legajo 63051 es válido: los puertos TCP van de 1 a 65535 y estos puertos altos no requieren privilegios de root para escuchar.

### Probar que seguimos en el host solicitado

~~~bash
hostname
whoami
~~~

hostname muestra el nombre del equipo de la shell; whoami el usuario efectivo. Debe quedar claro que los curl finales se ejecutan **en pdc del remoto**, no en tu terminal local.

### Elegir proxy para curl y delegar DNS

~~~bash
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY no_proxy NO_PROXY
export ALL_PROXY=socks5h://127.0.0.1:63051
~~~

unset elimina esas variables de la shell actual. export hace que la variable se herede por los comandos hijos, incluido curl.

- ALL_PROXY es el proxy de reserva de curl cuando no hay uno específico del protocolo.
- http_proxy y https_proxy podrían prevalecer; all_proxy minúscula también puede tener prioridad frente a ALL_PROXY.
- no_proxy/NO_PROXY puede excluir destinos e impedir que usen el túnel.
- socks5h:// selecciona SOCKS5 con resolución del nombre en el extremo del proxy.
- La h es crucial si el host no puede consultar DNS externo.
- 127.0.0.1:63051 es accesible para curl **en el remoto**, gracias a -R.

Con socks5:// curl intenta resolver localmente en el host sin salida; puede fallar antes de usar el túnel. Con socks5h:// envía el nombre: la resolución y conexión se completan desde la VM de salida, a través de SOCKS/SSH.

Para una única ejecución, después de limpiar posibles variables conflictivas:

~~~bash
ALL_PROXY=socks5h://127.0.0.1:63051 curl http://api.ipify.org
~~~

Asignar antes del comando solo cambia el entorno de esa ejecución. export sirve para que los siguientes curl funcionen sin repetir la variable.

### Demostrar HTTPS sin desactivar TLS

~~~bash
curl https://campus.itba.edu.ar/
curl -v --connect-timeout 5 --max-time 20 https://campus.itba.edu.ar/
~~~

El primero es la petición simple. -v del segundo muestra diagnóstico de SOCKS, TCP y TLS, además de headers; no cambia la URL solicitada.

curl valida el certificado del sitio y mantiene TLS entre el curl remoto y el sitio final. El SOCKS transporta ese flujo; no necesita terminar ni descifrar TLS. No hace falta -k: esa opción desactivaría la validación del certificado y no arregla un problema de túnel.

Si el sitio responde una redirección:

~~~bash
curl -L https://campus.itba.edu.ar/
~~~

-L sigue Location. Esta consigna no prohíbe seguir redirecciones; la obligación es poder alcanzar sitios arbitrarios, no autenticarte en Campus ni mostrar siempre un status 200.

Para ver solo cabeceras:

~~~bash
curl -I https://campus.itba.edu.ar/
~~~

-I solicita HEAD; algunos sitios lo tratan distinto de GET, así que un error solo en HEAD no prueba un fallo de conectividad. Para observar GET con cabeceras usar -i en lugar de -I.

## Forma corta: remote dynamic forwarding

En clientes OpenSSH que soporten remote dynamic forwarding (introducido en OpenSSH 7.6), se puede sustituir las dos conexiones por:

~~~bash
ssh -i ./llave.pem -o IdentitiesOnly=yes -o ExitOnForwardFailure=yes -p 2222 -R 127.0.0.1:63051 pdc@parcial.leak.com.ar
~~~

-R lleva **solo dirección de escucha y puerto**, sin destino fijo. El cliente SSH interpreta las solicitudes SOCKS recibidas del remoto y abre las conexiones desde tu VM. No se necesita sshd local ni -D; el servidor remoto sigue necesitando permitir el forward solicitado.

Es especialmente útil si no querés instalar/iniciar un sshd en tu máquina. Repetir la configuración ALL_PROXY y los curl dentro de la shell. No agregar un supuesto :127.0.0.1:9090 a esta forma si no existe ese SOCKS: la convertirías en un forward fijo.

Para consultar la versión del cliente:

~~~bash
ssh -V
~~~

-V mayúscula muestra versión; -v minúscula es diagnóstico de una conexión.

## Por qué es -R y no solamente -L o -D

| Mecanismo | Dónde escucha | Quién abre el destino | Aplicación |
| --- | --- | --- | --- |
| -L local:host:puerto | Lado cliente SSH | Servidor SSH | Tu VM accede a un servicio que ve el remoto |
| -D local | Lado cliente SSH, SOCKS | Servidor SSH | Tu VM navega saliendo por ese servidor |
| -R remoto:host:puerto | Lado servidor SSH | Cliente SSH | El remoto accede a un servicio que ve tu VM |
| -R remoto sin destino | Lado servidor SSH, SOCKS | Cliente SSH | El remoto elige destinos y navega saliendo por tu VM |

Aquí el cliente de la aplicación es curl en el remoto; por eso hay que darle allí un punto de entrada al servicio de salida que tenemos del lado local.

Un -L a api.ipify.org:80 solo resolvería ese servicio; no cubre HTTPS y sitios arbitrarios. Un SOCKS decide el destino por conexión.

---

## PRÁCTICA LOCAL: namespace sin Internet y VM con salida

Se entrega **practica-21.2-4.sh** junto a este apunte y su código completo al final. La práctica crea:
- Una interfaz veth de tu VM: 192.0.2.1/30.
- Namespace p214-sinred, con loopback y una interfaz de datos p214-remoto: 192.0.2.2/30.
- Ninguna ruta por defecto en el namespace: solo puede comunicarse con tu VM.
- Un sshd de práctica dentro del namespace en 192.0.2.2:2222.
- Otro sshd de práctica en 127.0.0.1:2299, para crear el SOCKS sin tocar el sshd principal.
- Llaves y archivos en ~/protos/practica/21.2-4, sin crear usuarios ni modificar ~/.ssh/authorized_keys.

La cuenta remota de práctica es tu usuario local jerodileo, no pdc. Ambas shells comparten filesystem por ser un namespace de red, pero tienen pilas de red separadas. hostname será el mismo: para distinguirlas usar ip -br addr e ip route.

**Diferencia con el enunciado:** el remoto de práctica no tiene default route; el real tiene gateway sin NAT. Son causas distintas de falta de salida, pero ambas conservan acceso al SSH interno y requieren el mismo mecanismo -R + SOCKS para curl. El laboratorio no pretende simular la topología institucional exacta.

### P0. Comprobar prerrequisitos

En tu VM, como jerodileo:

~~~bash
command -v ip ssh curl
test -x /usr/sbin/sshd
~~~

command -v localiza ejecutables; test -x comprueba que sshd sea ejecutable. Si falta:

~~~bash
sudo apt install openssh-server iproute2 curl
~~~

iproute2 aporta ip y ss. El script usa bash, ssh-keygen, awk y grep, habituales en Ubuntu. No ejecutarlo con sudo bash: el script necesita conservar tu usuario y solicita sudo solo para las operaciones de red/servidor.

### P1. Preparar red y servidores dedicados

Descargar el script, por ejemplo a Downloads, y ejecutar:

~~~bash
bash ~/Downloads/practica-21.2-4.sh up
~~~

bash ejecuta el script; up selecciona preparación. El script comprueba nombres, puertos y subred antes de crear recursos. Si falla durante la preparación, intenta retirar solo sus propios recursos.

Resultados esperados, **no observados aquí**:

~~~text
VM: 192.0.2.1/30; remoto: 192.0.2.2/30, SSH 2222.
Usuario de práctica: jerodileo (no se crea pdc).
SSH local para -D: 127.0.0.1:2299.
~~~

También muestra los fingerprints de los dos servidores: compararlos al aceptar el primer acceso. No se desactiva la verificación de claves de host.

### P2. Verificar aislamiento y ausencia de salida directa

~~~bash
bash ~/Downloads/practica-21.2-4.sh status
sudo ip netns exec p214-sinred curl --noproxy '*' --connect-timeout 3 --max-time 5 http://1.1.1.1/
~~~

status muestra interfaces, rutas y listeners. sudo ip netns exec NAMESPACE COMANDO ejecuta ese comando en la red aislada. El curl usa una IP para evitar que un error DNS oculte la demostración de que no hay ruta pública.

Se espera ver 192.0.2.2/30 y solo una ruta conectada, sin default. El curl directo a 1.1.1.1 debe fallar. No hace falta que ese destino atienda HTTP: aquí se muestra que no se puede establecer conexión directa desde el namespace.

### P3. Terminal A de tu VM: levantar SOCKS

~~~bash
ssh -F /dev/null -i ~/protos/practica/21.2-4/client_key -o IdentitiesOnly=yes -o ExitOnForwardFailure=yes -p 2299 -N -D 127.0.0.1:9090 jerodileo@127.0.0.1
~~~

-F /dev/null evita que una configuración de cliente previa cambie este laboratorio; -i usa su llave aislada; -p 2299 elige su sshd dedicado. Los demás parámetros ya se explicaron. Aceptar solo la huella generada por el script.

La llave de laboratorio no tiene passphrase para concentrarnos en túneles; no es la llave del parcial.

### P4. Terminal B: abrir sesión al remoto con el -R

~~~bash
ssh -F /dev/null -i ~/protos/practica/21.2-4/client_key -o IdentitiesOnly=yes -o ExitOnForwardFailure=yes -p 2222 -R 127.0.0.1:63051:127.0.0.1:9090 jerodileo@192.0.2.2
~~~

El puerto SSH coincide con la consigna; la IP privada es solo de práctica. Al entrar:

~~~bash
ip -br addr
ip route
curl --noproxy '*' --connect-timeout 3 --max-time 5 http://1.1.1.1/
~~~

ip -br addr resume interfaces y direcciones; ip route muestra rutas. Debe verse el namespace aislado y el fallo de salida directa. No confiar solo en el prompt o hostname.

### P5. En esa sesión: activar el proxy y probar sitios distintos

~~~bash
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY no_proxy NO_PROXY
export ALL_PROXY=socks5h://127.0.0.1:63051
curl --connect-timeout 5 --max-time 20 http://api.ipify.org
curl --connect-timeout 5 --max-time 20 https://campus.itba.edu.ar/
curl --connect-timeout 5 --max-time 20 https://example.com/
~~~

Los límites de tiempo son de diagnóstico, no de la mecánica del proxy. Se espera IP pública/HTML o una respuesta del sitio según su política, mientras la VM tenga salida TCP y DNS.

### P6. Demostrar que depende del túnel

Dejar las sesiones abiertas; en el remoto:

~~~bash
curl --noproxy '*' --connect-timeout 3 --max-time 5 http://1.1.1.1/
curl --connect-timeout 5 --max-time 20 http://api.ipify.org
~~~

El primero sigue fallando porque evita proxies; el segundo usa ALL_PROXY y debe funcionar. No cambiamos rutas ni agregamos NAT al remoto.

También se puede cerrar con Ctrl+C el -D de la terminal A y repetir el segundo curl: debe fallar al intentar acceder al destino local del forward. Restaurar -D si se quiere seguir practicando. Un listener -R existente no prueba que el servicio al otro lado siga vivo.

### P7. Cerrar y limpiar

Primero exit en la shell remota y Ctrl+C en la terminal del -D. Luego, en tu VM:

~~~bash
bash ~/Downloads/practica-21.2-4.sh down
~~~

down detiene procesos del namespace de práctica, el sshd dedicado del host y elimina veth/namespace. Conserva archivos y llaves de laboratorio por si se repite. No borra usuarios, llaves personales ni altera el SSH principal. Si sshd local principal se inició para la receta real y ya no se necesita, decidir aparte si detenerlo; no hacerlo a ciegas si hay otras sesiones.

## Qué hace la preparación del laboratorio, comando por comando

| Comando o construcción del script | Función y parámetros |
| --- | --- |
| set -euo pipefail | Aborta ante errores no manejados, variables no definidas y fallos de pipelines; las comprobaciones esperables usan condicionales |
| id -un / id -u | Usuario actual por nombre / UID numérico |
| sudo -v | Valida credenciales sudo antes de preparar |
| mkdir -p / chmod 700 / umask 077 | Crea carpeta y restringe acceso; la máscara retira permisos nuevos de grupo/otros |
| ssh-keygen -q -t ed25519 -N '' -f RUTA | Genera clave de práctica; q silencioso, t algoritmo, N passphrase vacía, f destino; -C agrega comentario en la clave cliente |
| cp ...pub authorized_keys / chmod 600 | Autoriza solo la pública de laboratorio; archivo privado para el propietario |
| ip netns add NOMBRE | Crea una pila de red separada con ese nombre |
| ip link add A type veth peer name B | Crea un par de interfaces Ethernet virtuales conectadas entre sí |
| ip link set B netns NOMBRE | Mueve un extremo al namespace |
| ip addr add IP/30 dev A | Asigna IPv4 y prefijo al extremo del host |
| ip link set A up | Activa interfaz; dentro se activa además lo |
| ip -n NOMBRE ... | Aplica el subcomando de red dentro del namespace indicado; aquí -n es namespace, no “números” |
| ip netns exec NOMBRE PROGRAMA | Ejecuta un proceso con la red de ese namespace; no crea un contenedor de filesystem |
| sshd -t -f CONFIG | Valida el archivo específico de sshd |
| sshd -f CONFIG -E LOG | Inicia el daemon dedicado con su configuración y archivo de log; no modifica el servicio principal |
| ssh-keygen -lf PUBLICA | Muestra fingerprint; l lista la huella, f elige archivo |
| ss -H -ltn 'sport = :2299' | Lista listeners TCP numéricos del puerto local; H sin encabezado, l escucha, t TCP, n numérico |
| ip netns pids NOMBRE / kill PID | Lista y termina procesos que mantienen viva la red aislada al limpiar |
| trap ... ERR | Registra limpieza ante un fallo de preparación |
| > archivo / <<EOF | Escribe el archivo de configuración y entrega un bloque de texto con expansión de variables |
| $(...) / variables entre comillas | Captura salida de un comando / evita separar rutas en palabras |

Los nombres del namespace y veth son exclusivos del laboratorio y se comprueban antes de usarlos. La subred 192.0.2.0/30 está reservada para documentación; si ya se usa o se superpone en tu máquina, adaptar la red del laboratorio. El script no agrega una ruta default ni toca reglas NAT.

### Directivas de los sshd de práctica

| Directiva | Función |
| --- | --- |
| Port / ListenAddress | Puerto e IP donde escucha cada daemon |
| HostKey | Clave privada que identifica a ese servidor de práctica |
| PidFile | Archivo de PID para poder limpiar el daemon correcto |
| AuthorizedKeysFile | Lista aislada de claves públicas autorizadas |
| AllowUsers | Restringe al usuario que ejecuta el script |
| PubkeyAuthentication yes | Permite autenticación por clave |
| PasswordAuthentication no / KbdInteractiveAuthentication no | No admite esos métodos en los daemons de práctica |
| UsePAM yes | Usa PAM para comprobaciones de cuenta y sesión en Ubuntu |
| PermitRootLogin no | La práctica usa tu cuenta normal, no root |
| StrictModes yes | Conserva comprobaciones de propiedad y permisos |
| AllowTcpForwarding yes | Habilita los forwards que estamos practicando |
| GatewayPorts no | Mantiene la escucha remota de forwards en loopback |
| LogLevel VERBOSE | Registra detalles útiles para diagnóstico |

---

## Si algo falla

| Síntoma | Causa posible | Arreglo |
| --- | --- | --- |
| El -D a localhost rechaza conexión | sshd local detenido o puerto incorrecto | Revisar systemctl status ssh o usar sshd dedicado 2299 en práctica |
| -D: Address already in use | 9090 ocupado | ss -ltnp; elegir otro puerto y cambiar el destino del -R |
| remote port forwarding failed | Puerto 63051 ocupado o política SSH | Elegir puerto libre y revisar permisos de forwarding; ExitOnForwardFailure evita continuar como si funcionara |
| curl remoto rechaza 127.0.0.1:63051 | No existe el listener remoto | Mantener -R abierto y comprobar ss -ltn en el remoto |
| -R escucha pero no navega | El SOCKS 9090 no está vivo o el -D sale por un host sin Internet | Revisar ambos extremos y probar -D desde la VM |
| Could not resolve host con socks5 | curl intenta DNS en el host aislado | Usar socks5h |
| ALL_PROXY no parece usarse | http_proxy/https_proxy/all_proxy o NO_PROXY prevalecen | Limpiar variables de la shell; probar curl -x socks5h://127.0.0.1:63051 URL |
| Se devuelve la IP de pampero | El servidor del -D es pampero | Es S5/salida por pampero; si se quiere IP propia, usar localhost o -R dinámico iniciado en tu VM |
| HTTPS da error de certificado | CA, reloj, nombre o inspección TLS | Revisar el error; no convertir -k en solución del túnel |
| Campus devuelve 301/302 o pide login | Comportamiento de la aplicación | Seguir con -L si corresponde; no confundir con falta de conectividad |
| ssh pide passphrase | Llave cifrada del ejercicio previo | Escribir la passphrase; no confundir con contraseña de pdc |
| Permission denied | Llave, usuario, puerto o política incorrecta | Revisar -i, pdc y 2222; usar -v para diagnóstico |
| Operation not permitted al crear namespace | Faltan privilegios/capacidades del kernel | Ejecutar laboratorio en la VM Ubuntu con sudo; este entorno no permite namespaces |
| La práctica dice root | Se ejecutó sudo bash script | Ejecutar como jerodileo; el script solicita sudo internamente |
| direct curl funciona en el namespace | Se cambió el aislamiento, hay ruta extra o no estás en ese namespace | ip -br addr, ip route; usar --noproxy '*' y destino numérico para la prueba |
| Dejó de funcionar al cerrar terminal | Se cerró una sesión que sostenía túnel | Reabrirla; -N en primer plano o variante -f para mantenerla |
| -R sin destino no se acepta | Cliente OpenSSH antiguo | Usar la solución clásica -D + -R fijo |
| No funciona UDP/ping | SOCKS/forwards usados aquí transportan TCP | La consigna es curl HTTP(S); no afirmar conectividad IP general |
| Script no elimina daemon local | No pudo confirmar PID/configuración | Revisar su host.pid y host.log; no matar otros sshd por nombre |

Para diagnóstico del remoto:

~~~bash
ss -ltn 'sport = :63051'
~~~

-l muestra listeners; -t TCP; -n números; el filtro selecciona el puerto local. Si se necesitan procesos y se dispone de permisos, agregar -p.

## Variantes: qué cambia y qué línea tocar

| Variante | Cambio exacto |
| --- | --- |
| Otro puerto SSH | Cambiar -p 2222 por -p PUERTO |
| Otro usuario/servidor | Cambiar pdc@parcial.leak.com.ar |
| Otra identidad | Cambiar -i ./llave.pem |
| Otro puerto remoto SOCKS | Cambiar 63051 en -R y en ALL_PROXY |
| Otro puerto local SOCKS | Cambiar 9090 en -D y en el destino de -R fijo |
| SOCKS solo para un curl | ALL_PROXY=socks5h://127.0.0.1:63051 curl URL |
| Proxy explícito | curl -x socks5h://127.0.0.1:63051 URL; -x selecciona proxy, pero NO_PROXY puede aún excluir destinos |
| No querés servidor SSH local | Usar -R 127.0.0.1:63051 sin destino, en cliente compatible |
| Solo un servicio interno | -L 8080:HOST_INTERNO:80; no sustituye la navegación a destinos arbitrarios |
| Enviar -D al fondo | ssh -f -N -o ExitOnForwardFailure=yes -D 127.0.0.1:9090 jerodileo@127.0.0.1; f pasa al fondo después de autenticarse |
| Túnel dedicado sin shell | Agregar -N al -R y abrir otra sesión para curl; no se pierde el listener si la sesión del túnel sigue viva |
| Salir por pampero | ssh -N -D 127.0.0.1:9090 jdileomuntaner@pampero.itba.edu.ar; las conexiones finales salen por pampero |
| Firefox en vez de curl | Configurar SOCKS v5 y DNS por SOCKS en la máquina donde está el listener apropiado |
| HTTP proxy en vez de SOCKS | http_proxy=http://PROXY:PUERTO y https_proxy=http://PROXY:PUERTO si soporta CONNECT; esto por sí solo no agrega el túnel SSH exigido |

### Diferencia con S4 y S5 de tus apuntes

- **S4:** el curl está en pampero o en el host aislado y debe salir por tu VM. Se usa -R hacia un SOCKS de tu VM, o -R dinámico. El ejemplo de S4 busca tu IP pública.
- **S5:** el curl está en tu VM y debe salir por pampero. Se usa -D apuntando a pampero y curl -x al SOCKS local.
- **Este Ejercicio IV:** se parece a S4; no alcanza con crear un -D desde tu VM hacia el mismo host que carece de Internet.

## Alternativa sin túneles: por qué vale menos

Si el host tiene ruta hasta un proxy HTTP/SOCKS externo con salida, se puede configurar curl para usarlo directamente. Para HTTPS el HTTP proxy debe soportar CONNECT. Eso puede resolver navegación, pero no demuestra el túnel SSH pedido y la consigna reduce el puntaje.

Cambiar NAT o rutas del gateway sería otra intervención de infraestructura, normalmente fuera de los permisos del usuario pdc; no asumir que se puede hacer. La receta principal no necesita acceso de root al gateway ni al servidor real.

## Qué mostrar en el video

1. Identificar terminal local y shell remota.
2. Probar que el remoto falla sin proxy y que tu VM tiene salida.
3. Mostrar los comandos -D y -R, con los puertos y los extremos correctos.
4. Mostrar ALL_PROXY con socks5h.
5. Ejecutar en el remoto HTTP, HTTPS y otro destino.
6. Comparar IP pública con la de tu máquina de salida y explicar que no se modificó NAT.
7. Si se usa la forma corta, explicar que -R sin destino actúa como SOCKS dinámico y por qué no hace falta -D.

**Frase de cierre:** “Publiqué en el loopback del host aislado un acceso SOCKS mediante un túnel SSH inverso; curl resuelve y abre HTTP y HTTPS por la máquina con salida, sin modificar el gateway ni configurar NAT.”

## Código completo del laboratorio

~~~bash
#!/usr/bin/env bash
# Ejecutar como usuario normal de la VM; no con sudo bash.
set -euo pipefail
LAB_DIR="$HOME/protos/practica/21.2-4"
LAB_NS="p214-sinred"
LAB_VETH="p214-host"
LAB_PEER="p214-remoto"
LAB_USER="$(id -un)"
ACTION=help
if [[ "$#" -ge 1 ]]; then ACTION="$1"; fi
need() { command -v "$1" >/dev/null || { echo "Falta: $1" >&2; exit 1; }; }
is_ns() { sudo ip netns list | awk '{print $1}' | grep -Fxq "$LAB_NS"; }
stop_lab() {
    if [[ ! -f "$LAB_DIR/OWNED" ]]; then
        echo "No hay marcador OWNED: no elimino recursos."; return 0
    fi
    if is_ns; then
        while read -r pid; do
            [[ -z "$pid" ]] || sudo kill "$pid" 2>/dev/null || true
        done < <(sudo ip netns pids "$LAB_NS")
    fi
    if [[ -f "$LAB_DIR/host.pid" ]]; then
        pid="$(cat "$LAB_DIR/host.pid")"
        if [[ "$pid" =~ ^[0-9]+$ ]] &&
           sudo test -r "/proc/$pid/cmdline" &&
           sudo grep -azFq "$LAB_DIR/host.conf" "/proc/$pid/cmdline"; then
            sudo kill "$pid" || true
        fi
    fi
    if is_ns; then sudo ip netns del "$LAB_NS"; fi
    if ip link show "$LAB_VETH" >/dev/null 2>&1; then
        sudo ip link del "$LAB_VETH"
    fi
    rm -f "$LAB_DIR/OWNED"
    echo "Laboratorio detenido; archivos conservados en $LAB_DIR"
}
case "$ACTION" in
up)
    if [[ "$(id -u)" -eq 0 ]]; then
        echo "Ejecutar como tu usuario normal, no con sudo bash." >&2; exit 1
    fi
    for cmd in ip ssh ssh-keygen curl sudo ss awk grep; do need "$cmd"; done
    [[ -x /usr/sbin/sshd ]] || { echo "Falta openssh-server"; exit 1; }
    sudo -v
    if is_ns || ip link show "$LAB_VETH" >/dev/null 2>&1; then
        echo "Los nombres del laboratorio ya están en uso." >&2; exit 1
    fi
    if [[ -e "$LAB_DIR/OWNED" ]]; then
        echo "Existe un laboratorio previo. Usar down y revisar." >&2; exit 1
    fi
    if [[ -n "$(ip -4 route show to exact 192.0.2.0/30)" ]]; then
        echo "192.0.2.0/30 ya está en uso: cambiar subred de práctica." >&2; exit 1
    fi
    if [[ -n "$(ss -H -ltn 'sport = :2299')" ]]; then
        echo "El puerto local 2299 está ocupado." >&2; exit 1
    fi
    mkdir -p "$LAB_DIR"
    chmod 700 "$LAB_DIR"
    umask 077
    [[ -e "$LAB_DIR/client_key" ]] ||
        ssh-keygen -q -t ed25519 -N '' -f "$LAB_DIR/client_key" -C "p214-practica"
    [[ -e "$LAB_DIR/host_key" ]] ||
        ssh-keygen -q -t ed25519 -N '' -f "$LAB_DIR/host_key"
    [[ -e "$LAB_DIR/remote_key" ]] ||
        ssh-keygen -q -t ed25519 -N '' -f "$LAB_DIR/remote_key"
    cp "$LAB_DIR/client_key.pub" "$LAB_DIR/authorized_keys"
    chmod 600 "$LAB_DIR/authorized_keys"
    write_config() {
        local file="$1" address="$2" port="$3" hostkey="$4" pidfile="$5"
        cat > "$file" <<EOF
Port $port
ListenAddress $address
HostKey $hostkey
PidFile $pidfile
AuthorizedKeysFile $LAB_DIR/authorized_keys
AllowUsers $LAB_USER
PubkeyAuthentication yes
PasswordAuthentication no
KbdInteractiveAuthentication no
UsePAM yes
PermitRootLogin no
StrictModes yes
AllowTcpForwarding yes
GatewayPorts no
LogLevel VERBOSE
EOF
    }
    write_config "$LAB_DIR/host.conf" 127.0.0.1 2299 "$LAB_DIR/host_key" "$LAB_DIR/host.pid"
    write_config "$LAB_DIR/remote.conf" 192.0.2.2 2222 "$LAB_DIR/remote_key" "$LAB_DIR/remote.pid"
    sudo mkdir -p /run/sshd
    sudo /usr/sbin/sshd -t -f "$LAB_DIR/host.conf"
    sudo /usr/sbin/sshd -t -f "$LAB_DIR/remote.conf"
    touch "$LAB_DIR/OWNED"
    trap 'echo "Fallo: retiro recursos del laboratorio." >&2; stop_lab' ERR
    sudo ip netns add "$LAB_NS"
    sudo ip link add "$LAB_VETH" type veth peer name "$LAB_PEER"
    sudo ip link set "$LAB_PEER" netns "$LAB_NS"
    sudo ip addr add 192.0.2.1/30 dev "$LAB_VETH"
    sudo ip link set "$LAB_VETH" up
    sudo ip -n "$LAB_NS" link set lo up
    sudo ip -n "$LAB_NS" addr add 192.0.2.2/30 dev "$LAB_PEER"
    sudo ip -n "$LAB_NS" link set "$LAB_PEER" up
    # Sin ruta por defecto: solo alcanza a la VM.
    sudo /usr/sbin/sshd -f "$LAB_DIR/host.conf" -E "$LAB_DIR/host.log"
    sudo ip netns exec "$LAB_NS" /usr/sbin/sshd -f "$LAB_DIR/remote.conf" -E "$LAB_DIR/remote.log"
    trap - ERR
    echo "VM: 192.0.2.1/30; remoto: 192.0.2.2/30, SSH 2222."
    echo "Usuario de práctica: $LAB_USER (no se crea pdc)."
    echo "SSH local para -D: 127.0.0.1:2299. Archivos: $LAB_DIR"
    echo "Huellas de los servidores:"
    ssh-keygen -lf "$LAB_DIR/host_key.pub"
    ssh-keygen -lf "$LAB_DIR/remote_key.pub"
    ;;
status)
    need ip
    if is_ns; then
        sudo ip -n "$LAB_NS" -br addr
        sudo ip -n "$LAB_NS" route
        sudo ip netns exec "$LAB_NS" ss -ltnp
    else
        echo "Namespace ausente."
    fi
    ;;
down)
    need ip; stop_lab
    ;;
*)
    echo "Uso: bash practica-21.2-4.sh up|status|down"
    echo "Crea red y dos sshd dedicados; no altera sshd principal ni configura NAT."
    ;;
esac


~~~

## Guardar y usar estos archivos en tu VM

Los documentos se entregan descargables: no se escribieron automáticamente en el home de tu VM. Después de descargarlos:

~~~bash
mkdir -p ~/protos/soluciones
cp ~/Downloads/21.2-4.md ~/protos/soluciones/
cp ~/Downloads/21.2-4.html ~/protos/soluciones/
~~~

mkdir -p crea padres faltantes y acepta carpetas existentes; cp copia archivos. Si tu navegador usa Descargas, ajustar el directorio. El HTML no necesita conexión a Internet ni recursos externos para leerse.

## Fuentes

- Imagen del Ejercicio IV aportada por el usuario.
- [Notion: Guía de parciales → SSH](https://app.notion.com/p/4056494c8b478186aaa9cd2e25afeea0).
- [Notion: Práctica P-SSH, S4 y S5](https://app.notion.com/p/4056494c8b4781d98a11d1f41191bda0).
- [OpenSSH: ssh](https://man.openbsd.org/ssh).
- [curl: proxy y variables de entorno](https://curl.se/docs/manpage.html).

