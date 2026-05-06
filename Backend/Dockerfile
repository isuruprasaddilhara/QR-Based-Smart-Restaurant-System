FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y gcc libpq-dev

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Load env variables
ENV DJANGO_SETTINGS_MODULE=scan2serve.settings

# Collect static
RUN python manage.py collectstatic --noinput

# Run server
CMD ["gunicorn", "--workers=3", "--bind=0.0.0.0:8000", "scan2serve.wsgi:application"]