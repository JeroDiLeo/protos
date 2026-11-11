# LabProtos2025-2C · Ejercicio II · Ruteo y descubrimiento

## Cómo interpretar el enunciado

La consigna da el gateway `192.168.50.250` y dice que detrás está la red `10.0.0.0/24`. Dentro de esa red hay un servidor cuya IP hay que descubrir. La entrega pide mostrar cómo llegamos a la red, qué hosts responden, qué servicios ofrece el servidor, qué devuelve por HTTP y qué routers atraviesa la comunicación.

**Primero configuramos un camino a toda la red.** Eso permite descubrir después cuál de sus IP pertenece al servidor.

## 1. Leer las rutas que ya tiene la máquina

Salida real desde el contenedor `alumno`.

```text
root@alumno:~# ip route
default via 192.168.50.1 dev eth1
192.168.50.0/24 dev eth1 proto kernel scope link src 192.168.50.20
192.168.100.0/24 dev eth0 proto kernel scope link src 192.168.100.1
root@alumno:~# ip route get 192.168.50.250
192.168.50.250 dev eth1 src 192.168.50.20 uid 0
    cache
root@alumno:~# ip route get 10.0.0.1
10.0.0.1 via 192.168.50.1 dev eth1 src 192.168.50.20 uid 0
    cache
```

| Qué leés | Qué significa |
|---|---|
| `default via 192.168.50.1 dev eth1` | Si el destino no coincide con una ruta más específica, el paquete va al router `.50.1` por `eth1`. |
| `192.168.50.0/24 dev eth1 ... scope link` | La subred está directamente conectada a `eth1`. Por eso `192.168.50.250` es alcanzable como siguiente salto. |
| `192.168.100.0/24 dev eth0` | Es la red interna que usamos para DHCP en el Ejercicio I. |
| `src 192.168.50.20` | Es la dirección de origen que Linux elige para enviar por `eth1`. |

