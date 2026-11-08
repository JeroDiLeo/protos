# Zona DNS `carlitos.com.ar` — resolución paso a paso

## Enunciado (textual)

*Fuente: Ejercicios de repaso práctica — Ejercicios varios.*

Configurar un servidor DNS para servir la zona `carlitos.com.ar`

- El servidor será la autoridad de dicha zona
- El responsable debe ser `carloselmascapo@carlitos.com.ar`
- `carlitos.com.ar` debe tener un registro A apuntando a `1.2.3.4` con un tiempo de vida de dos horas
- El subdominio `mysite` debe ser un registro CNAME apuntando a `example.org` y debe tener una validez de una semana
- El dominio para recibir correo electrónico debe ser `mail20.carlitos.com.ar`, `mail30.carlitos.com.ar` y `mail40.carlitos.com.ar` con las métricas 20, 30 y 40 respectivamente y una validez de 1 día
- Muestre con dig como su servidor DNS sirve todos estos registros

---

## Objetivo

Servir la zona `carlitos.com.ar` con BIND 9 en la VM propia (Ubuntu, `jerOS`). Práctica hecha el 07/11/2026; los comandos los corrió el estudiante y las salidas de abajo son las reales.

No hace falta pampero ni el laboratorio de The Vault: alcanza con cualquier Linux con BIND instalado.

## Traducción de requisitos

Antes de escribir nada, cada línea del enunciado se traduce a un registro DNS:

| El enunciado dice | Registro | Cómo queda escrito |
|---|---|---|
| "El servidor será la autoridad de dicha zona" | `type master` + SOA + NS | `zone "carlitos.com.ar" { type master; ... }` y `IN NS ns1.carlitos.com.ar.` |
| "El responsable debe ser carloselmascapo@carlitos.com.ar" | SOA, campo RNAME | `carloselmascapo.carlitos.com.ar.` (la `@` pasa a ser `.`) |
| "carlitos.com.ar ... registro A ... 1.2.3.4 ... dos horas" | A en la raíz (`@`) | `@ 7200 IN A 1.2.3.4` |
| "mysite ... CNAME ... example.org ... una semana" | CNAME | `mysite 604800 IN CNAME example.org.` |
| "recibir correo ... mail20/30/40 ... métricas 20, 30, 40 ... 1 día" | 3 MX en la raíz | `@ 86400 IN MX 20 mail20.carlitos.com.ar.` (y 30, 40) |
| "Muestre con dig" | verificación | `dig @127.0.0.1 <nombre> <tipo>` |

Conversión de tiempos (TTL en segundos):

| Pedido | Cuenta | Segundos |
|---|---|---|
| 2 horas | 2 × 3600 | `7200` |
| 1 día | 24 × 3600 | `86400` |
| 1 semana | 7 × 86400 | `604800` |

---

## Paso 1 — Ver cómo está configurado BIND

Antes de agregar una zona, mirar qué hay para seguir el mismo esquema y no pisar nada.

```bash
cat /etc/bind/named.conf.local
ls /etc/bind/
ls /var/cache/bind/ 2>/dev/null
```

| Parte | Qué hace |
|---|---|
| `cat` | Muestra el contenido de un archivo. |
| `/etc/bind/named.conf.local` | Donde se declaran las zonas propias (las que sirve este servidor). |
| `ls /etc/bind/` | Lista la carpeta de configuración: ahí están los archivos de zona `db.*`. |
| `ls /var/cache/bind/` | Otra ubicación habitual de zonas (y donde BIND guarda las zonas de los slaves). |
| `2>/dev/null` | Descarta los errores (si la carpeta no existe, no ensucia la salida). |

Salida real (resumida):

```text
// E50 - Zona directa
zone "foo.pdc.lab" {
    type primary;
    file "/etc/bind/db.foo.pdc.lab";
};
...
//Parcial 2C 2025 - Ejercicio 3
zone "it.itba.edu.ar" {
    type master;
    file "/etc/bind/db.it.itba.edu.ar";
};
db.10.0.2           db.foo.pdc.lab     named.conf        named.conf.options          named.conf.root-hints
db.foo.example.org  db.it.itba.edu.ar  named.conf.local  named.conf.options.pre-e54  rndc.key
managed-keys.bind  managed-keys.bind.jnl
```

**Qué nos dice:** cada zona se declara con un bloque `zone` y vive en su propio archivo `/etc/bind/db.<zona>`. Vamos a hacer lo mismo con `carlitos.com.ar`.

---

## Paso 2 — Declarar la zona en `named.conf.local`

```bash
sudo nano /etc/bind/named.conf.local
```

| Parte | Qué hace |
|---|---|
| `sudo` | Ejecuta con permisos de root (los archivos de `/etc/bind` son del sistema). |
| `nano` | Editor de texto en la terminal. Guardar: `Ctrl+O` y Enter. Salir: `Ctrl+X`. |

