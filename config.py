"""
Advanced MT5 Trading Bot - Configuration Manager
Handles loading, saving, and managing bot configuration
"""

import json
import os
from typing import Dict, Any, Optional
from utils import logger

class ConfigManager:
    """Configuration management class"""
    
    def __init__(self, config_file: str = "config.json"):
        """Initialize configuration manager"""
        self.config_file = config_file
        self.config = self._get_default_config()
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            # General settings
            "version": "2.0",
            "debug_mode": False,
            
            # MT5 Connection
            "auto_connect": True,
            "connection_timeout": 10,
            "max_reconnect_attempts": 5,
            
            # Trading settings
            "symbol": "XAUUSD",
            "strategy": "Scalping",
            "lot_size": 0.01,
            "auto_lot": True,
            "risk_percent": 1.0,
            
            # TP/SL settings
            "tp_value": 50,
            "tp_unit": "pips",
            "sl_value": 25,
            "sl_unit": "pips",
            "trailing_stop": False,
            "trailing_distance": 15,
            
            # Risk management
            "max_daily_loss": 5.0,
            "daily_profit_target": 10.0,
            "max_positions": 10,
            "max_loss_streak": 3,
            "max_drawdown": 5.0,
            "auto_stop_drawdown": True,
            
            # AI settings
            "ai_enabled": True,
            "ai_confidence": 0.75,
            "ai_model_type": "ensemble",
            
            # Technical indicators
            "indicator_rsi": True,
            "indicator_macd": True,
            "indicator_ema": True,
            "indicator_atr": True,
            "indicator_bollinger_bands": True,
            
            # Strategy parameters
            "scalping_min_profit": 5,
            "hft_max_spread": 2,
            "intraday_pivot_levels": True,
            "arbitrage_threshold": 0.001,
            
            # Session settings
            "session_asia": True,
            "session_london": True,
            "session_new_york": True,
            "session_overlap_london_ny": True,
            
            # News filter
            "avoid_news": True,
            "news_buffer_minutes": 30,
            
            # Telegram settings
            "telegram_enabled": False,
            "telegram_token": os.getenv("TELEGRAM_TOKEN", ""),
            "telegram_chat_id": os.getenv("TELEGRAM_CHAT_ID", ""),
            "telegram_notifications": {
                "trades": True,
                "errors": True,
                "daily_summary": True,
                "connections": False
            },
            
            # Logging
            "log_level": "INFO",
            "log_to_file": True,
            "max_log_files": 30,
            
            # Performance
            "update_interval": 1500,
            "cleanup_interval": 300,
            "memory_cleanup_enabled": True,
            
            # Backtest settings
            "backtest_start": "2024-01-01",
            "backtest_end": "2024-12-31",
            "backtest_initial_balance": 10000,
            "backtest_spread": 2,
            
            # Advanced features
            "auto_update_enabled": False,
            "update_check_interval": 86400,  # 24 hours
            "github_repo": "username/mt5-advanced-bot",
            
            # Multi-symbol settings
            "watchlist_enabled": False,
            "watchlist_symbols": ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"],
            "symbol_rotation": False,
            
            # GUI settings
            "gui_theme": "default",
            "save_window_position": True,
            "auto_save_interval": 300,  # 5 minutes
            
            # Trading hours
            "trading_hours": {
                "enabled": False,
                "start_time": "00:00",
                "end_time": "23:59",
                "timezone": "UTC"
            },
            
            # Error handling
            "max_consecutive_errors": 10,
            "error_recovery_delay": 30,
            "emergency_stop_threshold": 20,  # % loss
            
            # Position management
            "partial_close_enabled": False,
            "partial_close_percentage": 50,
            "break_even_enabled": True,
            "break_even_trigger_pips": 20,
            
            # Market analysis
            "volatility_filter": True,
            "correlation_analysis": False,
            "sentiment_analysis": False,
            
            # GUI values (will be populated by GUI)
            "gui_values": {}
        }
    
    def load_config(self) -> bool:
        """Load configuration from file"""
        try:
            if not os.path.exists(self.config_file):
                logger(f"ℹ️ Config file {self.config_file} not found, creating default")
                self.save_config()
                return True
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
            
            # Merge with defaults (in case new settings were added)
            self._merge_config(loaded_config)
            
            logger(f"✅ Configuration loaded from {self.config_file}")
            return True
            
        except json.JSONDecodeError as e:
            logger(f"❌ Invalid JSON in config file: {str(e)}")
            logger("ℹ️ Using default configuration")
            return False
        except Exception as e:
            logger(f"❌ Error loading config: {str(e)}")
            return False
    
    def save_config(self) -> bool:
        """Save configuration to file"""
        try:
            # Create backup of existing config
            if os.path.exists(self.config_file):
                backup_file = f"{self.config_file}.bak"
                import shutil
                shutil.copy2(self.config_file, backup_file)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, sort_keys=True)
            
            logger(f"✅ Configuration saved to {self.config_file}")
            return True
            
        except Exception as e:
            logger(f"❌ Error saving config: {str(e)}")
            return False
    
    def _merge_config(self, loaded_config: Dict[str, Any]) -> None:
        """Merge loaded config with defaults"""
        def merge_dict(default: Dict, loaded: Dict) -> Dict:
            """Recursively merge dictionaries"""
            result = default.copy()
            for key, value in loaded.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = merge_dict(result[key], value)
                else:
                    result[key] = value
            return result
        
        self.config = merge_dict(self.config, loaded_config)
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        return self.config.copy()
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get specific setting"""
        try:
            keys = key.split('.')
            value = self.config
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def update_config(self, key: str, value: Any) -> None:
        """Update configuration setting"""
        try:
            keys = key.split('.')
            config = self.config
            
            # Navigate to the parent dictionary
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            # Set the value
            config[keys[-1]] = value
            
            logger(f"✅ Config updated: {key} = {value}")
            
        except Exception as e:
            logger(f"❌ Error updating config: {str(e)}")
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to defaults"""
        logger("🔄 Resetting configuration to defaults...")
        self.config = self._get_default_config()
        self.save_config()
    
    def validate_config(self) -> bool:
        """Validate configuration values"""
        try:
            errors = []
            
            # Validate numeric ranges
            if not 0.01 <= self.config.get('lot_size', 0.01) <= 100:
                errors.append("lot_size must be between 0.01 and 100")
            
            if not 0.1 <= self.config.get('risk_percent', 1.0) <= 50:
                errors.append("risk_percent must be between 0.1 and 50")
            
            if not 0.1 <= self.config.get('max_daily_loss', 5.0) <= 100:
                errors.append("max_daily_loss must be between 0.1 and 100")
            
            if not 0.5 <= self.config.get('ai_confidence', 0.75) <= 1.0:
                errors.append("ai_confidence must be between 0.5 and 1.0")
            
            # Validate string choices
            valid_strategies = ['Scalping', 'HFT', 'Intraday', 'Arbitrage']
            if self.config.get('strategy') not in valid_strategies:
                errors.append(f"strategy must be one of: {valid_strategies}")
            
            valid_units = ['pips', 'price', 'percent', 'currency']
            if self.config.get('tp_unit') not in valid_units:
                errors.append(f"tp_unit must be one of: {valid_units}")
            if self.config.get('sl_unit') not in valid_units:
                errors.append(f"sl_unit must be one of: {valid_units}")
            
            # Validate Telegram settings if enabled
            if self.config.get('telegram_enabled', False):
                if not self.config.get('telegram_token'):
                    errors.append("telegram_token required when Telegram is enabled")
                if not self.config.get('telegram_chat_id'):
                    errors.append("telegram_chat_id required when Telegram is enabled")
            
            if errors:
                for error in errors:
                    logger(f"❌ Config validation error: {error}")
                return False
            
            logger("✅ Configuration validation passed")
            return True
            
        except Exception as e:
            logger(f"❌ Error validating config: {str(e)}")
            return False
    
    def export_config(self, filename: str) -> bool:
        """Export configuration to file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, sort_keys=True)
            
            logger(f"✅ Configuration exported to {filename}")
            return True
            
        except Exception as e:
            logger(f"❌ Error exporting config: {str(e)}")
            return False
    
    def import_config(self, filename: str) -> bool:
        """Import configuration from file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            # Validate imported config
            temp_config = self.config
            self.config = imported_config
            
            if self.validate_config():
                logger(f"✅ Configuration imported from {filename}")
                self.save_config()
                return True
            else:
                logger(f"❌ Invalid configuration in {filename}")
                self.config = temp_config
                return False
                
        except Exception as e:
            logger(f"❌ Error importing config: {str(e)}")
            return False
    
    def get_strategy_params(self, strategy: str) -> Dict[str, Any]:
        """Get parameters for specific strategy"""
        strategy_params = {
            'Scalping': {
                'min_profit_pips': self.config.get('scalping_min_profit', 5),
                'max_spread_multiplier': 1.5,
                'timeframe': 'M1',
                'indicators': ['RSI', 'EMA', 'MACD']
            },
            'HFT': {
                'max_spread': self.config.get('hft_max_spread', 2),
                'min_volume_spike': 1.5,
                'momentum_threshold': 0.001,
                'timeframe': 'M1',
                'indicators': ['Volume', 'Momentum']
            },
            'Intraday': {
                'pivot_levels': self.config.get('intraday_pivot_levels', True),
                'timeframe': 'H1',
                'session_filter': True,
                'indicators': ['Pivot', 'EMA', 'RSI', 'Support_Resistance']
            },
            'Arbitrage': {
                'threshold': self.config.get('arbitrage_threshold', 0.001),
                'mean_reversion_period': 20,
                'z_score_threshold': 2.0,
                'indicators': ['Mean_Reversion', 'Z_Score']
            }
        }
        
        return strategy_params.get(strategy, {})
    
    def get_session_config(self) -> Dict[str, bool]:
        """Get trading session configuration"""
        return {
            'Asia': self.config.get('session_asia', True),
            'London': self.config.get('session_london', True),
            'New_York': self.config.get('session_new_york', True),
            'Overlap_London_NY': self.config.get('session_overlap_london_ny', True)
        }
    
    def get_risk_config(self) -> Dict[str, Any]:
        """Get risk management configuration"""
        return {
            'max_daily_loss': self.config.get('max_daily_loss', 5.0),
            'daily_profit_target': self.config.get('daily_profit_target', 10.0),
            'max_positions': self.config.get('max_positions', 10),
            'max_loss_streak': self.config.get('max_loss_streak', 3),
            'max_drawdown': self.config.get('max_drawdown', 5.0),
            'auto_stop_drawdown': self.config.get('auto_stop_drawdown', True),
            'trailing_stop': self.config.get('trailing_stop', False),
            'trailing_distance': self.config.get('trailing_distance', 15)
        }
    
    def auto_save(self) -> None:
        """Auto-save configuration periodically"""
        import threading
        import time
        
        def save_worker():
            while True:
                time.sleep(self.config.get('auto_save_interval', 300))
                if hasattr(self, '_modified') and self._modified:
                    self.save_config()
                    self._modified = False
        
        if not hasattr(self, '_auto_save_thread'):
            self._auto_save_thread = threading.Thread(target=save_worker, daemon=True)
            self._auto_save_thread.start()
