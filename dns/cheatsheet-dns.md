# Cheatsheet: DNS (dig, registros, zonas, BIND)

Recetas de parciales: [zona-foo-example-org_1c2026.md](zona-foo-example-org_1c2026.md) · [corregir-zona-it-itba_2c2025.md](corregir-zona-it-itba_2c2025.md) · [mx-spf_recu2020.md](mx-spf_recu2020.md) · [zona-demiloo_2c2022.md](zona-demiloo_2c2022.md) · [zona-rota-errores-y-trampas.md](zona-rota-errores-y-trampas.md) · [zona-variantes-extra.md](zona-variantes-extra.md) · capturas: [../pcap/pcap.md](../pcap/pcap.md).

---

## 1. Formato de `dig`

~~~bash
dig [@servidor] [-p puerto] nombre [TIPO] [+opciones]
dig @127.0.0.1 -p 5353 empresa.lab MX +short
~~~
- Sin `@servidor` pregunta al resolver del sistema (`/etc/resolv.conf`). **Un nombre de laboratorio (`.lab`, `.foo`) solo existe en el servidor que te dan**: si no ponés `@IP -p PUERTO` te da `NXDOMAIN`.
- Sin `TIPO` pregunta por **A**.
- El orden no importa: `dig MX empresa.lab @1.2.3.4` también anda.

### Opciones más usadas
| Opción | Qué hace | Cuándo |
|---|---|---|
| `@IP` | a qué servidor le preguntás | servidor de referencia, tu BIND (`@127.0.0.1`), el autoritativo |
| `-p PUERTO` | puerto del servidor (por defecto 53) | "servidor DNS en 127.0.0.1:5354" |
| `+short` | solo la respuesta | sacar un dato para usarlo (passphrase, IP) |
| `+noall +answer` | solo la sección ANSWER, con nombre/TTL/tipo | ver la respuesta completa sin ruido |
| `+noall +answer +authority +additional` | elegir secciones | ver NS/glue |
| `-x IP` | consulta inversa (PTR) | "¿qué nombre tiene la IP X?" |
| `+trace` | resuelve desde la raíz siguiendo delegaciones | "¿quién es autoridad?", ver delegación |
| `+norec` | no pide recursión | preguntarle al autoritativo solo lo suyo |
| `+tcp` | usa TCP | respuestas grandes, probar TCP/53 |
| `AXFR` | transferencia de zona completa | "obtenga todos los registros de la zona" (si el server lo permite) |
| `+nocmd +nostats` | menos ruido | — |
| `+dnssec` | trae firmas RRSIG | DNSSEC |
| `-4` / `-6` | fuerza transporte | — |
| `+time=2 +tries=1` | timeouts cortos | server que no responde |

### Equivalentes
| dig | host | nslookup |
|---|---|---|
| `dig X A +short` | `host X` | `nslookup X` |
| `dig X MX` | `host -t MX X` | `nslookup -type=MX X` |
| `dig @S -p P X` | `host X S` (sin puerto) | `nslookup -port=P X S` |
| `dig -x IP` | `host IP` | `nslookup IP` |

---

## 2. Tipos de registro

| Tipo | Contiene | Ejemplo en zona | Consulta |
|---|---|---|---|
| **A** | IPv4 de un nombre | `www IN A 10.0.0.5` | `dig www.x.lab A` |
| **AAAA** | IPv6 | `www IN AAAA 2001:db8::5` | `dig www.x.lab AAAA` |
| **CNAME** | alias → otro nombre | `web IN CNAME www` | `dig web.x.lab` (sigue el alias) |
| **MX** | servidor de correo del dominio, con **prioridad** (menor = primero) | `@ IN MX 10 mail` | `dig x.lab MX` |
| **NS** | servidores autoritativos de la zona | `@ IN NS ns1` | `dig x.lab NS` |
| **SOA** | datos de la zona: NS primario, mail del responsable, **serial**, timers | `@ IN SOA ns1 admin ( … )` | `dig x.lab SOA` |
| **TXT** | texto libre (SPF, verificaciones, pistas) | `@ IN TXT "v=spf1 mx -all"` | `dig x.lab TXT` |
| **PTR** | IP → nombre (zona inversa) | `5 IN PTR www.x.lab.` | `dig -x 10.0.0.5` |
| **SRV** | servicio: prioridad peso puerto host | `_sip._tcp IN SRV 10 5 5060 sip` | `dig _sip._tcp.x.lab SRV` |
| **CAA** | qué CA puede emitir certificados | `@ IN CAA 0 issue "letsencrypt.org"` | `dig x.lab CAA` |
| **ANY** | "todo" (muchos servers lo rechazan) | — | mejor pedir tipo por tipo o AXFR |

**SPF** no es un tipo aparte: va en **TXT** (`v=spf1 …`).

