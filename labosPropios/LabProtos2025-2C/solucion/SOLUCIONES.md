# Soluciones — Parcial Práctico 2Q2025 (en el lab)

Spoilers. Todo se corre dentro de tu VM (`make ws`). Los datos salen del **enunciado real** (`Parcial Práctico - 2Q2025.pdf`).

> **Diferencias con el apunte `2025 2C.md`:**
> - **Ej I:** el apunte transcribió mal la impresora. El enunciado real dice MAC `08:00:27:AE:C8:6A` e IP `192.168.100.8`, que queda **fuera** del rango 10–200, así que el `range` va completo de `.10` a `.200`. El apunte dice `CB` y `.10`, y por eso tuvo que achicar el rango a 11–200.
> - **Ej III:** en el original el MX es `mail`, sin punto final.
> - **Ej IV:** el original pide **HTTPS** en `https://seguro.protos.foo`. La versión HTTP con `publico.protos.foo` es la del apunte, y en el lab quedó como IV-bis.

---

## Ejercicio I — DHCP

### 1. Identificar la placa interna y darle IP

```bash
ip -br addr
```

```text
lo               UNKNOWN        127.0.0.1/8
eth0@if145       UP             192.168.50.20/24     <- red del lab (la "WiFi"): NO
eth1@if146       UP                                   <- red interna: esta
```

> El nombre puede ser `eth0` o `eth1` según el arranque (Docker no garantiza el orden). Pasa lo mismo que en el parcial con `enp0s8`/`enp0s9`: **mirala siempre** y no la memorices. Abajo uso `<IF>`.

```bash
sudo ip link set <IF> up
sudo ip addr add 192.168.100.1/24 dev <IF>
```

### 2. Interfaz de escucha — `/etc/default/isc-dhcp-server`

```conf
INTERFACESv4="<IF>"
INTERFACESv6=""
```

### 3. `/etc/dhcp/dhcpd.conf`

```conf
ddns-update-style none;
authoritative;

default-lease-time 600;
max-lease-time 7200;

subnet 192.168.100.0 netmask 255.255.255.0 {
  range 192.168.100.10 192.168.100.200;          # punto 3: rango 10-200
  option subnet-mask 255.255.255.0;
  option broadcast-address 192.168.100.255;
  option domain-name-servers 8.8.8.8, 8.8.4.4;   # punto 2 (plural: servers)

  host impresora {                               # punto 1
    hardware ethernet 08:00:27:AE:C8:6A;
    fixed-address 192.168.100.8;
  }
}
```

La IP fija (`.8`) queda fuera del rango dinámico, así que nunca se le entrega a otro cliente.

### 4. Validar y levantar

```bash
sudo dhcpd -t -4 -cf /etc/dhcp/dhcpd.conf
sudo systemctl restart isc-dhcp-server
sudo systemctl status isc-dhcp-server --no-pager     # Active: active (running)
```

### 5. Verificar (comando del enunciado)

```bash
sudo nmap --script broadcast-dhcp-discover \
     --script-args "broadcast-dhcp-discover.mac=AA:BB:CC:DD:EE:FF"
```

```text
| broadcast-dhcp-discover:
|   Response 1 of 1:
|     Interface: eth1
|     IP Offered: 192.168.100.10
|     DHCP Message Type: DHCPOFFER
|     Subnet Mask: 255.255.255.0
|     Domain Name Server: 8.8.8.8, 8.8.4.4
```

Impresora:

```bash
sudo nmap --script broadcast-dhcp-discover \
     --script-args "broadcast-dhcp-discover.mac=08:00:27:AE:C8:6A"
# IP Offered: 192.168.100.8
```

### Errores típicos que el lab reproduce

| Síntoma | Causa |
|---|---|
| `Job for isc-dhcp-server.service failed` + en `journalctl -u isc-dhcp-server`: `No subnet declaration for ethX` / `Not configured to listen on any interfaces!` | La placa no tiene IP en `192.168.100.0/24`, o `INTERFACESv4` apunta a la placa equivocada. |
| `dhcpd -t` falla | Falta un `;`, escribiste `domain-name-server` sin la `s`, o el `range` no pertenece a la `subnet`. |
| La impresora recibe una IP del rango | La MAC está mal escrita: es `C8`, no `CB`. |

---