Al final del archivo, sin borrar las zonas que ya estaban, se agrega:

```
//Ejercicio - DNS zona carlitos.com.ar
zone "carlitos.com.ar" {
    type master;
    file "/etc/bind/db.carlitos.com.ar";
};
```

| Línea | Qué significa |
|---|---|
| `zone "carlitos.com.ar"` | El nombre de la zona que va a servir este BIND. |
| `type master;` | Este servidor es la **autoridad**: los datos los escribimos acá a mano. `primary` es sinónimo. |
| `file "..."` | Ruta al archivo con los registros de la zona. |
| `;` al final de cada línea y después de `}` | Obligatorio en `named.conf`. Si falta, `named-checkconf` falla. |

### ¿Por qué `master`?

| Tipo | Cuándo se usa |
|---|---|
| `master` / `primary` | El servidor **es la autoridad**: tiene el archivo original de la zona. Es lo que pide "el servidor será la autoridad". |
| `slave` / `secondary` | Copia la zona de otro servidor por transferencia (AXFR). En vez de escribirla, se pone `masters { IP; };`. |
| `forward` | No tiene la zona: reenvía las consultas a otro DNS (`forwarders { IP; };`). |
| `hint` | Lista de servidores raíz de internet (la trae `named.conf.root-hints`). |
| `stub` | Copia solo los NS de la zona. Casi no se usa. |

---

## Paso 3 — Escribir el archivo de zona

```bash
sudo nano /etc/bind/db.carlitos.com.ar
```

Contenido final:

```
$TTL    86400
@       IN      SOA     ns1.carlitos.com.ar. carloselmascapo.carlitos.com.ar. (
                              2026110701   ; Serial
                              3600         ; Refresh
                              1800         ; Retry
                              604800       ; Expire
                              86400 )      ; Minimum TTL

        IN      NS      ns1.carlitos.com.ar.
ns1     IN      A       1.2.3.4
@       7200    IN      A       1.2.3.4
mysite  604800  IN      CNAME   example.org.

@       86400   IN      MX      20      mail20.carlitos.com.ar.
@       86400   IN      MX      30      mail30.carlitos.com.ar.
@       86400   IN      MX      40      mail40.carlitos.com.ar.
mail20  IN      A       1.2.3.5
mail30  IN      A       1.2.3.6
mail40  IN      A       1.2.3.7
```

### Formato general de un registro

```
<nombre>   <TTL>   <clase>   <tipo>   <datos>
```

- **nombre**: `@` = la zona (`carlitos.com.ar.`). Un nombre sin punto final (`mysite`) es **relativo**: BIND le agrega `.carlitos.com.ar.`. Un nombre con punto final (`example.org.`) es **absoluto**.
- **TTL**: opcional. Si no está, se usa el `$TTL`.
- **clase**: `IN` (Internet), siempre.
- Si la línea empieza con espacios (sin nombre), hereda el nombre de la línea anterior. Por eso el `IN NS` de arriba es de `@`.

### Línea por línea

| Línea | Explicación |
|---|---|
| `$TTL 86400` | TTL por defecto para todo registro que no tenga uno propio: 1 día. |
| `@ IN SOA ns1.carlitos.com.ar. ...` | **Start Of Authority**: dice que esta zona tiene autoridad acá. El primer nombre es el servidor primario de la zona (MNAME). |
| `carloselmascapo.carlitos.com.ar.` | **Responsable** (RNAME): el mail `carloselmascapo@carlitos.com.ar` con la `@` reemplazada por `.`. La `@` no se puede usar porque en el archivo significa "la zona". Si la parte de antes de la `@` tuviera puntos (ej. `carlos.perez@...`), cada uno se escribe `\.` → `carlos\.perez.carlitos.com.ar.` |
| `2026110701 ; Serial` | Versión de la zona, formato `AAAAMMDDnn`. **Hay que subirlo cada vez que se modifica la zona** (si no, los secundarios no se enteran del cambio). |
| `3600 ; Refresh` | Cada cuánto un secundario pregunta si cambió el serial (1 h). |
| `1800 ; Retry` | Si falló el refresh, cada cuánto reintenta (30 min). |
| `604800 ; Expire` | Si el secundario no logra hablar con el primario durante este tiempo, deja de responder la zona (1 semana). |
| `86400 ; Minimum` | TTL del **caché negativo**: cuánto se recuerda que un nombre no existe (NXDOMAIN). |
| `IN NS ns1.carlitos.com.ar.` | El servidor de nombres autoritativo de la zona. Toda zona necesita al menos un NS. |
| `ns1 IN A 1.2.3.4` | El NS está dentro de la zona, así que tiene que resolver a una IP (registro *glue*). Sin esto, `named-checkzone` avisa que el NS no tiene dirección. |
| `@ 7200 IN A 1.2.3.4` | Pedido del enunciado: `carlitos.com.ar` → `1.2.3.4`, TTL 2 horas. |
| `mysite 604800 IN CNAME example.org.` | Pedido del enunciado: `mysite.carlitos.com.ar` es un alias de `example.org`, TTL 1 semana. El punto final de `example.org.` es obligatorio: sin él quedaría `example.org.carlitos.com.ar.` |
| `@ 86400 IN MX 20 mail20.carlitos.com.ar.` | Pedido del enunciado: los mails para `@carlitos.com.ar` los recibe `mail20`, con prioridad 20. **Menor número = más prioridad**: primero se intenta `mail20`, después `mail30`, después `mail40`. |
| `mail20 IN A 1.2.3.5` (y 30, 40) | El enunciado no da IPs para los servidores de correo, pero un MX tiene que apuntar a un nombre que resuelva. Se ponen IPs de prueba. |

