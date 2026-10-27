# Análisis de pcaps de parcial — Protocolos de Comunicación, ITBA

## Enunciado (textual)

*Fuente: 2C 2020 Ejercicios V y VI, y Recuperatorio Ejercicio II.*

**parcial-correo.pcap.gz (Ejercicio VI de VI)**

El archivo disponible en http://foo.leak.com.ar/parcial-correo.pcap.gz contiene entre sus paquetes un correo electrónico siendo transportado por alguno de los protocolos vistos en clase. El correo contiene una imagen. Muestre visualmente la imagen.

En el video respuesta que envíe:
1. Con el archivo pcap ya descargado muestre en Wireshark cómo encontrar el correo.
2. Luego muestre cómo lo procesa para obtener la imagen.
3. Finalmente muestre la imagen.

**dhcp-parcial.pcap.gz (Ejercicio V de VI)**

Obtenga control de la línea de comandos del usuario **pdc** del host `parcial.leak.com.ar` (existe un servidor SSH en el puerto 9090). Una llave privada que permite ingresar al usuario pdc se encuentra en http://foo.leak.com.ar/llave-pdc.pem, pero está con una passphrase. La passphrase tiene 11 caracteres y es la dirección IP (XX.XX.XX.XX) asignada por el servidor DHCP al cliente en la secuencia DHCP disponible en el archivo http://foo.leak.com.ar/dhcp-parcial.pcap.gz.

En el video respuesta que envíe:
1. Con el archivo pcap ya descargado muestre en Wireshark cómo encontrar la passphrase (llegue a mostrar el campo).
2. Muestre descarga de llave privada y cómo conectarse.
3. Una vez en el shell ejecute algún comando (ej date).

→ La passphrase es la respuesta de la sección C (yiaddr del ACK: `10.20.20.20`). La conexión es la receta de la llave .pem con `-p 9090`.

**botica / pcap de DNS y otros (Recuperatorio, Ejercicio II de V)**

En http://foo.leak.com.ar/parcial-dns-y-otros.pcap.gz se encuentra un archivo PCAP producido con Wireshark que contiene pedidos y respuestas DNS, y tramas de otros protocolos. En base a la información contenida en el archivo responda las siguientes preguntas:

A. ¿Cuál es la dirección IP del registro *ejercicio.leak.com.ar*? (1 punto)

B. Un usuario que recibe el correo electrónico destinado a <jcodagno@itba.edu.ar> ¿qué texto lee en su pantalla como cuerpo del mensaje? (1 punto)

→ B es la sección A4. Para A: filtro `dns.qry.name == "ejercicio.leak.com.ar"` y leer el registro A de la respuesta.

*Las preguntas de RIP, saltos de traceroute y contraseña de telnet (A1–A3) salen de la guía de parciales y de las páginas de práctica; no tengo la imagen del enunciado original.*

---

## RECETA GENERAL

Este apunte usa **las tres capturas reales adjuntadas**, analizadas con TShark 4.2.2. Se consultaron las dos páginas de Notion solicitadas y, para DHCP y variantes, la página “P-pcap – preguntas nuevas sobre dhcp-parcial, botica y parcial-correo”. Las respuestas de abajo fueron contrastadas con los paquetes, no copiadas sin verificar.

### 1. Ubicarse, identificar el archivo y ver los protocolos

En tu VM:

~~~bash
cd ~/protos/pcaps
capinfos botica.pcap.gz
tshark -n -r botica.pcap.gz -q -z io,phs
~~~

- cd cambia el directorio; ~ es tu carpeta personal.
- capinfos muestra formato, número de paquetes y otros metadatos.
- tshark es Wireshark por consola.
- -n evita resolución de nombres: muestra IP y puertos numéricos.
- -r ARCHIVO lee una captura guardada. Estos .gz se leen directamente; no hace falta gunzip.
- -q suprime el listado normal de paquetes.
- -z io,phs solicita la jerarquía de protocolos.

**Wireshark:** File → Open; Statistics → Capture File Properties y Statistics → Protocol Hierarchy. No hace falta capturar tráfico nuevo ni usar sudo para leer archivos accesibles.

Resultado real:

| Archivo | Paquetes | Evidencia destacada |
| --- | ---: | --- |
| botica.pcap.gz | 1963 | Telnet, SMTP/IMF, HTTP, RIP, ICMP, DHCP, DNS |
| parcial-correo.pcap.gz | 1573 | 88 paquetes reconocidos como SMTP, pero ningún IMF reconstruido |
| dhcp-parcial.pcap.gz | 4 | Discover, Offer, Request, ACK |

Estas capturas reúnen tráfico de fechas y escenarios diferentes. No interpretar su duración total como una única sesión de red continua, ni combinar hosts de distintos bloques para inventar una topología.

### 2. Encontrar los hosts y las conversaciones

~~~bash
tshark -n -r botica.pcap.gz -q -z endpoints,ip
tshark -n -r botica.pcap.gz -q -z conv,tcp
~~~

endpoints,ip resume direcciones IPv4; conv,tcp resume pares de extremos TCP. Son herramientas exploratorias; no sustituyen la evidencia de un paquete o flujo específico.

**Wireshark:** Statistics → Endpoints → IPv4; Statistics → Conversations → TCP. Los puertos y las IP ayudan a elegir la conversación.

### 3. Filtrar sin confundir captura con visualización

~~~bash
tshark -n -r botica.pcap.gz -Y 'ip.addr==192.168.0.1'
~~~

-Y aplica un filtro de visualización, igual al de la barra de Wireshark. ip.addr significa origen **o** destino; ip.src solo origen; ip.dst solo destino.

- == compara igualdad.
- && exige ambas condiciones.
- || permite cualquiera.
- ! niega una condición.
- Las comillas mantienen todo el filtro como un argumento de la terminal.
- -f usa filtros de captura con otra sintaxis: no usarlo como reemplazo de -Y en estas recetas.

### 4. Extraer campos y seguir flujos

~~~bash
tshark -n -r botica.pcap.gz -Y telnet -T fields -e tcp.stream | sort -u
tshark -n -r botica.pcap.gz -q -z follow,tcp,ascii,0
~~~

-T fields selecciona salida por campos; cada -e agrega una columna. tcp.stream identifica una conexión TCP dentro de esa captura. | envía la salida al siguiente comando; sort -u ordena y elimina líneas repetidas.

follow,tcp,ascii,0 muestra el flujo TCP 0 como texto. **Wireshark:** seleccionar un paquete → clic derecho → Follow → TCP Stream, o Analyze → Follow → TCP Stream. Elegir una sola dirección cuando el eco o las respuestas dificulten la lectura. Los colores dependen del tema: confirmar siempre los extremos del desplegable.

