# Protocolos — 2C 2022, Ejercicio 2/4: zona DNS demiloo.com.ar

## Consigna (textual, foto del parcial)
Instale un servidor de nombres BIND y realice los cambios necesarios para servir la zona `demiloo.com.ar` considerando que:
1. su servidor de DNS será la autoridad para estas zonas
2. la dirección de contacto con la persona responsable por la zona es `demiloo@leak.com.ar`
3. `demiloo.com.ar` debe tener un registro A apuntando a la dirección IP de `foo.leak.com.ar`. El registro tendrá una validez de **1 hora**.
4. el subdominio `www` debe ser registro CNAME apuntando a la raíz de la zona. Validez de **2 semanas**.
5. la zona debe poder recibir correos electrónicos. El correo será atendido por los mismos servidores que atienden el dominio `proto.leak.com.ar` (**manteniendo el orden**). Validez de **1 semana**.

Deberá demostrar la correcta configuración utilizando dig.

> Es el mismo molde que 26.1-1 (foo.example.org). Solo cambian los datos.

---

## ⭐ RECETA PARA EL PARCIAL

### Paso 0 — Consigna → registros
| La consigna dice | Registro | Cómo se escribe |
|---|---|---|
| autoridad | SOA + NS | `@ IN SOA ns.demiloo.com.ar. ...` y `@ IN NS ns.demiloo.com.ar.` + `ns IN A 127.0.0.1` |
| responsable `demiloo@leak.com.ar` | SOA (RNAME) | `demiloo.leak.com.ar.` (la `@` pasa a `.`; no hay puntos en el usuario → nada que escapar) |
| A a la IP de `foo.leak.com.ar`, 1 hora | A | `@ 1h IN A <IP>` → la IP se **consulta** |
| `www` CNAME a la raíz, 2 semanas | CNAME | `www 2w IN CNAME demiloo.com.ar.` |
| MX iguales a `proto.leak.com.ar`, en orden, 1 semana | MX | una línea por MX, **mismas prioridades** → se **consultan** |

### Paso 1 — Mostrar BIND y conseguir los datos externos
~~~bash
systemctl status bind9
sudo systemctl stop bind9                       # el video arranca mostrando que no corre
dig +short A foo.leak.com.ar                    # IP para el registro A
dig +short MX proto.leak.com.ar | sort -n       # prioridad + host de cada MX, ordenados
~~~
- `+short`: solo los valores, para copiarlos.
- `sort -n`: ordena por el número de prioridad. `dig` puede devolver los MX en cualquier orden (en la prueba salió 21 antes que 20): **el orden lo da el número, no la línea**.
- Si `foo.leak.com.ar` es un CNAME, `dig +short A` muestra la cadena y al final la IP: copiar **la IP** (la última línea).

### Paso 2 — Declarar la zona
~~~bash
sudo nano /etc/bind/named.conf.local
~~~
~~~conf
zone "demiloo.com.ar" {
    type master;
    file "/etc/bind/db.demiloo.com.ar";
};
~~~

### Paso 3 — Archivo de zona
~~~bash
sudo nano /etc/bind/db.demiloo.com.ar
~~~
~~~dns
$ORIGIN demiloo.com.ar.
$TTL 1h
@ IN SOA ns.demiloo.com.ar. demiloo.leak.com.ar. (
    2026102701 ; serial
    1h         ; refresh
    15m        ; retry
    1w         ; expire
    1h )       ; negative TTL

@   IN NS ns.demiloo.com.ar.
ns  IN A  127.0.0.1

@   1h IN A     <IP de foo.leak.com.ar>
www 2w IN CNAME demiloo.com.ar.
@   1w IN MX    <prio1> <host1>.
@   1w IN MX    <prio2> <host2>.
~~~
Con los datos históricos de `proto.leak.com.ar` (2020) las dos líneas MX quedaban:
~~~dns
@   1w IN MX    20 smtp20.proto.leak.com.ar.
@   1w IN MX    21 smtp30.proto.leak.com.ar.
~~~
**Copiar los valores que dé `dig` ese día**, no estos.

