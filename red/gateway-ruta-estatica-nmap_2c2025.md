# Protocolos — 2C 2025, Ejercicio II: servidor detrás de un gateway

## Consigna (textual)
El host en **192.168.50.250** es el gateway de la red **10.0.0.0/24**. Sabe que existe un servidor distinto al gateway en esta red, pero no está seguro de qué dirección IP tiene asignada. Descubra la dirección del servidor, y los servicios que tiene expuesto el host.

Debe mostrar:
- El resultado de acceder vía HTTP a dicho servidor.
- Los routers que intervienen en esta comunicación.

**Nota:** de usar una VM, el adaptador de red debe estar en modo **Bridge/Puente** conectado a la red abierta.

> **Todo este documento se probó** en una red simulada con la misma topología (namespaces de Linux): una "VM" en 192.168.50.10 con su propio gateway por defecto, el gateway A (192.168.50.250 / 10.0.0.1, con forwarding) y un servidor escondido en 10.0.0.77 con HTTP en el 80 y SSH en el 2222. Las salidas de abajo son reales de esa prueba; **en el parcial las IPs y puertos del servidor van a ser otros.**

---

## La idea en un dibujo
~~~text
Mi VM 192.168.50.X ──(red 192.168.50.0/24)── A: 192.168.50.250
                                              A: 10.0.0.1 ──(red 10.0.0.0/24)── servidor 10.0.0.?
~~~
Mi VM no conoce la red `10.0.0.0/24`. Sin hacer nada, los paquetes para `10.0.0.x` se van por la **ruta por defecto** (mi gateway de siempre), que no sabe llegar → timeout. Hay que decirle: "para `10.0.0.0/24`, mandalo a `192.168.50.250`". Eso es una **ruta estática**.

---

## ⭐ RECETA PARA EL PARCIAL

### Paso 0 — VirtualBox
Adaptador de la VM en **Adaptador puente (Bridge)** sobre la interfaz conectada a la red del laboratorio indicada. En **NAT no funciona**: la VM queda en `10.0.2.x` y no ve a `192.168.50.250`.

### Paso 1 — Comprobar que estoy en la red correcta
~~~bash
ip -br addr
ip route
ping -c 3 192.168.50.250
~~~
- `ip -br addr`: mis interfaces y sus IPs en una línea (`-br` = brief). Tengo que tener una IP `192.168.50.X/24` en alguna interfaz.
- `ip route`: mi tabla de rutas. Vas a ver `default via ...` y `192.168.50.0/24 dev ...`. **No** hay nada para `10.0.0.0/24`.
- `ping -c 3`: manda 3 pings al gateway A. Si responde, estoy en la misma red que él.

Salida de la prueba:
~~~text
lab0  UP  192.168.50.10/24
default via 192.168.50.1 dev lab0
192.168.50.0/24 dev lab0 proto kernel scope link src 192.168.50.10
64 bytes from 192.168.50.250: icmp_seq=1 ttl=64 time=0.089 ms
~~~
Si no tengo IP en `192.168.50.0/24`: revisar el modo Bridge. (Si la red del laboratorio no reparte IPs por DHCP, se puede poner una a mano con `sudo ip addr add 192.168.50.X/24 dev IFACE`, eligiendo una X libre.)

### Paso 2 — Mostrar que ANTES no llego
~~~bash
ip route get 10.0.0.1
ping -c 2 -W 1 10.0.0.1
~~~
- `ip route get IP`: dice por dónde saldría un paquete hacia esa IP, **sin mandarlo**. Antes de la ruta muestra `via <mi gateway por defecto>`: o sea, se iría por el camino equivocado.
- El ping falla (`100% packet loss`). Esto deja claro en el video para qué es el paso siguiente.

Salida de la prueba: `10.0.0.77 via 192.168.50.1 dev lab0` y `100% packet loss`.