`ip route` muestra la tabla. `ip route get` hace una consulta de esa tabla para una IP concreta. Elegimos `10.0.0.1` como ejemplo de destino dentro de la subred. La consulta muestra la decisión local de Linux y se puede hacer aunque todavía no sepas qué IP tiene un servidor activo. Antes del cambio, esa decisión era usar `192.168.50.1`. [Manual de ip route](https://man7.org/linux/man-pages/man8/ip-route.8.html)

## 2. Agregar una ruta específica

```bash
ip route add 10.0.0.0/24 via 192.168.50.250 dev eth1
```

- `ip route add` agrega una ruta.
- `10.0.0.0/24` es el conjunto de destinos al que se aplica. El `/24` viene de la consigna. Son los primeros 24 bits de la IPv4, equivalentes a la máscara `255.255.255.0`. En esta red quedan fijos `10.0.0` y varía el último octeto.
- `via 192.168.50.250` especifica el siguiente salto, el gateway que indica el enunciado.
- `dev eth1` explicita la interfaz de salida. Es la que conecta al contenedor con la red del gateway.

Linux usa el prefijo más específico que coincide con el destino. Para `10.0.0.1`, la nueva ruta `/24` tiene prioridad sobre la ruta por defecto `/0`. Para comprobar el cambio repetimos la misma consulta.

```text
root@alumno:~# ip route get 10.0.0.1
10.0.0.1 via 192.168.50.250 dev eth1 src 192.168.50.20 uid 0
    cache
```

Ahora `via` muestra la `.250`. Con esto confirmamos la decisión de ruteo. En el siguiente paso mandamos tráfico para comprobar quién responde.

## 3. Descubrir los hosts activos

```text
root@alumno:~# nmap -sn -n 10.0.0.0/24
Starting Nmap 7.94SVN ( https://nmap.org ) at 2026-11-11 18:04 UTC
Nmap scan report for 10.0.0.137
Host is up (0.000076s latency).
Nmap scan report for 10.0.0.254
Host is up (0.00034s latency).
Nmap done: 256 IP addresses (2 hosts up) scanned in 56.15 seconds
```

`-sn` hace descubrimiento de hosts y omite el escaneo de puertos. `-n` evita resolver nombres. Le pasamos la subred entera porque la IP del servidor todavía era desconocida. Nmap encontró dos IP que respondieron, `10.0.0.137` y `10.0.0.254`. La repetición con `nmap -sn 10.0.0.0/24` devolvió los mismos dos hosts. [Descubrimiento de hosts en Nmap](https://nmap.org/book/man-host-discovery.html)

## 4. Identificar los servicios en las dos IP

```text
root@alumno:~# nmap -sV -n 10.0.0.137 10.0.0.254
Starting Nmap 7.94SVN ( https://nmap.org ) at 2026-11-11 18:07 UTC
Nmap scan report for 10.0.0.137
Host is up (0.000057s latency).
Not shown: 998 closed tcp ports (reset)
PORT     STATE SERVICE VERSION
22/tcp   open  ssh     OpenSSH 9.6p1 Ubuntu 3ubuntu13.20 (Ubuntu Linux; protocol 2.0)
8080/tcp open  http    nginx 1.24.0 (Ubuntu)
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Nmap scan report for 10.0.0.254
Host is up (0.000046s latency).
All 1000 scanned ports on 10.0.0.254 are in ignored states.
Not shown: 1000 closed tcp ports (reset)

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 2 IP addresses (2 hosts up) scanned in 7.03 seconds
```

Sacamos `-sn` para que Nmap examine puertos. `-sV` intenta identificar el servicio y su versión en los puertos abiertos. Acotamos los destinos a las dos IP que respondieron. **`10.0.0.137` expone SSH en `22/tcp` y HTTP en `8080/tcp`**. En `10.0.0.254` los 1000 puertos TCP escaneados estaban cerrados. La detección de HTTP en la `.137` determina qué IP y puerto usar con `curl`. [Detección de versiones en Nmap](https://nmap.org/book/man-version-detection.html)

## 5. Acceder por HTTP

```text
root@alumno:~# curl -i http://10.0.0.137:8080/
HTTP/1.1 200 OK
Server: nginx/1.24.0 (Ubuntu)
Date: Wed, 11 Nov 2026 18:08:47 GMT
Content-Type: text/html
Content-Length: 130
Connection: keep-alive

<html>
  <body>
    <h1>Servidor encontrado</h1>
    <p>Llegaste a la red 10.0.0.0/24 a traves del gateway.</p>
  </body>
</html>
```

`http://` indica el protocolo, `:8080` selecciona el puerto que detectó Nmap y `/` pide la página raíz. `-i` muestra la línea de estado, los encabezados y el cuerpo. El `200 OK` y el HTML «Servidor encontrado» son la evidencia de acceso que pide la consigna.

## 6. Mostrar qué routers atraviesa la comunicación

`traceroute` envía paquetes de prueba, llamados **sondas**, y muestra qué equipos responden a lo largo del camino hacia una IP. Lo usamos porque el enunciado pide **mostrar los routers que intervienen**.

```text
root@alumno:~# traceroute -n -T -p 8080 10.0.0.137
traceroute to 10.0.0.137 (10.0.0.137), 30 hops max, 60 byte packets
 1  192.168.50.250  9.363 ms  0.125 ms  0.060 ms
 2  10.0.0.137  0.114 ms * *
```

### Qué hace cada opción

| Parte del comando | Qué significa en esta prueba |
|---|---|
| `-n` | Muestra las IP de los saltos directamente. Así podés compararlas con el gateway y el servidor que ya identificaste. |
| `-T` | Usa sondas TCP. |
| `-p 8080` | Envía las sondas TCP al puerto del servicio HTTP que encontró Nmap. |
| `10.0.0.137` | Es la IP final a la que queremos llegar. |

### Cómo descubre los saltos

Cada sonda lleva un **TTL**, un contador que cada router reduce al reenviar el paquete. Si llega a cero, el router descarta la sonda y puede avisarle al origen con un mensaje ICMP *Time Exceeded*. `traceroute` empieza con TTL 1 y lo va aumentando para descubrir equipos más lejos. En nuestro lab, con TTL 1 la sonda vence en `192.168.50.250` y su respuesta permite identificar el primer salto. Con TTL 2 la sonda puede pasar por ese router y llegar a `10.0.0.137`. [Manual de traceroute](https://man7.org/linux/man-pages/man8/traceroute.8.html)

### Cómo leer nuestra salida

| Fila | Qué respondieron las sondas | Qué entregás |
|---|---|---|
| `1  192.168.50.250  9.363 ms  0.125 ms  0.060 ms` | El gateway respondió a las tres sondas. Cada tiempo mide la ida y vuelta desde `alumno` hasta el equipo que respondió. | `192.168.50.250` es el router intermedio. |
| `2  10.0.0.137  0.114 ms * *` | Una sonda obtuvo respuesta del servidor en `0.114 ms`. Cada `*` indica que otra sonda quedó sin respuesta dentro del tiempo de espera. | `10.0.0.137` es el destino. La traza tiene dos saltos y un solo router intermedio. |

`10.0.0.254`, que apareció en el escaneo, es la interfaz interna del **mismo gateway**, según `gateway/entrypoint.sh`. En la traza respondió por su dirección del lado de `alumno`, `192.168.50.250`.

Cada salida responde una pregunta distinta del ejercicio. `ip route get` muestra **qué siguiente salto eligió Linux**, `traceroute` muestra **quién respondió en el camino** y `curl` muestra **qué devolvió el servicio HTTP**. Para justificar la entrega, usá la fila `1` de la traza para identificar al router y el `200 OK` de `curl` para demostrar el acceso al servicio.
