FROM python:3.12-slim

# Variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código
COPY . .

# Coleta arquivos estáticos
RUN python manage.py collectstatic --noinput

# Expõe a porta
EXPOSE $PORT

# Script de inicialização
CMD ["sh", "-c", "python manage.py migrate && gunicorn academico_api.wsgi:application --bind 0.0.0.0:$PORT"]
