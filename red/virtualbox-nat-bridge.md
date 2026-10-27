# VirtualBox en el parcial: ¿NAT, Bridge o red interna?

En el parcial te conectás a la red de la cátedra (WiFi abierta) y desde ahí llegás a sus servidores (`protos.foo`, `parcial.protos.foo`, `mail.protos.foo`, etc.). Lo único que cambia entre ejercicios es **por dónde sale la placa de red de la VM**. Este archivo te dice cuál usar, cómo cambiarlo y cómo comprobar que quedó bien.

---

## ⭐ Regla rápida (leer primero)

**Por defecto: NAT.** Pasá a **Bridge** solo si el enunciado tiene alguna de estas señales. Para **DHCP server**: **red interna**, nunca Bridge.

| Si el enunciado dice… | Modo | Por qué |
|---|---|---|
| "modo Bridge / Puente", "conectado a la red abierta" | **Bridge** | Lo pide explícitamente |
| "el host X es el **gateway** de la red Y", "agregue la ruta", "descubra el servidor en la red 10.0.0.0/24" | **Bridge** | Tu VM tiene que estar en la misma red que el gateway para usarlo como próximo salto |
| "routers que intervienen", `traceroute` a una red interna de ellos | **Bridge** | Mismo motivo: el primer salto tiene que ser su gateway, no tu compu |
| "descubra los hosts de **esta red**", `nmap -sn` sobre la red del laboratorio | **Bridge** | Desde NAT solo ves la red interna de VirtualBox (10.0.2.0/24) |
| "dirección **MAC** de un host" **de la red del laboratorio** (no de pampero) | **Bridge** | ARP solo funciona dentro de la misma red física |
| "que **otros** (o la cátedra) accedan a un servicio de tu VM" | **Bridge** | Desde NAT nadie de afuera llega a tu VM |
| `nmap --script broadcast-dhcp-discover` contra **el DHCP de ellos** | **Bridge** | El broadcast tiene que salir a su red |
| "instale un **servidor DHCP**" | **Red interna** | En Bridge repartirías IPs a todo el laboratorio |
| Todo lo demás: BIND, nginx, curl/SOCKS, SSH a pampero o a `parcial.*`, túneles, SMTP/POP3, `dig` MX/SPF, pcap | **NAT** | Solo hacen falta conexiones **salientes** y resolver nombres, y NAT lo hace |

> **Regla mental:** si el ejercicio necesita que tu VM **esté en la red** de ellos (mismo segmento, misma subred, que te vean), es Bridge. Si solo necesita **salir** hacia sus servidores, es NAT.

---

## Tabla por tipo de ejercicio del repo

| Receta | Modo | Nota |
|---|---|---|
| `dns/zona-foo-example-org_1c2026.md`, `dns/zona-demiloo_2c2022.md` | NAT | `dig @127.0.0.1` es local; `dig` de los datos externos sale por NAT |
| `dns/corregir-zona-it-itba_2c2025.md` | NAT | Bajar la zona con `curl http://protos.foo/zona` funciona desde NAT |
| `dns/mx-spf_recu2020.md` | NAT | Solo consultas `dig` |
| `nginx/*` | NAT | El `curl` lo hacés desde la misma VM; nginx sale a buscar el backend |
| `curl/socks5h-acumulativo_1c2026.md` | NAT | El proxy SOCKS es de ellos; vos solo salís hacia él |
| `ssh/*` (tail, .pem, clave pública, sin NAT) | NAT | Todas son conexiones salientes; `-R` no necesita que entren a tu VM |
| `smtp/*` | NAT | `nc` saliente a los puertos 25 y 110 |
| `pcap/pcap.md` | (no importa) | Se analiza un archivo; no usa la red |
| `red/gateway-ruta-estatica-nmap_2c2025.md` | **Bridge** | El enunciado lo pide; `ip route add ... via 192.168.50.250` |
| `red/dhcp-servidor_2c2025.md` | **Red interna** | Nunca Bridge |

---

## Paso a paso: pasar a Bridge

### 1. Conectarte a la red del parcial
Primero conectá **tu compu** (no la VM) al WiFi de la cátedra. Fijate el nombre de la placa con la que te conectaste:

~~~bash
ip -br addr        # en tu compu (host), no en la VM
~~~
La que tiene IP de la red del parcial es la que vas a elegir. En notebooks suele ser `wlp...` (WiFi) o `enp...` (cable).

### 2. Cambiar el adaptador en VirtualBox
1. VirtualBox → seleccioná tu VM → **Configuración → Red → Adaptador 1**.
2. **Conectado a:** `Adaptador puente`.
3. **Nombre:** la placa del paso 1 (ej. `wlp3s0`).
4. **Aceptar.**

Con la VM prendida también se puede: en la ventana de la VM, abajo a la derecha, **clic derecho en el ícono de red → Configuración de red**. No se borra nada de la VM: solo cambia por dónde sale la placa.

