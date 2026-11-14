# ==============================================================================
# Dockerfile para RentMetrics · Gestion Inteligente en AWS ECS Fargate + ALB
# Dashboard Oficial Streamlit (taacos.py)
# ==============================================================================
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema mínimas
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Instalar requerimientos de Python (Streamlit, Pandas, Sklearn, Statsmodels, etc.)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente completo de la aplicación, datos limpios y modelos
COPY taacos.py .
COPY clean/ ./clean/
COPY raw/ ./raw/
COPY services/ ./services/
COPY models/ ./models/
COPY .streamlit/ ./.streamlit/
COPY portafolio_inmuebles.csv .

# Variables de entorno para Streamlit optimizadas para AWS ALB
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

# Healthcheck interno del contenedor sobre el endpoint oficial de Streamlit
HEALTHCHECK --interval=20s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8080/_stcore/health || exit 1

# Ejecutar el Tablero RentMetrics en el puerto 8080
CMD ["streamlit", "run", "taacos.py", "--server.port=8080", "--server.address=0.0.0.0", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]
