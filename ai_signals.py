"""
Advanced MT5 Trading Bot - AI Signal Generator
Machine learning based signal generation using OHLCV data
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, Any, List
import warnings
from utils import logger

# Suppress sklearn warnings for cleaner output
warnings.filterwarnings('ignore', category=UserWarning)

try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger("⚠️ scikit-learn not available, AI signals disabled")

class AISignalGenerator:
    """AI-based trading signal generator"""
    
    def __init__(self):
        """Initialize AI signal generator"""
        self.models = {}
        self.scalers = {}
        self.feature_columns = []
        self.is_trained = False
        self.confidence_threshold = 0.75
        
        if SKLEARN_AVAILABLE:
            self._initialize_models()
        else:
            logger("❌ AI Signal Generator disabled - sklearn not available")
    
    def _initialize_models(self):
        """Initialize machine learning models"""
        try:
            # Ensemble of different models for better accuracy
            self.models = {
                'random_forest': RandomForestClassifier(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42,
                    n_jobs=-1
                ),
                'gradient_boost': GradientBoostingClassifier(
                    n_estimators=100,
                    learning_rate=0.1,
                    max_depth=6,
                    random_state=42
                ),
                'logistic_regression': LogisticRegression(
                    random_state=42,
                    max_iter=1000
                )
            }
            
            # Initialize scalers for each model
            for model_name in self.models.keys():
                self.scalers[model_name] = StandardScaler()
                
            logger("✅ AI models initialized")
            
        except Exception as e:
            logger(f"❌ Error initializing AI models: {str(e)}")
    
    def generate_signal(self, df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Generate trading signal from OHLCV data"""
        try:
            if not SKLEARN_AVAILABLE:
                return None
            
            if len(df) < 200:
                logger("⚠️ Insufficient data for AI signal generation")
                return None
            
            # Prepare features
            features = self._prepare_features(df)
            if features is None or len(features) == 0:
                return None
            
            # If not trained, train on available data
            if not self.is_trained:
                self._train_models(df)
            
            # Generate predictions
            predictions = self._predict(features.iloc[-1:])
            if not predictions:
                return None
            
            # Ensemble voting
            signal = self._ensemble_vote(predictions)
            
            if signal:
                logger(f"🤖 AI Signal: {signal['action']} with confidence {signal['confidence']:.3f}")
                return signal
            
            return None
            
        except Exception as e:
            logger(f"❌ Error generating AI signal: {str(e)}")
            return None
    
    def _prepare_features(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Prepare features for machine learning"""
        try:
            features_df = df.copy()
            
            # Price-based features
            features_df['returns'] = features_df['close'].pct_change()
            features_df['log_returns'] = np.log(features_df['close'] / features_df['close'].shift(1))
            
            # Moving averages
            for period in [5, 10, 20, 50]:
                features_df[f'sma_{period}'] = features_df['close'].rolling(period).mean()
                features_df[f'price_to_sma_{period}'] = features_df['close'] / features_df[f'sma_{period}']
            
            # Exponential moving averages
            for period in [12, 26, 50]:
                features_df[f'ema_{period}'] = features_df['close'].ewm(span=period).mean()
                features_df[f'price_to_ema_{period}'] = features_df['close'] / features_df[f'ema_{period}']
            
            # RSI
            features_df['rsi'] = self._calculate_rsi(features_df['close'], 14)
            features_df['rsi_oversold'] = (features_df['rsi'] < 30).astype(int)
            features_df['rsi_overbought'] = (features_df['rsi'] > 70).astype(int)
            
            # MACD
            ema_12 = features_df['close'].ewm(span=12).mean()
            ema_26 = features_df['close'].ewm(span=26).mean()
            features_df['macd'] = ema_12 - ema_26
            features_df['macd_signal'] = features_df['macd'].ewm(span=9).mean()
            features_df['macd_histogram'] = features_df['macd'] - features_df['macd_signal']
            
            # Bollinger Bands
            bb_period = 20
            bb_std = 2
            features_df['bb_middle'] = features_df['close'].rolling(bb_period).mean()
            bb_std_dev = features_df['close'].rolling(bb_period).std()
            features_df['bb_upper'] = features_df['bb_middle'] + (bb_std_dev * bb_std)
            features_df['bb_lower'] = features_df['bb_middle'] - (bb_std_dev * bb_std)
            features_df['bb_position'] = (features_df['close'] - features_df['bb_lower']) / (features_df['bb_upper'] - features_df['bb_lower'])
            
            # ATR (Average True Range)
            features_df['tr'] = np.maximum(
                features_df['high'] - features_df['low'],
                np.maximum(
                    abs(features_df['high'] - features_df['close'].shift(1)),
                    abs(features_df['low'] - features_df['close'].shift(1))
                )
            )
            features_df['atr'] = features_df['tr'].rolling(14).mean()
            features_df['atr_normalized'] = features_df['atr'] / features_df['close']
            
            # Volume features
            features_df['volume_sma'] = features_df['tick_volume'].rolling(20).mean()
            features_df['volume_ratio'] = features_df['tick_volume'] / features_df['volume_sma']
            
            # Price patterns
            features_df['high_low_ratio'] = features_df['high'] / features_df['low']
            features_df['body_size'] = abs(features_df['close'] - features_df['open']) / features_df['close']
            features_df['upper_shadow'] = (features_df['high'] - np.maximum(features_df['open'], features_df['close'])) / features_df['close']
            features_df['lower_shadow'] = (np.minimum(features_df['open'], features_df['close']) - features_df['low']) / features_df['close']
            
            # Momentum indicators
            for period in [3, 5, 10]:
                features_df[f'momentum_{period}'] = features_df['close'] / features_df['close'].shift(period) - 1
            
            # Volatility measures
            for period in [5, 10, 20]:
                features_df[f'volatility_{period}'] = features_df['returns'].rolling(period).std()
            
            # Support and resistance levels
            features_df['recent_high'] = features_df['high'].rolling(20).max()
            features_df['recent_low'] = features_df['low'].rolling(20).min()
            features_df['distance_to_high'] = (features_df['recent_high'] - features_df['close']) / features_df['close']
            features_df['distance_to_low'] = (features_df['close'] - features_df['recent_low']) / features_df['close']
            
            # Trend indicators
            features_df['price_trend_5'] = (features_df['close'] > features_df['close'].shift(5)).astype(int)
            features_df['price_trend_10'] = (features_df['close'] > features_df['close'].shift(10)).astype(int)
            features_df['ema_trend'] = (features_df['ema_12'] > features_df['ema_26']).astype(int)
            
            # Select feature columns (exclude OHLCV and intermediate calculations)
            self.feature_columns = [
                'returns', 'log_returns',
                'price_to_sma_5', 'price_to_sma_10', 'price_to_sma_20', 'price_to_sma_50',
                'price_to_ema_12', 'price_to_ema_26', 'price_to_ema_50',
                'rsi', 'rsi_oversold', 'rsi_overbought',
                'macd', 'macd_signal', 'macd_histogram',
                'bb_position', 'atr_normalized',
                'volume_ratio', 'high_low_ratio', 'body_size', 'upper_shadow', 'lower_shadow',
                'momentum_3', 'momentum_5', 'momentum_10',
                'volatility_5', 'volatility_10', 'volatility_20',
                'distance_to_high', 'distance_to_low',
                'price_trend_5', 'price_trend_10', 'ema_trend'
            ]
            
            # Return features dataframe
            feature_data = features_df[self.feature_columns].copy()
            
            # Drop rows with NaN values
            feature_data = feature_data.dropna()
            
            return feature_data
            
        except Exception as e:
            logger(f"❌ Error preparing features: {str(e)}")
            return None
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        except:
            return pd.Series(index=prices.index, dtype=float)
    
    def _create_labels(self, df: pd.DataFrame, lookahead: int = 5) -> pd.Series:
        """Create labels for supervised learning"""
        try:
            # Calculate future returns
            future_returns = df['close'].shift(-lookahead) / df['close'] - 1
            
            # Create labels: 1 for buy, 0 for hold, -1 for sell
            labels = pd.Series(index=df.index, dtype=int)
            
            # Define thresholds (can be adjusted)
            buy_threshold = 0.002  # 0.2% gain
            sell_threshold = -0.002  # 0.2% loss
            
            labels[future_returns > buy_threshold] = 1  # Buy signal
            labels[future_returns < sell_threshold] = -1  # Sell signal
            labels[(future_returns >= sell_threshold) & (future_returns <= buy_threshold)] = 0  # Hold
            
            return labels
            
        except Exception as e:
            logger(f"❌ Error creating labels: {str(e)}")
            return pd.Series(dtype=int)
    
    def _train_models(self, df: pd.DataFrame) -> bool:
        """Train machine learning models"""
        try:
            logger("🤖 Training AI models...")
            
            # Prepare features and labels
            features = self._prepare_features(df)
            if features is None or len(features) < 100:
                logger("❌ Insufficient data for training")
                return False
            
            labels = self._create_labels(df)
            
            # Align features and labels
            aligned_data = features.join(labels.rename('label'), how='inner')
            aligned_data = aligned_data.dropna()
            
            if len(aligned_data) < 50:
                logger("❌ Insufficient aligned data for training")
                return False
            
            # Split features and labels
            X = aligned_data[self.feature_columns]
            y = aligned_data['label']
            
            # Filter out hold signals for binary classification
            binary_mask = y != 0
            X_binary = X[binary_mask]
            y_binary = (y[binary_mask] > 0).astype(int)  # 1 for buy, 0 for sell
            
            if len(X_binary) < 30:
                logger("❌ Insufficient binary signals for training")
                return False
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X_binary, y_binary, test_size=0.2, random_state=42, stratify=y_binary
            )
            
            # Train each model
            trained_models = 0
            for model_name, model in self.models.items():
                try:
                    # Scale features
                    X_train_scaled = self.scalers[model_name].fit_transform(X_train)
                    X_test_scaled = self.scalers[model_name].transform(X_test)
                    
                    # Train model
                    model.fit(X_train_scaled, y_train)
                    
                    # Evaluate
                    y_pred = model.predict(X_test_scaled)
                    accuracy = accuracy_score(y_test, y_pred)
                    
                    logger(f"✅ {model_name} trained - Accuracy: {accuracy:.3f}")
                    trained_models += 1
                    
                except Exception as e:
                    logger(f"❌ Error training {model_name}: {str(e)}")
                    continue
            
            if trained_models > 0:
                self.is_trained = True
                logger(f"✅ AI training completed - {trained_models} models trained")
                return True
            else:
                logger("❌ No models successfully trained")
                return False
                
        except Exception as e:
            logger(f"❌ Error in model training: {str(e)}")
            return False
    
    def _predict(self, features: pd.DataFrame) -> Dict[str, Any]:
        """Generate predictions from all models"""
        try:
            predictions = {}
            
            for model_name, model in self.models.items():
                try:
                    # Scale features
                    features_scaled = self.scalers[model_name].transform(features[self.feature_columns])
                    
                    # Get prediction and probability
                    prediction = model.predict(features_scaled)[0]
                    probabilities = model.predict_proba(features_scaled)[0]
                    
                    # Store prediction with confidence
                    predictions[model_name] = {
                        'prediction': prediction,
                        'confidence': max(probabilities)
                    }
                    
                except Exception as e:
                    logger(f"⚠️ Error in {model_name} prediction: {str(e)}")
                    continue
            
            return predictions
            
        except Exception as e:
            logger(f"❌ Error in prediction: {str(e)}")
            return {}
    
    def _ensemble_vote(self, predictions: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Combine predictions from multiple models"""
        try:
            if not predictions:
                return None
            
            # Collect votes and confidences
            buy_votes = 0
            sell_votes = 0
            total_confidence = 0
            model_count = 0
            
            for model_name, pred_data in predictions.items():
                prediction = pred_data['prediction']
                confidence = pred_data['confidence']
                
                if prediction == 1:  # Buy
                    buy_votes += confidence
                else:  # Sell
                    sell_votes += confidence
                
                total_confidence += confidence
                model_count += 1
            
            if model_count == 0:
                return None
            
            # Determine final signal
            avg_confidence = total_confidence / model_count
            
            # Require minimum confidence
            if avg_confidence < self.confidence_threshold:
                return None
            
            # Determine action based on weighted votes
            if buy_votes > sell_votes:
                action = 'buy'
                confidence = buy_votes / (buy_votes + sell_votes)
            else:
                action = 'sell'
                confidence = sell_votes / (buy_votes + sell_votes)
            
            # Final confidence check
            if confidence < self.confidence_threshold:
                return None
            
            return {
                'action': action,
                'symbol': 'XAUUSD',  # Default symbol
                'strategy': 'AI_ML',
                'confidence': confidence,
                'price': 0,  # Will be filled by trading engine
                'reason': f'AI ensemble vote ({model_count} models)',
                'model_votes': {
                    'buy_votes': buy_votes,
                    'sell_votes': sell_votes,
                    'model_count': model_count
                }
            }
            
        except Exception as e:
            logger(f"❌ Error in ensemble voting: {str(e)}")
            return None
    
    def update_confidence_threshold(self, threshold: float) -> None:
        """Update confidence threshold"""
        try:
            if 0.5 <= threshold <= 1.0:
                self.confidence_threshold = threshold
                logger(f"✅ AI confidence threshold updated to {threshold}")
            else:
                logger("❌ Invalid confidence threshold (must be between 0.5 and 1.0)")
        except Exception as e:
            logger(f"❌ Error updating confidence threshold: {str(e)}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about trained models"""
        try:
            return {
                'is_trained': self.is_trained,
                'available_models': list(self.models.keys()) if SKLEARN_AVAILABLE else [],
                'feature_count': len(self.feature_columns),
                'confidence_threshold': self.confidence_threshold,
                'sklearn_available': SKLEARN_AVAILABLE
            }
        except Exception as e:
            logger(f"❌ Error getting model info: {str(e)}")
            return {}
    
    def retrain_models(self, df: pd.DataFrame) -> bool:
        """Retrain models with new data"""
        try:
            logger("🔄 Retraining AI models with new data...")
            self.is_trained = False
            return self._train_models(df)
        except Exception as e:
            logger(f"❌ Error retraining models: {str(e)}")
            return False
