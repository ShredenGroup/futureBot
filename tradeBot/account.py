from binance.um_futures import UMFutures
from .config import Config
config=Config()
class Account:
    def __init__(self,config:Config):
        self.client=UMFutures(key=config.HP_API_KEY,private_key=config.HP_SECRET_KEY)
    def open_order(self,config:Config):
        params = {
            'symbol': 'WLDUSDT',
            'side': 'SELL',
            'type': 'MARKET',
            'quantity': config.WLD_AMOUNT,
        }
        self.client.new_order(**params)
        print("Successfully open order with amount of", config.WLD_AMOUNT)
    def get_all_orders(self,config:Config):  
        all_orders=self.client.get_position_risk()
        orders=[]
        for item in all_orders:
            if float(item.get('positionAmt'))!=0:
                   orders.append(item)
        print(orders)
    def get_orders(self,keypair):
        orders=self.client.get_position_risk(symbol=keypair)
        print(orders)
       

    def close_position(self,keypair):
        position_info=self.client.get_position_risk(symbol=keypair)[0]
        
        position_amount=float(position_info.get('positionAmt'))
        position_abs_amount=abs(position_amount)
        side=''
        if position_amount<0:
            side='BUY'
        else:
            side='SELL'
        close_param={
            'symbol':keypair,
            'type':'market',
            'reduceOnly':'true',
            'quantity': position_abs_amount,
            'side':side
        } 
        response=self.client.new_order(**close_param)
        print(response)

    def get_balance(self):
        balance=self.client.balance()
        account_balance={}
        for item in balance:
            if float(item.get('balance'))!=0:
                account_balance[item.get('asset')]=item.get('balance')
        if account_balance=={}:
            print("You dont have any token balance greater than zero")
        else:
         print("Your balance:",account_balance)

class mockAccount:
    def __init__(self,balance:float):
        self.balance=balance

     

