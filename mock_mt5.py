"""
Mock MetaTrader5 Interface for Replit Environment
Simulates MT5 functionality for testing and demonstration
"""

import time
import random
import datetime
import threading
from typing import Optional, Dict, Any, List, NamedTuple
import numpy as np

# Mock constants
TIMEFRAME_M1 = 1
TIMEFRAME_M5 = 5
TIMEFRAME_M15 = 15
TIMEFRAME_H1 = 60
TIMEFRAME_H4 = 240
TIMEFRAME_D1 = 1440

ORDER_TYPE_BUY = 0
ORDER_TYPE_SELL = 1

TRADE_ACTION_DEAL = 0
TRADE_ACTION_PENDING = 1

ORDER_FILLING_FOK = 0
ORDER_FILLING_IOC = 1

# Mock data structures
class AccountInfo(NamedTuple):
    login: int
    balance: float
    equity: float
    margin: float
    margin_free: float
    margin_level: float
    profit: float

class SymbolInfo(NamedTuple):
    name: str
    bid: float
    ask: float
    point: float
    digits: int
    spread: int
    volume_min: float
    volume_max: float
    volume_step: float
    trade_contract_size: float
    visible: bool

class Position(NamedTuple):
    ticket: int
    symbol: str
    type: int
    volume: float
    price_open: float
    price_current: float
    profit: float
    comment: str

class TradeRequest(NamedTuple):
    action: int
    symbol: str
    volume: float
    type: int
    price: float
    sl: float
    tp: float
    comment: str

class TradeResult(NamedTuple):
    retcode: int
    deal: int
    order: int
    volume: float
    price: float
    comment: str

# Global state
_initialized = False
_account_info = None
_positions = []
_symbols = {}
_market_data = {}
_last_error = (0, "No error")

def initialize(path: str = None, login: int = None, password: str = None, server: str = None) -> bool:
    """Initialize mock MT5 connection"""
    global _initialized, _account_info
    
    try:
        # Simulate connection delay
        time.sleep(0.5)
        
        _initialized = True
        _account_info = AccountInfo(
            login=12345678,
            balance=10000.0,
            equity=10000.0,
            margin=0.0,
            margin_free=10000.0,
            margin_level=999999.0,
            profit=0.0
        )
        
        # Initialize mock symbols
        _init_symbols()
        
        return True
    except Exception:
        return False

def shutdown():
    """Shutdown mock MT5 connection"""
    global _initialized, _account_info, _positions, _symbols, _market_data
    
    _initialized = False
    _account_info = None
    _positions.clear()
    _symbols.clear()
    _market_data.clear()

def last_error() -> tuple:
    """Get last error"""
    return _last_error

def version():
    """Get MT5 version info"""
    return type('Version', (), {
        'build': 3815,
        'date': '2024-01-15',
        'version': '5.0.44'
    })()

def account_info() -> Optional[AccountInfo]:
    """Get account information"""
    if not _initialized:
        return None
    return _account_info

def symbol_info(symbol: str) -> Optional[SymbolInfo]:
    """Get symbol information"""
    if not _initialized or symbol not in _symbols:
        return None
    return _symbols[symbol]

def symbol_select(symbol: str, enable: bool = True) -> bool:
    """Select symbol in market watch"""
    if not _initialized:
        return False
    
    if symbol in _symbols:
        # Update visibility
        symbol_data = _symbols[symbol]._asdict()
        symbol_data['visible'] = enable
        _symbols[symbol] = SymbolInfo(**symbol_data)
        return True
    
    return False

def positions_get(symbol: str = None) -> tuple:
    """Get open positions"""
    if not _initialized:
        return tuple()
    
    if symbol:
        return tuple(pos for pos in _positions if pos.symbol == symbol)
    return tuple(_positions)

def positions_total() -> int:
    """Get total number of positions"""
    if not _initialized:
        return 0
    return len(_positions)

def copy_rates_from_pos(symbol: str, timeframe: int, start_pos: int, count: int) -> Optional[np.ndarray]:
    """Get historical rates"""
    if not _initialized or symbol not in _symbols:
        return None
    
    # Generate mock OHLCV data
    rates = []
    base_price = _symbols[symbol].bid
    
    current_time = int(time.time()) - (count * 60)  # Start from count minutes ago
    
    for i in range(count):
        # Generate realistic price movement
        price_change = random.uniform(-0.01, 0.01) * base_price
        current_price = base_price + price_change
        
        high = current_price + random.uniform(0, 0.005) * current_price
        low = current_price - random.uniform(0, 0.005) * current_price
        open_price = base_price + random.uniform(-0.005, 0.005) * base_price
        
        volume = random.randint(100, 1000)
        
        rates.append((
            current_time + (i * 60),  # time
            open_price,               # open
            high,                     # high  
            low,                      # low
            current_price,            # close
            volume,                   # tick_volume
            0,                        # spread
            volume                    # real_volume
        ))
        
        base_price = current_price
    
    # Convert to numpy structured array
    dtype = [
        ('time', 'i8'),
        ('open', 'f8'),
        ('high', 'f8'),
        ('low', 'f8'),
        ('close', 'f8'),
        ('tick_volume', 'i8'),
        ('spread', 'i4'),
        ('real_volume', 'i8')
    ]
    
    return np.array(rates, dtype=dtype)

