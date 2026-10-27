# DNS: registros y zonas que no salieron en los parciales vistos (por las dudas)

Complemento de `zona-foo-example-org_1c2026.md`, que ya cubre SOA, NS, A, AAAA, CNAME, MX, SPF, TTL, responsable con punto y "que se propague rápido". Acá van los casos que **podrían** pedir cambiando el enunciado. Todo pasó `named-checkzone` (BIND 9).

El procedimiento es el mismo de siempre: editar zona → subir serial → `named-checkzone` → `named-checkconf` → `systemctl restart bind9` → `dig @127.0.0.1`.

---

## ⭐ Regla rápida

| El enunciado pide… | Registro | Línea |
|---|---|---|
| "resolución inversa", "que la IP X resuelva al nombre" | PTR en una **zona inversa** | ver 1 |
| "delegue el subdominio `sub` al servidor Y" | NS + glue | ver 2 |
| "cualquier subdominio resuelva a…" | comodín `*` | `* IN A 192.0.2.10` |
| "servicio SIP/XMPP/LDAP en el puerto…" | SRV | ver 3 |
| "solo esta CA puede emitir certificados" | CAA | `@ IN CAA 0 issue "letsencrypt.org"` |
| un texto cualquiera | TXT | `@ IN TXT "lo que pidan"` |
| IPv6 | AAAA | `@ IN AAAA 2001:db8::10` |

---

## 1. Zona inversa (PTR)

Para la red `192.0.2.0/24` la zona se llama `2.0.192.in-addr.arpa`: los tres primeros octetos **al revés** + `.in-addr.arpa`.

`/etc/bind/named.conf.local`:
~~~conf
zone "2.0.192.in-addr.arpa" {
    type master;
    file "/etc/bind/db.192.0.2";
};
~~~
`/etc/bind/db.192.0.2`:
~~~dns
$TTL 1h
@   IN SOA ns.foo.example.org. admin.foo.example.org. ( 2026102701 1h 15m 1w 1h )
@   IN NS  ns.foo.example.org.
10  IN PTR foo.example.org.
20  IN PTR sip.foo.example.org.
~~~
- `10` = el último octeto: `192.0.2.10` → `foo.example.org.`
- El destino del PTR siempre lleva **punto final**.

Validar y probar:
~~~bash
sudo named-checkzone 2.0.192.in-addr.arpa /etc/bind/db.192.0.2
dig @127.0.0.1 -x 192.0.2.10
~~~
`dig -x IP` arma solo la pregunta `10.2.0.192.in-addr.arpa PTR`.

---

## 2. Delegar un subdominio (NS + glue)

"El subdominio `sub.foo.example.org` lo administra el servidor `ns.sub.foo.example.org` (192.0.2.53)":
~~~dns
sub      IN NS  ns.sub.foo.example.org.
ns.sub   IN A   192.0.2.53          ; "glue": sin esto nadie puede encontrar al NS
~~~
`named-checkzone` muestra este aviso, que **no es error** (termina en OK):
~~~text
sub.foo.example.org/NS 'ns.sub.foo.example.org' (out of zone) has no addresses records (A or AAAA)
~~~
Probar: `dig @127.0.0.1 sub.foo.example.org NS` responde con una **referencia** (sección AUTHORITY, sin `aa`). Es lo esperado: tu servidor ya no es la autoridad de `sub`.

---

## 3. SRV

Formato: `_servicio._protocolo  IN SRV  prioridad peso puerto destino.`
~~~dns
_sip._tcp IN SRV 10 5 5060 sip.foo.example.org.
sip       IN A   192.0.2.20
~~~
Probar: `dig @127.0.0.1 _sip._tcp.foo.example.org SRV`.

---

## 4. Comodín
~~~dns
*   IN A 192.0.2.10
~~~
Cualquier nombre que **no exista** explícitamente (`loquesea.foo.example.org`) responde esa IP. Los que sí existen (`www`, `ns`) responden lo suyo. Probar con `dig @127.0.0.1 inventado.foo.example.org`.

---

## Archivo de prueba completo (validado)
~~~dns
$ORIGIN foo.example.org.
$TTL 1h
@ IN SOA ns.foo.example.org. admin.foo.example.org. ( 2026102701 1h 15m 1w 1h )
@        IN NS    ns.foo.example.org.
ns       IN A     127.0.0.1
@        IN A     192.0.2.10
@        IN AAAA  2001:db8::10
*        IN A     192.0.2.10
sub      IN NS    ns.sub.foo.example.org.
ns.sub   IN A     192.0.2.53
_sip._tcp IN SRV  10 5 5060 sip.foo.example.org.
sip      IN A     192.0.2.20
@        IN TXT   "v=spf1 ip4:1.2.3.4 -all"
@        IN CAA   0 issue "letsencrypt.org"
~~~