Los índices 0, 23, 26 y 27 de este apunte se verificaron en estos archivos concretos; no son universales.

### 5. Detalles, objetos y archivos

- -V muestra el árbol completo de cada paquete.
- -O http muestra en detalle HTTP y resume los otros protocolos.
- -E header=y agrega una fila con nombres de columnas.
- -E occurrence=f imprime la primera aparición de cada campo. Es importante para IP dentro de ICMP.
- Por defecto, un campo repetido puede salir separado por comas; no confundir cabecera IP externa con la citada dentro del ICMP.
- File → Export Objects → HTTP permite exportar objetos HTTP reconstruidos.
- File → Export Objects → IMF, si está disponible y hay mensajes reconstruidos, permite extraer el correo.
- Si no aparece el mensaje, seguir el flujo TCP, aislar la dirección cliente y separar DATA/MIME.
- -w escribe paquetes en una nueva captura; **no** extrae directamente el archivo PNG ni el texto de la conversación. Para texto usar > archivo.

### Respuestas rápidas verificadas

| Pregunta | Respuesta |
| --- | --- |
| Redes de 10.0.0.1 | Anuncia 200.0.1.0/24; se observa vecino 10.0.0.2 anunciando 200.0.2.0/24. En la interpretación RIP esperada: esas dos redes y el segmento 10.0.0.0, con /8 solo si se asume esquema classful. Ver límites en A1. |
| Saltos de 192.168.0.27 a 8.8.8.8 | 9, según sonda UDP a puerto 33442 y respuesta del destino |
| Login remoto a 192.168.0.1 | Telnet: usuario fake, contraseña user |
| Cuerpo del mail para jcodagno@itba.edu.ar | áéíóú |
| Imagen del otro correo | PNG 1200 × 628, imagen del encuentro OLS/ITBA sobre economía circular |
| DHCP | Cliente academy04, MAC 00:50:ba:12:47:cb; servidor 10.20.20.4; IP 10.20.20.20; lease 300 s; sin opción Router |

---

## A1. botica: ¿a qué redes tiene acceso 10.0.0.1?

**Qué buscamos:** respuestas RIP que anuncien redes alcanzables, distinguiéndolas de los pedidos de tabla.

~~~bash
tshark -n -r botica.pcap.gz -Y 'rip && rip.command==2' -T fields -e ip.src -e rip.version -e rip.ip -e rip.metric | sort -u
~~~

rip reconoce el protocolo; rip.command==2 selecciona Response; comando 1 sería Request. ip.src identifica al anunciante; rip.version la versión; rip.ip el destino anunciado; rip.metric su distancia.

Salida real, sin duplicados:

~~~text
10.0.0.1    1    200.0.1.0    1
10.0.0.2    1    200.0.2.0    1
~~~

Para ver una respuesta de cada router:

~~~bash
tshark -n -r botica.pcap.gz -Y 'frame.number==393 || frame.number==397' -V
~~~

frame.number es el número de paquete. || selecciona cualquiera de esos dos. El detalle real muestra destino IP 255.255.255.255 y MAC ff:ff:ff:ff:ff:ff en ambos anuncios; RIPv1, UDP 520.

**Respuesta razonada:**
1. 10.0.0.1 anuncia 200.0.1.0 con métrica 1.
2. 10.0.0.2, en el segmento de intercambio, anuncia 200.0.2.0 con métrica 1.
3. La lectura esperada del ejercicio es que 10.0.0.1 tiene su red 200.0.1.0, el segmento que comparte con 10.0.0.2 y puede aprender 200.0.2.0 a través de este último.

Para los anuncios externos 200.0.1.0 y 200.0.2.0 se infiere /24 bajo la interpretación classful de RIPv1. **La captura no transmite la máscara del enlace 10.0.0.x:** /8 es la suposición classful habitual del ejercicio, no un campo observado. RIPv1 puede operar sobre subredes con máscara conocida localmente: no deducir siempre la máscara efectiva solo por la clase.

La captura confirma anuncios, no muestra la tabla interna completa ni prueba que no existan filtros de importación, ACL u otras rutas. Si preguntan exclusivamente “qué anuncia 10.0.0.1”, la respuesta observada es **200.0.1.0**, no las dos redes. Para “acceso” se explica la inferencia de aprendizaje RIP.

**Trampas:**
- Métrica 16 en un Response significa inalcanzable.
- Una petición de tabla completa con comando 1 y métrica 16 no anuncia una ruta inalcanzable.
- En TShark 4.2.2 rip.netmask sale vacío para estos RIPv1: no afirmar que se observó una máscara explícita de ceros.
- La métrica anunciada no debe equipararse sin más al número de routers intermedios desde quien escucha: el receptor aplica las reglas de RIP al incorporar la ruta.

**Wireshark:** filtro rip; expandir Routing Information Protocol, revisar Command, Version, IP Address y Metric. Para centrarse en el router: rip && ip.src==10.0.0.1.

**Frase:** “Identifiqué los anuncios RIPv1 de ambos routers y distinguí las redes anunciadas de las rutas que se infieren por aprendizaje y del segmento compartido.”

## A2. botica: ¿a cuántos saltos está 8.8.8.8 desde 192.168.0.27?

**Qué buscamos:** asociar cada sonda UDP con su TTL de salida y luego con el ICMP que la cita.

~~~bash
tshark -n -r botica.pcap.gz -Y '!icmp && ip.src==192.168.0.27 && ip.dst==8.8.8.8 && udp' -T fields -E header=y -e frame.number -e ip.ttl -e udp.srcport -e udp.dstport
~~~

!icmp excluye las respuestas que contienen una copia de la sonda; así no se confunden con sondas originales. udp exige UDP. ip.ttl es el TTL del pedido original, y los puertos identifican la sonda.

Salida real:

~~~text
frame.number ip.ttl udp.srcport udp.dstport
1946         1      35596       33434
1947         2      54178       33435
1948         3      33752       33436
1949         4      49659       33437
1950         5      60414       33438
1951         6      37589       33439
1952         7      33714       33440
1953         8      38145       33441
1954         9      36523       33442
1955         10     57890       33443
1956         11     39091       33444
1957         12     35182       33445
~~~

Ahora buscamos quién respondió y qué sonda cita:

~~~bash
tshark -n -r botica.pcap.gz -Y 'icmp && ip.dst==192.168.0.27' -T fields -E header=y -E occurrence=f -e frame.number -e ip.src -e icmp.type -e icmp.code -e udp.dstport
~~~

