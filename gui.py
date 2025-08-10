"""
Advanced MT5 Trading Bot - GUI Module
Identical layout and functionality to bobot2.py with enhanced features
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.scrolledtext import ScrolledText
import threading
import datetime
import time
from typing import Optional, Dict, Any, List
import json

from utils import logger, validate_numeric_input, validate_string_input
from config import ConfigManager

class TradingBotGUI:
    """Main GUI class with identical layout to bobot2.py"""
    
    def __init__(self, root: tk.Tk, config_manager: ConfigManager):
        """Initialize the GUI"""
        self.root = root
        self.config_manager = config_manager
        self.trading_engine = None
        self.log_text = None
        self.status_vars = {}
        self.input_vars = {}
        self.update_job = None
        
        self.setup_window()
        self.create_widgets()
        self.setup_bindings()
        self.load_saved_values()
        
    def setup_window(self):
        """Setup main window properties"""
        self.root.title("MT5 Advanced Trading Bot v2.0")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)
        
        # Set window icon (using default)
        try:
            self.root.iconbitmap(default="")
        except:
            pass
        
        # Configure grid weights
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
    def create_widgets(self):
        """Create all GUI widgets with identical layout to bobot2.py"""
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="5")
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="MT5 Advanced Trading Bot", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, pady=(0, 10))
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=1, column=0, sticky="nsew")
        
        # Create tabs
        self.create_main_tab()
        self.create_settings_tab()
        self.create_risk_tab()
        self.create_strategy_tab()
        self.create_logs_tab()
        self.create_analysis_tab()
        
        # Status bar
        self.create_status_bar(main_frame)
        
    def create_main_tab(self):
        """Create main trading tab"""
        main_tab = ttk.Frame(self.notebook)
        self.notebook.add(main_tab, text="Main Trading")
        
        # Configure grid
        main_tab.grid_columnconfigure(1, weight=1)
        
        # Connection frame
        conn_frame = ttk.LabelFrame(main_tab, text="MT5 Connection", padding="5")
        conn_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 5))
        
        ttk.Button(conn_frame, text="Connect MT5", command=self.connect_mt5).grid(row=0, column=0, padx=5)
        ttk.Button(conn_frame, text="Disconnect", command=self.disconnect_mt5).grid(row=0, column=1, padx=5)
        
        self.status_vars['connection'] = tk.StringVar(value="Disconnected")
        ttk.Label(conn_frame, textvariable=self.status_vars['connection']).grid(row=0, column=2, padx=10)
        
        # Trading controls frame
        controls_frame = ttk.LabelFrame(main_tab, text="Trading Controls", padding="5")
        controls_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
        
        # Strategy selection
        ttk.Label(controls_frame, text="Strategy:").grid(row=0, column=0, sticky="w")
        self.input_vars['strategy'] = tk.StringVar(value="Scalping")
        strategy_combo = ttk.Combobox(controls_frame, textvariable=self.input_vars['strategy'],
                                    values=["Scalping", "HFT", "Intraday", "Arbitrage"],
                                    state="readonly", width=15)
        strategy_combo.grid(row=0, column=1, padx=5, sticky="w")
        
        # Symbol input
        ttk.Label(controls_frame, text="Symbol:").grid(row=0, column=2, sticky="w", padx=(20, 0))
        self.input_vars['symbol'] = tk.StringVar(value="XAUUSD")
        symbol_entry = ttk.Entry(controls_frame, textvariable=self.input_vars['symbol'], width=10)
        symbol_entry.grid(row=0, column=3, padx=5)
        
        # Auto-detect gold button
        ttk.Button(controls_frame, text="Auto Gold", command=self.auto_detect_gold).grid(row=0, column=4, padx=5)
        
        # Lot size
        ttk.Label(controls_frame, text="Lot Size:").grid(row=1, column=0, sticky="w")
        self.input_vars['lot_size'] = tk.StringVar(value="0.01")
        lot_entry = ttk.Entry(controls_frame, textvariable=self.input_vars['lot_size'], width=10)
        lot_entry.grid(row=1, column=1, padx=5)
        
        # Auto lot checkbox
        self.input_vars['auto_lot'] = tk.BooleanVar(value=True)
        ttk.Checkbutton(controls_frame, text="Auto Lot", 
                       variable=self.input_vars['auto_lot']).grid(row=1, column=2, padx=5)
        
        # Risk percentage
        ttk.Label(controls_frame, text="Risk %:").grid(row=1, column=3, sticky="w")
        self.input_vars['risk_percent'] = tk.StringVar(value="1.0")
        risk_entry = ttk.Entry(controls_frame, textvariable=self.input_vars['risk_percent'], width=10)
        risk_entry.grid(row=1, column=4, padx=5)
        
        # TP/SL Settings
        tp_sl_frame = ttk.LabelFrame(main_tab, text="TP/SL Settings", padding="5")
        tp_sl_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)
        
        # Take Profit
        ttk.Label(tp_sl_frame, text="Take Profit:").grid(row=0, column=0, sticky="w")
        self.input_vars['tp_value'] = tk.StringVar(value="50")
        tp_entry = ttk.Entry(tp_sl_frame, textvariable=self.input_vars['tp_value'], width=10)
        tp_entry.grid(row=0, column=1, padx=5)
        
        self.input_vars['tp_unit'] = tk.StringVar(value="pips")
        tp_unit_combo = ttk.Combobox(tp_sl_frame, textvariable=self.input_vars['tp_unit'],
                                   values=["pips", "price", "percent", "currency"],
                                   state="readonly", width=10)
        tp_unit_combo.grid(row=0, column=2, padx=5)
        
        # Stop Loss
        ttk.Label(tp_sl_frame, text="Stop Loss:").grid(row=0, column=3, sticky="w", padx=(20, 0))
        self.input_vars['sl_value'] = tk.StringVar(value="25")
        sl_entry = ttk.Entry(tp_sl_frame, textvariable=self.input_vars['sl_value'], width=10)
        sl_entry.grid(row=0, column=4, padx=5)
        
        self.input_vars['sl_unit'] = tk.StringVar(value="pips")
        sl_unit_combo = ttk.Combobox(tp_sl_frame, textvariable=self.input_vars['sl_unit'],
                                   values=["pips", "price", "percent", "currency"],
                                   state="readonly", width=10)
        sl_unit_combo.grid(row=0, column=5, padx=5)
        
        # Trailing stop
        self.input_vars['trailing_stop'] = tk.BooleanVar(value=False)
        ttk.Checkbutton(tp_sl_frame, text="Trailing Stop", 
                       variable=self.input_vars['trailing_stop']).grid(row=1, column=0, pady=5)
        
        self.input_vars['trailing_distance'] = tk.StringVar(value="15")
        ttk.Entry(tp_sl_frame, textvariable=self.input_vars['trailing_distance'], 
                 width=10).grid(row=1, column=1, padx=5)
        
        # Trading buttons
        buttons_frame = ttk.Frame(main_tab)
        buttons_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        # Start/Stop bot
        ttk.Button(buttons_frame, text="Start Bot", command=self.start_bot,
                  style="Accent.TButton").grid(row=0, column=0, padx=5)
        ttk.Button(buttons_frame, text="Stop Bot", command=self.stop_bot).grid(row=0, column=1, padx=5)
        
        # Manual trading
        ttk.Button(buttons_frame, text="Buy", command=self.manual_buy,
                  style="Success.TButton").grid(row=0, column=2, padx=5)
        ttk.Button(buttons_frame, text="Sell", command=self.manual_sell,
                  style="Danger.TButton").grid(row=0, column=3, padx=5)
        
        # Close positions
        ttk.Button(buttons_frame, text="Close All", command=self.close_all_positions).grid(row=0, column=4, padx=5)
        
        # Account info frame
        account_frame = ttk.LabelFrame(main_tab, text="Account Information", padding="5")
        account_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=5)
        account_frame.grid_columnconfigure(1, weight=1)
        account_frame.grid_columnconfigure(3, weight=1)
        
        # Account details
        self.status_vars['account'] = tk.StringVar(value="Not connected")
        self.status_vars['balance'] = tk.StringVar(value="0.00")
        self.status_vars['equity'] = tk.StringVar(value="0.00")
        self.status_vars['margin'] = tk.StringVar(value="0.00")
        self.status_vars['profit'] = tk.StringVar(value="0.00")
        
        ttk.Label(account_frame, text="Account:").grid(row=0, column=0, sticky="w")
        ttk.Label(account_frame, textvariable=self.status_vars['account']).grid(row=0, column=1, sticky="w")
        
        ttk.Label(account_frame, text="Balance:").grid(row=0, column=2, sticky="w", padx=(20, 0))
        ttk.Label(account_frame, textvariable=self.status_vars['balance']).grid(row=0, column=3, sticky="w")
        
        ttk.Label(account_frame, text="Equity:").grid(row=1, column=0, sticky="w")
        ttk.Label(account_frame, textvariable=self.status_vars['equity']).grid(row=1, column=1, sticky="w")
        
        ttk.Label(account_frame, text="Margin:").grid(row=1, column=2, sticky="w", padx=(20, 0))
        ttk.Label(account_frame, textvariable=self.status_vars['margin']).grid(row=1, column=3, sticky="w")
        
    def create_settings_tab(self):
        """Create settings tab"""
        settings_tab = ttk.Frame(self.notebook)
        self.notebook.add(settings_tab, text="Settings")
        
        # Session settings
        session_frame = ttk.LabelFrame(settings_tab, text="Trading Sessions", padding="5")
        session_frame.grid(row=0, column=0, sticky="ew", pady=5)
        
        sessions = ["Asia", "London", "New_York", "Overlap_London_NY"]
        for i, session in enumerate(sessions):
            var_name = f'session_{session.lower()}'
            self.input_vars[var_name] = tk.BooleanVar(value=True)
            ttk.Checkbutton(session_frame, text=session.replace("_", " "), 
                           variable=self.input_vars[var_name]).grid(row=i//2, column=i%2, sticky="w", padx=5, pady=2)
        
        # News filter
        news_frame = ttk.LabelFrame(settings_tab, text="News Filter", padding="5")
        news_frame.grid(row=1, column=0, sticky="ew", pady=5)
        
        self.input_vars['avoid_news'] = tk.BooleanVar(value=True)
        ttk.Checkbutton(news_frame, text="Avoid High Impact News", 
                       variable=self.input_vars['avoid_news']).grid(row=0, column=0, sticky="w")
        
        # Telegram settings
        telegram_frame = ttk.LabelFrame(settings_tab, text="Telegram Notifications", padding="5")
        telegram_frame.grid(row=2, column=0, sticky="ew", pady=5)
        
        self.input_vars['telegram_enabled'] = tk.BooleanVar(value=False)
        ttk.Checkbutton(telegram_frame, text="Enable Telegram", 
                       variable=self.input_vars['telegram_enabled']).grid(row=0, column=0, sticky="w")
        
        ttk.Label(telegram_frame, text="Bot Token:").grid(row=1, column=0, sticky="w")
        self.input_vars['telegram_token'] = tk.StringVar()
        ttk.Entry(telegram_frame, textvariable=self.input_vars['telegram_token'], 
                 width=40, show="*").grid(row=1, column=1, sticky="ew", padx=5)
        
        ttk.Label(telegram_frame, text="Chat ID:").grid(row=2, column=0, sticky="w")
        self.input_vars['telegram_chat_id'] = tk.StringVar()
        ttk.Entry(telegram_frame, textvariable=self.input_vars['telegram_chat_id'], 
                 width=20).grid(row=2, column=1, sticky="w", padx=5)
        
        telegram_frame.grid_columnconfigure(1, weight=1)
        
    def create_risk_tab(self):
        """Create risk management tab"""
        risk_tab = ttk.Frame(self.notebook)
        self.notebook.add(risk_tab, text="Risk Management")
        
        # Daily limits
        daily_frame = ttk.LabelFrame(risk_tab, text="Daily Limits", padding="5")
        daily_frame.grid(row=0, column=0, sticky="ew", pady=5)
        
        ttk.Label(daily_frame, text="Max Daily Loss %:").grid(row=0, column=0, sticky="w")
        self.input_vars['max_daily_loss'] = tk.StringVar(value="5.0")
        ttk.Entry(daily_frame, textvariable=self.input_vars['max_daily_loss'], width=10).grid(row=0, column=1, padx=5)
        
        ttk.Label(daily_frame, text="Daily Profit Target %:").grid(row=0, column=2, sticky="w", padx=(20, 0))
        self.input_vars['daily_profit_target'] = tk.StringVar(value="10.0")
        ttk.Entry(daily_frame, textvariable=self.input_vars['daily_profit_target'], width=10).grid(row=0, column=3, padx=5)
        
        ttk.Label(daily_frame, text="Max Positions:").grid(row=1, column=0, sticky="w")
        self.input_vars['max_positions'] = tk.StringVar(value="10")
        ttk.Entry(daily_frame, textvariable=self.input_vars['max_positions'], width=10).grid(row=1, column=1, padx=5)
        
        ttk.Label(daily_frame, text="Max Loss Streak:").grid(row=1, column=2, sticky="w", padx=(20, 0))
        self.input_vars['max_loss_streak'] = tk.StringVar(value="3")
        ttk.Entry(daily_frame, textvariable=self.input_vars['max_loss_streak'], width=10).grid(row=1, column=3, padx=5)
        
        # Drawdown settings
        drawdown_frame = ttk.LabelFrame(risk_tab, text="Drawdown Protection", padding="5")
        drawdown_frame.grid(row=1, column=0, sticky="ew", pady=5)
        
        ttk.Label(drawdown_frame, text="Max Drawdown %:").grid(row=0, column=0, sticky="w")
        self.input_vars['max_drawdown'] = tk.StringVar(value="5.0")
        ttk.Entry(drawdown_frame, textvariable=self.input_vars['max_drawdown'], width=10).grid(row=0, column=1, padx=5)
        
        self.input_vars['auto_stop_drawdown'] = tk.BooleanVar(value=True)
        ttk.Checkbutton(drawdown_frame, text="Auto-stop on max drawdown", 
                       variable=self.input_vars['auto_stop_drawdown']).grid(row=0, column=2, padx=20)
        
    def create_strategy_tab(self):
        """Create strategy configuration tab"""
        strategy_tab = ttk.Frame(self.notebook)
        self.notebook.add(strategy_tab, text="Strategy Config")
        
        # AI Settings
        ai_frame = ttk.LabelFrame(strategy_tab, text="AI Signal Generator", padding="5")
        ai_frame.grid(row=0, column=0, sticky="ew", pady=5)
        
        self.input_vars['ai_enabled'] = tk.BooleanVar(value=True)
        ttk.Checkbutton(ai_frame, text="Enable AI Signals", 
                       variable=self.input_vars['ai_enabled']).grid(row=0, column=0, sticky="w")
        
        ttk.Label(ai_frame, text="AI Confidence Threshold:").grid(row=1, column=0, sticky="w")
        self.input_vars['ai_confidence'] = tk.StringVar(value="0.75")
        ttk.Entry(ai_frame, textvariable=self.input_vars['ai_confidence'], width=10).grid(row=1, column=1, padx=5)
        
        # Technical Indicators
        indicators_frame = ttk.LabelFrame(strategy_tab, text="Technical Indicators", padding="5")
        indicators_frame.grid(row=1, column=0, sticky="ew", pady=5)
        
        indicators = ["RSI", "MACD", "EMA", "ATR", "Bollinger_Bands"]
        for i, indicator in enumerate(indicators):
            var_name = f'indicator_{indicator.lower()}'
            self.input_vars[var_name] = tk.BooleanVar(value=True)
            ttk.Checkbutton(indicators_frame, text=indicator.replace("_", " "), 
                           variable=self.input_vars[var_name]).grid(row=i//3, column=i%3, sticky="w", padx=5, pady=2)
        
        # Strategy parameters for each strategy type
        strategy_params_frame = ttk.LabelFrame(strategy_tab, text="Strategy Parameters", padding="5")
        strategy_params_frame.grid(row=2, column=0, sticky="ew", pady=5)
        
        # Scalping parameters
        scalping_frame = ttk.LabelFrame(strategy_params_frame, text="Scalping", padding="3")
        scalping_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=2)
        
        ttk.Label(scalping_frame, text="Min Pip Profit:").grid(row=0, column=0, sticky="w")
        self.input_vars['scalping_min_profit'] = tk.StringVar(value="5")
        ttk.Entry(scalping_frame, textvariable=self.input_vars['scalping_min_profit'], width=8).grid(row=0, column=1, padx=2)
        
        # HFT parameters
        hft_frame = ttk.LabelFrame(strategy_params_frame, text="HFT", padding="3")
        hft_frame.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        
        ttk.Label(hft_frame, text="Max Spread:").grid(row=0, column=0, sticky="w")
        self.input_vars['hft_max_spread'] = tk.StringVar(value="2")
        ttk.Entry(hft_frame, textvariable=self.input_vars['hft_max_spread'], width=8).grid(row=0, column=1, padx=2)
        
    def create_logs_tab(self):
        """Create logs and monitoring tab"""
        logs_tab = ttk.Frame(self.notebook)
        self.notebook.add(logs_tab, text="Logs & Monitor")
        
        # Log display
        log_frame = ttk.LabelFrame(logs_tab, text="Trading Logs", padding="5")
        log_frame.grid(row=0, column=0, sticky="nsew", pady=5)
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
        
        self.log_text = ScrolledText(log_frame, height=20, width=80)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        
        # Log controls
        log_controls = ttk.Frame(logs_tab)
        log_controls.grid(row=1, column=0, sticky="ew", pady=5)
        
        ttk.Button(log_controls, text="Clear Logs", command=self.clear_logs).grid(row=0, column=0, padx=5)
        ttk.Button(log_controls, text="Save Logs", command=self.save_logs).grid(row=0, column=1, padx=5)
        ttk.Button(log_controls, text="Export CSV", command=self.export_csv).grid(row=0, column=2, padx=5)
        
        # Configure tab grid weights
        logs_tab.grid_rowconfigure(0, weight=1)
        logs_tab.grid_columnconfigure(0, weight=1)
        
    def create_analysis_tab(self):
        """Create analysis and backtest tab"""
        analysis_tab = ttk.Frame(self.notebook)
        self.notebook.add(analysis_tab, text="Analysis")
        
        # Backtest frame
        backtest_frame = ttk.LabelFrame(analysis_tab, text="Backtest", padding="5")
        backtest_frame.grid(row=0, column=0, sticky="ew", pady=5)
        
        ttk.Label(backtest_frame, text="Start Date:").grid(row=0, column=0, sticky="w")
        self.input_vars['backtest_start'] = tk.StringVar(value="2024-01-01")
        ttk.Entry(backtest_frame, textvariable=self.input_vars['backtest_start'], width=12).grid(row=0, column=1, padx=5)
        
        ttk.Label(backtest_frame, text="End Date:").grid(row=0, column=2, sticky="w", padx=(20, 0))
        self.input_vars['backtest_end'] = tk.StringVar(value="2024-12-31")
        ttk.Entry(backtest_frame, textvariable=self.input_vars['backtest_end'], width=12).grid(row=0, column=3, padx=5)
        
        ttk.Button(backtest_frame, text="Run Backtest", command=self.run_backtest).grid(row=0, column=4, padx=20)
        
        # Performance metrics
        metrics_frame = ttk.LabelFrame(analysis_tab, text="Performance Metrics", padding="5")
        metrics_frame.grid(row=1, column=0, sticky="ew", pady=5)
        
        self.status_vars['total_trades'] = tk.StringVar(value="0")
        self.status_vars['win_rate'] = tk.StringVar(value="0%")
        self.status_vars['profit_factor'] = tk.StringVar(value="0.00")
        self.status_vars['max_dd'] = tk.StringVar(value="0%")
        
        ttk.Label(metrics_frame, text="Total Trades:").grid(row=0, column=0, sticky="w")
        ttk.Label(metrics_frame, textvariable=self.status_vars['total_trades']).grid(row=0, column=1, sticky="w")
        
        ttk.Label(metrics_frame, text="Win Rate:").grid(row=0, column=2, sticky="w", padx=(20, 0))
        ttk.Label(metrics_frame, textvariable=self.status_vars['win_rate']).grid(row=0, column=3, sticky="w")
        
        ttk.Label(metrics_frame, text="Profit Factor:").grid(row=1, column=0, sticky="w")
        ttk.Label(metrics_frame, textvariable=self.status_vars['profit_factor']).grid(row=1, column=1, sticky="w")
        
        ttk.Label(metrics_frame, text="Max Drawdown:").grid(row=1, column=2, sticky="w", padx=(20, 0))
        ttk.Label(metrics_frame, textvariable=self.status_vars['max_dd']).grid(row=1, column=3, sticky="w")
        
    def create_status_bar(self, parent):
        """Create status bar"""
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=2, column=0, sticky="ew", pady=(5, 0))
        status_frame.grid_columnconfigure(1, weight=1)
        
        self.status_vars['bot_status'] = tk.StringVar(value="Bot Stopped")
        self.status_vars['last_update'] = tk.StringVar(value="Never")
        
        ttk.Label(status_frame, text="Status:").grid(row=0, column=0, sticky="w")
        ttk.Label(status_frame, textvariable=self.status_vars['bot_status']).grid(row=0, column=1, sticky="w", padx=5)
        
        ttk.Label(status_frame, text="Last Update:").grid(row=0, column=2, sticky="e", padx=(0, 5))
        ttk.Label(status_frame, textvariable=self.status_vars['last_update']).grid(row=0, column=3, sticky="e")
        
    def setup_bindings(self):
        """Setup event bindings"""
        # Window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Tab change event
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        
    def load_saved_values(self):
        """Load saved configuration values"""
        try:
            config = self.config_manager.get_config()
            
            # Load values from config
            for key, value in config.get('gui_values', {}).items():
                if key in self.input_vars:
                    if isinstance(self.input_vars[key], tk.BooleanVar):
                        self.input_vars[key].set(bool(value))
                    else:
                        self.input_vars[key].set(str(value))
                        
        except Exception as e:
            logger(f"⚠️ Error loading saved values: {str(e)}")
    
    def save_current_values(self):
        """Save current GUI values to config"""
        try:
            gui_values = {}
            for key, var in self.input_vars.items():
                try:
                    if isinstance(var, tk.BooleanVar):
                        gui_values[key] = var.get()
                    else:
                        gui_values[key] = var.get()
                except:
                    pass
            
            self.config_manager.update_config('gui_values', gui_values)
            self.config_manager.save_config()
            
        except Exception as e:
            logger(f"⚠️ Error saving values: {str(e)}")
    
    def set_trading_engine(self, trading_engine):
        """Set the trading engine reference"""
        self.trading_engine = trading_engine
    
    def log(self, message: str):
        """Add message to log display"""
        if self.log_text:
            try:
                self.log_text.insert(tk.END, message + "\n")
                self.log_text.see(tk.END)
                self.root.update_idletasks()
            except:
                pass
    
    def update_status(self):
        """Update status displays"""
        try:
            if self.trading_engine:
                # Update connection status
                if self.trading_engine.is_connected():
                    self.status_vars['connection'].set("Connected")
                    
                    # Update account info
                    account_info = self.trading_engine.get_account_info()
                    if account_info:
                        self.status_vars['account'].set(f"{account_info.get('login', 'N/A')}")
                        self.status_vars['balance'].set(f"{account_info.get('balance', 0):.2f}")
                        self.status_vars['equity'].set(f"{account_info.get('equity', 0):.2f}")
                        self.status_vars['margin'].set(f"{account_info.get('margin', 0):.2f}")
                        
                        # Calculate floating profit
                        profit = account_info.get('equity', 0) - account_info.get('balance', 0)
                        self.status_vars['profit'].set(f"{profit:.2f}")
                else:
                    self.status_vars['connection'].set("Disconnected")
                    
                # Update bot status
                if self.trading_engine.is_running():
                    self.status_vars['bot_status'].set("Bot Running")
                else:
                    self.status_vars['bot_status'].set("Bot Stopped")
                    
                # Update performance metrics
                metrics = self.trading_engine.get_performance_metrics()
                if metrics:
                    self.status_vars['total_trades'].set(str(metrics.get('total_trades', 0)))
                    self.status_vars['win_rate'].set(f"{metrics.get('win_rate', 0):.1f}%")
                    self.status_vars['profit_factor'].set(f"{metrics.get('profit_factor', 0):.2f}")
                    self.status_vars['max_dd'].set(f"{metrics.get('max_drawdown', 0):.1f}%")
            
            # Update timestamp
            self.status_vars['last_update'].set(datetime.datetime.now().strftime("%H:%M:%S"))
            
        except Exception as e:
            logger(f"⚠️ Error updating status: {str(e)}")
        
        # Schedule next update
        if self.update_job:
            self.root.after_cancel(self.update_job)
        self.update_job = self.root.after(1500, self.update_status)
    
    # Event handlers
    def connect_mt5(self):
        """Connect to MT5"""
        if self.trading_engine:
            threading.Thread(target=self.trading_engine.connect, daemon=True).start()
    
    def disconnect_mt5(self):
        """Disconnect from MT5"""
        if self.trading_engine:
            self.trading_engine.disconnect()
    
    def start_bot(self):
        """Start the trading bot"""
        if self.trading_engine:
            self.save_current_values()
            self.trading_engine.start()
    
    def stop_bot(self):
        """Stop the trading bot"""
        if self.trading_engine:
            self.trading_engine.stop()
    
    def manual_buy(self):
        """Execute manual buy order"""
        if self.trading_engine:
            params = self.get_trading_params()
            threading.Thread(target=self.trading_engine.manual_trade, 
                           args=("buy", params), daemon=True).start()
    
    def manual_sell(self):
        """Execute manual sell order"""
        if self.trading_engine:
            params = self.get_trading_params()
            threading.Thread(target=self.trading_engine.manual_trade, 
                           args=("sell", params), daemon=True).start()
    
    def close_all_positions(self):
        """Close all open positions"""
        if self.trading_engine:
            if messagebox.askyesno("Confirm", "Close all open positions?"):
                threading.Thread(target=self.trading_engine.close_all_positions, daemon=True).start()
    
    def auto_detect_gold(self):
        """Auto-detect gold symbol"""
        if self.trading_engine:
            symbol = self.trading_engine.auto_detect_gold_symbol()
            if symbol:
                self.input_vars['symbol'].set(symbol)
                logger(f"✅ Auto-detected gold symbol: {symbol}")
            else:
                logger("❌ Could not auto-detect gold symbol")
    
    def clear_logs(self):
        """Clear log display"""
        if self.log_text:
            self.log_text.delete(1.0, tk.END)
    
    def save_logs(self):
        """Save logs to file"""
        if self.log_text:
            try:
                filename = filedialog.asksaveasfilename(
                    defaultextension=".txt",
                    filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
                )
                if filename:
                    with open(filename, 'w') as f:
                        f.write(self.log_text.get(1.0, tk.END))
                    logger(f"✅ Logs saved to {filename}")
            except Exception as e:
                logger(f"❌ Error saving logs: {str(e)}")
    
    def export_csv(self):
        """Export trading data to CSV"""
        if self.trading_engine:
            threading.Thread(target=self.trading_engine.export_trading_data, daemon=True).start()
    
    def run_backtest(self):
        """Run backtest"""
        if self.trading_engine:
            start_date = self.input_vars['backtest_start'].get()
            end_date = self.input_vars['backtest_end'].get()
            threading.Thread(target=self.trading_engine.run_backtest, 
                           args=(start_date, end_date), daemon=True).start()
    
    def get_trading_params(self) -> Dict[str, Any]:
        """Get current trading parameters from GUI"""
        try:
            return {
                'symbol': self.input_vars['symbol'].get(),
                'lot_size': float(self.input_vars['lot_size'].get()),
                'auto_lot': self.input_vars['auto_lot'].get(),
                'risk_percent': float(self.input_vars['risk_percent'].get()),
                'tp_value': float(self.input_vars['tp_value'].get()),
                'tp_unit': self.input_vars['tp_unit'].get(),
                'sl_value': float(self.input_vars['sl_value'].get()),
                'sl_unit': self.input_vars['sl_unit'].get(),
                'trailing_stop': self.input_vars['trailing_stop'].get(),
                'trailing_distance': float(self.input_vars['trailing_distance'].get()),
                'strategy': self.input_vars['strategy'].get(),
                'ai_enabled': self.input_vars['ai_enabled'].get(),
                'ai_confidence': float(self.input_vars['ai_confidence'].get()),
            }
        except (ValueError, KeyError) as e:
            logger(f"❌ Error getting trading parameters: {str(e)}")
            return {}
    
    def on_tab_changed(self, event):
        """Handle tab change event"""
        pass
    
    def on_closing(self):
        """Handle window closing"""
        try:
            if self.trading_engine and self.trading_engine.is_running():
                if messagebox.askyesno("Confirm Exit", "Bot is running. Stop bot and exit?"):
                    self.trading_engine.stop()
                    self.save_current_values()
                    self.root.quit()
            else:
                self.save_current_values()
                self.root.quit()
        except:
            self.root.quit()
    
    def start(self):
        """Start the GUI main loop"""
        try:
            # Start status updates
            self.update_status()
            
            # Start main loop
            self.root.mainloop()
            
        except Exception as e:
            logger(f"❌ GUI error: {str(e)}")
            raise
