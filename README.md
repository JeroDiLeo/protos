# Protos · índice de todo el repo

Recetas, cheatsheets, ejercicios resueltos y labos para el parcial práctico de Protocolos de Comunicación (72.07, ITBA).

**Cómo usarlo en el parcial:** subrayá en la consigna los sustantivos técnicos ("negrita", "SOCKS", "MX", "túnel", "captura", "Host", "DHCP"…) y buscalos acá con Ctrl+F. Las **tablas por tema** te dicen qué pide cada archivo, las palabras clave y los comandos que lo resuelven.

Desde la terminal: `grep -ril "palabra" .` · índice plano con referencias a Notion: `grep -i "palabra" indice-protos.txt`.

**Tipos de archivo:** **Receta** = enunciado textual de un parcial real + receta para el parcial + práctica + variantes · **Resuelto** = paso a paso hecho en uno de los labos de `labosPropios/` · **Cheatsheet** = referencia de comandos por tema.

**Abreviaturas de labos** (`labosPropios/`): **LP26** = LabParcial-Rec20261c · **LR26** = LabPracticaRecu20262C · **LP25** = LabProtos2025-2C · **SIM** = SimilParcial20262c · **COR** = lab-correo · **SSH** = lab-ssh.

---

## Contenido

1. [Mapa del repo](#mapa-del-repo)
2. [Cheatsheets](#cheatsheets)
3. [DNS y BIND](#dns-y-bind)
4. [nginx y proxy HTTP](#nginx-y-proxy-http)
5. [curl, SOCKS y búsqueda de pistas](#curl-socks-y-búsqueda-de-pistas)
6. [Correo: SMTP, POP3, IMAP y MIME](#correo-smtp-pop3-imap-y-mime)
7. [SSH: claves, passphrase y túneles](#ssh-claves-passphrase-y-túneles)
8. [Red, DHCP y VirtualBox](#red-dhcp-y-virtualbox)
9. [Capturas (pcap) y Wireshark](#capturas-pcap-y-wireshark)
10. [Integrador](#integrador)
11. [Labos para practicar](#labos-para-practicar)
12. [Por parcial](#por-parcial)

---

## Mapa del repo

| Carpeta / archivo | Qué hay |
|---|---|
| [`dns/`](dns/) | Recetas de zonas BIND (crear, corregir, MX/SPF), trampas y registros extra (PTR, SRV, comodín) + cheatsheet |
| [`nginx/`](nginx/) | Recetas de proxy inverso (headers, URL sin cambiar, gzip) + todas las variantes + cheatsheet |
| [`curl/`](curl/) | curl acumulativo por SOCKS5, tres ejercicios paso a paso + cheatsheet |
| [`smtp/`](smtp/) | SMTP a mano + POP3, base64, multipart/negrita, variantes MIME, misión de la cátedra + cheatsheet |
| [`ssh/`](ssh/) | Túnel + tail, clave pública, .pem con passphrase (MAC), host sin NAT (-R/-D) + cheatsheet |
| [`red/`](red/) | Servidor DHCP, gateway + ruta estática + nmap, VirtualBox NAT/Bridge + cheatsheet |
| [`pcap/`](pcap/) | Análisis de capturas de parcial (botica, parcial-correo, dhcp-parcial) |
| [`pistas/`](pistas/) | Método para ejercicios de "búsqueda del tesoro" (HTTP, DNS, nc, SSH) |
| [`Protolab/`](Protolab/) | Integrador "The Vault" (PDF) y zona carlitos.com.ar (repaso) |
| [`labosPropios/`](labosPropios/) | 6 laboratorios Docker/locales con consignas, corrector y 37 ejercicios resueltos en `*/Resueltos/` |
| [`cheatsheet-herramientas.md`](cheatsheet-herramientas.md) | base64 y otras codificaciones, netcat, puertos, descargar/comprimir, permisos |
| [`indice-protos.txt`](indice-protos.txt) | Índice plano para `grep`, con referencias a la guía práctica (E1…E70) y a Notion |

---

## Cheatsheets

| Archivo | Para qué | Palabras clave |
|---|---|---|
| [dns/cheatsheet-dns.md](dns/cheatsheet-dns.md) | dig, tipos de registro, leer la salida, SPF, zona BIND, DNS en pcap | `dig @IP nombre TIPO +short/+noall +answer/+norecurse/+trace`, status/flags (`aa`), AXFR, `-x` |
| [nginx/cheatsheet-nginx.md](nginx/cheatsheet-nginx.md) | Procedimiento, anatomía de un sitio, directivas, errores de `nginx -t`, qué ves con curl | sites-available/enabled, server_name, listen, location, proxy_pass (barra final), proxy_set_header, 502/404 |
| [curl/cheatsheet-curl.md](curl/cheatsheet-curl.md) | curl acumulativo: qué agregar según el enunciado o la respuesta, códigos HTTP, errores de curl | `-i -v -L -x -H -X -d -u -A -b -c --resolve`, 302/400/401/403/406, headers de pista |
| [smtp/cheatsheet-correo.md](smtp/cheatsheet-correo.md) | SMTP/POP3, headers, base64/QP, encoded-word, HTML, multipart, dot-stuffing, plantilla | EHLO, AUTH PLAIN/LOGIN, `=?UTF-8?B?…?=`, alternative/mixed/related, `curl smtp://` / `pop3://` |
| [ssh/cheatsheet-ssh.md](ssh/cheatsheet-ssh.md) | Claves, passphrase, permisos, túneles -L/-R/-D/-J, errores, `~/.ssh/config`, sshd | `ssh-keygen`, `ssh-copy-id`, `-i -p -o IdentitiesOnly=yes`, Permission denied, UNPROTECTED PRIVATE KEY |
| [red/cheatsheet-red-dhcp.md](red/cheatsheet-red-dhcp.md) | IP/MAC/rutas, MAC de una IP, netplan, traceroute, nmap, subredes, DHCP, VirtualBox | `ip -br addr`, `ip route add`, `ip neigh`, `nmap -sn/-sV`, dhcpd.conf |
| [cheatsheet-herramientas.md](cheatsheet-herramientas.md) | Codificaciones, netcat, puertos y procesos, descargar/comprimir, texto, permisos | `base64 -d`, `xxd`, `nc -C/-l/-z`, `ss -tlnp`, `wget/scp/tar`, `chmod 600` |

---

## DNS y BIND

Patrón común: consultar los datos de referencia con `dig`, declarar `zone` en `named.conf.local`, escribir `db.<zona>` ($TTL, SOA, NS + A del NS), validar con `named-checkzone` / `named-checkconf -z`, arrancar/recargar y probar con `dig @127.0.0.1 <zona> <TIPO> +norecurse +noall +answer` (flag `aa` = autoridad).

| Archivo | Tipo | Qué pide | Palabras clave | Comandos / líneas clave |
|---|---|---|---|---|
| [zona-foo-example-org_1c2026](dns/zona-foo-example-org_1c2026.md) | Receta 1C 2026 Ej1 | Zona foo.example.org: responsable example.admin@foo.com.ar, A = IP de bar.protos.foo TTL 1h, www CNAME 1 semana, MX como mail.protos.foo (orden), solo 1.2.3.4 envía | SOA, contacto con `\.`, TTL por registro, CNAME a la raíz, MX con preferencia, SPF `-all` | `dig +short A bar.protos.foo`, `dig MX mail.protos.foo`, `named-checkzone`, `named-checkconf` |
| [zona-demiloo_2c2022](dns/zona-demiloo_2c2022.md) | Receta 2C 2022 Ej2/4 | Igual, zona demiloo.com.ar (A = foo.leak.com.ar, MX = proto.leak.com.ar, sin SPF) | Mismo molde que foo.example.org, TTL 2 semanas | — |
| [zona-carlitos-com-ar](Protolab/zona-carlitos-com-ar%28bind%2Cdns%29.md) | Receta repaso | Zona carlitos.com.ar: A 1.2.3.4 TTL 2h, mysite CNAME example.org, 3 MX con métricas 20/30/40 | CNAME a nombre externo (punto final), varios MX, TTL 1 día | `dig @127.0.0.1 carlitos.com.ar MX` |
| [corregir-zona-it-itba_2c2025](dns/corregir-zona-it-itba_2c2025.md) | Receta 2C 2025 Ej III | Zona it.itba.edu.ar no carga: corregir errores y SOA para propagación rápida | admin@ en el SOA, bad dotted quad, NS/MX sin A, serial, refresh/retry/expire, tabla de errores | `named-checkzone it.itba.edu.ar /etc/bind/db.it.itba.edu.ar`, `curl http://protos.foo/zona` |
| [zona-rota-errores-y-trampas](dns/zona-rota-errores-y-trampas.md) | Guía | Mensaje de named-checkzone → qué está mal; errores que dan OK igual | Punto final faltante (zona repetida), `@`, TXT sin comillas/partido, bucle CNAME, CNAME con otros registros | Procedimiento en 5 pasos |
| [zona-variantes-extra](dns/zona-variantes-extra.md) | Guía | Registros que no salieron todavía | Zona inversa PTR (`in-addr.arpa`), delegación NS + glue, SRV, comodín `*`, CAA, AAAA | `dig @127.0.0.1 -x 192.0.2.10` |
| [mx-spf_recu2020](dns/mx-spf_recu2020.md) | Receta recu 2020 Ej I | IPs de los SMTP que reciben el correo de proto.leak.com.ar; IPs permitidas por SPF | MX ordenado por preferencia, A de cada MX, TXT `v=spf1`, include/redirect (seguir la cadena) | `dig +short MX dominio`, `dig +short TXT dominio` |
| [LR26 Ej3](labosPropios/LabPracticaRecu20262C/Resueltos/LabRecu2026_Ej3_BIND9_zona_paso_a_paso.md) | Resuelto | Zona recu.protos.foo con contacto, A, www, MX copiados, SPF | Cómo se arma el SOA, nombres y TTL | `systemctl start bind9`, `dig @127.0.0.1 … +norecurse` |
| [LP26 Ej1](labosPropios/LabParcial-Rec20261c/Resueltos/LabProtos2026_Ej1_BIND_DNS_paso_a_paso.md) | Resuelto | Zona foo.example.org en el lab | `example\.admin`, $TTL 1w, DNS de Docker 127.0.0.11 vs DNS de referencia, SPF vs MX | `named-checkconf -z`, `named -c /etc/bind/named.conf` |
| [LP25 Ej3](labosPropios/LabProtos2025-2C/Resueltos/LabProtos2025-2C_Ej3_BIND9_zona_paso_a_paso.md) | Resuelto | Reparar zona it.itba.edu.ar | `www IN A pampero` → CNAME, glue, serial, tiempos | `systemctl reload bind9` |
| [SIM Ej4](labosPropios/SimilParcial20262c/Resueltos/SimilParcial20262c_Ej4_DNS_BIND_desde_pcap_paso_a_paso.md) | Resuelto | Reconstruir protos.lab desde backup.pcapng y agregar TXT "cachito hola" | Wireshark Answers → zona, quitar repetidos, dos TXT | filtro `dns.flags.response == 1 && ip.src == …` |
| [COR C8](labosPropios/lab-correo/Resueltos/C8_DNS_MX_SMTP_paso_a_paso.md) | Resuelto | Dominio sin A: descubrir el servidor por MX | MX → A, dig con puerto | `dig @127.0.0.1 -p 5361 MX empresa.lab` |

---

## nginx y proxy HTTP

Patrón común: diagnosticar el backend con `curl -i` y agregar `-H 'Nombre: valor'` hasta que responda bien; eso se traduce a `proxy_set_header Nombre valor;`. El nombre público se resuelve con `/etc/hosts` (o `curl --resolve`). Validar con `nginx -t` antes de `systemctl reload nginx`.

| Archivo | Tipo | Qué pide | Palabras clave | Comandos / líneas clave |
|---|---|---|---|---|
| [proxy-metadata-headers_1c2026](nginx/proxy-metadata-headers_1c2026.md) | Receta 1C 2026 Ej2 | `curl http://metadata.local` sin opciones obtiene metadata.protos.foo, que exige `Metadata: true` (JSON) | SSRF, proxy_set_header, Accept, /etc/hosts, proxy_pass con/sin barra, logs 404/502, 301 a HTTPS, backend HTTPS | `proxy_set_header Metadata true;`, `127.0.0.1 metadata.local` |
| [proxy-publico-url-sin-cambiar_2c2025](nginx/proxy-publico-url-sin-cambiar_2c2025.md) | Receta 2C 2025 Ej IV | Publicar http://publico.protos.foo con el contenido de parcial.protos.foo, sin cambiar la URL | Proxy inverso vs redirección, Host del backend, "What?", diferencias con metadata | `proxy_pass http://parcial.protos.foo;`, `proxy_set_header Host …` |
| [proxy-gzip_2c2021](nginx/proxy-gzip_2c2021.md) | Receta 2C 2021 Ej1 (y 2C 2020/2022 sin gzip) | http://foo.example.org/ sirve foo.leak.com.ar, comprimido si el cliente lo pide | gzip on, gzip_proxied any, gzip_vary, gzip_types, Accept-Encoding, Content-Encoding, backend que ya comprime, cualquier ruta | `curl --compressed …`, `curl -s -D - -o /dev/null -H "Accept-Encoding: gzip" …`, `-w '%{size_download}'` |
| [nginx-variantes-extra](nginx/nginx-variantes-extra.md) | Guía | Todas las variantes que pueden pedir | auth_basic/htpasswd, allow/deny, return 301, location por ruta, rewrite, autoindex, limit_except GET, error_page, upstream, X-Forwarded-For, proxy_cache, CORS, server_tokens, Accept-Language | `openssl passwd -apr1` (sin apache2-utils) |
| [LR26 Ej2](labosPropios/LabPracticaRecu20262C/Resueltos/LabRecu2026_Ej2_Nginx_proxy_metadata_paso_a_paso.md) | Resuelto | metadata.local en el lab | Aislar resolución vs header, sin editar /etc/hosts | `curl --resolve metadata.local:80:127.0.0.1 http://metadata.local` |
| [LP26 Ej2](labosPropios/LabParcial-Rec20261c/Resueltos/LabProtos2026_Ej2_Nginx_proxy_metadata_paso_a_paso.md) | Resuelto | metadata.local + variantes de parcial | Otro puerto/URL del cliente, headers extra (X-Legajo, Accept-Language), Host especial, `location = /`, proxy_pass con ruta | `getent hosts metadata.local`, `nginx -s reload` |
| [LP25 Ej4bis](labosPropios/LabProtos2025-2C/Resueltos/LabProtos2025-2C_Ej4bis_Nginx_HTTP_paso_a_paso.md) | Resuelto | publico.protos.foo → parcial.protos.foo | Backend responde "What?" por IP → fijar Host | `proxy_set_header Host parcial.protos.foo;` |
| [LP25 Ej4 HTTPS](labosPropios/LabParcial-Rec20261c/Resueltos/LabProtos2025-2C_Ej4_Nginx_HTTPS_paso_a_paso%281%29.md) | Resuelto | https://seguro.protos.foo con el contenido de parcial.protos.foo | `listen 443 ssl`, ssl_certificate(_key), CA de confianza, subjectAltName, mkcert vs OpenSSL | `mkcert -install`, `mkcert seguro.protos.foo`, `openssl req -x509 -newkey rsa:2048 -noenc …` |
| [LR26 Ej2bis](labosPropios/LabPracticaRecu20262C/Resueltos/LabRecu2026_Ej2bis_Negociacion_HTTP_paso_a_paso.md) | Resuelto | /foo/ en text/plain y español | Negociación de contenido, Accept, Accept-Language, Vary, Content-Language | `curl -i -H 'Accept: text/plain' -H 'Accept-Language: es' …` |

---

## curl, SOCKS y búsqueda de pistas

| Archivo | Tipo | Qué pide | Palabras clave | Comandos / líneas clave |
|---|---|---|---|---|
| [socks5h-acumulativo_1c2026](curl/socks5h-acumulativo_1c2026.md) | Receta 1C 2026 Ej3 | Navegar ejercicio3.protos.foo:3126 solo accesible vía `socks5h://proxy.protos.foo:1080` | socks5 vs socks5h, 302/Location, X-legajo, idioma, POST, JSON, Basic auth, base64 no es cifrado, redirecciones (-L, --post302), respuesta → opción | `curl -i -x socks5h://proxy.protos.foo:1080 …` |
| [curl-ejercicios-paso-a-paso](curl/curl-ejercicios-paso-a-paso.md) | Receta (3 ejercicios) | 1: reparar `/debugger` · 2: juego de Alzara (cookie) · 3: tesoro detrás del proxy SOCKS (token base64) | 302, X-Legajo, Accept-Language, POST, JSON, `-u`, Set-Cookie → `-b`, `-v`, token | `curl -b "winner=true" …`, `curl -x socks5h://… "…?token=…"` |
| [seguir-pistas-http-dns-ssh](pistas/seguir-pistas-http-dns-ssh.md) | Guía | Ejercicios de "búsqueda del tesoro" | Qué pide el servidor → qué agregar, decodificar pistas (base64/hex/ROT13), pistas en TXT/SRV/AXFR, nc a servicios de texto, encontrar puertos, pistas SSH | `curl -L --post302 -c jar.txt -b jar.txt -A 'Mozilla/5.0'`, `nc -C HOST PUERTO`, `nmap -sV -p-` |
| [LP26 Ej3](labosPropios/LabParcial-Rec20261c/Resueltos/LabProtos2026_Ej3_curl_SOCKS5_paso_a_paso.md) | Resuelto | Pistas acumulativas por SOCKS5 hasta aprobar | /debugger, X-legajo, Content-Language: ru → Accept-Language: es, POST JSON `{"fix":"yes"}`, `-u admin:admin`, variantes (HTML en POST, iconv) | `curl -i -X POST -H "Content-Type: application/json" -d '{"fix":"yes"}' -u admin:admin -x socks5h://…` |
| [SIM Ej1](labosPropios/SimilParcial20262c/Resueltos/SimilParcial20262c_Ej1_HTTP_SOCKS5_paso_a_paso.md) | Resuelto | Pistas en modo verboso y pedir http://secrets.ct.os/ por el proxy | `-v`, el proxy resuelve el nombre (socks5h), nombre interno no resoluble | `curl -v -x socks5h://172.30.0.12:1080 http://secrets.ct.os` |

---

## Correo: SMTP, POP3, IMAP y MIME

Patrón común: `date -R` para la fecha, `echo -n '…'` + `base64` para textos con tildes, `nc -C host 25` (SMTP) y `nc -C host 110` (POP3), `base64 -d` para verificar. Encabezados con tildes: `=?UTF-8?B?…?=`. Al servidor se llega por el MX del dominio (`dig MX`).

| Archivo | Tipo | Qué pide | Palabras clave | Comandos / líneas clave |
|---|---|---|---|---|
| [smtp-pop3-base64_1c2026](smtp/smtp-pop3-base64_1c2026.md) | Receta 1C 2026 Ej5 | Correo con X-Parcial 2024/2, ¡Buenos días!, remitente ITBA, ¡Hola mundo!, sin QP, a legajo@mail.sebikul.com; verificar POP3 | Sobre vs cabeceras, Content-Transfer-Encoding: base64, charset=UTF-8, encoded-word, usuario = contraseña POP3 | `nc -C mail.sebikul.com 25`, `USER/PASS`, `LIST`, `RETR 1` |
| [smtp-multipart-negrita_recu2026](smtp/smtp-multipart-negrita_recu2026.md) | Receta recu 2026 Ej1 | Igual con ¡Hola mundo! en negrita, X-Parcial 2026/1R, a legajo@mail.protos.foo | multipart/alternative, boundary, text/plain + text/html `<b>`, MX (mx1.protos.foo), Date y Message-ID (GreenMail) | `dig +short MX mail.protos.foo`, `nc -C mx1.protos.foo 25` |
| [smtp-variantes-mime](smtp/smtp-variantes-mime.md) | Guía | Todas las variantes de formato y MIME | Negrita/cursiva/subrayado/color/link, adjunto (multipart/mixed), inline `cid:` (multipart/related), inline + adjunto, quoted-printable, Cc/Bcc/Reply-To, nombre con tildes, plan B: mensaje en un archivo enviado con `nc` | `Content-Disposition: attachment`, `Content-ID: <…>` |
| [smtp-pop3-mision-catedra](smtp/smtp-pop3-mision-catedra.md) | Receta (práctica cátedra) | Buzón del agente 5: leer la misión, responder a secretary@usa.com con la clave bien codificada, borrar el original | `curl pop3://`, CAPA, AUTH PLAIN, base64 de ida y vuelta, DELE + QUIT | `curl -v --user "5" pop3://192.168.0.238:110/1` |
| [LP26 Ej5](labosPropios/LabParcial-Rec20261c/Resueltos/LabProtos2026_Ej5_SMTP_POP3_Base64_paso_a_paso.md) | Resuelto | El Ej5 de 1C 2026 en el lab | Qué significa "MUA sin QP", Message-ID, From/Subject codificados | `echo -n '¡Hola mundo!'` + `base64` |
| [LP26 Recu1](labosPropios/LabParcial-Rec20261c/Resueltos/LabProtos2026_Recu1_SMTP_POP3_negrita_paso_a_paso.md) | Resuelto | Negrita, servidor elegido por DNS | MX con prioridad, multipart/alternative | `dig MX mail.protos.foo +noall +answer` |
| [LR26 Ej1](labosPropios/LabPracticaRecu20262C/Resueltos/LabRecu2026_Ej1_SMTP_POP3_HTML_paso_a_paso.md) | Resuelto | Negrita, X-Parcial 2026/2R | Cuándo hace falta boundary, ver en Thunderbird / navegador | `nc -C mx1.protos.foo 25` |
| [COR C1](labosPropios/lab-correo/Resueltos/C1_SMTP_POP3_paso_a_paso.md) | Resuelto | Encontrar los errores del diálogo SMTP de Lucía y rehacerlo | nc sin -C (CRLF), falta EHLO (503), RCPT TO equivocado, X-Parcial mal, Subject UTF-8 sin encoded-word, faltan Date/Message-ID/charset, HTML en text/plain, Ctrl+C vs QUIT | `nc -C 127.0.0.1 2525` |
| [COR C2](labosPropios/lab-correo/Resueltos/C2_SMTP_POP3_paso_a_paso.md) | Resuelto | Texto simple sin QP | base64 vs 7bit/8bit, errores frecuentes | `nc -C 127.0.0.1 2110` |
| [COR C3](labosPropios/lab-correo/Resueltos/C3_SMTP_POP3_MIME_negrita_paso_a_paso.md) | Resuelto | Negrita + alternativa de texto plano | multipart/alternative, orden de las partes | `boundary="limiteC3"` |
| [COR C4](labosPropios/lab-correo/Resueltos/C4_POP3_SMTP_mision_paso_a_paso.md) | Resuelto | Misión: leer, responder con Re: y la clave no-ASCII, borrar | TOP, RETR, DELE, In-Reply-To, References | `TOP 1 0`, `DELE 1` |
| [COR C5](labosPropios/lab-correo/Resueltos/C5_SMTP_POP3_imagen_adjunta_paso_a_paso.md) | Resuelto | Adjuntar logo.png y extraerlo por POP3 | multipart/mixed, image/png, attachment; filename | `base64 logo.png`, `file`, `cmp` |
| [COR C6](labosPropios/lab-correo/Resueltos/C6_SMTP_POP3_imagen_inline_paso_a_paso.md) | Resuelto | Imagen dentro del HTML | multipart/related, Content-ID, `cid:`, inline | `<img src="cid:logoC6">` |
| [COR C7](labosPropios/lab-correo/Resueltos/C7_SMTP_To_Cc_Bcc_paso_a_paso.md) | Resuelto | To, Cc y copia oculta | Sobre vs mensaje, varios RCPT TO, no escribir Bcc | tres `RCPT TO` |
| [COR C8](labosPropios/lab-correo/Resueltos/C8_DNS_MX_SMTP_paso_a_paso.md) | Resuelto | Entregar a dominio sin A, por MX | MX → A, 7bit, Permission denied del script | `dig @127.0.0.1 -p 5361 MX empresa.lab` |
| [COR C9](labosPropios/lab-correo/Resueltos/C9_SMTP_AUTH_PLAIN_paso_a_paso.md) | Resuelto | Enviar a dominio externo con submission autenticada | 587/submission, relay, 250-AUTH, AUTH PLAIN = base64(\0usuario\0clave) | `echo -ne '\x0063051\x00protos2026'` + `base64` |
| [COR C10](labosPropios/lab-correo/Resueltos/C10_quoted_printable_dot_stuffing_paso_a_paso.md) | Resuelto | Cuerpo en QP, remitente Pingüino Ñandú, línea que empieza con punto | quoted-printable (=C3=B3 por byte), dot-stuffing `..` | — |
| [COR C11](labosPropios/lab-correo/Resueltos/C11_POP3_limpieza_buzon_paso_a_paso.md) | Resuelto | Borrar los 3 mensajes con X-Spam-Flag: YES sin bajar cuerpos | TOP n 0, DELE, QUIT confirma | `TOP 1 0` … `TOP 7 0` |
| [COR C12](labosPropios/lab-correo/Resueltos/C12_POP3_SMTP_respuesta_mismo_hilo_paso_a_paso.md) | Resuelto | Responder conservando el hilo | Message-ID original, In-Reply-To, References, Re: | `In-Reply-To: <consulta-7731@…>` |
| [SIM Ej3](labosPropios/SimilParcial20262c/Resueltos/SimilParcial20262c_Ej3_SMTP_IMAP_POP3_paso_a_paso.md) | Resuelto | Corregir sesión SMTP (puerto 143, HELLO, MAIL TO) y leer la flag por IMAP | IMAP: tags, LOGIN, LIST "" "*", EXAMINE, FETCH BODY.PEEK[], LOGOUT; variante POP3 | `nc -C 172.30.0.30 143`, `a1 LOGIN 63051 63051` |

---

## SSH: claves, passphrase y túneles

Patrón de "clave expuesta": `curl … -o mykey`, `chmod 600 mykey`, conseguir la passphrase (panel por proxy, DNS, base64, captura, MAC) y entrar con `ssh -v -i mykey -o IdentitiesOnly=yes usuario@host`. Passphrase ≠ contraseña del usuario. Túneles: `-L` abre el puerto en **tu** máquina, `-R` en la **remota**, `-D` es un SOCKS.

| Archivo | Tipo | Qué pide | Palabras clave | Comandos / líneas clave |
|---|---|---|---|---|
| [tunel-tail-pampero_1c2026](ssh/tunel-tail-pampero_1c2026.md) | Receta 1C 2026 Ej4 (2C 2020/2022 igual) | `tail -f archivo.log` local sigue /tmp/parcial-20261 de pampero, con túnel y legajo como puerto | -L, nc -l, pipes y redirecciones, 3 terminales, archivo que no crece | `ssh -L 63051:127.0.0.1:63051 …`, `tail -f … \| nc -l 127.0.0.1 63051`, `nc 127.0.0.1 63051 > archivo.log` |
| [clave-publica-persistir-acceso_recu2026](ssh/clave-publica-persistir-acceso_recu2026.md) | Receta recu 2026 Ej2 | Seguir entrando aunque cambien la contraseña | authorized_keys, clave vs contraseña son métodos independientes, puerto con nmap, permisos | `ssh-keygen`, `ssh-copy-id -p PUERTO`, `-o PreferredAuthentications=publickey` |
| [pem-passphrase-mac_2c2021](ssh/pem-passphrase-mac_2c2021.md) | Receta 2C 2021 Ej III | Entrar como pdc (puerto 2222) con llave.pem cuya passphrase es la MAC de ens3 de pampero | MAC propia (`ip link`), MAC de otro host / gateway (`ip neigh`, `arp`), IP por DHCP de una captura, puerto 9090 en el recu | `curl -o llave.pem …`, `ssh -i ./llave.pem -o IdentitiesOnly=yes -p 2222 pdc@…` |
| [internet-sin-nat_2c2021](ssh/internet-sin-nat_2c2021.md) | Receta 2C 2021 Ej IV | Host sin NAT debe poder hacer curl a internet; variante: que se vea tu IP y no la de pampero | Remote dynamic forwarding `-R puerto` (SOCKS), -R vs -L vs -D, ALL_PROXY, socks5h | `ssh -i llave.pem -p 2222 -R 63051 pdc@…`, `export ALL_PROXY=socks5h://127.0.0.1:63051` |
| [LP26 Ej4](labosPropios/LabParcial-Rec20261c/Resueltos/LabProtos2026_Ej4_tunel_SSH_tail_paso_a_paso.md) | Resuelto | Túnel + tail en el lab | Cómo decidir -L vs -R, ExitOnForwardFailure, 4 terminales | `ssh -o ExitOnForwardFailure=yes -L 127.0.0.1:63051:127.0.0.1:63051 …` |
| [LR26 Ej4](labosPropios/LabPracticaRecu20262C/Resueltos/LabRecu2026_Ej4_SSH_claves_paso_a_paso.md) | Resuelto | Clave pública + cambio de contraseña | nmap -sV, ed25519, huella `ssh-keygen -lf`, revocar, `passwd` | `ssh-copy-id -i ~/.ssh/id_ed25519_recu4.pub parcial@parcial.protos.foo` |
| [SSH Ej1](labosPropios/lab-ssh/Resueltos/SSH_Ej1_clave_expuesta_panel_interno_paso_a_paso.md) | Resuelto | Con 2 bloques nginx dados: bajar /sec/mykey1, passphrase del panel secrethost | root + ruta = URL, try_files, server_name → header Host, proxy a servicio interno | `curl -i -H "Host: secrethost" http://127.0.0.1:8061/` |
| [SSH Ej2](labosPropios/lab-ssh/Resueltos/SSH_Ej2_clave_oculta_DNS_paso_a_paso.md) | Resuelto | Clave no enlazada; passphrase = IP de llave.internal.lab | robots.txt, /privado/respaldo/id_rsa, registro A | `dig @127.0.0.1 -p 5360 A llave.internal.lab` |
| [SSH Ej3](labosPropios/lab-ssh/Resueltos/SSH_Ej3_vhost_token_DNS_proxy_paso_a_paso.md) | Resuelto | Clave solo con Host archivos.lab; passphrase en /clave con ?token= publicado en TXT | Virtual host, query string, TXT | `curl -i -H "Host: secrethost" "127.0.0.1:8061/clave?token=…"` |
| [SIM Ej2](labosPropios/SimilParcial20262c/Resueltos/SimilParcial20262c_Ej2_nginx_SSH_paso_a_paso.md) | Resuelto | Listado /sec/, pista.txt, mykey, panel puerto 81 con Host secrethost, passphrase base64, flag | 301 → curl -L, listado de directorio, 403 por permisos, header con base64 | `curl -v -H "Host: secrethost" http://172.30.0.20:81` |
| [SIM Ej6](labosPropios/SimilParcial20262c/Resueltos/SimilParcial20262c_Ej6_HTTP_Basic_Wireshark_SSH_paso_a_paso.md) | Resuelto | Passphrase sacada de un Authorization: Basic en una captura | Follow HTTP stream, base64(usuario:clave), Permission denied (publickey), cuenta bloqueada | `ssh -v -i mykey -o IdentitiesOnly=yes pepito@172.30.0.70` |

---

## Red, DHCP y VirtualBox

| Archivo | Tipo | Qué pide | Palabras clave | Comandos / líneas clave |
|---|---|---|---|---|
| [dhcp-servidor_2c2025](red/dhcp-servidor_2c2025.md) | Receta 2C 2025 Ej I | Red 192.168.100.0/24, impresora por MAC con IP fija, DNS de Google, rango 10–200; verificar con nmap | isc-dhcp-server, INTERFACESv4, subnet, range, host + hardware ethernet + fixed-address, option domain-name-servers, síntomas de falla | `dhcpd -t -cf /etc/dhcp/dhcpd.conf`, `nmap --script broadcast-dhcp-discover --script-args "broadcast-dhcp-discover.mac=…"` |
| [gateway-ruta-estatica-nmap_2c2025](red/gateway-ruta-estatica-nmap_2c2025.md) | Receta 2C 2025 Ej II | 192.168.50.250 es gateway de 10.0.0.0/24: descubrir el servidor, servicios, HTTP y routers | Bridge, ruta estática, host discovery, servicios, traceroute | `ip route add 10.0.0.0/24 via 192.168.50.250`, `nmap -sn`, `nmap -sV`, `traceroute -n -T -p 80` |
| [virtualbox-nat-bridge](red/virtualbox-nat-bridge.md) | Guía | ¿NAT, Bridge o red interna? | Regla: estar en la red → Bridge, solo salir → NAT; red interna para DHCP; tabla por ejercicio | `ip -br addr`, `ip route`, `dhclient` |
| [LP25 Ej1](labosPropios/LabProtos2025-2C/Resueltos/LabProtos2025-2C_Ej1_DHCP_paso_a_paso.md) | Resuelto | Servidor DHCP en el lab | IP propia del servidor, lease, variantes (Client Identifier, rango exclusivo) | `ip addr add 192.168.100.1/24 dev eth0`, `dhcpd -t -4 -cf …` |
| [LP25 Ej2](labosPropios/LabProtos2025-2C/Resueltos/LabProtos2025-2C_Ej2_Ruteo_y_descubrimiento_paso_a_paso.md) | Resuelto | Ruteo y descubrimiento en el lab | Leer la tabla de rutas, traceroute TCP, cómo descubre saltos | `ip route get 10.0.0.1`, `traceroute -n -T -p 8080 10.0.0.137` |
| [SIM Ej5](labosPropios/SimilParcial20262c/Resueltos/SimilParcial20262c_Ej5_DHCP_Wireshark_paso_a_paso.md) | Resuelto | DHCP en una captura | DORA, xid, opciones 12/50/53/54, yiaddr vs ciaddr, 0.0.0.0 y broadcast, puertos 68→67 | filtro `dhcp` |

---

## Capturas (pcap) y Wireshark

Las capturas originales (`botica.pcap.gz`, `parcial-correo.pcap.gz`, `dhcp-parcial.pcap.gz`) están en el proyecto de Claude "protos" (carpeta "Protos contexto").

| Archivo | Tipo | Qué pide | Palabras clave | Comandos / líneas clave |
|---|---|---|---|---|
| [pcap](pcap/pcap.md) | Receta 2C 2020 Ej V–VI + recu Ej II | botica: redes de 10.0.0.1, saltos a 8.8.8.8, password de telnet, cuerpo del mail · parcial-correo: mostrar la imagen · dhcp-parcial: negociación (MAC, servidor, lease, gateway, DNS, unicast/broadcast) · extras: telnet, SMTP Received, HTTP ETag, RIP, fragmentación | Filtro de captura vs visualización, Follow TCP Stream, Export Objects, trampa del disector, script extraer_correo.py | `tshark -r … -Y …`, `-T fields -e …`, `zcat`, `capinfos` |
| [SIM Ej4](labosPropios/SimilParcial20262c/Resueltos/SimilParcial20262c_Ej4_DNS_BIND_desde_pcap_paso_a_paso.md) | Resuelto | DNS: reconstruir zona | Answers → zona | `dns.flags.response == 1` |
| [SIM Ej5](labosPropios/SimilParcial20262c/Resueltos/SimilParcial20262c_Ej5_DHCP_Wireshark_paso_a_paso.md) | Resuelto | DHCP: DORA | yiaddr, opciones | `dhcp` |
| [SIM Ej6](labosPropios/SimilParcial20262c/Resueltos/SimilParcial20262c_Ej6_HTTP_Basic_Wireshark_SSH_paso_a_paso.md) | Resuelto | HTTP: Basic auth | Follow HTTP Stream, Authorization | `http` |

---

## Integrador

| Archivo | Qué combina |
|---|---|
| [Protolab/EJ-Integrador(Vault).pdf](Protolab/EJ-Integrador%28Vault%29.pdf) | "The Vault": entrar a un SSH sin internet combinando ruteo + DNS (SOA) + HTTP (headers, negociación de contenido) + email (multipart, base64) + token sin estado + ruta estática + nmap + clave SSH con passphrase |

---

## Labos para practicar

Todos en [`labosPropios/`](labosPropios/). Cada uno tiene consignas, un corrector y los resueltos paso a paso en `Resueltos/`.

| Labo | Cómo se usa | Ejercicios | Consignas / soluciones |
|---|---|---|---|
| [LabParcial-Rec20261c](labosPropios/LabParcial-Rec20261c/) (**LP26**) | Docker: `./levantar.sh` o `make up`, `make ws` (workstation), `./verificar.sh`, `make down` | 1C 2026: 1 BIND · 2 nginx metadata · 3 curl SOCKS5 · 4 túnel SSH + tail · 5 SMTP+POP3 · Recu: 1 SMTP negrita · 2 SSH por clave | [CONSIGNAS](labosPropios/LabParcial-Rec20261c/LabProtos2026/CONSIGNAS.md) · [resoluciones/](labosPropios/LabParcial-Rec20261c/LabProtos2026/resoluciones/) · [SOLUCIONES](labosPropios/LabParcial-Rec20261c/LabProtos2026/solucion/SOLUCIONES.md) · [Resueltos/](labosPropios/LabParcial-Rec20261c/Resueltos/) |
| [LabPracticaRecu20262C](labosPropios/LabPracticaRecu20262C/) (**LR26**) | Docker: `make up`, `make ws`, `make corregir [ej=1\|2\|2b\|3\|4] [leg=NNNNN]`, `make reset`, `make down` | 1 SMTP+POP3 negrita · 2 nginx metadata · 2b negociación HTTP · 3 BIND recu.protos.foo · 4 SSH por clave | [CONSIGNAS](labosPropios/LabPracticaRecu20262C/CONSIGNAS.md) · [resoluciones/](labosPropios/LabPracticaRecu20262C/resoluciones/) · [SOLUCIONES](labosPropios/LabPracticaRecu20262C/solucion/SOLUCIONES.md) · [Resueltos/](labosPropios/LabPracticaRecu20262C/Resueltos/) |
| [LabProtos2025-2C](labosPropios/LabProtos2025-2C/) (**LP25**) | Docker: `make up`, `make check`, `make ws`, `make corregir [ej=1\|2\|3\|4\|4b]`, `make reset`, `make down` | 2Q2025: I DHCP · II gateway + ruta · III zona rota · IV nginx HTTPS · IV-bis nginx HTTP | [CONSIGNAS](labosPropios/LabProtos2025-2C/CONSIGNAS.md) · [resoluciones/](labosPropios/LabProtos2025-2C/resoluciones/) · [SOLUCIONES](labosPropios/LabProtos2025-2C/solucion/SOLUCIONES.md) · [Resueltos/](labosPropios/LabProtos2025-2C/Resueltos/) |
| [SimilParcial20262c](labosPropios/SimilParcial20262c/) (**SIM**) | Docker (red 172.30.0.0/24, puertos en 127.0.0.1): `.env` con LEGAJO, `./levantar.sh`, `./bajar.sh` | Simulacro 2C 2026 (Watch Dogs): 1 HTTP+SOCKS5 · 2 nginx+SSH · 3 SMTP+IMAP · 4 DNS desde pcap · 5 DHCP en pcap (extra) · 6 Basic auth en pcap + SSH (extra) | [CONSIGNAS](labosPropios/SimilParcial20262c/CONSIGNAS.md) · [SOLUCIONES](labosPropios/SimilParcial20262c/solucion/SOLUCIONES.md) · [Resueltos/](labosPropios/SimilParcial20262c/Resueltos/) |
| [lab-correo](labosPropios/lab-correo/) (**COR**) | Local, sin Docker (python3): `bash lab-correo.sh up`; SMTP 2525, submission 2587, POP3 2110, DNS 5361 | C1–C12: errores de diálogo, texto simple, negrita, misión, adjunto, inline, Cc/Bcc, MX, AUTH PLAIN, QP + dot-stuffing, limpieza POP3, responder en hilo | [consignas](labosPropios/lab-correo/consignas.md) · [Resueltos/](labosPropios/lab-correo/Resueltos/) |
| [lab-ssh](labosPropios/lab-ssh/) (**SSH**) | Local, sin Docker: `bash lab-ssh.sh` (HTTP 8060/8061, DNS 5360, sshd local) | 1 clave expuesta + panel interno · 2 clave oculta + DNS · 3 vhost + token DNS + proxy | [consignas](labosPropios/lab-ssh/consignas.md) · [Resueltos/](labosPropios/lab-ssh/Resueltos/) |

---

## Por parcial

| Parcial | Ejercicio → receta | Resuelto en labo |
|---|---|---|
| **2C 2026 (simulacro)** | 1 HTTP+SOCKS5 · 2 nginx+SSH · 3 SMTP+IMAP · 4 DNS desde pcap | [SIM](labosPropios/SimilParcial20262c/Resueltos/) |
| **Recuperatorio 2026** | 1 [SMTP negrita](smtp/smtp-multipart-negrita_recu2026.md) · 2 [SSH por clave](ssh/clave-publica-persistir-acceso_recu2026.md) | [LP26 Recu1](labosPropios/LabParcial-Rec20261c/Resueltos/LabProtos2026_Recu1_SMTP_POP3_negrita_paso_a_paso.md) · [LR26](labosPropios/LabPracticaRecu20262C/Resueltos/) |
| **1C 2026** | 1 [zona BIND](dns/zona-foo-example-org_1c2026.md) · 2 [nginx metadata](nginx/proxy-metadata-headers_1c2026.md) · 3 [curl SOCKS](curl/socks5h-acumulativo_1c2026.md) · 4 [túnel + tail](ssh/tunel-tail-pampero_1c2026.md) · 5 [SMTP + POP3](smtp/smtp-pop3-base64_1c2026.md) | [LP26](labosPropios/LabParcial-Rec20261c/Resueltos/) |
| **2C 2025** | I [DHCP](red/dhcp-servidor_2c2025.md) · II [gateway + ruta](red/gateway-ruta-estatica-nmap_2c2025.md) · III [zona con errores](dns/corregir-zona-it-itba_2c2025.md) · IV [nginx proxy](nginx/proxy-publico-url-sin-cambiar_2c2025.md) | [LP25](labosPropios/LabProtos2025-2C/Resueltos/) |
| **2C 2022** | 1 [nginx proxy](nginx/proxy-gzip_2c2021.md) (versión sin gzip) · 2/4 [zona demiloo](dns/zona-demiloo_2c2022.md) · túnel + tail con /tmp/pdc ([receta](ssh/tunel-tail-pampero_1c2026.md)) | — |
| **2C 2021** | I [nginx proxy + gzip](nginx/proxy-gzip_2c2021.md) · III [SSH con .pem y MAC](ssh/pem-passphrase-mac_2c2021.md) · IV [SSH sin NAT](ssh/internet-sin-nat_2c2021.md) | — |
| **2C 2020** | nginx proxy sin gzip ([receta](nginx/proxy-gzip_2c2021.md)) · túnel + tail con /tmp/bar ([receta](ssh/tunel-tail-pampero_1c2026.md)) · V–VI [pcap](pcap/pcap.md) (dhcp-parcial, parcial-correo) | — |
| **Recuperatorio 2020** | I [MX y SPF](dns/mx-spf_recu2020.md) · II [pcap](pcap/pcap.md) | — |
| **Repaso / cátedra** | [zona carlitos](Protolab/zona-carlitos-com-ar%28bind%2Cdns%29.md) · [misión SMTP+POP3](smtp/smtp-pop3-mision-catedra.md) · [curl acumulativo x3](curl/curl-ejercicios-paso-a-paso.md) · [The Vault](Protolab/EJ-Integrador%28Vault%29.pdf) | — |

**Variables que cambian entre parciales:** dominios, IPs, puertos, legajo, usuario y contraseña. Cada receta marca qué copiar del enunciado y qué es solo de la práctica local.
