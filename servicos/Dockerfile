# Serviços do kit: conector, ouvidoria simulada, API do tribunal simulada e página de controle
FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir fastapi==0.115.6 "uvicorn[standard]==0.32.1" httpx==0.28.1 python-multipart==0.0.20
COPY app/ /app/
ENV PYTHONUNBUFFERED=1
