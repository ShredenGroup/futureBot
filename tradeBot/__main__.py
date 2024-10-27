from .config import Config
from .account import Account,MockAccount     
from .db import DB
import pandas as pd
import numpy as np
import os 
from .strategy import Strategy
from .backtest import BackTest,BacktestVisualizer
def main():
    config=Config()
    account=Account(config)
    db=DB()
    WLD_df=DB.read_csv(config.WLD_PATH)
    BTC_df=DB.read_csv(config.BTC_PATH)
    ARB_df=DB.read_csv(config.ARB_PATH)
    merged_data, signal_details = Strategy.BTC_WLD_hour(WLD_df, BTC_df)

    account = MockAccount(initial_balance=1000.0, leverage=20.0)
    backtest = BackTest(account)
    print(merged_data)

    # 运行回测
    backtest.run_hour(WLD_df, merged_data)

    # 生成报告
    report = backtest.generate_report_hour()
    print("\n=== 回测报告 ===")
    for key, value in report.items():
        if key != "Daily Returns":
            print(f"{key}: {value}")
    visualizer=BacktestVisualizer(account)
    visualizer.generate_visual_report()


  
main()