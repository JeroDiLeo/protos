# Protocolos — 1C 2026, ejercicio 4: túnel SSH y tail
## Consigna y resultado
Desde mi host, tail -f archivo.log debe seguir /tmp/parcial-20261 de pampero.itba.edu.ar, usando un túnel SSH y el legajo como puerto.

Datos reales: usuario jdileomuntaner; legajo/puerto 63051.
Se recibió el contenido original por el túnel. Como el archivo no crecía, se crearon cinco líneas en un archivo remoto propio y el estudiante confirmó que llegaron al tail local. Práctica realizada en Pampero real; no se necesitó un sshd local.

## ⭐ RECETA PARA EL PARCIAL (leer esto primero)

> Estos comandos se probaron contra el **pampero real** con mis datos. En el parcial solo cambia lo marcado. Lo de `mktemp` y el bucle `for` (secciones 4 y 5) fue para demostrar en la práctica porque el archivo no crecía: **no hace falta en el parcial**.

### Datos que pueden cambiar
| Dato | En esta práctica | Dónde se usa |
|---|---|---|
| Usuario | `jdileomuntaner` | paso 1 |
| Host | `pampero.itba.edu.ar` | paso 1 |
| Puerto (= legajo) | `63051` | pasos 1, 2 y 3 (el **mismo** número en los tres) |
| Archivo remoto | `/tmp/parcial-20261` | paso 2 |
| Archivo local | `archivo.log` | pasos 3 y 4 |

### Los 4 pasos, en este orden
~~~bash
# TERMINAL 1 (mi máquina): abre el túnel y deja una shell en pampero
ssh -L 63051:127.0.0.1:63051 jdileomuntaner@pampero.itba.edu.ar

# EN ESA MISMA SESIÓN (ya estoy en pampero): publica el archivo en el puerto
tail -F /tmp/parcial-20261 | nc -l 127.0.0.1 63051

# TERMINAL 2 (mi máquina): se conecta a la entrada del túnel y guarda
nc 127.0.0.1 63051 > archivo.log

# TERMINAL 3 (mi máquina): lo que pide la consigna
tail -f archivo.log
~~~

**El orden importa:** el listener de pampero (paso 2) tiene que estar escuchando **antes** de conectar el receptor (paso 3). Si lo hacés al revés, el paso 3 termina enseguida y `archivo.log` queda vacío.

### Por qué funciona (para explicar en el video)
- `-L 63051:127.0.0.1:63051`: abre el puerto 63051 **en mi máquina**; lo que entra ahí viaja cifrado por SSH y pampero lo entrega a `127.0.0.1:63051` **visto desde pampero** (su propio loopback).
- `tail -F ... | nc -l 127.0.0.1 63051`: `tail -F` sigue el archivo aunque lo roten o recreen; el pipe le pasa cada línea nueva a `nc`, que espera una conexión en ese puerto.
- `nc 127.0.0.1 63051 > archivo.log`: acá `127.0.0.1` es **mi** máquina, la entrada del túnel. Lo que llega se guarda en el archivo.
- `tail -f archivo.log`: muestra en vivo lo que se va agregando.
- Recorrido: tail remoto → nc remoto → túnel SSH → nc local → archivo.log → tail local.

Frase de cierre: "Abro con `ssh -L` el puerto de mi legajo hacia el loopback de pampero, publico ahí la salida de `tail -F` con netcat, la recibo por el túnel en `archivo.log` y la sigo con `tail -f`."

### Checklist si algo falla
| Síntoma | Causa probable | Arreglo |
|---|---|---|
| `nc -l` da error de uso en pampero | otra variante de netcat | `nc -h`: OpenBSD → `nc -l 127.0.0.1 PUERTO`; traditional → `nc -l -p PUERTO` |
| `bind: Address already in use` al abrir el túnel | el puerto ya está ocupado en mi máquina (otro ssh abierto) | cerrar el ssh anterior o `ss -ltnp \| grep 63051` |
| `nc -l` dice address in use en pampero | otro proceso (o compañero) usa ese puerto | usar otro puerto y cambiarlo en los 3 lugares |
| paso 3 termina enseguida, archivo vacío | el listener no estaba levantado o ya atendió una conexión | volver a correr el paso 2 y después el 3 |
| `channel N: open failed: connect failed` en la terminal 1 | el túnel funciona pero en pampero nadie escucha | levantar el paso 2 |
| no aparecen líneas nuevas | el archivo no está creciendo | `stat /tmp/parcial-20261` y mirar `Modify` |
| se cortó todo | se cerró la sesión SSH de la terminal 1 | el túnel vive mientras viva esa sesión: reabrirla |

