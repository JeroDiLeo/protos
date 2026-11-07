# Cheatsheet: herramientas sueltas (codificar/decodificar, netcat, archivos, procesos)

Cheatsheets por tema: [curl](../curl/cheatsheet-curl.md) · [SSH](../ssh/cheatsheet-ssh.md) · [DNS](../dns/cheatsheet-dns.md) · [correo](../smtp/cheatsheet-correo.md) · [nginx](../nginx/cheatsheet-nginx.md) · [red y DHCP](../red/cheatsheet-red-dhcp.md). Búsqueda del tesoro: [../pistas/seguir-pistas-http-dns-ssh.md](../pistas/seguir-pistas-http-dns-ssh.md).

---

## 1. Base64

### Codificar y decodificar
| Quiero… | Comando | Resultado |
|---|---|---|
| codificar un texto | `echo -n 'hola' \| base64` | `aG9sYQ==` |
| decodificar | `echo 'aG9sYQ==' \| base64 -d` | `hola` |
| codificar sin `echo` | `printf '%s' 'hola' \| base64` | `aG9sYQ==` |
| decodificar sin pipe | `base64 -d <<< 'aG9sYQ=='` | `hola` |
| codificar un archivo | `base64 archivo.png > archivo.b64` | — |
| … en una sola línea | `base64 -w 0 archivo.png` | (sin saltos cada 76) |
| … con líneas de 76 (para mail) | `base64 -w 76 archivo.png` | — |
| decodificar a un archivo | `base64 -d archivo.b64 > archivo.png` | — |
| pegar un bloque largo y decodificar | `base64 -d`, Enter, pegar, Enter, **Ctrl+D** | — |
| ignorar basura (espacios, caracteres raros) | `base64 -d -i` | — |
| Python | `python3 -c "import base64;print(base64.b64decode('aG9sYQ==').decode())"` | `hola` |

### Las trampas
- **`echo` sin `-n` agrega un salto de línea** y queda codificado: `echo 'hola' | base64` → `aG9sYQo=` (el `o=` final es el `\n`). Para codificar usá `echo -n` o `printf '%s'`. Para **decodificar** da igual.
- **Base64 no cifra**: cualquiera lo decodifica. Basic auth, AUTH PLAIN de SMTP/POP3 y los encoded-words de mail son base64.
- **Le falta el `=` final** → `base64: invalid input` (igual imprime lo que pudo). Completar hasta múltiplo de 4:
  ~~~bash
  s='aG9sYQ'; echo "$s$(printf '=%.0s' $(seq 1 $(( (4 - ${#s} % 4) % 4 ))))" | base64 -d
  ~~~
- **Base64url** (usa `-` y `_` en vez de `+` y `/`, sin `=`; aparece en JWT y URLs): `echo 'xx-_' | tr '_-' '/+' | base64 -d`.
- Si al decodificar salen bytes raros (`�`), puede ser un **binario** (imagen, gzip): guardalo en archivo y mirá qué es con `file`.
- Si lo decodificado **vuelve a parecer base64**, decodificá otra vez (pistas en capas).
- `=` en el medio de la cadena no es base64 (puede ser `nombre=valor` o quoted-printable).

### ¿Es base64?
Solo `A-Z a-z 0-9 + /`, termina en nada, `=` o `==`, largo **múltiplo de 4**. Si termina en `==` casi seguro es base64.
Ejemplos que vas a ver: `YWRtaW46YWRtaW4=` (= `admin:admin`, Basic auth) · `dG9rZW49…` (= `token=…`) · `wqFIb2xh…` (= `¡Hola`, UTF-8) · `PGI+…` (= `<b>…`, HTML) · `iVBORw0KGgo…` (= una imagen **PNG**) · `/9j/…` (= **JPEG**) · `JVBERi0…` (= **PDF**) · `H4sI…` (= **gzip**) · `UEsDB…` (= **zip**) · `eyJ…` (= JSON `{"`, JWT).

### Base32
`echo -n hola | base32` → `NBXWYYI=` · `echo NBXWYYI= | base32 -d`. Solo mayúsculas `A-Z` y `2-7`, padding con `=`.

---

## 2. Otras codificaciones: reconocer y decodificar

