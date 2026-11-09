# Simulacro 2026-2C · Ejercicio 4 · Reconstruir una zona DNS desde una captura

Práctica del 9 de noviembre de 2026. BIND cargó la zona `protos.lab` con serial `2018010102`. Las consultas verificaron el SOA, el NS, los tres A, el MX, el CNAME y los dos TXT del dominio.

## 1. Qué pedía la consigna

Recuperar los registros originales de una zona DNS a partir de una captura de red. Configurar esa zona en BIND, agregar el TXT `cachito hola` al dominio raíz y demostrar que el servidor responde.

| Recurso o servicio | Dirección o ruta |
|---|---|
| Captura de red | `http://172.30.0.40:8000/backup.pcapng` |
| Servidor BIND | Servicio Docker Compose `ej4-bind` |
| Dirección DNS usada para verificar | `172.30.0.41:53` |
| Puerto publicado en el host tras la corrección del lab | `127.0.0.1:15353` |
| Configuración en el proyecto | `ej4/bind/etc-bind/`, montado en `/etc/bind` del contenedor |

## 2. Descargar y abrir la captura

Desde la carpeta del simulacro:

```bash
curl -f http://172.30.0.40:8000/backup.pcapng -o backup.pcapng
wireshark backup.pcapng
```

`curl` solicita el archivo por HTTP. `-f` hace que el comando devuelva error ante una respuesta HTTP como `404`. `-o backup.pcapng` guarda el cuerpo con ese nombre. Wireshark también permite abrir la captura desde **Archivo → Abrir** o con **Ctrl+O**.

En Wireshark se aplicó el filtro:

```text
dns.flags.response == 1
```

El filtro muestra los paquetes DNS con el bit de respuesta activado. La columna **Info** sirve para ubicar el paquete. En **Domain Name System → Answers** se pueden ver el dueño, tipo, TTL y datos de cada registro.

### Cómo elegir los paquetes que aportan registros

1. **Quedate con las respuestas del servidor de la captura.** En este ejercicio, la IP de origen de esas respuestas es `172.30.0.41`. El filtro puede combinar las dos condiciones:

   ```text
   dns.flags.response == 1 && ip.src == 172.30.0.41
   ```

2. **Buscá el SOA para identificar la zona.** En el paquete 2, abrí **Domain Name System → Answers → protos.lab: type SOA**. El campo `Name` dice a qué nombre pertenece el registro. En este caso, `protos.lab` es la raíz de la zona. `Primary name server` es uno de los datos del SOA y contiene `ns1.protos.lab`.
3. **Revisá también los nombres que están bajo la zona.** Un filtro que muestre solo consultas con nombre exacto `protos.lab` dejaría afuera las consultas de `ns1.protos.lab`, `www.protos.lab`, `mail.protos.lab` y `ftp.protos.lab`.
4. **Abrí Answers antes de anotar un registro.** La columna **Info** permite encontrar candidatos. Ahí también se ve el nombre y tipo que se preguntaron, incluso si el servidor no devolvió registros. **Queries** describe la pregunta. **Answers** contiene los datos que devolvió el servidor para esa consulta.
5. **Revisá todos los registros de la respuesta y eliminá las repeticiones exactas.** El paquete 14 trae un CNAME de `ftp` y un A de `www`. Ese A coincide con los de los paquetes 8 y 18, así que se escribe una sola vez. El paquete 20 muestra que se preguntó por el MX de `mail.protos.lab`, pero tiene **Answers vacío**. La pregunta por sí sola no aporta una línea para la zona.

### Cómo pasar de Answers al archivo de BIND

Para cada registro de **Answers**, anotá el **nombre al que pertenece**, el **TTL**, la **clase**, el **tipo** y sus **datos**. Ese es el orden que se usa en el archivo de zona.

En el paquete 8, por ejemplo:

| Campo en Wireshark | Valor |
|---|---|
| Name | `www.protos.lab` |
| Time to live | `3600` segundos |
| Class | `IN` |
| Type | `A` |
| Address | `172.30.0.50` |

La línea se puede escribir completa o aprovechar el origen y el TTL por defecto de la zona:

```dns
www.protos.lab. 3600 IN A 172.30.0.50
```

```dns
www IN A 172.30.0.50
```

En la segunda forma, BIND completa `www` con el origen `protos.lab.` y toma el TTL de `$TTL 3600`. Si en la captura un registro tiene un TTL distinto, indicá ese valor en su línea.

