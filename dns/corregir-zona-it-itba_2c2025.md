# Protocolos — 2C 2025, ejercicio 3: corregir zona BIND
## Resultado
Se configuró it.itba.edu.ar en la VM del estudiante, corrigiendo el archivo /etc/bind/db.it.itba.edu.ar.
Se validaron archivo y configuración, se reinició BIND y se obtuvieron respuestas NOERROR y autoritativas (aa) para SOA, NS, A del NS, MX, pampero y ambos alias.
No se configuraron secundarios ni se verificó una delegación pública; las pruebas fueron directas contra 127.0.0.1.

## 1. Estado y declaración
~~~bash
systemctl status bind9
~~~
systemctl administra servicios; status consulta; bind9 es el nombre utilizado. Mostró named.service activo. Los avisos de validación de otros dominios no eran errores de esta zona.

~~~bash
sudo nano /etc/bind/named.conf.local
~~~
sudo permite editar; nano abre el archivo. Se agregó conservando zonas anteriores:
~~~conf
// Parcial 2C 2025 - Ejercicio 3
zone "it.itba.edu.ar" {
    type master;
    file "/etc/bind/db.it.itba.edu.ar";
};
~~~
zone selecciona dominio; type master declara primaria; file ruta local. No duplicar declaración. // es comentario en named.conf; en zona se usa ;.

## 2. Archivo roto original
Se guardó tal cual en la ruta declarada:
~~~bash
sudo nano /etc/bind/db.it.itba.edu.ar
~~~
~~~dns
$TTL 604800
@ IN SOA ns1.it.itba.edu.ar. admin@it.itba.edu.ar. (
        2025060500      ; Serial
        604800          ; Refresh
        86400           ; Retry
        2419200         ; Expire
        604800          ; Negative Cache TTL
)

; Name Servers
@       IN NS ns1.it.itba.edu.ar.

; Mail
@       IN MX 10 mail.

; Hosts
ns1.it.itba.edu.ar     IN A 192.168.70.1
pampero                IN A 192.168.70.10

; Aliases
www     IN A pampero
correo  IN CNAME pampero
~~~
Numeración referida a este bloque: TTL 1, SOA 2, serial 3, refresh 4, retry 5, expire 6, negativo 7, NS 11, MX 14, A ns1 17, A pampero 18, www 21, correo 22.

### ⭐ En el parcial: bajar el archivo de http://protos.foo/zona (en vez de pegarlo)
En la práctica el contenido se pegó a mano porque `protos.foo` solo resuelve en la red del parcial. El día del examen:

~~~bash
curl -i http://protos.foo/zona
~~~
-i muestra headers de respuesta y cuerpo. Confirmar `200 OK` y que el cuerpo sea una zona ($TTL, SOA), no una página de error HTML.

~~~bash
curl -o ~/zona.orig http://protos.foo/zona
~~~
-o guarda la respuesta en el archivo indicado en vez de mostrarla. Sin sudo: se guarda en el home. Es la copia del original para comparar al final.

~~~bash
sudo cp ~/zona.orig /etc/bind/db.it.itba.edu.ar
~~~
sudo porque /etc/bind es del sistema. Alternativa en un paso: `sudo curl -o /etc/bind/db.it.itba.edu.ar http://protos.foo/zona` (pero se pierde la copia original).

~~~bash
ls -l /etc/bind/db.it.itba.edu.ar
cat -A /etc/bind/db.it.itba.edu.ar | head
~~~
- ls -l: named corre como usuario bind y debe poder leerlo. Si no: `sudo chmod 644 /etc/bind/db.it.itba.edu.ar`.
- cat -A muestra caracteres invisibles: fin de línea normal = `$`. Si aparece `^M$`, el archivo tiene finales Windows (CRLF); limpiarlo con `sudo sed -i 's/\r$//' /etc/bind/db.it.itba.edu.ar`. Trampa que no se ve en nano.

Al terminar todas las correcciones, para el video:
~~~bash
diff -u ~/zona.orig /etc/bind/db.it.itba.edu.ar
~~~
-u formato unificado: líneas `-` son las originales y `+` las corregidas. Muestra todos los arreglos juntos.

## 3. Validar y corregir de a uno
~~~bash
sudo named-checkzone it.itba.edu.ar /etc/bind/db.it.itba.edu.ar
~~~
named-checkzone intenta cargar y comprobar sintaxis y coherencia; primer argumento es origen de zona, segundo archivo. No inicia ni recarga el servicio.

No es cierto que siempre muestre exactamente un error y se detenga en el primero. Puede emitir varios diagnósticos, y algunos controles se hacen solo después de parsear correctamente. Aquí se corrigió de a uno y se repitió.