def order_send(request: dict) -> TradeResult:
    """Send trading order"""
    global _positions, _account_info
    
    if not _initialized:
        return TradeResult(10004, 0, 0, 0.0, 0.0, "Not initialized")
    
    try:
        symbol = request.get('symbol', '')
        action = request.get('action', TRADE_ACTION_DEAL)
        volume = request.get('volume', 0.0)
        order_type = request.get('type', ORDER_TYPE_BUY)
        price = request.get('price', 0.0)
        sl = request.get('sl', 0.0)
        tp = request.get('tp', 0.0)
        comment = request.get('comment', '')
        
        if symbol not in _symbols:
            return TradeResult(10013, 0, 0, 0.0, 0.0, "Invalid symbol")
        
        # Get current price
        symbol_info_obj = _symbols[symbol]
        current_price = symbol_info_obj.ask if order_type == ORDER_TYPE_BUY else symbol_info_obj.bid
        
        # Create position
        ticket = random.randint(100000, 999999)
        position = Position(
            ticket=ticket,
            symbol=symbol,
            type=order_type,
            volume=volume,
            price_open=current_price,
            price_current=current_price,
            profit=0.0,
            comment=comment
        )
        
        _positions.append(position)
        
        # Update account balance (simulate spread cost)
        spread_cost = volume * 10  # Simplified spread cost
        new_balance = _account_info.balance - spread_cost
        _account_info = _account_info._replace(balance=new_balance, equity=new_balance)
        
        return TradeResult(10009, ticket, ticket, volume, current_price, "Trade executed")
        
    except Exception as e:
        return TradeResult(10004, 0, 0, 0.0, 0.0, str(e))

def _init_symbols():
    """Initialize mock symbols"""
    global _symbols
    
    symbols_data = {
        'XAUUSD': {
            'bid': 2650.45,
            'ask': 2650.85,
            'point': 0.01,
            'digits': 2,
            'spread': 40
        },
        'EURUSD': {
            'bid': 1.0845,
            'ask': 1.0847,
            'point': 0.00001,
            'digits': 5,
            'spread': 2
        },
        'GBPUSD': {
            'bid': 1.2734,
            'ask': 1.2736,
            'point': 0.00001,
            'digits': 5,
            'spread': 2
        },
        'USDJPY': {
            'bid': 149.123,
            'ask': 149.145,
            'point': 0.001,
            'digits': 3,
            'spread': 22
        }
    }
    
    for symbol_name, data in symbols_data.items():
        _symbols[symbol_name] = SymbolInfo(
            name=symbol_name,
            bid=data['bid'],
            ask=data['ask'],
            point=data['point'],
            digits=data['digits'],
            spread=data['spread'],
            volume_min=0.01,
            volume_max=100.0,
            volume_step=0.01,
            trade_contract_size=100000.0,
            visible=True
        )

def _update_prices():
    """Background thread to update prices"""
    while _initialized:
        try:
            for symbol_name in _symbols:
                symbol_data = _symbols[symbol_name]._asdict()
                
                # Generate small price movements
                change = random.uniform(-0.001, 0.001)
                new_bid = symbol_data['bid'] * (1 + change)
                new_ask = new_bid + (symbol_data['spread'] * symbol_data['point'])
                
                symbol_data['bid'] = new_bid
                symbol_data['ask'] = new_ask
                
                _symbols[symbol_name] = SymbolInfo(**symbol_data)
            
            # Update position profits
            _update_position_profits()
            
            time.sleep(1)  # Update every second
            
        except Exception:
            break

def _update_position_profits():
    """Update position profits"""
    global _positions, _account_info
    
    updated_positions = []
    total_profit = 0.0
    
    for pos in _positions:
        if pos.symbol in _symbols:
            symbol_info_obj = _symbols[pos.symbol]
            current_price = symbol_info_obj.bid if pos.type == ORDER_TYPE_BUY else symbol_info_obj.ask
            
            # Calculate profit
            if pos.type == ORDER_TYPE_BUY:
                profit = (current_price - pos.price_open) * pos.volume * 100
            else:
                profit = (pos.price_open - current_price) * pos.volume * 100
            
            updated_pos = pos._replace(price_current=current_price, profit=profit)
            updated_positions.append(updated_pos)
            total_profit += profit
    
    _positions[:] = updated_positions
    
    # Update account info
    if _account_info:
        new_equity = _account_info.balance + total_profit
        _account_info = _account_info._replace(equity=new_equity, profit=total_profit)

# Start price update thread when module is imported
if _initialized:
    threading.Thread(target=_update_prices, daemon=True).start()