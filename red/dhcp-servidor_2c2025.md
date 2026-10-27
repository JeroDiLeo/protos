# Protocolos — 2C 2025, Ejercicio I: servidor DHCP

## Consigna (textual)
Usted administra la red de una pequeña oficina (`192.168.100.0/24`) que utiliza un servidor DHCP para la asignación de direcciones IP. Configure el servidor para que cumpla con los siguientes requisitos:
1. Una impresora de red crítica, con la dirección MAC `08:00:27:AE:CB:6A`, debe tener siempre la dirección IP estática `192.168.100.10`.
2. Todos los clientes deben usar los servidores DNS de Google (`8.8.8.8` y `8.8.4.4`).
3. Se desea usar el rango de direcciones `10-200` para asignar. El resto queda reservado para uso futuro.

Verifique con:
~~~bash
sudo nmap --script broadcast-dhcp-discover \
  --script-args "broadcast-dhcp-discover.mac=AA:BB:CC:DD:EE:FF"
~~~
**Aviso:** no resolverlo sobre una interfaz conectada al WiFi del laboratorio: usar una red interna o interfaz virtual.

> **Todo lo de este documento se probó** con isc-dhcp-server y nmap 7.94, en una red aislada (namespaces de Linux): servidor en 192.168.100.1 y un cliente consultando con el `nmap` del enunciado.

---

## ⭐ RECETA PARA EL PARCIAL

### Paso 0 — Consigna → configuración
| La consigna dice | Va en | Cómo se escribe |
|---|---|---|
| red `192.168.100.0/24` | bloque `subnet` | `subnet 192.168.100.0 netmask 255.255.255.0 { ... }` |
| impresora MAC → siempre `.10` | bloque `host` | `hardware ethernet 08:00:27:AE:CB:6A;` + `fixed-address 192.168.100.10;` |
| DNS de Google | opción | `option domain-name-servers 8.8.8.8, 8.8.4.4;` (**con s**) |
| rango `10-200` | `range` | `range 192.168.100.11 192.168.100.200;` → **empieza en .11** (ver por qué abajo) |
| "el resto reservado" | — | no se hace nada: lo que queda fuera del `range` y no es fijo, no se asigna |

### Paso 1 — Preparar la red (en VirtualBox, antes de arrancar la VM)
- Adaptador de la VM en **Red interna** (Internal Network) o **Solo anfitrión** (Host-only). **Nunca Bridge al WiFi**: DHCP responde por broadcast y le estarías dando IPs a las máquinas del laboratorio.
- Si querés internet para instalar paquetes, dejá un adaptador 1 en NAT y agregá un adaptador 2 en Red interna para el ejercicio.

### Paso 2 — Instalar y elegir la interfaz
~~~bash
sudo apt install -y isc-dhcp-server nmap
ip -br addr
~~~
- `ip -br addr`: lista interfaces en una línea cada una (`-br` = brief). Identificar la de la red interna (suele ser `enp0s8` o `enp0s9`; la `enp0s3` suele ser la NAT).
- En el resto del documento: `IFACE` = esa interfaz. **Reemplazarla por el nombre real.**

### Paso 3 — Darle IP fija al servidor dentro de la red
~~~bash
sudo systemctl stop NetworkManager      # solo en la VM: evita que pise la IP manual
sudo ip link set IFACE up
sudo ip addr replace 192.168.100.1/24 dev IFACE
ip -br addr show IFACE                  # debe mostrar 192.168.100.1/24
~~~
- `ip link set ... up`: levanta la interfaz.
- `ip addr replace`: pone esa IP (si ya tenía una igual, no da error; `add` sí daría "File exists").
- El servidor DHCP necesita una IP **dentro de la subred** que sirve: si no, `isc-dhcp-server` no arranca ("No subnet declaration for IFACE").

### Paso 4 — Decirle por qué interfaz escuchar
~~~bash
sudo nano /etc/default/isc-dhcp-server
~~~
~~~conf
INTERFACESv4="IFACE"
INTERFACESv6=""
~~~
Limita el servicio a la red interna. Es lo que evita contestarle a la red real.

### Paso 5 — Configuración
~~~bash
sudo nano /etc/dhcp/dhcpd.conf
~~~
Borrar o comentar lo que trae de ejemplo y dejar:
~~~conf
ddns-update-style none;
authoritative;
default-lease-time 600;
max-lease-time 7200;