| Cómo se ve | Qué es | Decodificar | Codificar |
|---|---|---|---|
| `686f6c61` (solo `0-9a-f`, largo par) | **hex** | `echo 686f6c61 \| xxd -r -p` · `python3 -c "print(bytes.fromhex('686f6c61').decode())"` | `echo -n hola \| xxd -p` · `echo -n hola \| od -An -tx1` |
| `\x68\x6f` | hex escapado | `printf '\x68\x6f\n'` | — |
| `68 6f 6c 61` | hex con espacios | `echo '68 6f 6c 61' \| xxd -r -p` | `echo -n hola \| xxd` |
| `0x686f6c61` | hex con prefijo | sacar `0x` y `xxd -r -p` | — |
| `01101000 01101111` | **binario** | `echo '01101000 01101111' \| python3 -c "import sys;print(''.join(chr(int(b,2)) for b in sys.stdin.read().split()))"` | `echo -n ho \| xxd -b` |
| `104 111 108 97` | **ASCII decimal** | `python3 -c "print(''.join(map(chr,[104,111,108,97])))"` | `echo -n hola \| od -An -tu1` |
| `150 157` (`0-7`) | **octal** | `printf '\150\157\n'` | `echo -n ho \| od -An -to1` |
| `hola%20mundo%C3%B1` | **URL encoding** | `python3 -c "import urllib.parse as u;print(u.unquote('hola%20mundo'))"` | `python3 -c "import urllib.parse as u;print(u.quote('hola mundo ñ'))"` |
| `hola+mundo` (en un form) | URL form (`+` = espacio) | `u.unquote_plus(...)` | `u.quote_plus(...)` |
| `=C2=A1Hola` | **quoted-printable** | `python3 -c "import quopri;print(quopri.decodestring('=C2=A1Hola').decode())"` | `python3 -c "import quopri;print(quopri.encodestring('¡Hola'.encode()).decode())"` |
| `=?UTF-8?B?wqFIb2xh?=` / `=?UTF-8?Q?…?=` | **encoded-word** (header de mail) | `python3 -c "from email.header import decode_header as d;b,c=d('=?UTF-8?B?wqFIb2xh?=')[0];print(b.decode(c))"` | `python3 -c "from email.header import Header;print(Header('¡Hola','utf-8').encode())"` |
| `&lt;b&gt;` `&#241;` | **entidades HTML** | `python3 -c "import html;print(html.unescape('&lt;b&gt;'))"` | `html.escape('<b>')` |
| `\u00f1` | escape Unicode (JSON) | `python3 -c 'import json;print(json.loads("\"\\u00f1\""))'` · `echo '"\u00f1"' \| jq -r .` | — |
| `gbxra` (letras "corridas") | **ROT13** | `echo gbxra \| tr 'A-Za-z' 'N-ZA-Mn-za-m'` | lo mismo |
| letras corridas N lugares | **César** | probar los 25: `for n in $(seq 1 25); do echo "$n: $(python3 -c "import sys;n=$n;print(''.join(chr((ord(c)-97-n)%26+97) if c.islower() else c for c in 'texto'))")"; done` | — |
| `.... --- .-.. .-` | **Morse** | a mano / tabla | — |
| `eyJhbGc….eyJ….firma` | **JWT** (3 partes base64url con puntos) | `echo 'parte2' \| tr '_-' '/+' \| base64 -d` (el payload) | — |
| `H4sI…` en base64, o archivo `gzip compressed` | **gzip** | `echo 'H4sI…' \| base64 -d \| gunzip` · `gunzip -c archivo.gz` | `echo -n hola \| gzip \| base64` |
| `x\x9c…` / `eJ…` en base64 | **zlib** | `python3 -c "import zlib,base64,sys;print(zlib.decompress(base64.b64decode(sys.argv[1])).decode())" 'eJ…'` | — |
| 32 hex | **MD5** (hash, **no se decodifica**) | se compara: `echo -n x \| md5sum` | `md5sum archivo` |
| 40 / 64 hex | **SHA1 / SHA256** (hash) | se compara: `sha256sum` | `sha256sum archivo` |
| `$6$…` / `$apr1$…` / `$2y$…` | hash de contraseña (shadow/htpasswd) | no se decodifica | `openssl passwd -6 clave` / `-apr1` |
| `-----BEGIN …-----` | PEM (clave/certificado: base64 adentro) | `openssl x509 -in c.pem -text -noout` · `ssh-keygen -y -f clave` | — |

**Identificar un archivo**: `file archivo` (dice "PNG image", "gzip compressed", "ASCII text", "OpenSSH private key"…). Ver los primeros bytes: `xxd archivo | head` · `head -c 16 archivo | od -c`. Texto escondido en un binario: `strings archivo | less`.

Sin `xxd` (viene con `vim`): `sudo apt install xxd`, o usar `od` / Python.

---

## 3. Netcat (`nc`)