### Error 1: A cuyo contenido es un nombre
Salida real inicial:
~~~text
dns_rdata_fromtext: /etc/bind/db.it.itba.edu.ar:21: near 'pampero': bad dotted quad
zone it.itba.edu.ar/IN: loading from master file /etc/bind/db.it.itba.edu.ar failed: bad dotted quad
zone it.itba.edu.ar/IN: not loaded due to errors.
~~~
Un A exige IPv4 válida, no hostname.
~~~bash
sudo nano +21 /etc/bind/db.it.itba.edu.ar
~~~
+21 abre en línea 21. Se cambió únicamente:
~~~dns
www IN CNAME pampero
~~~
CNAME es alias; el destino relativo se completa con el origen. Otra opción era www IN A 192.168.70.10.
Después de guardar se repitió named-checkzone.

### Error 2: NS sin dirección por expansión del nombre
Nueva salida:
~~~text
zone it.itba.edu.ar/IN: NS 'ns1.it.itba.edu.ar' has no address records (A or AAAA)
zone it.itba.edu.ar/IN: not loaded due to errors.
~~~
La línea 17 sin punto final creaba:
~~~text
ns1.it.itba.edu.ar.it.itba.edu.ar.
~~~
El NS apuntaba al nombre correcto, pero el A estaba en otro propietario.
~~~bash
sudo nano +17 /etc/bind/db.it.itba.edu.ar
~~~
Se agregó punto final:
~~~dns
ns1.it.itba.edu.ar. IN A 192.168.70.1
~~~
También sería válido ns1 IN A 192.168.70.1. El origen proviene del nombre de zona aunque no se escriba $ORIGIN.
El validador sí detectó la falta de dirección del NS interno.

### Error 3: MX absoluto equivocado
Tras corregir NS:
~~~text
zone it.itba.edu.ar/IN: getaddrinfo(mail) failed: Temporary failure in name resolution
zone it.itba.edu.ar/IN: loaded serial 2025060500
OK
~~~
La zona pasó, pero el aviso seguía siendo relevante. mail. es nombre absoluto bajo la raíz DNS; no se convierte en mail.it.itba.edu.ar.
La falla temporal no demuestra universalmente que ese nombre no exista, pero sí que no pudo resolverse allí y no corresponde al host interno pretendido.

Se eligió usar pampero como destino del MX, pues ya tiene un A. Se asume para este ejercicio que aloja correo; dig no comprueba un servicio SMTP.
~~~dns
@ IN MX 10 pampero.it.itba.edu.ar.
~~~
10 es preferencia: menor número se prefiere. El punto final evita agregar origen. No se eligió correo como MX porque correo es CNAME; un destino MX no debe ser alias.
Alternativa: definir mail IN A con IP real del servidor y usar MX 10 mail.it.itba.edu.ar.
Nueva validación:
~~~text
zone it.itba.edu.ar/IN: loaded serial 2025060500
OK
~~~

