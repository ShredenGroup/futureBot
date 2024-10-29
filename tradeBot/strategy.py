import pandas as pd
from .account import Account
from typing import Tuple, List, Dict
class Strategy:
    @staticmethod
    def _prepare_data(df_WLD: pd.DataFrame, df_BTC: pd.DataFrame, 
                 time_frame: str = 'day') -> Tuple[pd.DataFrame, str]:
        """
        准备数据，计算涨跌幅并合并数据
        time_frame: 'day', 'hour', 或 '4hour'
        """
        for df in [df_WLD, df_BTC]:
            df['open_time'] = pd.to_datetime(df['open_time'])
        
        if time_frame == 'day':
            # 对于日线数据，使用当天的第一个open_time
            wld_data = df_WLD.groupby(df_WLD['open_time'].dt.date).agg({
                'open_time': 'first',  # 保留每天第一个open_time
                'day_change_static': 'first'
            }).reset_index(drop=True)
            
            btc_data = df_BTC.groupby(df_BTC['open_time'].dt.date).agg({
                'open_time': 'first',
                'day_change_static': 'first'
            }).reset_index(drop=True)
            
            merge_key = 'open_time'
        
        elif time_frame == '4hour':
            # 转换为4小时数据
            wld_4h = Strategy._convert_to_4h(df_WLD)
            btc_4h = Strategy._convert_to_4h(df_BTC)
            
            merge_key = 'open_time'
            wld_data = wld_4h[['open_time']].copy()
            btc_data = btc_4h[['open_time']].copy()
            
            # 计算4小时涨跌幅
            wld_data['change'] = wld_4h['close'].pct_change() * 100
            btc_data['change'] = btc_4h['close'].pct_change() * 100
        
        else:  # hourly
            merge_key = 'open_time'
            # 小时线逻辑保持不变
            wld_data = df_WLD[['open_time']].copy()
            btc_data = df_BTC[['open_time']].copy()
            wld_data['change'] = df_WLD['close'].pct_change() * 100
            btc_data['change'] = df_BTC['close'].pct_change() * 100

        # 合并数据
        change_col = 'day_change_static' if time_frame == 'day' else 'change'
        merged_data = pd.merge(
            wld_data.rename(columns={change_col: 'wld_change'}),
            btc_data.rename(columns={change_col: 'btc_change'}),
            on=merge_key
        )
        
        merged_data['wld_outperforms'] = merged_data['wld_change'] > merged_data['btc_change']
        merged_data = merged_data.iloc[1:].reset_index(drop=True)
        
        return merged_data, merge_key
    @staticmethod
    def _check_strategy_conditions(data: pd.DataFrame, current_idx: int) -> bool:
        """检查策略条件"""
        if current_idx < 10:
            return False
        
        # 检查最近两个周期的条件
        if not(
            (data['wld_change'].iloc[current_idx-1] < data['btc_change'].iloc[current_idx-1]) and
            (data['wld_change'].iloc[current_idx-2] < data['btc_change'].iloc[current_idx-2]) and
            (data['wld_change'].iloc[current_idx-1] < 0) and 
            (data['wld_change'].iloc[current_idx-2] < 0)
        ):
            return False
        
        # 寻找最近的连续三个周期WLD表现好于BTC的时期
        idx = current_idx - 3
        streak_end = None
        
        while idx >= 2:
            if (data['wld_outperforms'].iloc[idx] and 
                data['wld_outperforms'].iloc[idx-1] and 
                data['wld_outperforms'].iloc[idx-2]):
                streak_end = idx
                break
            idx -= 1
        
        if streak_end is None:
            return False
        
        # 检查从连续三个周期优势期结束到前两个周期这段时间内是否有连续两个周期WLD表现差于BTC
        for i in range(streak_end + 1, current_idx - 2):
            if (not data['wld_outperforms'].iloc[i] and 
                not data['wld_outperforms'].iloc[i+1]):
                return False
        
        return True, streak_end
    @staticmethod
    def _convert_to_4h(df: pd.DataFrame) -> pd.DataFrame:
        """将1小时数据转换为4小时数据"""
        # 确保时间索引是正确的
        df = df.copy()
        df['4h_group'] = df['open_time'].dt.floor('4H')
        
        # 按4小时周期聚合数据
        df_4h = df.groupby('4h_group').agg({
            'open': 'first',          # 第一个小时的开盘价
            'high': 'max',            # 4小时内的最高价
            'low': 'min',             # 4小时内的最低价
            'close': 'last',          # 最后一个小时的收盘价
            'volume': 'sum',          # 4小时内的总成交量
            'open_time': 'first'      # 使用第一个小时的时间戳
        }).reset_index(drop=True)
        
        df_4h['open_time'] = df_4h['open_time']  # 保持原始open_time
        return df_4h
    @staticmethod
    def _generate_signals(data: pd.DataFrame, time_key: str) -> Tuple[pd.DataFrame, List[Dict]]:
        """生成交易信号"""
        signals = []
        signal_details = []
        
        for i in range(len(data)):
            result = Strategy._check_strategy_conditions(data, i)
            should_short = False if isinstance(result, bool) else True
            streak_end = None if isinstance(result, bool) else result[1]
            
            signals.append(should_short)
            
            if should_short:
                signal_details.append({
                    f'signal_{time_key}': data[time_key].iloc[i],
                    f'three_period_streak_end_{time_key}': data[time_key].iloc[streak_end],
                    f'periods_since_streak': i - streak_end,
                    'wld_last_two_periods': data['wld_change'].iloc[i-2:i].tolist(),
                    'btc_last_two_periods': data['btc_change'].iloc[i-2:i].tolist()
                })
        
        data['short_signal'] = signals
        return data, signal_details 
    @staticmethod
    def BTC_WLD_4hour(df_WLD: pd.DataFrame, df_BTC: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict]]:
        """4小时线策略"""
        merged_data, time_key = Strategy._prepare_data(df_WLD, df_BTC, '4hour')
        return Strategy._generate_signals(merged_data, time_key)
    
    @staticmethod
    def BTC_WLD(df_WLD: pd.DataFrame, df_BTC: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict]]:
        """日线策略"""
        merged_data, time_key = Strategy._prepare_data(df_WLD, df_BTC, 'day')
        return Strategy._generate_signals(merged_data, time_key)

    @staticmethod
    def BTC_WLD_hour(df_WLD: pd.DataFrame, df_BTC: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict]]:
        """小时线策略"""
        merged_data, time_key = Strategy._prepare_data(df_WLD, df_BTC, 'hour')
        return Strategy._generate_signals(merged_data, time_key)