subnet 192.168.100.0 netmask 255.255.255.0 {
  range 192.168.100.11 192.168.100.200;
  option subnet-mask 255.255.255.0;
  option broadcast-address 192.168.100.255;
  option domain-name-servers 8.8.8.8, 8.8.4.4;
}

host impresora {
  hardware ethernet 08:00:27:AE:CB:6A;
  fixed-address 192.168.100.10;
}
~~~

| Línea | Por qué |
|---|---|
| `ddns-update-style none;` | no intenta actualizar un DNS dinámico (no lo pide la consigna) |
| `authoritative;` | este servidor es el oficial de la red: responde NAK a pedidos de IPs que no corresponden, así el cliente pide una nueva |
| `default-lease-time 600;` / `max-lease-time 7200;` | duración del préstamo en segundos (10 min por defecto, 2 h máximo) |
| `subnet ... netmask ...` | la red que atiende. Tiene que coincidir con la IP que le diste al servidor |
| `range .11 .200` | IPs que se reparten dinámicamente |
| `option subnet-mask` / `broadcast-address` | máscara y broadcast que recibe el cliente |
| `option domain-name-servers 8.8.8.8, 8.8.4.4;` | DNS que recibe el cliente, separados por **coma** |
| `host impresora { ... }` | reserva: a esa MAC siempre se le da esa IP. El nombre `impresora` es libre |
| `hardware ethernet` | la MAC de la impresora (mayúsculas o minúsculas dan igual: probado) |
| `fixed-address` | la IP fija |

**¿Por qué el `host` fuera del `subnet`?** Si se pone adentro funciona igual, pero `dhcpd` avisa `WARNING: Host declarations are global`: las reservas siempre valen para todas las subredes. Afuera queda sin avisos y es más claro.

### ¿Por qué el rango empieza en .11 y no en .10? (probado)
Con `range 192.168.100.10 192.168.100.200;` el servidor **le ofreció la `.10` a un cliente cualquiera** (`AA:BB:CC:DD:EE:01 → 192.168.100.10`, del log: `DHCPOFFER on 192.168.100.10 to aa:bb:cc:dd:ee:01`). Si la impresora se conecta después, su IP ya está prestada a otro equipo y se rompe el requisito 1. Por eso:
- `.10` → solo la impresora (`fixed-address`).
- `.11` a `.200` → dinámicas.
- `.201` a `.254` (y `.2` a `.9`) → reservadas para uso futuro.

En el video decirlo así: "el rango 10–200 lo cubro con la `.10` reservada para la impresora y `.11–.200` dinámico; si incluyo la `.10` en el rango, el servidor la puede prestar a otro equipo, lo comprobé".

### Paso 6 — Validar y levantar
~~~bash
systemctl status isc-dhcp-server --no-pager     # mostrar que no está corriendo (lo pide el video)
sudo dhcpd -t -4 -cf /etc/dhcp/dhcpd.conf        # validar sintaxis
sudo systemctl restart isc-dhcp-server
systemctl status isc-dhcp-server --no-pager      # debe decir active (running)
~~~
- `dhcpd -t`: solo **prueba** la configuración, no arranca nada. `-4` = IPv4. `-cf` = archivo de configuración. Si está bien, imprime solo la cabecera (Config file / Database file / PID file) sin errores.

### Paso 7 — Verificar con nmap (el comando del enunciado + `-e`)
~~~bash
sudo nmap --script broadcast-dhcp-discover \
  --script-args "broadcast-dhcp-discover.mac=AA:BB:CC:DD:EE:FF" -e IFACE

sudo nmap --script broadcast-dhcp-discover \
  --script-args "broadcast-dhcp-discover.mac=08:00:27:AE:CB:6A" -e IFACE
~~~
- `--script broadcast-dhcp-discover`: manda un DHCPDISCOVER por broadcast y muestra la oferta que llegue. **No toma la IP**: solo pregunta.
- `--script-args "...mac=..."`: la MAC con la que se hace pasar el pedido. Con la de la impresora tiene que ofrecer la `.10`.
- `-e IFACE`: por qué interfaz mandarlo. Sin `-e`, nmap lo manda por las interfaces que tengan IPv4 (en la prueba funcionó igual y la salida muestra `Interface: ...`). **Agregalo igual**: en una VM con dos placas (NAT + red interna) así te asegurás de que el pedido salga por la red del ejercicio y no por la NAT.
- Al final aparece `WARNING: No targets were specified, so 0 hosts scanned.` **No es un error**: el script es de broadcast y no escanea ningún host. Lo que importa es el bloque `broadcast-dhcp-discover` de arriba.

