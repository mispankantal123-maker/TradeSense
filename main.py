#!/usr/bin/env python3
"""
Advanced MT5 Trading Bot - Main Entry Point
Enhanced version with AI signals, multi-strategy trading, and comprehensive risk management
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox
import threading
import time
from typing import Optional

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui import TradingBotGUI
from trading import TradingEngine
from config import ConfigManager
from telegram_bot import TelegramBot
from utils import logger, ensure_log_directory
try:
    import MetaTrader5 as mt5
except ImportError:
    import mock_mt5 as mt5
    logger("⚠️ Using mock MT5 interface for demonstration")

class MT5TradingBot:
    """Main trading bot application"""
    
    def __init__(self):
        """Initialize the trading bot"""
        self.root = None
        self.gui = None
        self.trading_engine = None
        self.config_manager = None
        self.telegram_bot = None
        self.running = False
        
    def initialize(self) -> bool:
        """Initialize all components"""
        try:
            # Ensure log directory exists
            ensure_log_directory()
            
            logger("🚀 Initializing MT5 Advanced Trading Bot...")
            
            # Initialize configuration manager
            self.config_manager = ConfigManager()
            if not self.config_manager.load_config():
                logger("⚠️ Using default configuration")
            
            # Initialize GUI
            self.root = tk.Tk()
            self.gui = TradingBotGUI(self.root, self.config_manager)
            
            # Initialize Telegram bot
            self.telegram_bot = TelegramBot(self.config_manager)
            
            # Initialize trading engine
            self.trading_engine = TradingEngine(self.config_manager, self.gui)
            
            # Connect GUI to trading engine
            self.gui.set_trading_engine(self.trading_engine)
            
            # Send startup notification
            if self.telegram_bot.enabled:
                self.telegram_bot.send_message("🚀 MT5 Advanced Trading Bot Started Successfully!")
            
            logger("✅ Bot initialization completed successfully")
            return True
            
        except Exception as e:
            logger(f"❌ Failed to initialize bot: {str(e)}")
            import traceback
            logger(f"Full traceback: {traceback.format_exc()}")
            return False
    
    def run(self) -> None:
        """Start the trading bot application"""
        try:
            if not self.initialize():
                messagebox.showerror("Initialization Error", 
                                   "Failed to initialize trading bot. Check logs for details.")
                return
            
            self.running = True
            
            # Start the GUI main loop
            logger("🎯 Starting GUI main loop...")
            self.gui.start()
            
        except KeyboardInterrupt:
            logger("🛑 Bot stopped by user (Ctrl+C)")
            self.shutdown()
        except Exception as e:
            logger(f"❌ Critical error in main loop: {str(e)}")
            import traceback
            logger(f"Full traceback: {traceback.format_exc()}")
            self.shutdown()
    
    def shutdown(self) -> None:
        """Gracefully shutdown the bot"""
        try:
            logger("🛑 Shutting down trading bot...")
            self.running = False
            
            # Send shutdown notification
            if self.telegram_bot and self.telegram_bot.enabled:
                self.telegram_bot.send_message("🛑 MT5 Trading Bot Shutting Down")
            
            # Stop trading engine
            if self.trading_engine:
                self.trading_engine.stop()
            
            # Shutdown MT5 connection
            try:
                mt5.shutdown()
                logger("✅ MT5 connection closed")
            except:
                pass
            
            # Close GUI
            if self.root:
                try:
                    self.root.quit()
                    self.root.destroy()
                except:
                    pass
            
            logger("✅ Bot shutdown completed")
            
        except Exception as e:
            logger(f"⚠️ Error during shutdown: {str(e)}")

def main():
    """Main entry point"""
    try:
        # Check Python version
        if sys.version_info < (3, 7):
            print("❌ Python 3.7+ required")
            sys.exit(1)
        
        # Check if running on Windows for MT5 compatibility
        import platform
        if platform.system() != "Windows":
            logger("⚠️ Warning: MT5 officially supports Windows only")
        
        # Create and run the bot
        bot = MT5TradingBot()
        bot.run()
        
    except Exception as e:
        logger(f"❌ Fatal error: {str(e)}")
        import traceback
        logger(f"Full traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