### Versión sin túnel (vale la mitad): solo como último recurso
~~~bash
ssh jdileomuntaner@pampero.itba.edu.ar 'tail -f /tmp/parcial-20261' > archivo.log   # terminal 1
tail -f archivo.log                                                               # terminal 2
~~~
Funciona, pero no usa reenvío de puertos, así que no cumple la consigna completa.

---

# PRÁCTICA (detalle de lo que se ejecutó)

## 1. Versión sin reenvío de puertos
En la máquina local:
~~~bash
ssh jdileomuntaner@pampero.itba.edu.ar 'tail -f /tmp/parcial-20261' > archivo.log
~~~
ssh autentica y ejecuta el comando remoto entre comillas; usuario@host selecciona cuenta y servidor. tail muestra diez últimas líneas; -f continúa siguiendo lo agregado. La redirección > es interpretada localmente: crea o vacía archivo.log y guarda la salida recibida. No escribe en el archivo remoto.

En otra terminal local:
~~~bash
tail -f archivo.log
~~~
El programa sigue el archivo local mientras el primer comando lo actualiza. Ambos quedan ejecutándose; Ctrl+C los detiene. Aunque SSH cifra la sesión, no hay reenvío de puertos -L, por lo que no cumple el requisito de túnel de la consigna.

## 2. Solución con túnel: cuatro comandos
### Terminal 1 local: abrir túnel y sesión
~~~bash
ssh -L 63051:127.0.0.1:63051 jdileomuntaner@pampero.itba.edu.ar
~~~
-L significa reenvío local:
- Primer 63051: puerto abierto en el cliente SSH, mi máquina.
- 127.0.0.1: destino visto desde el servidor SSH; es el loopback de Pampero.
- Último 63051: puerto de destino en Pampero.
- usuario@host: sesión SSH de transporte.

El cliente nc se conectará en mi máquina: por eso -L. No se elige por la dirección del contenido; TCP transporta en ambos sentidos.
La forma explícita para limitar el listener local a IPv4 loopback es:
~~~bash
ssh -L 127.0.0.1:63051:127.0.0.1:63051 jdileomuntaner@pampero.itba.edu.ar
~~~

### En esa sesión de Pampero: exponer las líneas
Primero se identificó netcat:
~~~bash
nc -h
~~~
-h muestra ayuda. Resultado: OpenBSD netcat (Debian patchlevel 1.238-1).

~~~bash
tail -F /tmp/parcial-20261 | nc -l 127.0.0.1 63051
~~~
-F sigue por nombre y reintenta si desaparece; equivale en GNU tail a --follow=name --retry. -f sigue por descriptor de forma predeterminada: al reemplazar el archivo puede seguir el antiguo.
| pasa salida de tail a entrada de nc.
nc -l espera una conexión; 127.0.0.1 restringe escucha al loopback remoto; 63051 es el puerto del servicio. El proceso queda esperando, no muestra datos en pantalla.

### Terminal 2 local: recibir
~~~bash
nc 127.0.0.1 63051 > archivo.log
~~~
Sin -l, nc conecta. Esta dirección 127.0.0.1 es la máquina local, no Pampero. El puerto es la entrada del túnel. > guarda los bytes y vacía cualquier contenido previo. No ejecutar en Pampero.

### Terminal 3 local: visualizar
~~~bash
tail -f archivo.log
~~~
Ejecutar en el mismo directorio que el receptor. Mantener los tres procesos abiertos.

Recorrido: tail remoto → nc remoto → canal SSH → nc local → archivo.log → tail local.
La conexión se inicia en sentido local hacia remoto; las líneas vuelven por esa conexión.

