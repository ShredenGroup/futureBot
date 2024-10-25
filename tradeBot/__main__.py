from .config import Config
from .account import Account     
from .db import DB
import pandas as pd
import numpy as np
import os 
def main():
    config=Config()
    account=Account(config)
    db=DB()
    db.export_to_csv(db.add_day_changes(db.read_csv(config.BTC_PATH)),config.BTC_PATH)

main()