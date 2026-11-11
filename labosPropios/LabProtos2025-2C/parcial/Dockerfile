FROM ubuntu:24.04
RUN apt-get update && apt-get install -y --no-install-recommends nginx curl \
    && rm -rf /var/lib/apt/lists/* && rm -f /etc/nginx/sites-enabled/default
COPY parcial.conf /etc/nginx/conf.d/parcial.conf
RUN nginx -t
CMD ["nginx", "-g", "daemon off;"]
