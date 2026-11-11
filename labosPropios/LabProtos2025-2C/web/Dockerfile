FROM ubuntu:24.04
RUN apt-get update && apt-get install -y --no-install-recommends nginx curl \
    && rm -rf /var/lib/apt/lists/* && rm -f /etc/nginx/sites-enabled/default
COPY protos.foo.conf /etc/nginx/conf.d/protos.foo.conf
COPY zona /srv/protos.foo/zona
RUN chmod 755 /srv/protos.foo && chmod 644 /srv/protos.foo/zona && nginx -t
CMD ["nginx", "-g", "daemon off;"]
