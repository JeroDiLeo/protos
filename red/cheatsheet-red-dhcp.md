# Cheatsheet: red, MAC, rutas, nmap y DHCP

Recetas de parciales: [dhcp-servidor_2c2025.md](dhcp-servidor_2c2025.md) · [gateway-ruta-estatica-nmap_2c2025.md](gateway-ruta-estatica-nmap_2c2025.md) · [virtualbox-nat-bridge.md](virtualbox-nat-bridge.md) · capturas: [../pcap/pcap.md](../pcap/pcap.md).

---

## 1. Ver tu propia red

| Comando | Qué muestra |
|---|---|
| `ip a` (`ip addr`) | interfaces, **IPs** (`inet 192.168.0.10/24`) y **MAC** (`link/ether 08:00:27:…`) |
| `ip -br a` | lo mismo, una línea por interfaz |
| `ip link` / `ip -br link` | interfaces, estado (`UP`/`DOWN`) y MAC |
| `ip route` (`ip r`) | tabla de rutas; `default via X` = tu **gateway** |
| `ip route get 8.8.8.8` | por qué interfaz y gateway sale un paquete a esa IP |
| `ip neigh` (`ip n`) | tabla ARP: IP → MAC de los vecinos |
| `resolvectl status` / `cat /etc/resolv.conf` | qué DNS usás |
| `hostname -I` | tus IPs, en una línea |
| `cat /etc/hosts` | nombres fijos locales |
| `nmcli dev show` | todo junto (si hay NetworkManager) |
| `ifconfig` / `route -n` / `arp -n` | equivalentes viejos (`sudo apt install net-tools`) |

Nombres de interfaz: `lo` (loopback), `enp0s3`/`eth0` (cable), `wlp2s0` (wifi), `docker0`/`virbr0` (virtuales).

### Leer `ip a`
~~~text
2: enp0s3: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 …
    link/ether 08:00:27:ae:cb:6a brd ff:ff:ff:ff:ff:ff        ← MAC
    inet 192.168.0.10/24 brd 192.168.0.255 scope global dynamic enp0s3   ← IP/máscara, broadcast
    inet6 fe80::a00:27ff:feae:cb6a/64 scope link                ← IPv6 link-local
~~~
`UP` = encendida; `LOWER_UP` = tiene cable/enlace; `dynamic` = la dio DHCP.

---

## 2. Averiguar la MAC de una IP

Herramientas que quizá falten: `sudo apt install arping arp-scan ipcalc net-tools`.

**La MAC solo se ve dentro de la misma red local (mismo segmento / broadcast).** Si la IP está detrás de un router, la MAC que ves es la **del router**.

| Cómo | Comando |
|---|---|
| ping + tabla ARP | `ping -c1 192.168.0.20 && ip neigh show 192.168.0.20` |
| tabla ARP vieja | `arp -n 192.168.0.20` |
| arping (pregunta ARP directo, funciona aunque el host bloquee ping) | `sudo arping -c 2 -I enp0s3 192.168.0.20` |
| nmap (muestra MAC y fabricante en la red local; **con sudo**) | `sudo nmap -sn 192.168.0.20` → `MAC Address: 08:00:27:AE:CB:6A (Oracle VirtualBox virtual NIC)` |
| toda la red | `sudo nmap -sn 192.168.0.0/24` / `sudo arp-scan --localnet` |
| desde una captura | `tshark -r cap.pcap -Y 'arp' -T fields -e arp.src.proto_ipv4 -e arp.src.hw_mac` |
| de DHCP en la captura | `tshark -r cap.pcap -Y dhcp -T fields -e dhcp.hw.mac_addr -e dhcp.ip.your -e dhcp.option.hostname` |
| leases del servidor DHCP | `cat /var/lib/dhcp/dhcpd.leases` (`lease IP { … hardware ethernet MAC; }`) |
| tu propia MAC | `ip link show enp0s3` / `cat /sys/class/net/enp0s3/address` |
| MAC del gateway | `ip neigh show $(ip route \| awk '/default/{print $3}')` |

### Leer `ip neigh`
~~~text
192.168.0.20 dev enp0s3 lladdr 08:00:27:ae:cb:6a REACHABLE
192.168.0.30 dev enp0s3 FAILED                      ← no respondió al ARP: no está o no está en tu red
~~~
Estados: `REACHABLE` (confirmada recién) · `STALE` (vieja pero válida) · `DELAY`/`PROBE` (verificando) · `INCOMPLETE`/`FAILED` (no respondió).

