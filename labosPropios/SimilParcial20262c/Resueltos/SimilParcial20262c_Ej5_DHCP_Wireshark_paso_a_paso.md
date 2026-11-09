# Simulacro 2026-2C · Ejercicio 5 · DHCP en Wireshark

Práctica del 9 de noviembre de 2026. En los paquetes 1 a 4, el servidor DHCP `172.30.0.1` asigna **`172.30.0.123`** a `cliente-dedsec` por **86400 segundos (1 día)**.

## 1. Descargar la captura

Desde la carpeta del simulacro:

```bash
curl -f http://172.30.0.60:8000/dhcp.pcapng -o dhcp.pcapng
wireshark dhcp.pcapng
```

`curl` pide la captura al servidor HTTP. `-f` devuelve un error si el servidor responde con un error HTTP y `-o dhcp.pcapng` guarda el cuerpo de la respuesta con ese nombre. También se puede abrir el archivo con **Ctrl+O** desde Wireshark.

## 2. Elegir los paquetes del cliente correcto

1. Abrí la captura. El filtro de visualización `dhcp` deja a la vista los mensajes del protocolo. En este archivo aparecen ocho paquetes DHCP.
2. Seleccioná un **Discover** y expandí **Dynamic Host Configuration Protocol**. En el paquete **1**, **Client MAC address** es `02:42:ac:1e:00:aa` y la **opción 12 (Host Name)** dice `cliente-dedsec`.
3. Buscá **Transaction ID** en ese paquete. El valor es **`0xded5ec01`**.
4. Sobre **Transaction ID**, usá **clic derecho → Apply as Filter → Selected**. Así Wireshark conserva los paquetes con ese mismo valor. En esta captura quedan los paquetes **1, 2, 3 y 4**.
5. Confirmá en el ACK que sigue apareciendo la misma MAC en **Client MAC address**.

El **Transaction ID**, también llamado `xid`, permite asociar las respuestas del servidor con los pedidos del cliente. La **MAC del cliente dentro de DHCP** ayuda a comprobar la identidad en ambas direcciones. En un Offer o un ACK, la MAC de origen del encabezado Ethernet corresponde al servidor. Los paquetes **5 a 8** tienen otro Transaction ID y la MAC `02:42:ac:1e:00:bb`.

La lista de paquetes permite encontrar el tipo en la columna **Info**. Si querés confirmarlo en el detalle, expandí la **opción 53 (DHCP Message Type)**. En el paquete 4, la opción 53 dice **ACK**.

## 3. Orden de los mensajes

| Paquete | Opción 53 | Quién lo envía | Qué pasa |
|---:|---|---|---|
| 1 | Discover (1) | Cliente | Busca un servidor DHCP que pueda ofrecerle una configuración. |
| 2 | Offer (2) | Servidor | Ofrece `172.30.0.123` en **Your (client) IP address**. |
| 3 | Request (3) | Cliente | Pide `172.30.0.123` en la opción 50 y elige a `172.30.0.1` en la opción 54. |
| 4 | ACK (5) | Servidor | Confirma la dirección y los parámetros del lease. |

El intercambio se llama **DORA**, por **Discover → Offer → Request → ACK**. El Offer muestra lo propuesto. El ACK permite contestar qué recibió el cliente al terminar la asignación.

## 4. Leer la IP y las opciones del ACK

En el **paquete 4**, expandí **Dynamic Host Configuration Protocol** y abrí con el triangulito las opciones que muestran su detalle plegado.

| Dato de la consigna | Campo en Wireshark | Valor observado |
|---|---|---|
| IP asignada | **Your (client) IP address** (`yiaddr`) | `172.30.0.123` |
| Servidor DHCP | **Opción 54**, DHCP Server Identifier | `172.30.0.1` |
| Duración del lease | **Opción 51**, IP Address Lease Time | `86400` segundos, **1 día** |
| Máscara de subred | **Opción 1**, Subnet Mask | `255.255.255.0` (`/24`) |
| Puerta de enlace | **Opción 3**, Router | `172.30.0.1` |
| Servidor DNS | **Opción 6**, Domain Name Server | `172.30.0.41` |
| Dominio entregado | **Opción 15**, Domain Name | `protos.lab` |
| ID de transacción | **Transaction ID** | `0xded5ec01` |

El campo **Client IP address** (`ciaddr`) del ACK figura como `0.0.0.0`. Para leer la IP asignada en este intercambio, el campo que corresponde es **Your (client) IP address** (`yiaddr`).

En esta captura, el identificador del servidor DHCP y la puerta de enlace tienen el mismo valor, `172.30.0.1`. Cada uno se comprueba por separado en su opción. El DNS se obtiene de la opción 6. Su IP coincide con la de BIND en el ejercicio 4.

## 5. Por qué se usa 0.0.0.0 y broadcast

Para comprobarlo, abrí **Internet Protocol Version 4** y **User Datagram Protocol** en los paquetes 1 y 3. Hacé lo mismo en los paquetes 2 y 4 para comparar las respuestas.

| Paquetes | IP de origen | IP de destino | UDP origen → destino |
|---|---|---|---|
| 1 y 3 · Discover y Request | `0.0.0.0` | `255.255.255.255` | **68 → 67** |
| 2 y 4 · Offer y ACK | `172.30.0.1` | `255.255.255.255` | **67 → 68** |

El cliente usa **`0.0.0.0` como origen** porque todavía está obteniendo su configuración IPv4. En este Request inicial ya conoce la oferta, pero está esperando el ACK antes de usar la dirección solicitada.

**`255.255.255.255`** es el broadcast limitado de IPv4. En el Discover permite buscar servidores DHCP en la red local. En el Request de esta transacción, el cliente vuelve a enviar por broadcast y señala con la **opción 54** qué servidor eligió. Así, si otros servidores hicieron ofertas, pueden saber que se eligió otro. En la captura, Offer y ACK también tienen destino broadcast y el ACK muestra **Broadcast flag** en los detalles DHCP.

DHCPv4 usa **UDP 67 para el servidor y UDP 68 para el cliente**. En las peticiones de este intercambio se ve `68 → 67`, y en las respuestas `67 → 68`.

