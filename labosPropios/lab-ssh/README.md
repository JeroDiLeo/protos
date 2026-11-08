# Lab: clave SSH expuesta + passphrase

Laboratorio aparte, enfocado en un solo tipo de ejercicio de parcial: una clave
privada SSH quedó expuesta, está protegida con passphrase, y hay que **conseguir
la clave, averiguar la passphrase y entrar por SSH**. La passphrase nunca se
rompe por diccionario: siempre es un dato publicado o consultable (un servicio
interno detrás de un proxy, un registro DNS, etc.).

Son 3 ejercicios de dificultad creciente. Todo corre en `127.0.0.1`: no toca
internet ni la red del laboratorio.

## Primera vez (paso a paso)

> **Todo DENTRO de la VM**, como tu **usuario normal** (NO `sudo bash`).

1. Creá una carpeta y poné ahí `lab-ssh.sh`, `consignas.md` y `README.md`:
   ~~~bash
   mkdir -p ~/lab-ssh-practica && cd ~/lab-ssh-practica
   ls   # tienen que estar los tres archivos
   ~~~
2. Instalá lo que usa el lab (una vez):
   ~~~bash
   sudo apt update
   sudo apt install -y python3 curl dnsutils openssh-server openssh-client
   ~~~
3. Levantá el entorno:
   ~~~bash
   bash lab-ssh.sh up
   ~~~
   Pide sudo solo para iniciar el sshd y usa tu cuenta para autorizar las claves
   de práctica (se sacan con `down`).
4. Abrí las consignas y resolvé:
   ~~~bash
   cat consignas.md
   ~~~
5. Al terminar, apagá y limpiá:
   ~~~bash
   bash lab-ssh.sh down
   ~~~

## Uso

~~~bash
bash lab-ssh.sh up        # levanta los servidores y autoriza las claves
bash lab-ssh.sh status    # qué está corriendo
bash lab-ssh.sh down      # apaga todo y saca las claves de practica de tu cuenta
~~~

## Qué levanta

| Servicio | Dónde | Para qué |
|---|---|---|
| HTTP estático | `http://127.0.0.1:8060/` | sirve las claves expuestas y las pistas |
| Reverse proxy | `http://127.0.0.1:8061/` | `server_name secrethost` → servicio interno |
| Servicio interno | `127.0.0.1:9061` | entrega passphrases; solo accesible vía proxy |
| DNS de referencia | `127.0.0.1:5360` (UDP) | registros A y TXT con pistas |

## Diferencia con tu VM y con el parcial

- En el parcial el usuario SSH te lo dan (`pepito`); acá entrás con **tu propio
  usuario**: `ssh -i <clave> $USER@localhost`.
- La primera vez que hagas `ssh ... localhost` te va a pedir confirmar la huella
  del host: escribí `yes`.
- Si `ssh` se queja de permisos de la clave, acordate del `chmod 600`.

## Nota técnica

Los "servidores del otro lado" están implementados en Python (no hace falta
instalar nginx ni bind), para que lo puedas pasar a un compañero y le funcione
solo con `python3`, `curl`, `dig` y `openssh`. El método que practicás es el
mismo del parcial; los puertos son altos para no chocar con servicios reales.
