from .account import MockAccount, OrderStatus, OrderSide
import pandas as pd
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from typing import Dict, Tuple, List,Optional
from enum import Enum

class TimeFrame(Enum):
    DAY = 'day'
    HOUR = 'hour'
    FOUR_HOUR = '4hour'

class BackTest:
    def __init__(self, account: MockAccount, risk_free_rate: float = 0.03):
        self.account = account
        self.trades = []
        self.risk_free_rate = risk_free_rate
        self.annualization_factors = {
            TimeFrame.DAY: 252,
            TimeFrame.HOUR: 252 * 24,
            TimeFrame.FOUR_HOUR: 252 * 6
        }

    def _prepare_data(self, data: pd.DataFrame, signals: pd.DataFrame, 
                 timeframe: TimeFrame) -> pd.DataFrame:
        """统一数据准备逻辑"""
        # 确保所有时间列是datetime格式
        data['open_time'] = pd.to_datetime(data['open_time'])
        if 'date' in signals.columns:
            signals['open_time'] = pd.to_datetime(signals['date']).apply(
                lambda x: x.replace(hour=0, minute=0, second=0)
            )
        
        if timeframe == TimeFrame.DAY:
            daily_data = data.groupby(data['open_time'].dt.date).agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'open_time': 'first'
            }).reset_index(drop=True)
            
        elif timeframe == TimeFrame.FOUR_HOUR:
            # 假设已经传入了4小时数据
            daily_data = data
            
        else:  # HOUR
            daily_data = data
        
        # 统一合并逻辑
        merged_data = pd.merge(
            daily_data,
            signals[['open_time', 'short_signal', 'wld_change', 'btc_change']],
            on='open_time',
            how='inner'
        )
        
        return merged_data 

    def _execute_trades(self, merged_data: pd.DataFrame, timeframe: TimeFrame):
        """统一交易执行逻辑"""
        time_key = 'date' if timeframe == TimeFrame.DAY else 'open_time'
        current_position = None
        
        for i in range(1, len(merged_data)):
            current_row = merged_data.iloc[i]
            
            # 检查开仓信号
            if current_row['short_signal'] and not current_position:
                stop_loss = merged_data['high'].iloc[i-1]
                entry_price = current_row['close']
                price_diff = stop_loss - entry_price
                take_profit = entry_price - (price_diff * 2)  
                
                print(f"\nOpening position on {current_row[time_key]}:")
                print(f"Entry: {entry_price:.4f}")
                print(f"Stop Loss: {stop_loss:.4f} (Risk: {price_diff:.4f})")
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
            
            # 检查止损止盈
            if "WLD" in self.account.positions:
                position = self.account.positions["WLD"]
                
                if (current_row['high'] >= position.stop_loss or 
                    current_row['low'] <= position.take_profit):
                    close_price = (position.stop_loss if current_row['high'] >= position.stop_loss 
                                 else position.take_profit)
                    
                    print(f"\nClosing position on {current_row[time_key]}:")
                    print(f"Close price: {close_price:.4f}")
                    print(f"P&L: {(position.entry_price - close_price) * position.size:.2f}")
                    
                    self.account.close_position("WLD", close_price, current_row['open_time'])
                    current_position = None
            
            # 更新账户余额
            self.account.update_daily_balance(current_row[time_key])

    def calculate_sharpe_ratio(self, returns: pd.Series, timeframe: TimeFrame) -> float:
        """计算夏普比率"""
        annualization_factor = self.annualization_factors[timeframe]
        returns_std = returns.std() * np.sqrt(annualization_factor)
        returns_mean = returns.mean() * annualization_factor
        
        return (returns_mean - self.risk_free_rate) / returns_std if returns_std != 0 else 0

    def generate_performance_metrics(self, timeframe: TimeFrame) -> Dict:
        """生成统一的性能指标"""
        returns = pd.Series(self.account.daily_balance).pct_change().dropna()
        total_return = (self.account.balance - self.account.initial_balance) / self.account.initial_balance
        
        winning_trades = len([order for order in self.account.orders 
                            if order.status == OrderStatus.CLOSED and order.pnl > 0])
        total_trades = len(self.account.orders)
        
        # 计算平均持仓时间
        holding_times = []
        for order in self.account.orders:
            if order.status == OrderStatus.CLOSED:
                holding_time = (order.close_time - order.open_time).total_seconds() / 3600
                holding_times.append(holding_time)
        
        metrics = {
            "Initial Balance": self.account.initial_balance,
            "Final Balance": self.account.balance,
            "Total Return": f"{total_return:.2%}",
            "Max Drawdown": f"{self.account.max_drawdown:.2%}",
            "Sharpe Ratio": f"{self.calculate_sharpe_ratio(returns, timeframe):.2f}",
            "Total Trades": total_trades,
            "Winning Trades": winning_trades,
            "Win Rate": f"{winning_trades/total_trades:.2%}" if total_trades > 0 else "N/A",
            "Returns": returns
        }
        
        if timeframe != TimeFrame.DAY:
            metrics["Average Holding Time (hours)"] = (
                f"{sum(holding_times)/len(holding_times):.2f}" if holding_times else "N/A"
            )
        
        return metrics

    def run(self, data: pd.DataFrame, signals: pd.DataFrame, timeframe: TimeFrame):
        """统一的回测入口"""
        print(f"Running backtest for {timeframe.value} timeframe")
        merged_data = self._prepare_data(data, signals, timeframe)
        print(f"Total {timeframe.value}s after merge: {len(merged_data)}")
        
        self._execute_trades(merged_data, timeframe)
        return self.generate_performance_metrics(timeframe)
