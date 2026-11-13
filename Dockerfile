# Imagen base optimizada con Python 3.12
FROM python:3.12-slim

# Evitar generación de archivos .pyc y habilitar buffers limpios
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema para OpenCV y procesamiento de imagen
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias
COPY pyproject.toml* requirements.txt* ./

# Instalar dependencias Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    pymupdf \
    python-docx \
    rapidocr-onnxruntime \
    streamlit \
    rich \
    pandas \
    pytest

# Copiar el código fuente y assets
COPY . /app

# Puerto oficial de Streamlit
EXPOSE 8501

# Configuración de salud del contenedor
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Comando de ejecución en modo servidor
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.enableCORS=false", "--server.headless=true"]