### Formato de una MAC
- 6 bytes en hex: `08:00:27:AE:CB:6A`. También aparece como `08-00-27-AE-CB-6A` (Windows) o `0800.27ae.cb6a` (Cisco).
- Los 3 primeros bytes (**OUI**) son el fabricante: `08:00:27` = VirtualBox, `52:54:00` = QEMU/KVM, `00:0c:29` / `00:50:56` = VMware, `02:42` = Docker.
- `ff:ff:ff:ff:ff:ff` = broadcast.
- Si la MAC es una **passphrase**, probá el formato exacto que sugiera el enunciado (minúsculas, mayúsculas, con `:`).
  `echo 08:00:27:AE:CB:6A | tr 'A-F' 'a-f'` · `echo 08:00:27:ae:cb:6a | tr 'a-f' 'A-F'` · `echo 08:00:27:ae:cb:6a | tr -d ':'`

### IP de una MAC (al revés)
~~~bash
ip neigh | grep -i 08:00:27:ae:cb:6a
sudo nmap -sn 192.168.0.0/24 | grep -i -B2 08:00:27:AE:CB:6A    # la línea "Nmap scan report for IP" está 2 arriba
~~~

---

## 3. Configurar IP y rutas

### IP (temporal, se pierde al reiniciar)
| Comando | Qué hace |
|---|---|
| `sudo ip addr add 192.168.100.1/24 dev enp0s8` | agrega una IP |
| `sudo ip addr del 192.168.100.1/24 dev enp0s8` | la saca |
| `sudo ip addr flush dev enp0s8` | saca todas |
| `sudo ip link set enp0s8 up` / `down` | prende / apaga la interfaz |
| `sudo ip link set dev enp0s8 address 02:11:22:33:44:55` | **cambia la MAC** (con la interfaz `down`) |
| `sudo dhclient -v enp0s3` | pide IP por DHCP (muestra DISCOVER/OFFER/REQUEST/ACK) |
| `sudo dhclient -r enp0s3` | suelta la IP |
| `sudo nmcli dev reapply enp0s3` / `nmcli con up NOMBRE` | con NetworkManager |

### IP permanente (netplan, Ubuntu)
~~~yaml
# /etc/netplan/01-red.yaml
network:
  version: 2
  ethernets:
    enp0s8:
      addresses: [192.168.100.1/24]
      routes:
        - to: 10.0.0.0/24
          via: 192.168.100.254
      nameservers:
        addresses: [8.8.8.8]
    enp0s3:
      dhcp4: true
~~~
`sudo netplan apply` (o `sudo netplan try`). Permisos: `sudo chmod 600 /etc/netplan/01-red.yaml`.

### Rutas
| Comando | Qué hace |
|---|---|
| `sudo ip route add 10.0.0.0/24 via 192.168.50.250` | para llegar a la red 10.0.0.0/24, mandar a ese gateway |
| `sudo ip route add 10.0.0.5 via 192.168.50.250` | ruta a un solo host (/32) |
| `sudo ip route add 10.0.0.0/24 dev enp0s8` | red directamente conectada por esa interfaz |
| `sudo ip route del 10.0.0.0/24` | borrar |
| `sudo ip route replace default via 192.168.0.1` | cambiar el gateway por defecto |
| `ip route get 10.0.0.5` | verificar por dónde sale |
| `sudo route add -net 10.0.0.0/24 gw 192.168.50.250` | equivalente viejo |

- El `via` (gateway) tiene que estar **en tu misma red**; si no: `Nexthop has invalid gateway`.
- Se escribe la **red** (`10.0.0.0/24`), no una IP suelta con máscara (`10.0.0.5/24` da `Invalid prefix for given prefix length`).
- Para que el **otro lado** te responda, el gateway tiene que saber volver (ruta de vuelta) o hacer NAT.

### Tu máquina como router / NAT
~~~bash
sudo sysctl -w net.ipv4.ip_forward=1                        # reenviar paquetes entre interfaces
sudo iptables -t nat -A POSTROUTING -o enp0s3 -j MASQUERADE # NAT hacia la interfaz con internet
sudo iptables -t nat -L -n -v                               # ver
~~~

---

## 4. Diagnóstico

