FROM debian:12-slim
RUN apt-get update && apt-get install -y --no-install-recommends dante-server \
    && rm -rf /var/lib/apt/lists/*
COPY danted.conf /etc/danted.conf
EXPOSE 1080
CMD ["/usr/sbin/danted", "-f", "/etc/danted.conf"]
