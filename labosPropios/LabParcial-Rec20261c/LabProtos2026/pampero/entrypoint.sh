#!/bin/bash
set -e
# cuenta del alumno, lista para entrar por CLAVE desde el arranque (sin passwd manual)
id alumno >/dev/null 2>&1 || useradd -m -s /bin/bash alumno
# desbloquear la cuenta (el '!' en shadow bloquea el login): le damos password
echo 'alumno:holamundo' | chpasswd
mkdir -p /home/alumno/.ssh
cp /opt/keys/id_ed25519.pub /home/alumno/.ssh/authorized_keys
chown -R alumno:alumno /home/alumno/.ssh
chmod 700 /home/alumno/.ssh; chmod 600 /home/alumno/.ssh/authorized_keys

# archivo que el alumno va a seguir con tail -f; late solo para que vea cambios
touch /tmp/parcial-20261; chown alumno:alumno /tmp/parcial-20261
( while true; do echo "latido $(date -u +%H:%M:%S) desde pampero" >> /tmp/parcial-20261; sleep 15; done ) &

ssh-keygen -A
exec /usr/sbin/sshd -D -e
