# LabRecu2026 · Ejercicio 3 · Zona autoritativa con BIND9

## Qué pide la consigna

Servir la zona `recu.protos.foo` desde tu BIND, publicar el contacto `admin@recu.protos.foo`, copiar la IPv4 de `bar.protos.foo` al A de la raíz, crear el alias `www`, copiar los MX de `mail.protos.foo` con sus preferencias y autorizar solo a `1.2.3.4` mediante SPF. La verificación final se hace con `dig`.

En el lab BIND ya viene instalado. La práctica consiste en declarar la zona, escribir sus registros, validar, arrancar el servicio y consultar el DNS local.

## 1. Consultar los datos de referencia

Salida real dentro de `alumno`:

```text
root@alumno:~# dig A bar.protos.foo +noall +answer
root@alumno:~# dig MX mail.protos.foo +noall +answer
bar.protos.foo.       300 IN A  93.184.216.34
mail.protos.foo.      300 IN MX 10 mx1.protos.foo.
mail.protos.foo.      300 IN MX 20 mx2.protos.foo.
```

`dig A bar.protos.foo` consulta la IPv4 del nombre indicado. `dig MX mail.protos.foo` pide los destinos de correo y sus preferencias. Al omitir `@servidor` usamos el DNS configurado en `alumno`. `+noall` oculta las secciones de salida y `+answer` habilita la sección de respuestas. Copiamos la IPv4 y los pares de preferencia y destino. Los TTL nuevos salen de la consigna. El `300` que aparece en estas respuestas pertenece a los registros de referencia.

## 2. Declarar la zona en named.conf.local

Abrimos `nano /etc/bind/named.conf.local` y agregamos:

```conf
zone "recu.protos.foo" {
    type master;
    file "/etc/bind/db.recu.protos.foo";
};
```

| Línea | Qué significa y por qué está |
|---|---|
| `zone "recu.protos.foo" {` | Abre la declaración de la zona exacta que pide el enunciado. BIND usa ese nombre como origen al interpretar los registros del archivo. |
| `type master;` | Declara que este BIND es primario para la zona y la carga desde su archivo local. Cumple el requisito de que nuestro servidor sea autoritativo. |
| `file "/etc/bind/db.recu.protos.foo";` | Señala la ruta absoluta del archivo que contiene los registros. El nombre del archivo es una elección de la práctica. Lo importante es que la ruta declarada coincida con el archivo creado. |
| `};` | Cierra el bloque de configuración de la zona. |

