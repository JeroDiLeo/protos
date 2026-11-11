FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        bind9 bind9-utils bind9-dnsutils nginx \
        curl netcat-openbsd nmap net-tools traceroute iproute2 iputils-ping \
        openssh-client sshpass sudo nano vim-tiny less procps ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN sed -i 's/dnssec-validation auto;/dnssec-validation no;/' /etc/bind/named.conf.options \
    && ( [ -f /etc/bind/rndc.key ] || rndc-confgen -a ) \
    && chown root:bind /etc/bind/rndc.key && chmod 640 /etc/bind/rndc.key \
    && mkdir -p /var/log/lab
RUN sed -i '/listen \[::\]:80/d' /etc/nginx/sites-available/default && nginx -t
COPY systemctl journalctl /usr/local/bin/
COPY entrypoint.sh /entrypoint.sh
RUN chmod 755 /usr/local/bin/systemctl /usr/local/bin/journalctl && chmod +x /entrypoint.sh
WORKDIR /root
CMD ["/entrypoint.sh"]
