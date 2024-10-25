from .config import Config
from .account import Account     
from .db import DB
import pandas as pd
import numpy as np
import os 
def main():
    config=Config()
    account=Account(config)
    print(account.get_balance())
main()