`named.conf.local` está incluido desde la configuración principal de BIND en el lab. Ahí declaramos qué zona sirve y dónde leerla. El archivo `db.recu.protos.foo` contiene los registros que se publican. [Configuración de zonas en BIND](https://bind9.readthedocs.io/en/v9.18.39/reference.html#zone-statement-grammar)

## 3. Escribir db.recu.protos.foo

```dns
$TTL 3600

@ IN SOA ns1.recu.protos.foo. admin.recu.protos.foo. (
    2026111101 ; Serial
    3600       ; Refresh
    900        ; Retry
    1209600    ; Expire
    300        ; Negative Cache TTL
)

@       IN NS    ns1.recu.protos.foo.
ns1     IN A     192.168.60.20

@       3600    IN A     93.184.216.34
www     1209600 IN CNAME recu.protos.foo.

@       604800  IN MX    10 mx1.protos.foo.
@       604800  IN MX    20 mx2.protos.foo.

@       IN TXT   "v=spf1 ip4:1.2.3.4 -all"
```

### Cómo leer los nombres y los TTL

`@` representa el origen `recu.protos.foo.`. Un nombre relativo como `ns1` se expande a `ns1.recu.protos.foo.`. El punto final marca un nombre completo. `IN` indica la clase Internet. El valor entre el nombre y `IN`, cuando está presente, es el TTL en segundos. `$TTL 3600` les da un TTL predeterminado de una hora a los registros que carecen de un valor explícito. Elegimos ese valor predeterminado y escribimos además los tres TTL que la consigna fija para el A de la raíz, el CNAME y los MX. [Archivos de zona DNS](https://www.rfc-editor.org/rfc/rfc1035.html#section-5.1)

### Cómo se arma el SOA

`@ IN SOA` publica los datos administrativos de la zona. El primer nombre, `ns1.recu.protos.foo.`, es el servidor primario. El segundo, `admin.recu.protos.foo.`, representa el correo `admin@recu.protos.foo` pedido. En ese campo, el primer punto sin escape separa el usuario del dominio. Los paréntesis permiten escribir los valores del SOA en varias líneas y lo que sigue a cada punto y coma es un comentario.

| Valor | Qué controla y por qué lo elegimos |
|---|---|
| `2026111101` | Serial de la zona. Usamos la fecha de la práctica, 11 de noviembre de 2026, y revisión `01`. Si después publicamos una versión nueva, incrementamos el serial para que un secundario pueda detectarla. |
| `3600` | Refresh. Un secundario puede comprobar si hay una versión nueva cada hora mediante este intervalo. |
| `900` | Retry. Si falla esa comprobación, espera 15 minutos antes de reintentar. |
| `1209600` | Expire. Da al secundario un margen de 14 días para servir su copia desde la última actualización exitosa si pierde contacto con el primario. |
| `300` | Campo usado para limitar la caché negativa. Con el TTL de este SOA, una respuesta negativa puede cachearse hasta 5 minutos. |

El enunciado fija el contacto del SOA y deja a nuestro criterio el serial inicial y los cuatro tiempos. Los TTL exigidos para A, CNAME y MX se fijan en sus propias líneas. [Campos del SOA](https://www.rfc-editor.org/rfc/rfc1035.html#section-3.3.13) · [Caché negativa](https://www.rfc-editor.org/rfc/rfc2308.html#section-5)

### Cómo sale cada registro de lo que pide el enunciado

| Línea | Qué publica y de dónde sale |
|---|---|
| `@ IN NS ns1.recu.protos.foo.` | Identifica al servidor de nombres autoritativo de la zona. Elegimos `ns1` como nombre para nuestro BIND. |
| `ns1 IN A 192.168.60.20` | Da una IPv4 al servidor que acabamos de anunciar en el NS. Usamos la IP de `alumno`, donde corre BIND en este lab. |
| `@ 3600 IN A 93.184.216.34` | Asocia `recu.protos.foo.` a la IPv4 que devolvió `bar.protos.foo`. Una hora son `3600` segundos. |
| `www 1209600 IN CNAME recu.protos.foo.` | Hace que `www.recu.protos.foo.` sea un alias de la raíz de la zona. Dos semanas son `1209600` segundos. |
| `@ 604800 IN MX 10 mx1.protos.foo.` | Anuncia `mx1` para recibir correo. Conservamos su preferencia `10` del DNS de referencia y publicamos el TTL de una semana. |
| `@ 604800 IN MX 20 mx2.protos.foo.` | Anuncia el segundo destino con preferencia `20`. Entre los dos, el número menor tiene prioridad. Los puntos finales preservan los nombres externos completos. |
| `@ IN TXT "v=spf1 ip4:1.2.3.4 -all"` | Publica la política de correo saliente. `v=spf1` identifica SPF, `ip4:1.2.3.4` autoriza esa IPv4 y `-all` produce un resultado SPF Fail para cualquier otro origen. El receptor aplica su propia política a ese resultado. |

El A de `ns1` indica dónde corre el DNS. El A de la raíz publica la IP que pidió la consigna. En correo, el MX indica **adónde entregar** los mensajes dirigidos al dominio y SPF declara **qué IP está autorizada a enviar** usando el dominio que se está evaluando. [SPF y el mecanismo ip4](https://www.rfc-editor.org/rfc/rfc7208.html#section-5.6)

## 4. Validar los archivos

Salidas reales:

```text
root@alumno:~# named-checkzone recu.protos.foo /etc/bind/db.recu.protos.foo
zone recu.protos.foo/IN: loaded serial 2026111101
OK
root@alumno:~# named-checkconf -z
zone recu.protos.foo/IN: loaded serial 2026111101
zone localhost/IN: loaded serial 2
zone 127.in-addr.arpa/IN: loaded serial 1
zone 0.in-addr.arpa/IN: loaded serial 1
zone 255.in-addr.arpa/IN: loaded serial 1
```

- `named-checkzone recu.protos.foo /etc/bind/db.recu.protos.foo` valida el archivo de esa zona. El primer argumento le da el origen para interpretar los nombres relativos. El segundo elige el archivo. `loaded serial` y `OK` indican que el archivo pudo cargarse con el serial esperado.
- `named-checkconf -z` valida la configuración principal y sus archivos incluidos. Con `-z`, también intenta cargar las zonas primarias declaradas. Esto comprueba que BIND ve el bloque agregado en `named.conf.local` y encuentra el archivo de zona que declaramos. Las otras líneas corresponden a zonas que ya venían con BIND.

Estas pruebas validan la configuración en disco. El enunciado pide además comprobar el servicio en ejecución. [Herramientas de validación de BIND](https://bind9.readthedocs.io/en/v9.18.39/manpages.html)

## 5. Arrancar BIND y verificar con dig

```bash
systemctl start bind9
dig @127.0.0.1 recu.protos.foo SOA +norecurse
```

`systemctl start bind9` arranca el servicio. En `dig`, `@127.0.0.1` selecciona el BIND de `alumno`, `SOA` pide los datos administrativos de la zona y `+norecurse` envía la consulta sin pedir recursión. Este es el extracto de la salida real.

```text
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 15433
;; flags: qr aa ra; QUERY: 1, ANSWER: 1, AUTHORITY: 1, ADDITIONAL: 2

;; ANSWER SECTION:
recu.protos.foo.        3600 IN SOA ns1.recu.protos.foo. admin.recu.protos.foo. 2026111101 3600 900 1209600 300

;; AUTHORITY SECTION:
recu.protos.foo.        3600 IN NS  ns1.recu.protos.foo.

;; ADDITIONAL SECTION:
ns1.recu.protos.foo.    3600 IN A   192.168.60.20

;; SERVER: 127.0.0.1#53(127.0.0.1) (UDP)
```

`NOERROR` y la respuesta SOA muestran que la consulta se resolvió. `aa` indica que el servidor respondió como autoridad para la zona. `ra` anuncia que el servidor ofrece recursión. En esta consulta, `+norecurse` hizo que el cliente enviara la pregunta con el flag `rd` desactivado. El SOA trae el contacto y el serial de la zona que configuramos. Las secciones `AUTHORITY` y `ADDITIONAL` muestran el NS publicado y su dirección `192.168.60.20`.

## 6. Comprobar los registros y sus TTL

```bash
dig @127.0.0.1 recu.protos.foo A +norecurse +noall +answer
dig @127.0.0.1 www.recu.protos.foo CNAME +norecurse +noall +answer
dig @127.0.0.1 recu.protos.foo MX +norecurse +noall +answer
dig @127.0.0.1 recu.protos.foo TXT +norecurse +noall +answer
```

Repetimos `@127.0.0.1` y `+norecurse` para consultar al mismo BIND. Cada comando pide un tipo de registro. `+noall` oculta las secciones de la salida y `+answer` habilita la sección de respuestas. Así se puede comparar la segunda columna, que indica el TTL en segundos.

Salida real de las cuatro consultas.

```text
recu.protos.foo.        3600    IN A     93.184.216.34
www.recu.protos.foo.    1209600 IN CNAME recu.protos.foo.
recu.protos.foo.        604800  IN MX    10 mx1.protos.foo.
recu.protos.foo.        604800  IN MX    20 mx2.protos.foo.
recu.protos.foo.        3600    IN TXT   "v=spf1 ip4:1.2.3.4 -all"
```

El A publica la misma IPv4 que devolvió `bar.protos.foo` y tiene TTL de una hora. El CNAME de `www` apunta a la raíz con TTL de dos semanas. Los MX conservan los nombres y las preferencias del DNS de referencia, con TTL de una semana. El TXT publica la autorización SPF para `1.2.3.4`. Con estas consultas queda demostrada la configuración que pide el ejercicio.