### Paso 4 — Validar y levantar
~~~bash
sudo named-checkzone demiloo.com.ar /etc/bind/db.demiloo.com.ar
sudo named-checkconf
sudo systemctl start bind9
~~~
`named-checkzone` puede mostrar este **aviso**, que **no es error** (termina en `OK`):
~~~text
demiloo.com.ar/MX 'smtp20.proto.leak.com.ar' (out of zone) has no addresses records (A or AAAA)
...
OK
~~~
Significa que los hosts de los MX son de otra zona y BIND no puede verificarlos desde el archivo. Es esperado: el enunciado pide usar los servidores de otro dominio.

### Paso 5 — Demostrar con dig
~~~bash
dig @127.0.0.1 demiloo.com.ar A
dig @127.0.0.1 www.demiloo.com.ar CNAME
dig @127.0.0.1 demiloo.com.ar MX
dig @127.0.0.1 demiloo.com.ar SOA
~~~
Qué mirar (salida real de la prueba en un BIND local):
~~~text
demiloo.com.ar.      3600     IN  A      52.92.161.219            ← 1 hora
www.demiloo.com.ar.  1209600  IN  CNAME  demiloo.com.ar.          ← 2 semanas
demiloo.com.ar.      604800   IN  MX     21 smtp30.proto.leak.com.ar.   ← 1 semana
demiloo.com.ar.      604800   IN  MX     20 smtp20.proto.leak.com.ar.
demiloo.com.ar.      3600     IN  SOA    ns.demiloo.com.ar. demiloo.leak.com.ar. 2026102701 ...
;; flags: qr aa rd                                                ← aa = respuesta autoritativa
~~~
- `@127.0.0.1`: pregunto a **mi** BIND; el DNS del sistema no conoce la zona.
- Sin `+short`, para que se vean TTL y el flag `aa`.
- Los MX pueden aparecer rotados: lo que importa es que las **prioridades** coincidan con las de `proto.leak.com.ar`.

### Conversión de tiempos (para verificar lo que muestra dig)
| Consigna | En el archivo | dig muestra |
|---|---|---|
| 1 hora | `1h` | 3600 |
| 1 semana | `1w` | 604800 |
| 2 semanas | `2w` | 1209600 |

### Para el video
"Cada requisito es un registro: autoridad con SOA y NS, el responsable en el SOA con la `@` convertida en punto, el A con la IP de foo.leak.com.ar que consulté con dig, el CNAME de www a la raíz y los MX copiados de proto.leak.com.ar con las mismas prioridades. Los TTL de 1 hora, 2 semanas y 1 semana se ven en dig como 3600, 1209600 y 604800, y el flag `aa` muestra que mi servidor es la autoridad."

### Errores típicos
| Error | Consecuencia |
|---|---|
| `demiloo@leak.com.ar.` en el SOA | la `@` no va: es `demiloo.leak.com.ar.` |
| host de MX sin punto final | se convierte en `smtp20.proto.leak.com.ar.demiloo.com.ar.` |
| renumerar las prioridades (10, 20) | no "mantiene el orden" de proto.leak.com.ar: copiar los números exactos |
| TTL después de `IN A` (`@ IN A 1h ...`) | `1h` queda en el lugar del dato: error de sintaxis |
| no subir el serial al editar | secundarios no ven el cambio |
| `dig` sin `@127.0.0.1` | NXDOMAIN o datos de otro servidor |

### Variantes
| Si cambia... | Tocás |
|---|---|
| responsable con punto en el usuario (`juan.perez@x.com`) | `juan\.perez.x.com.` |
| la IP es literal | `@ 1h IN A 1.2.3.4` sin consultar |
| varios alias (`www`, `ftp`) | una línea CNAME por cada uno |
| MX propios | `@ IN MX 10 mail.demiloo.com.ar.` + `mail IN A <IP>` (el MX no puede apuntar a un CNAME) |
| piden además SPF | `@ IN TXT "v=spf1 ip4:X -all"` (o `mx -all` si son "los servidores de correo") |