---

## 3. El enunciado dice → qué consultar

| El enunciado dice… | Consulta |
|---|---|
| "la IP de X" / "la dirección de X" | `dig @S -p P X A +short` |
| "la IPv6 de X" | `… X AAAA +short` |
| "los servidores que **reciben** el correo de D" / "a qué servidor entregar" | `… D MX` → el de **menor** prioridad → `… <ese> A` |
| "D no tiene registro A, entregue igual" | MX de D (el correo va al MX, no al dominio) |
| "qué IPs pueden **enviar** correo por D" / "política SPF" | `… D TXT` → leer `v=spf1` (sección 6) |
| "un texto publicado / documentado en el DNS" | `… nombre TXT +short \| tr -d '"'` |
| "los servidores de nombres / autoritativos de D" | `… D NS` |
| "quién es la autoridad" / "el responsable de la zona" / "el serial" | `… D SOA` (2º campo = mail del responsable con `.` en lugar de `@`) |
| "a qué apunta el alias X" | `… X CNAME` (o `dig X` y ver la cadena) |
| "qué nombre tiene la IP X" / "resolución inversa" | `dig @S -p P -x X +short` |
| "en qué puerto está el servicio S" | `… _S._tcp.D SRV` |
| "todos los registros de la zona" | `dig @S -p P D AXFR` |
| "el servidor de referencia en IP:puerto" | `@IP -p PUERTO` en **todas** las consultas |
| "verifique contra el servidor autoritativo" | `dig D NS +short` → `dig @<ns> nombre +norec` |
| "verifique que su BIND sirve la zona" | `dig @127.0.0.1 nombre TIPO` y mirar `aa` y `status: NOERROR` |
| "que funcione desde otra máquina" | `dig @IP_de_tu_VM …` desde la otra; revisar `listen-on` y `allow-query` |
| "que los cambios se propaguen" | **subir el serial** del SOA y `rndc reload` |
| "la passphrase es la IP / el texto de X" | `+short` para tener el valor limpio |

**¿A o TXT?** Si el dato es una **dirección**, es A (o AAAA). Si es una **palabra, token o frase**, es TXT. Si no estás seguro, probá los dos.

---

## 4. Leer la salida de `dig`

~~~text
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 4242
;; flags: qr aa rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 1, ADDITIONAL: 2

;; QUESTION SECTION:
;www.empresa.lab.          IN  A

;; ANSWER SECTION:
www.empresa.lab.   3600    IN  A   10.0.0.5
;   nombre          TTL    clase tipo dato

;; AUTHORITY SECTION:
empresa.lab.       3600    IN  NS  ns1.empresa.lab.

;; ADDITIONAL SECTION:
ns1.empresa.lab.   3600    IN  A   10.0.0.2

;; SERVER: 127.0.0.1#5354(127.0.0.1) (UDP)
~~~

### `status`
| status | Significa | Qué hacer |
|---|---|---|
| `NOERROR` + ANSWER con datos | encontró | — |
| `NOERROR` + `ANSWER: 0` | **el nombre existe pero no tiene ese tipo** (NODATA) | probar otro tipo (TXT en vez de A, etc.) |
| `NXDOMAIN` | el nombre **no existe** (en ese servidor) | ¿preguntaste al servidor correcto (`@ -p`)? ¿está bien escrito? ¿falta el dominio? |
| `SERVFAIL` | el servidor no pudo resolver (zona rota, no cargó, DNSSEC, no llega al autoritativo) | `named-checkzone`, logs de BIND |
| `REFUSED` | el servidor no te quiere responder | `allow-query`, `allow-recursion`, o le pediste recursión a un autoritativo |
| `FORMERR` / `NOTIMP` | el server no entiende la consulta | tipo raro, server mínimo |
| `connection timed out; no servers could be reached` | no responde nada en esa IP/puerto | IP/puerto mal, BIND apagado, firewall, `listen-on` |
| `communications error … connection refused` | no hay nada escuchando en ese puerto | servicio caído o puerto equivocado |
| `Transfer failed.` (en AXFR) | no permite transferencia | `allow-transfer` |

### `flags`
| Flag | Significa |
|---|---|
| `qr` | es una respuesta |
| `aa` | **authoritative answer**: el servidor es autoridad de esa zona (tu BIND sirviendo tu zona tiene que mostrarlo) |
| `rd` | pediste recursión |
| `ra` | el servidor ofrece recursión |
| `tc` | respuesta truncada → repetir con `+tcp` |
| `ad` | validada con DNSSEC |
| sin `ra` + `WARNING: recursion requested but not available` | es un autoritativo puro: solo responde sus zonas |

