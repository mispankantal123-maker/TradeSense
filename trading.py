"""
Advanced MT5 Trading Bot - Trading Engine
Enhanced trading logic with AI signals, multi-strategy support, and comprehensive risk management
"""

try:
    import MetaTrader5 as mt5
except ImportError:
    import mock_mt5 as mt5
import threading
import time
import datetime
from typing import Optional, Dict, Any, List, Tuple
import numpy as np
import pandas as pd

from utils import logger, validate_numeric_input, cleanup_resources
from config import ConfigManager
from ai_signals import AISignalGenerator
from risk_management import RiskManager
from indicators import TechnicalIndicators
from session_manager import SessionManager
from telegram_bot import TelegramBot

class TradingEngine:
    """Main trading engine with enhanced features"""
    
    def __init__(self, config_manager: ConfigManager, gui=None):
        """Initialize trading engine"""
        self.config_manager = config_manager
        self.gui = gui
        self.running = False
        self.connected = False
        
        # Initialize components
        self.ai_signals = AISignalGenerator()
        self.risk_manager = RiskManager(config_manager)
        self.indicators = TechnicalIndicators()
        self.session_manager = SessionManager()
        self.telegram_bot = TelegramBot(config_manager)
        
        # Trading state
        self.trade_lock = threading.Lock()
        self.last_trade_time = {}
        self.position_count = 0
        self.session_data = {
            'start_balance': 0.0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_profit': 0.0,
            'daily_profit': 0.0,
            'max_equity': 0.0,
            'trades_log': []
        }
        
        # Connection parameters
        self.max_connection_attempts = 5
        self.connection_retry_delay = 3
        
    def connect(self) -> bool:
        """Connect to MT5 with enhanced error handling"""
        try:
            logger("🔄 Connecting to MT5...")
            
            # Shutdown existing connection
            try:
                mt5.shutdown()
                time.sleep(1)
            except:
                pass
            
            # Try multiple initialization methods
            init_methods = [
                lambda: mt5.initialize(),
                lambda: mt5.initialize(path="C:\\Program Files\\MetaTrader 5\\terminal64.exe"),
                lambda: mt5.initialize(path="C:\\Program Files (x86)\\MetaTrader 5\\terminal.exe"),
            ]
            
            for attempt in range(self.max_connection_attempts):
                logger(f"🔄 Connection attempt {attempt + 1}/{self.max_connection_attempts}")
                
                for i, init_method in enumerate(init_methods):
                    try:
                        if init_method():
                            logger(f"✅ MT5 connected using method {i + 1}")
                            self.connected = True
                            
                            # Get account info
                            account_info = mt5.account_info()
                            if account_info:
                                logger(f"✅ Account: {account_info.login}")
                                logger(f"💰 Balance: {account_info.balance}")
                                self.session_data['start_balance'] = account_info.balance
                                
                                # Initialize telegram if enabled
                                if self.config_manager.get_config().get('telegram_enabled', False):
                                    self.telegram_bot.send_message("🤖 MT5 Trading Bot Connected")
                                
                                return True
                            else:
                                logger("❌ Failed to get account info")
                    except Exception as e:
                        logger(f"⚠️ Init method {i + 1} failed: {str(e)}")
                        continue
                
                if attempt < self.max_connection_attempts - 1:
                    time.sleep(self.connection_retry_delay)
            
            logger("❌ All connection attempts failed")
            self.connected = False
            return False
            
        except Exception as e:
            logger(f"❌ Connection error: {str(e)}")
            self.connected = False
            return False
    
    def disconnect(self) -> None:
        """Disconnect from MT5"""
        try:
            logger("🔌 Disconnecting from MT5...")
            self.connected = False
            mt5.shutdown()
            logger("✅ MT5 disconnected")
        except Exception as e:
            logger(f"⚠️ Disconnect error: {str(e)}")
    
    def is_connected(self) -> bool:
        """Check if connected to MT5"""
        try:
            if not self.connected:
                return False
            
            # Test connection with account info
            account_info = mt5.account_info()
            return account_info is not None
        except:
            self.connected = False
            return False
    
    def start(self) -> None:
        """Start the trading bot"""
        if self.running:
            logger("⚠️ Bot is already running")
            return
        
        if not self.is_connected():
            logger("❌ Cannot start bot: Not connected to MT5")
            return
        
        self.running = True
        logger("🚀 Starting trading bot...")
        
        # Start trading thread
        threading.Thread(target=self._trading_loop, daemon=True).start()
        
        # Send telegram notification
        if self.config_manager.get_config().get('telegram_enabled', False):
            self.telegram_bot.send_message("🚀 Trading Bot Started")
    
    def stop(self) -> None:
        """Stop the trading bot"""
        if not self.running:
            logger("⚠️ Bot is already stopped")
            return
        
        logger("🛑 Stopping trading bot...")
        self.running = False
        
        # Send telegram notification
        if self.config_manager.get_config().get('telegram_enabled', False):
            profit = self.session_data['total_profit']
            trades = self.session_data['total_trades']
            self.telegram_bot.send_message(f"🛑 Trading Bot Stopped\n💰 Session P/L: {profit:.2f}\n📊 Total Trades: {trades}")
    
    def is_running(self) -> bool:
        """Check if bot is running"""
        return self.running
    
    def _trading_loop(self) -> None:
        """Main trading loop"""
        logger("🔄 Trading loop started")
        
        config = self.config_manager.get_config()
        strategy = config.get('strategy', 'Scalping')
        loop_interval = {
            'HFT': 0.5,
            'Scalping': 1.0, 
            'Intraday': 2.0,
            'Arbitrage': 2.0
        }.get(strategy, 1.0)
        
        while self.running:
            try:
                if not self.is_connected():
                    logger("❌ Connection lost, attempting reconnect...")
                    if not self.connect():
                        time.sleep(10)
                        continue
                
                # Check trading conditions
                if not self._should_trade():
                    time.sleep(loop_interval)
                    continue
                
                # Get trading signals
                signals = self._get_trading_signals()
                
                # Process signals
                for signal in signals:
                    if not self.running:
                        break
                    
                    self._process_signal(signal)
                
                # Manage existing positions
                self._manage_positions()
                
                # Cleanup resources
                cleanup_resources()
                
                time.sleep(loop_interval)
                
            except Exception as e:
                logger(f"❌ Error in trading loop: {str(e)}")
                time.sleep(5)
        
        logger("✅ Trading loop stopped")
    
    def _should_trade(self) -> bool:
        """Check if trading conditions are met"""
        try:
            # Check session
            if not self.session_manager.is_trading_session_active():
                return False
            
            # Check risk limits
            if not self.risk_manager.can_trade():
                return False
            
            # Check news filter
            config = self.config_manager.get_config()
            if config.get('avoid_news', True):
                from utils import is_high_impact_news_time
                if is_high_impact_news_time():
                    return False
            
            # Check position limits
            positions = mt5.positions_total()
            max_positions = config.get('max_positions', 10)
            if positions >= max_positions:
                return False
            
            return True
            
        except Exception as e:
            logger(f"❌ Error checking trading conditions: {str(e)}")
            return False
    
    def _get_trading_signals(self) -> List[Dict[str, Any]]:
        """Get trading signals from all sources"""
        signals = []
        
        try:
            config = self.config_manager.get_config()
            symbol = config.get('symbol', 'XAUUSD')
            
            # Get market data
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 200)
            if rates is None or len(rates) < 200:
                return signals
            
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            # Technical analysis signals
            tech_signals = self._get_technical_signals(df, symbol)
            signals.extend(tech_signals)
            
            # AI signals
            if config.get('ai_enabled', True):
                ai_signal = self.ai_signals.generate_signal(df)
                if ai_signal:
                    signals.append(ai_signal)
            
            return signals
            
        except Exception as e:
            logger(f"❌ Error getting trading signals: {str(e)}")
            return []
    
    def _get_technical_signals(self, df: pd.DataFrame, symbol: str) -> List[Dict[str, Any]]:
        """Get signals from technical indicators"""
        signals = []
        
        try:
            config = self.config_manager.get_config()
            
            # Calculate indicators
            indicators = {}
            
            if config.get('indicator_rsi', True):
                indicators['rsi'] = self.indicators.calculate_rsi(df['close'])
            
            if config.get('indicator_macd', True):
                macd_data = self.indicators.calculate_macd(df['close'])
                indicators.update(macd_data)
            
            if config.get('indicator_ema', True):
                indicators['ema_20'] = self.indicators.calculate_ema(df['close'], 20)
                indicators['ema_50'] = self.indicators.calculate_ema(df['close'], 50)
            
            if config.get('indicator_atr', True):
                indicators['atr'] = self.indicators.calculate_atr(df['high'], df['low'], df['close'])
            
            # Generate signals based on strategy
            strategy = config.get('strategy', 'Scalping')
            
            if strategy == 'Scalping':
                signal = self._scalping_strategy(df, indicators, symbol)
            elif strategy == 'HFT':
                signal = self._hft_strategy(df, indicators, symbol)
            elif strategy == 'Intraday':
                signal = self._intraday_strategy(df, indicators, symbol)
            elif strategy == 'Arbitrage':
                signal = self._arbitrage_strategy(df, indicators, symbol)
            else:
                signal = None
            
            if signal:
                signals.append(signal)
            
            return signals
            
        except Exception as e:
            logger(f"❌ Error in technical analysis: {str(e)}")
            return []
    
    def _scalping_strategy(self, df: pd.DataFrame, indicators: Dict, symbol: str) -> Optional[Dict[str, Any]]:
        """Scalping strategy implementation"""
        try:
            if len(df) < 50:
                return None
            
            current_price = df['close'].iloc[-1]
            rsi = indicators.get('rsi')
            ema_20 = indicators.get('ema_20')
            ema_50 = indicators.get('ema_50')
            
            if rsi is None or ema_20 is None or ema_50 is None:
                return None
            
            # Scalping conditions
            current_rsi = rsi.iloc[-1]
            current_ema_20 = ema_20.iloc[-1]
            current_ema_50 = ema_50.iloc[-1]
            
            # Buy signal: RSI oversold + EMA crossover up
            if (current_rsi < 30 and 
                current_ema_20 > current_ema_50 and 
                ema_20.iloc[-2] <= ema_50.iloc[-2]):
                
                return {
                    'action': 'buy',
                    'symbol': symbol,
                    'strategy': 'Scalping',
                    'confidence': 0.8,
                    'price': current_price,
                    'reason': 'RSI oversold + EMA bullish crossover'
                }
            
            # Sell signal: RSI overbought + EMA crossover down
            elif (current_rsi > 70 and 
                  current_ema_20 < current_ema_50 and 
                  ema_20.iloc[-2] >= ema_50.iloc[-2]):
                
                return {
                    'action': 'sell',
                    'symbol': symbol,
                    'strategy': 'Scalping',
                    'confidence': 0.8,
                    'price': current_price,
                    'reason': 'RSI overbought + EMA bearish crossover'
                }
            
            return None
            
        except Exception as e:
            logger(f"❌ Scalping strategy error: {str(e)}")
            return None
    
    def _hft_strategy(self, df: pd.DataFrame, indicators: Dict, symbol: str) -> Optional[Dict[str, Any]]:
        """High Frequency Trading strategy"""
        try:
            if len(df) < 20:
                return None
            
            # Check spread conditions
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                return None
            
            spread = symbol_info.spread * symbol_info.point
            max_spread = self.config_manager.get_config().get('hft_max_spread', 2) * symbol_info.point
            
            if spread > max_spread:
                return None
            
            # Quick momentum strategy
            prices = df['close'].tail(10)
            momentum = (prices.iloc[-1] - prices.iloc[-5]) / prices.iloc[-5]
            
            # Volume spike detection
            volumes = df['tick_volume'].tail(5)
            avg_volume = volumes.mean()
            current_volume = volumes.iloc[-1]
            
            if current_volume > avg_volume * 1.5:  # Volume spike
                if momentum > 0.001:  # 0.1% momentum up
                    return {
                        'action': 'buy',
                        'symbol': symbol,
                        'strategy': 'HFT',
                        'confidence': 0.7,
                        'price': df['close'].iloc[-1],
                        'reason': 'Volume spike + positive momentum'
                    }
                elif momentum < -0.001:  # 0.1% momentum down
                    return {
                        'action': 'sell',
                        'symbol': symbol,
                        'strategy': 'HFT',
                        'confidence': 0.7,
                        'price': df['close'].iloc[-1],
                        'reason': 'Volume spike + negative momentum'
                    }
            
            return None
            
        except Exception as e:
            logger(f"❌ HFT strategy error: {str(e)}")
            return None
    
    def _intraday_strategy(self, df: pd.DataFrame, indicators: Dict, symbol: str) -> Optional[Dict[str, Any]]:
        """Intraday trading strategy"""
        try:
            # Use longer timeframe data for intraday
            rates_h1 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 50)
            if rates_h1 is None or len(rates_h1) < 50:
                return None
            
            df_h1 = pd.DataFrame(rates_h1)
            
            # Calculate daily pivot points
            yesterday_high = df_h1['high'].iloc[-24:-1].max() if len(df_h1) > 24 else df_h1['high'].max()
            yesterday_low = df_h1['low'].iloc[-24:-1].min() if len(df_h1) > 24 else df_h1['low'].min()
            yesterday_close = df_h1['close'].iloc[-24] if len(df_h1) > 24 else df_h1['close'].iloc[0]
            
            pivot = (yesterday_high + yesterday_low + yesterday_close) / 3
            r1 = 2 * pivot - yesterday_low
            s1 = 2 * pivot - yesterday_high
            
            current_price = df['close'].iloc[-1]
            
            # Trend detection
            ema_20 = indicators.get('ema_20')
            if ema_20 is None:
                return None
            
            trend = 'up' if current_price > ema_20.iloc[-1] else 'down'
            
            # Support/Resistance strategy
            if trend == 'up' and abs(current_price - s1) / current_price < 0.001:  # Near support
                return {
                    'action': 'buy',
                    'symbol': symbol,
                    'strategy': 'Intraday',
                    'confidence': 0.75,
                    'price': current_price,
                    'reason': f'Uptrend + near support level (S1: {s1:.5f})'
                }
            
            elif trend == 'down' and abs(current_price - r1) / current_price < 0.001:  # Near resistance
                return {
                    'action': 'sell',
                    'symbol': symbol,
                    'strategy': 'Intraday',
                    'confidence': 0.75,
                    'price': current_price,
                    'reason': f'Downtrend + near resistance level (R1: {r1:.5f})'
                }
            
            return None
            
        except Exception as e:
            logger(f"❌ Intraday strategy error: {str(e)}")
            return None
    
    def _arbitrage_strategy(self, df: pd.DataFrame, indicators: Dict, symbol: str) -> Optional[Dict[str, Any]]:
        """Arbitrage strategy (basic implementation)"""
        try:
            # This is a simplified arbitrage strategy
            # In real arbitrage, you'd compare prices across different brokers/exchanges
            
            # Mean reversion strategy as placeholder
            prices = df['close'].tail(20)
            mean_price = prices.mean()
            std_price = prices.std()
            current_price = prices.iloc[-1]
            
            # Calculate z-score
            z_score = (current_price - mean_price) / std_price if std_price > 0 else 0
            
            # Arbitrage opportunity detection
            if z_score > 2:  # Price too high, expect reversion
                return {
                    'action': 'sell',
                    'symbol': symbol,
                    'strategy': 'Arbitrage',
                    'confidence': 0.6,
                    'price': current_price,
                    'reason': f'Mean reversion opportunity (z-score: {z_score:.2f})'
                }
            
            elif z_score < -2:  # Price too low, expect reversion
                return {
                    'action': 'buy',
                    'symbol': symbol,
                    'strategy': 'Arbitrage',
                    'confidence': 0.6,
                    'price': current_price,
                    'reason': f'Mean reversion opportunity (z-score: {z_score:.2f})'
                }
            
            return None
            
        except Exception as e:
            logger(f"❌ Arbitrage strategy error: {str(e)}")
            return None
    
    def _process_signal(self, signal: Dict[str, Any]) -> None:
        """Process trading signal"""
        try:
            if not signal or not self.running:
                return
            
            # Check signal confidence
            min_confidence = self.config_manager.get_config().get('ai_confidence', 0.75)
            if signal.get('confidence', 0) < min_confidence:
                return
            
            # Check time since last trade on this symbol
            symbol = signal['symbol']
            now = time.time()
            if symbol in self.last_trade_time:
                time_diff = now - self.last_trade_time[symbol]
                min_time_between_trades = 60  # 1 minute minimum
                if time_diff < min_time_between_trades:
                    return
            
            # Execute trade
            with self.trade_lock:
                result = self._execute_trade(signal)
                if result:
                    self.last_trade_time[symbol] = now
                    
                    # Send telegram notification
                    if self.config_manager.get_config().get('telegram_enabled', False):
                        message = f"🎯 Trade Executed\n"
                        message += f"Symbol: {signal['symbol']}\n"
                        message += f"Action: {signal['action'].upper()}\n"
                        message += f"Strategy: {signal['strategy']}\n"
                        message += f"Confidence: {signal['confidence']:.2f}\n"
                        message += f"Reason: {signal['reason']}"
                        self.telegram_bot.send_message(message)
            
        except Exception as e:
            logger(f"❌ Error processing signal: {str(e)}")
    
    def _execute_trade(self, signal: Dict[str, Any]) -> bool:
        """Execute a trade based on signal"""
        try:
            symbol = signal['symbol']
            action = signal['action']
            
            # Get symbol info
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                logger(f"❌ Symbol {symbol} not found")
                return False
            
            # Calculate lot size
            config = self.config_manager.get_config()
            if config.get('auto_lot', True):
                lot_size = self.risk_manager.calculate_lot_size(symbol, signal)
            else:
                lot_size = config.get('lot_size', 0.01)
            
            if lot_size <= 0:
                logger("❌ Invalid lot size calculated")
                return False
            
            # Get current price
            if action == 'buy':
                price = mt5.symbol_info_tick(symbol).ask
                order_type = mt5.ORDER_TYPE_BUY
            else:
                price = mt5.symbol_info_tick(symbol).bid
                order_type = mt5.ORDER_TYPE_SELL
            
            # Calculate TP/SL
            tp_price, sl_price = self._calculate_tp_sl(symbol, action, price)
            
            # Create order request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot_size,
                "type": order_type,
                "price": price,
                "sl": sl_price,
                "tp": tp_price,
                "deviation": 20,
                "magic": 234000,
                "comment": f"Bot_{signal['strategy']}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Send order
            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger(f"❌ Order failed: {result.retcode} - {result.comment}")
                return False
            
            # Log successful trade
            logger(f"✅ {action.upper()} order executed: {symbol} {lot_size} lots at {price}")
            
            # Update session data
            self.session_data['total_trades'] += 1
            
            # Log trade details
            trade_log = {
                'time': datetime.datetime.now(),
                'symbol': symbol,
                'action': action,
                'volume': lot_size,
                'price': price,
                'tp': tp_price,
                'sl': sl_price,
                'strategy': signal['strategy'],
                'confidence': signal['confidence'],
                'ticket': result.order
            }
            self.session_data['trades_log'].append(trade_log)
            
            return True
            
        except Exception as e:
            logger(f"❌ Trade execution error: {str(e)}")
            return False
    
    def _calculate_tp_sl(self, symbol: str, action: str, price: float) -> Tuple[float, float]:
        """Calculate take profit and stop loss levels"""
        try:
            config = self.config_manager.get_config()
            symbol_info = mt5.symbol_info(symbol)
            
            tp_value = config.get('tp_value', 50)
            tp_unit = config.get('tp_unit', 'pips')
            sl_value = config.get('sl_value', 25)
            sl_unit = config.get('sl_unit', 'pips')
            
            # Calculate TP
            if tp_unit == 'pips':
                pip_value = symbol_info.point * 10 if 'JPY' in symbol else symbol_info.point * 10
                if action == 'buy':
                    tp_price = price + (tp_value * pip_value)
                else:
                    tp_price = price - (tp_value * pip_value)
            elif tp_unit == 'price':
                tp_price = tp_value
            elif tp_unit == 'percent':
                if action == 'buy':
                    tp_price = price * (1 + tp_value / 100)
                else:
                    tp_price = price * (1 - tp_value / 100)
            else:
                tp_price = 0  # No TP
            
            # Calculate SL
            if sl_unit == 'pips':
                pip_value = symbol_info.point * 10 if 'JPY' in symbol else symbol_info.point * 10
                if action == 'buy':
                    sl_price = price - (sl_value * pip_value)
                else:
                    sl_price = price + (sl_value * pip_value)
            elif sl_unit == 'price':
                sl_price = sl_value
            elif sl_unit == 'percent':
                if action == 'buy':
                    sl_price = price * (1 - sl_value / 100)
                else:
                    sl_price = price * (1 + sl_value / 100)
            else:
                sl_price = 0  # No SL
            
            # Round to symbol digits
            digits = symbol_info.digits
            tp_price = round(tp_price, digits) if tp_price > 0 else 0
            sl_price = round(sl_price, digits) if sl_price > 0 else 0
            
            return tp_price, sl_price
            
        except Exception as e:
            logger(f"❌ Error calculating TP/SL: {str(e)}")
            return 0, 0
    
    def _manage_positions(self) -> None:
        """Manage existing positions (trailing stop, etc.)"""
        try:
            positions = mt5.positions_get()
            if not positions:
                return
            
            config = self.config_manager.get_config()
            if not config.get('trailing_stop', False):
                return
            
            trailing_distance = config.get('trailing_distance', 15)
            
            for position in positions:
                if position.magic != 234000:  # Only our positions
                    continue
                
                self._update_trailing_stop(position, trailing_distance)
                
        except Exception as e:
            logger(f"❌ Error managing positions: {str(e)}")
    
    def _update_trailing_stop(self, position, trailing_distance: float) -> None:
        """Update trailing stop for a position"""
        try:
            symbol = position.symbol
            symbol_info = mt5.symbol_info(symbol)
            pip_value = symbol_info.point * 10 if 'JPY' in symbol else symbol_info.point * 10
            
            current_price = mt5.symbol_info_tick(symbol).bid if position.type == mt5.POSITION_TYPE_BUY else mt5.symbol_info_tick(symbol).ask
            
            if position.type == mt5.POSITION_TYPE_BUY:
                new_sl = current_price - (trailing_distance * pip_value)
                if position.sl == 0 or new_sl > position.sl:
                    self._modify_position(position.ticket, new_sl, position.tp)
            else:
                new_sl = current_price + (trailing_distance * pip_value)
                if position.sl == 0 or new_sl < position.sl:
                    self._modify_position(position.ticket, new_sl, position.tp)
                    
        except Exception as e:
            logger(f"❌ Error updating trailing stop: {str(e)}")
    
    def _modify_position(self, ticket: int, sl: float, tp: float) -> bool:
        """Modify position SL/TP"""
        try:
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "position": ticket,
                "sl": round(sl, mt5.symbol_info(mt5.positions_get(ticket=ticket)[0].symbol).digits),
                "tp": round(tp, mt5.symbol_info(mt5.positions_get(ticket=ticket)[0].symbol).digits) if tp > 0 else 0,
            }
            
            result = mt5.order_send(request)
            return result.retcode == mt5.TRADE_RETCODE_DONE
            
        except Exception as e:
            logger(f"❌ Error modifying position: {str(e)}")
            return False
    
    def manual_trade(self, action: str, params: Dict[str, Any]) -> None:
        """Execute manual trade"""
        try:
            signal = {
                'action': action,
                'symbol': params.get('symbol', 'XAUUSD'),
                'strategy': 'Manual',
                'confidence': 1.0,
                'price': 0,  # Will be filled with current price
                'reason': 'Manual trade'
            }
            
            self._execute_trade(signal)
            
        except Exception as e:
            logger(f"❌ Manual trade error: {str(e)}")
    
    def close_all_positions(self) -> None:
        """Close all open positions"""
        try:
            positions = mt5.positions_get()
            if not positions:
                logger("ℹ️ No positions to close")
                return
            
            closed = 0
            for position in positions:
                if position.magic == 234000:  # Only our positions
                    if self._close_position(position):
                        closed += 1
            
            logger(f"✅ Closed {closed} positions")
            
        except Exception as e:
            logger(f"❌ Error closing positions: {str(e)}")
    
    def _close_position(self, position) -> bool:
        """Close a specific position"""
        try:
            symbol = position.symbol
            volume = position.volume
            
            if position.type == mt5.POSITION_TYPE_BUY:
                order_type = mt5.ORDER_TYPE_SELL
                price = mt5.symbol_info_tick(symbol).bid
            else:
                order_type = mt5.ORDER_TYPE_BUY
                price = mt5.symbol_info_tick(symbol).ask
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": order_type,
                "position": position.ticket,
                "price": price,
                "deviation": 20,
                "magic": 234000,
                "comment": "Close by bot",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            return result.retcode == mt5.TRADE_RETCODE_DONE
            
        except Exception as e:
            logger(f"❌ Error closing position: {str(e)}")
            return False
    
    def auto_detect_gold_symbol(self) -> Optional[str]:
        """Auto-detect gold trading symbol"""
        try:
            # Common gold symbols
            gold_symbols = ['XAUUSD', 'GOLD', 'GOLDUSD', 'XAU/USD', 'Gold']
            
            for symbol in gold_symbols:
                symbol_info = mt5.symbol_info(symbol)
                if symbol_info:
                    # Try to add to market watch
                    if not symbol_info.visible:
                        mt5.symbol_select(symbol, True)
                    
                    logger(f"✅ Found gold symbol: {symbol}")
                    return symbol
            
            logger("❌ No gold symbol found")
            return None
            
        except Exception as e:
            logger(f"❌ Error detecting gold symbol: {str(e)}")
            return None
    
    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """Get current account information"""
        try:
            if not self.is_connected():
                return None
            
            account_info = mt5.account_info()
            if account_info:
                return account_info._asdict()
            return None
            
        except Exception as e:
            logger(f"❌ Error getting account info: {str(e)}")
            return None
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        try:
            total_trades = self.session_data['total_trades']
            winning_trades = self.session_data['winning_trades']
            losing_trades = self.session_data['losing_trades']
            
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            # Calculate profit factor (simplified)
            account_info = self.get_account_info()
            if account_info and self.session_data['start_balance'] > 0:
                current_balance = account_info['balance']
                total_profit = current_balance - self.session_data['start_balance']
                profit_factor = abs(total_profit) / self.session_data['start_balance'] if self.session_data['start_balance'] > 0 else 0
            else:
                profit_factor = 0
            
            return {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'profit_factor': profit_factor,
                'max_drawdown': 0,  # Simplified for now
                'total_profit': self.session_data['total_profit']
            }
            
        except Exception as e:
            logger(f"❌ Error calculating metrics: {str(e)}")
            return {}
    
    def export_trading_data(self) -> None:
        """Export trading data to CSV"""
        try:
            if not self.session_data['trades_log']:
                logger("ℹ️ No trading data to export")
                return
            
            import csv
            import os
            
            # Ensure logs directory exists
            os.makedirs('logs', exist_ok=True)
            
            filename = f"logs/trades_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            with open(filename, 'w', newline='') as csvfile:
                fieldnames = ['time', 'symbol', 'action', 'volume', 'price', 'tp', 'sl', 'strategy', 'confidence', 'ticket']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for trade in self.session_data['trades_log']:
                    writer.writerow(trade)
            
            logger(f"✅ Trading data exported to {filename}")
            
        except Exception as e:
            logger(f"❌ Error exporting data: {str(e)}")
    
    def run_backtest(self, start_date: str, end_date: str) -> None:
        """Run backtest (simplified implementation)"""
        try:
            logger(f"🔍 Running backtest from {start_date} to {end_date}")
            
            # This is a simplified backtest implementation
            # In a full implementation, you would:
            # 1. Get historical data for the date range
            # 2. Run your strategy on historical data
            # 3. Calculate performance metrics
            # 4. Display results
            
            logger("ℹ️ Backtest feature is in development")
            logger("📊 Use the current live trading metrics for performance evaluation")
            
        except Exception as e:
            logger(f"❌ Backtest error: {str(e)}")