icmp.type y icmp.code identifican el mensaje. Tipo 11/código 0 es TTL excedido; tipo 3/código 3 es puerto inalcanzable. **No cualquier tipo 3 demuestra llegada al destino**: revisar código y emisor. udp.dstport pertenece aquí a la sonda citada. occurrence=f conserva el primer ip.src, el del emisor externo.

~~~text
frame.number ip.src         icmp.type icmp.code udp.dstport
1958         192.168.0.1    11        0         33434
1959         72.14.194.198  11        0         33440
1960         8.8.8.8        3         3         33445
1961         8.8.8.8        3         3         33442
1962         8.8.8.8        3         3         33444
1963         8.8.8.8        3         3         33443
~~~

**Respuesta: 9 saltos en el sentido habitual del traceroute.** El paquete 1961 de 8.8.8.8 cita el puerto 33442, cuya sonda original es el 1954 con TTL 9. Es el menor TTL de salida que se observa llegando al destino. Bajo un camino estable, esto corresponde a 8 routers intermedios más el destino en el salto 9.

**Trampas verificadas:**
- La primera respuesta del destino en orden de captura es la del TTL 12, no la mínima.
- Solo dos routers responden Time Exceeded, pero eso no significa dos saltos.
- El paquete 1961 tiene dos TTL: 116 en el ICMP externo y 1 en la IP citada. Ninguno es el TTL original 9.
- Restar 116 a un supuesto TTL inicial 128 estima el retorno; no resuelve el camino de ida.
- En otra captura, si no se observa alcanzar el destino, no inventar una distancia exacta. Puede haber balanceo o cambios de ruta.

**Wireshark:** filtrar las sondas; en Internet Protocol Version 4 leer TTL, en UDP el puerto. Luego filtrar ICMP; expandir ICMP → IP original → UDP y cruzar el puerto. Clic derecho sobre TTL → Apply as Column ayuda, pero distinguir cabecera externa e interna.

**Frase:** “La respuesta de puerto inalcanzable de 8.8.8.8 cita una sonda que salió con TTL 9; ese es el menor TTL que llegó al destino.”

## A3. botica: ¿cuál es la contraseña del usuario que entra a 192.168.0.1?

**Qué buscamos:** la sesión Telnet y únicamente lo que escribe el cliente durante el login.

~~~bash
tshark -n -r botica.pcap.gz -Y telnet -T fields -e tcp.stream | sort -u
tshark -n -r botica.pcap.gz -q -z follow,tcp,ascii,0
~~~

Primer resultado: **0**. En el flujo:

~~~text
Node 0: 192.168.0.2:1254
Node 1: 192.168.0.1:23
~~~

El seguimiento ASCII incluye longitudes y cambios de dirección, y el usuario aparece con eco. Para mostrar las letras de la contraseña con evidencia puntual:

~~~bash
tshark -n -r botica.pcap.gz -Y 'telnet && ip.src==192.168.0.2 && frame.number>=36 && frame.number<=66' -T fields -e frame.number -e telnet.data
~~~

>= y <= limitan al tramo de login de este archivo. telnet.data muestra los datos de aplicación. Salida real:

~~~text
36 f
40 a
44 k
48 e
52 \r
58 u
60 s
62 e
64 r
66 \r
~~~

**Respuesta: usuario fake, contraseña user.** El servidor solicita Password antes del paquete 58; el cliente manda u, s, e, r y Enter. No sumar las letras del usuario ni duplicarlas con el eco.

**Wireshark:** filtro telnet → Follow TCP Stream → dirección 192.168.0.2 → 192.168.0.1. El usuario se ve repetido al mezclar ambas direcciones porque hay eco. La contraseña no se refleja en pantalla, pero viaja en claro. Los bytes IAC iniciales negocian opciones, no son contraseña.

**Frase:** “Seguí el flujo Telnet, aislé los datos del cliente y reconstruí la contraseña user después del pedido Password.”

## A4. botica: ¿qué cuerpo lee el destinatario jcodagno@itba.edu.ar?

**Qué buscamos:** el RCPT TO del sobre, el DATA correspondiente y la parte MIME decodificada.

~~~bash
tshark -n -r botica.pcap.gz -Y smtp -T fields -e tcp.stream -e ip.src -e ip.dst | sort -u
tshark -n -r botica.pcap.gz -q -z follow,tcp,ascii,26
tshark -n -r botica.pcap.gz -q -z follow,tcp,ascii,27
~~~

Los flujos SMTP reales son 26 y 27: el mismo mensaje en dos tramos. Extracto literal del flujo 26:

~~~text
MAIL FROM: <juan@leak.com.ar>
RCPT TO: <jcodagno@itba.edu.ar>
Subject: prueba
Content-Type: multipart/alternative; boundary="0000000000008285d40588771da8"

Content-Type: text/plain; charset="UTF-8"
Content-Transfer-Encoding: base64

w6HDqcOtw7PDug0K
~~~

**Antes del próximo comando:** queremos convertir la representación Base64 a bytes y leerlos como UTF-8:

~~~bash
printf '%s' 'w6HDqcOtw7PDug0K' | base64 --decode
~~~

printf imprime con formato %s sin agregar salto; | conecta comandos; base64 --decode decodifica. -d es su forma abreviada.

Resultado real: **áéíóú**, seguido de CRLF. La alternativa HTML decodificada es:

~~~html
<div dir="ltr">áéíóú</div>
~~~

**Respuesta:** el usuario lee **áéíóú**, no el bloque Base64. multipart/alternative ofrece el mismo contenido en dos representaciones; no son dos mensajes.

**Wireshark:** smtp → localizar RCPT TO → Follow TCP Stream. También imf en este archivo sí reconoce el mensaje. Expandir las partes MIME y revisar Content-Transfer-Encoding y charset. El flujo 27 agrega Received y confirma el reenvío.

**Frase:** “Localicé el correo para jcodagno, identifiqué Base64 y lo decodifiqué con el charset declarado; el cuerpo dice áéíóú.”

---

## B1. parcial-correo: el correo contiene una imagen; mostrarla

**Qué buscamos:** una conversación al puerto 25, aunque Wireshark no reconstruya IMF.

~~~bash
tshark -n -r parcial-correo.pcap.gz -Y 'tcp.port==25' -T fields -e tcp.stream | sort -u
tshark -n -r parcial-correo.pcap.gz -Y imf -T fields -e frame.number
~~~

tcp.port incluye puerto origen o destino. Primer resultado real: **23**. El segundo no imprime paquetes. No significa que no haya correo.

Seguir el flujo en formato raw:

~~~bash
tshark -n -r parcial-correo.pcap.gz -q -z follow,tcp,raw,23 > correo-raw.txt
~~~

raw imprime los bytes reconstruidos en hexadecimal; > guarda el texto completo de esa salida. **Ese archivo aún no es un .eml ni un PNG.** Sus extremos reales son:

~~~text
Node 0: 192.168.122.1:33572
Node 1: 192.168.122.235:25
~~~

En este caso Node 0 es el cliente. En el formato raw de TShark, sus líneas hexadecimales no llevan tab; las de Node 1 sí. Verificar extremos antes de reutilizar la selección en otra captura.

### Extracción reproducible del mensaje y de todas las partes

Se entrega extraer_correo.py junto al apunte; su código completo está al final. Copiarlo al directorio de trabajo o indicar su ruta absoluta.

~~~bash
python3 extraer_correo.py correo-raw.txt correo-extraido 0
file correo-extraido/5-image.png
~~~

python3 ejecuta el script; argumentos: seguimiento raw, carpeta de salida y nodo cliente 0. El script:
1. Selecciona los bytes del nodo correcto desde el flujo reconstruido por TShark.
2. Busca una línea DATA completa, no una coincidencia arbitraria dentro de texto.
3. Termina en la línea de punto y revierte el dot-stuffing si existe.
4. Usa el parser MIME de Python para decodificar Base64/quoted-printable y respetar charsets.
5. Guarda los adjuntos con nombres locales saneados y un índice.

Resultado real abreviado:

~~~text
Subject: feliz parcial
From: A <a@a>
To: V <b@b>
Bytes cliente: 601746 | CRLF: 0 | LF: 7844
0 multipart/mixed
1 multipart/related
2 multipart/alternative
3 text/plain
4 text/html
5 image/png image.png
Guardado: 5-image.png bytes: 437326
6 text/plain lineamientos-parcial.txt
Guardado: 6-lineamientos-parcial.txt bytes: 6680
~~~

file verificó:

~~~text
PNG image data, 1200 x 628, 8-bit/color RGB, non-interlaced
~~~

Para mostrarla en la VM:

~~~bash
xdg-open correo-extraido/5-image.png
~~~

xdg-open abre el archivo con el visor gráfico predeterminado. El contenido extraído es un anuncio del **Primer Encuentro Bimensual 2020 del OLS/ITBA, modalidad online, temática Economía Circular, 5 de mayo**.

![Imagen PNG extraída de parcial-correo.pcap.gz](pcap-image.png)

### Cómo hacerlo en Wireshark

1. Abrir parcial-correo.pcap.gz y filtrar tcp.port==25.
2. Seleccionar un paquete → Follow → TCP Stream; verificar flujo 23.
3. Elegir solo 192.168.122.1 → 192.168.122.235.
4. Show data as: Raw → Save as… → cliente-smtp.bin. En Raw, Save as guarda bytes binarios del flujo, no el texto hexadecimal de TShark.
5. Sacar el Base64 de la imagen y decodificarlo con un solo comando (probado sobre esta captura: da el mismo PNG de 1200 × 628, SHA-256 `8c0072cc…`, que el script):

~~~bash
awk '/^Content-Type: image\/png/{f=1;next} f && /^\r?$/ {if(!s){s=1;next}} f && s && /^--/{exit} f && s {print}' cliente-smtp.bin | base64 -d > imagen.png
file imagen.png
xdg-open imagen.png
~~~

- `/^Content-Type: image\/png/{f=1;next}`: cuando encuentra la cabecera de la parte PNG, prende la marca `f`.
- `f && /^\r?$/ {if(!s){s=1;next}}`: la primera línea vacía después de esa cabecera separa los headers MIME del contenido; desde ahí prende `s`.
- `f && s && /^--/{exit}`: la línea que empieza con `--` es el siguiente boundary; ahí termina el Base64.
- `f && s {print}`: imprime solo las líneas del Base64 de la imagen.
- `base64 -d`: decodifica a los bytes del PNG.
- Si la imagen es JPEG, cambiar `image\/png` por `image\/jpeg`. Si hay dos imágenes, saca la primera.

Si no podés guardar desde Wireshark, el mismo `cliente-smtp.bin` sale por consola:

~~~bash
tshark -n -r parcial-correo.pcap.gz -q -z follow,tcp,raw,23 | grep -E '^[0-9a-f]+$' \
  | python3 -c "import sys;sys.stdout.buffer.write(bytes.fromhex(''.join(l.strip() for l in sys.stdin)))" > cliente-smtp.bin
~~~

`grep -E '^[0-9a-f]+$'` se queda con las líneas hexadecimales **sin tab** (las del Node 0, el cliente); el `python3 -c` las convierte a bytes. Si el cliente fuera Node 1, filtrar las que empiezan con tab.

6. Plan B a mano: elegir ASCII, buscar `Content-Type: image/png`, copiar solo el bloque Base64 hasta el siguiente boundary a imagen.b64, y decodificar:

~~~bash
base64 --decode imagen.b64 > imagen.png
file imagen.png
xdg-open imagen.png
~~~

No incluir cabeceras MIME, separadores ni datos del servidor en imagen.b64.

### La trampa del disector

Verificado en el archivo:
- El cliente empieza a mandar contenido en el frame 1403; el banner 220 del servidor aparece recién en el 1419.
- El stream del cliente contiene **7844 LF y cero CRLF**.
- TShark marca contenido como “C: DATA fragment”; imf no produce frames.

Por eso la reconstrucción IMF automática falla en esta versión. El flujo TCP y los límites MIME permiten recuperar el contenido de todos modos. La falta de sincronización y las terminaciones LF son observables; no atribuir toda la causa exclusivamente a una de ellas sin comparar implementaciones del disector.

No concatenar tcp.payload paquete por paquete: puede incluir retransmisiones o datos fuera de orden. Follow TCP Stream ya realiza la reconstrucción.

**Frase:** “Aunque Wireshark no reconstruye IMF, seguí la dirección cliente del flujo TCP, separé DATA y decodifiqué la parte image/png para mostrar la imagen original.”

## B2. Variantes sobre el mismo correo, verificadas

El procedimiento es el de B1; cambiar el dato que se lee del sobre o de la parte MIME.