### Secciones
- **ANSWER:** la respuesta.
- **AUTHORITY:** quién es autoridad (NS) o, si no hay respuesta, el **SOA** de la zona (en NXDOMAIN/NODATA).
- **ADDITIONAL:** datos de ayuda ("glue": la IP de los NS).
- **TTL:** segundos que se puede cachear. Si baja en cada consulta, te está respondiendo un **caché**, no el autoritativo.

---

## 5. Recetas de consultas

~~~bash
# IP de un nombre en el servidor de referencia
dig @127.0.0.1 -p 5354 clave.ref.lab +short

# Texto (sin comillas) para usarlo como dato
dig @127.0.0.1 -p 5354 token.ref.lab TXT +short | tr -d '"'
# si el TXT viene partido en varias cadenas: "abc" "def"
dig … TXT +short | sed 's/" "//g; s/"//g'

# A qué servidor entregar correo de un dominio
dig @S -p P empresa.lab MX +short          # → 10 mx1.empresa.lab.  20 mx2.empresa.lab.
dig @S -p P mx1.empresa.lab A +short       # el de menor número primero

# Inversa
dig @S -p P -x 10.0.0.5 +short

# Toda la zona
dig @S -p P empresa.lab AXFR

# Quién es autoridad y el serial
dig @S -p P empresa.lab SOA +short         # ns1.empresa.lab. admin.empresa.lab. 2026110701 3600 900 604800 300

# Delegación desde la raíz (internet real)
dig +trace www.itba.edu.ar

# Preguntarle directo al autoritativo, sin caché
dig itba.edu.ar NS +short
dig @<ns devuelto> www.itba.edu.ar +norec

# Muchas consultas
for n in www mail ns1; do echo -n "$n: "; dig @S -p P $n.empresa.lab +short; done
~~~

### Campos del SOA
~~~text
@ IN SOA ns1.empresa.lab. admin.empresa.lab. (
        2026110701 ; serial    → subirlo en cada cambio (AAAAMMDDnn)
        3600       ; refresh   → cada cuánto el secundario consulta
        900        ; retry     → si falló, cada cuánto reintenta
        604800     ; expire    → cuándo el secundario deja de responder
        300 )      ; minimum   → TTL de respuestas negativas (NXDOMAIN)
~~~
`admin.empresa.lab.` = `admin@empresa.lab` (el primer `.` es la `@`; si el usuario tiene un punto, se escapa: `juan\.perez.empresa.lab.`).

---

## 6. SPF (va en TXT)

~~~text
"v=spf1 ip4:10.0.0.0/24 ip4:200.5.1.7 a mx include:_spf.google.com ~all"
~~~
| Mecanismo | Autoriza a… |
|---|---|
| `ip4:X` / `ip4:X/24` | esa IP / esa red |
| `ip6:X` | IPv6 |
| `a` | las IPs del registro A del dominio |
| `mx` | las IPs de los MX del dominio |
| `include:otro` | lo que autorice el SPF de `otro` (consultarlo también) |
| `redirect=otro` | usar el SPF de `otro` |
| `-all` | todo lo demás: **rechazar** (fail) |
| `~all` | todo lo demás: softfail (marcar) |
| `?all` | neutral |
| `+all` | aceptar todo (mala práctica) |

"¿Qué IPs pueden enviar por D?" → resolver cada mecanismo: `ip4` directo, `a` → `dig D A`, `mx` → `dig D MX` + A de cada uno, `include` → `dig otro TXT` recursivo.

---

## 7. Zona en BIND (lo que se escribe)

### Archivo de zona
~~~text
$TTL 3600
$ORIGIN empresa.lab.
@       IN SOA  ns1.empresa.lab. admin.empresa.lab. ( 2026110701 3600 900 604800 300 )
@       IN NS   ns1
ns1     IN A    10.0.0.2
@       IN A    10.0.0.5
www     IN CNAME @
@       IN MX   10 mail
mail    IN A    10.0.0.6
@       IN TXT  "v=spf1 mx -all"
~~~
| Regla | Por qué |
|---|---|
| nombre **sin punto final** → se le agrega `$ORIGIN` | `mail` = `mail.empresa.lab.` |
| nombre **con punto final** → es absoluto | `mail.otro.com.` |
| ⚠ `mail.empresa.lab` **sin** punto | queda `mail.empresa.lab.empresa.lab.` (error silencioso) |
| `@` = el origen de la zona | `empresa.lab.` |
| línea que empieza con espacio/tab | hereda el nombre de la línea anterior |
| un nombre con **CNAME** no puede tener otros registros | por eso no se pone CNAME en `@` cuando ya hay SOA/NS |
| MX y NS apuntan a **nombres** con A, no a IPs ni CNAME | — |
| TXT entre comillas | sin comillas, cada palabra es una cadena aparte |
| subir el **serial** en cada cambio | si no, los secundarios/cachés no se enteran |

