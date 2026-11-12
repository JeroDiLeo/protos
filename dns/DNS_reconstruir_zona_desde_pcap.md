# Reconstruir una zona DNS desde una captura (pcap) — guía con ejemplo completo

El tipo de ejercicio: te dan una captura (`.pcap` / `.pcapng`) con tráfico DNS, o un backup, y te piden **recuperar los registros de una zona**, cargarla en BIND (a veces con un registro agregado) y demostrar que responde.

Esta guía usa un **ejemplo inventado completo**, la zona `parcial.lab`. Muestra cada paquete tal como lo verías en Wireshark, cómo se traduce a una línea del archivo de zona y cómo queda la zona final. La zona del ejemplo está validada con `named-checkzone`.

---

## 1. El método en 6 pasos

1. **Abrí la captura y filtrá solo respuestas DNS:** `dns.flags.response == 1`.
2. **Identificá el servidor de la zona:** quién manda las respuestas con el bit **Authoritative** (`aa`).
3. **Buscá el SOA:** te dice el nombre de la zona y todos sus parámetros.
4. **Recorré cada respuesta y abrí Answers, Authority y Additional.** Anotá por cada registro: dueño, TTL, clase, tipo y datos.
5. **Descartá lo que no aporta:** repetidos, respuestas vacías, NXDOMAIN y respuestas de cachés con TTL rebajado.
6. **Escribí la zona, validala con `named-checkzone`, declarala en `named.conf.local`, recargá BIND y verificá con `dig`.**

---

## 2. Filtros de Wireshark útiles

Se escriben en la barra de filtro de arriba (la verde).

| Filtro | Qué muestra |
|---|---|
| `dns` | Todo el tráfico DNS (consultas y respuestas). |
| `dns.flags.response == 1` | **Solo respuestas.** Las consultas no traen registros. |
| `dns.flags.response == 1 && ip.src == 10.10.0.53` | Solo las respuestas que mandó ese servidor. |
| `dns.flags.authoritative == 1` | Solo respuestas con autoridad (`aa`): datos originales, no de caché. |
| `dns.qry.name contains "parcial.lab"` | Solo lo que tiene que ver con la zona (saca el ruido de otros dominios). |
| `dns.flags.rcode == 3` | Respuestas NXDOMAIN ("ese nombre no existe"). |
| `dns.qry.type == 252` | Transferencia de zona (AXFR). Si aparece, **la zona entera viene en esa respuesta**. |
| `dns.resp.type == 6` | Respuestas que traen un SOA. |

Números de tipo, por si filtrás por tipo: `1` A · `2` NS · `5` CNAME · `6` SOA · `12` PTR · `15` MX · `16` TXT · `28` AAAA · `252` AXFR.

Los filtros se combinan con `&&` (y), `||` (o) y `!` (no).

---

## 3. Cómo leer un paquete en Wireshark

Wireshark tiene tres paneles:

1. **Arriba, la lista de paquetes:** una línea por paquete. La columna **Info** resume la consulta y la respuesta.
2. **Al medio, el detalle:** el paquete desarmado por capas. Ahí abrís **Domain Name System (response)**.
3. **Abajo, los bytes en hexadecimal.** Para estos ejercicios no lo necesitás.

Dentro de **Domain Name System (response)** te importan:

| Parte | Qué te dice |
|---|---|
| **Flags** | Si es respuesta, si tiene autoridad (`Authoritative`) y el código de respuesta (`Reply code`: `No error` o `No such name`). |
| **Answer RRs / Authority RRs / Additional RRs** | Cuántos registros hay en cada sección. Si `Answer RRs: 0`, no hay respuesta directa. |
| **Queries** | Qué se preguntó (nombre y tipo). **No aporta registros.** |
| **Answers** | Los registros que responden la pregunta. **Lo principal.** |
| **Authoritative nameservers** | Sección Authority: NS de la zona, o el SOA en respuestas negativas. **También aporta registros.** |
| **Additional records** | Datos extra, típicamente el A de los servidores nombrados (NS, MX). **También aporta registros.** |

