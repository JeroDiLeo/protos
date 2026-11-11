FROM ubuntu:24.04
RUN apt-get update && apt-get install -y --no-install-recommends \
        openssh-server passwd netcat-openbsd \
    && rm -rf /var/lib/apt/lists/* && mkdir -p /run/sshd
COPY sshd_config /etc/ssh/sshd_config
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
EXPOSE 22
CMD ["/entrypoint.sh"]
