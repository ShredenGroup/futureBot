from .account import MockAccount, OrderStatus,OrderSide
import pandas as pd
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import seaborn as sns
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
    def run_hour(self, data: pd.DataFrame, signals: pd.DataFrame):
        """
        data: 小时级的价格数据 (WLD_df)
        signals: 小时级的信号数据 (merged_data)
        """
        # 合并小时级价格数据和信号数据
        merged = pd.merge(
            data,
            signals[['open_time', 'short_signal', 'wld_change', 'btc_change']],
            on='open_time',
            how='inner'
        )
        
        print(f"Total trading hours after merge: {len(merged)}")
        
        current_position = None
        
        for i in range(1, len(merged)):  # 从第二个小时开始
            current_row = merged.iloc[i]
            
            # 检查是否有开仓信号
            if current_row['short_signal']:
                if not current_position:
                    stop_loss = merged['high'].iloc[i-1]  # 前一小时的最高价
                    entry_price = current_row['close']
                    price_diff = stop_loss - entry_price
                    take_profit = entry_price - (price_diff * 2)  # 1:5的风险收益比
                    
                    print(f"\nOpening position on {current_row['open_time']}:")
                    print(f"Entry: {entry_price:.4f}")
                    print(f"Stop Loss: {stop_loss:.4f} (Risk: {price_diff:.4f})")
                    print(f"Take Profit: {take_profit:.4f} (Reward: {entry_price - take_profit:.4f})")
                    print(f"Risk/Reward Ratio: 1:{(entry_price - take_profit) / price_diff:.2f}")
                    
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
                    
                    print(f"\nClosing position on {current_row['open_time']}:")
                    print(f"Close price: {close_price:.4f}")
                    print(f"P&L: {(position.entry_price - close_price) * position.size:.2f}")
                    
                    self.account.close_position("WLD", close_price, current_row['open_time'])
                    current_position = None
            
            # 更新小时余额
            self.account.update_daily_balance(current_row['open_time'])

    def generate_report_hour(self):
        hourly_returns = pd.Series(self.account.daily_balance)  # 实际上是小时收益了
        total_return = (self.account.balance - self.account.initial_balance) / self.account.initial_balance
        
        winning_trades = len([order for order in self.account.orders 
                            if order.status == OrderStatus.CLOSED and order.pnl > 0])
        total_trades = len(self.account.orders)
        
        # 计算平均持仓时间
        holding_times = []
        for order in self.account.orders:
            if order.status == OrderStatus.CLOSED:
                holding_time = (order.close_time - order.open_time).total_seconds() / 3600  # 转换为小时
                holding_times.append(holding_time)
        
        avg_holding_time = sum(holding_times) / len(holding_times) if holding_times else 0
        
        report = {
            "Initial Balance": self.account.initial_balance,
            "Final Balance": self.account.balance,
            "Total Return": f"{total_return:.2%}",
            "Max Drawdown": f"{self.account.max_drawdown:.2%}",
            "Total Trades": total_trades,
            "Winning Trades": winning_trades,
            "Win Rate": f"{winning_trades/total_trades:.2%}" if total_trades > 0 else "N/A",
            "Average Holding Time (hours)": f"{avg_holding_time:.2f}",
            "Hourly Returns": hourly_returns
        }
        
        return report