| Pregunta | Evidencia real / respuesta | Receta y frase para explicar |
| --- | --- | --- |
| Remitente y destinatario del sobre | MAIL FROM: foo@bar; RCPT TO: juan@localhost | Leer comandos antes de DATA. “El sobre determina entrega y retorno, no los nombres que muestra el mensaje.” |
| Remitente y destinatario visibles | From: A <a@a>; To: V <b@b> | Leer headers dentro de DATA. “El cliente muestra los headers, independientes del sobre.” |
| Asunto | feliz parcial | Leer Subject; el parser lo muestra. “El asunto está en la cabecera del mensaje.” |
| Estructura MIME | mixed → related → alternative (plain y HTML); related además contiene PNG; mixed además contiene el TXT | Revisar Content-Type y boundaries o las partes enumeradas por el script. “alternative ofrece formatos, related vincula imagen y HTML, mixed suma el adjunto.” |
| Cuerpo plain | Espero que te encuentres entretenido.; línea de emojis 😀😲 repetidos; [image: image.png] | Parte 3 decodificada, no el TXT adjunto. “Decodifiqué la parte text/plain del mensaje.” |
| ¿Con cuántos puntos se aprobaba? | El punto 10 del TXT dice CINCO (5) sobre DIEZ (10) | Abrir correo-extraido/6-lineamientos-parcial.txt. “La respuesta está en el adjunto decodificado, no en el cuerpo.” |
| Tamaño de imagen y presentación HTML | Original: 1200 × 628; HTML: width="542" height="284" | file para tamaño real; parte HTML para presentación. “Los atributos de HTML cambian visualización, no dimensiones del PNG.” |
| ¿Cómo se vincula la imagen al HTML? | src="cid:ii_ka5xvnoa0"; Content-ID: <ii_ka5xvnoa0> | Comparar ambos campos. “El CID referencia una parte relacionada del mensaje, no una URL de Internet.” |

Para mostrar el punto del adjunto:

~~~bash
grep -n -A 1 '^10\.' correo-extraido/6-lineamientos-parcial.txt
~~~

grep busca texto; -n agrega número de línea; -A 1 incluye la línea siguiente; ^ ancla al inicio y \. representa un punto literal. Salida del contenido:

~~~text
10. El parcial práctico se considerará aprobado con CINCO (5) puntos sobre un
    total de DIEZ (10) puntos.
~~~

---

## C. dhcp-parcial: negociación y preguntas

**Qué buscamos:** agrupar los cuatro mensajes por Transaction ID, luego leer cada opción en el mensaje que corresponde.

~~~bash
tshark -n -r dhcp-parcial.pcap.gz -Y dhcp -T fields -E header=y -e frame.number -e dhcp.option.dhcp -e dhcp.id -e dhcp.hw.mac_addr -e dhcp.ip.your -e dhcp.option.dhcp_server_id -e dhcp.option.ip_address_lease_time -e dhcp.option.router -e dhcp.option.domain_name_server -e dhcp.option.domain_name -e dhcp.option.hostname -e dhcp.option.requested_ip_address
~~~

dhcp filtra el protocolo. Los campos, en orden: número de frame; tipo de mensaje; ID de transacción; MAC del cliente; dirección ofrecida/asignada (yiaddr); identificador del servidor; lease en segundos; router; DNS; dominio; nombre del equipo; dirección solicitada.

Salida real, resumida por columnas para legibilidad:

| Frame | Tipo | ID | IP cliente yiaddr | Servidor ID | Lease | Router | DNS | Dominio | Hostname | IP pedida |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 Discover | 0xfe089c15 | 0.0.0.0 | — | — | — | — | — | academy04 | 10.20.20.20 |
| 2 | 2 Offer | 0xfe089c15 | 10.20.20.20 | 10.20.20.4 | 300 | — | 10.20.20.1 | far-far-away | — | — |
| 3 | 3 Request | 0xfe089c15 | 0.0.0.0 | 10.20.20.4 | — | — | — | — | academy04 | 10.20.20.20 |
| 4 | 5 ACK | 0xfe089c15 | 10.20.20.20 | 10.20.20.4 | 300 | — | 10.20.20.1 | far-far-away | — | — |

La MAC del cliente en los cuatro mensajes es **00:50:ba:12:47:cb**. Los guiones de esta tabla representan columnas vacías en TShark, no valores transmitidos.

**Wireshark, receta común:** filtro dhcp → elegir Discover/Offer/Request/ACK → expandir Dynamic Host Configuration Protocol → opciones. En versiones antiguas puede llamarse BOOTP; ver compatibilidad al final.

### C1. ¿MAC y nombre del cliente?

**Respuesta:** 00:50:ba:12:47:cb y academy04.

**Receta:** frame 1, Client MAC address y opción 12 Host Name; campos dhcp.hw.mac_addr y dhcp.option.hostname del comando anterior.

**Frase:** “Identifiqué al cliente por chaddr y la opción Host Name de su Discover.”

### C2. ¿IP del servidor DHCP?

**Respuesta:** 10.20.20.4.

**Receta:** frames 2/4, opción 54 Server Identifier. El campo dhcp.option.dhcp_server_id la muestra. En esta captura también coincide con la IP origen; en presencia de relay no siempre debe inferirse solo del origen IP.

**Frase:** “El servidor se identifica con la opción 54, que vale 10.20.20.4.”

### C3. ¿Duración del préstamo?

**Respuesta:** 300 segundos, 5 minutos.

**Receta:** frames 2/4, opción 51 IP Address Lease Time; dhcp.option.ip_address_lease_time. No confundir lease con los tiempos T1/T2 si aparecen.

**Frase:** “La opción 51 del Offer y del ACK fija un préstamo de 300 segundos.”

### C4. ¿Gateway informado?

**Respuesta:** no se informa un router en este intercambio.

**Receta:** comprobar opciones del Offer y ACK, no solo las solicitadas por el cliente. Para demostrar ausencia:

~~~bash
tshark -n -r dhcp-parcial.pcap.gz -Y dhcp -T fields -E header=y -e frame.number -e dhcp.option.type -e dhcp.option.request_list_item -e dhcp.option.router
~~~

dhcp.option.type enumera las opciones efectivamente presentes; dhcp.option.request_list_item enumera lo solicitado en la opción 55; dhcp.option.router sería la opción 3 entregada.

Evidencia real:
- Frame 1 pide, entre otros códigos: 1,15,**3**,6,...
- Frame 2 entrega: 53,54,51,1,15,6,0; no 3.
- Frame 4 entrega: 53,54,51,81,1,15,6,0; no 3.
- dhcp.option.router sale vacío.

No concluir que la red carece de gateway en general: solo que DHCP no lo comunica aquí.

**Frase:** “El cliente pidió Router, pero la opción 3 no aparece en Offer ni ACK; por tanto no se informó gateway.”

### C5. ¿Dominio y DNS?

**Respuesta:** dominio far-far-away, DNS 10.20.20.1.

**Receta:** opciones 15 y 6, respectivamente, en Offer/ACK. Dominio no es hostname ni dirección del servidor DHCP.

**Frase:** “Separé la opción Domain Name de la opción DNS y del identificador del servidor.”

### C6. ¿El cliente ya había tenido IP?

**Respuesta esperada:** recuerda o prefiere 10.20.20.20: la pide ya en su Discover, opción 50. Luego se ofrece y confirma esa IP.

