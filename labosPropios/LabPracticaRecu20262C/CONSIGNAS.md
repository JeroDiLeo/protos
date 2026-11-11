# Protocolos de Comunicación — Práctica de Recuperatorio

```
72.07 - Protocolos de Comunicación                               Práctica de recu
Nro. de Legajo: ____________
Nombre y Apellido: ______________________________
```

**Condición de aprobación: «obtener 5 puntos»**

|   1   |   2   |   3   |   4   | Total |
|:-----:|:-----:|:-----:|:-----:|:-----:|
| /2.5  | /2.5  | /2.5  | /2.5  |  /10  |

> Tu VM es el contenedor `alumno` (`make ws`). Ya tiene instalado lo que se usa en el parcial (bind9, nginx, netcat, nmap, curl, openssh-client) y `sudo`, `systemctl` y `journalctl` funcionan como en Ubuntu. Trabajás con IPs y nombres reales de la red del lab, nunca contra `localhost` para hablar con otros hosts. Cuando termines, `make corregir`; para empezar de nuevo, `make reset`. Tu legajo de práctica es **62815** (si usás otro, `make corregir leg=NNNNN`).

---

## Ejercicio 1

Envíe un correo electrónico cumpliendo todos los estándares y buenas prácticas, con los siguientes requisitos:

1. Contenga el header `X-Parcial` con el valor `2026/2R`.
2. Contenga un título (`Subject`): `¡Buenos días!`.
3. Contenga como remitente su nombre, apellido y cuenta de correo del ITBA.
4. Contenga el texto `¡Hola mundo!` en negrita.
5. El correo debe entregarse a la dirección `{legajo}@mail.protos.foo`, donde `{legajo}` es su número de legajo.
6. Debe poder ser leído por MUAs que no soporten la codificación quoted-printable.

Debe verificar su recepción utilizando el protocolo POP3. Para ello dispone de un servidor POP3 en el host `mail.protos.foo`. El nombre de usuario es `{legajo}@mail.protos.foo` y la contraseña tiene el mismo valor que el usuario.

---

## Ejercicio 2

En las nubes públicas es común encontrarse con *endpoints* de metadata que proveen información estructurada solo en formato JSON sobre la instancia en la cual se está corriendo. Normalmente se encuentran montados sobre direcciones IP no ruteables y requieren la presencia del header `Metadata: true` para evitar ataques de SSRF (Server Side Request Forgery).

Usted encontró un endpoint de metadata mal configurado disponible públicamente en:

```text
http://metadata.protos.foo
```

Como un hacker curioso, quiere intentar descubrir qué endpoints la nube tiene disponibles y ver qué es posible explotar. Para facilitar las pruebas, y con el objetivo de escribir la menor cantidad de caracteres, desea montar un proxy de forma tal que pueda ejecutar:

```bash
curl http://metadata.local
```

y obtener el contenido de:

```text
http://metadata.protos.foo
```

**Requisito:** no se permiten otras opciones de `curl` al hacer pedidos a `http://metadata.local`.

---

## Ejercicio 3

Instale un servidor de nombres BIND y realice los cambios necesarios para servir la zona `recu.protos.foo` considerando que:

1. Su servidor de DNS será la autoridad para esta zona.
2. La dirección de contacto de la persona responsable de la zona es `admin@recu.protos.foo`.
3. `recu.protos.foo` debe tener un registro A apuntando a la dirección IP de `bar.protos.foo`. El registro tendrá una validez de 1 hora.
4. El subdominio `www` debe ser un CNAME apuntando a la raíz de la zona. El registro tendrá una validez de 2 semanas.
5. La zona debe poder recibir correos electrónicos. El correo será atendido por los mismos servidores de correo que atienden el dominio `mail.protos.foo` (manteniendo el orden). Estos registros tendrán una validez de 1 semana.
6. El servidor con la IP `1.2.3.4` es el único autorizado a enviar correos para esta zona.

Deberá demostrar la correcta configuración utilizando `dig`.

---

## Ejercicio 4

El host `parcial.protos.foo` está corriendo un servidor SSH poco convencional y poco seguro. Usted sabe, por fuentes confiables, que la contraseña del usuario `parcial` es `holamundo`.

Siendo un hacker experimentado, desea poder persistir el acceso al servidor aunque el administrador descubra esta filtración y cambie las credenciales del usuario.

Muestre que, sin importar la contraseña del usuario `parcial`, usted sigue pudiendo acceder al servidor vulnerado.

---

## ⭐ Ejercicio 2-bis (extra, no suma puntos)

Obtenga la representación textual, con media type `text/plain`, en lenguaje español (`es`), del recurso:

```text
http://ejercicio2.protos.foo:8080/foo/
```

usando `curl`.