**Truco:** clic derecho sobre un campo del detalle (por ejemplo `Time to live`) → **Apply as Column**. Así ves ese dato de todos los paquetes en la lista de arriba, sin abrirlos de a uno.

---

## 4. El ejemplo: la captura de `parcial.lab`

Supongamos que la captura tiene esta lista de paquetes (filtro `dns`):

```text
No.  Source       Destination  Protocol  Info
 1   10.10.0.20   10.10.0.53   DNS       Standard query 0x1001 SOA parcial.lab
 2   10.10.0.53   10.10.0.20   DNS       Standard query response 0x1001 SOA parcial.lab SOA ns1.parcial.lab
 3   10.10.0.20   10.10.0.53   DNS       Standard query 0x1002 NS parcial.lab
 4   10.10.0.53   10.10.0.20   DNS       Standard query response 0x1002 NS parcial.lab NS ns1.parcial.lab NS ns2.parcial.lab A 10.10.0.53 A 10.10.0.54
 5   10.10.0.20   10.10.0.53   DNS       Standard query 0x1003 A www.parcial.lab
 6   10.10.0.53   10.10.0.20   DNS       Standard query response 0x1003 A www.parcial.lab A 10.10.0.80 A 10.10.0.81
 7   10.10.0.20   10.10.0.53   DNS       Standard query 0x1004 AAAA www.parcial.lab
 8   10.10.0.53   10.10.0.20   DNS       Standard query response 0x1004 AAAA www.parcial.lab AAAA 2001:db8::80
 9   10.10.0.20   10.10.0.53   DNS       Standard query 0x1005 MX parcial.lab
10   10.10.0.53   10.10.0.20   DNS       Standard query response 0x1005 MX parcial.lab MX 10 mail.parcial.lab MX 20 mx.backup.com A 10.10.0.25
11   10.10.0.20   10.10.0.53   DNS       Standard query 0x1006 A ftp.parcial.lab
12   10.10.0.53   10.10.0.20   DNS       Standard query response 0x1006 A ftp.parcial.lab CNAME www.parcial.lab A 10.10.0.80 A 10.10.0.81
13   10.10.0.20   10.10.0.53   DNS       Standard query 0x1007 TXT parcial.lab
14   10.10.0.53   10.10.0.20   DNS       Standard query response 0x1007 TXT parcial.lab TXT TXT
15   10.10.0.20   10.10.0.53   DNS       Standard query 0x1008 MX mail.parcial.lab
16   10.10.0.53   10.10.0.20   DNS       Standard query response 0x1008 MX mail.parcial.lab SOA ns1.parcial.lab
17   10.10.0.20   10.10.0.53   DNS       Standard query 0x1009 A dev.parcial.lab
18   10.10.0.53   10.10.0.20   DNS       Standard query response 0x1009 No such name A dev.parcial.lab SOA ns1.parcial.lab
19   10.10.0.30   10.10.0.1    DNS       Standard query 0x2001 A www.parcial.lab
20   10.10.0.1    10.10.0.30   DNS       Standard query response 0x2001 A www.parcial.lab A 10.10.0.80 A 10.10.0.81
21   10.10.0.20   10.10.0.53   DNS       Standard query 0x100a A www.parcial.lab
22   10.10.0.53   10.10.0.20   DNS       Standard query response 0x100a A www.parcial.lab A 10.10.0.80 A 10.10.0.81
```

Primeras conclusiones, solo con la lista:
- Las consultas van a `10.10.0.53`, y de ahí salen casi todas las respuestas: **ese es el servidor de la zona**.
- Los paquetes impares son consultas, así que **solo miramos los pares**.
- El 19 y el 20 son de **otra conversación** (`10.10.0.30` le pregunta a `10.10.0.1`). Ojo con esos (paquete 20 más abajo).

Ahora, paquete por paquete. El detalle está **recortado** a lo que importa: Wireshark muestra algunas líneas más, como `Data length` o `[Name Length]`, que podés ignorar.

---