**Precisión:** esto es un indicio de configuración previa, no prueba histórica absoluta de un lease anterior: un cliente también puede solicitar una IP por otra preferencia/configuración. Lo demostrado es que la solicitó antes del Offer.

**Receta:** frame 1, Requested IP Address y dhcp.option.requested_ip_address; comparar con yiaddr de frames 2/4.

**Frase:** “El Discover ya solicita 10.20.20.20, compatible con que el cliente recuerde una dirección previa.”

### C7. ¿El Offer es unicast o broadcast?

**Qué buscamos:** destinos efectivos de capa 2 y 3, además del flag del cliente:

~~~bash
tshark -n -r dhcp-parcial.pcap.gz -Y dhcp -T fields -E header=y -e frame.number -e ip.src -e ip.dst -e eth.dst -e dhcp.flags.bc
~~~

eth.dst es la MAC Ethernet destino; dhcp.flags.bc es el flag BROADCAST de DHCP, no el destino Ethernet.

Salida real:

~~~text
frame.number ip.src     ip.dst           eth.dst            dhcp.flags.bc
1            0.0.0.0    255.255.255.255  ff:ff:ff:ff:ff:ff  False
2            10.20.20.4 255.255.255.255  ff:ff:ff:ff:ff:ff  False
3            0.0.0.0    255.255.255.255  ff:ff:ff:ff:ff:ff  False
4            10.20.20.4 255.255.255.255  ff:ff:ff:ff:ff:ff  False
~~~

**Respuesta:** el Offer, frame 2, se envía por broadcast. Aunque el flag esté apagado, los destinos observados son broadcast. No decir que “siempre debe ser broadcast porque el cliente no tiene IP”: DHCP puede emplear unicast en determinadas condiciones.

**Wireshark:** abrir Ethernet II e IPv4 y comparar destinos; después revisar el flag DHCP. La MAC cliente dentro de DHCP identifica al destinatario lógico aunque el frame se difunda.

**Frase:** “Es broadcast porque los destinos Ethernet e IP son los de difusión, independientemente del flag DHCP observado.”

---

## D. Más preguntas de las páginas de práctica, verificadas

### D1. Telnet: sistema operativo, comandos y ping

**Receta:** flujo 0 de A3. El banner y los datos del servidor muestran:

~~~text
OpenBSD/i386 (oof) (ttyp1)
OpenBSD 2.6-beta (OOF)
PING www.yahoo.com (204.71.200.74): 56 data bytes
13 packets transmitted, 11 packets received, 15% packet loss
~~~

**Respuestas:** servidor OpenBSD 2.6-beta, host oof; comandos ls, ls -a, /sbin/ping www.yahoo.com y exit. El ping se interrumpe con Ctrl+C; destino 204.71.200.74, 15 % de pérdida según su estadística impresa. Telnet transmite credenciales en claro; SSH cifra la sesión.

**Wireshark:** Follow del flujo 0, solo cliente para comandos y solo servidor para banner/estadísticas.

**Frase:** “Reconstruí comandos y respuestas por dirección y leí la pérdida del resumen del ping, no la inferí contando paquetes de toda la captura.”

### D2. SMTP: recorrido, error y Received

**Receta:** flujos 26 y 27 de A4.

| Pregunta | Respuesta real |
| --- | --- |
| Primer destino y software | 192.168.122.158, Postfix; banner 220 juan-virtual-machine ESMTP Postfix |
| Error de protocolo | Después de MAIL FROM y RCPT TO el cliente envía MAIL otra vez; respuesta 503 5.5.1 Error: nested MAIL command |
| ¿Se abortó el correo? | No: DATA fue aceptado y se encoló como B114A631CC |
| Segundo destino | 64.233.190.27; banner mx.google.com |
| ¿Por qué ese servidor? | Compatible con entrega al MX de itba.edu.ar. El banner y destinatario están observados; comprobar DNS MX en la captura antes de afirmar que se vio la consulta concreta |
| Header agregado | Received, con origen 192.168.122.1, receptor juan-virtual-machine, Postfix, SMTP, ID B114A631CC, destinatario y fecha |
| Sobre versus From | En este correo coinciden: juan@leak.com.ar |

El cliente del primer tramo no manda HELO/EHLO antes de MAIL; Postfix igualmente acepta. El del segundo manda EHLO juan-virtual-machine. No extrapolar ese permiso a todos los servidores SMTP.

**Wireshark:** smtp, Follow de ambos flujos, buscar 503 y Received. Cada servidor agrega Received arriba; leer de abajo hacia arriba para reconstruir cronología.

**Frase:** “Relacioné ambos tramos por el mensaje y el ID de cola y distinguí la respuesta al comando inválido de la posterior aceptación del correo.”

### D3. HTTP: recurso, negociación, representación y ETag

**Qué buscamos:** pedidos y respuestas del mismo flujo; no mezclar el HTML principal con publicidad de otro host.

~~~bash
tshark -n -r botica.pcap.gz -Y http.request -T fields -E header=y -e frame.number -e ip.src -e http.host -e http.request.uri -e http.accept_language -e http.accept_encoding
tshark -n -r botica.pcap.gz -Y 'frame.number==310' -O http
~~~

http.request selecciona pedidos; http.host es Host; request.uri es ruta/query; accept_language y accept_encoding muestran negociación. -O http desarrolla HTTP y resume las otras capas.

**Resultados reales:**
- Frame 276: cliente 145.254.160.237, Host www.ethereal.com, GET /download.html.
- Accept-Language: en-us,en;q=0.5: preferencia por inglés estadounidense y luego inglés con peso 0,5.
- Accept-Encoding: gzip,deflate: acepta ambas codificaciones.
- Frame 310: 200 OK, Server Apache, Content-Length 18070, Content-Type text/html; charset=ISO-8859-1, sin Content-Encoding.
- ETag: "9a01a-4696-7e354b00".
- El frame 299 corresponde a otro recurso, de publicidad, y sí lleva gzip. No atribuirlo al HTML principal.

Para un GET condicional, si el mismo recurso mantuviera ese ETag:

~~~bash
curl -i -H 'If-None-Match: "9a01a-4696-7e354b00"' http://www.ethereal.com/download.html
~~~

-i muestra cabeceras; -H agrega If-None-Match; las comillas simples preservan las dobles del ETag. Si el servidor lo valida como vigente, responde 304 sin cuerpo. **No se ejecutó contra el sitio actual ni se garantiza hoy un 304 con un ETag de 2004.**

**Wireshark:** http.request, Follow TCP Stream para emparejar; en respuesta expandir HTTP. Se puede filtrar tcp.stream==N según el índice de esa conexión.

