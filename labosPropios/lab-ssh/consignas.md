# Consignas — Clave SSH expuesta + passphrase

Tres ejercicios estilo parcial. En todos el objetivo es el mismo: una clave
privada SSH quedó expuesta, está protegida con una **passphrase**, y hay que
**conseguir la clave, averiguar la passphrase y hacer login por SSH**.

La passphrase **nunca** se rompe por fuerza bruta ni diccionario: siempre es un
dato que está publicado o que se puede consultar en el entorno. Hay que
encontrarlo.

> Levantá todo con `bash lab-ssh.sh up` (dentro de tu VM, como tu usuario).
> Para entrar vas a usar tu propio usuario: `ssh -i <clave> TU_USUARIO@localhost`.
> En un parcial real el usuario te lo da el enunciado (por ejemplo, `pepito`).

## Datos del entorno

| Servicio | Dónde | Notas |
|---|---|---|
| HTTP estático | `http://127.0.0.1:8060/` | sirve archivos; tiene un `root` web |
| Reverse proxy | `http://127.0.0.1:8061/` | `server_name secrethost` |
| Servicio interno | `127.0.0.1:9061` | **no accesible directo**; solo vía el proxy |
| DNS de referencia | `127.0.0.1:5360` (UDP) | `dig @127.0.0.1 -p 5360 <nombre> <tipo>` |

Cuando termines: `bash lab-ssh.sh down` (apaga todo y saca las claves de prueba de tu cuenta).

---

## Ejercicio 1 — La clave y el panel interno

El host `127.0.0.1` tiene un servidor nginx con **dos** server configurados:

```
server {
    listen 8060;
    root /var/www;
    location / { try_files $uri $uri/ =404; }
}

server {
    listen 8061;
    server_name secrethost;
    location / { proxy_pass http://127.0.0.1:9061/; }
}
```

Además corre un OpenSSH que solo acepta login por **clave privada**.

Sabemos que la clave privada quedó guardada en `/var/www/sec/mykey1`, pero su
dueño le puso una passphrase. Por algún lado de la infraestructura esa
passphrase quedó accesible.

**Se pide:** extraiga la clave, averigüe la passphrase y haga login por SSH.
Justifique por qué el servicio interno no es alcanzable de forma directa y cómo
llegó a él.

---

## Ejercicio 2 — La clave escondida y el registro DNS

El mismo servidor HTTP del puerto `8060` publica archivos, pero esta vez la
ruta de la clave **no se conoce de entrada**: el administrador creyó que, por no
estar enlazada, nadie la encontraría.

Se sabe, además, que la passphrase de esa clave fue "documentada" por el equipo
de redes como la **dirección IP** del nombre `llave.internal.lab`, consultable
en el servidor DNS de referencia.

**Se pide:** descubra dónde está publicada la clave privada, extráigala,
averigüe la passphrase a partir del DNS y haga login por SSH. Indique qué pista
lo llevó a la ubicación del archivo.

---

## Ejercicio 3 — Doble salto: vhost + token + proxy

La infraestructura se endureció. Ahora:

- La clave privada (`mykey3`) se sirve por HTTP en el puerto `8060`, pero el
  servidor **solo la entrega si el pedido llega con el nombre de host correcto**
  (`archivos.lab`). Con la IP directa responde 404.
- La passphrase está detrás del **servicio interno**, accesible solo a través
  del proxy `secrethost` (puerto `8061`), en la ruta `/clave`. Pero esa ruta
  exige un parámetro `token` en la URL.
- El valor del `token` está publicado en un registro **TXT** del DNS, bajo el
  nombre `token.internal.lab`.

**Se pide:** obtenga la clave usando el host virtual correcto, consiga el token
desde el DNS, úselo para que el servicio interno le entregue la passphrase, y
haga login por SSH. Escriba la cadena completa de comandos que usó, en orden.

---

## Cómo trabajar

1. Resolvé un ejercicio probando comandos; anotá qué devuelve cada paso.
2. Antes de intentar el `ssh`, podés verificar la passphrase sin conectarte:
   `ssh-keygen -y -f <clave>` — si es correcta, imprime la clave pública.
3. Cuando lo tengas (o si te trabás), contale a quien te está ayudando qué
   comandos usaste y qué respuesta recibiste.
