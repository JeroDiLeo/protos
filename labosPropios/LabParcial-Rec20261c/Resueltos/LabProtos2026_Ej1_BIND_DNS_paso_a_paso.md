# LabProtos2026 · Ejercicio 1 · Zona DNS autoritativa con BIND

## Qué pide el ejercicio

Configurar BIND como autoridad para la zona `foo.example.org` y demostrarlo con `dig`.

| Punto | Requisito |
|---|---|
| 1 | El BIND de la workstation debe servir la zona como autoridad. |
| 2 | El contacto del responsable es `example.admin@foo.com.ar`. |
| 3 | La raíz de la zona debe tener un A con la IP de `bar.protos.foo` y TTL de una hora. |
| 4 | `www` debe ser un CNAME a la raíz de la zona, con TTL de una semana. |
| 5 | Los MX deben ser los mismos que los de `mail.protos.foo`, con las mismas prioridades y TTL de una semana. |
| 6 | La única IP autorizada por SPF para enviar correo por el dominio es `1.2.3.4`. |

Los comandos de esta práctica se ejecutaron dentro de la workstation del laboratorio, con el prompt `root@workstation:/#`. BIND ya venía instalado en la imagen y había que configurarlo y arrancarlo.

## 1. Consultar el DNS que ya usa la workstation

La consigna da nombres, como `bar.protos.foo`, y deja que averigüemos sus registros. Primero consultamos sin `@IP` para aprovechar el DNS configurado en la máquina. El tipo `A` pide la dirección IPv4.

```bash
dig A bar.protos.foo
```

Salida de la workstation, con las líneas relevantes:

```text
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 43321
;; flags: qr aa; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 0

;; ANSWER SECTION:
bar.protos.foo.          3600    IN  A   123.123.123.123

;; SERVER: 127.0.0.11#53(127.0.0.11) (UDP)
```

De la respuesta copiamos `123.123.123.123`. El TTL del A de nuestra zona sale de **nuestra consigna**. En este caso coincide con el observado, `3600` segundos.

El segundo dato que necesitamos es el conjunto de servidores de correo. El tipo `MX` devuelve sus nombres y prioridades.

```bash
dig MX mail.protos.foo
```

```text
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 48947
;; flags: qr aa; QUERY: 1, ANSWER: 2, AUTHORITY: 0, ADDITIONAL: 0

;; ANSWER SECTION:
mail.protos.foo.         3600    IN  MX  5 mx2.protos.foo.
mail.protos.foo.         3600    IN  MX  10 mx1.protos.foo.

;; SERVER: 127.0.0.11#53(127.0.0.11) (UDP)
```

Copiamos cada pareja de prioridad y nombre. **El número menor tiene preferencia**, así que se prefiere `mx2.protos.foo.` con prioridad `5`, seguido de `mx1.protos.foo.` con `10`. Aunque `dig` pueda mostrar los registros en otro orden, la preferencia sale del número. El TTL que publicó el DNS de referencia fue `3600`, pero el ejercicio nos pide publicar nuestros MX con `604800` segundos.

También verificamos que los dos nombres de los MX resuelven a una IPv4:

```bash
dig A mx2.protos.foo
dig A mx1.protos.foo
```

Registros observados en las dos respuestas:

```text
mx2.protos.foo.          3600    IN  A   172.28.0.25
mx1.protos.foo.          3600    IN  A   172.28.0.25
```

La coincidencia de IP confirma que los dos nombres apuntan al mismo servidor en el lab. Conservamos los nombres en los MX.

### De dónde sale la IP del DNS

En el parcial, el primer intento razonable es `dig nombre tipo` sin `@`. Si la respuesta ya trae los registros en `ANSWER SECTION`, se pueden usar. Si faltan, revisá las instrucciones generales y qué DNS tiene configurado el entorno.

| Dirección | Papel en el laboratorio |
|---|---|
| `127.0.0.11` | DNS interno de Docker al que `dig` le consulta por defecto desde la workstation. Por eso aparece en `SERVER`. |
| `172.28.0.53` | DNS de referencia del lab. El servicio `dns` y la opción `dns` de la workstation aparecen en `docker-compose.yml`. También figura en el mapa del `README.md`. |
| `127.0.0.1` | Dirección local a la que enviamos la consulta directa al BIND que levantamos en la workstation. |
| `172.28.0.5` | IP de la workstation en la red del laboratorio. La publicamos como el A de `ns.foo.example.org.`. |

Si hiciera falta consultar directamente al DNS de referencia en este lab, la forma sería `dig @172.28.0.53 bar.protos.foo A`. La opción `@IP` indica **a quién le pregunto**. `bar.protos.foo` indica **por qué nombre pregunto**.

## 2. Declarar la zona en BIND

