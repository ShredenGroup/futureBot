from binance.um_futures import UMFutures
from .config import Config
from typing import Dict,Set
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
import numpy as np
config=Config()
class Account:
    def __init__(self,config:Config):
        self.client=UMFutures(key=config.API_KEY,private_key=config.SECRET_KEY)
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

    def get_balance(self)->Dict[str,str]:
        balance=self.client.balance()
        account_balance={}
        for item in balance:
            if float(item.get('balance'))!=0:
                account_balance[item.get('asset')]=item.get('balance')
        if account_balance=={}:
            return {"asset":"No token in your balance"}
        else:
         return account_balance 

class OrderSide(Enum):
    LONG = "LONG"
    SHORT = "SHORT"

class OrderStatus(Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"

# Order数据类
@dataclass
class Order:
    symbol: str
    side: OrderSide
    size: float
    entry_price: float
    stop_loss: float
    take_profit: float
    open_time: datetime
    status: OrderStatus = OrderStatus.OPEN
    close_time: datetime = None
    close_price: float = None
    pnl: float = 0.0

class Position:
    def __init__(self, order: Order):
        self.symbol = order.symbol
        self.side = order.side
        self.size = order.size
        self.entry_price = order.entry_price
        self.stop_loss = order.stop_loss
        self.take_profit = order.take_profit
        self.unrealized_pnl = 0.0
        self.order = order

    def update_pnl(self, current_price: float):
        multiplier = -1 if self.side == OrderSide.SHORT else 1
        self.unrealized_pnl = (current_price - self.entry_price) * self.size * multiplier

class MockAccount:
    def __init__(self, initial_balance: float = 1000.0, leverage: float = 20.0):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.leverage = leverage
        self.fee_rate = 0.0002  # 万分之二手续费
        self.positions = {}  # symbol -> Position
        self.orders = []
        self.daily_balance = {}
        self.max_drawdown = 0.0
        self.equity_peak = initial_balance
        self.fixed_position_value=10

    def calculate_position_size(self, price: float) -> float:
     
        position_size = (self.fixed_position_value * self.leverage) / price
        return position_size

    def open_position(self, symbol: str, side: OrderSide, price: float, 
                     stop_loss: float, take_profit: float, timestamp: datetime) -> Order:
        # 计算仓位大小
        size = self.calculate_position_size(price)
        
        # 计算手续费
        fee = price * size * self.fee_rate
        self.balance -= fee

        # 创建订单
        order = Order(
            symbol=symbol,
            side=side,
            size=size,
            entry_price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            open_time=timestamp
        )
        
        # 创建持仓
        self.positions[symbol] = Position(order)
        self.orders.append(order)
        
        return order

    def close_position(self, symbol: str, price: float, timestamp: datetime):
        if symbol not in self.positions:
            return

        position = self.positions[symbol]
        multiplier = -1 if position.side == OrderSide.SHORT else 1
        pnl = (price - position.entry_price) * position.size * multiplier
        
        # 扣除手续费
        fee = price * position.size * self.fee_rate
        final_pnl = pnl - fee
        
        # 更新余额
        self.balance += final_pnl
        
        # 更新订单状态
        position.order.status = OrderStatus.CLOSED
        position.order.close_time = timestamp
        position.order.close_price = price
        position.order.pnl = final_pnl
        
        # 删除持仓
        del self.positions[symbol]
        
        # 更新最大回撤
        self.equity_peak = max(self.equity_peak, self.balance)
        current_drawdown = (self.equity_peak - self.balance) / self.equity_peak
        self.max_drawdown = max(self.max_drawdown, current_drawdown)

    def update_daily_balance(self, date: datetime):
        total_value = self.balance
        for position in self.positions.values():
            total_value += position.unrealized_pnl
        self.daily_balance[date] = total_value