### Paso 3 — Agregar la ruta estática
~~~bash
sudo ip route add 10.0.0.0/24 via 192.168.50.250
ip route
ip route get 10.0.0.1
~~~
- `ip route add 10.0.0.0/24`: agrega una ruta para **toda** la red `10.0.0.0/24` (se escribe la red, no una IP suelta).
- `via 192.168.50.250`: el próximo salto es A. Tiene que estar en mi misma red (si no, da `Nexthop has invalid gateway`).
- `sudo`: modificar rutas requiere root.

Salida de la prueba:
~~~text
10.0.0.0/24 via 192.168.50.250 dev lab0          ← la ruta nueva
10.0.0.77 via 192.168.50.250 dev lab0 src 192.168.50.10   ← ip route get: ahora sale por A
~~~
Forma equivalente con net-tools (probada, mismo resultado):
~~~bash
sudo route add -net 10.0.0.0/24 gw 192.168.50.250
route -n
~~~
En `route -n` la línea es `10.0.0.0  192.168.50.250  255.255.255.0  UG`: **U** = activa, **G** = va por un gateway.

Si lo corrés dos veces: `RTNETLINK answers: File exists` → la ruta ya estaba, no es un problema.

### Paso 4 — Descubrir el servidor
~~~bash
sudo nmap -sn 10.0.0.0/24
~~~
- `-sn`: solo descubre qué hosts están vivos, **no** escanea puertos (rápido).
- `10.0.0.0/24`: las 256 direcciones de la red.
- Con `sudo`, nmap usa varias sondas (ping ICMP, TCP a 80 y 443, etc.).

Salida de la prueba:
~~~text
Nmap scan report for 10.0.0.1
Host is up (0.00015s latency).
Nmap scan report for 10.0.0.77
Host is up (0.000090s latency).
Nmap done: 256 IP addresses (2 hosts up) scanned in 16.98 seconds
~~~
**Cuál es el servidor:** `10.0.0.1` es **A** (su pata en la red 10, la que usa como gateway). El enunciado dice "un servidor **distinto al gateway**" → el servidor es **el otro**: `10.0.0.77` en la prueba. Si aparecen varios, escanear cada uno en el paso 5.

Si `-sn` no encuentra nada aparte de A (el servidor puede no responder a ping):
~~~bash
sudo nmap -Pn --open -p 22,80,443,8000,8080 10.0.0.0/24
~~~
`-Pn` = no hacer ping previo, probar igual; `--open` = mostrar solo puertos abiertos.

### Paso 5 — Servicios expuestos (con `-sV`)
~~~bash
sudo nmap -sS -sV -p- 10.0.0.77
~~~
- `-sS`: escaneo SYN (manda SYN; si vuelve SYN/ACK, el puerto está abierto). Requiere sudo.
- `-sV`: **conecta y pregunta** qué servicio y versión hay. **Usalo**: sin `-sV`, nmap solo adivina el nombre por el número de puerto.
- `-p-`: los 65535 puertos, no solo los 1000 más comunes (el servidor puede tener algo en un puerto raro).

Lo que pasó en la prueba, y por qué importa `-sV`:
~~~text
sin -sV:   2222/tcp open  EtherNetIP-1        ← nombre adivinado por la tabla de puertos: INCORRECTO
con -sV:   80/tcp   open  http    SimpleHTTPServer 0.6 (Python 3.13.17)
           2222/tcp open  ssh     OpenSSH 9.6 (protocol 2.0)   ← lo que realmente es
~~~
**Respuesta "servicios expuestos":** HTTP en el 80 y SSH en el 2222 (en la prueba). Reportar la tabla de `-sV` completa.

### Paso 6 — Acceder por HTTP
~~~bash
curl -i http://10.0.0.77
~~~
- `-i`: muestra también la línea de estado y los headers (se ve el `200 OK` y qué servidor responde).
- Si el HTTP está en otro puerto: `curl -i http://10.0.0.77:PUERTO`.

Salida de la prueba:
~~~text
HTTP/1.0 200 OK
Server: SimpleHTTP/0.6 Python/3.13.17
...
Encontraste el servidor escondido (10.0.0.77)
~~~
Si hay más de un puerto HTTP en el `-sV`, hacer `curl` a cada uno.