| Paquete | Cómo interpretar los datos de Answers | Línea correspondiente |
|---:|---|---|
| 4 | El dueño del NS es `protos.lab`. Su destino es `ns1.protos.lab`. | `@ IN NS ns1.protos.lab.` |
| 12 | El dueño del MX es `protos.lab`. El destino es `mail.protos.lab` con preferencia `10`. | `@ IN MX 10 mail.protos.lab.` |
| 14 | El dueño del CNAME es `ftp.protos.lab`. Su destino es `www.protos.lab`. | `ftp IN CNAME www.protos.lab.` |
| 16 | El dueño del TXT es `protos.lab`. El campo TXT contiene `v=protos1`. | `@ IN TXT "v=protos1"` |

Usá `@` cuando el dueño sea la raíz de la zona. El punto final hace que un nombre como `mail.protos.lab.` se use completo en el destino de un registro. Si lo omitís en un nombre absoluto, BIND puede completarlo con el origen de la zona.

Para **agregar** un registro, buscá en la consigna su dueño, tipo y valor. Acá pide un TXT para la raíz, con el texto exacto `cachito hola`. El paquete 16 aporta el TXT anterior. En la zona quedan ambas líneas:

```dns
@ IN TXT "v=protos1"
@ IN TXT "cachito hola"
```

El cambio se registra incrementando el serial del SOA de `2018010101` a `2018010102`. Después se comprueba con `dig @172.30.0.41 protos.lab TXT +norecurse` que BIND devuelve ambos valores.

## 3. Recuperar los registros originales

El paquete **2** muestra el SOA de `protos.lab`. Al expandirlo se encontraron estos campos:

| Campo | Valor en la captura | Significado |
|---|---|---|
| Dueño del registro | `protos.lab.` | Raíz de la zona. |
| TTL del registro | `3600` | Tiempo que puede permanecer en caché este registro. |
| Servidor principal | `ns1.protos.lab.` | Nombre del servidor principal indicado en el SOA. |
| Responsable | `admin.protos.lab.` | Representa la dirección `admin@protos.lab`. |
| Serial | `2018010101` | Versión de la zona en la captura. |
| Refresh | `3600` | Intervalo de comprobación de cambios por un servidor secundario. |
| Retry | `1800` | Tiempo antes de que el secundario reintente una comprobación fallida. |
| Expire | `604800` | Tiempo máximo que el secundario conserva la zona si no puede actualizarla. |
| Minimum | `86400` | Campo del SOA que interviene en el TTL de respuestas negativas. |

El paquete **16** muestra el TXT original, `v=protos1`, con TTL `3600`. Como la consigna pide agregar un TXT, se conserva ese registro y se añade `cachito hola`.

El resto de los registros se obtuvo al revisar la sección **Answers** del archivo de captura. Todos los registros recuperados tenían TTL `3600`.

| Paquete | Dueño | Tipo | Datos |
|---:|---|---|---|
| 2 | `protos.lab.` | SOA | Servidor principal, responsable, serial e intervalos de la tabla anterior. |
| 4 | `protos.lab.` | NS | `ns1.protos.lab.` |
| 6 | `ns1.protos.lab.` | A | `172.30.0.41` |
| 8 | `www.protos.lab.` | A | `172.30.0.50` |
| 10 | `mail.protos.lab.` | A | `172.30.0.51` |
| 12 | `protos.lab.` | MX | Prioridad `10`, destino `mail.protos.lab.` |
| 14 | `ftp.protos.lab.` | CNAME | `www.protos.lab.` |
| 16 | `protos.lab.` | TXT | `v=protos1` |

El paquete 14 también trae el A de `www`, y el 18 repite ese mismo A. En el archivo de zona alcanza con escribirlo una sola vez. El paquete 20 contiene una consulta por el MX de `mail.protos.lab.`, pero su sección **Answers** está vacía. El MX recuperado pertenece a `protos.lab.` y su destino es `mail.protos.lab.`.

## 4. Escribir la zona en BIND

Desde la carpeta del simulacro:

```bash
nano ej4/bind/etc-bind/zones/db.protos.lab
```

Contenido de la zona que se cargó:

```dns
$TTL 3600

@   IN  SOA    ns1.protos.lab. admin.protos.lab. (
               2018010102  ; serial
               3600        ; refresh
               1800        ; retry
               604800      ; expire
               86400       ; minimum
)

@     IN  NS     ns1.protos.lab.
ns1   IN  A      172.30.0.41
www   IN  A      172.30.0.50
mail  IN  A      172.30.0.51
@     IN  MX     10 mail.protos.lab.
ftp   IN  CNAME  www.protos.lab.
@     IN  TXT    "v=protos1"
@     IN  TXT    "cachito hola"
```

