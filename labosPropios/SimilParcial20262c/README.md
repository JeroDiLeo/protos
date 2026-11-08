# Lab SimilParcial20262c

Laboratorio con **4 ejercicios idénticos en skill** al parcial práctico 2026-2C de Protocolos de Comunicación (temática *Watch Dogs*). Todo corre en Docker, aislado en una red propia.

| # | Tema | Skill que practicás |
|---|------|---------------------|
| 1 | HTTP + SOCKS5 | `curl -v`/`-H`, leer headers, tunelizar por proxy SOCKS5 (`socks5h`) |
| 2 | nginx + SSH | misconfig de nginx (listing de dir), virtual host por `Host:`, leer headers con `-v`, base64 (como Basic auth), login SSH con clave |
| 3 | SMTP + IMAP | hablar SMTP a mano (EHLO/MAIL FROM/RCPT TO/DATA/`.`), leer por IMAP/POP3 |
| 4 | DNS / bind9 | reconstruir una zona desde un pcap, configurar bind9, agregar record TXT, `dig` |
| **5 ⭐** | **DHCP (extra)** | analizar el handshake DORA en un pcap: IP ofrecida, server id, lease, opciones |
| **6 ⭐** | **nginx+SSH (extra)** | variante del Ej2: la passphrase está sniffeada en un pcap (Follow TCP Stream + Basic auth + base64) |

> ⭐ Los ejercicios **5 y 6 son EXTRA**: no estaban en el parcial, los sumé para practicar.

## Requisitos
- Docker + plugin `compose` (`docker compose version`).
- Estás en Linux: podés pegarle directo a las IP `172.30.0.x`. Igual todo está publicado en `127.0.0.1`.
- Útiles para resolver: `curl`, `ssh`, `nc`, `dig`, `base64`, `tshark`/Wireshark.

## Uso
```bash
# 1) (opcional) poné tu legajo
nano .env            # LEGAJO=TU_LEGAJO   (usuario y pass del Ej3)

# 2) levantar (la 1ra vez compila imágenes, tarda unos minutos)
./levantar.sh

# 3) resolvé los ejercicios
less CONSIGNAS.md

# 4) chequeo automático (después de resolver el Ej4)
LEGAJO=62345 bash solucion/verificar.sh

# 5) apagar
./bajar.sh
```

## Estructura
```
SimilParcial20262c/
├── docker-compose.yml      # la red + los 7 contenedores
├── .env                    # tu legajo
├── levantar.sh / bajar.sh
├── CONSIGNAS.md            # lo que tenés que resolver
├── ej1/  entry/ proxy/ secret/
├── ej2/  host/   (nginx + ssh; la passphrase se encuentra por pistas)
├── ej3/  mail/
├── ej4/  http/ (sirve backup.pcapng)  bind/ (tu DNS)  gen_pcap.py
├── ej5/  http/ (sirve dhcp.pcapng)     gen_dhcp.py        ⭐ EXTRA
├── ej6/  host/ (nginx+ssh, pista en captura.pcapng)  gen_capture.py  ⭐ EXTRA
└── solucion/
    ├── SOLUCIONES.md       # walkthrough completo (spoilers)
    └── verificar.sh        # chequea las 4 FLAGs
```

## Flags
- `FLAG{ej1-socks5-tunel-ctos-ok}`
- `FLAG{ej2-ssh-login-pepito-ok}` y `FLAG{ej2-vhost-secrethost-proxy-ok}`
- `FLAG{ej3-imap-fetch-ok}`
- Ej4 no tiene flag: se valida con `dig` mostrando la zona y el TXT `cachito hola`.
- Ej5 ⭐ (extra) no tiene flag: se responde con el análisis del pcap (ver `SOLUCIONES.md`).
- `FLAG{ej6-pcap-basicauth-ssh-ok}` ⭐ (extra)

> El pcap del Ej4 lo genera `ej4/gen_pcap.py` (ya está generado en `ej4/http/backup.pcapng`).
> Si querés cambiar los registros, editá ese script y corré `python3 ej4/gen_pcap.py` desde la carpeta `ej4/`.

## Notas de red
Subred `172.30.0.0/24`. El `ej1-secret` **no** publica puertos: sólo se llega atravesando el proxy SOCKS5 (esa es la gracia). El `ej4-bind` monta su `/etc/bind` desde `ej4/bind/etc-bind/` para que edites la zona en tu disco y reinicies el contenedor.