Salida real de la prueba:
~~~text
cliente cualquiera (AA:BB:CC:DD:EE:FF):
|     IP Offered: 192.168.100.11
|     DHCP Message Type: DHCPOFFER
|     Server Identifier: 192.168.100.1
|     IP Address Lease Time: 10m00s
|     Subnet Mask: 255.255.255.0
|     Domain Name Server: 8.8.8.8, 8.8.4.4
|_    Broadcast Address: 192.168.100.255

impresora (08:00:27:AE:CB:6A):
|     IP Offered: 192.168.100.10
|     Domain Name Server: 8.8.8.8, 8.8.4.4
~~~
Qué señalar en el video: `IP Offered` dentro de 11–200 para el cliente común, `.10` para la impresora, y `Domain Name Server: 8.8.8.8, 8.8.4.4` en los dos.

### Para el video
"Configuré isc-dhcp-server en la red interna 192.168.100.0/24. La impresora tiene una reserva por MAC a la .10, todos los clientes reciben los DNS de Google, y el rango dinámico es .11–.200, porque si incluyo la .10 el servidor puede dársela a otro equipo. Lo verifico con nmap: un cliente cualquiera recibe una IP del rango y la MAC de la impresora recibe la .10."

---

## Si algo falla (síntomas probados)
| Ves | Causa | Arreglo |
|---|---|---|
| `unknown option dhcp.domain-name-server` | falta la **s** | `domain-name-servers` |
| `bad range, address ... not in subnet ...` | el `range` no pertenece a la `subnet` | revisar los tres primeros octetos |
| el servicio no arranca: `No subnet declaration for IFACE (x.x.x.x)` y `Not configured to listen on any interfaces!` | el servidor no tiene IP dentro de `192.168.100.0/24` (probado: con 10.9.9.1 pasa esto), o `INTERFACESv4` está mal | Paso 3 y Paso 4; `sudo journalctl -u isc-dhcp-server -n 50 --no-pager` |
| nmap: `broadcast-dhcp-discover threw an error! ... attempt to index a boolean value` | la interfaz del `-e` **no tiene ninguna IPv4** (nmap no puede leer sus datos) | darle una IP: `sudo ip addr replace 192.168.100.1/24 dev IFACE` |
| nmap no muestra ninguna oferta | el servicio no corre, o el pedido salió por otra interfaz | `systemctl status isc-dhcp-server`; usar `-e IFACE` con la interfaz de la red interna |
| a un cliente común le ofrece la `.10` | el `range` empieza en `.10` | `range 192.168.100.11 ...` |
| `WARNING: Host declarations are global` | el bloque `host` está dentro del `subnet` | no es error; sacarlo afuera para que no aparezca |
| la impresora recibe una IP del rango | MAC mal escrita | revisar los 6 pares; mayúsculas/minúsculas da igual |
| la IP manual del servidor desaparece | NetworkManager la pisó | `sudo systemctl stop NetworkManager` (solo en la VM) |

## Variantes
Las directivas de esta tabla se validaron con `dhcpd -t` (sintaxis OK); `deny booting` y `deny unknown-clients` no se probaron con un cliente.

| Si piden... | Agregar o cambiar |
|---|---|
| gateway / router por defecto | dentro del `subnet`: `option routers 192.168.100.1;` |
| nombre de dominio | `option domain-name "oficina.local";` |
| otro rango | `range INICIO FIN;` (sin incluir las IPs fijas) |
| otra reserva | otro bloque `host nombre { hardware ethernet ...; fixed-address ...; }` |
| que un equipo **no** reciba IP | `host bloqueado { hardware ethernet XX:...; deny booting; }` |
| solo atender a equipos conocidos | en el `subnet`: `deny unknown-clients;` |
| otra duración de préstamo | `default-lease-time` / `max-lease-time` en segundos |
| ver las IPs prestadas | `cat /var/lib/dhcp/dhcpd.leases` |
| ver los mensajes DORA en vivo | `sudo journalctl -u isc-dhcp-server -f` (DHCPDISCOVER / DHCPOFFER / DHCPREQUEST / DHCPACK) |

## Al terminar (para no romper otros ejercicios)
~~~bash
sudo systemctl stop isc-dhcp-server
sudo systemctl start NetworkManager
~~~
