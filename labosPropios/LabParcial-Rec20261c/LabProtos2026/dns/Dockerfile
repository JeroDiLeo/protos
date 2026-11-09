FROM python:3.12-slim
WORKDIR /app
COPY dnsserver.py healthcheck.py ./
EXPOSE 53/udp 53/tcp
CMD ["python3","dnsserver.py"]
