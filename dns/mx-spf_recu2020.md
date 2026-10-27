# Protocolos — DNS de correo: MX y SPF (recu 2020 y similares)

## Enunciado (textual)

*Fuente: Recuperatorio 2020, Ejercicio I.*

Responda las siguientes preguntas sobre el dominio `proto.leak.com.ar`:

A. ¿Cuáles son las direcciones IPs de los servidores SMTP que reciben el correo entrante? (1 punto)

B. Según la política SPF, ¿cuáles son las direcciones IP que tienen permitido enviar correos electrónicos salientes? (1 punto)

**Consejo.** Escriba como comentario de la entrega de campus las soluciones para una primera corrección rápida.

---

## Consigna típica
- "Enumere todas las direcciones IP de los servidores SMTP que reciben el correo entrante de `proto.leak.com.ar`" (o: "¿a qué servidores SMTP me conecto para entregar un correo a ese dominio?").
- "Según la política SPF del dominio, ¿qué direcciones IP pueden enviar correo en su nombre?"

> No se configura nada: son consultas con `dig` y leer la salida. Lo que se evalúa es **qué registro consultar y cómo interpretarlo**.

---

## ⭐ RECETA PARA EL PARCIAL

### A) Servidores que RECIBEN el correo → registro MX
~~~bash
dig +short MX proto.leak.com.ar | sort -n
~~~
Salida (datos de 2020, verificados contra un BIND local con la misma zona):
~~~text
20 smtp20.proto.leak.com.ar.
21 smtp30.proto.leak.com.ar.
~~~
- `MX` = Mail eXchanger: qué hosts reciben el correo de ese dominio. Es a quien se conecta un servidor que quiere **entregar** un mail ahí.
- El número es la **preferencia**: el **menor** se intenta primero (20 antes que 21). Si falla, se pasa al siguiente.
- `sort -n` ordena por ese número: `dig` puede devolverlos en cualquier orden.

La consigna pide **IPs**, y el MX da **nombres**. Hay que resolver cada uno:
~~~bash
dig +short A smtp20.proto.leak.com.ar
dig +short A smtp30.proto.leak.com.ar
~~~
~~~text
127.0.0.1
192.168.122.235
~~~
Atajo que hace todo junto:
~~~bash
for h in $(dig +short MX proto.leak.com.ar | sort -n | awk '{print $2}'); do echo "$h -> $(dig +short A $h)"; done
~~~
- `awk '{print $2}'` se queda con la segunda columna (el host); el `for` pide el A de cada uno.

**Respuesta:** los servidores que reciben el correo son `smtp20` (127.0.0.1, preferencia 20) y `smtp30` (192.168.122.235, preferencia 21).

Para mostrarlo con TTL y todo junto:
~~~bash
dig proto.leak.com.ar MX +noall +answer +additional
~~~
La sección `additional` suele traer ya las IPs de los hosts del MX.

### B) Quién puede ENVIAR → registro TXT con SPF
~~~bash
dig +short TXT proto.leak.com.ar
~~~
~~~text
"v=spf1 ip4:192.168.122.235 -all"
~~~
Si el dominio tiene varios TXT, quedarse con el que empieza con `v=spf1`:
~~~bash
dig +short TXT proto.leak.com.ar | grep spf1
~~~

**Cómo se lee el SPF** (de izquierda a derecha, gana el primero que coincide):
| Parte | Significa |
|---|---|
| `v=spf1` | esto es una política SPF versión 1 |
| `ip4:192.168.122.235` | esa IPv4 está autorizada (también `ip4:1.2.3.0/24` para un rango) |
| `ip6:...` | lo mismo para IPv6 |
| `a` | autorizadas las IPs del registro A del dominio |
| `mx` | autorizadas las IPs de los servidores MX del dominio |
| `include:otro.dom` | también vale la política SPF de `otro.dom` → **hay que consultarla** con otro `dig TXT` |
| `-all` | **todo lo demás falla** (rechazar) |
| `~all` | todo lo demás es "softfail": sospechoso, pero no se rechaza |
| `?all` | neutral: no se afirma nada |

**Respuesta:** según la política SPF, solo `192.168.122.235` puede enviar correo como `proto.leak.com.ar` (`-all` hace fallar a cualquier otra IP).

### Si hay `include:`
~~~bash
dig +short TXT gmail.com | grep spf1          # ej: "v=spf1 redirect=_spf.google.com"
dig +short TXT _spf.google.com | grep spf1    # seguir la cadena hasta llegar a ip4/ip6
~~~
`redirect=` funciona parecido a `include:`: hay que seguirlo.

### Diferencia clave (pregunta típica del video)
- **MX** dice dónde se **recibe** el correo del dominio.
- **SPF** dice desde qué IPs se puede **enviar** correo en nombre del dominio.
- Pueden no coincidir: en este caso `smtp20` (127.0.0.1) recibe, pero no está autorizado a enviar.

### Para el video
"Los servidores que reciben el correo están en los registros MX: los consulto con `dig MX`, los ordeno por preferencia y resuelvo cada host con `dig A` para obtener sus IPs. Quién puede enviar lo dice el registro TXT que empieza con `v=spf1`: acá solo autoriza `ip4:192.168.122.235` y `-all` hace fallar al resto."

### Si algo falla
| Ves | Significa | Qué hacer |
|---|---|---|
| `dig` no devuelve nada | tu red no resuelve ese dominio | probar `dig @8.8.8.8 ...`, o hacerlo desde pampero (`ssh pampero.itba.edu.ar` y repetir) |
| el MX da nombres pero `dig A` del host no devuelve nada | ese host no resuelve desde tu red | repetirlo desde pampero (en 2020 así se resolvió) |
| varios TXT | otros servicios usan TXT | `grep spf1` |
| el MX apunta a un CNAME | mala configuración del dominio (un MX no debe apuntar a un alias) | informarlo y resolver el CNAME igual |

### Variantes
| Pregunta | Comando |
|---|---|
| ¿A qué servidor SMTP me conecto para mandarle a `x@dominio`? | `dig +short MX dominio \| sort -n` → el de menor número; si no hay MX, el A del propio dominio |
| ¿Qué DNS son autoritativos? | `dig +short NS dominio` |
| Preguntar a un DNS específico | `dig @8.8.8.8 MX dominio` |
| IPv6 de los servidores | `dig +short AAAA host` |
| Ver todo junto | `dig dominio MX +noall +answer +additional` |
