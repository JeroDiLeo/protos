# Protocolos de Comunicación — 1C 2026, ejercicio 1
## Objetivo
Servir la zona foo.example.org con BIND. Práctica realizada en la máquina del estudiante el 26/10/2026; los comandos fueron ejecutados por él y sus salidas compartidas en el chat.

## Traducción de requisitos
| Requisito | Registro | Dato |
|---|---|---|
| Responsable example.admin@foo.com.ar | SOA, RNAME | example\.admin.foo.com.ar. |
| Raíz con la IP de bar.protos.foo, TTL 1 hora | A | Consultado: 123.123.123.123 |
| www alias de la raíz, TTL 1 semana | CNAME | foo.example.org. |
| MX iguales a mail.protos.foo, conservando orden, TTL 1 semana | MX | Consultado: 10 mx1.protos.foo. |
| Solo 1.2.3.4 autorizada a enviar | TXT con SPF | "v=spf1 ip4:1.2.3.4 -all" |
| Servidor autoritativo | NS | ns.foo.example.org. |

El dominio protos.foo resolvió: no se usaron datos inventados. La IP 127.0.0.1 del NS es una elección para esta práctica local; para atender clientes externos corresponde usar una dirección accesible desde ellos.

## 1. Mostrar el estado inicial de BIND
Consultar antes de modificar:

~~~bash
systemctl status bind9
~~~

- systemctl administra servicios; status consulta su estado; bind9 identifica BIND.
- Inicialmente estaba activo y habilitado. Se lo detuvo:
~~~bash
sudo systemctl stop bind9
~~~
- sudo ejecuta con permisos administrativos; stop detiene ahora sin deshabilitar el arranque automático.
- Se repitió systemctl status bind9 y el estudiante confirmó inactive.
- enabled / preset: enabled no significa que esté corriendo: indica habilitación de arranque / política predeterminada.

## 2. Averiguar los datos externos
~~~bash
dig bar.protos.foo. A
~~~
dig consulta DNS; el nombre con punto final es absoluto; A pide IPv4. Sin @servidor se usa el DNS configurado en el sistema.
Resultado real:
~~~text
bar.protos.foo. 217 IN A 123.123.123.123
~~~
Respondió 127.0.0.53, el resolvedor local del sistema, distinto de BIND en 127.0.0.1. El 217 era el TTL restante recibido; nuestra zona usa su propio TTL: 3600.

~~~bash
dig mail.protos.foo. MX
~~~
MX pide servidores de correo y prioridades.
Resultado real:
~~~text
mail.protos.foo. 300 IN MX 10 mx1.protos.foo.
~~~
Solo respondió un MX; se copió ese único registro. Menor número significa mayor preferencia: conservar prioridades conserva el orden, aunque DNS muestre las respuestas en otro orden.
La sección adicional informó:
~~~text
mx1.protos.foo. 300 IN A 192.168.0.135
~~~
Ese A pertenece a otra zona y no hay que copiarlo.

## 3. Declarar la zona
~~~bash
sudo nano /etc/bind/named.conf.local
~~~
sudo da permisos administrativos; nano abre el editor; el argumento es la ruta del archivo. Conservar las declaraciones existentes y agregar:
~~~conf
zone "foo.example.org" {
    type master;
    file "/etc/bind/db.foo.example.org";
};
~~~
zone identifica la zona; type master indica una zona primaria cargada desde un archivo local; file indica su ubicación.
Guardar en nano con Ctrl+O, Enter; salir con Ctrl+X.

## 4. Crear el archivo de zona
~~~bash
sudo nano /etc/bind/db.foo.example.org
~~~
Mismos componentes del comando anterior, con la ruta del archivo de registros.

Contenido final:
~~~dns
$ORIGIN foo.example.org.
$TTL 1h

@ IN SOA ns.foo.example.org. example\.admin.foo.com.ar. (
    2026102601 ; Serial
    1h         ; Refresh
    15m        ; Retry
    1w         ; Expire
    1h         ; Cache negativa
)

@   IN NS    ns.foo.example.org.
ns  IN A     127.0.0.1

@   1h IN A     123.123.123.123
www 1w IN CNAME foo.example.org.
@   1w IN MX    10 mx1.protos.foo.
@      IN TXT   "v=spf1 ip4:1.2.3.4 -all"
~~~

