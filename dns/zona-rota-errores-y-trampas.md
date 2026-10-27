# DNS: zona rota, errores silenciosos y trampas

Para cuando el ejercicio de DNS viene con vueltas: una zona rota con errores sutiles, requisitos con detalles finos o registros raros. Complementa a:
- `zona-foo-example-org_1c2026.md`: crear una zona (procedimiento completo).
- `corregir-zona-it-itba_2c2025.md`: corregir una zona (el ejercicio del 2C 2025).
- `zona-variantes-extra.md`: PTR, delegación, SRV, comodín.

**Todos los mensajes de error de abajo son reales**: los obtuve corriendo `named-checkzone` (BIND 9.18) sobre zonas rotas a propósito.

---

## ⭐ Lo más importante: `named-checkzone OK` NO significa que la zona esté bien

Hay errores que BIND **acepta sin quejarse** porque son sintácticamente válidos, pero la zona queda mal. En la prueba, estos cinco dieron `OK`:

| Error | Qué queda en realidad | Cómo se ve |
|---|---|---|
| Nombre completo **sin punto final**: `web IN CNAME host.zona.test` | `host.zona.test.zona.test.` | `named-checkzone -D` |
| **`@` en el mail del SOA**: `admin@zona.test.` | `admin\@zona.test.`, una etiqueta rara | `named-checkzone -D` |
| **NS del SOA sin punto**: `ns1.zona.test admin...` | `ns1.zona.test.zona.test.` | `named-checkzone -D` |
| **TXT sin comillas**: `@ IN TXT v=spf1 ip4:1.2.3.4 -all` | tres textos separados: `"v=spf1" "ip4:1.2.3.4" "-all"`, y el SPF no funciona | `named-checkzone -D` |
| **Bucle de CNAME**: `a → b`, `b → a` | `dig` responde `SERVFAIL` | `dig @127.0.0.1 a.zona A` |

**Por eso, después del OK, siempre mirá la zona como la entendió BIND:**
~~~bash
sudo named-checkzone -D -o - ZONA /etc/bind/db.ZONA
~~~
- `-D` vuelca la zona ya interpretada, con todos los nombres completos.
- `-o -` la imprime en pantalla.

**Buscá a ojo:** un nombre con la zona **repetida** (`.zona.test.zona.test.`), una `\@` o comillas partidas. Si aparece algo así, es uno de estos errores.

---

## Mensaje de `named-checkzone` → qué está mal

| Mensaje (real) | Causa | Ejemplo roto | Arreglo |
|---|---|---|---|
| `bad dotted quad` | Un A no tiene una IPv4 válida | `www IN A host` / `www IN A 192.0.2.300` | Poner una IP real; si querés apuntar a un nombre, usar CNAME |
| `bad dotted quad` (cerca de un número) | TTL escrito **después** del tipo | `www IN A 3600 192.0.2.5` | El TTL va antes del tipo: `www 3600 IN A 192.0.2.5` |
| `bad IPv6 address` | AAAA con una IPv4 | `www IN AAAA 192.0.2.5` | AAAA solo lleva IPv6; para IPv4 es A |
| `CNAME and other data` | CNAME junto a otro registro del mismo nombre, o en la raíz | `@ IN CNAME host` / `www` con CNAME y TXT | El alias solo; en la raíz usar A |
| `not a valid number` | Falta la prioridad del MX (o un número del SOA) | `@ IN MX mail.zona.test.` | `@ IN MX 10 mail.zona.test.` |
| `empty label` | Dos puntos seguidos | `www..zona.test.` | Un solo punto |
| `unknown RR type '1hora'` | TTL mal escrito | `www 1hora IN A ...` | `1h`, `30m`, `1d`, `1w` o segundos |
| `unbalanced parentheses` | Falta `(` o `)` en el SOA | `SOA ... 2026102701 1h ... )` | Agregar el `(` |
| `has no NS records` | La zona no tiene NS en la raíz | — | `@ IN NS ns1.zona.` + el A de `ns1` |
| `NS 'x' has no address records` | El NS apunta a un host sin A (**no carga**) | `@ IN NS ns2` | Crear `ns2 IN A ...` |
| `MX 'x' is a CNAME (illegal)` | El MX apunta a un alias (carga, **pero está mal**) | `mail IN CNAME host` + `MX 10 mail` | Apuntar el MX a un nombre con A |
| `MX 'x' has no address records` | El MX apunta a un host sin A (carga, **pero está mal**) | `@ IN MX 10 correo` | Crear `correo IN A ...` o apuntar a uno que exista |
| `no TTL specified; using SOA MINTTL` | Falta `$TTL` arriba | — | Agregar `$TTL 1h` |
| `(out of zone) has no addresses` | El MX o NS es de **otro** dominio | `MX 10 smtp.otro.com.` | **No es error** si el enunciado lo pide (MX copiados de otro dominio) |

**Avisos que dicen OK pero hay que corregir igual:** `is a CNAME (illegal)` y `has no address records` en un MX. El enunciado espera que la zona funcione, no solo que cargue.

