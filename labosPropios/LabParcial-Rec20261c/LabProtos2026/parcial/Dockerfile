FROM debian:12-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
        openssh-server nginx python3 \
    && rm -rf /var/lib/apt/lists/* && mkdir -p /run/sshd
COPY sshd_config /etc/ssh/sshd_config
COPY nginx.conf /etc/nginx/conf.d/default.conf
RUN rm -f /etc/nginx/sites-enabled/default
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
EXPOSE 22 80 8000
CMD ["/entrypoint.sh"]