**Frase:** “Relacioné el pedido con su respuesta: el cliente aceptaba compresión, pero esta representación concreta llegó sin Content-Encoding.”

### D4. Otro traceroute y un Request RIP

**Receta:** RIP de A1. El frame 394 de 10.0.0.2 es comando Request, versión 1, Address Family 0 y métrica 16: pide tabla completa; no anuncia una ruta útil a 0.0.0.0. Sus Response anuncian 200.0.2.0 con métrica 1.

Para el otro traceroute:

~~~bash
tshark -n -r botica.pcap.gz -Y '!icmp && ip.src==192.168.0.11 && ip.dst==172.217.28.195 && udp' -T fields -e frame.number -e ip.ttl -e udp.dstport
tshark -n -r botica.pcap.gz -Y 'icmp && ip.dst==192.168.0.11' -T fields -E occurrence=f -e frame.number -e ip.src -e icmp.type -e icmp.code -e udp.dstport
~~~

**Respuesta real:** 9 saltos; sonda frame 1389, TTL 9, puerto 33458; ICMP frame 1402, origen 172.217.28.195, tipo 3 código 3, cita ese puerto. Primer router: 192.168.0.1, responde al TTL 1. Las sondas son UDP a puertos altos, no ICMP Echo Request. Los TTL 2–4 no obtienen respuestas visibles.

**Wireshark:** mismo cruce de A2 cambiando direcciones; el TTL citado dentro del error no reemplaza al original.

**Frase:** “Crucé el puerto 33458 con la sonda de TTL 9 y la respuesta final del destino.”

### D5. Fragmentación IPv4

**Qué buscamos:** todos los fragmentos, incluido el último, que tiene MF apagado.

~~~bash
tshark -n -r botica.pcap.gz -Y 'ip.flags.mf==1 || ip.frag_offset>0' -T fields -E header=y -e frame.number -e ip.src -e ip.dst -e ip.id -e ip.flags.mf -e ip.frag_offset
~~~

MF indica que siguen fragmentos; frag_offset indica desplazamiento en unidades de 8 bytes. || incluye ambos casos.

Salida real:

~~~text
frame.number ip.src     ip.dst        ip.id  ip.flags.mf ip.frag_offset
904          193.0.9.59 192.168.0.11  0xcf25 True        0
905          193.0.9.59 192.168.0.11  0xcf25 True        172
906          193.0.9.59 192.168.0.11  0xcf25 False       344
~~~

**Respuesta:** tres fragmentos del datagrama con ID 0xcf25 y mismos extremos/protocolo. Desplazamientos: 0, 1376 y 2752 bytes de payload original. No usar el ID solo como identificador global: se interpreta junto con extremos, protocolo y contexto temporal. La causa general es superar una MTU de salida; no afirmar que esa MTU es necesariamente 1500 sin medir el caso.

**Wireshark:** filtro anterior → IPv4 → Identification, Flags y Fragment Offset; revisar además reensamblado si está habilitado.

**Frase:** “Incluí el último fragmento mediante su offset y convertí los desplazamientos multiplicando por ocho.”

---

## Qué me preguntan → qué filtro o herramienta uso

| Pregunta | Filtro / herramienta | Qué mirar |
| --- | --- | --- |
| Qué protocolos hay | Statistics → Protocol Hierarchy; -z io,phs | Elegir el protocolo pertinente |
| Redes anunciadas | rip && rip.command==2 | Anunciante, versión, entrada y métrica |
| Solicitud de tabla RIP | rip && rip.command==1 | AFI, entrada especial, métrica 16 |
| Saltos de traceroute | UDP de ida sin ICMP + ICMP de vuelta | TTL original, puertos citados, tipo/código |
| Credenciales Telnet | telnet; Follow TCP Stream | Dirección cliente; negociación versus datos |
| Correo para un destinatario | smtp; tcp.port==25 | RCPT TO antes de DATA y To dentro |
| Texto visible del correo | imf o Follow TCP Stream | MIME, CTE, charset; no confundir adjunto y cuerpo |
| Extraer imagen | Export Objects si funciona; Follow + parser MIME | Cliente correcto, boundary y Base64 |
| IP/MAC cliente DHCP | dhcp | chaddr, hostname, yiaddr |
| Gateway informado | DHCP opción 3 en Offer/ACK | No confundir con Parameter Request List |
| DHCP broadcast | Ethernet/IP de Offer | Destinos observados y flag como dato separado |
| HTTP compresión | http.response | Content-Encoding, no solo Accept-Encoding |
| Revalidación de caché | HTTP ETag, If-None-Match | Código 304, sin cuerpo |
| Fragmentos | ip.flags.mf==1 || ip.frag_offset>0 | ID, extremos, offset × 8 |
| Tráfico TLS/SSH | tls / ssh | No esperar leer contenido cifrado sin material de descifrado |

## Si algo falla

| Síntoma | Causa posible | Arreglo |
| --- | --- | --- |
| tshark no existe | Herramienta no instalada en tu VM | Instalar tshark con el gestor de paquetes; los comandos de análisis no necesitan privilegios |
| No abre .gz | Soporte de compresión ausente o archivo dañado | gzip -t ARCHIVO; si hace falta gzip -dc ARCHIVO > copia.pcap, conservando el original |
| Campo inválido | Diferencia de versión | tshark -G fields y buscar el campo; usar -V como alternativa |
| dhcp no coincide | Versión antigua usa bootp | Probar filtro bootp y su prefijo de campos según -G fields |
| No aparece rip.netmask | RIPv1 no la transmite como RIPv2 | No inventar máscara; explicar la inferencia y los límites |
| Flujo N no corresponde | Se cambió archivo, filtro de exportación o versión | Volver a descubrir tcp.stream; no memorizar el número |
| Contraseña ilegible | Se mezcla eco, servidor y bytes IAC | Elegir solo cliente y ubicar el pedido Password |
| Muchos TTL o IP separados por comas | ICMP contiene otra cabecera IP | -E occurrence=f para cabecera externa y buscar la sonda original por puerto |
| Distancia de traceroute demasiado baja | Se contaron solo routers que respondieron | Cruzar con TTL de salida; routers silenciosos también consumen TTL |
| Sale 12 en lugar de 9 | Se tomó la primera respuesta final del archivo | Buscar el mínimo TTL asociado a respuestas del destino |
| imf vacío | El disector no reconstruyó el mensaje | Follow TCP Stream; extraer DATA y parsear MIME |
| Base64 da error o imagen inválida | Cabeceras, límites MIME o direcciones mezclados | Extraer solo la parte correcta; preferir parser MIME |
| Archivo extraído duplicado o corrupto | Concatenación de segmentos/retransmisiones | Usar el flujo reensamblado, no tcp.payload sin reconstrucción |
| Router DHCP vacío | Opción ausente, o se consultó solo Discover | Revisar Offer y ACK y opciones presentes |
| Deducción DHCP demasiado fuerte | Se toma Requested IP como prueba de un lease anterior | Describir lo observado y separar la inferencia |
| MIME muestra bytes raros | Charset o codificación de transferencia no aplicados | Decodificar CTE y después charset |
| Paquetes de muchos años | Captura de enseñanza combinada | Separar conversaciones y escenarios; no asumir una sola red |

