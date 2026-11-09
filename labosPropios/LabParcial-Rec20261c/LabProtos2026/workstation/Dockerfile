FROM debian:12
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl ca-certificates dnsutils netcat-openbsd openssh-client nmap \
        bind9 bind9utils nginx python3 sshpass \
        iproute2 iputils-ping less nano vim-tiny procps \
    && rm -rf /var/lib/apt/lists/*
# bind9 y nginx quedan INSTALADOS pero APAGADOS (el alumno los configura en Ej1/Ej2)
RUN rm -f /etc/nginx/sites-enabled/default
RUN mkdir -p /opt/keys
COPY keys/id_ed25519 keys/id_ed25519.pub /opt/keys/
COPY ssh_config /opt/ssh_config
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
CMD ["/entrypoint.sh"]
