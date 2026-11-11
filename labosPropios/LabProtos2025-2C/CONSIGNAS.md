# Parcial Práctico — 2Q2025

```
Hoja: 1 de 2                                72.07 - Protocolos de Comunicación
Nro. de Legajo: ____________                                 Parcial práctico
Nombre y Apellido: ______________________________          31 de Octubre 2025
```

**Condición de aprobación: «obtener 5 puntos»**

|   I   |  II   |  III  |  IV   | Total |
|:-----:|:-----:|:-----:|:-----:|:-----:|
| /2.5  | /2.5  | /2.5  | /2.5  |  /10  |

> **Cómo se usa este lab.** Tu "VM del parcial" es el contenedor `alumno`: entrás con `make ws`. Ahí ya está instalado todo lo que se usa en el parcial (isc-dhcp-server, bind9, nginx, nmap, traceroute, net-tools, openssl) y los comandos `sudo`, `systemctl` y `journalctl` funcionan como en Ubuntu. Todo se hace con IPs y nombres reales de la red del lab, nunca con `localhost` para hablar con otros hosts. Cuando termines un ejercicio, corré `make corregir` desde tu máquina; si querés volver a empezar, `make reset`.

---

## Ejercicio I

Usted administra la red de una pequeña oficina (`192.168.100.0/24`) que utiliza un servidor DHCP para la asignación de direcciones IP. Configure el servidor para que cumpla con los siguientes requisitos:

1. Una impresora de red crítica, con la dirección MAC `08:00:27:AE:C8:6A`, debe tener siempre la dirección IP estática `192.168.100.8` para que los scripts de impresión funcionen correctamente.
2. Se desea que todos los clientes tengan un servidor DNS siempre disponible, y que el proveedor sea confiable. Deben utilizar los servidores DNS de Google (`8.8.8.8` y `8.8.4.4`).
3. Se desea usar el rango de direcciones de 10-200 para asignar. El resto queda reservado para uso futuro.

Verifique la configuración con el siguiente comando, que le permite simular DHCP Request:

```bash
sudo nmap --script broadcast-dhcp-discover \
     --script-args "broadcast-dhcp-discover.mac=AA:BB:CC:DD:EE:FF"
```

**Aviso:** No resuelva el ejercicio sobre una interfaz conectada a la red WIFI del Laboratorio. Hágalo en una red interna o interfaz virtual.

> **En el lab:** tu VM tiene una segunda placa conectada a una red interna aislada, la red `192.168.100.0/24`. Esa placa arranca **sin dirección IP**, como una "Internal Network" recién agregada en VirtualBox. La otra placa es la de la red del laboratorio, que en este escenario hace de WiFi: no la uses para DHCP.

**Entrega:** `/etc/default/isc-dhcp-server`, `/etc/dhcp/dhcpd.conf` y la salida del comando de verificación, para un cliente cualquiera y para la MAC de la impresora.

---

## Ejercicio II

El host en `192.168.50.250` es el gateway de la red `10.0.0.0/24`. Sabe que existe un servidor distinto al gateway en esta red, pero no está seguro de qué dirección IP tiene asignada. Descubra la dirección del servidor, y los servicios que tiene expuesto el host.

Debe mostrar:

- El resultado de acceder vía HTTP a dicho servidor.
- Los routers que intervienen en esta comunicación.

**Nota:** Recomendamos utilizar una VM para resolver este ejercicio, pero no es necesario de poder hacerlo en su Host. De usar una VM, el adaptador de red debe estar en modo Bridge (Puente) conectado a la red abierta.

> **En el lab:** tu VM ya está conectada a la red abierta `192.168.50.0/24`, igual que con el adaptador en modo Bridge.

**Entrega:** los comandos usados y sus salidas: cómo llegaste a la red `10.0.0.0/24`, el descubrimiento de hosts, los servicios expuestos, la respuesta HTTP del servidor y los routers del camino.

---

*Hoja: 2 de 2*

## Ejercicio III

Usted es el administrador de un servidor DNS que utiliza BIND9 y es autoritativo para la zona `it.itba.edu.ar`. Recientemente, tras una serie de cambios, los clientes han reportado que la resolución de nombres para todos los hosts dentro de esa zona (como `pampero.it.itba.edu.ar`) ha dejado de funcionar. Sus navegadores arrojan problemas al resolver nombres, y administradores de DNS de los ISP lo han contactado por problemas en la zona.

Al revisar los registros del sistema, observa que el servicio BIND9 se queja de múltiples errores al intentar cargar el archivo de zona, ubicado en `/etc/bind/db.it.itba.edu.ar` (disponible en `http://protos.foo/zona`).

Inspeccione el archivo de zona, identifique y corrija todos los errores de sintaxis y de configuración lógica que impiden su correcto funcionamiento. Una vez corregidos los errores, haga los cambios necesarios en el registro SOA para asegurar que los cambios se propaguen de manera correcta y rápido.

```
$TTL 604800
@ IN SOA ns1.it.itba.edu.ar. admin@it.itba.edu.ar. (
        2025060500      ; Serial
        604800          ; Refresh
        86400           ; Retry
        2419200         ; Expire
        604800          ; Negative Cache TTL
)

; Name Servers
@       IN NS ns1.it.itba.edu.ar.

; Mail
@       IN MX 10 mail

; Hosts
ns1.it.itba.edu.ar     IN A 192.168.70.1
pampero                IN A 192.168.70.10

; Aliases
www     IN A pampero
correo  IN CNAME pampero
```

> **En el lab:** tu VM es ese servidor. BIND9 ya tiene declarada la zona en `/etc/bind/named.conf.local` y está corriendo con el archivo roto: mirá `systemctl status bind9` o `journalctl -u bind9`.

**Entrega:** la lista de errores encontrados, explicando cada uno; el archivo de zona corregido; la salida de `named-checkzone`, y consultas con `dig` que muestren que la zona resuelve.

---

## Ejercicio IV

El servidor en `parcial.protos.foo` está corriendo un servidor HTTP inseguro. Usted, como un administrador responsable, desea exponerlo al público a través de HTTPS. Configure lo necesario para que al acceder a `https://seguro.protos.foo` con un HTTP User Agent (Firefox, Google Chrome, Curl), se sirva el contenido devuelto por `parcial.protos.foo`.

**Requisito.** No se debe ver modificada la URL ingresada en el browser. Si se utiliza curl no se permiten otras opciones. Se recomienda verificación utilizando curl:

```bash
$ curl https://seguro.protos.foo
```

**Entrega:** la configuración de nginx, cómo generaste el certificado y cómo lograste que sea aceptado, y la salida de `curl https://seguro.protos.foo`.

---

## ⭐ Extra: Ejercicio IV-bis (no suma puntos)

> Esta es la versión del Ejercicio IV que figura en el apunte del repo (`2025 2C.md`). Es la misma idea, pero por HTTP. Sirve como paso previo antes de agregarle TLS.

El servidor en `parcial.protos.foo` está corriendo un servidor HTTP. Usted desea publicar ese mismo contenido bajo el nombre `publico.protos.foo`, también mediante HTTP. Configure lo necesario para que al acceder a `http://publico.protos.foo` con un cliente HTTP (Firefox, Google Chrome, Curl) se sirva el contenido devuelto por `parcial.protos.foo`.

**Requisito:** no se debe ver modificada la URL ingresada en el browser. Si se utiliza `curl`, no se permiten otras opciones: `curl http://publico.protos.foo`.
