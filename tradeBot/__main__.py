from .config import Config
from .account import Account,MockAccount     
from .db import DB
import pandas as pd
import numpy as np
import os 
from .strategy import Strategy
from .backtest import BackTest
def main():
    config=Config()
    account=Account(config)
    db=DB()
    WLD_df=DB.read_csv(config.WLD_PATH)
    BTC_df=DB.read_csv(config.BTC_PATH)
    merged_data, signal_details = Strategy.BTC_WLD(WLD_df, BTC_df)
    account = MockAccount(initial_balance=1000.0, leverage=20.0)
    backtest = BackTest(account)
    print(merged_data)

    # 运行回测
    backtest.run(WLD_df, merged_data)

    # 生成报告
    report = backtest.generate_report()
    print("\n=== 回测报告 ===")
    for key, value in report.items():
        if key != "Daily Returns":
            print(f"{key}: {value}")
   


  
main()