```bash
nano /etc/bind/named.conf.local
```

Agregamos:

```conf
zone "foo.example.org" {
    type master;
    file "/etc/bind/db.foo.example.org";
};
```

`type master` configura este BIND como primario para la zona. La directiva `file` le dice de qué archivo cargar los registros. Si el archivo se crea en otra carpeta, hay que reflejar esa ruta en `file`.

## 3. Escribir el archivo de zona

```bash
nano /etc/bind/db.foo.example.org
```

```dns
$ORIGIN foo.example.org.
$TTL 1w

@   IN  SOA  ns.foo.example.org. example\.admin.foo.com.ar. (
             2026110901
             1h
             15m
             1w
             1h
)

@       IN  NS     ns.foo.example.org.
ns      IN  A      172.28.0.5

@   1h  IN  A      123.123.123.123
www     IN  CNAME  foo.example.org.
@       IN  MX     5 mx2.protos.foo.
@       IN  MX     10 mx1.protos.foo.
@       IN  TXT    "v=spf1 ip4:1.2.3.4 -all"
```

- `$ORIGIN foo.example.org.` fija la base para los nombres relativos. `@` representa esa base y `www` se expande a `www.foo.example.org.`.
- El punto final indica que un nombre está completo. En `mx2.protos.foo.` evita que BIND le agregue `foo.example.org.`.
- `$TTL 1w` da un TTL predeterminado de `604800` segundos. El A de la raíz tiene `1h` explícito, equivalente a `3600` segundos. El TTL indica cuánto puede cachearse el registro.
- `IN` es la clase Internet.
- En el `CNAME`, el dueño es `www.foo.example.org.` y el destino es el nombre de la raíz. El A de la raíz aporta la dirección IPv4.

### SOA, NS y A del servidor de nombres

| Fragmento | Qué declara |
|---|---|
| `@ IN SOA ns.foo.example.org. ...` | `ns.foo.example.org.` es el nombre del servidor primario de la zona. |
| `@ IN NS ns.foo.example.org.` | `ns.foo.example.org.` es uno de los servidores autoritativos para la zona. |
| `ns IN A 172.28.0.5` | El servidor identificado por ese nombre está en la IP de la workstation. |
| `@ 1h IN A 123.123.123.123` | El propio dominio `foo.example.org.` apunta a la dirección de `bar.protos.foo` que encontramos antes. |

`ns` fue el nombre que elegimos para nuestro BIND. También habría servido `ns1` si lo usábamos de forma consistente. Como hay un solo autoritativo y es el primario, el mismo nombre aparece en el SOA y en el NS.

Si la consigna diera **otro nombre para nuestro BIND**, usaríamos ese nombre en SOA y NS, con la IP que le corresponda. Si pidiera **primario y secundario**, ambos podrían figurar en los NS y el SOA seguiría identificando al primario. Si designara **otro servidor real como único autoritativo**, ese otro servidor tendría que cargar la zona. Escribir su nombre en el archivo de nuestra workstation por sí solo no configura el otro servidor.

Los campos del SOA se leen en este orden:

| Campo | Valor | Significado |
|---|---|---|
| Servidor primario | `ns.foo.example.org.` | Nombre del BIND primario. |
| Contacto | `example\.admin.foo.com.ar.` | Representa `example.admin@foo.com.ar`. El primer punto sin escape separa la parte local del dominio. La barra conserva el punto interno de `example.admin`. |
| Serial | `2026110901` | Versión de la zona. Elegimos el formato fecha más revisión y lo incrementamos al publicar cambios. |
| Refresh | `1h` | Cada cuánto un secundario comprueba si hubo cambios. |
| Retry | `15m` | Cuánto espera un secundario para reintentar si falla la comprobación. |
| Expire | `1w` | Límite tras el cual un secundario deja de servir la zona si no consigue refrescarla. |
| Negative cache TTL | `1h` | Valor que interviene en cuánto se cachean respuestas negativas. El TTL negativo se limita al menor entre este valor y el TTL del SOA. |

### TXT de SPF y diferencia con MX

```dns
@ IN TXT "v=spf1 ip4:1.2.3.4 -all"
```

Cuando un servidor recibe un correo cuyo `MAIL FROM` usa `foo.example.org`, puede consultar esta política y compararla con la IP del servidor que le está entregando el mensaje.

| Parte | Significado |
|---|---|
| `v=spf1` | Identifica el TXT como una política SPF versión 1. |
| `ip4:1.2.3.4` | Esa dirección IPv4 obtiene un resultado SPF Pass. |
| `-all` | Cualquier otra IP obtiene un resultado SPF Fail. |

El **MX** dice a qué servidores entregar correo **para** `foo.example.org`. El **SPF** dice qué IP está autorizada para enviar correo **por** ese dominio.

