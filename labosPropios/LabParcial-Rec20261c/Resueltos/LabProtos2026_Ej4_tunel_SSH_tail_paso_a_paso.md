# LabProtos2026 · Ejercicio 4 · Seguir un archivo remoto por un túnel SSH

> **Primero, mejor leé la resolución del repo de Keo.** Esta guía complementa esa lectura con la prueba que hicimos en la workstation y el criterio para elegir entre un túnel local y uno remoto.

## Qué pide el ejercicio

Desde la workstation, ejecutar `tail -f archivo.log` y ver en vivo las líneas que se agregan a `/tmp/parcial-20261` en `pampero.itba.edu.ar`. La solución debe usar un túnel SSH para obtener el puntaje completo. Para el puerto elegimos `63051`, el legajo.

| Lugar | Archivo o puerto | Qué hace |
|---|---|---|
| Pampero | `/tmp/parcial-20261` | Es el archivo remoto que genera los datos. |
| Pampero | `127.0.0.1:63051` | El netcat remoto escucha y entrega las líneas nuevas al túnel. |
| Workstation | `127.0.0.1:63051` | SSH escucha en este puerto local y reenvía la conexión a Pampero. |
| Workstation | `archivo.log` | El netcat local guarda lo que recibe. El `tail -f` de la consigna mira este archivo. |

## Cómo decidir entre un túnel local y uno remoto

Antes de elegir la opción, ubicá **desde qué máquina ejecutás `ssh`** y **desde qué máquina se va a conectar el programa que usa el túnel**. En este lab ejecutamos `ssh` en la workstation, así que la workstation es el lado local y Pampero es el lado remoto. Para elegir la opción, la pregunta es **¿en qué lado tiene que escuchar SSH para recibir esa conexión?**

| Si el enunciado pide… | Dónde tiene que escuchar SSH | Qué opción usar |
|---|---|---|
| «Desde mi máquina, conectarme a un servicio que corre en Pampero» o «quiero entrar por `localhost` de mi máquina a un servicio remoto». | En la workstation. La aplicación que usa el túnel se conecta a un puerto de la workstation. | `-L`. Pampero abre la conexión al servicio de destino. |
| «Desde Pampero, acceder a un servicio que corre en mi máquina» o «quiero que Pampero pueda conectarse a su propio `localhost` y llegar a mi servicio». | En Pampero. La aplicación que usa el túnel se conecta a un puerto de Pampero. | `-R`. La workstation abre la conexión al servicio de destino. |

En este ejercicio, la consigna nos dice que queremos **seguir el archivo desde la workstation**. Armamos la solución para que Pampero ofrezca las líneas por un `nc -l`, y para que el `nc` de la workstation **inicie la conexión** al puerto del túnel. Por eso usamos `-L`. El `tail -f archivo.log` solo lee el archivo local. El programa que se conecta al túnel es `nc`.

Acá la conexión la inicia la workstation y las líneas viajan de Pampero a la workstation por esa misma conexión. **Local y remoto describen dónde escucha SSH**, y una conexión TCP permite que los bytes viajen en ambos sentidos. Si el enunciado solo menciona dónde está el archivo, todavía hay que decidir qué proceso va a escuchar y cuál se va a conectar.

### Ejemplo de un enunciado que pide `-R`

Supongamos que el enunciado dice «desde Pampero, hacé `curl http://127.0.0.1:63051` y obtené la página del servidor HTTP que corre en el puerto `8080` de tu workstation». El `curl` corre en Pampero, así que el puerto `63051` tiene que escuchar **en Pampero**. Si el servidor HTTP escucha en `127.0.0.1:8080` de la workstation, podés abrir el túnel desde la workstation con este comando.

```bash
ssh -R 127.0.0.1:63051:127.0.0.1:8080 alumno@pampero.itba.edu.ar
```