| Uso | Comando |
|---|---|
| conectarse a un puerto TCP (cliente) | `nc host 25` |
| … con CR+LF (SMTP, POP3, HTTP a mano) | `nc -C host 25` |
| … y cerrar al terminar la entrada | `nc -N host 80` (o `-q 1`) |
| UDP | `nc -u host 53` |
| ¿está abierto el puerto? | `nc -zv host 22` |
| escanear un rango | `nc -zv host 20-100` (`2>&1 \| grep succeeded`) |
| timeout | `nc -w 3 host 80` |
| escuchar en un puerto (servidor) | `nc -l 9000` (en openbsd; en el viejo: `nc -l -p 9000`) |
| escuchar solo en loopback | `nc -l 127.0.0.1 9000` |
| seguir escuchando después de cada cliente | `nc -lk 9000` |
| mandar un archivo | receptor: `nc -l 9000 > recibido.txt` · emisor: `nc host 9000 < archivo.txt` |
| mandar la salida de un comando | `tail -F log \| nc -l 127.0.0.1 9000` (y del otro lado `nc 127.0.0.1 9000`) |
| HTTP a mano | `printf 'GET / HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n' \| nc host 80` |
| servidor HTTP mínimo | `printf 'HTTP/1.1 200 OK\r\nContent-Length: 5\r\n\r\nhola\n' \| nc -l 8080` |
| chat entre dos | `nc -l 9000` / `nc host 9000` |

- Hay dos `nc`: **netcat-openbsd** (Ubuntu, tiene `-C`, `-N`, `-k`) y netcat-traditional. `nc -h` dice cuál es.
- **El que escucha tiene que arrancar primero.** Si el cliente conecta antes, sale enseguida sin nada.
- `nc -l` sin IP escucha en todas las interfaces.
- Alternativas: `telnet host 25` (ya manda CRLF), `ncat` (de nmap, tiene `--ssl`), `socat`, `openssl s_client` (TLS).

### TLS a mano
~~~bash
openssl s_client -connect host:443 -servername host -crlf     # HTTPS
openssl s_client -starttls smtp -connect host:587 -crlf        # SMTP con STARTTLS
openssl s_client -connect host:995 -crlf                       # POP3S
openssl s_client -connect host:443 </dev/null 2>/dev/null | openssl x509 -noout -subject -dates   # ver certificado
~~~

---

## 4. Puertos y procesos

| Comando | Para qué |
|---|---|
| `ss -tlnp` | puertos TCP **escuchando** y qué proceso (`sudo` para ver todos) |
| `ss -ulnp` | idem UDP |
| `ss -tnp` | conexiones establecidas |
| `sudo lsof -i :80` | quién usa el puerto 80 |
| `sudo fuser -k 8080/tcp` | matar lo que use el 8080 |
| `ps aux \| grep nginx` | procesos |
| `pgrep -a python3` | procesos por nombre |
| `kill PID` / `kill -9 PID` / `pkill -f patron` | terminar |
| `comando &` / `jobs` / `fg` | segundo plano |
| `nohup comando > log 2>&1 &` | que siga aunque cierres la terminal |
| `Ctrl+C` / `Ctrl+Z` / `Ctrl+D` | cortar / pausar / fin de entrada |
| `systemctl status X` / `start` / `stop` / `restart` / `reload` / `enable` | servicios |
| `journalctl -u X -e` / `-f` | logs de un servicio |
| `tail -f /var/log/syslog` | log en vivo |
| `watch -n 1 'ss -tn'` | repetir un comando cada segundo |

Puertos conocidos: 20/21 FTP · **22 SSH** · 23 Telnet · **25 SMTP** · **53 DNS** · **67/68 DHCP** · **80 HTTP** · **110 POP3** · 123 NTP · 143 IMAP · 161 SNMP · **443 HTTPS** · 465 SMTPS · **587 submission** · 993 IMAPS · 995 POP3S · **1080 SOCKS** · 3128 proxy · 3306 MySQL · 5432 Postgres · 8080 HTTP alt · 9050 Tor.

---

## 5. Descargar, mover y comprimir archivos

