class BackTest:
    def __init__(self, account: MockAccount):
        self.account = account
        self.trades = []
        
    def run(self, data: pd.DataFrame, signals: pd.DataFrame):
        current_position = None
        
        for i in range(len(data)):
            current_row = data.iloc[i]
            date = pd.to_datetime(current_row['open_time']).date()
            
            # 检查是否有开仓信号
            if signals['short_signal'].iloc[i]:
                if not current_position:
                    stop_loss = data['high'].iloc[i-1]  # 前一天的最高价
                    entry_price = current_row['close']
                    price_diff = stop_loss - entry_price
                    take_profit = entry_price - (price_diff * 3)  # 1:3的风险收益比
                    
                    self.account.open_position(
                        symbol="WLD",
                        side=OrderSide.SHORT,
                        price=entry_price,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        timestamp=current_row['open_time']
                    )
            
            # 检查止损和止盈
            if "WLD" in self.account.positions:
                position = self.account.positions["WLD"]
                current_price = current_row['close']
                
                if (current_row['high'] >= position.stop_loss or 
                    current_row['low'] <= position.take_profit):
                    self.account.close_position("WLD", current_price, current_row['open_time'])
            
            # 更新每日余额
            self.account.update_daily_balance(date)

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
