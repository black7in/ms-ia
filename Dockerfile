FROM python:3.11-slim AS base

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --timeout=120 -r requirements.txt


FROM base AS dev

COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

ENV FLASK_DEBUG=true
ENV FLASK_APP=app.main:create_app

EXPOSE 8002

CMD ["python", "-c", "from app.main import create_app; app = create_app(); app.run(host='0.0.0.0', port=8002, debug=True)"]


FROM base AS production

COPY app/ app/
COPY .env .env

EXPOSE 8002

CMD ["gunicorn", "--bind", "0.0.0.0:8002", "--workers", "2", "--timeout", "30", "app.main:create_app()"]