### Error 4: correo del responsable en SOA
La línea 2 todavía contenía admin@it.itba.edu.ar. y esta versión no lo rechazó. Se corrigió manualmente:
~~~dns
@ IN SOA ns1.it.itba.edu.ar. admin.it.itba.edu.ar. (
~~~
RNAME es representación de mailbox como nombre DNS: el primer punto separa usuario y dominio. admin.it.itba.edu.ar. representa admin@it.itba.edu.ar. No lleva @ literal.
Si el usuario fuera example.admin, su punto literal se escaparía: example\.admin.it.itba.edu.ar.

### Alias correo
correo IN CNAME pampero ya era correcto. El destino se expande a pampero.it.itba.edu.ar. No coexistía con otro dato en correo y no hubo que cambiarlo.
No hay CNAME en apex ni bucles en el archivo dado.

## 4. Ajuste SOA y caché
Se editó TTL y SOA:
~~~dns
$TTL 300
@ IN SOA ns1.it.itba.edu.ar. admin.it.itba.edu.ar. (
        2026102601      ; Serial
        300             ; Refresh
        60              ; Retry
        604800          ; Expire
        60              ; Negative Cache TTL
)
~~~
| Campo | Antes | Ahora | Razón |
|---|---|---|---|
| TTL por defecto | 604800: 7 días | 300: 5 minutos | Permite renovar registros cacheados más seguido |
| Serial | 2025060500 | 2026102601 | Versión superior con formato AAAAMMDDNN |
| Refresh | 604800: 7 días | 300: 5 minutos | Comprobación periódica de secundarios más frecuente |
| Retry | 86400: 1 día | 60: 1 minuto | Reintento rápido tras fallo |
| Expire | 2419200: 28 días | 604800: 7 días | Margen ante indisponibilidad prolongada, mayor que refresh |
| Mínimo negativo | 604800: 7 días | 60: 1 minuto | Evita conservar demasiado tiempo respuestas negativas nuevas |

Son valores elegidos para una corrección urgente del laboratorio, no una receta universal.
La vida de caché negativa se determina con el menor entre TTL del SOA y su campo MINIMUM: aquí min(300,60)=60.
Expire no acelera la propagación: limita cuánto sirve un secundario sin refrescar con éxito.

Serial: los secundarios comparan la versión y transfieren si corresponde. Editar contenido sin aumentarlo puede dejar secundarios sirviendo la anterior. AAAAMMDDNN es convención; BIND usa aritmética de serial de 32 bits, no interpreta fechas. En este caso el incremento es válido. Nuevas ediciones publicadas deben subirlo.

Refresh/retry afectan secundarios; TTL afecta cachés. NOTIFY puede disparar una comprobación antes de refresh, pero no elimina la necesidad de serial correcto. No se configuraron secundarios en esta práctica.
Bajar TTL no vacía cachés existentes: una respuesta previamente cacheada con 7 días puede seguir allí hasta expirar. Consultar directamente el primario muestra sus nuevos datos antes que algunos clientes.
Estos cambios no garantizan propagación pública instantánea ni arreglan delegaciones/firewalls.

## 5. Archivos finales completos
### named.conf.local, bloque agregado
~~~conf
// Parcial 2C 2025 - Ejercicio 3
zone "it.itba.edu.ar" {
    type master;
    file "/etc/bind/db.it.itba.edu.ar";
};
~~~

### /etc/bind/db.it.itba.edu.ar
~~~dns
$TTL 300
@ IN SOA ns1.it.itba.edu.ar. admin.it.itba.edu.ar. (
        2026102601      ; Serial
        300             ; Refresh
        60              ; Retry
        604800          ; Expire
        60              ; Negative Cache TTL
)

; Name Servers
@       IN NS ns1.it.itba.edu.ar.

; Mail
@       IN MX 10 pampero.it.itba.edu.ar.

; Hosts
ns1.it.itba.edu.ar.    IN A 192.168.70.1
pampero                IN A 192.168.70.10

; Aliases
www     IN CNAME pampero
correo  IN CNAME pampero
~~~

## 6. Validación y publicación reales
~~~bash
sudo named-checkzone it.itba.edu.ar /etc/bind/db.it.itba.edu.ar
~~~
Salida:
~~~text
zone it.itba.edu.ar/IN: loaded serial 2026102601
OK
~~~
~~~bash
sudo named-checkconf
~~~
Sin argumentos revisa named.conf e inclusiones. No imprimió errores. Sin -z no reemplaza la carga de zonas hecha antes por named-checkzone.
~~~bash
sudo systemctl restart bind9
~~~
systemctl administra servicios; restart detiene e inicia. Se ejecutó correctamente.

## 7. Pruebas dig reales
En todos:
- dig consulta DNS.
- @127.0.0.1 selecciona directamente el BIND local, no el resolvedor por defecto.
- Nombres terminados en punto son absolutos.
- Último argumento es tipo solicitado.
- NOERROR indica consulta sin error; aa significa respuesta autoritativa.
- TTL numérico en segundos. Todos los datos de respuesta de estas consultas mostraron 300.
- SERVER: 127.0.0.1#53 confirma servidor y puerto.

~~~bash
dig @127.0.0.1 it.itba.edu.ar. SOA
~~~
~~~text
it.itba.edu.ar. 300 IN SOA ns1.it.itba.edu.ar. admin.it.itba.edu.ar. 2026102601 300 60 604800 60
~~~
Responsable, serial y tiempos coinciden.
~~~bash
dig @127.0.0.1 it.itba.edu.ar. NS
~~~
~~~text
it.itba.edu.ar. 300 IN NS ns1.it.itba.edu.ar.
~~~
La sección adicional también mostró A correcto del NS.
~~~bash
dig @127.0.0.1 ns1.it.itba.edu.ar. A
~~~
~~~text
ns1.it.itba.edu.ar. 300 IN A 192.168.70.1
~~~
~~~bash
dig @127.0.0.1 it.itba.edu.ar. MX
~~~
~~~text
it.itba.edu.ar. 300 IN MX 10 pampero.it.itba.edu.ar.
~~~
La sección adicional mostró pampero A 192.168.70.10.
~~~bash
dig @127.0.0.1 pampero.it.itba.edu.ar. A
~~~
~~~text
pampero.it.itba.edu.ar. 300 IN A 192.168.70.10
~~~
~~~bash
dig @127.0.0.1 www.it.itba.edu.ar. A
~~~
~~~text
www.it.itba.edu.ar. 300 IN CNAME pampero.it.itba.edu.ar.
pampero.it.itba.edu.ar. 300 IN A 192.168.70.10
~~~
~~~bash
dig @127.0.0.1 correo.it.itba.edu.ar. A
~~~
~~~text
correo.it.itba.edu.ar. 300 IN CNAME pampero.it.itba.edu.ar.
pampero.it.itba.edu.ar. 300 IN A 192.168.70.10
~~~
Pedir A de un alias mostró cadena completa; para ver solo alias se puede consultar CNAME.

## 8. Tabla de errores
| Error o ajuste | Línea original | Corrección | Demostración |
|---|---|---|---|
| A con nombre | 21 | www IN CNAME pampero | dig www ... A muestra CNAME y A destino |
| Falta punto en propietario A de ns1 | 17 | ns1.it.itba.edu.ar. IN A 192.168.70.1 | dig ns1 ... A y adicional de NS |
| MX mail. equivocado | 14 | MX 10 pampero.it.itba.edu.ar. | dig zona MX y A del destino |
| RNAME con @ literal | 2 | admin.it.itba.edu.ar. | dig zona SOA |
| Serial anterior a las correcciones | 3 | 2026102601 | SOA muestra versión nueva |
| Caché por defecto larga | 1 | $TTL 300 | TTL 300 en respuestas |
| Refresh/retry lentos | 4–5 | 300 / 60 | SOA; secundarios no probados |
| Expire | 6 | 604800 | SOA; margen mayor que refresh |
| Caché negativa larga | 7 | 60 | SOA; mínimo con TTL SOA |
| correo CNAME pampero | 22 | Sin cambio | Cadena correcta, no era error |

## 9. Variantes: qué cambia y qué línea tocar
| Variante | Qué revisar/corregir |
|---|---|
| Falta paréntesis SOA | Completar ( antes de números y ) al final; revisar EOF/unexpected token en named-checkzone |
| TTL después de IN | No es necesariamente error: www 300 IN A 192.0.2.1 y www IN 300 A 192.0.2.1 son válidos en BIND; usar la primera forma para claridad |
| TTL después del tipo A | www IN A 300 192.0.2.1 es incorrecto: 300 ya está en posición de datos; mover TTL antes del tipo |
| Falta NS en raíz | Agregar @ IN NS ns1.it.itba.edu.ar. y dirección del NS interno |
| Serial menor o igual al publicado | Poner versión más nueva según aritmética DNS; el validador aislado no conoce necesariamente el histórico |
| MX hacia correo CNAME | Reemplazar destino por pampero con A/AAAA propio, o convertir servidor mail en host real |
| CNAME y A/TXT en mismo nombre | Elegir alias o datos propios; no mezclarlos, salvo metadatos DNSSEC permitidos |
| CNAME en apex @ | No puede coexistir con SOA/NS obligatorios; usar A/AAAA en raíz y alias en otro nombre |
| IPv4 inválida | Corregir cada octeto a 0–255; A no admite hostname ni IPv6 |
| AAAA con IPv4 | Usar A para IPv4 o AAAA con IPv6 válida |
| Falta punto en nombre completo | Usar FQDN terminado en punto o nombre relativo corto |
| Punto en nombre corto mail. | Es absoluto: usar mail o mail.it.itba.edu.ar. si se pretende el host interno |
| Punto duplicado ns1.. | Etiqueta vacía intermedia; corregir a un único separador |
| Bucle CNAME | Romper el ciclo; terminar cadena en nombre con datos apropiados |
| mail de usuario con punto | Escapar punto literal del usuario, ejemplo example\.admin.it.itba.edu.ar. |
| TTL explícito alto en un RR | Cambiar ese TTL: bajar $TTL no reemplaza TTL explícitos |

Corrección importante: el orden TTL/clase admite ambas variantes antes del tipo. No afirmar que cualquier TTL después de IN es un error.

## Frase para justificar
“Corregí los registros y los nombres de la zona, aumenté el serial y ajusté sus tiempos; validé la carga y comprobé con dig respuestas autoritativas y los destinos correctos.”

## Estado y guardado
La zona quedó declarada y activa en BIND local; no se ejecutó limpieza ni se retiró esa declaración. Ninguna prueba demuestra alcance público o disponibilidad real de los servicios de las IP de ejemplo.
Descargar el apunte y guardar en la VM:
~~~bash
mkdir -p ~/protos/soluciones
~~~
mkdir crea directorios; -p padres faltantes.
~~~bash
cp ~/Downloads/25.2-3.md ~/protos/soluciones/25.2-3.md
~~~
cp copia origen a destino; ~ es home del usuario.

## Referencias oficiales
- [Zonas y formato BIND](https://bind9.readthedocs.io/en/stable/chapter3.html)
- [Transferencias y seriales](https://kb.isc.org/docs/aa-00726)

