import configparser
import os
import sys
CFG_FL='./futureBot/user.cfg'
USER_CFG_SECTION="sub_account"

class Config:
    def __init__(self):
        print("welcome to config module")
        config=configparser.ConfigParser()
        if os.path.exists("./futureBot/user.cfg"):
            
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
        with open ("/home/litterpigger/.keypair/Private_key") as f:
          private_key=f.read()
        self.HP_SECRET_KEY=private_key

        self.PC_API_KEY=config.get(USER_CFG_SECTION,"PC_API_KEY")
        self.PC_SECRET_KEY=config.get(USER_CFG_SECTION,"PC_SECRET_KEY")
        self.HP_API_KEY=config.get(USER_CFG_SECTION,"HP_API_KEY")
        self.WLD_AMOUNT=3
        self.TRADING_PAIR=["WLDUSDT"]

        


