#!/bin/bash
set -e
# usuario 'parcial' con contraseña 'holamundo' (la credencial filtrada del enunciado).
# chpasswd deja la cuenta DESBLOQUEADA, así el login por contraseña y por clave andan desde el arranque.
id parcial >/dev/null 2>&1 || useradd -m -s /bin/bash parcial
echo 'parcial:holamundo' | chpasswd
mkdir -p /home/parcial/.ssh && chown -R parcial:parcial /home/parcial/.ssh && chmod 700 /home/parcial/.ssh
ssh-keygen -A >/dev/null
mkdir -p /run/sshd
echo "parcial.protos.foo listo (ssh usuario parcial / holamundo)"
exec /usr/sbin/sshd -D -e
