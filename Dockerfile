# Usar imagen base de Alpine con Python
FROM python:3.11-alpine

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias para compilar paquetes Python
# gcc, musl-dev, linux-headers: para compilar extensiones de Python
# libffi-dev: para cffi (requerido por algunas dependencias)
# openssl-dev: para soporte SSL
RUN apk add --no-cache \
    gcc \
    musl-dev \
    linux-headers \
    libffi-dev \
    openssl-dev \
    && rm -rf /var/cache/apk/*

# Copiar archivo de requerimientos
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY app.py version.py .

# Exponer el puerto 3010
EXPOSE 3010

# Comando para ejecutar la aplicación
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "3010"]
