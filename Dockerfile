FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libxml2-dev \
    libxmlsec1-dev \
    libxmlsec1-openssl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app
ENV DJANGO_SETTINGS_MODULE=repuestocontrol.settings

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
