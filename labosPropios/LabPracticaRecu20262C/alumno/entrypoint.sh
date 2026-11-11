#!/bin/bash
# VM del alumno (recu). Arranca como una Ubuntu recien instalada para el parcial.
printf 'nameserver 192.168.60.53\noptions timeout:2 attempts:2\n' > /etc/resolv.conf
ip route replace default via 192.168.60.1 2>/dev/null || true
mkdir -p /var/log/lab
# nginx y bind instalados pero el alumno los configura/arranca segun cada ejercicio
exec sleep infinity