### Paquete 2 — SOA: identifica la zona

```text
Domain Name System (response)
    Transaction ID: 0x1001
    Flags: 0x8580 Standard query response, No error
        1... .... .... .... = Response: Message is a response
        .... .1.. .... .... = Authoritative: Server is an authority for domain
        .... .... .... 0000 = Reply code: No error (0)
    Questions: 1
    Answer RRs: 1
    Authority RRs: 0
    Additional RRs: 0
    Queries
        parcial.lab: type SOA, class IN
    Answers
        parcial.lab: type SOA, class IN, mname ns1.parcial.lab
            Name: parcial.lab
            Type: SOA (Start Of a zone of Authority) (6)
            Class: IN (0x0001)
            Time to live: 3600 (1 hour)
            Primary name server: ns1.parcial.lab
            Responsible authority's mailbox: admin.parcial.lab
            Serial Number: 2026111201
            Refresh Interval: 7200 (2 hours)
            Retry Interval: 1800 (30 minutes)
            Expire limit: 1209600 (14 days)
            Minimum TTL: 3600 (1 hour)
```

**Qué mirar:**
- `Authoritative: Server is an authority` confirma que es un dato original.
- `Name: parcial.lab` es **el nombre de la zona**: va en `zone "parcial.lab"` y en el comando `named-checkzone`.
- `Time to live: 3600` es buen candidato para el `$TTL` por defecto.
- El resto son los campos del SOA, que se copian en este orden: servidor principal, mailbox, serial, refresh, retry, expire, minimum.

**Traducción:**

| Wireshark | Archivo de zona |
|---|---|
| `Name: parcial.lab` | `@` (la raíz de la zona) |
| `Primary name server: ns1.parcial.lab` | `ns1.parcial.lab.` (**con punto**) |
| `Responsible authority's mailbox: admin.parcial.lab` | `admin.parcial.lab.` (es el mail `admin@parcial.lab`, escrito con punto en vez de `@`) |
| `Serial Number` … `Minimum TTL` | los 5 números, en ese orden |

```dns
$TTL 3600
@  IN  SOA  ns1.parcial.lab. admin.parcial.lab. (
            2026111201  ; serial
            7200        ; refresh
            1800        ; retry
            1209600     ; expire
            3600        ; minimum
)
```

---

### Paquete 4 — NS, con datos en Additional

```text
Domain Name System (response)
    Flags: 0x8580 Standard query response, No error
        .... .1.. .... .... = Authoritative: Server is an authority for domain
    Answer RRs: 2
    Authority RRs: 0
    Additional RRs: 2
    Queries
        parcial.lab: type NS, class IN
    Answers
        parcial.lab: type NS, class IN, ns ns1.parcial.lab
            Name: parcial.lab
            Type: NS (authoritative Name Server) (2)
            Time to live: 3600 (1 hour)
            Name Server: ns1.parcial.lab
        parcial.lab: type NS, class IN, ns ns2.parcial.lab
            Name: parcial.lab
            Type: NS (authoritative Name Server) (2)
            Time to live: 3600 (1 hour)
            Name Server: ns2.parcial.lab
    Additional records
        ns1.parcial.lab: type A, class IN, addr 10.10.0.53
            Name: ns1.parcial.lab
            Type: A (Host Address) (1)
            Time to live: 3600 (1 hour)
            Address: 10.10.0.53
        ns2.parcial.lab: type A, class IN, addr 10.10.0.54
            Name: ns2.parcial.lab
            Type: A (Host Address) (1)
            Time to live: 3600 (1 hour)
            Address: 10.10.0.54
```

**Qué mirar:** un solo paquete aporta **4 registros**. Los NS están en Answers, pero las IPs de `ns1` y `ns2` están en **Additional records**. Si solo mirás Answers, te las perdés, y sin ellas BIND no carga la zona (exige que un NS dentro de la zona tenga su A).

**Traducción:**

```dns
@    IN  NS  ns1.parcial.lab.
@    IN  NS  ns2.parcial.lab.
ns1  IN  A   10.10.0.53
ns2  IN  A   10.10.0.54
```