| Comando | Para qué |
|---|---|
| `ping -c 3 IP` | ¿responde? (ICMP puede estar bloqueado: no responde ≠ no existe) |
| `ping -c 1 -W 1 IP` | timeout corto |
| `ping -I enp0s8 IP` | salir por una interfaz concreta |
| `traceroute -n IP` | **routers que intervienen** (saltos), sin resolver nombres |
| `traceroute -n -I IP` / `-T -p 80` | con ICMP / TCP (si UDP está filtrado) |
| `tracepath -n IP` | parecido, sin root |
| `mtr -n -r -c 5 IP` | traceroute + estadística |
| `ss -tlnp` / `ss -ulnp` | qué escucha en TCP / UDP (con proceso) |
| `ss -tnp` | conexiones TCP establecidas |
| `nc -zv IP 80` | ¿está abierto ese puerto? |
| `curl -v http://IP/` | ¿responde HTTP? |
| `sudo tcpdump -ni enp0s8` | ver tráfico en vivo |
| `sudo tcpdump -ni enp0s8 port 67 or port 68` | ver DHCP |
| `sudo tcpdump -ni enp0s8 arp` | ver ARP |
| `sudo tcpdump -ni any -w cap.pcap` | grabar para abrir con Wireshark/tshark |

### Leer `traceroute`
~~~text
 1  192.168.50.250  0.4 ms      ← primer router (tu gateway)
 2  10.0.0.1        0.9 ms      ← segundo router
 3  10.0.0.77       1.2 ms      ← destino
 4  * * *                       ← no responde (filtra ICMP/UDP), no significa que no exista
~~~
Cada línea con IP antes del destino es un **router que interviene**.

---

## 5. nmap

| Comando | Qué hace |
|---|---|
| `sudo nmap -sn 192.168.0.0/24` | **qué hosts están vivos** (sin escanear puertos); en la red local muestra MAC |
| `nmap -sn -n 10.0.0.0/24` | idem sin resolver nombres (más rápido) |
| `nmap IP` | 1000 puertos TCP más comunes |
| `nmap -p 22,80,443 IP` / `-p 1-65535` / `-p-` | puertos específicos / todos |
| `nmap --top-ports 100 IP` | los 100 más comunes |
| `nmap -sV IP` | **versión** del servicio de cada puerto ("servicios expuestos") |
| `sudo nmap -O IP` | sistema operativo |
| `sudo nmap -sU -p 53,67,161 IP` | puertos **UDP** |
| `nmap -Pn IP` | no hace ping antes (si el host bloquea ICMP y nmap dice "host down") |
| `nmap -A IP` | -sV + -O + scripts + traceroute |
| `nmap --traceroute IP` | traceroute con nmap |
| `sudo nmap --script broadcast-dhcp-discover -e enp0s8` | ¿hay un servidor DHCP? ¿qué ofrece? |
| `… --script-args broadcast-dhcp-discover.mac=08:00:27:AE:CB:6A` | qué le ofrecería a esa MAC (no toma la IP) |
| `nmap --script http-title -p 80 IP` | título de la página |
| `nmap -oN salida.txt …` | guardar resultado |

### Estados de un puerto
| Estado | Significa |
|---|---|
| `open` | hay un servicio escuchando |
| `closed` | se llega, pero no hay nada (RST) |
| `filtered` | un firewall no deja saber (no responde) |
| `open\|filtered` | típico en UDP: sin respuesta |

`WARNING: No targets were specified, so 0 hosts scanned.` con un script `broadcast-*` **no es error**: el resultado está arriba.

---

## 6. Subredes (rápido)

| Máscara | /n | Hosts útiles | Ejemplo red / broadcast |
|---|---|---|---|
| 255.0.0.0 | /8 | 16.777.214 | 10.0.0.0 / 10.255.255.255 |
| 255.255.0.0 | /16 | 65.534 | 172.16.0.0 / 172.16.255.255 |
| 255.255.255.0 | /24 | 254 | 192.168.0.0 / 192.168.0.255 |
| 255.255.255.128 | /25 | 126 | .0–.127 / .128–.255 |
| 255.255.255.192 | /26 | 62 | .0, .64, .128, .192 |
| 255.255.255.224 | /27 | 30 | saltos de 32 |
| 255.255.255.240 | /28 | 14 | saltos de 16 |
| 255.255.255.252 | /30 | 2 | enlaces punto a punto |
| 255.255.255.255 | /32 | 1 | un solo host |

