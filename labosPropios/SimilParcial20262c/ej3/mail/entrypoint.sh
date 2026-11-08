#!/bin/bash
set -e
LEGAJO="${LEGAJO:-62345}"

# crear usuario legajo con password = legajo (si no existe)
if ! id "$LEGAJO" >/dev/null 2>&1; then
    useradd -m -s /bin/bash "$LEGAJO"
    echo "$LEGAJO:$LEGAJO" | chpasswd
fi

# Maildir
su - "$LEGAJO" -c 'maildirmake.dovecot ~/Maildir 2>/dev/null || mkdir -p ~/Maildir/{cur,new,tmp}'

# mensaje pre-cargado (asi la parte b anda aunque no mandes nada)
MSG="/home/$LEGAJO/Maildir/new/welcome.$(date +%s)"
cat > "$MSG" <<MAIL
From: friend@pdc.lab
To: $LEGAJO@pdc.lab
Subject: Hola
Date: $(date -R)

Como estas? Este mensaje ya estaba en tu casilla.
Si ves esto por IMAP, la parte (b) esta OK.
FLAG{ej3-imap-fetch-ok}
MAIL
chown -R "$LEGAJO:$LEGAJO" "/home/$LEGAJO/Maildir"

# postfix: destino local = pdc.lab, entrega a Maildir
postconf -e "myhostname = pdc.lab"
postconf -e "mydestination = pdc.lab, localhost"
postconf -e "mynetworks = 0.0.0.0/0"
postconf -e "home_mailbox = Maildir/"
postconf -e "smtpd_banner = pdc.lab ESMTP ready"

service postfix start
exec dovecot -F
