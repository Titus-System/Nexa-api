FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y ca-certificates && \
    update-ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Cria diretório da aplicação
WORKDIR /app

# Copia requirements
COPY requirements.txt .

# Instala dependências
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia aplicação
COPY . .

# Cria pasta de logs
RUN mkdir -p /app/logs && chmod -R 777 /app/logs

ENV SSL_CERT_DIR /etc/ssl/certs

# Cria usuário appuser
RUN useradd -ms /bin/bash appuser && \
    chown -R appuser:appuser /app


# Usa appuser
USER appuser

# Exposição da porta
EXPOSE 5000

# Comando padrão com Gunicorn + eventlet
CMD ["gunicorn", "-k", "eventlet", "-w", "1", "run:app", "--bind", "0.0.0.0:5000"]
