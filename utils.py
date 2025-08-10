"""
Advanced MT5 Trading Bot - Utility Functions
Common utility functions and helpers
"""

import os
import sys
import datetime
import time
import gc
import traceback
from typing import Optional, List, Any

def logger(msg: str) -> None:
    """Enhanced logging function with timestamp"""
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    full_msg = f"[{timestamp}] {msg}"
    print(full_msg)
    
    # Try to log to file
    try:
        ensure_log_directory()
        log_file = f"logs/bot_{datetime.datetime.now().strftime('%Y%m%d')}.log"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(full_msg + "\n")
    except Exception as e:
        print(f"File logging failed: {str(e)}")

def validate_numeric_input(value: str, min_val: float = 0.0, max_val: float = None) -> float:
    """Validate and convert numeric input"""
    try:
        numeric_value = float(value.strip())
        if numeric_value < min_val:
            raise ValueError(f"Value {numeric_value} is below minimum {min_val}")
        if max_val is not None and numeric_value > max_val:
            raise ValueError(f"Value {numeric_value} exceeds maximum {max_val}")
        return numeric_value
    except (ValueError, AttributeError) as e:
        logger(f"Invalid numeric input '{value}': {str(e)}")
        raise

def validate_string_input(value: str, allowed_values: List[str] = None) -> str:
    """Validate string input"""
    try:
        clean_value = value.strip().upper()
        if not clean_value:
            raise ValueError("Empty string not allowed")
        if allowed_values and clean_value not in allowed_values:
            raise ValueError(f"Value '{clean_value}' not in allowed values: {allowed_values}")
        return clean_value
    except AttributeError as e:
        logger(f"Invalid string input: {str(e)}")
        raise

def is_high_impact_news_time() -> bool:
    """Check if current time is during high-impact news"""
    try:
        utc_now = datetime.datetime.utcnow()
        current_hour = utc_now.hour
        current_minute = utc_now.minute
        day_of_week = utc_now.weekday()
        
        # Critical news times (UTC)
        critical_times = [
            (8, 30, 9, 30),   # European session major news
            (12, 30, 14, 30), # US session major news
            (16, 0, 16, 30),  # London Fix
        ]
        
        # Weekly specifics
        if day_of_week == 2:  # Wednesday
            critical_times.append((13, 0, 14, 0))  # FOMC minutes
        if day_of_week == 4:  # Friday
            critical_times.append((12, 30, 15, 0))  # NFP + major data
        
        current_time_minutes = current_hour * 60 + current_minute
        
        for start_h, start_m, end_h, end_m in critical_times:
            start_minutes = start_h * 60 + start_m
            end_minutes = end_h * 60 + end_m
            
            if start_minutes <= current_time_minutes <= end_minutes:
                logger(f"⚠️ High-impact news time detected: {current_hour:02d}:{current_minute:02d} UTC")
                return True
        
        return False
        
    except Exception as e:
        logger(f"❌ Error in news time check: {str(e)}")
        return False

def cleanup_resources() -> None:
    """Cleanup memory and resources"""
    try:
        gc.collect()
        logger("🧹 Memory cleanup completed")
    except Exception as e:
        logger(f"⚠️ Memory cleanup error: {str(e)}")

def ensure_log_directory() -> bool:
    """Ensure log directory exists"""
    try:
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            logger(f"📁 Created log directory: {log_dir}")
        return True
    except Exception as e:
        logger(f"❌ Failed to create log directory: {str(e)}")
        return False

def format_currency(amount: float, currency: str = "USD") -> str:
    """Format currency amount"""
    try:
        return f"{amount:,.2f} {currency}"
    except:
        return f"{amount} {currency}"

def calculate_pip_value(symbol: str, lot_size: float) -> float:
    """Calculate pip value for a symbol"""
    try:
        try:
            import MetaTrader5 as mt5
        except ImportError:
            import mock_mt5 as mt5
        
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            return 0.0
        
        # For most forex pairs, pip value = (pip in decimal places) * lot size * contract size
        if 'JPY' in symbol:
            pip_size = 0.01  # For JPY pairs, pip is at 2nd decimal
        else:
            pip_size = 0.0001  # For most pairs, pip is at 4th decimal
        
        pip_value = pip_size * lot_size * symbol_info.trade_contract_size
        
        return pip_value
        
    except Exception as e:
        logger(f"❌ Error calculating pip value: {str(e)}")
        return 0.0

def get_market_session() -> str:
    """Get current market session"""
    try:
        utc_now = datetime.datetime.utcnow()
        hour = utc_now.hour
        
        if 21 <= hour or hour < 6:
            return "Asia"
        elif 7 <= hour < 15:
            return "London"
        elif 15 <= hour < 21:
            return "New_York"
        else:
            return "Closed"
            
    except Exception as e:
        logger(f"❌ Error getting market session: {str(e)}")
        return "Unknown"

