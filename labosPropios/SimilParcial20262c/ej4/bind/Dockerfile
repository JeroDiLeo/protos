FROM debian:12-slim
RUN apt-get update && apt-get install -y --no-install-recommends bind9 bind9-utils \
    && rm -rf /var/lib/apt/lists/*
EXPOSE 53/udp 53/tcp
CMD ["/usr/sbin/named","-g","-c","/etc/bind/named.conf"]
