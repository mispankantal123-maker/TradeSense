"""
Advanced MT5 Trading Bot - Technical Indicators
Comprehensive technical analysis indicators
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple, List
from utils import logger

class TechnicalIndicators:
    """Technical analysis indicators calculator"""
    
    def __init__(self):
        """Initialize technical indicators calculator"""
        self.cache = {}  # Cache for computed indicators
        
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        try:
            if len(prices) < period + 1:
                return pd.Series(index=prices.index, dtype=float)
            
            # Calculate price changes
            delta = prices.diff()
            
            # Separate gains and losses
            gains = delta.where(delta > 0, 0)
            losses = -delta.where(delta < 0, 0)
            
            # Calculate average gains and losses
            avg_gains = gains.rolling(window=period).mean()
            avg_losses = losses.rolling(window=period).mean()
            
            # Calculate RS and RSI
            rs = avg_gains / avg_losses
            rsi = 100 - (100 / (1 + rs))
            
            return rsi
            
        except Exception as e:
            logger(f"❌ Error calculating RSI: {str(e)}")
            return pd.Series(index=prices.index, dtype=float)
    
    def calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        try:
            if len(prices) < slow + signal:
                empty_series = pd.Series(index=prices.index, dtype=float)
                return {
                    'macd': empty_series,
                    'macd_signal': empty_series,
                    'macd_histogram': empty_series
                }
            
            # Calculate EMAs
            ema_fast = prices.ewm(span=fast).mean()
            ema_slow = prices.ewm(span=slow).mean()
            
            # Calculate MACD line
            macd_line = ema_fast - ema_slow
            
            # Calculate signal line
            signal_line = macd_line.ewm(span=signal).mean()
            
            # Calculate histogram
            histogram = macd_line - signal_line
            
            return {
                'macd': macd_line,
                'macd_signal': signal_line,
                'macd_histogram': histogram
            }
            
        except Exception as e:
            logger(f"❌ Error calculating MACD: {str(e)}")
            empty_series = pd.Series(index=prices.index, dtype=float)
            return {
                'macd': empty_series,
                'macd_signal': empty_series,
                'macd_histogram': empty_series
            }
    
    def calculate_ema(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        try:
            if len(prices) < period:
                return pd.Series(index=prices.index, dtype=float)
            
            return prices.ewm(span=period).mean()
            
        except Exception as e:
            logger(f"❌ Error calculating EMA: {str(e)}")
            return pd.Series(index=prices.index, dtype=float)
    
    def calculate_sma(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Simple Moving Average"""
        try:
            if len(prices) < period:
                return pd.Series(index=prices.index, dtype=float)
            
            return prices.rolling(window=period).mean()
            
        except Exception as e:
            logger(f"❌ Error calculating SMA: {str(e)}")
            return pd.Series(index=prices.index, dtype=float)
    
    def calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        try:
            if len(high) < period + 1:
                return pd.Series(index=high.index, dtype=float)
            
            # Calculate True Range
            prev_close = close.shift(1)
            tr1 = high - low
            tr2 = abs(high - prev_close)
            tr3 = abs(low - prev_close)
            
            true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            
            # Calculate ATR
            atr = true_range.rolling(window=period).mean()
            
            return atr
            
        except Exception as e:
            logger(f"❌ Error calculating ATR: {str(e)}")
            return pd.Series(index=high.index, dtype=float)
    
    def calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: float = 2) -> Dict[str, pd.Series]:
        """Calculate Bollinger Bands"""
        try:
            if len(prices) < period:
                empty_series = pd.Series(index=prices.index, dtype=float)
                return {
                    'bb_upper': empty_series,
                    'bb_middle': empty_series,
                    'bb_lower': empty_series,
                    'bb_width': empty_series,
                    'bb_percent': empty_series
                }
            
            # Calculate middle band (SMA)
            middle_band = prices.rolling(window=period).mean()
            
            # Calculate standard deviation
            std = prices.rolling(window=period).std()
            
            # Calculate upper and lower bands
            upper_band = middle_band + (std * std_dev)
            lower_band = middle_band - (std * std_dev)
            
            # Calculate band width and %B
            band_width = (upper_band - lower_band) / middle_band
            percent_b = (prices - lower_band) / (upper_band - lower_band)
            
            return {
                'bb_upper': upper_band,
                'bb_middle': middle_band,
                'bb_lower': lower_band,
                'bb_width': band_width,
                'bb_percent': percent_b
            }
            
        except Exception as e:
            logger(f"❌ Error calculating Bollinger Bands: {str(e)}")
            empty_series = pd.Series(index=prices.index, dtype=float)
            return {
                'bb_upper': empty_series,
                'bb_middle': empty_series,
                'bb_lower': empty_series,
                'bb_width': empty_series,
                'bb_percent': empty_series
            }
    
    def calculate_stochastic(self, high: pd.Series, low: pd.Series, close: pd.Series, 
                           k_period: int = 14, d_period: int = 3) -> Dict[str, pd.Series]:
        """Calculate Stochastic Oscillator"""
        try:
            if len(high) < k_period + d_period:
                empty_series = pd.Series(index=high.index, dtype=float)
                return {
                    'stoch_k': empty_series,
                    'stoch_d': empty_series
                }
            
            # Calculate %K
            lowest_low = low.rolling(window=k_period).min()
            highest_high = high.rolling(window=k_period).max()
            
            k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
            
            # Calculate %D (moving average of %K)
            d_percent = k_percent.rolling(window=d_period).mean()
            
            return {
                'stoch_k': k_percent,
                'stoch_d': d_percent
            }
            
        except Exception as e:
            logger(f"❌ Error calculating Stochastic: {str(e)}")
            empty_series = pd.Series(index=high.index, dtype=float)
            return {
                'stoch_k': empty_series,
                'stoch_d': empty_series
            }
    
    def calculate_williams_r(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Williams %R"""
        try:
            if len(high) < period:
                return pd.Series(index=high.index, dtype=float)
            
            highest_high = high.rolling(window=period).max()
            lowest_low = low.rolling(window=period).min()
            
            williams_r = -100 * ((highest_high - close) / (highest_high - lowest_low))
            
            return williams_r
            
        except Exception as e:
            logger(f"❌ Error calculating Williams %R: {str(e)}")
            return pd.Series(index=high.index, dtype=float)
    
    def calculate_cci(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20) -> pd.Series:
        """Calculate Commodity Channel Index"""
        try:
            if len(high) < period:
                return pd.Series(index=high.index, dtype=float)
            
            # Calculate typical price
            typical_price = (high + low + close) / 3
            
            # Calculate moving average of typical price
            sma_tp = typical_price.rolling(window=period).mean()
            
            # Calculate mean deviation
            mad = typical_price.rolling(window=period).apply(lambda x: np.mean(np.abs(x - x.mean())))
            
            # Calculate CCI
            cci = (typical_price - sma_tp) / (0.015 * mad)
            
            return cci
            
        except Exception as e:
            logger(f"❌ Error calculating CCI: {str(e)}")
            return pd.Series(index=high.index, dtype=float)
    
    def calculate_momentum(self, prices: pd.Series, period: int = 10) -> pd.Series:
        """Calculate Momentum indicator"""
        try:
            if len(prices) < period + 1:
                return pd.Series(index=prices.index, dtype=float)
            
            momentum = prices / prices.shift(period) - 1
            return momentum * 100  # Convert to percentage
            
        except Exception as e:
            logger(f"❌ Error calculating Momentum: {str(e)}")
            return pd.Series(index=prices.index, dtype=float)
    
    def calculate_roc(self, prices: pd.Series, period: int = 10) -> pd.Series:
        """Calculate Rate of Change"""
        try:
            if len(prices) < period + 1:
                return pd.Series(index=prices.index, dtype=float)
            
            roc = ((prices - prices.shift(period)) / prices.shift(period)) * 100
            return roc
            
        except Exception as e:
            logger(f"❌ Error calculating ROC: {str(e)}")
            return pd.Series(index=prices.index, dtype=float)
    
    def calculate_adx(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> Dict[str, pd.Series]:
        """Calculate Average Directional Index"""
        try:
            if len(high) < period * 2:
                empty_series = pd.Series(index=high.index, dtype=float)
                return {
                    'adx': empty_series,
                    'di_plus': empty_series,
                    'di_minus': empty_series
                }
            
            # Calculate True Range
            tr = self.calculate_atr(high, low, close, 1)
            
            # Calculate Directional Movement
            up_move = high - high.shift(1)
            down_move = low.shift(1) - low
            
            plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
            minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
            
            plus_dm = pd.Series(plus_dm, index=high.index)
            minus_dm = pd.Series(minus_dm, index=high.index)
            
            # Calculate smoothed values
            atr = tr.rolling(window=period).mean()
            plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
            minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
            
            # Calculate ADX
            dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
            adx = dx.rolling(window=period).mean()
            
            return {
                'adx': adx,
                'di_plus': plus_di,
                'di_minus': minus_di
            }
            
        except Exception as e:
            logger(f"❌ Error calculating ADX: {str(e)}")
            empty_series = pd.Series(index=high.index, dtype=float)
            return {
                'adx': empty_series,
                'di_plus': empty_series,
                'di_minus': empty_series
            }
    
    def calculate_pivot_points(self, high: pd.Series, low: pd.Series, close: pd.Series) -> Dict[str, float]:
        """Calculate daily pivot points"""
        try:
            if len(high) < 1:
                return {}
            
            # Use previous day's high, low, close
            prev_high = high.iloc[-1]
            prev_low = low.iloc[-1]
            prev_close = close.iloc[-1]
            
            # Calculate pivot point
            pivot = (prev_high + prev_low + prev_close) / 3
            
            # Calculate support and resistance levels
            r1 = 2 * pivot - prev_low
            s1 = 2 * pivot - prev_high
            r2 = pivot + (prev_high - prev_low)
            s2 = pivot - (prev_high - prev_low)
            r3 = prev_high + 2 * (pivot - prev_low)
            s3 = prev_low - 2 * (prev_high - pivot)
            
            return {
                'pivot': pivot,
                'r1': r1,
                'r2': r2,
                'r3': r3,
                's1': s1,
                's2': s2,
                's3': s3
            }
            
        except Exception as e:
            logger(f"❌ Error calculating pivot points: {str(e)}")
            return {}
    
    def calculate_fibonacci_levels(self, high_price: float, low_price: float) -> Dict[str, float]:
        """Calculate Fibonacci retracement levels"""
        try:
            price_range = high_price - low_price
            
            levels = {
                'fib_0': high_price,
                'fib_236': high_price - (price_range * 0.236),
                'fib_382': high_price - (price_range * 0.382),
                'fib_500': high_price - (price_range * 0.500),
                'fib_618': high_price - (price_range * 0.618),
                'fib_786': high_price - (price_range * 0.786),
                'fib_100': low_price
            }
            
            return levels
            
        except Exception as e:
            logger(f"❌ Error calculating Fibonacci levels: {str(e)}")
            return {}
    
    def calculate_support_resistance(self, high: pd.Series, low: pd.Series, close: pd.Series, 
                                   window: int = 20) -> Dict[str, List[float]]:
        """Calculate support and resistance levels"""
        try:
            if len(high) < window * 2:
                return {'support': [], 'resistance': []}
            
            # Find local maxima and minima
            resistance_levels = []
            support_levels = []
            
            for i in range(window, len(high) - window):
                # Check for resistance (local maximum)
                if high.iloc[i] == high.iloc[i-window:i+window+1].max():
                    resistance_levels.append(high.iloc[i])
                
                # Check for support (local minimum)
                if low.iloc[i] == low.iloc[i-window:i+window+1].min():
                    support_levels.append(low.iloc[i])
            
            # Remove duplicates and sort
            resistance_levels = sorted(list(set(resistance_levels)), reverse=True)[:5]  # Top 5
            support_levels = sorted(list(set(support_levels)))[:5]  # Bottom 5
            
            return {
                'resistance': resistance_levels,
                'support': support_levels
            }
            
        except Exception as e:
            logger(f"❌ Error calculating support/resistance: {str(e)}")
            return {'support': [], 'resistance': []}
    
    def calculate_volatility(self, prices: pd.Series, period: int = 20) -> pd.Series:
        """Calculate price volatility (standard deviation of returns)"""
        try:
            if len(prices) < period + 1:
                return pd.Series(index=prices.index, dtype=float)
            
            returns = prices.pct_change()
            volatility = returns.rolling(window=period).std() * np.sqrt(252)  # Annualized
            
            return volatility
            
        except Exception as e:
            logger(f"❌ Error calculating volatility: {str(e)}")
            return pd.Series(index=prices.index, dtype=float)
    
    def calculate_volume_indicators(self, prices: pd.Series, volume: pd.Series) -> Dict[str, pd.Series]:
        """Calculate volume-based indicators"""
        try:
            if len(prices) != len(volume) or len(prices) < 20:
                empty_series = pd.Series(index=prices.index, dtype=float)
                return {
                    'vwap': empty_series,
                    'volume_sma': empty_series,
                    'volume_ratio': empty_series
                }
            
            # Volume Weighted Average Price (VWAP)
            cumulative_volume = volume.cumsum()
            cumulative_price_volume = (prices * volume).cumsum()
            vwap = cumulative_price_volume / cumulative_volume
            
            # Volume moving average
            volume_sma = volume.rolling(window=20).mean()
            
            # Volume ratio (current volume vs average)
            volume_ratio = volume / volume_sma
            
            return {
                'vwap': vwap,
                'volume_sma': volume_sma,
                'volume_ratio': volume_ratio
            }
            
        except Exception as e:
            logger(f"❌ Error calculating volume indicators: {str(e)}")
            empty_series = pd.Series(index=prices.index, dtype=float)
            return {
                'vwap': empty_series,
                'volume_sma': empty_series,
                'volume_ratio': empty_series
            }
    
    def detect_candlestick_patterns(self, open_prices: pd.Series, high: pd.Series, 
                                  low: pd.Series, close: pd.Series) -> Dict[str, pd.Series]:
        """Detect basic candlestick patterns"""
        try:
            if len(open_prices) < 3:
                empty_series = pd.Series(index=open_prices.index, dtype=bool)
                return {
                    'doji': empty_series,
                    'hammer': empty_series,
                    'shooting_star': empty_series,
                    'engulfing_bullish': empty_series,
                    'engulfing_bearish': empty_series
                }
            
            # Calculate body and shadow sizes
            body = abs(close - open_prices)
            upper_shadow = high - np.maximum(open_prices, close)
            lower_shadow = np.minimum(open_prices, close) - low
            total_range = high - low
            
            # Doji pattern (small body)
            doji = body <= (total_range * 0.1)
            
            # Hammer pattern (small body, long lower shadow)
            hammer = (
                (body <= (total_range * 0.3)) &
                (lower_shadow >= (total_range * 0.6)) &
                (upper_shadow <= (total_range * 0.1))
            )
            
            # Shooting star pattern (small body, long upper shadow)
            shooting_star = (
                (body <= (total_range * 0.3)) &
                (upper_shadow >= (total_range * 0.6)) &
                (lower_shadow <= (total_range * 0.1))
            )
            
            # Bullish engulfing pattern
            prev_body = body.shift(1)
            prev_close = close.shift(1)
            prev_open = open_prices.shift(1)
            
            engulfing_bullish = (
                (prev_close < prev_open) &  # Previous candle bearish
                (close > open_prices) &     # Current candle bullish
                (open_prices < prev_close) &  # Current open below prev close
                (close > prev_open)         # Current close above prev open
            )
            
            # Bearish engulfing pattern
            engulfing_bearish = (
                (prev_close > prev_open) &  # Previous candle bullish
                (close < open_prices) &     # Current candle bearish
                (open_prices > prev_close) &  # Current open above prev close
                (close < prev_open)         # Current close below prev open
            )
            
            return {
                'doji': doji,
                'hammer': hammer,
                'shooting_star': shooting_star,
                'engulfing_bullish': engulfing_bullish,
                'engulfing_bearish': engulfing_bearish
            }
            
        except Exception as e:
            logger(f"❌ Error detecting candlestick patterns: {str(e)}")
            empty_series = pd.Series(index=open_prices.index, dtype=bool)
            return {
                'doji': empty_series,
                'hammer': empty_series,
                'shooting_star': empty_series,
                'engulfing_bullish': empty_series,
                'engulfing_bearish': empty_series
            }
    
    def get_trend_direction(self, prices: pd.Series, short_period: int = 20, long_period: int = 50) -> str:
        """Determine overall trend direction"""
        try:
            if len(prices) < long_period:
                return "Unknown"
            
            short_ma = self.calculate_sma(prices, short_period).iloc[-1]
            long_ma = self.calculate_sma(prices, long_period).iloc[-1]
            current_price = prices.iloc[-1]
            
            if short_ma > long_ma and current_price > short_ma:
                return "Uptrend"
            elif short_ma < long_ma and current_price < short_ma:
                return "Downtrend"
            else:
                return "Sideways"
                
        except Exception as e:
            logger(f"❌ Error determining trend: {str(e)}")
            return "Unknown"
    
    def calculate_all_indicators(self, ohlcv_data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate all indicators for given OHLCV data"""
        try:
            if len(ohlcv_data) < 50:
                logger("⚠️ Insufficient data for comprehensive indicator calculation")
                return {}
            
            indicators = {}
            
            # Basic price data
            open_prices = ohlcv_data['open']
            high = ohlcv_data['high']
            low = ohlcv_data['low']
            close = ohlcv_data['close']
            volume = ohlcv_data.get('tick_volume', ohlcv_data.get('volume', pd.Series()))
            
            # Moving averages
            indicators['sma_20'] = self.calculate_sma(close, 20)
            indicators['sma_50'] = self.calculate_sma(close, 50)
            indicators['ema_12'] = self.calculate_ema(close, 12)
            indicators['ema_26'] = self.calculate_ema(close, 26)
            
            # Momentum indicators
            indicators['rsi'] = self.calculate_rsi(close)
            macd_data = self.calculate_macd(close)
            indicators.update(macd_data)
            
            # Volatility indicators
            indicators['atr'] = self.calculate_atr(high, low, close)
            bb_data = self.calculate_bollinger_bands(close)
            indicators.update(bb_data)
            
            # Oscillators
            stoch_data = self.calculate_stochastic(high, low, close)
            indicators.update(stoch_data)
            indicators['williams_r'] = self.calculate_williams_r(high, low, close)
            indicators['cci'] = self.calculate_cci(high, low, close)
            
            # Trend indicators
            adx_data = self.calculate_adx(high, low, close)
            indicators.update(adx_data)
            
            # Other indicators
            indicators['momentum'] = self.calculate_momentum(close)
            indicators['roc'] = self.calculate_roc(close)
            indicators['volatility'] = self.calculate_volatility(close)
            
            # Volume indicators (if volume data available)
            if not volume.empty:
                volume_data = self.calculate_volume_indicators(close, volume)
                indicators.update(volume_data)
            
            # Candlestick patterns
            pattern_data = self.detect_candlestick_patterns(open_prices, high, low, close)
            indicators.update(pattern_data)
            
            # Support/Resistance levels
            sr_levels = self.calculate_support_resistance(high, low, close)
            indicators['support_resistance'] = sr_levels
            
            # Pivot points
            pivot_points = self.calculate_pivot_points(high, low, close)
            indicators['pivot_points'] = pivot_points
            
            # Trend direction
            indicators['trend_direction'] = self.get_trend_direction(close)
            
            logger(f"✅ Calculated {len(indicators)} technical indicators")
            return indicators
            
        except Exception as e:
            logger(f"❌ Error calculating all indicators: {str(e)}")
            return {}
