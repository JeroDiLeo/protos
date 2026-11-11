# LabProtos2025-2C · Ejercicio I · DHCP paso a paso

## Qué hace DHCP

DHCP le entrega automáticamente a un dispositivo los parámetros para usar la red. En este ejercicio el servidor ofrece una dirección IPv4, una máscara y los servidores DNS. La duración del préstamo de la IP se llama *lease*. En la negociación inicial, el cliente envía `DHCPDISCOVER`, el servidor propone una configuración con `DHCPOFFER`, el cliente solicita la propuesta con `DHCPREQUEST` y el servidor confirma con `DHCPACK`. La prueba de Nmap que pide la consigna llega hasta la **oferta**. [RFC 2131, negociación DHCP](https://www.rfc-editor.org/rfc/rfc2131.html#section-3.1) · [Script broadcast-dhcp-discover](https://nmap.org/nsedoc/scripts/broadcast-dhcp-discover.html)

## Cómo interpretar el enunciado

| Lo que te dan o te piden | Decisión para este ejercicio |
|---|---|
| Red `192.168.100.0/24` | Declarar esa subred con máscara `255.255.255.0` y atenderla por la placa interna. |
| Direcciones dinámicas de la `.10` a la `.200` | Configurar un `range`. Cada cliente común puede recibir una IP disponible de ese conjunto. |
| MAC `08:00:27:AE:C8:6A` y siempre la IP `192.168.100.8` | Declarar un `host` que coincida por MAC y una `fixed-address` para esa impresora. |
| DNS `8.8.8.8` y `8.8.4.4` | Anunciarlos a los clientes con `option domain-name-servers`. |
| Verificar con Nmap usando dos MAC | Comparar una oferta del rango general con la oferta de la reserva. |

## 1. Identificar la interfaz interna

Salida real en `root@alumno`:

```text
root@alumno:~# ip -br addr
lo               UNKNOWN        127.0.0.1/8 ::1/128
eth0@if44        UP
eth1@if45        UP             192.168.50.20/24
```

`ip` consulta la configuración de red, `addr` muestra las direcciones y `-br` resume una interfaz por línea. `lo` es el loopback. La IPv4 `192.168.50.20/24` identifica a `eth1` como la placa de la red abierta. `eth0` está activa y arranca sin IPv4, tal como describe el lab para la placa interna. El nombre que usamos en los comandos es `eth0`. El sufijo `@if44` identifica el otro extremo del enlace virtual.

## 2. Darle una IP propia al servidor

El Compose del lab reserva `192.168.100.1` para `alumno` en la red interna y su arranque quita esa IP de la placa para que el alumno la configure. La consigna fija la subred, la reserva y el rango. La dirección propia del servidor sale de la configuración de este entorno.

```text
root@alumno:~# ip addr add 192.168.100.1/24 dev eth0
root@alumno:~# ip -br addr show dev eth0
eth0@if44        UP             192.168.100.1/24
```

`addr add` agrega la IPv4. El prefijo `/24` fija la máscara y `dev eth0` selecciona la placa interna. El segundo comando comprueba el cambio filtrando la salida a esa interfaz. La `.1` la usa el servidor. La `.8` queda para la impresora y el conjunto `.10`–`.200` queda para ofertas dinámicas.

## 3. Elegir dónde escucha el servicio

En `/etc/default/isc-dhcp-server`, configuramos:

```bash
INTERFACESv4="eth0"
```

Esa línea indica en qué interfaz debe escuchar el servicio IPv4 al arrancar. El proceso se restringe a la placa interna, como pide la consigna.

## 4. Definir qué puede ofrecer

Bloque del ejercicio en `/etc/dhcp/dhcpd.conf`:

```conf
subnet 192.168.100.0 netmask 255.255.255.0 {
    range 192.168.100.10 192.168.100.200;
    option domain-name-servers 8.8.8.8, 8.8.4.4;
}

host impresora {
    hardware ethernet 08:00:27:AE:C8:6A;
    fixed-address 192.168.100.8;
}
```

- `subnet` indica a qué red pertenecen las reglas. `netmask` expresa el `/24` en decimal.
- `range` indica el conjunto del que sale la IP de un cliente común. Incluye ambos extremos.
- `option domain-name-servers` anuncia los DNS que deben usar los clientes de esa subred, incluida la impresora.
- `host impresora` le da un nombre al bloque. `hardware ethernet` selecciona al cliente por su MAC Ethernet y `fixed-address` indica la dirección fija de ese cliente.

## 5. Validar y arrancar

```bash
dhcpd -t -4 -cf /etc/dhcp/dhcpd.conf
```

`-t` prueba la configuración sin arrancar el servicio, `-4` selecciona IPv4 y `-cf` indica qué archivo leer. En la salida real se mostró el archivo de configuración y las rutas de la base de leases y del PID. El comando volvió al prompt sin errores de configuración.

```bash
systemctl start isc-dhcp-server
systemctl status isc-dhcp-server
```

`start` inicia el servicio y `status` comprueba su estado. Extracto real:

```text
● isc-dhcp-server.service - ISC DHCP IPv4 server
     Active: active (running)
Listening on LPF/eth0/6a:b3:f2:d3:5b:62/192.168.100.0/24
Sending on   LPF/eth0/6a:b3:f2:d3:5b:62/192.168.100.0/24
Server starting service.
```

`Active` confirma que el proceso está corriendo. `Listening on …/eth0/…/192.168.100.0/24` confirma que escucha en la placa y subred esperadas.

## 6. Probar dos clientes cambiando la MAC

```bash
# Cliente común
nmap -e eth0 --script broadcast-dhcp-discover \
  --script-args 'broadcast-dhcp-discover.mac=AA:BB:CC:DD:EE:FF'

# Impresora
nmap -e eth0 --script broadcast-dhcp-discover \
  --script-args 'broadcast-dhcp-discover.mac=08:00:27:AE:C8:6A'
```

`-e eth0` selecciona la interfaz interna. `--script` ejecuta el script de descubrimiento DHCP por broadcast. `--script-args` pasa la MAC del cliente simulado. El aviso `No targets were specified` se refiere al escaneo de hosts de Nmap. El script se ejecuta en la etapa de preescaneo y la respuesta aparece en `Pre-scan script results`. [Documentación de Nmap](https://nmap.org/nsedoc/scripts/broadcast-dhcp-discover.html)

**Salida real del cliente común**

```text
Pre-scan script results:
| broadcast-dhcp-discover:
|   Response 1 of 1:
|     Interface: eth0
|     IP Offered: 192.168.100.10
|     DHCP Message Type: DHCPOFFER
|     Server Identifier: 192.168.100.1
|     IP Address Lease Time: 10m00s
|     Subnet Mask: 255.255.255.0
|     Domain Name Server: 8.8.8.8, 8.8.4.4
|_    Domain Name: example.org
WARNING: No targets were specified, so 0 hosts scanned.
```

**Salida real de la impresora**

```text
Pre-scan script results:
| broadcast-dhcp-discover:
|   Response 1 of 1:
|     Interface: eth0
|     IP Offered: 192.168.100.8
|     DHCP Message Type: DHCPOFFER
|     Server Identifier: 192.168.100.1
|     IP Address Lease Time: 10m00s
|     Subnet Mask: 255.255.255.0
|     Domain Name Server: 8.8.8.8, 8.8.4.4
|_    Domain Name: example.org
WARNING: No targets were specified, so 0 hosts scanned.
```

En ambas salidas, `Server Identifier` identifica a nuestro servidor, `IP Address Lease Time` indica la duración propuesta, `Subnet Mask` muestra la máscara y `Domain Name Server` muestra los DNS pedidos. `Domain Name: example.org` es otra opción anunciada en la práctica. La consigna evalúa las dos direcciones que aparecen en `Domain Name Server`.

### Por qué se repite la .10

Cada repetición usa la misma MAC `AA:BB:CC:DD:EE:FF`, así que estás simulando el mismo cliente. La salida muestra un `DHCPOFFER`. El script llega hasta esa oferta, mientras que el cliente DHCP completa la asignación con `DHCPREQUEST` y `DHCPACK`. Si repetís la prueba con el mismo cliente y la `.10` sigue disponible para él, el servidor puede volver a ofrecerla. ISC DHCP selecciona las IP del rango según el estado de sus asignaciones y direcciones disponibles. El inicio del rango por sí solo no permite predecir el orden en que van a salir. [Cómo selecciona direcciones ISC DHCP](https://manpages.debian.org/bookworm/isc-dhcp-server/dhcpd.conf.5.en.html) · [RFC 2131, negociación DHCP](https://www.rfc-editor.org/rfc/rfc2131.html#section-3.1)

Para defender el resultado, alcanza con mostrar que la `.10` cae dentro del rango y que al cambiar la MAC a la de la impresora la oferta pasa exactamente a la `.8`. Eso verifica la configuración pedida mediante las dos ofertas.

### Prueba adicional con otra MAC común

Cambiamos el último byte de la MAC de `FF` a `FE` para simular otro cliente común. El servidor, la interfaz y el rango se mantuvieron iguales. La salida real fue la siguiente.

```text
root@alumno:~# nmap -e eth0 --script broadcast-dhcp-discover --script-args 'broadcast-dhcp-discover.mac=AA:BB:CC:DD:EE:FE'
Starting Nmap 7.94SVN ( https://nmap.org ) at 2026-11-11 17:54 UTC
Pre-scan script results:
| broadcast-dhcp-discover:
|   Response 1 of 1:
|     Interface: eth0
|     IP Offered: 192.168.100.11
|     DHCP Message Type: DHCPOFFER
|     Server Identifier: 192.168.100.1
|     IP Address Lease Time: 10m00s
|     Subnet Mask: 255.255.255.0
|     Domain Name Server: 8.8.8.8, 8.8.4.4
|_    Domain Name: example.org
WARNING: No targets were specified, so 0 hosts scanned.
Nmap done: 0 IP addresses (0 hosts up) scanned in 10.41 seconds
```

Para `AA:BB:CC:DD:EE:FF` vimos una oferta por la `.10` y para `AA:BB:CC:DD:EE:FE` una por la `.11`. Las dos direcciones salen del rango general. El valor `.11` describe lo que ocurrió en esta prueba. El servidor puede elegir otras direcciones disponibles del rango en pruebas futuras.

## Variantes para interpretar otros enunciados

### Te dan un Client Identifier en vez de la MAC

Si el cliente envía un identificador DHCP de texto cuyo valor exacto es `impresora-01`, el bloque puede quedar así:

```conf
host impresora {
    option dhcp-client-identifier "impresora-01";
    fixed-address 192.168.100.8;
}
```

Si te dan el identificador como una secuencia de bytes, copiá los bytes exactos en hexadecimal. Por ejemplo, `option dhcp-client-identifier 01:08:00:27:ae:c8:6a;` sirve si ese es el identificador que envía el cliente. `host impresora` es el nombre del bloque. Si el enunciado te da solo un nombre de equipo, averiguá la MAC o el identificador DHCP para configurar la coincidencia. [Reglas de identificación de clientes en ISC DHCP](https://manpages.debian.org/bookworm/isc-dhcp-server/dhcpd.conf.5.en.html)

### Te piden un rango exclusivo para la impresora

Si la consigna cambiara a «la impresora puede recibir cualquiera entre la `.8` y la `.10`», podés identificarla con una clase y dejarle un `pool` exclusivo:

```conf
class "impresora" {
    match if hardware = 01:08:00:27:ae:c8:6a;
}

subnet 192.168.100.0 netmask 255.255.255.0 {
    option domain-name-servers 8.8.8.8, 8.8.4.4;

    pool {
        allow members of "impresora";
        range 192.168.100.8 192.168.100.10;
    }

    pool {
        deny members of "impresora";
        range 192.168.100.11 192.168.100.200;
    }
}
```

`hardware` contiene el tipo de interfaz seguido de la MAC. `01` representa Ethernet. `allow members of` le da acceso al primer pool a la impresora y `deny members of` la excluye del rango general. En este ejemplo la `.10` quedó en el rango exclusivo, por eso el general empieza en `.11`. Si el enunciado exige que la `.10` también esté en el rango general, primero aclararía cómo debe resolverse ese solapamiento. Esta variante se contrastó con el manual. Queda pendiente probarla en el lab. [Clases y pools en ISC DHCP](https://manpages.debian.org/bookworm/isc-dhcp-server/dhcpd.conf.5.en.html) · [Expresiones DHCP y operador hardware](https://manpages.debian.org/bookworm/isc-dhcp-common/dhcp-eval.5.en.html#hardware)

En la guía práctica de la materia, el **E89 de la página 44** pide que un host reciba siempre la misma IP aunque haya otros clientes. Ese enunciado corresponde al caso de IP fija del parcial.
