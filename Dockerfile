FROM python:3.12-slim

WORKDIR /app

# Build-time değerler; CI tarafından --build-arg ile geçirilir
ARG APP_VERSION=dev
ARG BUILD_SHA=unknown

# Runtime'da da erişilebilir olsun (ENVIRONMENT ise K8s tarafından inject edilir)
ENV APP_VERSION=${APP_VERSION}
ENV BUILD_SHA=${BUILD_SHA}

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