---

### Paquete 6 — dos A para el mismo nombre, con TTL distinto

```text
    Answers
        www.parcial.lab: type A, class IN, addr 10.10.0.80
            Name: www.parcial.lab
            Type: A (Host Address) (1)
            Time to live: 300 (5 minutes)
            Address: 10.10.0.80
        www.parcial.lab: type A, class IN, addr 10.10.0.81
            Name: www.parcial.lab
            Type: A (Host Address) (1)
            Time to live: 300 (5 minutes)
            Address: 10.10.0.81
```

**Qué mirar:**
- **Dos A para `www`:** van **las dos líneas** (es balanceo de carga, no un error).
- **`Time to live: 300`, no 3600.** Si escribís `www IN A ...`, BIND le pone el `$TTL` (3600) y el TTL **no coincide con la captura**. Hay que escribirlo explícito.

**Traducción:**

```dns
www  300  IN  A  10.10.0.80
www  300  IN  A  10.10.0.81
```

---

### Paquete 8 — AAAA (IPv6)

```text
    Answers
        www.parcial.lab: type AAAA, class IN, addr 2001:db8::80
            Name: www.parcial.lab
            Type: AAAA (IPv6 Address) (28)
            Time to live: 300 (5 minutes)
            AAAA Address: 2001:db8::80
```

**Traducción:**

```dns
www  300  IN  AAAA  2001:db8::80
```

---

### Paquete 10 — MX: dos servidores y uno externo

```text
    Answer RRs: 2
    Additional RRs: 1
    Queries
        parcial.lab: type MX, class IN
    Answers
        parcial.lab: type MX, class IN, preference 10, mx mail.parcial.lab
            Name: parcial.lab
            Type: MX (Mail eXchange) (15)
            Time to live: 3600 (1 hour)
            Preference: 10
            Mail Exchange: mail.parcial.lab
        parcial.lab: type MX, class IN, preference 20, mx mx.backup.com
            Name: parcial.lab
            Type: MX (Mail eXchange) (15)
            Time to live: 3600 (1 hour)
            Preference: 20
            Mail Exchange: mx.backup.com
    Additional records
        mail.parcial.lab: type A, class IN, addr 10.10.0.25
            Name: mail.parcial.lab
            Time to live: 3600 (1 hour)
            Address: 10.10.0.25
```

**Qué mirar:**
- El **dueño** de los MX es `parcial.lab` (la raíz), **no** `mail.parcial.lab`. Es decir: "el correo para `@parcial.lab` lo reciben estos servidores".
- `Preference` va **antes** del nombre en la línea. El número más bajo tiene más prioridad.
- `mx.backup.com` es de **otra zona**. Se escribe con punto y **no** se le inventa un A: ese A vive en la zona `backup.com`, no en la tuya.
- El A de `mail` viene en **Additional**: también se anota.

**Traducción:**

```dns
@     IN  MX  10 mail.parcial.lab.
@     IN  MX  20 mx.backup.com.
mail  IN  A   10.10.0.25
```

---

### Paquete 12 — CNAME seguido de A

```text
    Queries
        ftp.parcial.lab: type A, class IN
    Answers
        ftp.parcial.lab: type CNAME, class IN, cname www.parcial.lab
            Name: ftp.parcial.lab
            Type: CNAME (Canonical NAME for an alias) (5)
            Time to live: 3600 (1 hour)
            CNAME: www.parcial.lab
        www.parcial.lab: type A, class IN, addr 10.10.0.80
            Name: www.parcial.lab
            Time to live: 300 (5 minutes)
            Address: 10.10.0.80
        www.parcial.lab: type A, class IN, addr 10.10.0.81
            Name: www.parcial.lab
            Time to live: 300 (5 minutes)
            Address: 10.10.0.81
```

**Qué mirar:** se preguntó el **A de `ftp`**, pero el servidor contestó que `ftp` es un **alias** (CNAME) de `www`, y además mandó los A de `www` para ahorrar otra consulta.