gzip -t comprueba integridad; -d descomprime; -c escribe a stdout; > guarda una copia sin borrar el .gz. tshark -G fields lista campos del disector instalado.

## Variantes: qué cambia y qué línea tocar

- Otra captura: cambiar -r; volver a descubrir streams y números de frame.
- Otros extremos: cambiar ip.src/ip.dst; conservar la separación de cabeceras externas e internas.
- Traceroute ICMP: correlacionar identificador y secuencia de Echo Request/Reply; no habrá UDP dstport.
- Traceroute TCP: correlacionar sondas SYN con respuestas TCP/ICMP; no aplicar ciegamente Port Unreachable UDP.
- RIPv2: leer máscara y next hop transmitidos en cada entrada; no usar clase histórica.
- Otro mail: identificar nodo cliente, DATA, boundary, CTE y charset; el script admite nodo 0 o 1.
- Puerto de aplicación no estándar: revisar Conversations; Analyze → Decode As…, o -d tcp.port==PUERTO,smtp si procede. -d selecciona un disector para ese puerto, no corrige un diálogo mal formado.
- Imagen JPEG en lugar de PNG: el parser usa la parte y su nombre; confirmar contenido con file, no cambiar solamente la extensión.
- Correo cifrado con STARTTLS: reconstruir flujo no descifra TLS por sí solo.
- En otra versión de Wireshark, pueden cambiar nombres de menú, campos o heurísticas: verificar -V y -G fields.

## Script completo: extraer_correo.py

El archivo descargable es el mismo código de esta sección. Solo maneja los ejemplos SMTP con DATA; no implementa BDAT/CHUNKING ni sesiones con varios mensajes seleccionables. Para otra captura con múltiples DATA, adaptar la selección del mensaje. No ejecutar adjuntos; se guardan como datos.

~~~python
#!/usr/bin/env python3
"""Uso: python3 extraer_correo.py flujo-raw.txt carpeta-salida [0|1]"""
import re, sys
from pathlib import Path
from email import policy
from email.parser import BytesParser

source, output = Path(sys.argv[1]), Path(sys.argv[2])
node = int(sys.argv[3]) if len(sys.argv) > 3 else 0
if node not in (0, 1):
    raise SystemExit("El nodo debe ser 0 o 1")
lines = source.read_text().splitlines()
for line in lines:
    if line.startswith("Node "):
        print(line)
chunks = []
for line in lines:
    direction = 1 if line.startswith("\t") else 0
    value = line.strip()
    if direction == node and re.fullmatch(r"[0-9a-fA-F]+", value):
        chunks.append(bytes.fromhex(value))
raw = b"".join(chunks)
data = re.search(rb"(?im)^DATA[ \t]*\r?\n", raw)
if data is None:
    raise SystemExit("No encontré DATA: verificar nodo cliente y flujo")
message = re.split(rb"(?m)^\.\r?$", raw[data.end():], maxsplit=1)[0]
message = re.sub(rb"(?m)^\.\.", b".", message)
output.mkdir(parents=True, exist_ok=True)
(output / "mensaje.eml").write_bytes(message)
msg = BytesParser(policy=policy.default).parsebytes(message)
print("Subject:", msg["Subject"])
print("From:", msg["From"])
print("To:", msg["To"])
print("Bytes cliente:", len(raw), "| CRLF:", raw.count(b"\r\n"),
      "| LF:", raw.count(b"\n"))
for i, part in enumerate(msg.walk()):
    print(i, part.get_content_type(), part.get_filename(),
          "CTE:", part["Content-Transfer-Encoding"])
    if part.is_multipart():
        continue
    payload = part.get_payload(decode=True) or b""
    if part.get_content_maintype() == "text" and not part.get_filename():
        print(payload.decode(part.get_content_charset() or "utf-8",
                             errors="replace"))
    if part.get_filename():
        safe_name = Path(part.get_filename().replace("\\", "/")).name
        if safe_name in ("", ".", ".."):
            safe_name = "parte-" + str(i)
        target = output / (str(i) + "-" + safe_name)
        target.write_bytes(payload)
        print("Guardado:", target.name, "bytes:", len(payload))


~~~

## Integridad y alcance

SHA-256 de los .gz recibidos:

~~~text
botica.pcap.gz:
a3601ae6cdab191381b485dd158537b31dd682a11ea2cae951e78ae7d3770f78

parcial-correo.pcap.gz:
507322fde1b8bb389937de1a3697086d8b75ae51dda174afcd541b53d25bc5b5

dhcp-parcial.pcap.gz:
5694a90edc33d56cbbbb969189c3790ef233d0fcf44f6c5a1d2dfc0e554b114f
~~~

PNG extraído: 437326 bytes, SHA-256 8c0072cc4fe6029fb6749e4dee3c8a3ae5f68580373bceea5b18f8d1431114a1.

El análisis se ejecutó sobre copias adjuntas en el entorno de trabajo, no mediante acceso remoto a tu VM. Los comandos de la receta usan tu ubicación prevista ~/protos/pcaps. El script y documentos se entregan para descargar; copiarlos a ~/protos/soluciones si querés esa organización.

## Frase general para el video

“Filtré la conversación relevante, reconstruí los datos y mostré los campos concretos que sustentan la respuesta, distinguiendo lo observado de lo inferido.”

## Fuentes

- Capturas adjuntas: botica.pcap.gz, parcial-correo.pcap.gz y dhcp-parcial.pcap.gz.
- [Notion: análisis de capa 3](https://app.notion.com/p/4056494c8b478135852dd4757bb56666).
- [Notion: seguir flujos TCP](https://app.notion.com/p/4056494c8b47814aa370d7a57c75319e).
- [Notion: variantes sobre las tres capturas](https://app.notion.com/p/4056494c8b4781dd9647f39b52e8cbbd).
- [Manual oficial de TShark](https://www.wireshark.org/docs/man-pages/tshark.html).
- [Wireshark: seguimiento de flujos](https://www.wireshark.org/docs/wsug_html_chunked/ChAdvFollowStreamSection.html).

