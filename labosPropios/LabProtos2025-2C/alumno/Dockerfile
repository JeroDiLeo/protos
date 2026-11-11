FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        isc-dhcp-server bind9 bind9-utils bind9-dnsutils nginx \
        nmap net-tools traceroute iproute2 iputils-ping curl netcat-openbsd \
        tcpdump openssh-client sudo nano vim-tiny less procps ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# shims de systemd (systemctl / journalctl) para usar los comandos del parcial
COPY systemctl journalctl /usr/local/bin/
RUN chmod 755 /usr/local/bin/systemctl /usr/local/bin/journalctl

# Ej III: la zona rota ya esta "instalada" en el servidor
COPY named.conf.local /etc/bind/named.conf.local
COPY db.it.itba.edu.ar /etc/bind/db.it.itba.edu.ar
RUN sed -i 's/dnssec-validation auto;/dnssec-validation no;/' /etc/bind/named.conf.options \
    && chmod 644 /etc/bind/db.it.itba.edu.ar /etc/bind/named.conf.local \
    && ( [ -f /etc/bind/rndc.key ] || rndc-confgen -a ) \
    && chown root:bind /etc/bind/rndc.key && chmod 640 /etc/bind/rndc.key \
    && mkdir -p /var/log/lab

# nginx recien instalado; sin la linea IPv6 para que arranque aunque el kernel no tenga IPv6
RUN sed -i '/listen \[::\]:80/d' /etc/nginx/sites-available/default && nginx -t

# Ej I: isc-dhcp-server instalado pero sin configurar (como recien instalado)
RUN printf 'INTERFACESv4=""\nINTERFACESv6=""\n' > /etc/default/isc-dhcp-server

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
WORKDIR /root
CMD ["/entrypoint.sh"]