- `$TTL 3600` fija el TTL por defecto. El `86400` del SOA tiene un propósito diferente y se mantiene como en la captura.
- `@` representa el origen de la zona, `protos.lab.`. Los nombres relativos, como `www` a la izquierda, se completan con ese origen.
- Los nombres que terminan en punto son absolutos. Por ejemplo, `mail.protos.lab.` como destino del MX se usa tal cual.
- `IN` es la clase Internet. El `10` del MX es la preferencia de ese servidor de correo.
- Las comillas agrupan el texto de cada TXT. El segundo TXT tiene un espacio entre sus palabras.
- Se incrementó el serial de `2018010101` a `2018010102` para reflejar el TXT agregado.

## 5. Declarar y validar la zona

```bash
nano ej4/bind/etc-bind/named.conf.local
```

Se habilitó el bloque que declara a BIND como servidor principal de la zona:

```conf
zone "protos.lab" {
    type master;
    file "/etc/bind/zones/db.protos.lab";
};
```

`file` usa la ruta que ve el proceso de BIND **dentro del contenedor**. En la máquina, ese mismo archivo está bajo `ej4/bind/etc-bind/zones/`.

Antes de reiniciar se comprobó que la configuración se pudiera cargar:

```bash
docker compose exec ej4-bind named-checkconf -z
```

`docker compose exec ej4-bind` ejecuta el comando dentro del contenedor. `named-checkconf` comprueba la configuración de BIND y `-z` intenta cargar las zonas primarias que declara.

Salida real:

```text
zone protos.lab/IN: loaded serial 2018010102
```

Eso confirmó que el archivo se podía leer y cargar. Para aplicar el cambio al servicio en ejecución:

```bash
docker compose restart ej4-bind
```

## 6. Verificar el TXT y la autoridad de la respuesta

```bash
dig @172.30.0.41 protos.lab TXT +norecurse
```

`@172.30.0.41` elige el servidor DNS al que se consulta. `protos.lab` es el nombre consultado y `TXT` el tipo. `+norecurse` envía la consulta sin pedir recursión. En esta conexión directa al contenedor se usa el puerto DNS predeterminado, `53`. Para usar el puerto publicado en la máquina, la consulta equivalente es `dig @127.0.0.1 -p 15353 protos.lab TXT +norecurse`.

La primera consulta, inmediatamente después del reinicio, dio:

```text
;; communications error to 172.30.0.41#53: connection refused
;; no servers could be reached
```

Se repitió el mismo comando sin cambiar la zona ni la dirección. Por la secuencia observada, lo más probable es que la primera consulta haya salido antes de que BIND empezara a escuchar. La segunda devolvió:

```text
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 36622
;; flags: qr aa; QUERY: 1, ANSWER: 2, AUTHORITY: 1, ADDITIONAL: 2

;; ANSWER SECTION:
protos.lab.     3600    IN    TXT   "cachito hola"
protos.lab.     3600    IN    TXT   "v=protos1"

;; AUTHORITY SECTION:
protos.lab.     3600    IN    NS    ns1.protos.lab.

;; ADDITIONAL SECTION:
ns1.protos.lab. 3600    IN    A     172.30.0.41

;; SERVER: 172.30.0.41#53(172.30.0.41) (UDP)
```

El espaciado de las columnas está normalizado. `NOERROR` indica que la consulta se procesó sin error. `qr` marca el mensaje como respuesta y `aa` indica que BIND respondió con autoridad sobre la zona. Las dos líneas TXT confirman que el nuevo registro está publicado y que el original se conservó.

## 7. Verificar todos los registros solicitados

```bash
dig @172.30.0.41 protos.lab SOA +norecurse +noall +answer
dig @172.30.0.41 protos.lab NS +norecurse +noall +answer
dig @172.30.0.41 ns1.protos.lab A +norecurse +noall +answer
dig @172.30.0.41 www.protos.lab A +norecurse +noall +answer
dig @172.30.0.41 mail.protos.lab A +norecurse +noall +answer
dig @172.30.0.41 protos.lab MX +norecurse +noall +answer
dig @172.30.0.41 ftp.protos.lab CNAME +norecurse +noall +answer
```

`+noall` desactiva la salida detallada y `+answer` vuelve a mostrar solo los registros de respuesta. Así se pueden comparar directamente con los datos extraídos de la captura.

Salida real, con espaciado normalizado:

```text
protos.lab.      3600  IN  SOA    ns1.protos.lab. admin.protos.lab. 2018010102 3600 1800 604800 86400
protos.lab.      3600  IN  NS     ns1.protos.lab.
ns1.protos.lab.  3600  IN  A      172.30.0.41
www.protos.lab.  3600  IN  A      172.30.0.50
mail.protos.lab. 3600  IN  A      172.30.0.51
protos.lab.      3600  IN  MX     10 mail.protos.lab.
ftp.protos.lab.  3600  IN  CNAME  www.protos.lab.
```

Los datos y TTL coinciden con los de la captura. El serial refleja la actualización y la consulta TXT anterior demuestra que se publicó `cachito hola`.

