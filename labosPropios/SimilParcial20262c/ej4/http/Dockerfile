FROM python:3.12-slim
WORKDIR /srv
COPY index.html backup.pcapng ./
EXPOSE 8000
CMD ["python3","-m","http.server","8000"]
