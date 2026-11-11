#!/bin/sh
[ "$(cat /proc/sys/net/ipv4/ip_forward)" = 1 ] || exit 1
SRV=$(cat /run/srv.pid 2>/dev/null) || exit 1
nsenter -t "$SRV" -n curl -fs -o /dev/null http://127.0.0.1:8080/ || exit 1
curl -fs -o /dev/null http://10.0.0.137:8080/ || exit 1
