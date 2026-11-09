#!/bin/bash
set -e
# usuario 'parcial' con password 'holamundo' (parte del ejercicio: credencial filtrada).
# PasswordAuthentication yes -> el alumno entra con pass y luego hace ssh-copy-id.
id parcial >/dev/null 2>&1 || useradd -m -s /bin/bash parcial
echo 'parcial:holamundo' | chpasswd
mkdir -p /home/parcial/.ssh && chown -R parcial:parcial /home/parcial/.ssh && chmod 700 /home/parcial/.ssh

# servicio web en 80 (nginx) y en 8000 (python) para que el nmap muestre 3 puertos
mkdir -p /srv/www && echo '<h1>parcial.protos.foo</h1><p>servidor web del recu</p>' > /srv/www/index.html
nginx
( cd /srv/www && python3 -m http.server 8000 --bind 0.0.0.0 ) &

ssh-keygen -A
exec /usr/sbin/sshd -D -e
