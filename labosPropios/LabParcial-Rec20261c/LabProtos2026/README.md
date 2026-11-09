# LabProtos2026

Laboratorio Docker con los ejercicios del **parcial 2026 1C** y del **recuperatorio 2026** de Protocolos de Comunicación. Pensado para arrancar de una y practicar con **IPs reales** y nombres DNS reales (nada de `localhost`).

## Cómo se usa

```bash
./levantar.sh                          # construye y levanta todo (1ra vez tarda)
docker compose exec workstation bash   # entrás al workstation y practicás
less CONSIGNAS.md                       # los enunciados
./verificar.sh                          # confirma que el lab está funcional
./bajar.sh                              # apaga y limpia
```

O con los atajos del `Makefile` (misma cosa, más corto): `make up`, `make ws` (entra al workstation), `make check`, `make logs s=mail`, `make down`. `make` solo lista todos.

Trabajás **dentro del workstation**: desde ahí `curl`, `dig`, `nc`, `ssh`, `nmap` resuelven los nombres `.protos.foo` a las IPs reales de la red Docker. Por eso **no se publica ningún puerto a tu host** y nada puede chocar (ni el 53, ni el 5353).

## Ejercicios

| # | Tema | Host / servicio |
|---|------|-----------------|
| 1 | BIND / DNS | datos en `bar.protos.foo`, MX de `mail.protos.foo` |
| 2 | proxy nginx (metadata, anti-SSRF) | `metadata.protos.foo` |
| 3 | HTTP acumulativo vía SOCKS5 | `ejercicio3.protos.foo:3126` por `proxy.protos.foo:1080` |
| 4 | túnel SSH + netcat | `pampero.itba.edu.ar` (user `alumno`) |
| 5 | SMTP + POP3 (MIME base64) | `mail.sebikul.com` :25 / :110 |
| recu-1 ⭐ | SMTP a `mail.protos.foo` (negrita) | `mx1.protos.foo` :25 / POP3 :110 |
| recu-2 ⭐ | persistir acceso SSH | `parcial.protos.foo` (user `parcial`/`holamundo`) |

## Mapa de red

```
red protos 172.28.0.0/24                 red oculta 172.29.0.0/24 (internal)
  workstation  172.28.0.5  <- entrás acá   ej3    172.29.0.30
  dns          172.28.0.53                 proxy  172.29.0.40 (+172.28.0.40)
  mail         172.28.0.25
  metadata     172.28.0.20
  proxy        172.28.0.40
  pampero      172.28.0.60
  parcial      172.28.0.72
```

`ejercicio3.protos.foo` vive en la red *oculta*: el workstation no lo rutea, por eso el Ej3 **obliga** a pasar por el proxy SOCKS5 (con `socks5h`, el proxy resuelve el nombre).

## Estructura

```
LabProtos2026/
├── docker-compose.yml   levantar.sh   bajar.sh   verificar.sh
├── CONSIGNAS.md                 # enunciados (parcial + recu)
├── dns/                         # dnsmasq: toda la zona -> IPs reales
├── workstation/                 # tu máquina (curl, dig, nc, ssh, nmap, bind9, nginx)
├── metadata/  ej3/  proxy/      # Ej2 / Ej3
├── mail/                        # Ej5 + recu-1 (SMTP+POP3 en python)
├── pampero/  parcial/           # Ej4 / recu-2
├── common/keys/                 # par SSH del alumno (pre-generado)
├── resoluciones/                # ACÁ escribís vos (un .md por ejercicio)
└── solucion/SOLUCIONES.md       # guía de respuestas (spoilers)
```

## Requisitos
- Docker + plugin `docker compose` (v2). En Ubuntu con `docker.io`: `sudo apt install -y docker-compose-v2`. El `levantar.sh` lo verifica y avisa si falta.
- Internet la primera vez (para construir las imágenes). Después corre todo offline.

## Notas de las correcciones respecto del lab anterior
- **Compose:** `levantar.sh` chequea `docker compose version` y el daemon antes de arrancar, con mensaje claro.
- **Puertos:** no se publican puertos al host → imposible que choquen (5353, 53, etc.).
- **SSH:** las cuentas (`alumno`, `parcial`) quedan con contraseña asignada y clave autorizada desde el build/arranque; entrás sin tocar `passwd`.
- **nginx/clave:** no aplica el 403 del lab viejo; acá la clave del alumno se monta con permisos correctos en el build.
- **Readiness:** todos los servicios tienen `healthcheck` y `levantar.sh` espera a que estén *healthy* antes de darte el prompt (no más `dig connection refused` en el primer intento).