## 3. Puerto, IP y variantes de nc
63051 está en 1–65535; es mayor que 1023, normalmente utilizable sin root. El puerto 0 no sirve como número fijo de este ejercicio. El puerto debe estar libre en cada lado. Si el legajo supera 65535, no cabe en TCP: aclarar la situación y acordar un puerto válido; no truncarlo silenciosamente.

| Implementación | Listener |
|---|---|
| OpenBSD netcat, confirmado en Pampero | nc -l 127.0.0.1 63051 |
| netcat-traditional | nc -l -p 63051 |
| Traditional con dirección local explícita, si la versión lo permite | nc -l -s 127.0.0.1 -p 63051 |

En traditional, -p fija el puerto local; -s selecciona dirección local. Consultar nc -h de esa máquina. No mezclar sintaxis con OpenBSD. En la VM no se registró su versión: el cliente nc funcionó; para identificarlo, ejecutar localmente nc -h.

Sin -k, el listener OpenBSD usado acepta una conexión. Al terminar nc no se destruye necesariamente SSH: el túnel vive mientras viva la sesión. Repetir el listener y luego el receptor. nc -k permite nuevas conexiones en OpenBSD, pero no garantiza un replay ni convierte este flujo en un servicio robusto con historial.

## 4. Diagnóstico del archivo que no crecía
Se recibieron estas últimas líneas:
~~~text
linea 13:13:57
...
linea 13:14:15
~~~
No aparecían nuevas. Se consultó:
~~~bash
ssh jdileomuntaner@pampero.itba.edu.ar 'stat /tmp/parcial-20261'
~~~
stat informa metadatos. Resultado:
- Size: 10770.
- Modify: 2026-10-25 13:14:15.
- Propietario: ldesmery; permisos 0644 (-rw-r--r--).

El archivo estaba detenido desde el día anterior. 0644 permite escribir solo al propietario y leer a grupo/resto. La pertenencia al curso no concede escritura. chmod sobre archivo ajeno requiere ser propietario o tener privilegios; para la consigna solo hace falta lectura.

## 5. Demostración real con archivo propio
Se detuvo el pipeline remoto con Ctrl+C, conservando SSH. Se creó:
~~~bash
mktemp /tmp/parcial-63051.XXXXXX
~~~
mktemp crea un archivo nuevo y privado; reemplaza X por caracteres aleatorios.
Resultado real: /tmp/parcial-63051.AGjSHB.

En Pampero:
~~~bash
tail -F /tmp/parcial-63051.AGjSHB | nc -l 127.0.0.1 63051
~~~
Se volvió a ejecutar el receptor local y tail local con los comandos anteriores. En una cuarta terminal local:
~~~bash
ssh jdileomuntaner@pampero.itba.edu.ar 'for n in 1 2 3 4 5; do date "+linea %H:%M:%S" >> /tmp/parcial-63051.AGjSHB; sleep 2; done'
~~~
for recorre cinco valores; do/done delimitan cuerpo; date produce hora remota con prefijo linea; >> agrega sin pisar; sleep 2 espera dos segundos; los ; separan instrucciones. Las comillas externas hacen ejecutar bucle y redirección en Pampero.
El estudiante confirmó: «si, cayeron 5». Esto prueba el seguimiento en vivo por el túnel con un archivo controlado.

## 6. Cierre realizado
Ctrl+C detuvo el pipeline remoto. En Pampero:
~~~bash
rm /tmp/parcial-63051.AGjSHB
~~~
rm borró únicamente el archivo propio de práctica. El original del compañero se conservó.
Luego:
~~~bash
exit
~~~
exit cerró la sesión SSH que transportaba el túnel. Ctrl+C detuvo tail y cualquier nc local aún abierto.
archivo.log queda como archivo local; no mantiene servicios activos.

