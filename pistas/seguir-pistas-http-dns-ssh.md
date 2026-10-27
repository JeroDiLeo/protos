# Ejercicios de "búsqueda del tesoro": seguir pistas con curl, dig, nc y ssh

Ejercicios donde **cada respuesta te dice qué hacer después**: el servidor te pide un header, después otra cosa, después otra, hasta llegar al final (un mensaje, un flag, una shell). Ya cayeron en los parciales:

| Parcial | Cadena de pistas | Receta |
|---|---|---|
| 1C 2026 Ej 3 | 302 → `/debugger` → header `X-legajo` → idioma → POST → JSON → usuario | `curl/socks5h-acumulativo_1c2026.md` |
| 2C 2021 / 2020 | MAC de un host (o IP de un pcap de DHCP) → passphrase → llave .pem → shell | `ssh/pem-passphrase-mac_2c2021.md`, `pcap/pcap.md` (C) |
| 2C 2025 Ej II | Ruta al gateway → `nmap` encuentra el servidor → servicios → HTTP | `red/gateway-ruta-estatica-nmap_2c2025.md` |

**Todo lo de este archivo se probó** contra un servidor de pistas armado a propósito (HTTP de 11 pasos, DNS con pistas escondidas y un servicio TCP). Las salidas son reales.

---

## ⭐ Método (leer primero)

1. **Mirá la respuesta completa, no solo el cuerpo.** `curl -i` (o `-v`) muestra el código, los headers (`Location`, `Set-Cookie`, `WWW-Authenticate`, `Allow`, headers raros `X-...`) y el cuerpo. La pista puede estar en cualquiera.
2. **Cambiá una sola cosa por vez** y volvé a mandar. Así sabés qué arregló cada paso, y es lo que hay que contar en el video.
3. **Acumulá:** cada opción nueva se **suma** al comando anterior. No la reemplaza.
4. **Si algo parece basura, decodificalo:** base64, hex, URL encoding (tabla de abajo).
5. **Anotá cada comando en un archivo** (`nano pasos.txt`). El video tiene que mostrar el recorrido completo, no solo el final.

---

## 1. HTTP: qué te pide el servidor → qué agregar a curl

| La respuesta dice… | Significa | Agregar |
|---|---|---|
| `301` / `302` + `Location: /otra` | Andá a otra URL | `-L`, o pedir la URL de `Location` directamente |
| `302` después de un **POST** | Redirección que con `-L` se vuelve GET | `-L --post302` (o `--post301`), o pedir la nueva URL a mano con el POST |
| `400` "falta el header X" | Header obligatorio | `-H 'X: valor'` |
| `403` "solo navegadores" | Mira el User-Agent | `-A 'Mozilla/5.0'` |
| `406` / respuesta en otro idioma | Negociación de idioma | `-H 'Accept-Language: es'` |
| `406` / te da HTML y querés texto | Negociación de tipo | `-H 'Accept: text/plain'` (o `application/json`) |
| "falta el parámetro X" | Query string | `'URL?x=valor'` (con comillas, por el `?` y el `&`) |
| `405` + `Allow: POST` | Método equivocado | `-X POST` (o PUT, DELETE…) |
| `415` / "quiero JSON" | Tipo del cuerpo | `-H 'Content-Type: application/json' -d '{"k":"v"}'` |
| Formulario | Datos de formulario | `-d 'usuario=x&clave=y'` (`-d` ya implica POST) |
| `401` + `WWW-Authenticate: Basic` | Usuario y contraseña | `-u usuario:clave` |
| `401` + `Bearer` | Token | `-H 'Authorization: Bearer TOKEN'` |
| `Set-Cookie: sesion=...` | Hay que devolver la cookie | `-b 'sesion=...'`, o `-c jar.txt -b jar.txt` para que curl las maneje |
| "solo desde la página X" | Referer | `-e 'http://pagina-x/'` |
| No conecta / timeout | Proxy o ruta | `-x socks5h://proxy:puerto` (ver la receta del 1C 2026) |
| Cuerpo ilegible | Viene comprimido | `--compressed` |