- **El A pertenece a `www`, no a `ftp`.** No escribas `ftp IN A 10.10.0.80`: eso sería otro registro distinto (y además un nombre con CNAME no puede tener otros registros).
- Los A de `www` ya los tenías del paquete 6, así que son **repetidos** y no se vuelven a escribir.

**Traducción (una sola línea nueva):**

```dns
ftp  IN  CNAME  www.parcial.lab.
```

---

### Paquete 14 — TXT

```text
    Queries
        parcial.lab: type TXT, class IN
    Answers
        parcial.lab: type TXT, class IN
            Name: parcial.lab
            Type: TXT (Text strings) (16)
            Time to live: 3600 (1 hour)
            TXT Length: 14
            TXT: v=spf1 mx -all
        parcial.lab: type TXT, class IN
            Name: parcial.lab
            Type: TXT (Text strings) (16)
            Time to live: 3600 (1 hour)
            TXT Length: 14
            TXT: parcial protos
```

**Qué mirar:** en la columna Info solo dice `TXT TXT`, **sin el texto**. Para leerlo hay que abrir el paquete. El texto va **entre comillas** en el archivo de zona, más que nada si tiene espacios.

**Traducción:**

```dns
@  IN  TXT  "v=spf1 mx -all"
@  IN  TXT  "parcial protos"
```

---

### Paquete 16 — respuesta vacía (NODATA): no aporta

```text
    Flags: 0x8580 Standard query response, No error
        .... .... .... 0000 = Reply code: No error (0)
    Answer RRs: 0
    Authority RRs: 1
    Additional RRs: 0
    Queries
        mail.parcial.lab: type MX, class IN
    Authoritative nameservers
        parcial.lab: type SOA, class IN, mname ns1.parcial.lab
            Name: parcial.lab
            Time to live: 3600 (1 hour)
            Primary name server: ns1.parcial.lab
            ...
```

**Qué mirar:** `No error` pero **`Answer RRs: 0`**. El nombre `mail.parcial.lab` existe (tiene un A), pero **no tiene MX**. La respuesta trae el SOA de la zona en **Authority**, que es como el servidor dice "pregunta válida, no tengo ese tipo".

- **No escribas** `mail IN MX ...`: la pregunta sola no es un registro.
- El SOA que viene acá es el mismo del paquete 2, así que es **repetido**.

**Traducción:** nada.

> Dato útil: si en la captura **nadie preguntó el SOA**, las respuestas vacías y las NXDOMAIN **igual lo traen en Authority**. Es otra forma de conseguirlo.

---

### Paquete 18 — NXDOMAIN: no aporta

```text
    Flags: 0x8583 Standard query response, No such name
        .... .1.. .... .... = Authoritative: Server is an authority for domain
        .... .... .... 0011 = Reply code: No such name (3)
    Answer RRs: 0
    Authority RRs: 1
    Queries
        dev.parcial.lab: type A, class IN
    Authoritative nameservers
        parcial.lab: type SOA, class IN, mname ns1.parcial.lab
```

**Qué mirar:** `No such name` (código 3): **`dev.parcial.lab` no existe** en la zona. En la lista de paquetes aparece directamente como `No such name`.

**Traducción:** nada. Y si el enunciado no te pide crearlo, **no lo agregues**: tu zona tiene que reproducir la original.

---

### Paquete 20 — respuesta de un caché: cuidado con el TTL

```text
No.  Source      Destination  Info
20   10.10.0.1   10.10.0.30   Standard query response 0x2001 A www.parcial.lab A 10.10.0.80 A 10.10.0.81
```

```text
    Flags: 0x8180 Standard query response, No error
        .... .0.. .... .... = Authoritative: Server is not an authority for domain
        .... .... 1... .... = Recursion available: Server can do recursive queries
    Answers
        www.parcial.lab: type A, class IN, addr 10.10.0.80
            Time to live: 187 (3 minutes, 7 seconds)
            Address: 10.10.0.80
        www.parcial.lab: type A, class IN, addr 10.10.0.81
            Time to live: 187 (3 minutes, 7 seconds)
            Address: 10.10.0.81
```