### Cómo leerlo
- $ORIGIN es la base para nombres relativos: www se expande a www.foo.example.org.
- @ representa el origen de la zona.
- IN es la clase Internet.
- $TTL 1h fija el TTL predeterminado para los registros que no tienen uno explícito.
- Los TTL explícitos se escribieron antes de IN: @ 1h IN A y www 1w IN CNAME. dig muestra segundos: 1h = 3600; 1w = 604800.
- Los nombres absolutos llevan punto final. Sin él, un destino como mx1.protos.foo se expandiría incorrectamente a mx1.protos.foo.foo.example.org.
- El NS en la raíz identifica al servidor autoritativo y es necesario para una zona correctamente formada. El A de ns permite obtener su dirección.
- 127.0.0.1 significa esta misma máquina: se eligió para una demostración local.

### SOA
El primer nombre es el servidor primario. El segundo, RNAME, representa el correo del responsable:
~~~text
example.admin@foo.com.ar → example\.admin.foo.com.ar.
~~~
El punto literal del usuario se escapa; el primer punto sin escapar representa la separación de la @. El punto final cierra el nombre absoluto.

Los números son:
| Campo | Valor | Función |
|---|---|---|
| Serial | 2026102601 | Versión de la zona |
| Refresh | 3600 | Intervalo de comprobación por secundarios |
| Retry | 900 | Reintento de secundarios si falla la actualización |
| Expire | 604800 | Límite sin actualizar tras el que un secundario deja de servir la zona |
| Mínimo para caché negativa | 3600 | Junto con el TTL del SOA limita el TTL de respuestas negativas |

Subir el serial cada vez que se modifique el archivo: por ejemplo, 2026102602. Validar y recargar/reiniciar después para aplicar los cambios.

### SPF
SPF permite publicar qué IP puede enviar correo usando el dominio de la dirección de sobre SMTP (MAIL FROM); también puede aplicarse al dominio HELO. No autentica por sí solo el campo From visible del mensaje.

"v=spf1 ip4:1.2.3.4 -all" significa:
- v=spf1 identifica la política.
- ip4:1.2.3.4 autoriza esa única IPv4.
- -all hace que cualquier otra IP falle SPF. ~all sería un fallo suave.
El receptor decide el tratamiento del mensaje; publicar SPF no configura un servidor de correo ni garantiza rechazo automático.

MX indica dónde RECIBIR correo; SPF indica quién puede ENVIAR usando el dominio evaluado.

## 5. Validar
~~~bash
sudo named-checkzone foo.example.org /etc/bind/db.foo.example.org
~~~
named-checkzone comprueba sintaxis y coherencia; el primer argumento es la zona y el segundo su archivo. Salida real:
~~~text
zone foo.example.org/IN: loaded serial 2026102601
OK
~~~
No se usó -t: en named-checkzone, -t especifica un directorio para chroot; no indica el tipo de registro.

~~~bash
sudo named-checkconf
~~~
Sin archivo explícito, comprueba /etc/bind/named.conf y sus inclusiones. No imprimió errores, según confirmó el estudiante. Este comando sin -z valida configuración, no carga todas las zonas; la nuestra se comprobó con named-checkzone.

## 6. Iniciar y comprobar
~~~bash
sudo systemctl restart bind9
~~~
restart reinicia el servicio; si estaba detenido, lo inicia. Se ejecuta con permisos administrativos.
~~~bash
systemctl status bind9
~~~
El estudiante confirmó active. Esto prueba que el servicio corre; las consultas siguientes comprueban los registros.

## 7. Demostrar todos los registros con dig
En todos estos comandos:
- dig hace la consulta DNS.
- @127.0.0.1 selecciona directamente nuestro BIND. Sin ello, el DNS del sistema podría no conocer esta zona.
- El nombre terminado en punto es absoluto.
- El último argumento selecciona el tipo consultado.
- NOERROR indica consulta procesada sin errores; aa indica respuesta autoritativa.
- SERVER: 127.0.0.1#53 confirma el servidor y puerto consultados.
- La columna numérica antes de IN es el TTL en segundos.

### A — verificado
~~~bash
dig @127.0.0.1 foo.example.org. A
~~~
~~~text
foo.example.org. 3600 IN A 123.123.123.123
~~~
IP igual a la consultada y validez de una hora.

### CNAME — verificado
~~~bash
dig @127.0.0.1 www.foo.example.org. CNAME
~~~
~~~text
www.foo.example.org. 604800 IN CNAME foo.example.org.
~~~
Alias a la raíz con validez de una semana.

