from fastapi import FastAPI, HTTPException, Security, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader, APIKeyQuery
import yfinance as yf
from datetime import datetime, timedelta
import uvicorn
import logging
import os
from version import __version__, __version_info__

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="YFinance Simple API", version=__version__)

# Habilitar CORS para aceptar cualquier cliente
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key configuration
API_KEY = os.environ.get("API_KEY", "")
API_KEY_NAME = "X-API-Key"

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
api_key_query = APIKeyQuery(name="api_key", auto_error=False)


async def get_api_key(
    key_header: str = Security(api_key_header),
    key_query: str = Security(api_key_query),
):
    if not API_KEY:
        raise HTTPException(status_code=500, detail="API_KEY no configurada en el servidor")
    provided = key_header or key_query
    if provided == API_KEY:
        return provided
    raise HTTPException(status_code=403, detail="API key inválida o ausente")


# Caché para el tipo de cambio USD/EUR
exchange_rate_cache = {
    'rate': None,
    'timestamp': None
}

CACHE_DURATION_MINUTES = 5

def get_usdeur_rate():
    """
    Obtiene el tipo de cambio USD/EUR (cuántos euros vale 1 dólar).
    Usa caché si la última consulta fue hace menos de 5 minutos.
    """
    now = datetime.now()

    # Verificar si hay caché válido
    if (exchange_rate_cache['rate'] is not None and
        exchange_rate_cache['timestamp'] is not None):

        time_diff = now - exchange_rate_cache['timestamp']
        if time_diff < timedelta(minutes=CACHE_DURATION_MINUTES):
            logger.info(f"Usando tipo de cambio en caché: {exchange_rate_cache['rate']}")
            return exchange_rate_cache['rate']

    # Consultar nuevo tipo de cambio
    logger.info("Consultando nuevo tipo de cambio USD/EUR...")

    try:
        ticker = yf.Ticker("USDEUR=X")
        data = ticker.history(period="5d")  # Use 5 days to increase chance of getting data
        logger.info(f"Data retrieved for USDEUR=X, shape: {data.shape}, empty: {data.empty}")

        if not data.empty:
            # Usar el precio de cierre más reciente
            rate = data['Close'].iloc[-1]

            # Actualizar caché
            exchange_rate_cache['rate'] = rate
            exchange_rate_cache['timestamp'] = now

            logger.info(f"Nuevo tipo de cambio obtenido: {rate}")
            return rate

    except Exception as e:
        logger.error(f"Error al obtener tipo de cambio: {str(e)}")

    # If we have cached data but it's old, use it as fallback
    if exchange_rate_cache['rate'] is not None:
        logger.warning("Usando tipo de cambio en caché (expirado) como fallback")
        return exchange_rate_cache['rate']

    raise ValueError("No se pudo obtener el tipo de cambio USD/EUR")


def get_ticker_price_in_euros(ticker):
    """
    Obtiene el precio actual de un ticker y lo convierte a euros.
    """
    try:
        # Obtener el tipo de cambio USD/EUR
        usdeur_rate = get_usdeur_rate()

        # Obtener el precio del ticker
        logger.info(f"Consultando precio de {ticker}...")
        ticker_obj = yf.Ticker(ticker)

        # Try with 1 day first, then 5 days if that fails
        data = ticker_obj.history(period="1d")

        if data.empty:
            logger.warning(f"No data for {ticker} with period=1d, trying period=5d...")
            data = ticker_obj.history(period="5d")

        if data.empty:
            raise ValueError(f"No se pudo obtener datos para el ticker {ticker}")

        # Usar el precio de cierre más reciente (en USD)
        price_usd = data['Close'].iloc[-1]

        # Convertir a euros
        # USD/EUR rate indica cuántos EUR vale 1 USD
        # Para convertir USD a EUR: USD * (USD/EUR rate)
        price_eur = price_usd * usdeur_rate

        logger.info(f"Precio obtenido - USD: {price_usd}, EUR: {price_eur}")
        return {
            'ticker': ticker,
            'precio_usd': round(price_usd, 2),
            'precio_eur': round(price_eur, 2),
            'tipo_cambio_usdeur': round(usdeur_rate, 4),
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error al obtener precio: {str(e)}", exc_info=True)
        raise


@app.get('/precio/{ticker}')
async def get_precio(ticker: str, api_key: str = Security(get_api_key)):
    """
    Endpoint para obtener el precio de un ticker en euros.
    """
    try:
        result = get_ticker_price_in_euros(ticker)
        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail={
            'error': str(e),
            'ticker': ticker
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail={
            'error': f'Error interno del servidor: {str(e)}',
            'ticker': ticker
        })


@app.get('/health')
async def health():
    """
    Endpoint de health check.
    """
    return {
        'status': 'ok',
        'version': __version__,
        'cache_info': {
            'has_cache': exchange_rate_cache['rate'] is not None,
            'cache_timestamp': exchange_rate_cache['timestamp'].isoformat() if exchange_rate_cache['timestamp'] else None
        }
    }


@app.get('/version')
async def version():
    """
    Endpoint para obtener la versión de la API.
    """
    return {
        'version': __version__,
        'version_info': __version_info__,
        'api_name': 'YFinance Simple API'
    }


@app.get('/info')
async def info():
    """
    Endpoint que describe los endpoints disponibles y cómo usarlos.
    """
    info_payload = {
        'api': 'YFinance Simple API',
        'version': __version__,
        'endpoints': [
            {
                'path': '/precio/{ticker}',
                'method': 'GET',
                'description': 'Devuelve el precio del ticker en USD y convertido a EUR.',
                'usage_example': '/precio/AAPL'
            },
            {
                'path': '/health',
                'method': 'GET',
                'description': 'Health check básico con estado y caché.'
            },
            {
                'path': '/version',
                'method': 'GET',
                'description': 'Información de versión de la API.'
            }
        ],
        'examples': {
            'curl_precio_header': "curl -s -H 'X-API-Key: TU_API_KEY' 'http://localhost:3010/precio/AAPL'",
            'curl_precio_query': "curl -s 'http://localhost:3010/precio/AAPL?api_key=TU_API_KEY'",
            'httpie_precio': "http GET :3010/precio/AAPL X-API-Key:TU_API_KEY"
        },
        'notes': 'Reemplaza el puerto y host según donde esté desplegada la API.'
    }

    return JSONResponse(content=info_payload)


if __name__ == '__main__':
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3010
    logger.info(f"=" * 60)
    logger.info(f"Starting YFinance Simple API v{__version__}")
    logger.info(f"Version info: {__version_info__}")
    logger.info(f"Port: {port}")
    logger.info(f"=" * 60)
    uvicorn.run(app, host='0.0.0.0', port=port)
