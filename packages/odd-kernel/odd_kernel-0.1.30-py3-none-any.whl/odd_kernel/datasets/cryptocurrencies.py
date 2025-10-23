"""
Módulo para obtener datos de Binance.
Incluye funcionalidades para:
- Obtener listado de tickers disponibles
- Obtener datos históricos (klines, trades, aggTrades)
- Conectarse a streaming en tiempo real
- Mantener libro de órdenes actualizado
"""

import requests
import json
import time
import websockets
from enum import Enum
from typing import List, Dict, Optional, Callable, Any
from datetime import datetime, timedelta
from dataclasses import dataclass


class TimeUnit(Enum):
    """Unidades de tiempo para definir períodos."""
    SECOND = "s"
    MINUTE = "m"
    HOUR = "h"
    DAY = "d"
    WEEK = "w"
    MONTH = "M"


@dataclass
class Period:
    """
    Clase para definir granularidad de datos.
    
    Attributes:
        count: Número de unidades
        unit: Unidad de tiempo (TimeUnit)
    """
    count: int
    unit: TimeUnit
    
    def to_binance_interval(self) -> str:
        """
        Convierte el período a formato de intervalo de Binance.
        
        Returns:
            String con el intervalo en formato Binance (ej: "1m", "1h", "1d")
        """
        # Validar combinaciones válidas según documentación de Binance
        valid_intervals = {
            (1, TimeUnit.SECOND): "1s",
            (1, TimeUnit.MINUTE): "1m",
            (3, TimeUnit.MINUTE): "3m",
            (5, TimeUnit.MINUTE): "5m",
            (15, TimeUnit.MINUTE): "15m",
            (30, TimeUnit.MINUTE): "30m",
            (1, TimeUnit.HOUR): "1h",
            (2, TimeUnit.HOUR): "2h",
            (4, TimeUnit.HOUR): "4h",
            (6, TimeUnit.HOUR): "6h",
            (8, TimeUnit.HOUR): "8h",
            (12, TimeUnit.HOUR): "12h",
            (1, TimeUnit.DAY): "1d",
            (3, TimeUnit.DAY): "3d",
            (1, TimeUnit.WEEK): "1w",
            (1, TimeUnit.MONTH): "1M",
        }
        
        key = (self.count, self.unit)
        if key not in valid_intervals:
            raise ValueError(
                f"Intervalo no válido: {self.count}{self.unit.value}. "
                f"Intervalos válidos: {list(valid_intervals.values())}"
            )
        
        return valid_intervals[key]


class DataType(Enum):
    """Tipos de datos disponibles en Binance."""
    KLINES = "klines"  # Datos OHLCV (velas/candlesticks)
    TRADES = "trades"  # Trades individuales
    AGG_TRADES = "aggTrades"  # Trades agregados
    DEPTH = "depth"  # Libro de órdenes (snapshot)
    TICKER_24HR = "ticker24hr"  # Estadísticas de 24 horas


