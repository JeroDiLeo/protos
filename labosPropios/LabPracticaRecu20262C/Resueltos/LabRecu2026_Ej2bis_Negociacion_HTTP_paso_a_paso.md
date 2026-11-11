# LabRecu2026 · Ejercicio 2-bis · Negociación de contenido HTTP

## Qué pide la consigna

Obtener con `curl` la representación en texto plano (`text/plain`) y español (`es`) de `http://ejercicio2.protos.foo:8080/foo/`. La misma URL puede devolver distintas representaciones según las preferencias enviadas en el pedido.

## 1. Consultar la representación predeterminada

```text
root@alumno:~# curl -i http://ejercicio2.protos.foo:8080/foo/
HTTP/1.0 200 OK
Server: protos-neg/1.0 Python/3.12.3
Date: Wed, 11 Nov 2026 20:54:26 GMT
Content-Type: text/html; charset=utf-8
Content-Language: es
Content-Length: 95
Vary: Accept, Accept-Language

<!doctype html><html lang=es><body><h1>/foo/</h1><p>Esta es la version HTML.</p></body></html>
```

`curl` hace un GET al recurso `/foo/` en el puerto `8080`. `-i` incluye los encabezados de respuesta junto al cuerpo. El servidor devolvió `200 OK` con HTML y ya eligió español en esta prueba. Para la consigna todavía falta obtener el formato pedido, `text/plain`.

## 2. Pedir explícitamente el formato y el idioma

```bash
curl -i \
  -H 'Accept: text/plain' \
  -H 'Accept-Language: es' \
  http://ejercicio2.protos.foo:8080/foo/
```

- `-H` agrega un encabezado al pedido. Usamos un `-H` por cada preferencia.
- `Accept: text/plain` expresa el **formato que queremos recibir**.
- `Accept-Language: es` expresa el **idioma que queremos recibir**. Lo declaramos porque lo exige la consigna y porque el idioma predeterminado lo elige el servidor.
- `-i` permite comprobar ambas preferencias en los encabezados de respuesta. Las barras invertidas al final de línea permiten continuar el comando en Bash. [Negociación de contenido HTTP](https://www.rfc-editor.org/rfc/rfc9110.html#section-12.5)

Respuesta real:

```text
HTTP/1.0 200 OK
Server: protos-neg/1.0 Python/3.12.3
Date: Wed, 11 Nov 2026 20:54:34 GMT
Content-Type: text/plain; charset=utf-8
Content-Language: es
Content-Length: 101
Vary: Accept, Accept-Language

Recurso /foo/ en texto plano y en espanol.
Lo lograste: negociaste el tipo de contenido y el idioma.
```

| Preferencia que enviamos | Evidencia que devuelve el servidor |
|---|---|
| `Accept: text/plain` | `Content-Type: text/plain; charset=utf-8`. El tipo es texto plano y los caracteres están codificados en UTF-8. |
| `Accept-Language: es` | `Content-Language: es`. El idioma declarado en la respuesta es español. |

`Vary: Accept, Accept-Language` indica que esos encabezados pueden influir en la representación elegida. Le sirve a una caché para distinguir respuestas de la misma URL cuando cambian esas preferencias. [Vary en HTTP](https://www.rfc-editor.org/rfc/rfc9110.html#section-12.5.5)
