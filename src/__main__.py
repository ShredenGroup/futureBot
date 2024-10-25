from .config import Config
from .account import Account     
from .db import DB
import pandas as pd
import numpy as np
import os 
def main():
    config=Config()
    db=DB()
    combined_db=db.db_init()
    print(combined_db.head())
    db.export_to_csv(db.add_MACD(db.db_init()),'/home/litterpigger/myprojects/futureBot/format_data/BTC_format.csv')
main()