**Qué mirar:**
- La respuesta **no viene del servidor de la zona** (`10.10.0.53`), sino de `10.10.0.1`, un resolver con caché.
- `Authoritative: Server is not an authority`: no es la fuente original.
- `Time to live: 187`. El caché lo fue **descontando** desde 300. **No es el TTL real.**

**Regla:** los datos (IPs) sirven para confirmar, pero el **TTL se toma de la respuesta con autoridad** (paquete 6: `300`). Si un mismo registro aparece con TTLs distintos, el original es el de la respuesta con `aa` o, si no hay ninguna, el **mayor**.

**Traducción:** nada nuevo.

---

### Paquete 22 — repetido

Es igual al paquete 6: mismo dueño, mismo tipo, mismos datos y mismo TTL. **No se escribe dos veces.** Una zona no tiene registros duplicados.

**Traducción:** nada.

---

## 5. Tabla resumen de lo recuperado

| Paq. | Sección | Dueño | TTL | Tipo | Datos | ¿Va a la zona? |
|---:|---|---|---:|---|---|---|
| 2 | Answer | parcial.lab | 3600 | SOA | ns1 / admin / 2026111201 / 7200 / 1800 / 1209600 / 3600 | **Sí** |
| 4 | Answer | parcial.lab | 3600 | NS | ns1.parcial.lab | **Sí** |
| 4 | Answer | parcial.lab | 3600 | NS | ns2.parcial.lab | **Sí** |
| 4 | Additional | ns1.parcial.lab | 3600 | A | 10.10.0.53 | **Sí** |
| 4 | Additional | ns2.parcial.lab | 3600 | A | 10.10.0.54 | **Sí** |
| 6 | Answer | www.parcial.lab | 300 | A | 10.10.0.80 | **Sí** |
| 6 | Answer | www.parcial.lab | 300 | A | 10.10.0.81 | **Sí** |
| 8 | Answer | www.parcial.lab | 300 | AAAA | 2001:db8::80 | **Sí** |
| 10 | Answer | parcial.lab | 3600 | MX | 10 mail.parcial.lab | **Sí** |
| 10 | Answer | parcial.lab | 3600 | MX | 20 mx.backup.com | **Sí** |
| 10 | Additional | mail.parcial.lab | 3600 | A | 10.10.0.25 | **Sí** |
| 12 | Answer | ftp.parcial.lab | 3600 | CNAME | www.parcial.lab | **Sí** |
| 12 | Answer | www.parcial.lab | 300 | A | .80 / .81 | No: repetido (paq. 6) |
| 14 | Answer | parcial.lab | 3600 | TXT | "v=spf1 mx -all" | **Sí** |
| 14 | Answer | parcial.lab | 3600 | TXT | "parcial protos" | **Sí** |
| 16 | Authority | parcial.lab | 3600 | SOA | — | No: repetido; respuesta vacía |
| 18 | Authority | parcial.lab | 3600 | SOA | — | No: NXDOMAIN |
| 20 | Answer | www.parcial.lab | 187 | A | .80 / .81 | No: caché, TTL rebajado |
| 22 | Answer | www.parcial.lab | 300 | A | .80 / .81 | No: repetido |

---

## 6. La zona final

Supongamos que el enunciado además pide **agregar un TXT** `"cachito hola"` a la raíz. Entonces hay que **sumar 1 al serial** para registrar que la zona cambió (`2026111201` pasa a `2026111202`).

Archivo `/etc/bind/db.parcial.lab`:

```dns
$TTL 3600

@       IN  SOA   ns1.parcial.lab. admin.parcial.lab. (
                  2026111202  ; serial (2026111201 en la captura, +1 por el TXT nuevo)
                  7200        ; refresh
                  1800        ; retry
                  1209600     ; expire
                  3600        ; minimum
)

; --- Servidores de nombres (paq. 4) ---
@       IN  NS    ns1.parcial.lab.
@       IN  NS    ns2.parcial.lab.
ns1     IN  A     10.10.0.53
ns2     IN  A     10.10.0.54

; --- Web (paq. 6, 8 y 12) — TTL propio de 300 ---
www 300 IN  A     10.10.0.80
www 300 IN  A     10.10.0.81
www 300 IN  AAAA  2001:db8::80
ftp     IN  CNAME www.parcial.lab.

; --- Correo (paq. 10) ---
@       IN  MX    10 mail.parcial.lab.
@       IN  MX    20 mx.backup.com.
mail    IN  A     10.10.0.25

; --- Texto (paq. 14 + el pedido por el enunciado) ---
@       IN  TXT   "v=spf1 mx -all"
@       IN  TXT   "parcial protos"
@       IN  TXT   "cachito hola"     ; agregado por el enunciado
```

Como el enunciado dice **agregar**, se conservan los dos TXT originales y se suma el nuevo.

**Lo que conviene revisar antes de guardar:**
- Todo nombre completo (los destinos de NS, MX, CNAME y los dos del SOA) **termina en punto**. Sin el punto, `mail.parcial.lab` se lee como `mail.parcial.lab.parcial.lab.`.
- Los nombres de la izquierda (`www`, `ns1`, `mail`) van **sin** dominio y sin punto: BIND les agrega `parcial.lab.` solo.
- `@` es la raíz de la zona (`parcial.lab.`).
- Los registros con TTL distinto al `$TTL` lo llevan escrito (`www 300 ...`).

---

## 7. Declararla, validarla y cargarla

En `/etc/bind/named.conf.local`:

```conf
zone "parcial.lab" {
    type master;
    file "/etc/bind/db.parcial.lab";
};
```

Validar **antes** de recargar:

```bash
sudo named-checkzone parcial.lab /etc/bind/db.parcial.lab
sudo named-checkconf -z
```

- `named-checkzone ZONA ARCHIVO` revisa la sintaxis del archivo de zona. El nombre de zona tiene que ser el mismo que el de `named.conf.local`.
- `named-checkconf -z` revisa toda la configuración y trata de cargar todas las zonas.

Salida esperada del primer comando:

```text
zone parcial.lab/IN: parcial.lab/MX 'mx.backup.com' (out of zone) has no addresses records (A or AAAA)
zone parcial.lab/IN: loaded serial 2026111202
OK
```

La primera línea es solo un **aviso**: BIND no puede comprobar la IP de un servidor de correo que pertenece a otra zona. No impide cargar la zona. Lo que importa es `loaded serial` y `OK`.

Para ver cómo interpretó BIND cada línea, con todos los nombres completos y los TTL:

```bash
sudo named-checkzone -D -o - parcial.lab /etc/bind/db.parcial.lab
```

Si ahí aparece algo como `mail.parcial.lab.parcial.lab.`, falta un punto.

Recargar:

```bash
sudo systemctl reload bind9      # o: sudo rndc reload
```

---

## 8. Verificar contra la captura

Preguntale **directamente a tu BIND** con `@127.0.0.1` (si es un contenedor, usá su IP):

```bash
dig @127.0.0.1 parcial.lab SOA    +norecurse +noall +answer
dig @127.0.0.1 parcial.lab NS     +norecurse +noall +answer
dig @127.0.0.1 www.parcial.lab A  +norecurse +noall +answer
dig @127.0.0.1 www.parcial.lab AAAA +norecurse +noall +answer
dig @127.0.0.1 parcial.lab MX     +norecurse +noall +answer
dig @127.0.0.1 ftp.parcial.lab A  +norecurse +noall +answer
dig @127.0.0.1 parcial.lab TXT    +norecurse +noall +answer
```

- `+norecurse` pide que conteste solo con lo que sabe (como autoridad).
- `+noall +answer` muestra solo la sección de respuesta, para comparar línea a línea con tu tabla.

Salida esperada del TXT:

```text
parcial.lab.    3600  IN  TXT  "v=spf1 mx -all"
parcial.lab.    3600  IN  TXT  "parcial protos"
parcial.lab.    3600  IN  TXT  "cachito hola"
```