class BacktestVisualizer:
    def __init__(self, account: MockAccount, timeframe: TimeFrame):
        self.account = account
        self.timeframe = timeframe
        # 设置可视化风格
        sns.set_style("darkgrid")
        plt.rcParams['figure.figsize'] = [12, 8]
        
        # 时间框架相关的标签
        self.time_labels = {
            TimeFrame.DAY: 'Daily',
            TimeFrame.HOUR: 'Hourly',
            TimeFrame.FOUR_HOUR: '4-Hour'
        }

    def _prepare_trade_data(self) -> pd.DataFrame:
        """准备交易数据用于可视化"""
        trades = pd.DataFrame([
            {
                'entry_time': order.open_time,
                'exit_time': order.close_time,
                'entry_price': order.entry_price,
                'exit_price': order.close_price,
                'pnl': order.pnl,
                'holding_time': (order.close_time - order.open_time).total_seconds() / 3600
            }
            for order in self.account.orders if order.status == OrderStatus.CLOSED
        ])
        return trades

    def plot_equity_curve(self, ax: plt.Axes) -> None:
        """绘制权益曲线"""
        balance_data = pd.Series(self.account.daily_balance)
        ax.plot(balance_data.index, balance_data.values, linewidth=2, color='blue')
        ax.set_title(f'{self.time_labels[self.timeframe]} Balance History')
        ax.set_ylabel('Balance (USDT)')
        ax.grid(True)

    def plot_drawdown(self, ax: plt.Axes) -> None:
        
        balance_data = pd.Series(self.account.daily_balance)
        print("Balance data type:", type(balance_data))
        print("\nBalance index type:", type(balance_data.index))
        print("\nFirst few items of daily_balance:")
        print(pd.Series(self.account.daily_balance).head())
        print("\nIndex values:")
        print(balance_data.index[:5])
        print("\nBalance values:")
        print(balance_data.values[:5])
        # 确保索引是datetime类型
        balance_data.index = pd.to_datetime(balance_data.index)
        
        running_max = balance_data.cummax()
        drawdown = (running_max - balance_data) / running_max * 100
        
        # 创建数值索引用于绘图
        x_values = np.arange(len(drawdown))
        
        ax.fill_between(x_values, drawdown.values, color='red', alpha=0.3)
        
        # 设置x轴刻度和标签
        if len(x_values) > 0:
            # 选择合适数量的刻度
            n_ticks = min(10, len(x_values))
            tick_positions = np.linspace(0, len(x_values)-1, n_ticks, dtype=int)
            ax.set_xticks(tick_positions)
            # 格式化时间标签
            tick_labels = [balance_data.index[i].strftime('%Y-%m-%d %H:%M') 
                        for i in tick_positions]
            ax.set_xticklabels(tick_labels, rotation=45)
        
        ax.set_title('Drawdown (%)')
        ax.set_ylabel('Drawdown %')
        ax.grid(True)

    def plot_returns_distribution(self, ax: plt.Axes) -> None:
        """绘制收益分布"""
        balance_data = pd.Series(self.account.daily_balance)
        returns = balance_data.pct_change() * 100
        sns.histplot(data=returns.dropna(), bins=30, kde=True, ax=ax, color='blue')
        ax.set_title(f'{self.time_labels[self.timeframe]} Returns Distribution')
        ax.set_xlabel('Return (%)')
        ax.grid(True)

    def plot_pnl_distribution(self, trades: pd.DataFrame, ax: plt.Axes) -> None:
        """绘制盈亏分布"""
        sns.histplot(data=trades['pnl'], bins=20, kde=True, ax=ax, color='blue')
        ax.set_title('PnL Distribution')
        ax.set_xlabel('PnL (USDT)')

    def plot_holding_time_distribution(self, trades: pd.DataFrame, ax: plt.Axes) -> None:
        """绘制持仓时间分布"""
        sns.histplot(data=trades['holding_time'], bins=20, kde=True, ax=ax, color='green')
        ax.set_title('Holding Time Distribution')
        ax.set_xlabel(f'Holding Time ({self.time_labels[self.timeframe]})')

    def plot_cumulative_pnl(self, trades: pd.DataFrame, ax: plt.Axes) -> None:
        """绘制累计盈亏"""
        cumulative_pnl = trades['pnl'].cumsum()
        ax.plot(range(len(cumulative_pnl)), cumulative_pnl, color='purple')
        ax.set_title('Cumulative PnL')
        ax.set_xlabel('Trade Number')
        ax.set_ylabel('Cumulative PnL (USDT)')

    def plot_trade_pnl(self, trades: pd.DataFrame, ax: plt.Axes) -> None:
        """绘制每笔交易盈亏"""
        colors = ['green' if x > 0 else 'red' for x in trades['pnl']]
        ax.bar(range(len(trades)), trades['pnl'], color=colors)
        ax.set_title('PnL per Trade')
        ax.set_xlabel('Trade Number')
        ax.set_ylabel('PnL (USDT)')

    def add_performance_stats(self, fig: plt.Figure) -> None:
        """添加性能统计信息"""
        returns = pd.Series(self.account.daily_balance).pct_change()
        sharpe_ratio = self.calculate_sharpe_ratio(returns)
        win_rate = self.calculate_win_rate()
        
        stats_text = (
            f'Initial Balance: ${self.account.initial_balance:.2f}\n'
            f'Final Balance: ${self.account.balance:.2f}\n'
            f'Total Return: {((self.account.balance/self.account.initial_balance-1)*100):.2f}%\n'
            f'Max Drawdown: {self.account.max_drawdown*100:.2f}%\n'
            f'Sharpe Ratio: {sharpe_ratio:.2f}\n'
            f'Win Rate: {win_rate:.2f}%'
        )
        fig.text(0.15, 0.95, stats_text, fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    def calculate_win_rate(self) -> float:
        """计算胜率"""
        closed_trades = [order for order in self.account.orders 
                        if order.status == OrderStatus.CLOSED]
        if not closed_trades:
            return 0.0
        winning_trades = sum(1 for order in closed_trades if order.pnl > 0)
        return (winning_trades / len(closed_trades)) * 100

    def calculate_sharpe_ratio(self, returns: pd.Series) -> float:
        """计算夏普比率"""
        annualization_factor = {
            TimeFrame.DAY: 252,
            TimeFrame.HOUR: 252 * 24,
            TimeFrame.FOUR_HOUR: 252 * 6
        }[self.timeframe]
        
        returns_std = returns.std() * np.sqrt(annualization_factor)
        returns_mean = returns.mean() * annualization_factor
        return (returns_mean - 0.03) / returns_std if returns_std != 0 else 0

    def generate_report(self, save_path: Optional[str] = None) -> None:
        """生成完整的视觉报告"""

        # 创建主要性能图表
        fig1, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 15))
        self.plot_equity_curve(ax1)
        self.plot_drawdown(ax2)
        self.plot_returns_distribution(ax3)
        self.add_performance_stats(fig1)
        
        # 创建交易分析图表
        trades = self._prepare_trade_data()
        if len(trades) > 0:
            fig2, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
            self.plot_pnl_distribution(trades, ax1)
            self.plot_holding_time_distribution(trades, ax2)
            self.plot_cumulative_pnl(trades, ax3)
            self.plot_trade_pnl(trades, ax4)
            plt.tight_layout()
        
        if save_path:
            fig1.savefig(f'{save_path}_performance.png', dpi=300, bbox_inches='tight')
            if len(trades) > 0:
                fig2.savefig(f'{save_path}_trades.png', dpi=300, bbox_inches='tight')
        else:
            plt.show()