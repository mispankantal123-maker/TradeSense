
#!/usr/bin/env python3
"""
Quick Setup for MT5 Trading Bot with Telegram
One-click setup for getting started quickly
"""

import os
import sys
import json

def quick_setup():
    """Quick setup for the trading bot"""
    
    print("🚀 MT5 Trading Bot - Quick Setup")
    print("=" * 50)
    
    # Set environment variables
    print("1. Setting up Telegram credentials...")
    os.environ['TELEGRAM_TOKEN'] = "8365734234:AAH2uTaZPDD47Lnm3y_Tcr6aj3xGL-bVsgk"
    os.environ['TELEGRAM_CHAT_ID'] = "5061106648"
    print("   ✅ Telegram credentials set")
    
    # Update config.json
    print("2. Updating configuration...")
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        config['telegram_enabled'] = True
        config['telegram_token'] = os.environ['TELEGRAM_TOKEN']
        config['telegram_chat_id'] = os.environ['TELEGRAM_CHAT_ID']
        
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
        
        print("   ✅ Configuration updated")
    except Exception as e:
        print(f"   ⚠️ Config update warning: {str(e)}")
    
    # Test Telegram connection
    print("3. Testing Telegram connection...")
    try:
        from config import ConfigManager
        from telegram_bot import TelegramBot
        
        config_manager = ConfigManager()
        config_manager.load_config()
        
        telegram_bot = TelegramBot(config_manager)
        
        if telegram_bot.enabled:
            telegram_bot.send_message("✅ Quick Setup Complete! MT5 Trading Bot Ready")
            print("   ✅ Telegram test successful!")
        else:
            print("   ⚠️ Telegram test failed - check credentials")
    
    except Exception as e:
        print(f"   ⚠️ Telegram test error: {str(e)}")
    
    print("\n🎯 Setup Complete!")
    print("Run 'python main.py' to start the trading bot")
    print("Run 'python test_telegram_integration.py' for full Telegram testing")

if __name__ == "__main__":
    quick_setup()
    input("\nPress Enter to continue...")
