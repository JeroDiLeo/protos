#!/bin/sh
set -e
/usr/sbin/sshd
python3 /opt/control.py &
nginx -g 'daemon off;'
