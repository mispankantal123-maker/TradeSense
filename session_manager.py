"""
Advanced MT5 Trading Bot - Session Manager
Manages trading sessions and market hours
"""

import datetime
from typing import Dict, Any, Optional, List, Tuple
import pytz
from utils import logger, get_market_session, is_market_open

class SessionManager:
    """Trading session management system"""
    
    def __init__(self):
        """Initialize session manager"""
        self.sessions = {
            "Asia": {
                "start": "21:00",
                "end": "06:00",
                "timezone": "UTC",
                "active": True,
                "volatility": "medium",
                "preferred_pairs": ["USDJPY", "AUDUSD", "NZDUSD", "EURJPY", "GBPJPY"],
                "characteristics": {
                    "volume": "low_to_medium",
                    "volatility": "lower",
                    "spread_multiplier": 1.5,
                    "news_impact": "medium"
                }
            },
            "London": {
                "start": "07:00",
                "end": "16:00",
                "timezone": "UTC",
                "active": True,
                "volatility": "high",
                "preferred_pairs": ["EURUSD", "GBPUSD", "EURGBP", "EURJPY", "GBPJPY"],
                "characteristics": {
                    "volume": "high",
                    "volatility": "high",
                    "spread_multiplier": 1.0,
                    "news_impact": "high"
                }
            },
            "New_York": {
                "start": "13:00",
                "end": "22:00",
                "timezone": "UTC",
                "active": True,
                "volatility": "high",
                "preferred_pairs": ["EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD"],
                "characteristics": {
                    "volume": "high",
                    "volatility": "high",
                    "spread_multiplier": 0.9,
                    "news_impact": "very_high"
                }
            },
            "Overlap_London_NY": {
                "start": "13:00",
                "end": "16:00",
                "timezone": "UTC",
                "active": True,
                "volatility": "very_high",
                "preferred_pairs": ["EURUSD", "GBPUSD", "USDCAD"],
                "characteristics": {
                    "volume": "very_high",
                    "volatility": "very_high",
                    "spread_multiplier": 0.8,
                    "news_impact": "extreme"
                }
            }
        }
        
        self.current_session = None
        self.session_start_time = None
        self.daily_session_stats = {}
        
    def get_current_session(self) -> Optional[str]:
        """Get the current active trading session"""
        try:
            current_time = datetime.datetime.utcnow()
            current_hour = current_time.hour
            current_minute = current_time.minute
            current_time_minutes = current_hour * 60 + current_minute
            
            active_sessions = []
            
            for session_name, session_info in self.sessions.items():
                if not session_info.get('active', True):
                    continue
                
                start_time = self._parse_time(session_info['start'])
                end_time = self._parse_time(session_info['end'])
                
                # Handle sessions that cross midnight
                if start_time > end_time:  # Crosses midnight (like Asia session)
                    if current_time_minutes >= start_time or current_time_minutes <= end_time:
                        active_sessions.append(session_name)
                else:  # Normal session
                    if start_time <= current_time_minutes <= end_time:
                        active_sessions.append(session_name)
            
            # Prioritize overlap sessions
            if "Overlap_London_NY" in active_sessions:
                return "Overlap_London_NY"
            elif len(active_sessions) > 0:
                return active_sessions[0]
            else:
                return None
                
        except Exception as e:
            logger(f"❌ Error getting current session: {str(e)}")
            return None
    
    def _parse_time(self, time_str: str) -> int:
        """Parse time string to minutes from midnight"""
        try:
            hour, minute = map(int, time_str.split(':'))
            return hour * 60 + minute
        except:
            return 0
    
    def is_trading_session_active(self) -> bool:
        """Check if any trading session is currently active"""
        try:
            # First check if market is open (weekend check)
            if not is_market_open():
                return False
            
            current_session = self.get_current_session()
            
            if current_session:
                self.current_session = current_session
                logger(f"📊 Active trading session: {current_session}")
                return True
            else:
                logger("⏰ No active trading session")
                return False
                
        except Exception as e:
            logger(f"❌ Error checking session activity: {str(e)}")
            return False
    
    def get_session_characteristics(self, session_name: str = None) -> Dict[str, Any]:
        """Get characteristics of specified session or current session"""
        try:
            if session_name is None:
                session_name = self.get_current_session()
            
            if session_name and session_name in self.sessions:
                return self.sessions[session_name].get('characteristics', {})
            else:
                return {}
                
        except Exception as e:
            logger(f"❌ Error getting session characteristics: {str(e)}")
            return {}
    
    def get_preferred_pairs(self, session_name: str = None) -> List[str]:
        """Get preferred trading pairs for session"""
        try:
            if session_name is None:
                session_name = self.get_current_session()
            
            if session_name and session_name in self.sessions:
                return self.sessions[session_name].get('preferred_pairs', [])
            else:
                return ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"]  # Default pairs
                
        except Exception as e:
            logger(f"❌ Error getting preferred pairs: {str(e)}")
            return []
    
    def get_session_volatility_filter(self, session_name: str = None) -> float:
        """Get volatility filter multiplier for session"""
        try:
            characteristics = self.get_session_characteristics(session_name)
            volatility = characteristics.get('volatility', 'medium')
            
            volatility_multipliers = {
                'low': 0.7,
                'medium': 1.0,
                'high': 1.3,
                'very_high': 1.6
            }
            
            return volatility_multipliers.get(volatility, 1.0)
            
        except Exception as e:
            logger(f"❌ Error getting volatility filter: {str(e)}")
            return 1.0
    
    def get_session_spread_multiplier(self, session_name: str = None) -> float:
        """Get spread multiplier for session"""
        try:
            characteristics = self.get_session_characteristics(session_name)
            return characteristics.get('spread_multiplier', 1.0)
            
        except Exception as e:
            logger(f"❌ Error getting spread multiplier: {str(e)}")
            return 1.0
    
    def should_trade_pair(self, symbol: str, session_name: str = None) -> bool:
        """Check if symbol should be traded in current session"""
        try:
            preferred_pairs = self.get_preferred_pairs(session_name)
            
            # Check exact match first
            if symbol in preferred_pairs:
                return True
            
            # Check partial matches (e.g., XAUUSD matches patterns)
            for pair in preferred_pairs:
                if pair in symbol or symbol in pair:
                    return True
            
            # Special cases for gold
            if symbol in ['XAUUSD', 'GOLD', 'GOLDUSD']:
                return True  # Gold can be traded in any session
            
            return len(preferred_pairs) == 0  # If no preferences, allow all
            
        except Exception as e:
            logger(f"❌ Error checking if should trade pair: {str(e)}")
            return True
    
    def get_session_trading_intensity(self, session_name: str = None) -> str:
        """Get recommended trading intensity for session"""
        try:
            if session_name is None:
                session_name = self.get_current_session()
            
            if session_name and session_name in self.sessions:
                volatility = self.sessions[session_name].get('volatility', 'medium')
                
                intensity_map = {
                    'low': 'conservative',
                    'medium': 'moderate',
                    'high': 'aggressive',
                    'very_high': 'very_aggressive'
                }
                
                return intensity_map.get(volatility, 'moderate')
            
            return 'moderate'
            
        except Exception as e:
            logger(f"❌ Error getting trading intensity: {str(e)}")
            return 'moderate'
    
    def adjust_strategy_for_session(self, strategy_params: Dict[str, Any], 
                                  session_name: str = None) -> Dict[str, Any]:
        """Adjust strategy parameters based on session characteristics"""
        try:
            if session_name is None:
                session_name = self.get_current_session()
            
            if not session_name:
                return strategy_params
            
            characteristics = self.get_session_characteristics(session_name)
            intensity = self.get_session_trading_intensity(session_name)
            
            adjusted_params = strategy_params.copy()
            
            # Adjust based on session intensity
            if intensity == 'conservative':
                # Reduce risk and increase thresholds
                adjusted_params['risk_multiplier'] = 0.7
                adjusted_params['signal_threshold'] = adjusted_params.get('signal_threshold', 0.7) * 1.2
                adjusted_params['min_profit_multiplier'] = 1.3
                
            elif intensity == 'aggressive':
                # Increase risk and reduce thresholds
                adjusted_params['risk_multiplier'] = 1.3
                adjusted_params['signal_threshold'] = adjusted_params.get('signal_threshold', 0.7) * 0.8
                adjusted_params['min_profit_multiplier'] = 0.8
                
            elif intensity == 'very_aggressive':
                # Maximum risk and minimum thresholds
                adjusted_params['risk_multiplier'] = 1.5
                adjusted_params['signal_threshold'] = adjusted_params.get('signal_threshold', 0.7) * 0.6
                adjusted_params['min_profit_multiplier'] = 0.6
                
            # Adjust spread tolerance
            spread_multiplier = characteristics.get('spread_multiplier', 1.0)
            adjusted_params['max_spread'] = adjusted_params.get('max_spread', 3) * spread_multiplier
            
            # Adjust volatility filter
            vol_filter = self.get_session_volatility_filter(session_name)
            adjusted_params['volatility_filter'] = vol_filter
            
            logger(f"📊 Strategy adjusted for {session_name} session (intensity: {intensity})")
            return adjusted_params
            
        except Exception as e:
            logger(f"❌ Error adjusting strategy for session: {str(e)}")
            return strategy_params
    
    def get_session_schedule(self) -> Dict[str, Dict[str, str]]:
        """Get complete session schedule"""
        try:
            schedule = {}
            for session_name, session_info in self.sessions.items():
                schedule[session_name] = {
                    'start': session_info['start'],
                    'end': session_info['end'],
                    'timezone': session_info['timezone'],
                    'volatility': session_info['volatility']
                }
            return schedule
            
        except Exception as e:
            logger(f"❌ Error getting session schedule: {str(e)}")
            return {}
    
    def get_next_session(self) -> Tuple[Optional[str], Optional[datetime.datetime]]:
        """Get next upcoming session and its start time"""
        try:
            current_time = datetime.datetime.utcnow()
            current_minutes = current_time.hour * 60 + current_time.minute
            
            next_session = None
            next_start_time = None
            min_wait_minutes = 24 * 60  # Maximum wait time (24 hours)
            
            for session_name, session_info in self.sessions.items():
                if not session_info.get('active', True):
                    continue
                
                start_minutes = self._parse_time(session_info['start'])
                
                # Calculate wait time
                if start_minutes > current_minutes:
                    wait_minutes = start_minutes - current_minutes
                else:
                    wait_minutes = (24 * 60) - current_minutes + start_minutes  # Next day
                
                if wait_minutes < min_wait_minutes:
                    min_wait_minutes = wait_minutes
                    next_session = session_name
                    
                    # Calculate next start time
                    if start_minutes > current_minutes:
                        next_start_time = current_time.replace(
                            hour=start_minutes // 60,
                            minute=start_minutes % 60,
                            second=0,
                            microsecond=0
                        )
                    else:
                        next_start_time = (current_time + datetime.timedelta(days=1)).replace(
                            hour=start_minutes // 60,
                            minute=start_minutes % 60,
                            second=0,
                            microsecond=0
                        )
            
            return next_session, next_start_time
            
        except Exception as e:
            logger(f"❌ Error getting next session: {str(e)}")
            return None, None
    
    def update_session_config(self, session_name: str, config: Dict[str, Any]) -> bool:
        """Update session configuration"""
        try:
            if session_name in self.sessions:
                self.sessions[session_name].update(config)
                logger(f"✅ Updated {session_name} session configuration")
                return True
            else:
                logger(f"❌ Session {session_name} not found")
                return False
                
        except Exception as e:
            logger(f"❌ Error updating session config: {str(e)}")
            return False
    
    def enable_session(self, session_name: str, enabled: bool = True) -> bool:
        """Enable or disable a trading session"""
        try:
            if session_name in self.sessions:
                self.sessions[session_name]['active'] = enabled
                status = "enabled" if enabled else "disabled"
                logger(f"✅ Session {session_name} {status}")
                return True
            else:
                logger(f"❌ Session {session_name} not found")
                return False
                
        except Exception as e:
            logger(f"❌ Error enabling/disabling session: {str(e)}")
            return False
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """Get session trading statistics"""
        try:
            current_session = self.get_current_session()
            next_session, next_start = self.get_next_session()
            
            stats = {
                'current_session': current_session,
                'next_session': next_session,
                'next_session_start': next_start.strftime('%H:%M UTC') if next_start else None,
                'session_active': current_session is not None,
                'market_open': is_market_open(),
                'enabled_sessions': [name for name, info in self.sessions.items() if info.get('active', True)],
                'session_count': len([s for s in self.sessions.values() if s.get('active', True)])
            }
            
            if current_session:
                characteristics = self.get_session_characteristics(current_session)
                stats['current_session_characteristics'] = characteristics
                stats['preferred_pairs'] = self.get_preferred_pairs(current_session)
                stats['trading_intensity'] = self.get_session_trading_intensity(current_session)
            
            return stats
            
        except Exception as e:
            logger(f"❌ Error getting session statistics: {str(e)}")
            return {}
    
    def is_optimal_trading_time(self, symbol: str = None) -> bool:
        """Check if current time is optimal for trading"""
        try:
            # Check if market is open
            if not is_market_open():
                return False
            
            # Check if any session is active
            current_session = self.get_current_session()
            if not current_session:
                return False
            
            # Check if symbol is suitable for current session
            if symbol and not self.should_trade_pair(symbol, current_session):
                return False
            
            # Check session characteristics
            characteristics = self.get_session_characteristics(current_session)
            volatility = characteristics.get('volatility', 'medium')
            
            # Avoid very low volatility periods
            if volatility == 'low':
                return False
            
            return True
            
        except Exception as e:
            logger(f"❌ Error checking optimal trading time: {str(e)}")
            return False
    
    def get_trading_recommendations(self) -> Dict[str, Any]:
        """Get trading recommendations based on current session"""
        try:
            current_session = self.get_current_session()
            if not current_session:
                return {
                    'recommended': False,
                    'reason': 'No active trading session'
                }
            
            characteristics = self.get_session_characteristics(current_session)
            preferred_pairs = self.get_preferred_pairs(current_session)
            intensity = self.get_session_trading_intensity(current_session)
            
            recommendations = {
                'recommended': True,
                'session': current_session,
                'intensity': intensity,
                'preferred_pairs': preferred_pairs,
                'volatility_expectation': characteristics.get('volatility', 'medium'),
                'spread_condition': 'favorable' if characteristics.get('spread_multiplier', 1.0) <= 1.0 else 'normal',
                'volume_expectation': characteristics.get('volume', 'medium'),
                'risk_adjustment': {
                    'conservative': 0.7,
                    'moderate': 1.0,
                    'aggressive': 1.3,
                    'very_aggressive': 1.5
                }.get(intensity, 1.0)
            }
            
            return recommendations
            
        except Exception as e:
            logger(f"❌ Error getting trading recommendations: {str(e)}")
            return {'recommended': False, 'reason': 'Error getting recommendations'}
