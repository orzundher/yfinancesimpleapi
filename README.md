# YFinance Simple API

API REST simple en Python que consulta precios de Yahoo Finance y los convierte a euros.

## Características

- Endpoint REST para obtener precios de tickers en euros
- Conversión automática USD a EUR
- Sistema de caché para el tipo de cambio (5 minutos)
- Puerto configurable (por defecto 3010)

## Instalación

### Opción 1: Instalación local

```bash
pip install -r requirements.txt
```

### Opción 2: Docker

```bash
# Construir la imagen
docker build -t yfinance-api .

# Ejecutar el contenedor
docker run -d -p 3010:3010 --name yfinance-api yfinance-api

# Ver logs
docker logs -f yfinance-api

# Detener el contenedor
docker stop yfinance-api

# Eliminar el contenedor
docker rm yfinance-api
```

### Opción 3: Docker Compose (recomendado)

**En Windows:**
```bash
# Ejecutar el script build.bat
build.bat
```

**En Linux/Mac:**
```bash
# Construir y levantar servicios
docker-compose up --build -d

# Ver logs
docker-compose logs -f

# Detener servicios
docker-compose stop

# Detener y eliminar contenedores
docker-compose down

# Reiniciar servicios
docker-compose restart
```

## Uso

### Iniciar el servidor

**Con Python:**
```bash
python app.py
```

**Con Docker:**
```bash
docker run -d -p 3010:3010 --name yfinance-api yfinance-api
```

**Con Docker Compose:**
```bash
# Windows
build.bat

# Linux/Mac
docker-compose up -d
```

El servidor se iniciará en `http://localhost:3010`

### Endpoints

#### GET /precio/{ticker}

Obtiene el precio de un ticker en euros.

**Ejemplo:**
```bash
curl http://localhost:3010/precio/AAPL
```

**Respuesta:**
```json
{
  "ticker": "AAPL",
  "precio_usd": 150.25,
  "precio_eur": 138.42,
  "tipo_cambio_eurusd": 1.086,
  "timestamp": "2025-12-07T10:30:45.123456"
}
```

#### GET /health

Verifica el estado de la API y el caché.

**Ejemplo:**
```bash
curl http://localhost:3010/health
```

**Respuesta:**
```json
{
  "status": "ok",
  "cache_info": {
    "has_cache": true,
    "cache_timestamp": "2025-12-07T10:30:00.000000"
  }
}
```

## Documentación interactiva

FastAPI genera documentación automática:

- Swagger UI: `http://localhost:3010/docs`
- ReDoc: `http://localhost:3010/redoc`

## Funcionamiento

1. Consulta el tipo de cambio EUR/USD de Yahoo Finance
2. Almacena el tipo de cambio en caché por 5 minutos
3. Consulta el precio del ticker solicitado
4. Convierte el precio de USD a EUR usando el tipo de cambio
5. Devuelve los datos en formato JSON
