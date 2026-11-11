# LabRecu2026

Laboratorio Docker para practicar de cara al **recuperatorio** de Protocolos de Comunicación. Los 4 ejercicios siguen el estilo y los temas que más se repiten en los parciales y recus del repo (2022, 2025, recu 2025, 2026, recu 2026). Todo con IPs y nombres reales de una red propia del lab.

## Arranque

Desde tu VM Ubuntu, en la carpeta del lab:

```bash
make up          # construye y levanta todo; espera a que esté listo
make ws          # entrás a tu VM
make corregir    # desde otra terminal: autocorrige los 4 ejercicios
make reset       # tu VM vuelve al estado inicial, para practicar de nuevo
make down        # apagar
```

`make` solo lista todos los atajos. Autocorregir uno: `make corregir ej=3` (`1 | 2 | 2b | 3 | 4`). Si usás un legajo distinto de `62815`: `make corregir leg=NNNNN`.

## Los ejercicios

| # | Tema | Qué practicás |
|---|------|---------------|
| 1 | **Correo (SMTP + POP3)** | Enviar a mano con `nc` un mail que cumpla buenas prácticas: `X-Parcial`, Subject con tildes, remitente ITBA, cuerpo en negrita y **base64** (no quoted-printable), a `{legajo}@mail.protos.foo`, y verificar por POP3. |
| 2 | **Proxy a un endpoint de metadata** | Configurar un proxy nginx local para que `curl http://metadata.local` devuelva lo que `metadata.protos.foo` sólo da con el header `Metadata: true`. |
| 3 | **DNS / BIND9** | Servir desde cero la zona `recu.protos.foo`: A (con TTL 1h) heredando la IP de `bar.protos.foo`, CNAME de `www`, MX iguales a los de `mail.protos.foo`, y SPF. |
| 4 | **Persistencia SSH** | Entrar a `parcial.protos.foo` con la contraseña filtrada y dejar tu clave pública para seguir entrando aunque la cambien. |
| 2-bis ⭐ | **Negociación de contenido HTTP** | Obtener la representación `text/plain` en español de un recurso con los `Accept` correctos. Extra, no suma puntos. |

> **Por qué estos 4:** correo y persistencia-SSH cayeron en los dos últimos recus (2025 y 2026); DNS es el tema más estable del programa; y un ejercicio de HTTP con `curl`/nginx aparece en todos los parciales. El 2-bis cubre la variante de negociación de contenido (recu 2025).

## La red

```text
            red del lab 192.168.60.0/24
  tu VM (alumno) .20 | DNS .53 | mail.protos.foo .70
  ejercicio2.protos.foo .80 | metadata.protos.foo .85 | parcial.protos.foo .90
```

En tu VM funcionan `sudo`, `systemctl {start|stop|restart|reload|status}` y `journalctl -u <servicio>` para `bind9` y `nginx`, como en Ubuntu.

## Detalles de construcción (lecciones de labs anteriores)

- **Sin puertos publicados:** nada choca con servicios de tu máquina.
- **Healthchecks en todo:** `make up` no devuelve el prompt hasta que cada servicio responde de verdad.
- **DNS, correo y HTTP escritos en Python y probados端 a punta** antes de empaquetar, no sólo "el contenedor arranca".
- **`make up` chequea** Docker, el plugin compose, el daemon y que tu VM no tenga ya IPs en `192.168.60.0/24`.

Probado desde cero: `make up` → resolver los 4 como alumno → `make corregir` da 24/24.

## Estructura

```text
LabRecu2026/
├── Makefile  levantar.sh  verificar.sh  corregir.sh  bajar.sh  docker-compose.yml
├── CONSIGNAS.md                 # los 4 enunciados, estilo parcial, sin pistas
├── resoluciones/                # tus hojas de entrega (una por ejercicio)
├── solucion/SOLUCIONES.md       # guía completa (spoilers)
├── alumno/                      # tu VM
├── dns/  mail/  httpneg/  metadata/  parcial/   # los servicios del lab
```