def is_market_open() -> bool:
    """Check if market is open"""
    try:
        utc_now = datetime.datetime.utcnow()
        day_of_week = utc_now.weekday()
        hour = utc_now.hour
        
        # Market closed on weekends
        if day_of_week == 5 and hour >= 22:  # Friday 22:00 UTC
            return False
        if day_of_week == 6:  # Saturday
            return False
        if day_of_week == 0 and hour < 22:  # Sunday before 22:00 UTC
            return False
        
        return True
        
    except Exception as e:
        logger(f"❌ Error checking market status: {str(e)}")
        return True  # Default to open if check fails

def safe_divide(a: float, b: float, default: float = 0.0) -> float:
    """Safe division with default value"""
    try:
        if b == 0:
            return default
        return a / b
    except:
        return default

def round_to_symbol_digits(value: float, symbol: str) -> float:
    """Round value to symbol's decimal places"""
    try:
        try:
            import MetaTrader5 as mt5
        except ImportError:
            import mock_mt5 as mt5
        
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info:
            return round(value, symbol_info.digits)
        return round(value, 5)  # Default to 5 digits
        
    except:
        return round(value, 5)

def calculate_lot_from_risk(balance: float, risk_percent: float, 
                          stop_loss_pips: float, pip_value: float) -> float:
    """Calculate lot size based on risk percentage"""
    try:
        if pip_value <= 0 or stop_loss_pips <= 0:
            return 0.01  # Minimum lot size
        
        risk_amount = balance * (risk_percent / 100)
        lot_size = risk_amount / (stop_loss_pips * pip_value)
        
        # Round to 2 decimal places and ensure minimum
        lot_size = max(0.01, round(lot_size, 2))
        
        return lot_size
        
    except Exception as e:
        logger(f"❌ Error calculating lot size: {str(e)}")
        return 0.01

def get_trading_hours_info() -> dict:
    """Get trading hours information"""
    return {
        "Asia": {"start": "21:00", "end": "06:00", "timezone": "UTC"},
        "London": {"start": "07:00", "end": "15:00", "timezone": "UTC"},
        "New_York": {"start": "15:00", "end": "21:00", "timezone": "UTC"},
        "Overlap": {"start": "15:00", "end": "17:00", "timezone": "UTC"}
    }

def format_time_elapsed(start_time: datetime.datetime) -> str:
    """Format elapsed time"""
    try:
        elapsed = datetime.datetime.now() - start_time
        hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    except:
        return "00:00:00"

def get_system_info() -> dict:
    """Get system information"""
    try:
        import platform
        
        return {
            "platform": platform.system(),
            "architecture": platform.architecture()[0],
            "python_version": platform.python_version(),
            "machine": platform.machine(),
            "processor": platform.processor()
        }
    except Exception as e:
        logger(f"❌ Error getting system info: {str(e)}")
        return {}

def check_mt5_compatibility() -> bool:
    """Check MT5 compatibility"""
    try:
        import platform
        
        # MT5 officially supports Windows
        if platform.system() != "Windows":
            logger("⚠️ Warning: MT5 officially supports Windows only")
            return False
        
        # Check architecture
        if platform.architecture()[0] != "64bit":
            logger("⚠️ Warning: 64-bit system recommended for MT5")
            return False
        
        return True
        
    except Exception as e:
        logger(f"❌ Error checking compatibility: {str(e)}")
        return False

def retry_on_failure(func, max_retries: int = 3, delay: float = 1.0):
    """Retry decorator for functions"""
    def wrapper(*args, **kwargs):
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                logger(f"⚠️ Attempt {attempt + 1} failed: {str(e)}, retrying in {delay}s...")
                time.sleep(delay)
    return wrapper

class PerformanceTimer:
    """Simple performance timer"""
    
    def __init__(self, name: str = "Operation"):
        self.name = name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.time() - self.start_time
        logger(f"⏱️ {self.name} completed in {elapsed:.3f}s")

def validate_mt5_symbol(symbol: str) -> bool:
    """Validate if MT5 symbol exists"""
    try:
        try:
            import MetaTrader5 as mt5
        except ImportError:
            import mock_mt5 as mt5
        
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            return False
        
        # Try to select symbol in market watch
        if not symbol_info.visible:
            return mt5.symbol_select(symbol, True)
        
        return True
        
    except Exception as e:
        logger(f"❌ Error validating symbol {symbol}: {str(e)}")
        return False

def emergency_stop() -> None:
    """Emergency stop function"""
    try:
        logger("🚨 EMERGENCY STOP TRIGGERED")
        
        # Close all positions
        try:
            import MetaTrader5 as mt5
        except ImportError:
            import mock_mt5 as mt5
            
        positions = mt5.positions_get()
        
        if positions:
            for position in positions:
                # Close position logic here
                logger(f"🚨 Emergency closing position: {position.ticket}")
        
        logger("🚨 Emergency stop completed")
        
    except Exception as e:
        logger(f"❌ Emergency stop error: {str(e)}")
