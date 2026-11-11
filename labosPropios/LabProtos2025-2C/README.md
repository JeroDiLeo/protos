# LabProtos2025-2C

Laboratorio Docker para practicar el **Parcial Práctico 2Q2025** de Protocolos de Comunicación (72.07, 31/10/2025) con la dificultad real. Los enunciados son los del parcial original (`Parcial Práctico - 2Q2025.pdf`), y todo funciona con IPs y nombres reales de una red propia del lab.

## Arranque

Desde tu VM Ubuntu, en la carpeta del lab:

```bash
make up          # construye y levanta todo (la 1ra vez ~2-5 min); espera a que esté listo
make check       # confirma que el lab funciona
make ws          # entrás a tu "VM del parcial"
```

Adentro de `make ws` resolvés los ejercicios de `CONSIGNAS.md`. Desde afuera, en otra terminal:

```bash
make corregir          # autocorrige los 4 ejercicios (sin darte la respuesta)
make corregir ej=3     # solo uno: 1 | 2 | 3 | 4 | 4b
make reset             # tu VM vuelve al estado inicial del parcial, para practicar de nuevo
make down              # apagar
```

`make` solo lista todos los atajos.

## Qué hay en la red

```text
            red del laboratorio 192.168.50.0/24 (la "red abierta")
 ┌────────────┬──────────────┬───────────────┬────────────────────┬─────────────┐
 │ tu VM      │ DNS del lab  │ protos.foo    │ parcial.protos.foo │ gateway "A" │
 │ .20        │ .53          │ .80 (/zona)   │ .90 (backend HTTP) │ .250        │
 └─────┬──────┴──────────────┴───────────────┴────────────────────┴──────┬──────┘
       │ 2da placa, sin IP                                                │ .254
       │ red interna 192.168.100.0/24 (Ej I)          red 10.0.0.0/24 ────┴──── servidor oculto (Ej II)
```

| Ej | Tema | Qué tiene el lab |
|----|------|------------------|
| I | DHCP con isc-dhcp-server | Placa sin IP en una red aislada `192.168.100.0/24` y el `nmap broadcast-dhcp-discover` real. |
| II | Ruteo y descubrimiento | Gateway real `192.168.50.250` hacia `10.0.0.0/24`. El servidor no se alcanza hasta que agregás la ruta. |
| III | BIND9 | La zona rota del enunciado, cargada en tu BIND y publicada en `http://protos.foo/zona`. |
| IV | HTTPS + proxy reverso | `parcial.protos.foo` distingue sitios por el header `Host` (si le errás, responde `What?`). Hay que exponer `https://seguro.protos.foo` y que `curl` funcione sin opciones. |
| IV-bis ⭐ | Proxy reverso HTTP | Versión del apunte (`publico.protos.foo`). No suma puntos. |

En tu VM funcionan `sudo`, `systemctl {start|stop|restart|reload|status}` y `journalctl -u <servicio>` para `isc-dhcp-server`, `bind9` y `nginx`, como en Ubuntu. Igual que en el parcial, los nombres de las placas (`eth0`/`eth1`) pueden cambiar entre arranques: identificalas siempre con `ip -br addr`.

## Diferencias con el apunte `2025 2C.md`

El apunte del repo tiene errores de transcripción. El lab sigue el **PDF original**:

- **Ej I:** la impresora es `08:00:27:AE:C8:6A` → `192.168.100.8` (fuera del rango 10–200). El apunte dice `CB` y `.10`.
- **Ej III:** el MX es `mail`, sin punto final.
- **Ej IV:** el original pide HTTPS con `seguro.protos.foo`. La versión HTTP con `publico.protos.foo` del apunte quedó como IV-bis.

## Requisitos

- Docker y el plugin `docker compose` (v2). En Ubuntu: `sudo apt install -y docker.io docker-compose-v2`. `make up` lo verifica y te dice qué falta.
- Internet la primera vez, para bajar `ubuntu:24.04` e instalar paquetes.
- Que tu VM **no** tenga ya IPs en `192.168.50.0/24` ni en `192.168.100.0/24`. Por ejemplo, si te quedó `192.168.100.1` en `enp0s9` de una práctica anterior, `make up` lo detecta y te dice cómo sacarla.

## Cómo está armado (y por qué)

- **Sin puertos publicados:** nada choca con servicios de tu VM (53, 80, 443, etc.).
- **La red `10.0.0.0/24` vive dentro del gateway** (un *network namespace* conectado por un par veth). A rutea de verdad, y funciona igual en cualquier versión de Docker: Docker 28+ filtra el ruteo entre sus redes bridge.
- **Healthchecks en todo:** `make up` no te devuelve el prompt hasta que cada servicio responde de verdad, no solo cuando el contenedor arranca.
- **DNS propio del lab:** resuelve `protos.foo` y `parcial.protos.foo`, y lo que no conoce de `protos.foo` da NXDOMAIN, como `seguro.protos.foo` hasta que lo resuelvas vos. Lo demás se reenvía, así que `apt` funciona dentro de tu VM.

Probado desde cero: `make up` → `make check` → resolver los 4 ejercicios como alumno → `make corregir` (24/24) → `make reset`.

## Estructura

```text
LabProtos2025-2C/
├── Makefile  levantar.sh  verificar.sh  corregir.sh  bajar.sh  docker-compose.yml
├── CONSIGNAS.md                 # el parcial, con formato original
├── resoluciones/                # tus hojas de entrega (una por ejercicio)
├── solucion/SOLUCIONES.md       # guía completa (spoilers)
├── alumno/                      # tu VM (dhcp, bind9, nginx, nmap, ...)
├── gateway/                     # host A + red 10.0.0.0/24 + servidor oculto
├── dns/  web/  parcial/         # DNS del lab, protos.foo/zona, backend del Ej IV
```
