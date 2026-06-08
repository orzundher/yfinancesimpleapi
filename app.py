from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yfinance as yf
from datetime import datetime, timedelta
from typing import List, Union
import uvicorn
import logging
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


def get_ticker_price_in_euros(ticker, usdeur_rate=None):
    """
    Obtiene el precio actual de un ticker y lo convierte a euros.
    Si não se proporciona usdeur_rate, se obtiene uno nuevo (usando caché).
    """
    try:
        # Obtener el tipo de cambio USD/EUR si no se proporcionó
        if usdeur_rate is None:
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
        logger.error(f"Error al obtener precio: {str(e)}")
        raise


class TickersRequest(BaseModel):
    tickers: List[str]


@app.get('/precio/{ticker}')
async def get_precio(ticker: str):
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


@app.post('/precios')
async def get_precios_batch(request: TickersRequest):
    """
    Endpoint para obtener los precios de múltiples tickers en una sola llamada.
    Optimiza la conversión a euros obteniendo el tipo de cambio una sola vez.
    """
    try:
        # Obtener el tipo de cambio una sola vez para toda la lista
        usdeur_rate = get_usdeur_rate()
        
        results = []
        for ticker in request.tickers:
            try:
                # Pasar el rate ya obtenido para optimizar
                price_data = get_ticker_price_in_euros(ticker, usdeur_rate=usdeur_rate)
                results.append(price_data)
            except Exception:
                # En caso de error para un ticker, devolver false en esa posición
                logger.warning(f"Error al procesar ticker {ticker} en lote, devolviendo false")
                results.append(False)
        
        return results

    except Exception as e:
        logger.error(f"Error general en endpoint batch: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


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
                'path': '/precios',
                'method': 'POST',
                'description': 'Devuelve una lista de precios para múltiples tickers. Optimizado para conversión EUR.',
                'usage_example': 'POST /precios {"tickers": ["AAPL", "MSFT"]}'
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
            'curl_precio': "curl -s 'http://localhost:3010/precio/AAPL'",
            'httpie_precio': "http GET :3010/precio/AAPL"
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
