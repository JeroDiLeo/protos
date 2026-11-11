FROM ubuntu:24.04
RUN apt-get update && apt-get install -y --no-install-recommends nginx curl \
    && rm -rf /var/lib/apt/lists/* && rm -f /etc/nginx/sites-enabled/default
COPY default.conf /etc/nginx/conf.d/metadata.conf
RUN sed -i '/listen \[::\]:80/d' /etc/nginx/conf.d/metadata.conf 2>/dev/null; nginx -t
CMD ["nginx","-g","daemon off;"]