### 3. Pedir IP nueva dentro de la VM
Si la VM estaba prendida, todavía tiene la IP de NAT (`10.0.2.15`). Renovala:

~~~bash
sudo dhclient -r && sudo dhclient
# si no tenés dhclient:
sudo systemctl restart NetworkManager
~~~
- `dhclient -r`: libera la IP actual. `dhclient`: pide una nueva al DHCP de la red.

### 4. Comprobar
~~~bash
ip -br addr                 # una IP de la red del parcial (ej. 192.168.50.X), NO 10.0.2.x
ip route                    # "default via <router de la red del parcial>"
ping -c 2 <gateway del enunciado>     # ej. 192.168.50.250
dig +short protos.foo       # resuelve los nombres de la cátedra
~~~
Si los cuatro dan bien, seguí con la receta del ejercicio.

### 5. Volver a NAT al terminar
Mismo lugar, **Conectado a: NAT**, y repetir el paso 3. Así los demás ejercicios siguen funcionando como los practicaste.

---

## Paso a paso: red interna (solo para el DHCP)

La receta completa está en `red/dhcp-servidor_2c2025.md`. Resumen:

1. VM servidor → **Configuración → Red → Adaptador 2** → Habilitar → **Conectado a: Red interna** → nombre `intnet`. El Adaptador 1 queda en NAT, para tener internet e instalar paquetes.
2. Dentro de la VM, darle IP fija a la placa nueva (suele llamarse `enp0s8`):
   ~~~bash
   sudo ip addr add 192.168.100.1/24 dev enp0s8
   sudo ip link set enp0s8 up
   ~~~
3. Configurar el DHCP para que escuche **solo** en `enp0s8` (`/etc/default/isc-dhcp-server` → `INTERFACESv4="enp0s8"`).
4. Para probar: otra VM (o un clon) con su adaptador en **Red interna `intnet`**, que pida IP con `dhclient`. O desde el servidor: `sudo nmap --script broadcast-dhcp-discover -e enp0s8`.

La red interna es una red "de juguete" entre VMs: no sale a ningún lado y no molesta a nadie.

---

## Si algo falla

| Ves | Causa | Arreglo |
|---|---|---|
| Sigue con IP `10.0.2.x` | No renovó o el adaptador sigue en NAT | Revisar paso 2 y repetir paso 3 |
| Sin IP (`ip -br addr` no muestra IPv4) | La red no te dio IP por DHCP | Reintentar `sudo dhclient`; si la red no reparte IPs, poner una a mano: `sudo ip addr add 192.168.50.X/24 dev enp0s3` y `sudo ip route add default via <router>` |
| En "Nombre" no aparece la placa WiFi | VirtualBox no ve la interfaz | Reiniciar VirtualBox; revisar que el host esté conectado |
| Bridge sobre WiFi no consigue IP | Algunos access points bloquean varias MAC por cliente | Probar con cable si hay. Si no, resolver en NAT todo lo que se pueda y avisar en el video |
| `dig protos.foo` no resuelve en Bridge | El DHCP no te dio el DNS de ellos | `resolvectl status` para ver el DNS; probar `dig @<DNS de la red> protos.foo` |
| Después de volver a NAT no anda internet | Quedó la IP o ruta de Bridge | `sudo dhclient -r && sudo dhclient` |
| En NAT `ip route add ... via 192.168.50.250` da `Nexthop has invalid gateway` | Ese gateway no está en tu red: estás en NAT | Pasar a Bridge |
| Levantaste DHCP en Bridge por error | Repartís IPs en la red del laboratorio | `sudo systemctl stop isc-dhcp-server` **ya**, y pasar a red interna |

---

## Cómo practicarlo antes del parcial (en tu casa)

1. **Bridge con tu WiFi.** Poné la VM en Bridge sobre tu placa WiFi y comprobá que reciba una IP de tu router (`192.168.0.X` o `192.168.1.X`) y que `ping` al router funcione. Si anda en tu casa, anda allá.
2. **Ejercicio que lo usa.** Hacé `red/gateway-ruta-estatica-nmap_2c2025.md`. Ya tiene una simulación de la red del parcial con namespaces, así que no depende de tener el gateway real.
3. **Volver a NAT** y comprobar que un ejercicio de NAT siga andando, por ejemplo `dig +short MX gmail.com` o un `curl` cualquiera.
4. **Red interna.** Hacé `red/dhcp-servidor_2c2025.md` con un clon de la VM como cliente.

### Para el video (si el ejercicio usa Bridge)
"Pasé el adaptador de la VM a modo puente para que quede en la misma red que el gateway; con `ip -br addr` se ve que recibí una IP de esa red, y recién ahí puedo usar 192.168.50.250 como próximo salto."
