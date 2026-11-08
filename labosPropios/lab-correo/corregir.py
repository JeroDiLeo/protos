#!/usr/bin/env python3
"""Corrector del lab de correo.

  python3 corregir.py seed          crea los mensajes iniciales (buzones de C4, C11, C12) y el logo
  python3 corregir.py corregir C3   revisa el ultimo correo que mandaste para ese ejercicio
  python3 corregir.py pista C3      una pista corta, sin la solucion
  python3 corregir.py solucion C1   respuestas del ejercicio de "encontrar los errores"
"""
import email, email.policy, email.utils, hashlib, json, os, re, struct, sys, time, unicodedata, zlib
from email.header import decode_header, make_header

BASE = os.environ.get("LABC", os.path.expanduser("~/lab-correo"))
MAILDIR = os.path.join(BASE, "mail")
CONF = json.load(open(os.path.join(BASE, "config.json")))
LEG = CONF["legajo"]
NOMBRE = CONF["nombre"]
CUENTA = CONF["cuenta"].lower()
YO = f"{LEG}@mail.protos.lab"
LOGO = os.path.join(BASE, "adjuntos", "logo.png")
SECRETO = "«Ñandú-42¿»"
C10_TEXTO = ["Canción de prueba: ¿cómo están?", ".esta línea empieza con punto", "fin"]


# ----------------------------------------------------------------- semillas
def png(path, w=24, h=24):
    rows = b""
    for y in range(h):
        rows += b"\x00" + b"".join(bytes(((x * 10) % 256, (y * 10) % 256, 160)) for x in range(w))
    def chunk(t, d):
        c = struct.pack(">I", len(d)) + t + d
        return c + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    data = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) \
        + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b"")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "wb").write(data)


def put(addr, raw, n):
    d = os.path.join(MAILDIR, addr.lower())
    os.makedirs(d, exist_ok=True)
    date = email.utils.formatdate(localtime=True)
    top = (f"Return-Path: <semilla@protos.lab>\r\nReceived: from semilla (localhost [127.0.0.1])\r\n"
           f"\tby mx1.protos.lab with ESMTP id SEED{n:04d}\r\n\tfor <{addr}>; {date}\r\n")
    with open(os.path.join(d, f"{1000000000 + n:019d}-SEED{n:04d}.eml"), "wb") as f:
        f.write((top + raw.replace("\n", "\r\n")).encode())


def b64(s):
    import base64
    return base64.encodebytes(s.encode()).decode().strip()


def seed():
    png(LOGO)
    # C4: la mision
    cuerpo = (f"Agente {LEG}:\n\nLos planos ya están en camino. Para confirmar que recibió este mensaje, "
              f"responda a esta misma dirección con la clave de verificación exacta, sin agregarle nada:\n\n"
              f"{SECRETO}\n\nTenga en cuenta que la clave no es ASCII. Una vez leído, borre este mensaje del servidor.\n")
    put(YO, f"""From: =?UTF-8?Q?Secretar=C3=ADa_IMF?= <secretaria@mision.lab>
To: Agente {LEG} <{YO}>
Subject: =?UTF-8?B?{b64('Misión: Imposible').replace(chr(10),'')}?=
Date: {email.utils.formatdate(localtime=True)}
Message-ID: <seed-mision@mision.lab>
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: base64

{b64(cuerpo)}
""", 1)
    # C12: consulta en hilo
    put(YO, f"""From: Prof. Ana Torres <atorres@mail.protos.lab>
To: <{YO}>
Subject: Consulta sobre la entrega
Date: {email.utils.formatdate(localtime=True)}
Message-ID: <consulta-7731@mail.protos.lab>
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: base64

{b64('Hola. ¿Me confirmás tu número de legajo respondiendo este correo? Tiene que quedar en el mismo hilo.' + chr(10))}
""", 2)
    # C11: buzon para limpiar
    msgs = [
        ("Ventas Online <promo@ofertas.lab>", "Actualización de su cuenta", "YES"),
        ("Cooperadora ITBA <coop@mail.protos.lab>", "¡¡GANASTE!! Sorteo de la cooperadora", None),
        ("Mesa de ayuda <soporte@mail.protos.lab>", "Turno de laboratorio confirmado", None),
        ("Premios <win@premios.lab>", "Reclamá tu premio hoy", "YES"),
        ("Bedelía <bedelia@mail.protos.lab>", "Cambio de aula - Protocolos", None),
        ("Seguridad <no-reply@banco-falso.lab>", "Verifique su identidad", "YES"),
        ("Ana Torres <atorres@mail.protos.lab>", "Notas del parcial", None),
    ]
    for i, (frm, subj, spam) in enumerate(msgs, start=10):
        extra = f"X-Spam-Flag: {spam}\nX-Spam-Score: 9.1\n" if spam else "X-Spam-Flag: NO\nX-Spam-Score: 0.4\n"
        put("limpieza@mail.protos.lab", f"""From: {frm}
To: <limpieza@mail.protos.lab>
Subject: =?UTF-8?B?{b64(subj).replace(chr(10),'')}?=
Date: {email.utils.formatdate(localtime=True)}
Message-ID: <seed-{i}@protos.lab>
{extra}MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: base64

{b64('Mensaje de prueba número ' + str(i) + '.' + chr(10) * 1)}
""", i)
    print("semillas creadas")