### Por qué los MX van en `@`

"El dominio para recibir correo electrónico debe ser mail20, mail30 y mail40" quiere decir que **esos tres son los servidores que reciben el correo de `carlitos.com.ar`**. Los MX se ponen en el nombre del dominio que recibe correo (la raíz, `@`), y apuntan a los servidores.

---

## Paso 4 — Validar el archivo de zona

```bash
sudo named-checkzone carlitos.com.ar /etc/bind/db.carlitos.com.ar
```

| Parte | Qué hace |
|---|---|
| `named-checkzone` | Lee el archivo como lo haría BIND y reporta errores de sintaxis o de consistencia, sin tocar el servicio. |
| `carlitos.com.ar` | Nombre de la zona. Tiene que ser el mismo del bloque `zone "..."`: con él se completan los nombres relativos. |
| `/etc/bind/db.carlitos.com.ar` | Archivo a validar. |

Salida real:

```text
zone carlitos.com.ar/IN: loaded serial 2026110701
OK
```

`loaded serial 2026110701` confirma que leyó el SOA; `OK` = sin errores. Si hubiera un error, diría la línea (ej. `db.carlitos.com.ar:12: unknown RR type 'CNAM'`).

---

## Paso 5 — Validar la configuración y recargar BIND

```bash
sudo named-checkconf
sudo systemctl reload bind9
sudo systemctl status bind9
```

| Comando | Qué hace |
|---|---|
| `named-checkconf` | Valida `named.conf` y todo lo que incluye (`named.conf.local`, etc.). **Si está todo bien no imprime nada.** Si falta un `;` o una llave, dice archivo y línea. |
| `systemctl reload bind9` | Le pide a BIND que relea la configuración y las zonas sin cortar el servicio (internamente corre `rndc reload`). |
| `systemctl status bind9` | Muestra si el servicio está activo y los últimos mensajes del log. |

Salida real de `status` (recortada):

```text
● named.service - BIND Domain Name Server
     Active: active (running) since Sat 2026-11-07 18:44:31 -03; 2h 56min ago
    Process: 68926 ExecReload=/usr/sbin/rndc reload (code=exited, status=0/SUCCESS)
...
Nov 07 21:40:51 jerOS named[1662]: network unreachable resolving './DNSKEY/IN': 2001:7fd::1#53
Nov 07 21:40:51 jerOS named[1662]: all zones loaded
Nov 07 21:40:51 jerOS named[1662]: running
```

- `active (running)` y `ExecReload ... status=0/SUCCESS`: la recarga funcionó.
- `all zones loaded`: tomó la zona nueva.
- `network unreachable resolving './DNSKEY/IN': 2001:...`: BIND intenta validar las claves DNSSEC de la raíz por IPv6 y la VM no tiene salida IPv6. No tiene nada que ver con la zona.

---

## Paso 6 — Mostrar con `dig` que sirve todos los registros

```bash
dig @127.0.0.1 carlitos.com.ar A +noall +answer
dig @127.0.0.1 mysite.carlitos.com.ar CNAME +noall +answer
dig @127.0.0.1 carlitos.com.ar MX +noall +answer
dig @127.0.0.1 carlitos.com.ar SOA +noall +answer
```

| Parte | Qué hace |
|---|---|
| `dig` | Cliente DNS: hace una consulta y muestra la respuesta. |
| `@127.0.0.1` | Le pregunta a **nuestro BIND** y no al resolvedor del sistema (`127.0.0.53` en Ubuntu). Sin esto, la respuesta podría no venir de nuestro servidor. |
| `carlitos.com.ar` | Nombre a consultar. |
| `A` / `CNAME` / `MX` / `SOA` | Tipo de registro pedido. |
| `+noall +answer` | Oculta todo el output y muestra solo la sección ANSWER. Queda limpio para mostrar. |

