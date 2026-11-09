FROM nginx:1.27
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
COPY default.conf /etc/nginx/conf.d/default.conf
RUN nginx -t
EXPOSE 80
