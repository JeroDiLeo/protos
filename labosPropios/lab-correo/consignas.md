# Consignas — Lab de correo (SMTP / POP3 / MIME)

12 ejercicios. **C1** es del tipo "encontrá los errores" (como tu Ej3 del parcial). **C2 a C12**
son variantes de envío y lectura que tomaron en distintos cuatrimestres, más algunas nuevas.

En todos, cuando termines, corregí con:
```
bash lab-correo.sh corregir C1      # te dice qué está bien y qué falta
bash lab-correo.sh pista C3         # una pista, sin la solución
```

## Datos del entorno (los levanta el lab)

| Servicio | Dónde | Notas |
|---|---|---|
| SMTP recepción (MX) | `127.0.0.1:2525` | recibe para `mail.protos.lab` y `mision.lab` |
| SMTP de `empresa.lab` | se descubre por MX | otro servidor, otra IP (ejercicio C8) |
| SMTP envío (submission) | `127.0.0.1:2587` | para mandar afuera; **exige AUTH** (C9) |
| POP3 | `127.0.0.1:2110` | usuario = contraseña = la dirección del buzón |
| DNS del lab | `127.0.0.1:5361` (UDP) | `dig @127.0.0.1 -p 5361 ...` |
| Tu buzón | `<legajo>@mail.protos.lab` | el legajo lo pusiste al correr `up` |
| Submission (C9) | usuario `<legajo>`, contraseña `protos2026` | |

Conectarte a mano: `nc -C 127.0.0.1 2525`. Leer buzón: `nc -C 127.0.0.1 2110` o `curl --user "u" pop3://127.0.0.1:2110/`.

> El servidor **SÍ** valida: pide HELO antes que MAIL FROM, rechaza relay a dominios ajenos, exige `<...>` en las direcciones y aplica dot-stuffing. Si algo te lo rechaza, leé el código: te está marcando un error real.

---

## C1 — Encontrá los errores (estilo Ej3 del parcial)

Una compañera, Lucía (legajo 50122, `lsosa@itba.edu.ar`), tenía que resolver esto:

> *Envíe un correo cumpliendo todos los estándares y buenas prácticas: (1) header `X-Parcial: 2026/2C`; (2) Subject `¡Buenos días!`; (3) remitente con su nombre, apellido y cuenta del ITBA; (4) cuerpo `¡Hola mundo!`; (5) entregado a `{legajo}@mail.protos.foo`; (6) legible por MUAs que no soporten quoted-printable. Verifique por POP3.*

Lucía hizo esto (lo tenés en papel, no hay que ejecutarlo):

```
$ nc mail.protos.foo 25
220 mail.protos.foo ESMTP
MAIL FROM:<lsosa@itba.edu.ar>
RCPT TO:<lsosa@itba.edu.ar>
DATA
X-Parcial: 2026/2
Subject: ¡Buenos días!
From: <lsosa@itba.edu.ar>
To: <50122@mail.protos.foo>
MIME-Version: 1.0
Content-Type: text/plain
Content-Transfer-Encoding: base64

PGI+wqFIb2xhIG11bmRvITwvYj4=
.
^C
```
*(El base64 de arriba decodifica a `<b>¡Hola mundo!</b>`.)*

**Se pide:**
a) Liste **todos** los errores (de protocolo SMTP, de formato del mensaje, y respecto de la consigna), diciendo qué norma rompe cada uno y qué efecto tiene.
b) ¿El correo se entregó? Si se entregó, ¿dónde y con qué contenido?
c) Reescriba el diálogo correcto y mándelo de verdad contra el lab (a tu propio buzón, con `X-Parcial: 2026/2C`). Después `bash lab-correo.sh corregir C1`.

> Para ver la lista oficial de errores una vez que lo intentaste: `bash lab-correo.sh solucion C1`.

---

## C2 — Texto simple sin quoted-printable (2024/2C, 1C 2026)

Enviá un correo bien formado, entregado a tu buzón, con:
1. `X-Parcial: 2024/2`
2. Subject: `¡Buenos días!`
3. Remitente: tu nombre, apellido y cuenta del ITBA.
4. Cuerpo exactamente: `¡Hola mundo!`
5. Debe poder leerlo un MUA que **no** soporte quoted-printable.

Verificá por POP3 que llegó. *(La trampa: el `¡` y la `í` no son ASCII; pensá cómo van el cuerpo y el Subject.)*

---

## C3 — Cuerpo en negrita (Recu 2026)

Igual que C2 pero `X-Parcial: 2026/1R` y el cuerpo `¡Hola mundo!` debe verse **en negrita** en los MUAs con formato, conservando una versión de texto plano para los que no. Sin quoted-printable.

---

## C4 — Misión por POP3 (como el ejercicio de la cátedra)

