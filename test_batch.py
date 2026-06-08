from fastapi.testclient import TestClient
from app import app
import json

client = TestClient(app)

def test_batch_prices():
    # Test valid tickers
    response = client.post("/precios", json={"tickers": ["AAPL", "MSFT"]})
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test with invalid ticker
    response = client.post("/precios", json={"tickers": ["AAPL", "INVALID_TICKER_NAME_12345"]})
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

if __name__ == "__main__":
    test_batch_prices()
