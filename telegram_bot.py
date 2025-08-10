"""
Advanced MT5 Trading Bot - Telegram Integration
Telegram bot for notifications and remote monitoring
"""

import requests
import threading
import time
from typing import Optional, Dict, Any, List
import datetime
import os
from utils import logger

class TelegramBot:
    """Telegram bot for trading notifications"""
    
    def __init__(self, config_manager):
        """Initialize Telegram bot"""
        self.config_manager = config_manager
        self.token = None
        self.chat_id = None
        self.enabled = False
        self.message_queue = []
        self.last_message_time = 0
        self.rate_limit_delay = 1  # Seconds between messages
        
        self._load_credentials()
        
        if self.enabled:
            # Start message worker thread
            threading.Thread(target=self._message_worker, daemon=True).start()
    
    def _load_credentials(self) -> None:
        """Load Telegram credentials from config and environment"""
        try:
            config = self.config_manager.get_config()
            
            # Get credentials from environment variables or config
            self.token = os.getenv('TELEGRAM_TOKEN') or config.get('telegram_token', '')
            self.chat_id = os.getenv('TELEGRAM_CHAT_ID') or config.get('telegram_chat_id', '')
            
            # Check if Telegram is enabled and credentials are available
            self.enabled = (
                config.get('telegram_enabled', False) and
                bool(self.token) and
                bool(self.chat_id)
            )
            
            if self.enabled:
                logger("✅ Telegram bot initialized")
                # Test connection
                if self._test_connection():
                    self.send_message("🤖 MT5 Trading Bot - Telegram Connected")
                else:
                    logger("⚠️ Telegram connection test failed")
                    self.enabled = False
            else:
                logger("ℹ️ Telegram bot disabled or credentials missing")
                
        except Exception as e:
            logger(f"❌ Error loading Telegram credentials: {str(e)}")
            self.enabled = False
    
    def _test_connection(self) -> bool:
        """Test Telegram bot connection"""
        try:
            if not self.token:
                return False
            
            url = f"https://api.telegram.org/bot{self.token}/getMe"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    bot_info = data.get('result', {})
                    logger(f"✅ Telegram bot connected: @{bot_info.get('username', 'unknown')}")
                    return True
            
            logger(f"❌ Telegram test failed: {response.status_code}")
            return False
            
        except Exception as e:
            logger(f"❌ Telegram connection test error: {str(e)}")
            return False
    
    def send_message(self, message: str, priority: str = 'normal') -> bool:
        """Send message to Telegram (queued)"""
        try:
            if not self.enabled:
                return False
            
            # Add message to queue
            self.message_queue.append({
                'message': message,
                'priority': priority,
                'timestamp': time.time()
            })
            
            return True
            
        except Exception as e:
            logger(f"❌ Error queuing Telegram message: {str(e)}")
            return False
    
    def _message_worker(self) -> None:
        """Background worker to send queued messages"""
        while True:
            try:
                if not self.enabled or not self.message_queue:
                    time.sleep(1)
                    continue
                
                # Rate limiting
                current_time = time.time()
                if current_time - self.last_message_time < self.rate_limit_delay:
                    time.sleep(0.5)
                    continue
                
                # Get next message (priority queue)
                message_data = self._get_next_message()
                if not message_data:
                    continue
                
                # Send message
                if self._send_message_now(message_data['message']):
                    self.last_message_time = current_time
                else:
                    # Re-queue failed message if recent
                    if current_time - message_data['timestamp'] < 300:  # 5 minutes
                        self.message_queue.append(message_data)
                
                time.sleep(0.1)
                
            except Exception as e:
                logger(f"❌ Error in Telegram message worker: {str(e)}")
                time.sleep(5)
    
    def _get_next_message(self) -> Optional[Dict[str, Any]]:
        """Get next message from queue (priority-based)"""
        try:
            if not self.message_queue:
                return None
            
            # Sort by priority (high first) then by timestamp
            priority_order = {'high': 0, 'normal': 1, 'low': 2}
            
            self.message_queue.sort(
                key=lambda x: (priority_order.get(x['priority'], 1), x['timestamp'])
            )
            
            return self.message_queue.pop(0)
            
        except Exception as e:
            logger(f"❌ Error getting next message: {str(e)}")
            return None
    
    def _send_message_now(self, message: str) -> bool:
        """Send message immediately"""
        try:
            if not self.enabled or not self.token or not self.chat_id:
                return False
            
            # Prepare message
            formatted_message = self._format_message(message)
            
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            
            payload = {
                'chat_id': self.chat_id,
                'text': formatted_message,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': True
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    return True
                else:
                    logger(f"❌ Telegram API error: {data.get('description', 'Unknown error')}")
            else:
                logger(f"❌ Telegram HTTP error: {response.status_code}")
            
            return False
            
        except Exception as e:
            logger(f"❌ Error sending Telegram message: {str(e)}")
            return False
    
    def _format_message(self, message: str) -> str:
        """Format message for Telegram"""
        try:
            # Add timestamp
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            formatted = f"⏰ `{timestamp}`\n{message}"
            
            # Escape special characters for Markdown
            special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
            for char in special_chars:
                if char not in ['`', '*', '_']:  # Keep some formatting
                    formatted = formatted.replace(char, f'\\{char}')
            
            return formatted
            
        except Exception as e:
            logger(f"❌ Error formatting message: {str(e)}")
            return message
    
    def send_trade_notification(self, trade_data: Dict[str, Any]) -> bool:
        """Send trade execution notification"""
        try:
            if not self.enabled:
                return False
            
            config = self.config_manager.get_config()
            if not config.get('telegram_notifications', {}).get('trades', True):
                return False
            
            # Format trade message
            action = trade_data.get('action', 'UNKNOWN').upper()
            symbol = trade_data.get('symbol', 'UNKNOWN')
            volume = trade_data.get('volume', 0)
            price = trade_data.get('price', 0)
            strategy = trade_data.get('strategy', 'Unknown')
            confidence = trade_data.get('confidence', 0)
            
            message = f"🎯 *TRADE EXECUTED*\n\n"
            message += f"📊 Symbol: `{symbol}`\n"
            message += f"🔄 Action: *{action}*\n"
            message += f"💰 Volume: `{volume}` lots\n"
            message += f"💲 Price: `{price:.5f}`\n"
            message += f"🧠 Strategy: `{strategy}`\n"
            message += f"🎯 Confidence: `{confidence:.2f}`"
            
            # Add TP/SL if available
            if 'tp' in trade_data and trade_data['tp'] > 0:
                message += f"\n🎯 TP: `{trade_data['tp']:.5f}`"
            if 'sl' in trade_data and trade_data['sl'] > 0:
                message += f"\n🛑 SL: `{trade_data['sl']:.5f}`"
            
            return self.send_message(message, priority='high')
            
        except Exception as e:
            logger(f"❌ Error sending trade notification: {str(e)}")
            return False
    
    def send_signal_notification(self, signal_data: Dict[str, Any]) -> bool:
        """Send trading signal notification"""
        try:
            if not self.enabled:
                return False
            
            action = signal_data.get('action', 'UNKNOWN').upper()
            symbol = signal_data.get('symbol', 'UNKNOWN')
            strategy = signal_data.get('strategy', 'Unknown')
            confidence = signal_data.get('confidence', 0)
            reason = signal_data.get('reason', 'No reason provided')
            
            message = f"🚨 *TRADING SIGNAL*\n\n"
            message += f"📊 Symbol: `{symbol}`\n"
            message += f"🔄 Signal: *{action}*\n"
            message += f"🧠 Strategy: `{strategy}`\n"
            message += f"🎯 Confidence: `{confidence:.2f}`\n"
            message += f"💡 Reason: {reason}"
            
            return self.send_message(message, priority='normal')
            
        except Exception as e:
            logger(f"❌ Error sending signal notification: {str(e)}")
            return False
    
    def send_error_notification(self, error_message: str, error_type: str = 'General') -> bool:
        """Send error notification"""
        try:
            if not self.enabled:
                return False
            
            config = self.config_manager.get_config()
            if not config.get('telegram_notifications', {}).get('errors', True):
                return False
            
            message = f"❌ *ERROR ALERT*\n\n"
            message += f"🏷️ Type: `{error_type}`\n"
            message += f"📝 Message: {error_message}"
            
            return self.send_message(message, priority='high')
            
        except Exception as e:
            logger(f"❌ Error sending error notification: {str(e)}")
            return False
    
    def send_daily_summary(self, summary_data: Dict[str, Any]) -> bool:
        """Send daily trading summary"""
        try:
            if not self.enabled:
                return False
            
            config = self.config_manager.get_config()
            if not config.get('telegram_notifications', {}).get('daily_summary', True):
                return False
            
            date = summary_data.get('date', 'Unknown')
            profit = summary_data.get('daily_profit', 0)
            profit_pct = summary_data.get('daily_profit_pct', 0)
            trades = summary_data.get('total_trades', 0)
            win_rate = summary_data.get('win_rate', 0)
            balance = summary_data.get('current_balance', 0)
            
            profit_emoji = "📈" if profit > 0 else "📉" if profit < 0 else "➡️"
            
            message = f"📊 *DAILY SUMMARY*\n\n"
            message += f"📅 Date: `{date}`\n"
            message += f"{profit_emoji} P/L: `{profit:.2f}` ({profit_pct:.2f}%)\n"
            message += f"🔢 Trades: `{trades}`\n"
            message += f"🎯 Win Rate: `{win_rate:.1f}%`\n"
            message += f"💰 Balance: `{balance:.2f}`"
            
            return self.send_message(message, priority='normal')
            
        except Exception as e:
            logger(f"❌ Error sending daily summary: {str(e)}")
            return False
    
    def send_connection_notification(self, status: str, details: str = '') -> bool:
        """Send connection status notification"""
        try:
            if not self.enabled:
                return False
            
            config = self.config_manager.get_config()
            if not config.get('telegram_notifications', {}).get('connections', False):
                return False
            
            status_emoji = "✅" if status.lower() == 'connected' else "❌"
            
            message = f"{status_emoji} *MT5 CONNECTION*\n\n"
            message += f"📊 Status: `{status}`"
            
            if details:
                message += f"\n📝 Details: {details}"
            
            return self.send_message(message, priority='normal')
            
        except Exception as e:
            logger(f"❌ Error sending connection notification: {str(e)}")
            return False
    
    def send_custom_message(self, title: str, content: str, priority: str = 'normal') -> bool:
        """Send custom formatted message"""
        try:
            if not self.enabled:
                return False
            
            message = f"*{title}*\n\n{content}"
            return self.send_message(message, priority=priority)
            
        except Exception as e:
            logger(f"❌ Error sending custom message: {str(e)}")
            return False
    
    def get_bot_info(self) -> Dict[str, Any]:
        """Get Telegram bot information"""
        try:
            return {
                'enabled': self.enabled,
                'token_available': bool(self.token),
                'chat_id_available': bool(self.chat_id),
                'queue_size': len(self.message_queue),
                'last_message_time': self.last_message_time
            }
        except Exception as e:
            logger(f"❌ Error getting bot info: {str(e)}")
            return {}
    
    def clear_message_queue(self) -> int:
        """Clear message queue and return number of cleared messages"""
        try:
            cleared_count = len(self.message_queue)
            self.message_queue.clear()
            logger(f"🧹 Cleared {cleared_count} Telegram messages from queue")
            return cleared_count
        except Exception as e:
            logger(f"❌ Error clearing message queue: {str(e)}")
            return 0
    
    def update_credentials(self, token: str = None, chat_id: str = None) -> bool:
        """Update Telegram credentials"""
        try:
            if token:
                self.token = token
                # Update environment variable
                os.environ['TELEGRAM_TOKEN'] = token
            
            if chat_id:
                self.chat_id = chat_id
                # Update environment variable
                os.environ['TELEGRAM_CHAT_ID'] = chat_id
            
            # Update config
            if token or chat_id:
                if token:
                    self.config_manager.update_config('telegram_token', token)
                if chat_id:
                    self.config_manager.update_config('telegram_chat_id', chat_id)
                
                self.config_manager.save_config()
            
            # Re-test connection
            self.enabled = bool(self.token) and bool(self.chat_id)
            if self.enabled:
                if self._test_connection():
                    logger("✅ Telegram credentials updated successfully")
                    return True
                else:
                    logger("❌ Telegram credentials test failed")
                    self.enabled = False
                    return False
            
            return True
            
        except Exception as e:
            logger(f"❌ Error updating Telegram credentials: {str(e)}")
            return False
    
    def disable(self) -> None:
        """Disable Telegram notifications"""
        try:
            self.enabled = False
            self.config_manager.update_config('telegram_enabled', False)
            self.config_manager.save_config()
            logger("🔕 Telegram notifications disabled")
        except Exception as e:
            logger(f"❌ Error disabling Telegram: {str(e)}")
    
    def enable(self) -> bool:
        """Enable Telegram notifications"""
        try:
            if self.token and self.chat_id:
                self.enabled = True
                self.config_manager.update_config('telegram_enabled', True)
                self.config_manager.save_config()
                
                if self._test_connection():
                    logger("🔔 Telegram notifications enabled")
                    return True
                else:
                    self.enabled = False
                    return False
            else:
                logger("❌ Cannot enable Telegram: Missing credentials")
                return False
                
        except Exception as e:
            logger(f"❌ Error enabling Telegram: {str(e)}")
            return False
