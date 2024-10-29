from .config import Config
from .account import Account,MockAccount     
from .db import DB
import pandas as pd
import numpy as np
import os 
from .strategy import Strategy
from .backtest import BackTest,TimeFrame,BacktestVisualizer
def main():
    config=Config()
    account=Account(config)
    db=DB()
    DB.export_to_csv(DB.add_MACD(DB.read_csv(config.WLD_PATH)),"/home/litterpigger/myprojects/futureBot/tradeBot/format_data/WLD.csv")
    BTC_df=DB.read_csv(config.BTC_PATH)
    ARB_df=DB.read_csv(config.ARB_PATH)
    OP_df=DB.read_csv(config.OP_PATH)
    merged_data, signal_details = Strategy.BTC_WLD_hour(ARB_df, BTC_df)
    print(merged_data.head()) 
    """
    account = MockAccount(initial_balance=1000.0, leverage=20.0)
    backtest = BackTest(account,risk_free_rate=0.02)
    backtest.run(ARB_df,merged_data,TimeFrame.HOUR)
    print(backtest)
    # 运行回测
    BV=BacktestVisualizer(account,timeframe=TimeFrame.HOUR)
    BV.generate_report() 
    """
    
   
    

  
main()