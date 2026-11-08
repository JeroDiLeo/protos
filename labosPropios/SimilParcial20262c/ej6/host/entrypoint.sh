#!/bin/sh
set -e
/usr/sbin/sshd
nginx -g 'daemon off;'
