from .config import Config
from .account import Account     
from .db import DB
import pandas as pd
import numpy as np
import os 
from .strategy import Strategy
def main():
    config=Config()
    account=Account(config)
    db=DB()
    WLD_df=DB.read_csv(config.WLD_PATH)
    BTC_df=DB.read_csv(config.BTC_PATH)

    result,details=Strategy.BTC_WLD(WLD_df,BTC_df)
    for detail in details:
     print(f"\n信号日期: {detail['signal_date']}")
     print(f"三天连续优势期结束日期: {detail['three_day_streak_end_date']}")
     print(f"间隔天数: {detail['days_since_streak']}")
     print(f"WLD最近两天表现: {detail['wld_last_two_days']}")
     print(f"BTC最近两天表现: {detail['btc_last_two_days']}")
main()