# Lab de correo (SMTP / POP3 / MIME)

Monta en tu VM un servidor de correo de práctica (SMTP recepción, SMTP submission con auth, POP3 y
un DNS mínimo) y trae un **corrector** que revisa cada correo que mandás. 12 ejercicios: uno de
"encontrá los errores" como el Ej3 del parcial, más variantes de SMTP/POP3 de distintos
cuatrimestres y algunas nuevas.

Todo corre en `127.0.0.1` y **no instala nada** (solo necesita `python3`, `curl`, `nc` y `dnsutils`).
No usa Postfix ni Dovecot, así que no choca con nada y se lo podés pasar a un amigo.

## Primera vez

> Dentro de la VM, como tu usuario normal (no `sudo`).

1. Poné en una carpeta `lab-correo.sh`, `servidor.py`, `corregir.py` y `consignas.md`:
   ~~~bash
   mkdir -p ~/lab-correo-practica && cd ~/lab-correo-practica
   # copiá ahí los 4 archivos
   sudo apt install -y python3 curl netcat-openbsd dnsutils
   ~~~
2. Levantá el lab (la primera vez te pide tu legajo, nombre y cuenta ITBA; se usan para corregir):
   ~~~bash
   bash lab-correo.sh up
   ~~~
3. Abrí las consignas y resolvé:
   ~~~bash
   cat consignas.md
   ~~~

## Uso

~~~bash
bash lab-correo.sh up            # levanta los servidores
bash lab-correo.sh corregir C3   # corrige tu último correo de ese ejercicio
bash lab-correo.sh pista C3      # una pista corta
bash lab-correo.sh solucion C1   # la lista de errores del C1
bash lab-correo.sh log smtp      # lo último que vio el servidor (si algo no anda)
bash lab-correo.sh reset         # vacía los buzones y recrea los mensajes iniciales
bash lab-correo.sh down          # apaga
bash lab-correo.sh config        # cambiar legajo / nombre / cuenta
~~~

Conectarte a mano:
~~~bash
nc -C 127.0.0.1 2525                       # SMTP (recepción)
nc -C 127.0.0.1 2587                       # SMTP (envío afuera, con AUTH)
nc -C 127.0.0.1 2110                       # POP3
curl --user "63051@mail.protos.lab" pop3://127.0.0.1:2110/      # listar
curl --user "63051@mail.protos.lab" pop3://127.0.0.1:2110/1     # leer el 1
dig @127.0.0.1 -p 5361 MX empresa.lab +short                    # DNS del lab
~~~

## Qué cubre cada ejercicio

| Ej | Tema | De dónde sale |
|----|------|---------------|
| C1 | **Encontrar los errores** en un diálogo SMTP | como el Ej3 de tu parcial |
| C2 | Texto con acentos, sin quoted-printable | 2024/2C, 1C 2026 |
| C3 | Cuerpo en negrita (multipart/alternative) | Recu 2026 |
| C4 | Leer por POP3, decodificar, responder y borrar | ejercicio de la cátedra (misión) |
| C5 | Imagen **adjunta** (multipart/mixed) | Guía 4 |
| C6 | Imagen **en el cuerpo** (multipart/related, `cid:`) | 1C 2026 |
| C7 | To, Cc y copia oculta (Bcc) | variante nueva |
| C8 | Entregar al servidor que indica el **MX** | Recu 2026 (descubrir por DNS) |
| C9 | Mandar afuera con **submission + AUTH** | variante nueva |
| C10 | **Quoted-printable** + tildes en el From + dot-stuffing | variante nueva |
| C11 | **Limpiar** un buzón por POP3 (TOP, DELE, QUIT) | variante nueva |
| C12 | Responder **en el mismo hilo** (In-Reply-To) | variante nueva |

## Datos personales / pasárselo a un amigo

Tu legajo, nombre y cuenta quedan en `~/lab-correo/config.json`. El corrector valida contra eso. Si
se lo pasás a alguien, que corra `bash lab-correo.sh config` y ponga **sus** datos (o que borre
`~/lab-correo/config.json` y haga `up`). Los nombres de dominio (`mail.protos.lab`, `empresa.lab`,
etc.) son fijos del lab, iguales para todos.

## Nota

En el parcial los nombres, puertos y servidores son otros (y suele ser `mail.protos.foo` en el 25/110
reales). Acá se usan puertos altos para no pedir sudo ni chocar con servicios del sistema. Lo que
practicás es el **método**: el diálogo SMTP/POP3 y el armado MIME son idénticos.