class BacktestVisualizer:
    def __init__(self, account: MockAccount):
        self.account = account
        # 设置seaborn的样式
        sns.set_style("darkgrid")
        # 设置图表的默认大小
        plt.rcParams['figure.figsize'] = [12, 8]
        

    def plot_balance_history(self):
        """绘制账户余额历史"""
        balance_data = pd.Series(self.account.daily_balance)
        
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 15))
        
        # 1. 余额曲线
        ax1.plot(balance_data.index, balance_data.values, linewidth=2, color='blue')
        ax1.set_title('Account Balance History')
        ax1.set_ylabel('Balance (USDT)')
        ax1.grid(True)
        
        # 2. 回撤曲线
        running_max = balance_data.cummax()
        drawdown = (running_max - balance_data) / running_max * 100
        ax2.fill_between(drawdown.index, drawdown.values, color='red', alpha=0.3)
        ax2.set_title('Drawdown (%)')
        ax2.set_ylabel('Drawdown %')
        ax2.grid(True)
        
        # 3. 收益分布
        daily_returns = balance_data.pct_change() * 100
        sns.histplot(data=daily_returns.dropna(), bins=30, kde=True, ax=ax3, color='blue')
        ax3.set_title('Return Distribution')
        ax3.set_xlabel('Return (%)')
        ax3.grid(True)
        
        plt.tight_layout()
        
        # 添加关键统计信息
        stats_text = (
            f'Initial Balance: ${self.account.initial_balance:.2f}\n'
            f'Final Balance: ${self.account.balance:.2f}\n'
            f'Total Return: {((self.account.balance/self.account.initial_balance-1)*100):.2f}%\n'
            f'Max Drawdown: {self.account.max_drawdown*100:.2f}%\n'
            f'Win Rate: {self.calculate_win_rate():.2f}%'
        )
        fig.text(0.15, 0.95, stats_text, fontsize=10, verticalalignment='top', 
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        return fig

    def plot_trade_analysis(self):
        """绘制交易分析图"""
        trades = pd.DataFrame([
            {
                'entry_time': order.open_time,
                'exit_time': order.close_time,
                'entry_price': order.entry_price,
                'exit_price': order.close_price,
                'pnl': order.pnl,
                'holding_time': (order.close_time - order.open_time).total_seconds() / 3600 if order.close_time else 0
            }
            for order in self.account.orders if order.status == OrderStatus.CLOSED
        ])
        
        if len(trades) > 0:
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
            
            # 1. PnL分布
            sns.histplot(data=trades['pnl'], bins=20, kde=True, ax=ax1, color='blue')
            ax1.set_title('PnL Distribution')
            ax1.set_xlabel('PnL (USDT)')
            
            # 2. 持仓时间分布
            sns.histplot(data=trades['holding_time'], bins=20, kde=True, ax=ax2, color='green')
            ax2.set_title('Holding Time Distribution')
            ax2.set_xlabel('Holding Time (hours)')
            
            # 3. 累计PnL
            cumulative_pnl = trades['pnl'].cumsum()
            ax3.plot(range(len(cumulative_pnl)), cumulative_pnl, color='purple')
            ax3.set_title('Cumulative PnL')
            ax3.set_xlabel('Trade Number')
            ax3.set_ylabel('Cumulative PnL (USDT)')
            
            # 4. 每笔交易盈亏
            colors = ['green' if x > 0 else 'red' for x in trades['pnl']]
            ax4.bar(range(len(trades)), trades['pnl'], color=colors)
            ax4.set_title('PnL per Trade')
            ax4.set_xlabel('Trade Number')
            ax4.set_ylabel('PnL (USDT)')
            
            plt.tight_layout()
            return fig
        return None

    def calculate_win_rate(self) -> float:
        """计算胜率"""
        closed_trades = [order for order in self.account.orders 
                        if order.status == OrderStatus.CLOSED]
        if not closed_trades:
            return 0.0
        winning_trades = sum(1 for order in closed_trades if order.pnl > 0)
        return (winning_trades / len(closed_trades)) * 100

    def generate_visual_report(self, save_path: str = None):
        """生成完整的视觉报告"""
        balance_fig = self.plot_balance_history()
        trade_fig = self.plot_trade_analysis()
        
        if save_path:
            balance_fig.savefig(f'{save_path}_balance.png', dpi=300, bbox_inches='tight')
            if trade_fig:
                trade_fig.savefig(f'{save_path}_trades.png', dpi=300, bbox_inches='tight')
        else:
            plt.show()
