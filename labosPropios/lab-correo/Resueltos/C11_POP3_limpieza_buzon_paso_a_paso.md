# C11 — Limpiar un buzón por POP3 sin descargar los cuerpos

Práctica del 8 de noviembre de 2026. **Resultado real: 3/3 verificaciones, aprobado.** Se eliminaron los tres mensajes marcados como spam y quedaron los cuatro legítimos.

## 1. Consigna

El buzón `limpieza@mail.protos.lab` contiene siete mensajes. Tres tienen el encabezado `X-Spam-Flag: YES`. Hay que identificarlos sin descargar sus cuerpos completos, borrarlos y confirmar que quedan cuatro.

Uno de los legítimos tiene un asunto de sorteo: la decisión debe basarse en el encabezado solicitado, no en lo que sugiere el asunto.

## 2. Abrir POP3 y autenticar

En bash:

```bash
nc -C 127.0.0.1 2110
```

- nc abre una conexión TCP.
- -C usa CRLF en la variante de netcat de esta práctica.
- 127.0.0.1 es la máquina local del lab.
- 2110 es el puerto POP3 del lab; el puerto estándar sin TLS implícito es 110.

Diálogo real:

```text
+OK POP3 LabProtos ready
USER limpieza@mail.protos.lab
+OK
PASS limpieza@mail.protos.lab
+OK Logged in. 7 messages
LIST
+OK 7 messages:
1 573
2 594
3 586
4 561
5 573
6 572
7 563
.
```

USER identifica el buzón y PASS autentica. Que la contraseña sea igual a la dirección del buzón es una configuración del laboratorio.

LIST muestra el número y tamaño en octetos de cada mensaje. No muestra asuntos ni permite identificar por sí solo qué correo es spam. El punto termina la respuesta multilínea. +OK indica éxito y -ERR indicaría un error.

## 3. Obtener solo los encabezados

En la misma conexión se ejecutaron uno por uno:

```text
TOP 1 0
TOP 2 0
TOP 3 0
TOP 4 0
TOP 5 0
TOP 6 0
TOP 7 0
```

TOP recibe el número del mensaje y la cantidad de líneas del cuerpo que se desea obtener. El cero pide cero líneas del cuerpo: devuelve los encabezados, suficientes para leer X-Spam-Flag.

No se usó RETR. RETR recuperaría el mensaje completo, incluyendo el cuerpo, y no cumpliría la restricción de identificación de esta consigna.

## 4. Evidencia y decisión

Los siete TOP respondieron +OK. Resumen de los encabezados reales; los asuntos se muestran decodificados para facilitar la lectura:

| Número de esta sesión | Message-ID | Asunto | X-Spam-Flag | Acción |
|---:|---|---|---|---|
| 1 | <seed-10@protos.lab> | Actualización de su cuenta | YES | Borrar |
| 2 | <seed-11@protos.lab> | ¡¡GANASTE!! Sorteo de la cooperadora | NO | Conservar |
| 3 | <seed-12@protos.lab> | Turno de laboratorio confirmado | NO | Conservar |
| 4 | <seed-13@protos.lab> | Reclamá tu premio hoy | YES | Borrar |
| 5 | <seed-14@protos.lab> | Cambio de aula - Protocolos | NO | Conservar |
| 6 | <seed-15@protos.lab> | Verifique su identidad | YES | Borrar |
| 7 | <seed-16@protos.lab> | Notas del parcial | NO | Conservar |

Los mensajes 1, 4 y 6 también tenían X-Spam-Score: 9.1; los demás tenían 0.4. La regla del ejercicio era X-Spam-Flag, por lo que no se necesitó decidir por puntaje ni por asunto.

### Ejemplo real de respuesta de TOP

```text
TOP 1 0
+OK
Return-Path: <semilla@protos.lab>
Received: from semilla (localhost [127.0.0.1])
	by mx1.protos.lab with ESMTP id SEED0010
	for <limpieza@mail.protos.lab>; Sun, 08 Nov 2026 12:21:32 -0300
From: Ventas Online <promo@ofertas.lab>
To: <limpieza@mail.protos.lab>
Subject: =?UTF-8?B?QWN0dWFsaXphY2nDs24gZGUgc3UgY3VlbnRh?=
Date: Sun, 08 Nov 2026 12:21:32 -0300
Message-ID: <seed-10@protos.lab>
X-Spam-Flag: YES
X-Spam-Score: 9.1
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: base64

.
```