### Paso 7 — Routers que intervienen
~~~bash
traceroute -n 10.0.0.77
~~~
- Manda paquetes con TTL 1, 2, 3…; cada router que descarta uno por TTL agotado responde, y así aparece en la lista.
- `-n`: muestra IPs sin intentar resolver nombres (más rápido y sin esperas).

Salida de la prueba:
~~~text
traceroute to 10.0.0.77 (10.0.0.77), 30 hops max, 60 byte packets
 1  192.168.50.250  0.029 ms  0.004 ms  0.004 ms     ← router: A
 2  10.0.0.77       0.011 ms  0.005 ms  0.005 ms     ← destino: el servidor
~~~
**Respuesta "routers que intervienen":** `192.168.50.250` (A). El último salto es el servidor, **no** es un router.

Si aparecen `* * *`: algún equipo no contesta a las sondas UDP por defecto. Probar `sudo traceroute -n -I 10.0.0.77` (ICMP, probado: mismo resultado) o `sudo traceroute -n -T -p 80 10.0.0.77` (TCP al puerto HTTP).

### Para el video
"Mi VM no conocía la red 10.0.0.0/24, así que agregué una ruta estática con `ip route add 10.0.0.0/24 via 192.168.50.250`, usando como próximo salto al gateway. Con `nmap -sn` encontré dos hosts: 10.0.0.1 es la interfaz interna del gateway y el otro es el servidor. Con `nmap -sV -p-` vi los servicios que expone, accedí por HTTP con curl, y con traceroute se ve que el único router en el camino es 192.168.50.250."

### Al terminar
~~~bash
sudo ip route del 10.0.0.0/24 via 192.168.50.250
~~~
La ruta tampoco sobrevive a un reinicio: `ip route add` no es persistente.

---

## Si algo falla
| Ves | Causa | Arreglo |
|---|---|---|
| mi IP es `10.0.2.x` | VM en NAT | VirtualBox → Adaptador puente |
| `ping 192.168.50.250` sin respuesta | no estoy en esa red | revisar Bridge, la interfaz elegida y mi IP |
| `Nexthop has invalid gateway` al agregar la ruta | el `via` no está en mi red | verificar que tengo IP `192.168.50.X/24` |
| `RTNETLINK answers: File exists` | la ruta ya existía | nada; seguir |
| `Network is unreachable` | no hay ninguna ruta (ni default) hacia ese destino | agregar la ruta del paso 3 |
| `ip route get` sigue mostrando mi default | la ruta no se agregó (¿faltó sudo?) | repetir paso 3 y mirar `ip route` |
| `nmap -sn` solo muestra 10.0.0.1 | el servidor no responde a ping | `sudo nmap -Pn --open -p 22,80,443,8000,8080 10.0.0.0/24` |
| `Host seems down` en el paso 5 | ídem | agregar `-Pn` |
| nmap muestra un nombre de servicio raro | sin `-sV` solo adivina por número | agregar `-sV` |
| `curl: (7) Failed to connect` | puerto equivocado | usar el puerto HTTP que dio `-sV` |
| `curl: (52) Empty reply from server` | ese puerto no habla HTTP | probar otro puerto del `-sV` |
| traceroute con `* * *` | filtran UDP | `-I` (ICMP) o `-T -p 80` (TCP) |

## Variantes
| Si cambia... | Tocás |
|---|---|
| otra red o gateway | `ip route add RED/MASCARA via GATEWAY` |
| máscara distinta (ej. /16) | `ip route add 10.0.0.0/16 via ...` y `nmap -sn 10.0.0.0/16` (más lento: acotar si se puede) |
| te dan la IP del servidor | saltear el paso 4 |
| piden solo puertos TCP abiertos | `sudo nmap -sS -p- IP` (o `-sT` sin sudo) |
| piden también UDP | `sudo nmap -sU --top-ports 50 IP` (UDP es lento) |
| el HTTP pide un Host | `curl -H "Host: nombre" http://IP` |
| hay dos routers en el medio | traceroute muestra 3 saltos: los dos primeros son los routers |
| ruta que use una interfaz específica | `ip route add 10.0.0.0/24 via 192.168.50.250 dev IFACE` |