### `named.conf.local`
~~~text
zone "empresa.lab" {
    type master;
    file "/etc/bind/db.empresa.lab";
    allow-transfer { none; };
};
zone "0.0.10.in-addr.arpa" {         // inversa de 10.0.0.0/24 (octetos al revés)
    type master;
    file "/etc/bind/db.10.0.0";
};
~~~
`named.conf.options`: `listen-on { any; };` · `allow-query { any; };` · `recursion no;` (autoritativo) · `forwarders { 8.8.8.8; };` (si resuelve afuera).

### Comandos de BIND
| Comando | Para qué |
|---|---|
| `sudo apt install bind9 bind9-dnsutils` | instalar |
| `named-checkconf` | revisa `named.conf*` (sin salida = OK) |
| `named-checkzone empresa.lab /etc/bind/db.empresa.lab` | revisa la zona (`OK` + serial) |
| `sudo rndc reload` / `sudo rndc reload empresa.lab` | recargar sin reiniciar |
| `sudo systemctl restart named` (o `bind9`) | reiniciar |
| `sudo systemctl status named` / `sudo journalctl -u named -e` | ver errores de carga |
| `sudo rndc flush` | vaciar el caché |
| `ss -ulpn \| grep :53` | ¿está escuchando? |

### Errores de `named-checkzone` (resumen)
| Mensaje | Causa |
|---|---|
| `CNAME and other data` | un nombre con CNAME tiene otro registro |
| `has no address records (A or AAAA)` | un NS/MX apunta a un nombre sin A |
| `not loaded due to errors` | ver la línea anterior |
| `unknown RR type` / `bad dotted quad` | tipo mal escrito / IP mal escrita |
| `no current owner name` | la primera línea empieza con espacio |
| `file not found` | ruta del `file` en `named.conf` |
| `loaded serial N` + `OK` | cargó bien (pero puede tener errores **lógicos**: punto final, `@`) |

Más trampas: [zona-rota-errores-y-trampas.md](zona-rota-errores-y-trampas.md).

---

## 8. DNS dentro de una captura (pcap)

~~~bash
# Todas las consultas y respuestas
tshark -n -r captura.pcap -Y dns -T fields -e dns.qry.name -e dns.qry.type -e dns.a -e dns.resp.name
# Solo respuestas, con TXT, MX, CNAME, NS
tshark -n -r captura.pcap -Y 'dns.flags.response==1' -T fields \
  -e dns.qry.name -e dns.a -e dns.cname -e dns.mx.mail_exchange -e dns.mx.preference -e dns.txt -e dns.ns
# Transferencia de zona (AXFR va por TCP)
tshark -n -r captura.pcap -Y 'dns.qry.type==252'
~~~
Tipos numéricos: A=1, NS=2, CNAME=5, SOA=6, PTR=12, MX=15, TXT=16, AAAA=28, SRV=33, AXFR=252, ANY=255.

---

## 9. Problemas típicos

| Pasa | Causa | Arreglo |
|---|---|---|
| `NXDOMAIN` con un nombre del lab | le preguntaste al resolver del sistema | `@IP -p PUERTO` |
| `NOERROR` pero vacío | ese nombre no tiene ese **tipo** | otro tipo (TXT/A/MX) |
| `dig +short` no muestra nada | NXDOMAIN o NODATA | sacar `+short` y mirar `status` |
| la respuesta TXT trae comillas | dig las muestra | `tr -d '"'` |
| `connection timed out` | puerto/IP mal o servicio apagado | `-p`, `ss -ulpn`, `systemctl status` |
| tu BIND responde sin `aa` | no carga tu zona (responde desde caché/forwarder) | `named-checkzone`, `journalctl` |
| cambié la zona y sigue la respuesta vieja | no subiste el serial / no recargaste / caché | serial++, `rndc reload`, `rndc flush` |
| `REFUSED` desde otra máquina | `allow-query` / `listen-on` | `{ any; }` |
| `www.empresa.lab.empresa.lab.` en AXFR | faltó el punto final | agregar `.` |
| MX responde pero no podés conectar al dominio | el dominio no tiene A: está bien | conectar al **MX** |
| `curl` no resuelve un nombre que `dig @S` sí | curl usa el resolver del sistema | `--resolve nombre:puerto:IP`, `/etc/hosts`, o proxy `socks5h` |

---

## 10. Qué decir en el video
«Consulto siempre al servidor indicado con `@IP -p PUERTO`, elijo el tipo según el dato (A para direcciones, MX para quién recibe correo, TXT para textos y SPF, NS/SOA para autoridad, PTR para inversa) y leo `status`, `flags` (`aa`) y la sección ANSWER. En mi BIND reviso con `named-checkzone`, subo el serial y recargo con `rndc reload`.»