### MX — verificado
~~~bash
dig @127.0.0.1 foo.example.org. MX
~~~
~~~text
foo.example.org. 604800 IN MX 10 mx1.protos.foo.
~~~
Mismo host y prioridad que mail.protos.foo, con validez de una semana.

### TXT / SPF — verificado
~~~bash
dig @127.0.0.1 foo.example.org. TXT
~~~
~~~text
foo.example.org. 3600 IN TXT "v=spf1 ip4:1.2.3.4 -all"
~~~
Demuestra la publicación de la política; no es una prueba de un envío de correo.

### SOA — verificado
~~~bash
dig @127.0.0.1 foo.example.org. SOA
~~~
~~~text
foo.example.org. 3600 IN SOA ns.foo.example.org. example\.admin.foo.com.ar. 2026102601 3600 900 604800 3600
~~~
Responsable y serial correctos.

### NS — verificado
~~~bash
dig @127.0.0.1 foo.example.org. NS
~~~
~~~text
foo.example.org. 3600 IN NS ns.foo.example.org.
~~~
La sección adicional también mostró:
~~~text
ns.foo.example.org. 3600 IN A 127.0.0.1
~~~
Todas las consultas compartidas devolvieron NOERROR y aa.

### Opciones de presentación, si se necesitan
No fueron necesarias en las comprobaciones realizadas.
- +short muestra una salida breve con los datos; oculta TTL y cabecera, por lo que no alcanza para demostrar TTL o aa.
- +noall desactiva las secciones de salida; +answer vuelve a mostrar la sección de respuestas. Juntas dejan visibles registros y TTL, pero ocultan la cabecera con aa.
Para justificar la solución en el parcial, la salida completa permite mostrar tanto TTL como autoridad.

## Resumen de archivos finales
| Archivo | Función |
|---|---|
| /etc/bind/named.conf.local | Declara foo.example.org como zona primaria y referencia el archivo de registros |
| /etc/bind/db.foo.example.org | Contiene SOA, NS, A de ns, A de raíz, CNAME, MX y TXT/SPF |

## Justificación breve para responder en el parcial
“BIND responde de forma autoritativa por foo.example.org, con el responsable indicado, la IP y el MX consultados, los TTL pedidos y un SPF que autoriza únicamente a 1.2.3.4.”

## 8. Variantes: qué cambia y qué línea tocar

### Procedimiento fijo (siempre igual, cambie lo que cambie)
1. `systemctl status bind9`: mostrar el estado inicial.
2. Editar `/etc/bind/db.<zona>` (y `named.conf.local` solo si cambia el nombre de la zona).
3. **Subir el serial** (2026102601 → 2026102602).
4. `sudo named-checkzone <zona> /etc/bind/db.<zona>`: tiene que decir OK.
5. `sudo named-checkconf`
6. `sudo systemctl restart bind9`
7. `dig @127.0.0.1 <nombre>. <TIPO>` por cada registro pedido, sin +short (se necesita ver TTL y `aa`).

### Qué cambia → qué tocás

| Si cambia... | Línea(s) a tocar | Cómo se escribe |
|---|---|---|
| Nombre de la zona | `named.conf.local` (zone y file), nombre del archivo, `$ORIGIN`, NS y SOA, destino del CNAME, comando named-checkzone | Usar `@` en el CNAME (`www 1w IN CNAME @`) y no hay que retipear el dominio |
| Responsable | RNAME del SOA | `usuario@dom.com` → `usuario.dom.com.`; si el usuario tiene puntos: `juan.perez@itba.edu.ar` → `juan\.perez.itba.edu.ar.` |
| TTL de un registro | El número antes de `IN` | `30m`, `2h`, `1d`, `1w`. Equivalencias: 1m = 60, 1h = 3600, 1d = 86400, 1w = 604800 |
| IP del A | `@ <ttl> IN A <IP>` | Si es "la de otro host": `dig +short A host.` y copiar |
| Dos IPs para el mismo nombre | Dos líneas A | Cada una con su `IN A` |
| IPv6 | Línea AAAA | `@ IN AAAA 2001:db8::1` |
| Un host distinto (no la raíz) | `bar 1h IN A <IP>` | El nombre relativo se expande con `$ORIGIN` |
| Otro alias | `ftp 1w IN CNAME @` | Nunca en la raíz; y nunca el mismo nombre con otro registro |
| MX copiados de otro dominio | Una línea MX por cada uno | `dig +short MX dom. \| sort -n`; copiar **prioridad y host**, host con punto final |
| MX propio | `@ IN MX 10 mail.<zona>.` + `mail IN A <IP>` | Si el host es de la zona, necesita su A; el MX no puede apuntar a un CNAME |
| SPF | Línea TXT | Ver tabla de abajo |
| "Que se propague rápido" | SOA | Subir serial; bajar refresh, retry y TTL |