## 7. Variantes: qué cambia y qué línea tocar
Ejemplos para estudiar, no cambios ejecutados:
| Cambio | Comando o fragmento |
|---|---|
| Otro archivo remoto | tail -F /ruta/otro.log &#124; nc -l 127.0.0.1 63051 |
| Otro puerto de túnel y servicio | ssh -L 64000:127.0.0.1:64000 jdileomuntaner@pampero.itba.edu.ar |
| Adaptar listener/receptor | nc -l 127.0.0.1 64000 en remoto; nc 127.0.0.1 64000 > archivo.log en local |
| Otro usuario/host | ssh -L 63051:127.0.0.1:63051 otro@servidor |
| Servicio interno visto por Pampero | ssh -L 63051:10.20.0.8:8080 jdileomuntaner@pampero.itba.edu.ar |
| Servicio local 8080 accesible desde Pampero | ssh -N -R 127.0.0.1:63051:127.0.0.1:8080 jdileomuntaner@pampero.itba.edu.ar |
| Proxy SOCKS con salida desde Pampero | ssh -N -D 127.0.0.1:1080 jdileomuntaner@pampero.itba.edu.ar |
| Usarlo con curl | curl -x socks5h://127.0.0.1:1080 http://destino |
| Copiar archivo, sin seguimiento | scp jdileomuntaner@pampero.itba.edu.ar:/tmp/parcial-20261 ./archivo.log |
| SSH en otro puerto | ssh -p 2222 usuario@host |
| scp en otro puerto | scp -P 2222 usuario@host:/ruta/archivo ./ |
| Abortar si no se puede abrir el forward | ssh -o ExitOnForwardFailure=yes -L 63051:127.0.0.1:63051 usuario@host |

-R abre escucha en servidor SSH y conecta al destino desde el cliente. -D crea un SOCKS local con destinos elegidos por conexión; socks5h delega resolución del destino a ese proxy.
scp copia una instantánea; -P mayúscula selecciona puerto en scp, -p minúscula lo hace en ssh.
ExitOnForwardFailure no garantiza que nc remoto ya esté disponible; comprueba la creación del forward.

### -N, -f y otras opciones que pueden aparecer
-N evita ejecutar un comando remoto. -f manda SSH al fondo tras autenticar. Para un servicio remoto ya iniciado:
~~~bash
ssh -f -N -L 63051:127.0.0.1:63051 jdileomuntaner@pampero.itba.edu.ar
~~~
No conviene en nuestra sesión principal porque necesitamos la shell para correr tail | nc. Se podría usar otra sesión para el servicio.
-i selecciona una clave privada; -o establece una opción de configuración; -t solicita pseudo-terminal; -l usuario selecciona cuenta como alternativa a usuario@host. No necesitamos -t para transportar datos crudos. -F de ssh selecciona otro archivo de configuración; no confundir con -F de tail.

### Dar salida a aplicaciones de un host sin NAT mediante -D y -R
Supuesto: desde una máquina A con internet se puede iniciar SSH hacia B, sin NAT. A tiene un servidor SSH local disponible. Son dos sesiones:
En A, terminal 1:
~~~bash
ssh -N -D 127.0.0.1:1080 usuarioA@127.0.0.1
~~~
Crea SOCKS local cuya salida se realiza desde A.
En A, terminal 2:
~~~bash
ssh -N -R 127.0.0.1:1081:127.0.0.1:1080 usuarioB@B
~~~
Abre 1081 en B y lo lleva al SOCKS 1080 de A.
En B:
~~~bash
ALL_PROXY=socks5h://127.0.0.1:1081 curl https://example.com
~~~
ALL_PROXY afecta a esa ejecución; variables de proxy por protocolo y NO_PROXY pueden prevalecer. Esto da salida a aplicaciones que usan SOCKS, no configura NAT ni conectividad IP general. Si A no puede conectar por SSH con B, esta topología debe cambiar: sin NAT no significa automáticamente sin acceso SSH.

## Justificación para el parcial
“Abro el puerto local 63051 con SSH -L hacia el listener de Pampero, transporto por ese túnel la salida de tail remoto y la guardo en archivo.log para seguirla con tail -f.”

## Guardar en la VM
Descargar el archivo. Si está en Downloads:
~~~bash
mkdir -p ~/protos/soluciones
~~~
mkdir crea directorios; -p crea padres faltantes.
~~~bash
cp ~/Downloads/26.1-4.md ~/protos/soluciones/26.1-4.md
~~~
cp copia origen a destino; ~ es tu directorio personal.

## Referencias
- [Cliente SSH](https://man.openbsd.org/ssh)
- [OpenBSD netcat](https://man.openbsd.org/nc)