Salida real:

```text
carlitos.com.ar.	7200	IN	A	1.2.3.4
mysite.carlitos.com.ar.	604800	IN	CNAME	example.org.
carlitos.com.ar.	86400	IN	MX	20 mail20.carlitos.com.ar.
carlitos.com.ar.	86400	IN	MX	30 mail30.carlitos.com.ar.
carlitos.com.ar.	86400	IN	MX	40 mail40.carlitos.com.ar.
carlitos.com.ar.	86400	IN	SOA	ns1.carlitos.com.ar. carloselmascapo.carlitos.com.ar. 2026110701 3600 1800 604800 86400
```

Columnas: nombre, TTL, clase, tipo, datos.

| Requisito | Qué muestra el dig | ¿Cumple? |
|---|---|---|
| A a 1.2.3.4, 2 horas | `7200 IN A 1.2.3.4` | ✔ |
| mysite CNAME a example.org, 1 semana | `604800 IN CNAME example.org.` | ✔ |
| MX mail20/30/40 con 20/30/40, 1 día | tres `86400 IN MX` con 20, 30, 40 | ✔ |
| Responsable carloselmascapo@carlitos.com.ar | `carloselmascapo.carlitos.com.ar.` en el SOA | ✔ |
| Servidor con autoridad | responde el SOA; con el output completo de `dig` aparece el flag `aa` | ✔ |

### Para mostrar la autoridad

Sin `+noall +answer`, el encabezado trae los flags. El flag **`aa`** (*authoritative answer*) es la prueba de que el servidor es la autoridad:

```bash
dig @127.0.0.1 carlitos.com.ar SOA
```

```text
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 11547
;; flags: qr aa rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 1
```

Lo que importa es `status: NOERROR` y que esté `aa`. (`ra` aparece si tu BIND tiene la recursión activada, como en Ubuntu por defecto.)

### Todo de una vez

```bash
dig @127.0.0.1 carlitos.com.ar AXFR
```

`AXFR` pide la **transferencia de zona completa**: muestra todos los registros juntos. Funciona desde la misma máquina porque BIND la permite por defecto; si la configuración tiene `allow-transfer { none; };`, devuelve `Transfer failed`.

---

## Si algo falla

| Síntoma | Causa probable | Arreglo |
|---|---|---|
| `named-checkzone`: `unknown RR type` | Tipo mal escrito (`CNAM`, `MX20` sin espacio) | Corregir el tipo. |
| `named-checkzone`: `NS 'ns1.carlitos.com.ar' has no address records` | El NS está en la zona y no tiene A | Agregar `ns1 IN A <IP>`. |
| `named-checkzone`: `CNAME and other data` | Un nombre tiene CNAME y además otro registro | Un nombre con CNAME no puede tener nada más. |
| `named-checkconf`: `missing ';' before '}'` | Falta un `;` en el bloque `zone` | Agregarlo. |
| `dig` devuelve `status: REFUSED`, o responde pero **sin** el flag `aa` | BIND no tiene la zona cargada (no se recargó o el nombre de zona no coincide) y la está rechazando o buscando afuera | `sudo systemctl reload bind9` y revisar `zone "carlitos.com.ar"`. |
| `dig` devuelve `status: SERVFAIL` | La zona no cargó (error en el archivo) | `sudo journalctl -u named -n 30` muestra el error. |
| `dig` muestra `mysite... CNAME example.org.carlitos.com.ar.` | Faltó el punto final en `example.org` | Escribir `example.org.` |
| Cambié la zona y `dig` muestra lo viejo | No se recargó, o no se subió el serial | Subir el serial y `sudo rndc reload carlitos.com.ar`. |

---

## Resumen de comandos

```bash
sudo nano /etc/bind/named.conf.local                                # declarar la zona
sudo nano /etc/bind/db.carlitos.com.ar                              # escribir los registros
sudo named-checkzone carlitos.com.ar /etc/bind/db.carlitos.com.ar   # validar zona
sudo named-checkconf                                                # validar config (silencio = OK)
sudo systemctl reload bind9                                         # aplicar
sudo systemctl status bind9                                         # ver que esté running
dig @127.0.0.1 carlitos.com.ar A +noall +answer                     # verificar cada registro
dig @127.0.0.1 mysite.carlitos.com.ar CNAME +noall +answer
dig @127.0.0.1 carlitos.com.ar MX +noall +answer
dig @127.0.0.1 carlitos.com.ar SOA +noall +answer
```

Para registros que no aparecen en este ejercicio (SPF, PTR, delegación, etc.) ver [cheatsheet-dns.md](cheatsheet-dns.md) y [zona-variantes-extra.md](zona-variantes-extra.md).