**La cadena probada (cada línea suma algo a la anterior):**
~~~text
curl -i URL/                              → 302 Location: /paso1
curl -L URL/                              → "Solo navegadores (Mozilla)"            (403)
  + -A Mozilla/5.0                        → "Falta el header X-Legajo"              (400)
  + -H 'X-Legajo: 63051'                  → "Only Spanish speakers"                 (406)
  + -H 'Accept-Language: es'              → 400 "Falta el parametro token" + header X-Pista: dG9rZW49YWJj
       echo 'dG9rZW49YWJj' | base64 -d    → token=abc
  URL "…/paso1?token=abc"                 → 405 Allow: POST
  + -X POST                               → "Quiero JSON"                           (415)
  + -H 'Content-Type: application/json' -d '{"clave":"x"}'   → "Pista en hex: 7465736f726f"
       (hex → "tesoro")  -d '{"clave":"tesoro"}'              → 401 WWW-Authenticate: Basic
  + -u admin:admin                        → 302 Set-Cookie: sesion=ok
  + -b 'sesion=ok'                        → FLAG{encontraste_el_tesoro}
~~~

**Trampa verificada:** con `-L -c jar.txt -b jar.txt` (sin `--post302`), al seguir el último 302 curl **cambió el POST por GET** y el servidor respondió `Metodo no permitido`. Con `-L --post302` llegó al flag. Pasa lo mismo con 301 (`--post301`). Con 303 siempre se cambia a GET, como manda el estándar.

**Comando final, todo junto:**
~~~bash
curl -L --post302 -c jar.txt -b jar.txt -A 'Mozilla/5.0' \
  -H 'X-Legajo: 63051' -H 'Accept-Language: es' \
  -H 'Content-Type: application/json' -d '{"clave":"tesoro"}' \
  -u admin:admin 'http://servidor/paso1?token=abc'
~~~

### Ver lo que mandás y lo que recibís
~~~bash
curl -v URL                 # > lo que manda curl,  < lo que responde el servidor
curl -s -D - -o /dev/null URL   # solo los headers de la respuesta
curl -I URL                 # HEAD (algunos servidores responden distinto que a GET)
~~~

---

## 2. Decodificar pistas

| Se ve así | Es | Comando |
|---|---|---|
| `dG9rZW49YWJj`, termina en `=` o `==`, letras/números/`+/` | base64 | `echo 'TEXTO' \| base64 -d` |
| Igual pero con `-` y `_` | base64url | `echo 'TEXTO' \| tr '_-' '/+' \| base64 -d` |
| `7465736f726f` (solo 0-9 a-f, largo par) | hexadecimal | `echo 7465736f726f \| python3 -c "import sys;print(bytes.fromhex(sys.stdin.read().strip()).decode())"` |
| `%C2%A1Hola%20mundo` | URL encoding | `python3 -c "import urllib.parse,sys;print(urllib.parse.unquote(sys.argv[1]))" '%C2%A1Hola'` |
| `=C2=A1Hola` | quoted-printable | `python3 -c "import quopri,sys;print(quopri.decodestring(sys.argv[1]).decode())" '=C2=A1Hola'` |
| `Ubyn zhaqb` (letras corridas) | ROT13 | `echo 'Ubyn zhaqb' \| tr 'A-Za-z' 'N-ZA-Mn-za-m'` |
| Binario raro, empieza con `\x1f\x8b` | gzip | `base64 -d \| gunzip` (si venía en base64) |
| `=?UTF-8?B?...?=` | encoded-word (mail) | decodificar el base64 del medio |
| `01001000 01101111` | binario | `python3 -c "print(''.join(chr(int(b,2)) for b in '01001000 01101111'.split()))"` |

Si no sabés qué es: `echo 'TEXTO' | base64 -d | file -` dice qué tipo de dato sale.

---

## 3. DNS: pistas escondidas en registros

| Pista | Comando | Ejemplo probado |
|---|---|---|
| Texto en un TXT | `dig NOMBRE TXT +short` | `"pista=ZWwgc2Vydmlj..."` → decodificado: `el servicio esta en el SRV _tesoro._tcp` |
| Puerto de un servicio | `dig _servicio._tcp.DOMINIO SRV +short` | `0 0 9099 destino.tesoro.test.` → prioridad, peso, **puerto**, host |
| Cadena de alias | `dig NOMBRE A +short` | `paso2.tesoro.test.` → `destino.tesoro.test.` → `127.0.0.1` (la IP es la última línea) |
| Nombre a partir de una IP | `dig -x IP +short` | PTR |
| Quién es la autoridad | `dig DOMINIO NS +short` y después `dig @ESE_NS ...` | |
| **Todos** los nombres de la zona | `dig @NS_AUTORITATIVO DOMINIO AXFR` | Apareció `oculto-x7.tesoro.test. TXT "la palabra clave es HOLA"` |

