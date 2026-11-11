# LabProtos2025-2C · Ejercicio III · Reparar una zona BIND9

## Qué pide el enunciado

BIND9 es autoritativo para `it.itba.edu.ar` y tiene problemas para cargar su archivo de zona. Hay que diagnosticar y corregir los registros, ajustar el SOA para facilitar la propagación de los cambios y demostrar con `dig` que BIND sirve la versión corregida. En el lab, la zona ya estaba declarada en `/etc/bind/named.conf.local` y el archivo para editar era `/etc/bind/db.it.itba.edu.ar`. La consigna también publica la copia original en `http://protos.foo/zona`.

## 1. Validar el archivo y corregir el alias www

```text
root@alumno:~# named-checkzone it.itba.edu.ar /etc/bind/db.it.itba.edu.ar
dns_rdata_fromtext: /etc/bind/db.it.itba.edu.ar:21: near 'pampero': bad dotted quad
zone it.itba.edu.ar/IN: loading from master file /etc/bind/db.it.itba.edu.ar failed: bad dotted quad
zone it.itba.edu.ar/IN: not loaded due to errors.
```

`named-checkzone` valida el archivo. El primer argumento es el origen de la zona y le da contexto para expandir nombres relativos. El segundo argumento es la ruta del archivo que lee.

El primer diagnóstico apunta a `www IN A pampero`. Un registro `A` necesita una IPv4 de cuatro octetos separados por puntos. Como `www` debe ser un alias de `pampero`, corresponde `www IN CNAME pampero`. Así el nombre corto del destino se expande a `pampero.it.itba.edu.ar.`, cuyo registro A contiene la IP `192.168.70.10`.

## 2. Reparar el A del servidor de nombres y el contacto del SOA

Al corregir el alias, el siguiente diagnóstico fue:

```text
root@alumno:~# named-checkzone it.itba.edu.ar /etc/bind/db.it.itba.edu.ar
zone it.itba.edu.ar/IN: NS 'ns1.it.itba.edu.ar' has no address records (A or AAAA)
zone it.itba.edu.ar/IN: not loaded due to errors.
```

El NS ya apuntaba a `ns1.it.itba.edu.ar.`, pero el dueño del A estaba escrito como `ns1.it.itba.edu.ar` sin el punto final. BIND lo interpretaba como relativo y le agregaba el origen. El A quedaba para `ns1.it.itba.edu.ar.it.itba.edu.ar.`. Agregamos el punto final al nombre del A para que coincidiera con el destino del NS.

