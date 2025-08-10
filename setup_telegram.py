
#!/usr/bin/env python3
"""
Setup script for Telegram credentials
Run this once to set environment variables securely
"""

import os
import sys

def setup_telegram_credentials():
    """Set up Telegram credentials as environment variables"""
    
    # Default credentials from bobot2.py
    default_token = "8365734234:AAH2uTaZPDD47Lnm3y_Tcr6aj3xGL-bVsgk"
    default_chat_id = "5061106648"
    
    print("🔧 Setting up Telegram credentials...")
    
    # Set environment variables
    os.environ['TELEGRAM_TOKEN'] = default_token
    os.environ['TELEGRAM_CHAT_ID'] = default_chat_id
    
    print(f"✅ TELEGRAM_TOKEN set")
    print(f"✅ TELEGRAM_CHAT_ID set")
    
    # Verify credentials work
    try:
        from telegram_bot import TelegramBot
        from config import ConfigManager
        
        config_manager = ConfigManager()
        config_manager.load_config()
        
        # Enable Telegram in config
        config_manager.update_config('telegram_enabled', True)
        config_manager.save_config()
        
        # Test Telegram bot
        telegram_bot = TelegramBot(config_manager)
        
        if telegram_bot.enabled:
            print("✅ Telegram bot successfully initialized and tested!")
            telegram_bot.send_message("🚀 MT5 Trading Bot - Telegram Setup Complete!")
            return True
        else:
            print("❌ Telegram bot initialization failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Telegram: {str(e)}")
        return False

if __name__ == "__main__":
    if setup_telegram_credentials():
        print("\n🎉 Telegram setup completed successfully!")
        print("You can now run the main bot with Telegram notifications enabled.")
    else:
        print("\n⚠️ Telegram setup encountered issues. Check your credentials.")
    
    input("\nPress Enter to continue...")
