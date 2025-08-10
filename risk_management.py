"""
Advanced MT5 Trading Bot - Risk Management
Comprehensive risk management system for position sizing and protection
"""

try:
    import MetaTrader5 as mt5
except ImportError:
    import mock_mt5 as mt5
from typing import Dict, Any, Optional, List
import datetime
import numpy as np
from utils import logger, calculate_pip_value, safe_divide

class RiskManager:
    """Comprehensive risk management system"""
    
    def __init__(self, config_manager):
        """Initialize risk manager"""
        self.config_manager = config_manager
        self.daily_stats = {
            'start_balance': 0.0,
            'current_profit': 0.0,
            'trades_today': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'consecutive_losses': 0,
            'max_drawdown_today': 0.0,
            'last_reset': datetime.date.today()
        }
        self.position_history = []
        
    def can_trade(self) -> bool:
        """Check if trading is allowed based on risk rules"""
        try:
            # Update daily stats if new day
            self._check_daily_reset()
            
            # Get current account info
            account_info = mt5.account_info()
            if not account_info:
                logger("❌ Cannot get account info for risk check")
                return False
            
            config = self.config_manager.get_config()
            
            # Check daily loss limit
            if not self._check_daily_loss_limit(account_info):
                return False
            
            # Check daily profit target
            if not self._check_daily_profit_target(account_info):
                return False
            
            # Check maximum drawdown
            if not self._check_max_drawdown(account_info):
                return False
            
            # Check position limits
            if not self._check_position_limits():
                return False
            
            # Check consecutive loss streak
            if not self._check_loss_streak():
                return False
            
            # Check margin requirements
            if not self._check_margin_requirements(account_info):
                return False
            
            return True
            
        except Exception as e:
            logger(f"❌ Error in risk check: {str(e)}")
            return False
    
    def _check_daily_reset(self) -> None:
        """Reset daily statistics if new day"""
        try:
            today = datetime.date.today()
            if self.daily_stats['last_reset'] < today:
                # New trading day
                account_info = mt5.account_info()
                if account_info:
                    self.daily_stats['start_balance'] = account_info.balance
                
                self.daily_stats.update({
                    'current_profit': 0.0,
                    'trades_today': 0,
                    'winning_trades': 0,
                    'losing_trades': 0,
                    'consecutive_losses': 0,
                    'max_drawdown_today': 0.0,
                    'last_reset': today
                })
                
                logger(f"📅 Daily risk stats reset for {today}")
                
        except Exception as e:
            logger(f"❌ Error resetting daily stats: {str(e)}")
    
    def _check_daily_loss_limit(self, account_info) -> bool:
        """Check daily loss limit"""
        try:
            config = self.config_manager.get_config()
            max_daily_loss = config.get('max_daily_loss', 5.0)
            
            if self.daily_stats['start_balance'] == 0:
                self.daily_stats['start_balance'] = account_info.balance
            
            current_loss_pct = safe_divide(
                (self.daily_stats['start_balance'] - account_info.balance),
                self.daily_stats['start_balance'] * 100
            )
            
            if current_loss_pct > max_daily_loss:
                logger(f"🛑 Daily loss limit reached: {current_loss_pct:.2f}% > {max_daily_loss}%")
                return False
            
            return True
            
        except Exception as e:
            logger(f"❌ Error checking daily loss limit: {str(e)}")
            return False
    
    def _check_daily_profit_target(self, account_info) -> bool:
        """Check if daily profit target is reached"""
        try:
            config = self.config_manager.get_config()
            daily_profit_target = config.get('daily_profit_target', 10.0)
            
            if self.daily_stats['start_balance'] == 0:
                return True
            
            current_profit_pct = safe_divide(
                (account_info.balance - self.daily_stats['start_balance']),
                self.daily_stats['start_balance'] * 100
            )
            
            if current_profit_pct >= daily_profit_target:
                logger(f"🎯 Daily profit target reached: {current_profit_pct:.2f}% >= {daily_profit_target}%")
                # Optionally stop trading when target is reached
                # For now, we'll continue trading but log the achievement
                # return False
            
            return True
            
        except Exception as e:
            logger(f"❌ Error checking profit target: {str(e)}")
            return True
    
    def _check_max_drawdown(self, account_info) -> bool:
        """Check maximum drawdown"""
        try:
            config = self.config_manager.get_config()
            max_drawdown = config.get('max_drawdown', 5.0)
            auto_stop = config.get('auto_stop_drawdown', True)
            
            if not auto_stop:
                return True
            
            if self.daily_stats['start_balance'] == 0:
                return True
            
            # Calculate current drawdown
            peak_balance = max(self.daily_stats['start_balance'], account_info.equity)
            current_drawdown = safe_divide(
                (peak_balance - account_info.equity),
                peak_balance * 100
            )
            
            if current_drawdown > max_drawdown:
                logger(f"🛑 Maximum drawdown exceeded: {current_drawdown:.2f}% > {max_drawdown}%")
                return False
            
            return True
            
        except Exception as e:
            logger(f"❌ Error checking drawdown: {str(e)}")
            return False
    
    def _check_position_limits(self) -> bool:
        """Check position count limits"""
        try:
            config = self.config_manager.get_config()
            max_positions = config.get('max_positions', 10)
            
            current_positions = mt5.positions_total()
            if current_positions >= max_positions:
                logger(f"🛑 Maximum positions reached: {current_positions} >= {max_positions}")
                return False
            
            return True
            
        except Exception as e:
            logger(f"❌ Error checking position limits: {str(e)}")
            return False
    
    def _check_loss_streak(self) -> bool:
        """Check consecutive loss streak"""
        try:
            config = self.config_manager.get_config()
            max_loss_streak = config.get('max_loss_streak', 3)
            
            if self.daily_stats['consecutive_losses'] >= max_loss_streak:
                logger(f"🛑 Maximum loss streak reached: {self.daily_stats['consecutive_losses']} >= {max_loss_streak}")
                return False
            
            return True
            
        except Exception as e:
            logger(f"❌ Error checking loss streak: {str(e)}")
            return False
    
    def _check_margin_requirements(self, account_info) -> bool:
        """Check margin requirements"""
        try:
            # Ensure minimum free margin
            free_margin = account_info.margin_free
            margin_level = account_info.margin_level if account_info.margin > 0 else 999999
            
            # Minimum margin level (percentage)
            min_margin_level = 200  # 200%
            
            if margin_level < min_margin_level:
                logger(f"🛑 Insufficient margin level: {margin_level:.1f}% < {min_margin_level}%")
                return False
            
            # Minimum free margin amount
            min_free_margin = account_info.balance * 0.1  # 10% of balance
            if free_margin < min_free_margin:
                logger(f"🛑 Insufficient free margin: {free_margin:.2f} < {min_free_margin:.2f}")
                return False
            
            return True
            
        except Exception as e:
            logger(f"❌ Error checking margin: {str(e)}")
            return False
    
    def calculate_lot_size(self, symbol: str, signal: Dict[str, Any]) -> float:
        """Calculate optimal lot size based on risk management"""
        try:
            config = self.config_manager.get_config()
            
            # Get account info
            account_info = mt5.account_info()
            if not account_info:
                logger("❌ Cannot get account info for lot calculation")
                return 0.01
            
            # Get symbol info
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                logger(f"❌ Cannot get symbol info for {symbol}")
                return 0.01
            
            # Risk percentage
            risk_percent = config.get('risk_percent', 1.0)
            risk_amount = account_info.balance * (risk_percent / 100)
            
            # Calculate lot size based on strategy
            if config.get('auto_lot', True):
                lot_size = self._calculate_risk_based_lot(
                    risk_amount, symbol, symbol_info, signal
                )
            else:
                lot_size = config.get('lot_size', 0.01)
            
            # Apply lot size limits
            lot_size = self._apply_lot_limits(lot_size, symbol_info, account_info)
            
            logger(f"💰 Calculated lot size: {lot_size} (Risk: {risk_percent}%, Amount: {risk_amount:.2f})")
            return lot_size
            
        except Exception as e:
            logger(f"❌ Error calculating lot size: {str(e)}")
            return 0.01
    
    def _calculate_risk_based_lot(self, risk_amount: float, symbol: str, 
                                symbol_info, signal: Dict[str, Any]) -> float:
        """Calculate lot size based on risk amount"""
        try:
            config = self.config_manager.get_config()
            
            # Get stop loss distance
            sl_value = config.get('sl_value', 25)
            sl_unit = config.get('sl_unit', 'pips')
            
            # Convert SL to pips
            if sl_unit == 'pips':
                sl_pips = sl_value
            elif sl_unit == 'percent':
                current_price = signal.get('price', 0)
                if current_price > 0:
                    sl_distance = current_price * (sl_value / 100)
                    pip_size = symbol_info.point * 10 if 'JPY' in symbol else symbol_info.point * 10
                    sl_pips = sl_distance / pip_size
                else:
                    sl_pips = 25  # Default
            else:
                sl_pips = 25  # Default fallback
            
            if sl_pips <= 0:
                sl_pips = 25
            
            # Calculate pip value
            pip_value = calculate_pip_value(symbol, 1.0)  # For 1 lot
            if pip_value <= 0:
                pip_value = 10  # Default for XAUUSD
            
            # Calculate lot size
            lot_size = safe_divide(risk_amount, (sl_pips * pip_value))
            
            return lot_size
            
        except Exception as e:
            logger(f"❌ Error in risk-based lot calculation: {str(e)}")
            return 0.01
    
    def _apply_lot_limits(self, lot_size: float, symbol_info, account_info) -> float:
        """Apply minimum and maximum lot size limits"""
        try:
            # Symbol limits
            min_lot = symbol_info.volume_min
            max_lot = symbol_info.volume_max
            lot_step = symbol_info.volume_step
            
            # Ensure minimum
            lot_size = max(lot_size, min_lot)
            
            # Apply account balance limits (max 10% of balance at risk)
            balance = account_info.balance
            max_lot_by_balance = safe_divide(balance * 0.1, 1000)  # Rough calculation
            lot_size = min(lot_size, max_lot_by_balance)
            
            # Apply symbol maximum
            lot_size = min(lot_size, max_lot)
            
            # Round to lot step
            lot_size = round(lot_size / lot_step) * lot_step
            
            # Ensure minimum again after rounding
            lot_size = max(lot_size, min_lot)
            
            return round(lot_size, 2)
            
        except Exception as e:
            logger(f"❌ Error applying lot limits: {str(e)}")
            return 0.01
    
    def record_trade_result(self, symbol: str, action: str, lot_size: float, 
                          entry_price: float, exit_price: float, profit: float) -> None:
        """Record trade result for risk tracking"""
        try:
            trade_record = {
                'timestamp': datetime.datetime.now(),
                'symbol': symbol,
                'action': action,
                'lot_size': lot_size,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'profit': profit,
                'is_winning': profit > 0
            }
            
            self.position_history.append(trade_record)
            
            # Update daily stats
            self.daily_stats['trades_today'] += 1
            self.daily_stats['current_profit'] += profit
            
            if profit > 0:
                self.daily_stats['winning_trades'] += 1
                self.daily_stats['consecutive_losses'] = 0  # Reset loss streak
            else:
                self.daily_stats['losing_trades'] += 1
                self.daily_stats['consecutive_losses'] += 1
            
            # Log trade result
            result_type = "WIN" if profit > 0 else "LOSS"
            logger(f"📊 Trade {result_type}: {symbol} {action} {lot_size} lots, P/L: {profit:.2f}")
            
            # Check if emergency stop is needed
            self._check_emergency_conditions()
            
        except Exception as e:
            logger(f"❌ Error recording trade result: {str(e)}")
    
    def _check_emergency_conditions(self) -> None:
        """Check for emergency stop conditions"""
        try:
            config = self.config_manager.get_config()
            emergency_threshold = config.get('emergency_stop_threshold', 20)
            
            # Check if loss percentage exceeds emergency threshold
            account_info = mt5.account_info()
            if account_info and self.daily_stats['start_balance'] > 0:
                loss_pct = safe_divide(
                    (self.daily_stats['start_balance'] - account_info.balance),
                    self.daily_stats['start_balance'] * 100
                )
                
                if loss_pct > emergency_threshold:
                    logger(f"🚨 EMERGENCY STOP: Loss {loss_pct:.2f}% > {emergency_threshold}%")
                    # Trigger emergency stop
                    from utils import emergency_stop
                    emergency_stop()
            
        except Exception as e:
            logger(f"❌ Error checking emergency conditions: {str(e)}")
    
    def get_risk_metrics(self) -> Dict[str, Any]:
        """Get current risk metrics"""
        try:
            account_info = mt5.account_info()
            if not account_info:
                return {}
            
            # Calculate win rate
            total_trades = self.daily_stats['winning_trades'] + self.daily_stats['losing_trades']
            win_rate = safe_divide(self.daily_stats['winning_trades'], total_trades * 100)
            
            # Calculate current drawdown
            if self.daily_stats['start_balance'] > 0:
                current_profit_pct = safe_divide(
                    (account_info.balance - self.daily_stats['start_balance']),
                    self.daily_stats['start_balance'] * 100
                )
            else:
                current_profit_pct = 0
            
            # Calculate risk exposure
            positions = mt5.positions_get()
            total_risk = 0
            if positions:
                for pos in positions:
                    # Calculate risk per position (simplified)
                    position_risk = abs(pos.volume * pos.price_open * 0.01)  # 1% estimate
                    total_risk += position_risk
            
            risk_exposure_pct = safe_divide(total_risk, account_info.balance * 100)
            
            return {
                'daily_profit_pct': current_profit_pct,
                'trades_today': self.daily_stats['trades_today'],
                'win_rate': win_rate,
                'consecutive_losses': self.daily_stats['consecutive_losses'],
                'current_positions': mt5.positions_total(),
                'risk_exposure_pct': risk_exposure_pct,
                'margin_level': account_info.margin_level if account_info.margin > 0 else 999999,
                'free_margin': account_info.margin_free,
                'balance': account_info.balance,
                'equity': account_info.equity,
                'floating_pl': account_info.equity - account_info.balance
            }
            
        except Exception as e:
            logger(f"❌ Error getting risk metrics: {str(e)}")
            return {}
    
    def adjust_risk_after_loss(self) -> None:
        """Adjust risk parameters after consecutive losses"""
        try:
            consecutive_losses = self.daily_stats['consecutive_losses']
            
            if consecutive_losses >= 2:
                # Reduce risk after 2 consecutive losses
                current_risk = self.config_manager.get_setting('risk_percent', 1.0)
                reduced_risk = current_risk * 0.8  # Reduce by 20%
                reduced_risk = max(reduced_risk, 0.2)  # Minimum 0.2%
                
                self.config_manager.update_config('risk_percent', reduced_risk)
                logger(f"⚠️ Risk reduced to {reduced_risk:.1f}% after {consecutive_losses} losses")
                
        except Exception as e:
            logger(f"❌ Error adjusting risk: {str(e)}")
    
    def restore_normal_risk(self) -> None:
        """Restore normal risk after winning trade"""
        try:
            # Gradually increase risk back to normal after wins
            current_risk = self.config_manager.get_setting('risk_percent', 1.0)
            normal_risk = 1.0  # Default risk percentage
            
            if current_risk < normal_risk:
                increased_risk = min(current_risk * 1.1, normal_risk)  # Increase by 10%
                self.config_manager.update_config('risk_percent', increased_risk)
                logger(f"✅ Risk increased to {increased_risk:.1f}%")
                
        except Exception as e:
            logger(f"❌ Error restoring risk: {str(e)}")
    
    def validate_trade_parameters(self, symbol: str, lot_size: float, 
                                tp_price: float, sl_price: float) -> bool:
        """Validate trade parameters before execution"""
        try:
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                logger(f"❌ Invalid symbol: {symbol}")
                return False
            
            # Check lot size limits
            if lot_size < symbol_info.volume_min or lot_size > symbol_info.volume_max:
                logger(f"❌ Invalid lot size: {lot_size} (min: {symbol_info.volume_min}, max: {symbol_info.volume_max})")
                return False
            
            # Check lot step
            lot_step = symbol_info.volume_step
            if abs(lot_size % lot_step) > 0.001:
                logger(f"❌ Lot size not aligned with step: {lot_size} (step: {lot_step})")
                return False
            
            # Check price levels
            current_price = mt5.symbol_info_tick(symbol).ask
            min_distance = symbol_info.stops_level * symbol_info.point
            
            if tp_price > 0:
                tp_distance = abs(tp_price - current_price)
                if tp_distance < min_distance:
                    logger(f"❌ TP too close to current price: {tp_distance} < {min_distance}")
                    return False
            
            if sl_price > 0:
                sl_distance = abs(sl_price - current_price)
                if sl_distance < min_distance:
                    logger(f"❌ SL too close to current price: {sl_distance} < {min_distance}")
                    return False
            
            return True
            
        except Exception as e:
            logger(f"❌ Error validating trade parameters: {str(e)}")
            return False
    
    def get_daily_summary(self) -> Dict[str, Any]:
        """Get daily trading summary"""
        try:
            account_info = mt5.account_info()
            if not account_info:
                return {}
            
            summary = {
                'date': datetime.date.today().strftime('%Y-%m-%d'),
                'start_balance': self.daily_stats['start_balance'],
                'current_balance': account_info.balance,
                'daily_profit': account_info.balance - self.daily_stats['start_balance'],
                'daily_profit_pct': safe_divide(
                    (account_info.balance - self.daily_stats['start_balance']),
                    self.daily_stats['start_balance'] * 100
                ),
                'total_trades': self.daily_stats['trades_today'],
                'winning_trades': self.daily_stats['winning_trades'],
                'losing_trades': self.daily_stats['losing_trades'],
                'win_rate': safe_divide(
                    self.daily_stats['winning_trades'],
                    self.daily_stats['trades_today'] * 100
                ),
                'consecutive_losses': self.daily_stats['consecutive_losses'],
                'current_positions': mt5.positions_total(),
                'equity': account_info.equity,
                'margin_used': account_info.margin,
                'margin_free': account_info.margin_free
            }
            
            return summary
            
        except Exception as e:
            logger(f"❌ Error generating daily summary: {str(e)}")
            return {}
