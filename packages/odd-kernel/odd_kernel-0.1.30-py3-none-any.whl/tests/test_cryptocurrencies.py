import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from odd_kernel.datasets.cryptocurrencies import (
    Period, TimeUnit,
    BinanceClient, OrderBookManager
)

# -------------------------------
# Tests para Period
# -------------------------------

def test_to_binance_interval_valid():
    p = Period(1, TimeUnit.HOUR)
    assert p.to_binance_interval() == "1h"

def test_to_binance_interval_invalid():
    p = Period(10, TimeUnit.HOUR)
    with pytest.raises(ValueError):
        p.to_binance_interval()

# -------------------------------
# Tests para BinanceClient
# -------------------------------

@pytest.fixture
def mock_session_get():
    with patch("requests.Session.get") as mock_get:
        yield mock_get

@pytest.fixture
def client():
    return BinanceClient(api_key="test", api_secret="secret")

def test_get_exchange_info(mock_session_get, client):
    mock_response = MagicMock()
    mock_response.json.return_value = {"symbols": [{"symbol": "BTCUSDT", "status": "TRADING"}]}
    mock_response.raise_for_status.return_value = None
    mock_session_get.return_value = mock_response

    info = client.get_exchange_info()
    assert "symbols" in info
    mock_session_get.assert_called_once()

def test_get_all_tickers(mock_session_get, client):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "symbols": [
            {"symbol": "BTCUSDT", "status": "TRADING"},
            {"symbol": "ETHUSDT", "status": "BREAK"}
        ]
    }
    mock_response.raise_for_status.return_value = None
    mock_session_get.return_value = mock_response

    tickers = client.get_all_tickers()
    assert tickers == ["BTCUSDT"]

def test_get_orderbook_snapshot(mock_session_get, client):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "lastUpdateId": 123,
        "bids": [["50000.0", "1.5"]],
        "asks": [["50100.0", "2.0"]],
    }
    mock_response.raise_for_status.return_value = None
    mock_session_get.return_value = mock_response

    ob = client.get_orderbook_snapshot("BTCUSDT")
    assert ob["last_update_id"] == 123
    assert ob["bids"][0] == [50000.0, 1.5]

def test_get_historical_klines(mock_session_get, client):
    now = datetime.now()
    klines_data = [
        [now.timestamp() * 1000, "1", "2", "0.5", "1.5", "100", now.timestamp() * 1000 + 60000,
         "150", 10, "50", "75"]
    ]
    mock_response = MagicMock()
    mock_response.json.return_value = klines_data
    mock_response.raise_for_status.return_value = None
    mock_session_get.return_value = mock_response

    p = Period(1, TimeUnit.MINUTE)
    res = client.get_historical_klines("BTCUSDT", p, now - timedelta(minutes=1), now)
    assert len(res) == 1
    assert "open" in res[0]

def test_get_historical_trades(mock_session_get, client):
    now = datetime.now()
    mock_response = MagicMock()
    mock_response.json.return_value = [{
        "a": 1, "p": "30000", "q": "0.5", "f": 1, "l": 1,
        "T": now.timestamp() * 1000, "m": True
    }]
    mock_response.raise_for_status.return_value = None
    mock_session_get.return_value = mock_response

    trades = client.get_historical_trades("BTCUSDT", now - timedelta(minutes=1), now)
    assert len(trades) == 1
    assert trades[0]["price"] == 30000.0

def test_get_historical_data_invalid_type(client):
    with pytest.raises(ValueError):
        client.get_historical_data("BTCUSDT", "invalid", datetime.now())

# -------------------------------
# Tests para OrderBookManager
# -------------------------------

def test_initialize_from_snapshot(client):
    ob = OrderBookManager("BTCUSDT", client)
    client.get_orderbook_snapshot = MagicMock(return_value={
        "last_update_id": 10,
        "bids": [["50000", "1"]],
        "asks": [["50100", "2"]],
    })
    ob.initialize_from_snapshot()
    assert ob.bids[50000.0] == 1.0
    assert ob.asks[50100.0] == 2.0
    assert ob.initialized

