FROM debian:12-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
        openssh-server netcat-openbsd coreutils \
    && rm -rf /var/lib/apt/lists/* && mkdir -p /run/sshd
COPY sshd_config /etc/ssh/sshd_config
COPY entrypoint.sh /entrypoint.sh
RUN mkdir -p /opt/keys
COPY keys/id_ed25519.pub /opt/keys/id_ed25519.pub
RUN chmod +x /entrypoint.sh
EXPOSE 22
CMD ["/entrypoint.sh"]