En tu buzón hay un correo de `secretaria@mision.lab` (asunto `Misión: Imposible`). Entrá por POP3, leelo, y vas a encontrar una **clave de verificación** con caracteres no ASCII. Tenés que:
1. **Responder** a `secretaria@mision.lab` (Subject con `Re:`) poniendo en el cuerpo **exactamente** esa clave, con la codificación correcta para que llegue intacta.
2. **Borrar** el mensaje original del servidor.

*(Ojo con cómo codificás la clave y con cómo se borra en POP3.)*

---

## C5 — Imagen adjunta (Guía 4, variante típica)

Enviá a tu buzón un correo con `X-Parcial: LAB-C5`, Subject `Logo del laboratorio`, un cuerpo de texto `Adjunto el logo del laboratorio.` y **la imagen `~/lab-correo/adjuntos/logo.png` como adjunto**, de modo que un MUA la reconozca como archivo descargable. Verificá por POP3 que la parte de la imagen llegó, y mostrá cómo la extraerías.

---

## C6 — Imagen dentro del cuerpo (1C 2026, MIME related)

Enviá a tu buzón un correo con `X-Parcial: LAB-C6`, Subject `Logo en el cuerpo`, cuyo cuerpo sea **HTML con la imagen `logo.png` mostrada dentro del mensaje** (no como adjunto suelto). Pista: `cid:`.

---

## C7 — To, Cc y copia oculta (variante nueva)

Enviá un correo con `X-Parcial: LAB-C7`, Subject `Reunión de cátedra`, dirigido a tu buzón, con:
- **Copia (Cc)** visible a `ayudante@mail.protos.lab`.
- **Copia oculta (Bcc)** a `jefa@mail.protos.lab`.

Los tres tienen que recibirlo, pero `jefa` no debe aparecer en los headers de ninguna copia. *(Pensá qué va en el sobre `RCPT TO` y qué va en los headers.)*

---

## C8 — Entregar al servidor que diga el MX (Recu 2026, descubrir por DNS)

Tenés que entregarle un correo a `ventas@empresa.lab` (`X-Parcial: LAB-C8`, Subject `Pedido de presupuesto`). El dominio `empresa.lab` **no tiene registro A**: no te podés conectar a `empresa.lab` directo. Averiguá por DNS a qué servidor hay que entregarle y conectate a ese. *(`dig @127.0.0.1 -p 5361 MX empresa.lab` → menor prioridad primero → su registro A.)*

---

## C9 — Mandar afuera: submission con autenticación (variante nueva)

Tenés que mandarle un correo a `profe@externo.lab` (`X-Parcial: LAB-C9`, Subject `Entrega TP`). El servidor de recepción (`2525`) **rechaza** relay a dominios ajenos (te va a dar `554 Relay denied`). Para mandar afuera usá el servidor de **submission** en `127.0.0.1:2587`, que exige autenticarse primero (`AUTH`, usuario `<tu legajo>`, contraseña `protos2026`). *(Pensá cómo se arma el AUTH PLAIN con base64.)*

---

## C10 — Quoted-printable y tildes en el remitente (variante nueva)

Enviá un correo a tu buzón con `X-Parcial: LAB-C10`, remitente con nombre **`Pingüino Ñandú`** (y tu cuenta), Subject `Prueba de codificación`, y el cuerpo **codificado en quoted-printable** (no base64) con este texto exacto, tres líneas:
```
Canción de prueba: ¿cómo están?
.esta línea empieza con punto
fin
```
*(Dos trampas: el nombre del remitente tiene tildes → encoded-word; y la segunda línea empieza con un punto → dot-stuffing en DATA.)*

---

## C11 — Limpiar el buzón por POP3 (variante nueva)

El buzón `limpieza@mail.protos.lab` (contraseña igual) tiene 7 mensajes. Tres son spam: están marcados con el header `X-Spam-Flag: YES`. Entrá por POP3, identificá **sin descargar el cuerpo completo** cuáles son (pista: `TOP n 0` muestra solo los headers), borralos y confirmá. Deben quedar 4. *(Ojo: uno de los legítimos tiene asunto de "sorteo" pero no es spam — mirá el flag, no el asunto.)*

---

## C12 — Responder en el mismo hilo (variante nueva)

En tu buzón hay un correo de `atorres@mail.protos.lab` (`Consulta sobre la entrega`). Respondele (a esa dirección, Subject `Re: ...`) confirmando tu número de legajo en el cuerpo, de forma que la respuesta quede **enlazada al hilo original**. *(Qué headers hacen que un MUA agrupe la respuesta con el original.)*

---

## Cómo trabajar
1. Levantá el lab: `bash lab-correo.sh up`.
2. Resolvé un ejercicio (a mano con `nc -C`, o con `curl` para POP3).
3. Corregí: `bash lab-correo.sh corregir C<n>`. Si te traba algo, `bash lab-correo.sh log smtp`.
4. Para reintentar de cero: `bash lab-correo.sh reset`.