En `-R`, el primer `127.0.0.1:63051` corresponde a **Pampero** y el segundo `127.0.0.1:8080` corresponde a **la workstation**. En el `-L` de nuestro ejercicio, esas máquinas aparecen en el orden inverso. [Manual de OpenSSH para `-L` y `-R`](https://man.openbsd.org/ssh)

## 1. Entrar a Pampero y comprobar el archivo

Desde el host, `make ws` abre una shell dentro de la workstation. También se puede usar `docker compose exec workstation bash` desde la carpeta del lab.

```bash
ssh alumno@pampero.itba.edu.ar
```

Extracto de la sesión real

```text
root@workstation:/# ssh alumno@pampero.itba.edu.ar

The programs included with the Debian GNU/Linux system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Debian GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent
permitted by applicable law.
alumno@a5a95f117b41:~$
```

El cambio de prompt indica que ahora los comandos se ejecutan en Pampero como `alumno`. El laboratorio instala su propia clave en la workstation y autoriza la pública correspondiente en Pampero. Si necesitás diagnosticar un error de clave, desde la workstation podés probar `ssh -v -i /root/.ssh/id_ed25519 -o IdentitiesOnly=yes alumno@pampero.itba.edu.ar`. En la sesión de práctica el comando simple finalmente abrió la sesión.

Primero usamos `tail -n 3` para mirar las últimas tres líneas y recuperar el prompt. Como no imprimió nada, medimos el tamaño con `wc -c` y agregamos una línea para confirmar que podíamos escribir y leer el archivo correcto.

```text
alumno@a5a95f117b41:~$ tail -n 3 /tmp/parcial-20261
alumno@a5a95f117b41:~$ wc -c /tmp/parcial-20261
0 /tmp/parcial-20261
alumno@a5a95f117b41:~$ echo "Prueba desde Pampero" >> /tmp/parcial-20261
alumno@a5a95f117b41:~$ tail -n 3 /tmp/parcial-20261
Prueba desde Pampero
```

El archivo tenía `0` bytes en esta sesión, así que usamos escrituras manuales para probar el seguimiento. `>>` agrega una línea al final del archivo y conserva las anteriores.

## 2. Terminal A · Escuchar en Pampero

En la sesión remota que ya abrimos, dejamos corriendo:

```bash
tail -n 0 -f /tmp/parcial-20261 | nc -l 127.0.0.1 63051
```

- `tail -n 0` arranca sin emitir líneas anteriores. `-f` lo deja esperando lo que se agregue al archivo.
- `|` lleva la salida de `tail` a la entrada de `nc`.
- `nc -l 127.0.0.1 63051` pone a netcat en modo escucha en el loopback de **Pampero**. Como el comando se ejecuta en ese servidor, ese `127.0.0.1` es el remoto.
- La terminal queda ocupada. Las líneas nuevas van al pipe, así que esperamos verlas al otro extremo de la conexión.

## 3. Terminal B · Abrir el túnel desde la workstation

Abrimos otra terminal en la workstation con `make ws` y ejecutamos:

```bash
ssh -o ExitOnForwardFailure=yes \
  -L 127.0.0.1:63051:127.0.0.1:63051 \
  alumno@pampero.itba.edu.ar
```

La forma de `-L` es `dirección_local:puerto_local:destino_desde_Pampero:puerto_destino`. La **L** indica que el puerto que abre SSH para recibir conexiones queda del lado local.

| Parte de `-L` | Cómo se lee |
|---|---|
| Primer `127.0.0.1:63051` | SSH abre un puerto en el loopback de la **workstation**. Ahí se va a conectar el netcat local. |
| Segundo `127.0.0.1:63051` | Cuando alguien se conecta al puerto local, el servidor SSH se conecta al loopback de **Pampero**. Ahí está el netcat remoto. |

Reutilizar el número `63051` funciona porque los puertos pertenecen a dos máquinas distintas. `ExitOnForwardFailure=yes` hace que SSH termine si falla al instalar el reenvío, por ejemplo si el puerto local ya está ocupado. La conexión al listener de Pampero ocurre cuando el netcat local usa el túnel.

La sesión B además queda con un prompt remoto. Lo usamos para escribir las líneas de prueba mientras el túnel sigue abierto. Si solo quisieras mantener abierto el túnel, `ssh -N -L ...` prescindiría de la shell remota.

## 4. Terminales C y D · Guardar los datos y seguir el archivo

En una terminal nueva de la workstation, ejecutamos:

```bash
nc 127.0.0.1 63051 > archivo.log
```

Este `nc` funciona como cliente. Se conecta al puerto local que abrió SSH. Las líneas llegan desde Pampero por esa conexión, y `>` las escribe en el archivo local. La redirección crea el archivo o lo deja vacío al iniciar la prueba si ya existía.

En otra terminal de la workstation, desde el **mismo directorio** en el que se abrió `archivo.log`, ejecutamos lo que pide la consigna:

```bash
tail -f archivo.log
```

En la práctica el prompt era `root@workstation:/#`, así que el archivo relativo `archivo.log` se refiere a `/archivo.log`. Cada `tail` tiene su tarea. El remoto produce las líneas nuevas y el local muestra lo que llega al archivo de la workstation.

## 5. Generar un cambio y ver que llega

Con las terminales anteriores abiertas, desde el prompt de Pampero de la **terminal B** se puede agregar la marca de prueba:

```bash
echo "Esta línea viajó por el túnel SSH" >> /tmp/parcial-20261
```

Salida real en la terminal que miraba el archivo local

```text
jerodileo@jerOS:~/Documents/protoslaboratorios/LabProtos2026$ make ws
root@workstation:/# tail -f archivo.log
Esta línea viajó por el túnel SSH
Esta linea viajo por el tunel SSH
```

La evidencia es que las dos líneas aparecen en el `tail -f` que corre en la **workstation**. La primera línea de prueba, `Prueba desde Pampero`, se había escrito antes de arrancar el `tail -n 0 -f` remoto. Por eso usamos una marca distinta al comprobar el seguimiento.

Para cerrar la prueba, podés interrumpir con `Ctrl+C` el seguimiento local y el netcat local, salir de la sesión SSH que mantiene el túnel con `exit` y terminar el listener remoto si todavía está abierto.