Hosts útiles = 2^(32−n) − 2 (red y broadcast). Calcular: `ipcalc 192.168.0.10/26`.
Privadas: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`. Link-local: `169.254.0.0/16` (= **no consiguió DHCP**). Loopback: `127.0.0.0/8`.

---

## 7. DHCP

### Cómo funciona (DORA)
| Paso | Quién → quién | Qué |
|---|---|---|
| **D**ISCOVER | cliente (0.0.0.0:68) → broadcast (255.255.255.255:67) | "¿hay un servidor DHCP?" (lleva la MAC del cliente) |
| **O**FFER | servidor:67 → cliente:68 | "te ofrezco esta IP, máscara, gateway, DNS, tiempo" |
| **R**EQUEST | cliente → broadcast | "acepto la oferta de este servidor" |
| **A**CK | servidor → cliente | "confirmado, es tuya por X segundos" |
| NAK | servidor → cliente | "esa IP no te corresponde, pedí de nuevo" |
| RELEASE | cliente → servidor | "devuelvo la IP" |

UDP **67** (servidor) y **68** (cliente). El servidor identifica al cliente por la **MAC**.

### Servidor (isc-dhcp-server)
~~~bash
sudo apt install -y isc-dhcp-server
sudo ip addr add 192.168.100.1/24 dev enp0s8          # el server necesita IP DENTRO de la subred que sirve
sudo nano /etc/default/isc-dhcp-server                # INTERFACESv4="enp0s8"
sudo nano /etc/dhcp/dhcpd.conf
~~~
~~~conf
ddns-update-style none;
authoritative;
default-lease-time 600;
max-lease-time 7200;

subnet 192.168.100.0 netmask 255.255.255.0 {
  range 192.168.100.11 192.168.100.200;              # IPs dinámicas
  option routers 192.168.100.1;                      # gateway que recibe el cliente
  option subnet-mask 255.255.255.0;
  option broadcast-address 192.168.100.255;
  option domain-name-servers 8.8.8.8, 8.8.4.4;       # separados por COMA
  option domain-name "protos.lab";
}

host impresora {                                     # IP fija por MAC (reserva)
  hardware ethernet 08:00:27:AE:CB:6A;
  fixed-address 192.168.100.10;                      # FUERA del range
}
~~~
~~~bash
sudo dhcpd -t -cf /etc/dhcp/dhcpd.conf               # validar
sudo systemctl restart isc-dhcp-server
systemctl status isc-dhcp-server --no-pager
sudo journalctl -u isc-dhcp-server -n 50 --no-pager  # errores
cat /var/lib/dhcp/dhcpd.leases                        # IPs entregadas (IP ↔ MAC)
~~~

### Opciones que te pueden pedir
| Pide… | Línea |
|---|---|
| rango de IPs | `range A B;` |
| gateway / router | `option routers IP;` |
| DNS | `option domain-name-servers IP1, IP2;` |
| dominio de búsqueda | `option domain-name "x.lab";` |
| tiempo de préstamo | `default-lease-time 600; max-lease-time 7200;` (segundos) |
| IP fija a un equipo | `host nombre { hardware ethernet MAC; fixed-address IP; }` |
| servidor NTP | `option ntp-servers IP;` |
| nombre al equipo | `option host-name "impresora";` (dentro de `host`) |
| arrancar por red (PXE) | `next-server IP; filename "pxelinux.0";` |
| no dar IP a desconocidos | `deny unknown-clients;` (dentro de un `pool`) |
| varias redes | un `subnet { }` por red (y una interfaz con IP en cada una) |

### Probar como cliente
~~~bash
sudo nmap --script broadcast-dhcp-discover -e enp0s8                       # oferta para cualquier MAC
sudo nmap --script broadcast-dhcp-discover --script-args broadcast-dhcp-discover.mac=08:00:27:AE:CB:6A -e enp0s8
sudo dhclient -v enp0s8                                                    # pedir IP de verdad (desde otra VM)
sudo tcpdump -ni enp0s8 -vv port 67 or port 68                             # ver DORA
~~~

### Errores típicos
| Síntoma | Causa | Arreglo |
|---|---|---|
| `No subnet declaration for enp0s8 (x.x.x.x)` / `Not configured to listen on any interfaces!` | la interfaz no tiene IP dentro de la subred, o `INTERFACESv4` mal | `ip addr add` en esa red; revisar `/etc/default/isc-dhcp-server` |
| `Failed to start` sin más | error de sintaxis | `dhcpd -t`, `journalctl` |
| `expecting semicolon` | falta `;` | — |
| la impresora no recibe la `.10` | la `.10` está dentro del `range` y se la dio a otro, o MAC mal escrita | `fixed-address` fuera del rango; revisar MAC |
| el cliente recibe `169.254.x.x` | no llegó ningún OFFER | misma red (VirtualBox: misma "red interna"), server corriendo, firewall |
| el cliente recibe IP de **otra** red | hay otro DHCP (el de VirtualBox NAT) | usar red interna; `-e` correcto en nmap |
| `nmap` no muestra oferta | interfaz equivocada o sin root | `sudo`, `-e IFACE` |

---

## 8. VirtualBox: qué modo de red

| Modo | La VM… | Usar para |
|---|---|---|
| **NAT** | sale a internet, nadie de afuera la ve; IP 10.0.2.15, DHCP de VirtualBox | instalar paquetes, curl/ssh hacia afuera |
| **Bridge (puente)** | está en la **misma red física** que tu PC (IP del router de la facultad) | llegar a servidores/gateways de la red del laboratorio |
| **Red interna** | solo se ve con otras VMs en la misma red interna, **sin DHCP** | montar tu propio DHCP, laboratorios aislados |
| **Solo anfitrión** | se ve con tu PC (192.168.56.x) | probar desde tu PC hacia la VM |

Después de cambiar el modo: `sudo dhclient -r enp0s3; sudo dhclient -v enp0s3` (o reiniciar la interfaz) y `ip a` para ver la IP nueva.

---

## 9. El enunciado dice → qué hacer

| El enunciado dice… | Hacés |
|---|---|
| "la MAC de X" / "la passphrase es la MAC de X" | `ping -c1 X; ip neigh show X` (misma red) o `sudo nmap -sn X`; si viene de una captura, tshark ARP/DHCP |
| "qué IP tiene la MAC M" | `ip neigh \| grep -i M`, `sudo nmap -sn RED/24`, leases de DHCP |
| "su IP / su gateway / su DNS" | `ip a`, `ip route`, `resolvectl status` |
| "otra red detrás del gateway G" | `sudo ip route add RED/n via G` |
| "descubra el servidor en la red R" | `sudo nmap -sn R` (y comparar antes/después) |
| "qué servicios expone" | `nmap -sV IP` (+ `-p-` si hace falta) |
| "qué routers intervienen" | `traceroute -n IP` |
| "acceda por HTTP" | `curl -i http://IP:PUERTO/` |
| "instale un servidor DHCP en la red R" | isc-dhcp-server, IP del server en R, `INTERFACESv4`, `subnet` |
| "la impresora (MAC M) siempre con la IP I" | `host impresora { hardware ethernet M; fixed-address I; }` con I fuera del `range` |
| "los clientes deben recibir DNS D" | `option domain-name-servers D;` |
| "y gateway G" | `option routers G;` |
| "verifique con nmap broadcast-dhcp-discover" | `sudo nmap --script broadcast-dhcp-discover [--script-args …mac=M] -e IFACE` |
| "misma red que el laboratorio" | VirtualBox en **Bridge** |
| "red aislada para el DHCP" | VirtualBox **red interna** |
| "una IP por DHCP" en una captura | tshark `dhcp.ip.your` en el ACK |
| "el host no tiene internet / sin NAT" | túnel SSH `-R` (ver [../ssh/cheatsheet-ssh.md](../ssh/cheatsheet-ssh.md)) o NAT con iptables |

---

## 10. Qué decir en el video
«Con `ip a` y `ip route` muestro mi IP y gateway. Para la otra red agrego una ruta estática con `ip route add RED via GATEWAY` y lo verifico con `ip route get`. La MAC de un equipo la saco de la tabla ARP (`ip neigh`) después de un ping, porque ARP solo funciona dentro de la red local. Para DHCP, el servidor tiene IP en la subred que atiende, defino el rango y una reserva por MAC fuera del rango, y lo verifico con el script `broadcast-dhcp-discover` de nmap haciéndome pasar por esa MAC.»
