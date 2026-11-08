FROM debian:12-slim
ARG LEGAJO=62345
ENV LEGAJO=${LEGAJO}
ENV DEBIAN_FRONTEND=noninteractive
# preseed para que postfix se configure solo (Internet Site) y arme main.cf completo
RUN apt-get update && apt-get install -y --no-install-recommends debconf-utils \
    && echo "postfix postfix/main_mailer_type select Internet Site" | debconf-set-selections \
    && echo "postfix postfix/mailname string pdc.lab" | debconf-set-selections \
    && apt-get install -y --no-install-recommends \
        postfix dovecot-imapd dovecot-pop3d rsyslog \
    && rm -rf /var/lib/apt/lists/*
COPY dovecot.conf /etc/dovecot/dovecot.conf
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
EXPOSE 25 143 110
CMD ["/entrypoint.sh"]