- **`dig ANY` no alcanza:** en la prueba devolvió solo los registros de la raíz (3 líneas) y **no** el nombre escondido. Para ver todos los nombres hace falta la transferencia de zona (`AXFR`), y solo anda si el servidor la permite (`allow-transfer`). Si responde `Transfer failed`, no está permitida.
- **`AXFR` hay que pedírselo al servidor autoritativo** (el de `dig NS`), no al resolver de tu red.
- Para extraer el valor de un TXT y decodificarlo en un paso:
  ~~~bash
  dig DOMINIO TXT +short | tr -d '"' | sed 's/^pista=//' | base64 -d
  ~~~
- Para preguntar a un DNS en otro puerto: `dig @IP -p PUERTO ...`.

---

## 4. nc: servicios TCP que hablan texto

~~~bash
nc HOST PUERTO              # conectar y leer el banner
nc -C HOST PUERTO           # -C: manda CRLF al final de cada línea (SMTP, POP3, HTTP y la mayoría de protocolos)
nc -v -z HOST 20-100        # qué puertos están abiertos (escaneo rápido)
~~~
**Probado:** el servicio respondió `500 Use CRLF` con `nc` a secas, y `250 FLAG{dns_y_nc}` con `nc -C`. Si un servicio de texto no te entiende, **probá `-C` primero**.

- Leé el **banner**, la primera línea que manda el servidor: suele decir qué espera.
- Los códigos tipo SMTP: `2xx` OK, `3xx` seguí, `4xx`/`5xx` error.
- HTTP a mano: `printf 'GET / HTTP/1.1\r\nHost: x\r\n\r\n' | nc HOST 80`.

---

## 5. Encontrar dónde está el próximo paso (puertos y hosts)

~~~bash
nmap -sV -p- HOST              # todos los puertos y qué servicio hay (lento pero completo)
nmap -sV --top-ports 100 HOST  # rápido
nmap -sn 10.0.0.0/24           # qué hosts hay en una red (ver la receta del gateway)
curl -i http://HOST:PUERTO/    # si el puerto es HTTP
nc HOST PUERTO                 # si no: mirar el banner
~~~
`-sV` dice qué servicio es de verdad. Sin `-sV` nmap solo adivina por el número de puerto, y en la prueba del 2C 2025 nombró mal el 2222.

---

## 6. SSH: pistas para entrar

| Pista | Qué hacer |
|---|---|
| "llave en `http://.../llave.pem`" | `curl -O URL` → `chmod 600 llave.pem` → `ssh -i llave.pem -p PUERTO usuario@host` |
| "la passphrase es la MAC de X" | `ping -c1 X` y después `ip neigh` (o `arp -n`); minúsculas con `:` |
| "la passphrase es la IP que asignó el DHCP" | pcap → ACK → `yiaddr` (`pcap/pcap.md`, C) |
| Servidor SSH en un puerto raro | `nmap -sV -p- host` para encontrarlo; `ssh -p PUERTO` |
| Verificar la passphrase sin conectarse | `ssh-keygen -y -f llave.pem -P 'PASSPHRASE'` (si imprime la clave pública, es correcta) |
| Ya adentro: buscar el tesoro | `ls -la ~`, `cat ~/*.txt`, `find / -name '*flag*' 2>/dev/null`, `env`, `history` |

---

## Si algo falla

| Ves | Causa | Arreglo |
|---|---|---|
| Después de un POST + `-L` aparece "método no permitido" | `-L` cambió POST por GET | `--post302` / `--post301` |
| `-d` manda algo raro | `-d` es formulario por defecto | Agregar `-H 'Content-Type: application/json'` si es JSON |
| `Could not resolve host` | El nombre no resuelve en tu red | ¿Hay proxy? `-x socks5h://...`; o `dig` para ver qué pasa |
| La cookie no se reenvía | Sin `-b` | `-c jar.txt -b jar.txt` |
| Base64 da `invalid input` | Copiaste comillas, espacios o es base64url | `tr -d '" '`; probar con `tr '_-' '/+'` |
| `dig AXFR` → `Transfer failed` | El servidor no permite transferencias | Seguir con TXT, SRV, CNAME o nombres que te den las pistas |
| `nc` no recibe respuesta | Falta CRLF o el servidor espera otra cosa | `nc -C`; leer bien el banner |
| El `?` o el `&` de la URL hacen cosas raras | Los interpreta la shell | URL entre comillas simples |

## Para el video
"Seguí la cadena leyendo cada respuesta completa con `curl -i`. En cada paso el servidor me indicaba qué faltaba (código de estado y headers) y fui agregando la opción correspondiente, sin sacar las anteriores. Las pistas codificadas las decodifiqué con `base64 -d`. El último 302 venía después de un POST, así que usé `--post302` para que curl no lo convirtiera en GET."
