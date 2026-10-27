# Protos: recetas para el parcial práctico

Cada archivo es una receta: arriba el enunciado textual, después la receta para el parcial, después la práctica, la tabla "Si algo falla" y las variantes. Para encontrar el ejercicio, buscá en la tabla qué dice tu enunciado.

Desde la terminal: `grep -ril "palabra" .` o abrí este README en GitHub y usá Ctrl+F.

## Qué dice el enunciado → qué archivo abrir

| El enunciado dice... | Archivo |
|---|---|
| Instale BIND, sirva la zona, responsable, registro A, www CNAME, MX iguales a otro dominio, SPF | [dns/zona-foo-example-org_1c2026.md](dns/zona-foo-example-org_1c2026.md) (con SPF) · [dns/zona-demiloo_2c2022.md](dns/zona-demiloo_2c2022.md) (sin SPF) |
| Corrija los errores del archivo de zona, que los cambios se propaguen | [dns/corregir-zona-it-itba_2c2025.md](dns/corregir-zona-it-itba_2c2025.md) |
| Servidores SMTP que reciben el correo de un dominio, política SPF, qué IPs pueden enviar | [dns/mx-spf_recu2020.md](dns/mx-spf_recu2020.md) |
| `curl http://nombre.local` debe devolver el contenido de otro servidor, el backend exige un header | [nginx/proxy-metadata-headers_1c2026.md](nginx/proxy-metadata-headers_1c2026.md) |
| nginx: usuario y contraseña, solo cierta IP, redirección 301, contenido por ruta, rewrite, autoindex, solo GET, error 404 propio, varios backends, caché, CORS, idioma (y mapa de todas las variantes) | [nginx/nginx-variantes-extra.md](nginx/nginx-variantes-extra.md) |
| Proxy inverso con contenido comprimido (gzip) de forma transparente, host virtual, "What?" | [nginx/proxy-gzip_2c2021.md](nginx/proxy-gzip_2c2021.md) |
| Servir el contenido de otro host sin modificar la URL, proxy_pass | [nginx/proxy-publico-url-sin-cambiar_2c2025.md](nginx/proxy-publico-url-sin-cambiar_2c2025.md) |
| Navegar con curl a un host al que solo se llega por proxy SOCKS, el servidor pide cosas de a una (302, header, idioma, POST, JSON, auth) | [curl/socks5h-acumulativo_1c2026.md](curl/socks5h-acumulativo_1c2026.md) |
| `tail -f` en vivo de un archivo de pampero, usar un túnel SSH, el legajo como puerto | [ssh/tunel-tail-pampero_1c2026.md](ssh/tunel-tail-pampero_1c2026.md) |
| Seguir entrando por SSH aunque cambien la contraseña, authorized_keys | [ssh/clave-publica-persistir-acceso_recu2026.md](ssh/clave-publica-persistir-acceso_recu2026.md) |
| Llave privada .pem con passphrase (MAC o IP de un host), puerto SSH distinto | [ssh/pem-passphrase-mac_2c2021.md](ssh/pem-passphrase-mac_2c2021.md) |
| Un host sin NAT necesita internet, túneles -R y -D, SOCKS | [ssh/internet-sin-nat_2c2021.md](ssh/internet-sin-nat_2c2021.md) |
| Enviar un correo a mano (header X-Parcial, subject con tilde, remitente, "MUAs sin quoted-printable"), verificar por POP3 | [smtp/smtp-pop3-base64_1c2026.md](smtp/smtp-pop3-base64_1c2026.md) |
| Correo con el cuerpo en negrita, multipart/alternative | [smtp/smtp-multipart-negrita_recu2026.md](smtp/smtp-multipart-negrita_recu2026.md) |
| Formato en el mail: subrayado, cursiva, color, link; imagen adjunta o dentro del cuerpo (cid); CC, BCC, varios destinatarios; quoted-printable | [smtp/smtp-variantes-mime.md](smtp/smtp-variantes-mime.md) |
| Zona inversa (PTR), delegar un subdominio, comodín, SRV, CAA | [dns/zona-variantes-extra.md](dns/zona-variantes-extra.md) |
| Búsqueda del tesoro: el servidor pide cosas de a una, pistas en headers, base64/hex, TXT/SRV/AXFR, servicio con nc | [pistas/seguir-pistas-http-dns-ssh.md](pistas/seguir-pistas-http-dns-ssh.md) |
| Zona rota con trampas: mensajes de named-checkzone, errores que dan OK igual (punto final, @, TXT sin comillas, bucle CNAME) | [dns/zona-rota-errores-y-trampas.md](dns/zona-rota-errores-y-trampas.md) |
| Instale un servidor DHCP, impresora con IP fija por MAC, rango, DNS | [red/dhcp-servidor_2c2025.md](red/dhcp-servidor_2c2025.md) |
| Un gateway de otra red, descubra el servidor, servicios expuestos, routers que intervienen | [red/gateway-ruta-estatica-nmap_2c2025.md](red/gateway-ruta-estatica-nmap_2c2025.md) |
| ¿NAT o Bridge en VirtualBox? Gateway de otra red, misma red del laboratorio, modo puente, red interna para DHCP | [red/virtualbox-nat-bridge.md](red/virtualbox-nat-bridge.md) |
| Analizar una captura (pcap): redes, saltos, password de telnet, cuerpo de un mail, imagen adjunta, IP por DHCP | [pcap/pcap.md](pcap/pcap.md) |

## Por parcial

| Parcial | Ejercicios |
|---|---|
| 1C 2026 | 1 DNS zona · 2 nginx proxy con headers · 3 curl por SOCKS · 4 túnel SSH + tail · 5 SMTP + POP3 |
| Recuperatorio 2026 | 1 SMTP en negrita · 2 SSH por clave |
| 2C 2025 | I DHCP · II gateway y ruta · III zona con errores · IV nginx proxy |
| 2C 2022 | 1 nginx proxy + gzip · 4 zona demiloo |
| 2C 2021 | I nginx proxy + gzip · II SSH con .pem · IV SSH sin NAT |
| Recuperatorio 2020 | MX y SPF |

## Variables que cambian entre parciales

Dominios, IPs, puertos, legajo, usuario y contraseña. Cada receta marca qué copiar del enunciado y qué es solo de la práctica local.