## Ejercicio II — Servidor detrás del gateway

```bash
route -n                                          # solo conozco 192.168.50.0/24 y la default
sudo route add -net 10.0.0.0/24 gw 192.168.50.250
route -n
```

```text
Destination     Gateway         Genmask         Flags Metric Ref    Use Iface
0.0.0.0         192.168.50.1    0.0.0.0         UG    0      0        0 eth0
10.0.0.0        192.168.50.250  255.255.255.0   UG    0      0        0 eth0
192.168.50.0    0.0.0.0         255.255.255.0   U     0      0        0 eth0
```

Descubrir hosts:

```bash
sudo nmap -sn 10.0.0.0/24
```

```text
Nmap scan report for 10.0.0.137
Nmap scan report for 10.0.0.254
Nmap done: 256 IP addresses (2 hosts up)
```

`10.0.0.254` es la otra placa del gateway (A). El servidor es **`10.0.0.137`**.

Servicios expuestos:

```bash
sudo nmap -sS 10.0.0.137
```

```text
PORT     STATE SERVICE
22/tcp   open  ssh
8080/tcp open  http-proxy
```

Con `-sV`: `22 OpenSSH`, `8080 http nginx`.

Acceso HTTP:

```bash
curl -i http://10.0.0.137:8080
```

```text
HTTP/1.1 200 OK
Server: nginx/1.24.0 (Ubuntu)
...
<h1>Servidor encontrado</h1>
```

Routers que intervienen:

```bash
traceroute -n 10.0.0.137
```

```text
 1  192.168.50.250  ...
 2  10.0.0.137      ...
```

El único router intermedio es **`192.168.50.250`**: el salto 2 ya es el destino.

> Sin la ruta, `curl http://10.0.0.137:8080` no llega, porque el paquete sale por la default `192.168.50.1`, que no conoce esa red. Ese es el sentido del ejercicio.

---

## Ejercicio III — Zona `it.itba.edu.ar`

```bash
systemctl status bind9                         # muestra los errores de carga
curl -s http://protos.foo/zona -o db.it.itba.edu.ar
named-checkzone it.itba.edu.ar db.it.itba.edu.ar
# db.it.itba.edu.ar:21: near 'pampero': bad dotted quad
```

### Errores

1. **SOA, contacto con `@`:** `admin@it.itba.edu.ar.` va como `admin.it.itba.edu.ar.`. En el SOA, la `@` del mail se reemplaza por un punto.
2. **`ns1.it.itba.edu.ar` sin punto final:** es relativo, así que se expande a `ns1.it.itba.edu.ar.it.itba.edu.ar.`. Entonces el NS `ns1.it.itba.edu.ar.` queda sin registro A, lo que se conoce como *glue* faltante. Va `ns1` o `ns1.it.itba.edu.ar.`.
3. **El MX apunta a `mail`, que no existe:** `mail.it.itba.edu.ar` no tiene registro A. Hay que agregar `mail IN A 192.168.70.10`; uso la IP de pampero porque el enunciado no da otra.
4. **`www IN A pampero`:** un registro A lleva una IPv4, no un nombre (de ahí el `bad dotted quad`). Como es un alias, va `www IN CNAME pampero.it.itba.edu.ar.`.
5. **El serial no cambió:** hay que subirlo, por ejemplo a `2025103101`, para que los secundarios detecten el cambio.
6. **Tiempos muy altos para propagar rápido:** el `$TTL` y el Refresh/Negative de 604800 s (una semana) y el Retry de 86400 s demoran la propagación y cachean los errores. Se bajan.

### Zona corregida

```zone
$ORIGIN it.itba.edu.ar.
$TTL 300
@ IN SOA ns1.it.itba.edu.ar. admin.it.itba.edu.ar. (
        2025103101      ; Serial
        300             ; Refresh
        60              ; Retry
        2419200         ; Expire
        300             ; Negative Cache TTL
)
; Name Servers
@       IN NS ns1.it.itba.edu.ar.
; Mail
@       IN MX 10 mail.it.itba.edu.ar.
; Hosts
ns1     IN A 192.168.70.1
pampero IN A 192.168.70.10
mail    IN A 192.168.70.10
; Aliases
www     IN CNAME pampero.it.itba.edu.ar.
correo  IN CNAME pampero.it.itba.edu.ar.
```