También corregimos el **contacto del SOA**. El correo `admin@it.itba.edu.ar` se escribe `admin.it.itba.edu.ar.` en ese campo. El primer punto sin escapar separa la parte local `admin` del dominio. La secuencia `\.` sirve cuando la parte local del correo contiene un punto propio. Por ejemplo, `example.admin@foo.com.ar` se representa como `example\.admin.foo.com.ar.`. El `@` que abre el registro SOA representa la raíz de la zona. [Formato de registros y archivos de zona](https://www.rfc-editor.org/rfc/rfc1035.html#section-5.1)

## 3. Completar el destino del MX

La siguiente validación ya cargó la zona y mostró un aviso:

```text
root@alumno:~# named-checkzone it.itba.edu.ar /etc/bind/db.it.itba.edu.ar
zone it.itba.edu.ar/IN: it.itba.edu.ar/MX 'mail.it.itba.edu.ar' has no address records (A or AAAA)
zone it.itba.edu.ar/IN: loaded serial 2025060500
OK
```

`@ IN MX 10 mail` tiene un destino relativo válido. Se expande a `mail.it.itba.edu.ar.` y `10` es la preferencia del MX. El aviso decía que faltaba la dirección de ese destino. Un servidor de correo que consulte el MX obtiene el nombre `mail` y necesita su IP para conectarse. Agregamos el registro directo `mail IN A 192.168.70.10`.

**Supuesto de la resolución.** El enunciado no daba una IP aparte para el servicio de correo. Usamos la IP de `pampero` porque el alias `correo` del archivo original ya apuntaba a ese host. `mail` y `pampero` tienen cada uno su propio A, con la misma dirección.

Si la variante del ejercicio permite cambiar el nombre que devuelve el MX, `@ IN MX 10 pampero` usa el A que ya existe. El corrector del lab acepta un MX con destino resoluble mediante un A. En nuestra entrega conservamos el destino `mail` del archivo original.

## 4. Ajustar el serial y los tiempos de actualización

El enunciado pide que los cambios se propaguen correctamente y con rapidez. Los números específicos que elegimos se expresan en segundos, salvo el serial, que es el número de versión.

| Parámetro | Original → final | Qué controla y por qué |
|---|---|---|
| Serial | `2025060500` → `2025060501` | Un secundario puede detectar que el primario publicó una versión más nueva. Incrementarlo en uno alcanza para esta edición. |
| Refresh | `604800` → `3600` | El secundario comprueba si debe actualizar la zona después de 1 hora en lugar de 7 días. |
| Retry | `86400` → `900` | Si falla una comprobación, el secundario reintenta después de 15 minutos en lugar de 1 día. |
| Expire | `2419200` | El secundario puede servir su copia durante un máximo de 28 días sin refrescarla. Es el margen durante una caída prolongada del primario. |
| Negative Cache TTL | `604800` → `300` | Las nuevas respuestas negativas pueden cachearse por menos tiempo. En esta configuración el límite es 5 minutos. |
| `$TTL` | `604800` → `3600` | Fija el TTL predeterminado de los registros. En las consultas nuevas los registros aparecen con 1 hora de TTL. |

**Ejemplo para defenderlo.** El serial hace que un secundario pueda reconocer la versión que ya incluye el A de `mail`. El TTL negativo reduce la espera para volver a consultar después de una respuesta negativa cacheada. Los secundarios guardan una copia de la zona, mientras que los resolvers guardan respuestas a consultas. Las entradas ya cacheadas vencen con el TTL que recibieron en su momento. [Campos del SOA](https://www.rfc-editor.org/rfc/rfc1035.html#section-3.3.13) · [Caché negativa](https://www.rfc-editor.org/rfc/rfc2308.html#section-5)

## Archivo de zona corregido

```dns
$TTL 3600
@       IN SOA ns1.it.itba.edu.ar. admin.it.itba.edu.ar. (
        2025060501      ; Serial
        3600            ; Refresh
        900             ; Retry
        2419200         ; Expire
        300             ; Negative Cache TTL
)

; Name Servers
@       IN NS ns1.it.itba.edu.ar.

; Mail
@       IN MX 10 mail

; Hosts
ns1.it.itba.edu.ar.    IN A 192.168.70.1
pampero              IN A 192.168.70.10
mail                 IN A 192.168.70.10

; Aliases
www     IN CNAME pampero
correo  IN CNAME pampero
```

Los nombres relativos `pampero`, `mail`, `www` y `correo` usan el origen `it.itba.edu.ar.`. El punto final marca un nombre completo.

## 5. Validar en disco y recargar BIND

```text
root@alumno:~# named-checkzone it.itba.edu.ar /etc/bind/db.it.itba.edu.ar
zone it.itba.edu.ar/IN: loaded serial 2025060501
OK
root@alumno:~# systemctl reload bind9
```

La validación confirma que el archivo puede cargarse con el serial nuevo. `systemctl reload bind9` le pide al servicio en ejecución que relea su configuración y la zona. La consulta del SOA permite comprobar qué versión está sirviendo.

## 6. Verificar autoridad y serial con dig

```bash
dig @127.0.0.1 it.itba.edu.ar SOA +norecurse
```

- `@127.0.0.1` elige el BIND del propio contenedor.
- `it.itba.edu.ar SOA` pide el SOA de la zona.
- `+norecurse` envía la consulta sin pedir recursión.

Extracto de la salida real:

```text
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 56301
;; flags: qr aa ra; QUERY: 1, ANSWER: 1, AUTHORITY: 1, ADDITIONAL: 2

;; ANSWER SECTION:
it.itba.edu.ar.        3600 IN SOA ns1.it.itba.edu.ar. admin.it.itba.edu.ar. 2025060501 3600 900 2419200 300

;; AUTHORITY SECTION:
it.itba.edu.ar.        3600 IN NS  ns1.it.itba.edu.ar.

;; ADDITIONAL SECTION:
ns1.it.itba.edu.ar.    3600 IN A   192.168.70.1

;; SERVER: 127.0.0.1#53(127.0.0.1) (UDP)
```

`NOERROR` y la respuesta SOA indican que se pudo resolver la consulta. `aa` indica que BIND respondió como autoridad. `ra` indica que el servidor anuncia disponibilidad de recursión. La ausencia de `rd` indica que esta consulta no la pidió. El serial `2025060501` identifica la versión publicada.

## 7. Verificar cada registro

```bash
dig @127.0.0.1 ns1.it.itba.edu.ar A +norecurse +noall +answer
dig @127.0.0.1 pampero.it.itba.edu.ar A +norecurse +noall +answer
dig @127.0.0.1 www.it.itba.edu.ar CNAME +norecurse +noall +answer
dig @127.0.0.1 correo.it.itba.edu.ar CNAME +norecurse +noall +answer
dig @127.0.0.1 it.itba.edu.ar MX +norecurse +noall +answer
dig @127.0.0.1 mail.it.itba.edu.ar A +norecurse +noall +answer
```

`+noall +answer` deja solo la sección de respuestas. Salida real:

```text
ns1.it.itba.edu.ar.        3600 IN A     192.168.70.1
pampero.it.itba.edu.ar.    3600 IN A     192.168.70.10
www.it.itba.edu.ar.        3600 IN CNAME pampero.it.itba.edu.ar.
correo.it.itba.edu.ar.     3600 IN CNAME pampero.it.itba.edu.ar.
it.itba.edu.ar.            3600 IN MX    10 mail.it.itba.edu.ar.
mail.it.itba.edu.ar.       3600 IN A     192.168.70.10
```

Las consultas A comprueban las direcciones de `ns1` y `pampero`. Las CNAME muestran que ambos alias apuntan a `pampero`. Las dos últimas consultas verifican la cadena del correo. Primero el MX devuelve el nombre `mail` y luego su A devuelve la IP. La segunda columna, `3600`, confirma el TTL publicado de los seis registros.