## 4. Validar la zona y arrancar BIND

```bash
named-checkconf -z
```

`-z` prueba la carga de las zonas primarias declaradas. En particular, verifica que BIND puede abrir y leer el archivo en la ruta que pusimos en `file`.

Salida obtenida:

```text
zone foo.example.org/IN: loaded serial 2026110901
zone localhost/IN: loaded serial 2
zone 127.in-addr.arpa/IN: loaded serial 1
zone 0.in-addr.arpa/IN: loaded serial 1
zone 255.in-addr.arpa/IN: loaded serial 1
```

La primera línea corresponde a la zona del ejercicio. Las demás son zonas que ya estaban en la configuración. Como la zona cargó, arrancamos el servidor de la workstation:

```bash
named -c /etc/bind/named.conf
```

`named` inicia BIND y `-c` selecciona el archivo de configuración. En el contenedor usamos este arranque directo. La validación previa comprueba los archivos y la siguiente consulta comprueba el servicio en ejecución.

## 5. Demostrar la autoridad consultando al BIND local

```bash
dig @127.0.0.1 foo.example.org SOA +norecurse
```

- `@127.0.0.1` selecciona el servidor local de la workstation.
- `SOA` pide los datos administrativos de la zona.
- `+norecurse` envía la consulta sin pedir recursión. Así le pedimos a ese servidor una respuesta directa sobre la zona.

Extracto de la respuesta real:

```text
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 43460
;; flags: qr aa ra; QUERY: 1, ANSWER: 1, AUTHORITY: 1, ADDITIONAL: 2

;; ANSWER SECTION:
foo.example.org.         604800  IN  SOA  ns.foo.example.org. example\.admin.foo.com.ar. 2026110901 3600 900 604800 3600

;; AUTHORITY SECTION:
foo.example.org.         604800  IN  NS   ns.foo.example.org.

;; ADDITIONAL SECTION:
ns.foo.example.org.      604800  IN  A    172.28.0.5

;; SERVER: 127.0.0.1#53(127.0.0.1) (UDP)
```

La combinación de `NOERROR`, `aa` (respuesta autoritativa), el SOA esperado y el `SERVER` local demuestra que nuestro BIND sirve la zona. `ra` indica que el servidor ofrece recursión. En esta consulta el flag `rd`, que marca la solicitud de recursión, está ausente por `+norecurse`.

## 6. Verificar los demás registros y TTL

```bash
dig @127.0.0.1 foo.example.org A +norecurse +noall +answer
dig @127.0.0.1 www.foo.example.org CNAME +norecurse +noall +answer
dig @127.0.0.1 foo.example.org MX +norecurse +noall +answer
dig @127.0.0.1 foo.example.org TXT +norecurse +noall +answer
```

`+noall` desactiva las secciones de salida y `+answer` vuelve a mostrar la sección de respuestas. Sirve para comparar nombre, TTL, clase, tipo y valor. Dejamos la salida completa en la prueba de autoridad para ver también el encabezado y el servidor consultado.

Salida obtenida:

```text
foo.example.org.         3600    IN  A      123.123.123.123
www.foo.example.org.     604800  IN  CNAME  foo.example.org.
foo.example.org.         604800  IN  MX     5 mx2.protos.foo.
foo.example.org.         604800  IN  MX     10 mx1.protos.foo.
foo.example.org.         604800  IN  TXT    "v=spf1 ip4:1.2.3.4 -all"
```

La segunda columna muestra una hora para el A y una semana para el CNAME y los MX. Los MX conservan los nombres y prioridades del dominio de referencia. El TXT publica la política SPF pedida.

## 7. Qué pasó al probar el SOA sin @127.0.0.1

```bash
dig foo.example.org SOA +norecurse
```

Extracto de la salida real:

```text
;; ->>HEADER<<- opcode: QUERY, status: NXDOMAIN, id: 62763
;; flags: qr aa; QUERY: 1, ANSWER: 0, AUTHORITY: 0, ADDITIONAL: 0

;; QUESTION SECTION:
;foo.example.org.        IN      SOA

;; SERVER: 127.0.0.11#53(127.0.0.11) (UDP)
```

La línea que permite explicar el resultado es `SERVER`. Al sacar `@127.0.0.1`, la consulta vuelve al DNS predeterminado de Docker, `127.0.0.11`. Ese camino sigue usando el DNS de referencia del lab y allí no se publicó la zona nueva. `+norecurse` cambia el pedido de recursión y la selección del servidor sigue dependiendo de `@`.

El flag `aa` también puede aparecer en una respuesta negativa. En esta salida aparece junto con `NXDOMAIN` y cero respuestas. La demostración pedida por el ejercicio es la consulta **directa al BIND local** de los pasos 5 y 6, que devolvió los registros de la zona.