**`named-checkzone` puede mostrar un error y frenar.** Arreglá el que marca, volvé a correrlo, y repetí hasta que diga OK. Después, `-D`.

---

## Errores "lógicos" que no son de sintaxis

Pasan el chequeo pero el enunciado los considera errores:

| Revisá | Qué tiene que pasar |
|---|---|
| Serial | **Mayor** que el anterior. Formato `AAAAMMDDnn`. Si lo bajás, los secundarios ignoran el cambio |
| "Que se propague rápido" | Subir el serial y bajar `$TTL`, refresh, retry y negative TTL (ej. `300 / 300 / 60 / 60`) |
| TTL explícito alto en un registro | Bajar `$TTL` **no** cambia los registros que tienen su propio TTL escrito |
| Responsable con punto en el usuario | `juan.perez@dom` → `juan\.perez.dom.` (si no se escapa, el usuario queda "juan" en `perez.dom`) |
| MX "manteniendo el orden" | Mismos **números** de prioridad que el original, no 10, 20 inventados |
| SPF "solo X" | Termina en `-all`, no `~all`, y va **entre comillas** |
| Alias en la raíz | Imposible con CNAME: la raíz lleva A |
| NS/MX hacia un nombre de la zona | Ese nombre necesita su A en la zona |
| El A del NS | Si el NS es `ns1.zona.`, tiene que existir `ns1 IN A ...` |
| CNAME en cadena | Que termine en un nombre con A (sin bucles) |

---

## Procedimiento "picante" (cuando la zona viene rota)

~~~bash
# 1. Bajar o copiar la zona y guardar el original
curl -s http://protos.foo/zona -o /tmp/zona.original
sudo cp /tmp/zona.original /etc/bind/db.ZONA

# 2. Errores de sintaxis: corregir de a uno hasta que dé OK
sudo named-checkzone ZONA /etc/bind/db.ZONA

# 3. Errores silenciosos: mirar cómo quedó
sudo named-checkzone -D -o - ZONA /etc/bind/db.ZONA
#    buscar: zona repetida, \@, "texto" "partido", MX/NS sin A

# 4. Lógica: serial, tiempos SOA, TTL, responsable, MX, SPF (tabla de arriba)

# 5. Cargar y probar
sudo named-checkconf
sudo systemctl restart bind9
for t in SOA NS MX TXT; do dig @127.0.0.1 ZONA $t +noall +answer; done
dig @127.0.0.1 HOST.ZONA A +noall +answer +comments | grep -E "status|IN"
~~~
En el paso 5, cada consulta tiene que dar `status: NOERROR` y el flag `aa`. Un `SERVFAIL` en un nombre suele ser un bucle de CNAME.

**Mostrar la diferencia en el video:**
~~~bash
diff /tmp/zona.original /etc/bind/db.ZONA
~~~
Muestra línea por línea qué cambiaste: `<` es la versión original y `>` la corregida.

---

## Requisitos "picantes" al crear una zona

| El enunciado dice… | Trampa | Cómo va |
|---|---|---|
| "contacto `juan.perez@x.com`" | El punto del usuario | `juan\.perez.x.com.` |
| "A a la IP de `host.algo`" | `host.algo` es un CNAME | `dig +short A host.algo`: la **última** línea es la IP |
| "mismos MX que `otro.dom`, manteniendo el orden" | `dig` los rota | `dig +short MX otro.dom \| sort -n`, mismos números |
| "validez de 90 minutos / 2 días" | Unidades | `90m`, `2d` (o `5400`, `172800`) |
| "`www` y `ftp` alias de la raíz" | Dos registros | Uno por alias; `CNAME @` |
| "el correo lo atiende `mail` de esta zona" | Necesita su A | `MX 10 mail.zona.` + `mail IN A ...` |
| "solo los servidores de correo pueden enviar" | SPF con `mx` | `"v=spf1 mx -all"` |
| "solo `1.2.3.4` y la red `10.0.0.0/24`" | Varias reglas | `"v=spf1 ip4:1.2.3.4 ip4:10.0.0.0/24 -all"` |
| "cualquier subdominio" | Comodín | `* IN A ...` |
| "resolución inversa" | Otra zona | `in-addr.arpa` + PTR (ver `zona-variantes-extra.md`) |

---

## Preguntas que te pueden hacer en el video
- **¿Por qué el OK de `named-checkzone` no alcanza?** Porque solo valida sintaxis. Un nombre sin punto final es válido, pero apunta a otro lado.
- **¿Para qué subo el serial?** Los secundarios comparan el serial para saber si tienen que transferir la zona.
- **¿Por qué bajo refresh y retry?** Los secundarios preguntan más seguido y ven el cambio antes.
- **¿Por qué bajo el TTL?** Las cachés guardan los registros menos tiempo y piden la versión nueva antes.
- **¿Por qué el MX no puede ir a un CNAME?** El RFC lo prohíbe: los servidores de correo esperan un nombre con A directo.