# ----------------------------------------------------------------- lectura
def mensajes(addr):
    d = os.path.join(MAILDIR, addr.lower())
    if not os.path.isdir(d):
        return []
    out = []
    for f in sorted(os.listdir(d)):
        if f.endswith(".eml"):
            raw = open(os.path.join(d, f), "rb").read()
            out.append((f, raw, email.message_from_bytes(raw, policy=email.policy.default)))
    return out


def dec(v):
    if v is None:
        return None
    try:
        return str(make_header(decode_header(str(v))))
    except Exception:
        return str(v)


def norm(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


def raw_headers(raw):
    head = raw.split(b"\r\n\r\n", 1)[0]
    out, cur = {}, None
    for l in head.split(b"\r\n"):
        if l[:1] in (b" ", b"\t") and cur:
            out[cur] += b" " + l.strip()
        elif b":" in l:
            cur = l.split(b":", 1)[0].decode("latin-1").lower()
            out[cur] = l.split(b":", 1)[1].strip()
    return out


class R:
    def __init__(self, titulo):
        self.items = []
        print(f"\n== {titulo} ==")

    def ok(self, cond, bien, mal):
        self.items.append(bool(cond))
        print(("  [OK] " + bien) if cond else ("  [X]  " + mal))
        return cond

    def aviso(self, txt):
        print("  [!]  " + txt)

    def fin(self):
        n, t = sum(self.items), len(self.items)
        print(f"\n  Resultado: {n}/{t} verificaciones bien." + ("  ¡Aprobado!" if n == t else ""))


def partes(msg):
    return [p for p in msg.walk() if not p.is_multipart()]


def texto_de(part):
    try:
        return part.get_content()
    except Exception:
        return part.get_payload(decode=True).decode("utf-8", "replace")


def ultimo(addr, filtro):
    for f, raw, m in reversed(mensajes(addr)):
        if filtro(m):
            return raw, m
    return None, None


def del_alumno(m):
    return CUENTA in (email.utils.parseaddr(str(m.get("From", "")))[1] or "").lower()


def con_xparcial(valor):
    return lambda m: del_alumno(m) and str(m.get("X-Parcial", "")).strip() == valor


CONOCIDOS = {"2026/2C", "2024/2", "2026/1R", "LAB-C5", "LAB-C6", "LAB-C7", "LAB-C8", "LAB-C9", "LAB-C10"}


def buscar(addr, xp, titulo):
    """Tu último correo de ese buzón, salvo que su X-Parcial sea el de OTRO ejercicio.
    Así, si el X-Parcial está mal escrito, se corrige igual (y se marca el error)."""
    import difflib

    def candidato(m):
        v = str(m.get("X-Parcial", "")).strip()
        if not del_alumno(m):
            return False
        if v == xp or not v:
            return True
        if v in CONOCIDOS:
            return False
        parecido = max(CONOCIDOS, key=lambda k: difflib.SequenceMatcher(None, v.upper(), k.upper()).ratio())
        return parecido == xp
    raw, m = ultimo(addr, candidato)
    if m is None:
        print(f"  [X]  No encontré ningún correo tuyo (From: {CUENTA}) para este ejercicio en el buzón {addr}.")
        print("       ¿Lo mandaste al destinatario correcto? ¿El From tiene tu cuenta ITBA? Mirá: bash lab-correo.sh log")
        return None, None
    print(f"  corrigiendo: {m.get('Message-ID')}  ·  Subject: {dec(m.get('Subject'))!r}")
    return raw, m


# ----------------------------------------------------------------- chequeos comunes
def estandar(r, raw, m, xp=None, subject="¡Buenos días!", destino=YO, sin_qp=True, nombre=True):
    h = raw_headers(raw)
    if xp is not None:
        r.ok(str(m.get("X-Parcial", "")).strip() == xp, f"X-Parcial: {xp}", f"X-Parcial debería ser exactamente {xp!r} y es {str(m.get('X-Parcial'))!r}")
    if subject is not None:
        s = dec(m.get("Subject"))
        r.ok(s == subject, f"Subject = {subject}", f"Subject decodificado es {s!r}, se pedía {subject!r}")
        if "subject" in h:
            r.ok(all(b < 128 for b in h["subject"]), "Subject codificado en ASCII (encoded-word)",
                 "El Subject tiene bytes no ASCII crudos: el servidor no anuncia SMTPUTF8. Usá =?UTF-8?B?...?=")
    frm = m.get("From")
    nom, addr = email.utils.parseaddr(dec(frm) or "")
    r.ok(addr.lower() == CUENTA, f"From con tu cuenta ITBA ({CUENTA})", f"El From tiene {addr!r}, se esperaba {CUENTA}")
    if nombre:
        toks = norm(NOMBRE).split()
        r.ok(nom and toks and toks[0] in norm(nom) and toks[-1] in norm(nom),
             f"From con nombre y apellido ({nom})", f"El From no tiene tu nombre y apellido (tiene {nom!r}). Formato: From: Nombre Apellido <cuenta@itba.edu.ar>")
        if "from" in h:
            r.ok(all(b < 128 for b in h["from"]), "From en ASCII (si hay tildes, encoded-word)",
                 "El From tiene bytes no ASCII crudos: el nombre con tildes va como =?UTF-8?B?...?=")
    tos = [a.lower() for _, a in email.utils.getaddresses([dec(x) for x in m.get_all("To", [])])]
    r.ok(destino.lower() in tos, f"To: {destino}", f"El header To no incluye {destino} (tiene {tos})")
    rp = str(m.get("Return-Path", "")).strip("<> ").lower()
    if rp and rp != CUENTA:
        r.aviso(f"MAIL FROM (sobre) fue <{rp}> y el From es {CUENTA}: conviene que coincidan.")
    r.ok(str(m.get("MIME-Version", "")).strip() == "1.0", "MIME-Version: 1.0", "Falta MIME-Version: 1.0 (obligatorio si usás Content-Type/Transfer-Encoding)")
    d = m.get("Date")
    try:
        ok_date = d is not None and email.utils.parsedate_to_datetime(str(d)) is not None
    except Exception:
        ok_date = False
    r.ok(ok_date, "Date válido", "Falta Date o no tiene formato RFC 5322 (usá: date -R)")
    mid = str(m.get("Message-ID", "")).strip()
    r.ok(re.fullmatch(r"<[^<>@\s]+@[^<>@\s]+>", mid), "Message-ID con formato <algo@dominio>",
         f"Message-ID ausente o mal formado ({mid!r}). Ej: <123.456@itba.edu.ar>")
    if sin_qp:
        qp = [p for p in m.walk() if str(p.get("Content-Transfer-Encoding", "")).lower() == "quoted-printable"]
        r.ok(not qp, "Ninguna parte en quoted-printable", "Hay partes en quoted-printable: se pedía que lo lean MUAs SIN soporte de QP -> base64")
    for p in partes(m):
        if p.get_content_maintype() == "text":
            cs = (p.get_content_charset() or "").lower()
            cte = str(p.get("Content-Transfer-Encoding", "7bit")).lower()
            body = p.get_payload(decode=False)
            if isinstance(body, str) and any(ord(c) > 127 for c in body) and cte in ("7bit", ""):
                r.ok(False, "", f"La parte {p.get_content_type()} tiene caracteres no ASCII sin Content-Transfer-Encoding")
            if cs != "utf-8":
                r.ok(False, "", f"La parte {p.get_content_type()} no declara charset=UTF-8 (declara {cs or 'nada'})")


def texto_plano(r, m, esperado):
    pl = [p for p in partes(m) if p.get_content_type() == "text/plain"]
    if not r.ok(pl, "Hay una parte text/plain", "No hay ninguna parte text/plain"):
        return
    t = texto_de(pl[0]).strip()
    if "=C2=A1" in t or "=C3" in t:
        r.ok(False, "", f"El texto decodificado es {t!r}: codificaste en base64 un texto que ya estaba en quoted-printable (doble codificación)")
    else:
        r.ok(t == esperado, f"Texto = {esperado}", f"El texto decodificado es {t!r}, se pedía {esperado!r}")


# ----------------------------------------------------------------- ejercicios
def C_basico(n, xp):
    r = R(f"Corrección {n}")
    raw, m = buscar(YO, xp, f"Corrección {n}")
    if m is None:
        return
    estandar(r, raw, m, xp=xp)
    texto_plano(r, m, "¡Hola mundo!")
    r.fin()


def C3():
    r = R("Corrección C3 (negrita)")
    raw, m = buscar(YO, "2026/1R", "C3")
    if m is None:
        return
    estandar(r, raw, m, xp="2026/1R")
    r.ok(m.get_content_type() == "multipart/alternative", "Estructura multipart/alternative",
         f"La estructura es {m.get_content_type()}: para negrita + versión texto va multipart/alternative")
    texto_plano(r, m, "¡Hola mundo!")
    hs = [p for p in partes(m) if p.get_content_type() == "text/html"]
    if r.ok(hs, "Hay una parte text/html", "No hay parte text/html (la negrita va en HTML)"):
        html = texto_de(hs[0])
        if "=3D" in html:
            r.ok(False, "", "El HTML decodificado tiene '=3D': quedó quoted-printable dentro del base64")
        r.ok(re.search(r"<(b|strong)>\s*¡Hola mundo!\s*</(b|strong)>", html), "¡Hola mundo! en <b> o <strong>",
             f"No encontré <b>¡Hola mundo!</b> en el HTML: {html.strip()[:80]!r}")
    tipos = [p.get_content_type() for p in partes(m)]
    if "text/html" in tipos and "text/plain" in tipos:
        r.ok(tipos.index("text/plain") < tipos.index("text/html"), "Orden: text/plain primero, text/html último",
             "En multipart/alternative la versión preferida (HTML) va ÚLTIMA")
    r.fin()


def C4():
    r = R("Corrección C4 (misión por POP3)")
    quedo = [f for f, raw, m in mensajes(YO) if "seed-mision" in str(m.get("Message-ID", ""))]
    r.ok(not quedo, "Borraste el mensaje original (DELE + QUIT)",
         "El mensaje de la misión sigue en tu buzón: DELE solo marca; se borra recién al hacer QUIT")
    raw, m = ultimo("secretaria@mision.lab", del_alumno)
    if not r.ok(m is not None, "La secretaria recibió tu respuesta", "No llegó ninguna respuesta tuya a secretaria@mision.lab"):
        return r.fin()
    estandar(r, raw, m, subject=None, destino="secretaria@mision.lab", sin_qp=False, nombre=False)
    s = dec(m.get("Subject")) or ""
    r.ok(s.lower().startswith("re:"), f"Subject de respuesta ({s})", f"El Subject {s!r} no empieza con 'Re:'")
    pl = [p for p in partes(m) if p.get_content_type() == "text/plain"]
    if r.ok(pl, "Cuerpo text/plain", "No hay cuerpo text/plain"):
        t = texto_de(pl[0]).strip()
        r.ok(t == SECRETO, "La clave llegó exacta", f"El cuerpo decodificado es {t!r} y la clave era otra (¿copiaste bien los caracteres? ¿usaste echo y se coló un salto?)")
    if str(m.get("In-Reply-To", "")).strip() == "<seed-mision@mision.lab>":
        r.aviso("Bien: pusiste In-Reply-To (no se pedía, suma).")
    r.fin()


def C5():
    r = R("Corrección C5 (imagen adjunta)")
    raw, m = buscar(YO, "LAB-C5", "C5")
    if m is None:
        return
    estandar(r, raw, m, xp="LAB-C5", subject="Logo del laboratorio")
    r.ok(m.get_content_type() == "multipart/mixed", "Estructura multipart/mixed", f"Es {m.get_content_type()}: un adjunto va en multipart/mixed")
    texto_plano(r, m, "Adjunto el logo del laboratorio.")
    imgs = [p for p in partes(m) if p.get_content_maintype() == "image"]
    if r.ok(imgs, "Hay una parte image/*", "No hay ninguna parte de imagen"):
        p = imgs[0]
        r.ok(p.get_content_type() == "image/png", "Content-Type: image/png", f"El tipo es {p.get_content_type()}")
        r.ok(str(p.get("Content-Transfer-Encoding", "")).lower() == "base64", "Imagen en base64", "La imagen tiene que ir en base64")
        r.ok((p.get_content_disposition() == "attachment"), "Content-Disposition: attachment", "Falta Content-Disposition: attachment")
        r.ok(p.get_filename() == "logo.png", "filename=\"logo.png\"", f"El nombre de archivo es {p.get_filename()!r}")
        data = p.get_payload(decode=True) or b""
        r.ok(hashlib.sha256(data).digest() == hashlib.sha256(open(LOGO, 'rb').read()).digest(),
             "La imagen decodificada es idéntica a logo.png", "La imagen decodificada no coincide con logo.png (¿base64 cortado o con basura?)")
    r.fin()


def C6():
    r = R("Corrección C6 (imagen dentro del HTML)")
    raw, m = buscar(YO, "LAB-C6", "C6")
    if m is None:
        return
    estandar(r, raw, m, xp="LAB-C6", subject="Logo en el cuerpo")
    tipos = [p.get_content_type() for p in m.walk()]
    r.ok("multipart/related" in tipos, "Hay un multipart/related", "Falta multipart/related (HTML + imagen que va adentro)")
    if "multipart/alternative" not in tipos:
        r.aviso("No hay versión de texto plano (multipart/alternative): es buena práctica incluirla.")
    hs = [p for p in partes(m) if p.get_content_type() == "text/html"]
    imgs = [p for p in partes(m) if p.get_content_maintype() == "image"]
    if r.ok(hs and imgs, "Hay parte HTML y parte imagen", "Falta la parte HTML o la imagen"):
        html = texto_de(hs[0])
        cid = re.search(r'src=["\']cid:([^"\']+)["\']', html)
        if r.ok(cid, "El HTML referencia la imagen con src=\"cid:...\"", "El HTML no tiene <img src=\"cid:...\">"):
            want = cid.group(1)
            got = str(imgs[0].get("Content-ID", "")).strip("<> ")
            r.ok(want == got, f"Content-ID <{got}> coincide con cid:{want}", f"El Content-ID de la imagen es <{got}> y el HTML pide cid:{want}")
        data = imgs[0].get_payload(decode=True) or b""
        r.ok(data == open(LOGO, "rb").read(), "La imagen es logo.png", "La imagen no coincide con logo.png")
    r.fin()


def C7():
    r = R("Corrección C7 (To, Cc y Bcc)")
    raw, m = buscar(YO, "LAB-C7", "C7")
    if m is None:
        return
    estandar(r, raw, m, xp="LAB-C7", subject="Reunión de cátedra")
    mid = str(m.get("Message-ID", ""))
    ccs = [a.lower() for _, a in email.utils.getaddresses([dec(x) for x in m.get_all("Cc", [])])]
    r.ok("ayudante@mail.protos.lab" in ccs, "Cc: ayudante@mail.protos.lab", f"El header Cc no tiene a ayudante@mail.protos.lab ({ccs})")
    for who in ("ayudante@mail.protos.lab", "jefa@mail.protos.lab"):
        got = [x for _, _, x in mensajes(who) if str(x.get("Message-ID", "")) == mid]
        r.ok(got, f"{who} recibió el correo", f"{who} no lo recibió: falta un RCPT TO:<{who}> en el sobre")
        for x in got:
            r.ok(x.get("Bcc") is None, f"La copia de {who} no muestra Bcc", f"La copia de {who} tiene header Bcc: el oculto NO va en los headers, solo en RCPT TO")
    tos_cc = " ".join(dec(x) or "" for x in m.get_all("To", []) + m.get_all("Cc", []))
    r.ok("jefa@" not in tos_cc, "jefa no aparece en To/Cc (copia oculta)", "jefa aparece en To o Cc: tenía que ser copia oculta")
    r.fin()


def C8():
    r = R("Corrección C8 (servidor descubierto por MX)")
    raw, m = ultimo("ventas@empresa.lab", del_alumno)
    if not r.ok(m is not None, "ventas@empresa.lab recibió tu correo", "No llegó a ventas@empresa.lab. ¿Hiciste el MX y te conectaste a la IP que corresponde?"):
        return r.fin()
    estandar(r, raw, m, xp="LAB-C8", subject="Pedido de presupuesto", destino="ventas@empresa.lab")
    r.ok("by mx.empresa.lab" in str(m.get("Received", "")), "Entregado por mx.empresa.lab (prioridad 10)", "No pasó por mx.empresa.lab")
    r.fin()


def C9():
    r = R("Corrección C9 (envío autenticado)")
    raw, m = ultimo("profe@externo.lab", del_alumno)
    if not r.ok(m is not None, "profe@externo.lab recibió tu correo",
                "No llegó a profe@externo.lab. El MX (2525) rechaza dominios ajenos: hay que usar submission 2587 con AUTH"):
        return r.fin()
    estandar(r, raw, m, xp="LAB-C9", subject="Entrega TP", destino="profe@externo.lab")
    r.ok("ESMTPSA" in str(m.get("Received", "")), "Enviado autenticado (ESMTPSA)", "No figura como envío autenticado")
    r.fin()


def C10():
    r = R("Corrección C10 (quoted-printable y tildes en el remitente)")
    raw, m = buscar(YO, "LAB-C10", "C10")
    if m is None:
        return
    h = raw_headers(raw)
    r.ok(str(m.get("X-Parcial", "")).strip() == "LAB-C10", "X-Parcial: LAB-C10", "X-Parcial incorrecto")
    nom, addr = email.utils.parseaddr(dec(m.get("From")) or "")
    r.ok(nom == "Pingüino Ñandú", "Nombre del remitente = Pingüino Ñandú", f"El nombre del From decodificado es {nom!r}")
    r.ok(addr.lower() == CUENTA, "Dirección del From = tu cuenta ITBA", f"El From tiene {addr!r}")
    r.ok(all(b < 128 for b in h.get("from", b"")), "From codificado (encoded-word)", "El From tiene tildes crudas: va =?UTF-8?Q?...?= o =?UTF-8?B?...?=")
    s = dec(m.get("Subject"))
    r.ok(s == "Prueba de codificación", "Subject = Prueba de codificación", f"Subject = {s!r}")
    r.ok(all(b < 128 for b in h.get("subject", b"")), "Subject codificado", "Subject con tildes crudas")
    pl = [p for p in partes(m) if p.get_content_type() == "text/plain"]
    if r.ok(pl, "Parte text/plain", "No hay text/plain"):
        p = pl[0]
        r.ok(str(p.get("Content-Transfer-Encoding", "")).lower() == "quoted-printable", "Content-Transfer-Encoding: quoted-printable",
             "Se pedía quoted-printable")
        lines = [l.rstrip() for l in texto_de(p).strip().splitlines()]
        if len(lines) >= 2 and lines[1] == "esta línea empieza con punto":
            r.ok(False, "", "La segunda línea perdió el punto inicial: en DATA una línea que empieza con '.' se escribe '..' (dot-stuffing)")
        else:
            r.ok(lines == C10_TEXTO, "El texto llegó exacto (incluida la línea con punto)", f"El texto decodificado es {lines!r}")
    r.fin()


def C11():
    r = R("Corrección C11 (limpieza del buzón por POP3)")
    msgs = mensajes("limpieza@mail.protos.lab")
    quedan = {str(m.get("Message-ID", "")) for _, _, m in msgs}
    spam = {"<seed-10@protos.lab>", "<seed-13@protos.lab>", "<seed-15@protos.lab>"}
    bueno = {"<seed-11@protos.lab>", "<seed-12@protos.lab>", "<seed-14@protos.lab>", "<seed-16@protos.lab>"}
    r.ok(not (spam & quedan), "Borraste los 3 marcados X-Spam-Flag: YES", f"Quedan {len(spam & quedan)} con X-Spam-Flag: YES (¿hiciste QUIT al final?)")
    r.ok(bueno <= quedan, "No borraste ninguno legítimo", f"Borraste {len(bueno - quedan)} que NO eran spam (ojo con el asunto del sorteo)")
    r.ok(len(msgs) == 4, f"Quedan exactamente 4 mensajes", f"Quedan {len(msgs)} mensajes")
    r.fin()


def C12():
    r = R("Corrección C12 (respuesta en el mismo hilo)")
    raw, m = ultimo("atorres@mail.protos.lab", del_alumno)
    if not r.ok(m is not None, "La profesora recibió tu respuesta", "No llegó respuesta tuya a atorres@mail.protos.lab"):
        return r.fin()
    estandar(r, raw, m, subject="Re: Consulta sobre la entrega", destino="atorres@mail.protos.lab", sin_qp=False)
    want = "<consulta-7731@mail.protos.lab>"
    r.ok(str(m.get("In-Reply-To", "")).strip() == want, f"In-Reply-To: {want}", "Falta In-Reply-To con el Message-ID del original")
    r.ok(want in str(m.get("References", "")), f"References incluye {want}", "Falta References con el Message-ID del original")
    pl = [p for p in partes(m) if p.get_content_type() == "text/plain"]
    r.ok(pl and LEG in texto_de(pl[0]), "El cuerpo tiene tu legajo", "El cuerpo no contiene tu número de legajo")
    r.fin()


EJ = {"C1": lambda: C_basico("C1", "2026/2C"), "C2": lambda: C_basico("C2", "2024/2"), "C3": C3, "C4": C4,
      "C5": C5, "C6": C6, "C7": C7, "C8": C8, "C9": C9, "C10": C10, "C11": C11, "C12": C12}

PISTAS = {
    "C1": "Leé el diálogo línea por línea en orden: sobre (HELO, MAIL FROM, RCPT TO), headers y cuerpo. Decodificá el base64 del cuerpo y fijate qué se vería.",
    "C2": "Sin quoted-printable: texto en base64 con charset=UTF-8. El Subject con ¡ y í también va codificado (encoded-word).",
    "C3": "Negrita = HTML, y una versión de texto para quien no muestra HTML: multipart/alternative, text/plain primero.",
    "C4": "LIST -> RETR -> base64 -d -> DELE -> QUIT. Para responder, codificá la clave con printf '%s' (no echo).",
    "C5": "multipart/mixed: una parte de texto y otra image/png en base64 con Content-Disposition: attachment. base64 -w 76 logo.png",
    "C6": "multipart/related: el HTML con <img src=\"cid:logo\"> y la imagen con Content-ID: <logo>.",
    "C7": "To y Cc van en los headers Y en RCPT TO. El oculto (Bcc) va solo en RCPT TO.",
    "C8": "dig @127.0.0.1 -p 5361 MX empresa.lab -> menor número = más prioridad -> dig A de ese nombre.",
    "C9": "El 2525 es para RECIBIR. Para mandar afuera: 2587, EHLO, AUTH PLAIN con base64 de \\0usuario\\0clave.",
    "C10": "Quoted-printable: ó = =C3=B3. La línea que empieza con punto se tipea con dos puntos en DATA.",
    "C11": "TOP n 0 te muestra solo los headers. Buscá X-Spam-Flag. DELE solo marca; QUIT confirma.",
    "C12": "Copiá el Message-ID del original en In-Reply-To y en References. Subject con Re:.",
}

SOL_C1 = """
Errores del diálogo de Lucía (C1). Cada uno con qué norma rompe y qué efecto tiene:

 1. nc sin -C: manda LF en vez de CRLF. SMTP exige CRLF (RFC 5321). GreenMail lo tolera, otros
    servidores no; además el fin de DATA tiene que ser <CRLF>.<CRLF>.
 2. Nunca hizo HELO/EHLO. La sesión arranca con HELO/EHLO (RFC 5321). Un servidor estricto responde
    503 "send HELO/EHLO first" (el del lab lo hace).
 3. RCPT TO a su propia cuenta del ITBA. El correo tenía que entregarse a {legajo}@mail.protos.foo:
    RCPT TO es el destinatario REAL (sobre). Que el To: diga otra cosa no cambia a dónde se entrega.
 4. X-Parcial: 2026/2 (falta la C). Se pedía exactamente 2026/2C.
 5. Subject: ¡Buenos días! con bytes UTF-8 crudos. Los headers son ASCII (RFC 5322); sin SMTPUTF8
    anunciado hay que usar encoded-word (RFC 2047): =?UTF-8?B?wqFCdWVub3MgZMOtYXMh?=
 6. From sin nombre y apellido. Se pedía "Nombre Apellido <cuenta@itba.edu.ar>".
 7. Faltan Date y Message-ID: son buenas prácticas (Date es obligatorio en RFC 5322).
 8. Content-Type: text/plain sin charset=UTF-8: el MUA asume US-ASCII y muestra mal la ¡.
 9. Doble codificación del cuerpo: el base64 decodifica a "=C2=A1Hola mundo!", que es texto YA en
    quoted-printable. El MUA decodifica base64 y muestra literalmente "=C2=A1Hola mundo!". Además
    contradice el requisito "MUAs sin quoted-printable". Lo correcto: base64 de "¡Hola mundo!" en UTF-8.
10. Cortó con Ctrl+C sin QUIT. NO impide la entrega: el correo se aceptó en el "250" posterior al
    punto. QUIT solo cierra la sesión de forma ordenada (respuesta 221). Es un error de forma, no de entrega.

Y a la pregunta (c): el correo SÍ se entregó (hubo 250 después del punto), pero en el buzón
equivocado (la cuenta de Lucía, no {legajo}@mail.protos.foo) y con contenido incorrecto.
"""


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__); return
    if a[0] == "seed":
        seed()
    elif a[0] in ("corregir", "pista", "solucion") and len(a) > 1:
        e = a[1].upper()
        if e not in EJ:
            print("Ejercicios: " + ", ".join(EJ)); return
        if a[0] == "corregir":
            EJ[e]()
        elif a[0] == "pista":
            print(PISTAS[e])
        else:
            print(SOL_C1 if e == "C1" else "Solo C1 tiene solución escrita; para el resto usá 'corregir', que te dice qué falla.")
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
