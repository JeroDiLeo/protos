FROM ubuntu:24.04
RUN apt-get update && apt-get install -y --no-install-recommends python3 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY server.py ./
EXPOSE 8080
CMD ["python3","/app/server.py"]