class BinanceClient:
    """Cliente para interactuar con la API de Binance."""
    
    BASE_URL = "https://api.binance.com"
    WS_BASE_URL = "wss://stream.binance.com:9443"
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        """
        Inicializa el cliente de Binance.
        
        Args:
            api_key: API key de Binance (opcional, solo para endpoints privados)
            api_secret: API secret de Binance (opcional, solo para endpoints privados)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({'X-MBX-APIKEY': api_key})
    
    def get_exchange_info(self, symbol: Optional[str] = None) -> Dict:
        """
        Obtiene información del exchange incluyendo símbolos disponibles.
        
        Args:
            symbol: Símbolo específico (opcional)
            
        Returns:
            Diccionario con información del exchange
        """
        endpoint = f"{self.BASE_URL}/api/v3/exchangeInfo"
        params = {}
        
        if symbol:
            params['symbol'] = symbol.upper()
        
        response = self.session.get(endpoint, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_all_tickers(self) -> List[str]:
        """
        Obtiene el listado de todos los tickers (símbolos) disponibles.
        
        Returns:
            Lista de símbolos disponibles
        """
        exchange_info = self.get_exchange_info()
        symbols = [
            symbol_info['symbol'] 
            for symbol_info in exchange_info['symbols']
            if symbol_info['status'] == 'TRADING'
        ]
        return symbols
    
    def get_trading_pairs_info(self) -> List[Dict]:
        """
        Obtiene información detallada de todos los pares de trading.
        
        Returns:
            Lista de diccionarios con información de cada par
        """
        exchange_info = self.get_exchange_info()
        return [
            {
                'symbol': s['symbol'],
                'baseAsset': s['baseAsset'],
                'quoteAsset': s['quoteAsset'],
                'status': s['status']
            }
            for s in exchange_info['symbols']
        ]
    
    def get_historical_klines(
        self,
        symbol: str,
        period: Period,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Dict]:
        """
        Obtiene datos históricos de klines (OHLCV).
        
        Args:
            symbol: Par de trading (ej: "BTCUSDT")
            period: Período/granularidad de los datos
            start_time: Fecha de inicio
            end_time: Fecha de fin (opcional, por defecto ahora)
            limit: Número máximo de registros por request (max 1000)
            
        Returns:
            Lista de diccionarios con datos OHLCV
        """
        endpoint = f"{self.BASE_URL}/api/v3/klines"
        interval = period.to_binance_interval()
        
        if end_time is None:
            end_time = datetime.now()
        
        all_klines = []
        current_start = start_time
        
        while current_start < end_time:
            params = {
                'symbol': symbol.upper(),
                'interval': interval,
                'startTime': int(current_start.timestamp() * 1000),
                'endTime': int(end_time.timestamp() * 1000),
                'limit': limit
            }
            
            response = self.session.get(endpoint, params=params)
            response.raise_for_status()
            klines = response.json()
            
            if not klines:
                break
            
            # Convertir a formato más legible
            for kline in klines:
                all_klines.append({
                    'open_time': datetime.fromtimestamp(kline[0] / 1000),
                    'open': float(kline[1]),
                    'high': float(kline[2]),
                    'low': float(kline[3]),
                    'close': float(kline[4]),
                    'volume': float(kline[5]),
                    'close_time': datetime.fromtimestamp(kline[6] / 1000),
                    'quote_volume': float(kline[7]),
                    'trades': int(kline[8]),
                    'taker_buy_base_volume': float(kline[9]),
                    'taker_buy_quote_volume': float(kline[10])
                })
            
            # Actualizar start time para siguiente iteración
            current_start = datetime.fromtimestamp(klines[-1][6] / 1000) + timedelta(milliseconds=1)
            
            # Evitar rate limiting
            time.sleep(0.1)
        
        return all_klines
    
    def get_historical_trades(
        self,
        symbol: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Dict]:
        """
        Obtiene trades agregados históricos.
        
        Args:
            symbol: Par de trading
            start_time: Fecha de inicio
            end_time: Fecha de fin (opcional)
            limit: Número máximo de registros por request
            
        Returns:
            Lista de diccionarios con datos de trades
        """
        endpoint = f"{self.BASE_URL}/api/v3/aggTrades"
        
        if end_time is None:
            end_time = datetime.now()
        
        params = {
            'symbol': symbol.upper(),
            'startTime': int(start_time.timestamp() * 1000),
            'endTime': int(end_time.timestamp() * 1000),
            'limit': limit
        }
        
        all_trades = []
        
        while True:
            response = self.session.get(endpoint, params=params)
            response.raise_for_status()
            trades = response.json()
            
            if not trades:
                break
            
            for trade in trades:
                all_trades.append({
                    'id': trade['a'],
                    'price': float(trade['p']),
                    'quantity': float(trade['q']),
                    'first_trade_id': trade['f'],
                    'last_trade_id': trade['l'],
                    'timestamp': datetime.fromtimestamp(trade['T'] / 1000),
                    'is_buyer_maker': trade['m']
                })
            
            # Si recibimos menos del límite, ya no hay más datos
            if len(trades) < limit:
                break
            
            # Actualizar fromId para siguiente iteración
            params['fromId'] = trades[-1]['a'] + 1
            params.pop('startTime', None)
            params.pop('endTime', None)
            
            time.sleep(0.1)
        
        return all_trades
    
    def get_orderbook_snapshot(self, symbol: str, limit: int = 1000) -> Dict:
        """
        Obtiene snapshot del libro de órdenes.
        
        Args:
            symbol: Par de trading
            limit: Profundidad del libro (max 5000)
            
        Returns:
            Diccionario con bids y asks
        """
        endpoint = f"{self.BASE_URL}/api/v3/depth"
        params = {
            'symbol': symbol.upper(),
            'limit': min(limit, 5000)
        }
        
        response = self.session.get(endpoint, params=params)
        response.raise_for_status()
        data = response.json()
        
        return {
            'last_update_id': data['lastUpdateId'],
            'bids': [[float(price), float(qty)] for price, qty in data['bids']],
            'asks': [[float(price), float(qty)] for price, qty in data['asks']]
        }
    
    def get_24hr_ticker(self, symbol: Optional[str] = None) -> Dict | List[Dict]:
        """
        Obtiene estadísticas de 24 horas.
        
        Args:
            symbol: Par de trading (opcional, si no se especifica devuelve todos)
            
        Returns:
            Diccionario o lista de diccionarios con estadísticas
        """
        endpoint = f"{self.BASE_URL}/api/v3/ticker/24hr"
        params = {}
        
        if symbol:
            params['symbol'] = symbol.upper()
        
        response = self.session.get(endpoint, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_historical_data(
        self,
        symbol: str,
        data_type: DataType,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        period: Optional[Period] = None,
        **kwargs
    ) -> List[Dict]:
        """
        Método unificado para obtener datos históricos.
        
        Args:
            symbol: Par de trading
            data_type: Tipo de dato a obtener
            start_time: Fecha de inicio
            end_time: Fecha de fin
            period: Período (requerido para KLINES)
            **kwargs: Argumentos adicionales
            
        Returns:
            Lista de datos históricos
        """
        if data_type == DataType.KLINES:
            if period is None:
                raise ValueError("Period es requerido para DataType.KLINES")
            return self.get_historical_klines(symbol, period, start_time, end_time)
        
        elif data_type == DataType.AGG_TRADES:
            return self.get_historical_trades(symbol, start_time, end_time)
        
        elif data_type == DataType.TICKER_24HR:
            return [self.get_24hr_ticker(symbol)]
        
        elif data_type == DataType.DEPTH:
            return [self.get_orderbook_snapshot(symbol)]
        
        else:
            raise ValueError(f"DataType no soportado: {data_type}")


class BinanceWebSocketClient:
    """Cliente WebSocket para streaming en tiempo real de Binance."""
    
    WS_BASE_URL = "wss://stream.binance.com:9443"
    
    def __init__(self):
        """Inicializa el cliente WebSocket."""
        self.connections: Dict[str, Any] = {}
        self.callbacks: Dict[str, Callable] = {}
    
    async def connect_stream(
        self,
        streams: List[str],
        callback: Callable[[Dict], None]
    ):
        """
        Conecta a uno o más streams de WebSocket.
        
        Args:
            streams: Lista de nombres de streams (ej: ["btcusdt@trade", "ethusdt@ticker"])
            callback: Función a llamar cuando se reciban datos
        """
        stream_path = "/stream?streams=" + "/".join(streams)
        url = f"{self.WS_BASE_URL}{stream_path}"
        
        async with websockets.connect(url) as websocket:
            print(f"Conectado a streams: {streams}")
            
            async for message in websocket:
                data = json.loads(message)
                callback(data)
    
    async def connect_kline_stream(
        self,
        symbols: List[str],
        interval: str,
        callback: Callable[[Dict], None]
    ):
        """
        Conecta a stream de klines para múltiples símbolos.
        
        Args:
            symbols: Lista de símbolos
            interval: Intervalo (ej: "1m", "1h")
            callback: Función callback
        """
        streams = [f"{symbol.lower()}@kline_{interval}" for symbol in symbols]
        await self.connect_stream(streams, callback)
    
    async def connect_trade_stream(
        self,
        symbols: List[str],
        callback: Callable[[Dict], None]
    ):
        """
        Conecta a stream de trades para múltiples símbolos.
        
        Args:
            symbols: Lista de símbolos
            callback: Función callback
        """
        streams = [f"{symbol.lower()}@trade" for symbol in symbols]
        await self.connect_stream(streams, callback)
    
    async def connect_ticker_stream(
        self,
        symbols: List[str],
        callback: Callable[[Dict], None]
    ):
        """
        Conecta a stream de ticker para múltiples símbolos.
        
        Args:
            symbols: Lista de símbolos
            callback: Función callback
        """
        streams = [f"{symbol.lower()}@ticker" for symbol in symbols]
        await self.connect_stream(streams, callback)


class OrderBookManager:
    """Gestor de libro de órdenes en tiempo real."""
    
    def __init__(self, symbol: str, client: BinanceClient):
        """
        Inicializa el gestor de orderbook.
        
        Args:
            symbol: Par de trading
            client: Cliente de Binance para obtener snapshot inicial
        """
        self.symbol = symbol.upper()
        self.client = client
        self.bids: Dict[float, float] = {}  # precio -> cantidad
        self.asks: Dict[float, float] = {}  # precio -> cantidad
        self.last_update_id = 0
        self.initialized = False
        self.buffer = []
    
    def initialize_from_snapshot(self, limit: int = 1000):
        """
        Inicializa el orderbook desde un snapshot de la API REST.
        
        Args:
            limit: Profundidad del snapshot
        """
        snapshot = self.client.get_orderbook_snapshot(self.symbol, limit)
        
        self.last_update_id = snapshot['last_update_id']
        
        # Inicializar bids y asks
        self.bids = {float(price): float(qty) for price, qty in snapshot['bids']}
        self.asks = {float(price): float(qty) for price, qty in snapshot['asks']}
        
        self.initialized = True
        print(f"OrderBook inicializado para {self.symbol} (lastUpdateId: {self.last_update_id})")
    
    def process_depth_update(self, data: Dict):
        """
        Procesa una actualización del depth stream.
        
        Args:
            data: Datos del depth update
        """
        # Si es un combined stream, extraer data
        if 'data' in data:
            data = data['data']
        
        # Verificar que sea el símbolo correcto
        if data.get('s', '').upper() != self.symbol:
            return
        
        # Si no está inicializado, buffear eventos
        if not self.initialized:
            self.buffer.append(data)
            return
        
        # Verificar secuencia de updates
        first_update_id = data['U']
        final_update_id = data['u']
        
        # Descartar eventos antiguos
        if final_update_id <= self.last_update_id:
            return
        
        # Verificar que no haya gap
        if first_update_id > self.last_update_id + 1:
            print("Gap detectado en updates! Reinicializando...")
            self.initialized = False
            self.initialize_from_snapshot()
            return
        
        # Aplicar updates de bids
        for bid in data['b']:
            price = float(bid[0])
            qty = float(bid[1])
            
            if qty == 0:
                self.bids.pop(price, None)
            else:
                self.bids[price] = qty
        
        # Aplicar updates de asks
        for ask in data['a']:
            price = float(ask[0])
            qty = float(ask[1])
            
            if qty == 0:
                self.asks.pop(price, None)
            else:
                self.asks[price] = qty
        
        self.last_update_id = final_update_id
    
    def process_buffered_events(self):
        """Procesa eventos que fueron bufferados antes de la inicialización."""
        if not self.initialized:
            return
        
        for event in self.buffer:
            if event['u'] > self.last_update_id:
                self.process_depth_update(event)
        
        self.buffer.clear()
    
    def get_best_bid(self) -> Optional[tuple[float, float]]:
        """Obtiene el mejor bid (precio más alto)."""
        if not self.bids:
            return None
        best_price = max(self.bids.keys())
        return (best_price, self.bids[best_price])
    
    def get_best_ask(self) -> Optional[tuple[float, float]]:
        """Obtiene el mejor ask (precio más bajo)."""
        if not self.asks:
            return None
        best_price = min(self.asks.keys())
        return (best_price, self.asks[best_price])
    
    def get_spread(self) -> Optional[float]:
        """Calcula el spread entre bid y ask."""
        best_bid = self.get_best_bid()
        best_ask = self.get_best_ask()
        
        if best_bid and best_ask:
            return best_ask[0] - best_bid[0]
        return None
    
    def get_orderbook_snapshot(self, depth: int = 10) -> Dict:
        """
        Obtiene un snapshot del orderbook actual.
        
        Args:
            depth: Número de niveles a incluir
            
        Returns:
            Diccionario con bids y asks ordenados
        """
        sorted_bids = sorted(self.bids.items(), key=lambda x: x[0], reverse=True)[:depth]
        sorted_asks = sorted(self.asks.items(), key=lambda x: x[0])[:depth]
        
        return {
            'symbol': self.symbol,
            'last_update_id': self.last_update_id,
            'bids': [[price, qty] for price, qty in sorted_bids],
            'asks': [[price, qty] for price, qty in sorted_asks],
            'best_bid': self.get_best_bid(),
            'best_ask': self.get_best_ask(),
            'spread': self.get_spread()
        }
    
    async def start_stream(self):
        """Inicia el stream de depth updates."""
        url = f"{BinanceWebSocketClient.WS_BASE_URL}/ws/{self.symbol.lower()}@depth"
        
        async with websockets.connect(url) as websocket:
            print(f"Stream de depth iniciado para {self.symbol}")
            
            async for message in websocket:
                data = json.loads(message)
                self.process_depth_update(data)

