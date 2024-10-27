import configparser
import os
import sys
CFG_FL='./user.cfg'
USER_CFG_SECTION="sub_account"

class Config:
    def __init__(self):
        print("welcome to config module")
        config=configparser.ConfigParser()
        current_path=os.path.abspath(os.getcwd())
        if os.path.exists("./user.cfg"):
            
            config.read(CFG_FL)
            if USER_CFG_SECTION in config:
                print("Successfully fetch data")
            else:
                print("Section module is wrong or null")
                sys.exit(1)
                 
        
        else:
            print("No config file detected, exit")
            print(os.path.abspath("."))
            sys.exit(1)
        with open (os.path.join(current_path,"Private_key")) as f:
          private_key=f.read()
        current_dictionary=os.path.abspath(os.getcwd()) 
        data_dictionary=os.path.join(current_dictionary,"tradeBot","format_data")
        self.WLD_PATH=os.path.join(data_dictionary,"WLD_format.csv")
        self.BTC_PATH=os.path.join(data_dictionary,"BTC_format.csv")
        self.ARB_PATH=os.path.join(data_dictionary,"ARB_format.csv")
        self.API_KEY=config.get(USER_CFG_SECTION,"API_KEY")
        self.SECRET_KEY=private_key
        self.WLD_AMOUNT=3
        self.TRADING_PAIR=["WLDUSDT"]

        