### Orden de los MX
- En el archivo, el orden de las líneas MX **no importa**. Manda el número.
- **Número menor = más preferido**: el `10` se prueba antes que el `20`.
- Conviene escribirlos de menor a mayor número, por prolijidad.
- "Manteniendo el orden" en la consigna significa **copiar los mismos números de prioridad**, sin renumerar. No se refiere al orden de las líneas.
- `dig` puede mostrar las respuestas rotadas; por eso `dig +short MX dom. | sort -n` los deja ordenados para copiar.

~~~dns
@ 1w IN MX 10 mx1.protos.foo.    ; se prueba primero
@ 1w IN MX 20 mx2.protos.foo.    ; solo si el anterior falla
~~~

### SPF según lo que pidan

| Consigna | TXT |
|---|---|
| Solo la IP X | `"v=spf1 ip4:X -all"` |
| Un rango | `"v=spf1 ip4:1.2.3.0/24 -all"` |
| Solo los servidores de los MX | `"v=spf1 mx -all"` |
| El A de la zona y los MX | `"v=spf1 a mx -all"` |
| Varias IPs | `"v=spf1 ip4:X ip4:Y -all"` |
| Poco estricto (fallo suave) | termina en `~all` |

"Solo" o "únicamente" → `-all`. Siempre entre comillas y es un registro **TXT**.

### Mini-variantes para practicar (con la solución)

**V1.** Zona `demiloo.com.ar`, responsable `juan.perez@itba.edu.ar`, A con la IP de `bar.protos.foo` por 30 minutos, `www` alias de la raíz por 2 días, MX iguales a `mail.protos.foo`, SPF: solo los servidores de los MX.
~~~dns
$ORIGIN demiloo.com.ar.
$TTL 1h
@ IN SOA ns.demiloo.com.ar. juan\.perez.itba.edu.ar. ( 2026102701 1h 15m 1w 1h )
@   IN NS    ns.demiloo.com.ar.
ns  IN A     127.0.0.1
@   30m IN A     <IP de bar.protos.foo>
www 2d  IN CNAME @
@   1w  IN MX    <prio> <host>.      ; uno por cada MX de mail.protos.foo
@       IN TXT   "v=spf1 mx -all"
~~~
Demostrar: TTL 1800 en el A y 172800 en el CNAME.

**V2.** Dos IPs para la raíz, un `ftp` como alias y el MX es un host propio `correo` con IP 10.0.0.5.
~~~dns
@      1h IN A     <IP1>
@      1h IN A     <IP2>
ftp    1w IN CNAME @
correo IN A        10.0.0.5
@      1w IN MX    10 correo.<zona>.
~~~

### Preguntas que pueden hacerte en el video
- ¿Por qué el CNAME no puede estar en la raíz? Porque la raíz ya tiene SOA y NS, y un CNAME no puede convivir con otros registros del mismo nombre.
- ¿Por qué el host del MX lleva punto final? Sin él, BIND le agrega el `$ORIGIN` y apunta a un nombre inexistente.
- ¿Qué pasa si no subo el serial? Los secundarios no detectan el cambio y siguen con la versión vieja.
- ¿Qué diferencia hay entre MX y SPF? MX dice dónde se **recibe** el correo; SPF dice quién puede **enviarlo** usando el dominio.

## Guardar este documento en la máquina del estudiante
Descargar este archivo y ubicarlo en ~/protos/soluciones/26.1-1.md.
Si se descargó como ~/Descargas/26.1-1.md, primero crear el directorio:
~~~bash
mkdir -p ~/protos/soluciones
~~~
mkdir crea directorios; -p crea padres faltantes y acepta un directorio ya existente; ~ representa tu directorio personal.
Luego copiar:
~~~bash
cp ~/Descargas/26.1-1.md ~/protos/soluciones/26.1-1.md
~~~
cp copia desde el primer argumento al segundo. Ajustar Descargas si el navegador usa otra carpeta. El asistente no tiene acceso directo a la computadora del estudiante.