Para mostrar que la respuesta tiene **autoridad**, corré una sin `+noall` y señalá el flag `aa`:

```text
;; flags: qr aa; QUERY: 1, ANSWER: 3, AUTHORITY: 2, ADDITIONAL: 3
```

Los datos y TTL tienen que coincidir con la tabla de la sección 5. Para `www`, tiene que verse `300`, no `3600`.

---

## 9. Atajo: volcar todo con `tshark`

`tshark` es Wireshark por línea de comandos. Con esto ves todas las respuestas en una tabla, sin abrir paquete por paquete:

```bash
tshark -r captura.pcapng -Y "dns.flags.response == 1" \
  -T fields -E separator=' | ' \
  -e frame.number -e ip.src -e dns.flags.authoritative \
  -e dns.resp.name -e dns.resp.type -e dns.resp.ttl \
  -e dns.a -e dns.aaaa -e dns.ns -e dns.cname \
  -e dns.mx.preference -e dns.mx.mail_exchange -e dns.txt
```

- `-r` lee el archivo.
- `-Y` aplica el filtro (el mismo de Wireshark).
- `-T fields` imprime solo los campos que pedís con cada `-e`.
- Cuando un paquete tiene varios registros, los valores salen separados por coma, en orden.

Para ver el detalle completo de un paquete (como el panel del medio de Wireshark):

```bash
tshark -r captura.pcapng -Y "frame.number == 10" -V
```

Y para el SOA:

```bash
tshark -r captura.pcapng -Y "dns.resp.type == 6" -T fields \
  -e dns.soa.mname -e dns.soa.rname -e dns.soa.serial_number \
  -e dns.soa.refresh_interval -e dns.soa.retry_interval \
  -e dns.soa.expire_limit -e dns.soa.minimum_ttl
```

Si tu versión de `tshark` se queja de algún nombre de campo, buscalo en Wireshark: seleccioná el campo en el detalle y el nombre aparece abajo, en la barra de estado.

---

## 10. Errores típicos

| Error | Cómo evitarlo |
|---|---|
| Leer solo Answers | Revisá también **Authority** y **Additional**: ahí vienen los A de los NS y MX. |
| Anotar el A de `www` como si fuera de `ftp` (paq. 12) | Cada registro tiene su **Name**: el A es de `www`, no de quien preguntó. |
| Agregar registros por una pregunta sin respuesta (paq. 16 y 18) | Si `Answer RRs: 0` o `No such name`, **no hay registro**. |
| Usar el TTL de un caché (paq. 20) | Tomá el TTL de la respuesta con `Authoritative`. |
| Escribir todos los registros con el `$TTL` | Si uno tiene otro TTL en la captura, escribilo explícito. |
| Olvidar el punto final en nombres completos | `named-checkzone -D -o -` te muestra cómo quedaron. |
| Duplicar registros | Cada combinación dueño + tipo + datos va una sola vez. |
| Pisar los TXT originales al agregar uno | "Agregar" = los originales **más** el nuevo. |
| No subir el serial al cambiar la zona | Sumá 1 cada vez que la modificás. |
| Inventar un A para un MX externo | Si el nombre es de otra zona (`mx.backup.com`), no va en la tuya. |

---

## 11. Qué decirle al profe

> "Filtré las respuestas DNS de la captura y me quedé con las que mandó el servidor de la zona con el bit de autoridad. El SOA me dio el nombre de la zona y sus parámetros. Después recorrí cada respuesta mirando Answers, Authority y Additional, anoté dueño, TTL, tipo y datos de cada registro, y descarté los repetidos, las respuestas vacías, los NXDOMAIN y una respuesta de un caché que tenía el TTL rebajado. Escribí la zona respetando los TTL originales, agregué el TXT pedido y subí el serial. La validé con `named-checkzone` y verifiqué con `dig +norecurse` que BIND responde con autoridad (flag `aa`) y con los mismos datos que la captura."
