# LabProtos2026 — Consignas

Enunciados tomados del **parcial 2026 1C** (Ej1–Ej5) y del **recuperatorio 2026** (recu-1, recu-2).
Trabajás dentro del workstation:

```bash
docker compose exec workstation bash
```

Desde ahí todo resuelve por nombre a IPs reales de la red (no uses `localhost`). Tu legajo de práctica es **62815** (cambialo si querés, pero mantené el mismo en todos lados).

---

## Ejercicio 1 — BIND / DNS

Instale un servidor de nombres BIND y realice los cambios necesarios para servir la zona `foo.example.org` considerando que:

1. Su servidor de DNS será la autoridad para esta zona.
2. La dirección de contacto de la persona responsable es `example.admin@foo.com.ar`.
3. `foo.example.org` debe tener un registro A apuntando a la dirección IP de `bar.protos.foo`. El registro tendrá una validez de 1 hora.
4. El subdominio `www` debe ser un CNAME apuntando a la raíz de la zona. Validez de 1 semana.
5. La zona debe poder recibir correos. El correo será atendido por los mismos servidores de correo que atienden el dominio `mail.protos.foo` (manteniendo el orden). Validez de 1 semana.
6. El servidor con la IP `1.2.3.4` es el único autorizado a enviar correos para esta zona.

Demuestre la correcta configuración utilizando `dig`.

> En el workstation ya está instalado BIND. Configurás `/etc/bind/named.conf.local` y el archivo de zona, arrancás el daemon y verificás con `dig @127.0.0.1 ...`. Para arrancar/recargar BIND en el lab (no hay systemd): `sudo named -c /etc/bind/named.conf` y para recargar `sudo rndc reload` (o matás y relanzás `named`).

---

## Ejercicio 2 — proxy nginx a un endpoint de metadata

En las nubes públicas es común encontrar *endpoints* de metadata que proveen información **solo en formato JSON** sobre la instancia. Suelen estar sobre IPs no ruteables y requieren el header `Metadata: true` para evitar ataques de **SSRF**.

Usted encontró un endpoint mal configurado, disponible públicamente en `http://metadata.protos.foo`. Como hacker curioso quiere explorarlo escribiendo la menor cantidad de caracteres, así que desea montar un proxy local tal que al ejecutar `curl http://metadata.local` se devuelva el contenido de `http://metadata.protos.foo`.

**Requisito:** no se permiten otras opciones de `curl` al pedir a `http://metadata.local`.

> En el workstation ya está instalado nginx. Agregás `metadata.local` a `/etc/hosts`, creás el `server` con `proxy_pass`, y arrancás nginx (`sudo nginx`, recargás con `sudo nginx -s reload`).

---

## Ejercicio 3 — HTTP a través de un proxy SOCKS5

El administrador de su empresa necesita ayuda navegando el servidor HTTP en `ejercicio3.protos.foo:3126` usando `curl`.

**Dato:** la red no rutea paquetes hacia el host `ejercicio3.protos.foo`, pero es accesible mediante un proxy `socks5h://proxy.protos.foo:1080`.

El servidor está "roto" y te va pidiendo cosas de a una (es **acumulativo**: cada paso agrega un flag al `curl` anterior). Seguilo hasta que te dé el ejercicio por aprobado.

---

## Ejercicio 4 — seguir un archivo remoto en vivo (túnel SSH)

Realice los cambios necesarios para que, desde una terminal de su host, al ejecutar `tail -f archivo.log` pueda seguir en vivo los cambios del archivo `/tmp/parcial-20261` del host `pampero.itba.edu.ar`.

**Nota:** cualquier solución que no involucre túneles obtiene la mitad del puntaje. Si necesita asignar puertos para túneles, use su número de legajo para evitar colisiones.

**Pista:** `tail -f`, `netcat` y los pipes (`|`) y redirecciones (`>`) pueden canalizar la información.

> Acceso a pampero: usuario `alumno` (la clave del workstation ya está autorizada, entrás directo con `ssh alumno@pampero.itba.edu.ar`). El archivo `/tmp/parcial-20261` ya recibe una línea cada ~15s, así que vas a ver cambios aparecer solos; también podés escribirle vos desde otra sesión.

---

## Ejercicio 5 — enviar un correo (SMTP) y verificar por POP3

Envíe un correo electrónico cumpliendo todos los estándares y buenas prácticas, con:

1. Header `X-Parcial` con valor `2024/2`.
2. Subject: `¡Buenos días!`
3. Remitente: su nombre, apellido y cuenta de correo del ITBA.
4. Texto del cuerpo: `¡Hola mundo!`
5. El correo debe entregarse a `{legajo}@mail.sebikul.com`.
6. Debe poder ser leído por MUAs que **no** soporten quoted-printable.

Verifique la recepción por **POP3** en el host `mail.sebikul.com`. Usuario `{legajo}@mail.sebikul.com`, contraseña igual al usuario.

---

## ⭐ Recuperatorio 2026

> Estos dos salieron en el recu. El recu-1 es una variante del Ej5; el recu-2 es nuevo (SSH).

### recu-1 — correo con cuerpo en negrita, a `mail.protos.foo`

Igual que el Ej5 pero:

1. Header `X-Parcial` con valor `2026/1R`.
2. El cuerpo `¡Hola mundo!` debe ir **en negrita**.
3. El correo se entrega a `{legajo}@mail.protos.foo`. Para enviarlo mirá los `MX` de ese dominio y conectate al de mayor prioridad (`nc -C mx1.protos.foo 25`).
4. Verificá por POP3 en `mail.protos.foo` (usuario y pass = `{legajo}@mail.protos.foo`).

### recu-2 — persistir acceso SSH

El host `parcial.protos.foo` corre un servidor SSH poco seguro. Sabés que la contraseña del usuario `parcial` es `holamundo`.

Siendo un hacker experimentado, quiere **persistir** el acceso aunque el administrador cambie la contraseña. Muestre que, sin importar la contraseña del usuario `parcial`, usted sigue pudiendo entrar.

**Pista:** primero reconocé el host con `nmap -sV parcial.protos.foo` (vas a ver SSH, nginx y un HTTP de Python). Después entrá con la contraseña filtrada y dejá tu clave pública autorizada.
