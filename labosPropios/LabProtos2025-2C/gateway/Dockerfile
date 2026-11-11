FROM ubuntu:24.04
RUN apt-get update && apt-get install -y --no-install-recommends \
        iproute2 iputils-ping nginx openssh-server curl procps \
    && rm -rf /var/lib/apt/lists/* && rm -f /etc/nginx/sites-enabled/default
COPY site.conf /etc/nginx/conf.d/site.conf
COPY entrypoint.sh healthcheck.sh /
RUN chmod +x /entrypoint.sh /healthcheck.sh && nginx -t
CMD ["/entrypoint.sh"]
