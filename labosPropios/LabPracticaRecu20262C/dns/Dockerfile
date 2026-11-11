FROM ubuntu:24.04
RUN apt-get update && apt-get install -y --no-install-recommends python3-minimal \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY dnsserver.py healthcheck.py ./
CMD ["python3","/app/dnsserver.py"]