| Quiero… | Comando |
|---|---|
| bajar con curl | `curl -O http://h/archivo` (mismo nombre) · `curl -o nombre http://h/x` |
| bajar siguiendo redirecciones | `curl -LO URL` |
| bajar con wget | `wget URL` · `wget -O nombre URL` |
| subir/bajar por SSH | `scp archivo user@h:/ruta/` · `scp user@h:/ruta/archivo .` |
| servir una carpeta por HTTP | `python3 -m http.server 8000` (en esa carpeta) |
| comprimir / descomprimir tar.gz | `tar czf x.tar.gz carpeta/` · `tar xzf x.tar.gz` |
| ver qué tiene un tar | `tar tzf x.tar.gz` |
| gzip | `gzip archivo` · `gunzip archivo.gz` · `zcat archivo.gz` · `gunzip -c x.gz > x` |
| zip | `zip -r x.zip carpeta` · `unzip x.zip` · `unzip -l x.zip` |
| captura `.pcap.gz` | tshark la lee directo, o `gunzip -k cap.pcap.gz` |
| verificar integridad | `sha256sum archivo` y comparar |
| comparar dos archivos | `diff a b` · `cmp a b` |
| comparar dos salidas | `diff <(cmd1) <(cmd2)` |

---

## 6. Procesar texto

| Quiero… | Comando |
|---|---|
| buscar | `grep -i palabra archivo` · `grep -r palabra carpeta/` · `grep -n` (con línea) · `grep -v` (las que no) |
| con contexto | `grep -A3 -B3 palabra` |
| solo lo que coincide | `grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+'` (IPs) |
| columna N | `awk '{print $2}'` · `cut -d: -f1 /etc/passwd` |
| reemplazar | `sed 's/viejo/nuevo/g'` · en el archivo: `sed -i 's/…/…/' archivo` |
| sacar caracteres | `tr -d '"'` (comillas) · `tr -d '\r'` (CR de Windows) · `tr -d ' \n'` |
| mayúsculas/minúsculas | `tr 'a-z' 'A-Z'` |
| contar / únicos | `sort \| uniq -c \| sort -rn` · `wc -l` |
| primeras / últimas líneas | `head -n 20` · `tail -n 20` · `tail -f` (en vivo) · `tail -F` (aunque roten el archivo) |
| JSON | `jq .` (lindo) · `jq -r .token` (un campo) · sin jq: `python3 -m json.tool` |
| línea N | `sed -n '5p' archivo` |
| juntar líneas | `tr -d '\n'` · `paste -sd,` |
| guardar y ver a la vez | `comando \| tee salida.txt` |
| todo stdout+stderr a archivo | `comando > log 2>&1` |

---

## 7. Permisos y usuarios

| Comando | Para qué |
|---|---|
| `ls -l` | ver permisos (`-rw-r--r--` = 644) |
| `chmod 600 archivo` | solo el dueño lee/escribe (claves privadas) |
| `chmod 644` / `755` / `700` | archivo público / ejecutable o carpeta / carpeta privada |
| `chmod +x script.sh` | hacerlo ejecutable |
| `chown usuario:grupo archivo` | cambiar dueño |
| `sudo -i` / `sudo comando` | root |
| `whoami` / `id` / `hostname` | quién soy, dónde estoy (para el video) |
| `echo "x" \| sudo tee -a /etc/hosts` | escribir en un archivo de root (`sudo echo x >> f` **no** funciona) |

Permisos: r=4, w=2, x=1, para dueño / grupo / otros. `644` = rw- r-- r--.

---

## 8. El enunciado (o la pista) dice → qué usar

| Ves / te dicen… | Usás |
|---|---|
| texto que termina en `=`/`==` | `base64 -d` |
| "codifique en base64" | `echo -n 'x' \| base64` (con `-n`) |
| solo `0-9a-f` | `xxd -r -p` |
| `%XX` | `urllib.parse.unquote` |
| `=XX` en un mail | quoted-printable (`quopri`) |
| `=?UTF-8?…?=` | encoded-word (`email.header`) |
| letras que no forman palabras pero mantienen espacios | ROT13 / César |
| `0` y `1` en grupos de 8 | binario |
| un archivo raro | `file`, `strings`, `xxd \| head` |
| "conéctese al puerto N y …" | `nc host N` (o `-C` si es SMTP/POP3) |
| "un servicio escucha en N" | `nc -zv host N`, `ss -tlnp` (si es local) |
| "pase el archivo a la otra máquina" | `scp`, o `nc -l` + `nc <` |
| "publique la salida de X en el puerto N" | `X \| nc -l 127.0.0.1 N` |
| "verifique que no cambió" | `sha256sum` |
| "qué proceso usa el puerto" | `ss -tlnp` / `lsof -i :N` |
| un TXT con comillas | `tr -d '"'` |
| texto copiado de Windows con `^M` | `tr -d '\r'` o `dos2unix` |

---

## 9. Qué decir en el video
«La pista estaba en base64 (termina en `=` y el largo es múltiplo de 4), la decodifiqué con `base64 -d`; para codificar uso `echo -n` para no meter el salto de línea. Base64 no es cifrado: cualquiera lo revierte.»
