from .account import MockAccount, OrderStatus,OrderSide
import pandas as pd
class BackTest:
    def __init__(self, account: MockAccount):
        self.account = account
        self.trades = []
        
    def run(self, data: pd.DataFrame, signals: pd.DataFrame):
        """
        data: 小时级的价格数据 (WLD_df)
        signals: 日级的信号数据 (merged_data)
        """
        # 1. 使用已有的date列进行日级聚合
        daily_data = data.groupby('date').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'open_time': 'first'
        }).reset_index()
        
        # 2. 合并日级价格数据和信号数据
        merged = pd.merge(
            daily_data,
            signals[['date', 'short_signal', 'wld_change', 'btc_change']],
            on='date',
            how='inner'
        )
        
        print(f"Total trading days after merge: {len(merged)}")
        
        current_position = None
        
        for i in range(1, len(merged)):  # 从第二天开始
            current_row = merged.iloc[i]
            
            # 检查是否有开仓信号
            if current_row['short_signal']:
                if not current_position:
                    stop_loss = merged['high'].iloc[i-1]  # 前一天的最高价
                    entry_price = current_row['close']
                    price_diff = stop_loss - entry_price
                    take_profit = entry_price - (price_diff * 2)  # 1:3的风险收益比
                    
                    print(f"\nOpening position on {current_row['date']}:")
                    print(f"Entry: {entry_price:.4f}")
                    print(f"Stop Loss: {stop_loss:.4f}")
                    print(f"Take Profit: {take_profit:.4f}")
                    
                    self.account.open_position(
                        symbol="WLD",
                        side=OrderSide.SHORT,
                        price=entry_price,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        timestamp=current_row['open_time']
                    )
                    current_position = "SHORT"
            
            # 检查止损和止盈
            if "WLD" in self.account.positions:
                position = self.account.positions["WLD"]
                current_price = current_row['close']
                
                if (current_row['high'] >= position.stop_loss or 
                    current_row['low'] <= position.take_profit):
                    close_price = position.stop_loss if current_row['high'] >= position.stop_loss else position.take_profit
                    
                    print(f"\nClosing position on {current_row['date']}:")
                    print(f"Close price: {close_price:.4f}")
                    print(f"P&L: {(position.entry_price - close_price) * position.size:.2f}")
                    
                    self.account.close_position("WLD", close_price, current_row['open_time'])
                    current_position = None
            
            # 更新每日余额
            self.account.update_daily_balance(current_row['date'])

    def generate_report(self):
        daily_returns = pd.Series(self.account.daily_balance)
        total_return = (self.account.balance - self.account.initial_balance) / self.account.initial_balance
        
        winning_trades = len([order for order in self.account.orders 
                            if order.status == OrderStatus.CLOSED and order.pnl > 0])
        total_trades = len(self.account.orders)
        
        report = {
            "Initial Balance": self.account.initial_balance,
            "Final Balance": self.account.balance,
            "Total Return": f"{total_return:.2%}",
            "Max Drawdown": f"{self.account.max_drawdown:.2%}",
            "Total Trades": total_trades,
            "Winning Trades": winning_trades,
            "Win Rate": f"{winning_trades/total_trades:.2%}" if total_trades > 0 else "N/A",
            "Daily Returns": daily_returns
        }
        
        return report