```bash
named-checkzone it.itba.edu.ar db.it.itba.edu.ar      # loaded serial 2025103101 / OK
sudo cp db.it.itba.edu.ar /etc/bind/db.it.itba.edu.ar
sudo named-checkconf
sudo systemctl reload bind9

dig @localhost pampero.it.itba.edu.ar A      # 192.168.70.10, flags: qr aa rd ra
dig @localhost www.it.itba.edu.ar A          # CNAME pampero + A 192.168.70.10
dig @localhost it.itba.edu.ar MX             # 10 mail.it.itba.edu.ar.
dig @localhost it.itba.edu.ar SOA            # ... 2025103101 300 60 2419200 300
```

El flag `aa` (*authoritative answer*) muestra que tu BIND es la autoridad de la zona.

---

## Ejercicio IV — `https://seguro.protos.foo`

Arquitectura: `curl https://seguro.protos.foo` → nginx en tu VM (TLS en el puerto 443) → `http://parcial.protos.foo`.

### 1. El backend

```bash
curl http://parcial.protos.foo
# Contenido servido por parcial.protos.foo via HTTP inseguro. ...
curl http://192.168.50.90
# What?   <- el backend elige el sitio por el header Host
```

### 2. Que `seguro.protos.foo` apunte a tu VM

El nombre no existe en el DNS, así que se agrega en `/etc/hosts`:

```bash
echo "127.0.0.1 seguro.protos.foo" | sudo tee -a /etc/hosts
```

### 3. Certificado para `seguro.protos.foo`

```bash
sudo mkdir -p /etc/nginx/tls
sudo openssl req -x509 -newkey rsa:2048 -nodes -days 365 \
  -keyout /etc/nginx/tls/seguro.key -out /etc/nginx/tls/seguro.crt \
  -subj "/CN=seguro.protos.foo" -addext "subjectAltName=DNS:seguro.protos.foo"
```

### 4. Que el sistema confíe en el certificado

Este es el punto que hace que `curl` funcione **sin `-k`**:

```bash
sudo cp /etc/nginx/tls/seguro.crt /usr/local/share/ca-certificates/seguro.protos.foo.crt
sudo update-ca-certificates                       # 1 added
```

### 5. nginx — `/etc/nginx/sites-available/seguro-protos-foo`

```nginx
server {
    listen 443 ssl;
    server_name seguro.protos.foo;

    ssl_certificate     /etc/nginx/tls/seguro.crt;
    ssl_certificate_key /etc/nginx/tls/seguro.key;

    location / {
        proxy_pass http://parcial.protos.foo;
        proxy_set_header Host parcial.protos.foo;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/seguro-protos-foo /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

curl https://seguro.protos.foo
# Contenido servido por parcial.protos.foo via HTTP inseguro. ...
```

La URL no cambia porque es un **proxy reverso**: nginx busca el contenido y lo devuelve, sin mandar ningún 301 ni 302.

### Errores típicos

| Salida de `curl https://seguro.protos.foo` | Causa |
|---|---|
| `curl: (6) Could not resolve host` | Falta la entrada en `/etc/hosts`. |
| `curl: (7) Failed to connect ... port 443` | No hay `listen 443 ssl`, el sitio no está en `sites-enabled` o no recargaste nginx. |
| `curl: (60) SSL certificate problem: self-signed certificate` | El certificado no está en el almacén de confianza: faltó `update-ca-certificates`. |
| `curl: (60) ... no alternative certificate subject name matches` | El CN o el SAN del certificado no es `seguro.protos.foo`. |
| `What?` | `proxy_pass` a la IP sin el header `Host` correcto. |
| `301 Moved Permanently` | Usaste `return 301`, que cambia la URL y no cumple el requisito. |

---

## ⭐ IV-bis — `http://publico.protos.foo`

Es lo mismo sin TLS:

```bash
echo "127.0.0.1 publico.protos.foo" | sudo tee -a /etc/hosts
```

```nginx
server {
    listen 80;
    server_name publico.protos.foo;
    location / {
        proxy_pass http://parcial.protos.foo;
        proxy_set_header Host parcial.protos.foo;
    }
}
```

```bash
sudo nginx -t && sudo systemctl reload nginx
curl http://publico.protos.foo
```