La respuesta incluye encabezados MIME que describen el cuerpo, pero no el cuerpo: eso cumple lo pedido. La codificación del Subject es independiente de la codificación del cuerpo. No hizo falta decodificar ninguno para decidir: X-Spam-Flag se veía directamente.

## 5. Marcar los tres mensajes para borrar

Después de revisar todos los encabezados, se indicó ejecutar en esa misma conexión:

```text
DELE 1
DELE 4
DELE 6
```

Se debía esperar +OK después de cada comando. DELE marca un mensaje para borrado dentro de la sesión.

Los números no se renumeran al marcar mensajes en la misma sesión; por eso se conservan 1, 4 y 6. No se debe cambiar a 1, 3 y 4 ni restar números por eliminaciones anteriores.

Las respuestas exactas a DELE no se pegaron en el chat. El corrector posterior confirmó que se eliminaron los tres correctos.

## 6. Confirmar con QUIT

Se indicó cerrar la sesión autenticada mediante:

```text
QUIT
```

QUIT inicia la actualización que confirma las eliminaciones. Cerrar la ventana o perder la conexión no sustituye a QUIT para confirmar este borrado.

No se pegó la respuesta exacta a QUIT; la corrección confirmó el resultado persistente.

Si se marca un mensaje por error y aún se permanece en la sesión, RSET permite quitar las marcas de borrado. Esta es una referencia útil, no un comando que hayamos necesitado ejecutar aquí.

## 7. Corrector: comando y salida reales

El usuario ejecutó el identificador en minúscula y el script lo aceptó:

```bash
bash lab-correo.sh corregir c11
```

bash ejecuta el script, corregir selecciona la acción y c11 identifica el ejercicio.

Salida real:

```text
== Corrección C11 (limpieza del buzón por POP3) ==
  [OK] Borraste los 3 marcados X-Spam-Flag: YES
  [OK] No borraste ninguno legítimo
  [OK] Quedan exactamente 4 mensajes

  Resultado: 3/3 verificaciones bien.  ¡Aprobado!
```

No se realizó una segunda sesión POP3 para contar los mensajes restantes: el corrector confirmó que quedaban exactamente cuatro y que ninguno legítimo había sido eliminado.

## 8. Qué cambia entre sesiones

El número POP3 es una referencia de la sesión, no un identificador permanente. Si se abre otra conexión después de borrar, los mensajes restantes pueden recibir otros números.

Si se interrumpe el procedimiento y hay que reconectar, conviene volver a identificar los correos por sus encabezados y Message-ID antes de enviar DELE. No reutilizar ciegamente los números de la sesión anterior.

## 9. Resumen de comandos

| Comando | Función |
|---|---|
| USER buzón | Identificar la cuenta. |
| PASS contraseña | Autenticar. |
| LIST | Enumerar números de mensaje y tamaños. |
| TOP n 0 | Recuperar encabezados sin líneas del cuerpo. |
| RETR n | Recuperar mensaje completo; no se necesitó en C11. |
| DELE n | Marcar el mensaje n para borrar. |
| RSET | Retirar marcas de borrado en la sesión; no se ejecutó. |
| QUIT | Cerrar y confirmar las eliminaciones de la sesión autenticada. |

## 10. Qué recordar para el examen

1. Si piden decidir sin descargar el cuerpo, TOP n 0 permite inspeccionar encabezados.
2. Aplicar el criterio exacto de la consigna: aquí X-Spam-Flag: YES.
3. No decidir por un asunto llamativo: el sorteo de la cooperadora era legítimo.
4. Mantener los números de mensaje mientras se trabaja dentro de la misma sesión.
5. DELE marca; QUIT confirma.
6. Verificar tanto que se borraron los spam como que se conservaron los legítimos.
