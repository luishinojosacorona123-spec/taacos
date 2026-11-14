# ==============================================================================
# Dockerfile Ultra-ligero para RentMetrics · Streamlit en AWS ECS Fargate + ALB
# ==============================================================================
FROM python:3.11-slim

WORKDIR /app

# Instalar unicamente curl para el healthcheck (evita compiladores innecesarios)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias oficiales de Python (todos son wheels pre-compilados)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar tablero, datos y modelos
COPY taacos.py .
COPY clean/ ./clean/
COPY raw/ ./raw/
COPY services/ ./services/
COPY models/ ./models/
COPY .streamlit/ ./.streamlit/
COPY portafolio_inmuebles.csv .

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080 \
    STREAMLIT_SERVER_PORT=8080 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ENABLE_CORS=false \
    STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

EXPOSE 8080

HEALTHCHECK --interval=20s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8080/_stcore/health || exit 1

CMD ["streamlit", "run", "taacos.py", "--server.port=8080", "--server.address=0.0.0.0", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]
