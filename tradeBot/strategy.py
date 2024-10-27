import pandas as pd
from .account import Account

class Strategy:
    @staticmethod
    def BTC_WLD(df_WLD,df_BTC):
        for df in [df_WLD,df_BTC]:
            df['open_time']=pd.to_datetime(df['open_time'])
            df['date']=df['open_time'].dt.date
        def get_daily_change(df):
            return df.groupby('date')['day_change_static'].first().reset_index()
        
        WLD_day=get_daily_change(df_WLD)
        BTC_day=get_daily_change(df_BTC)
        merged_data=pd.merge(WLD_day.rename(columns={"day_change_static":"wld_change"}),BTC_day.rename(columns={"day_change_static":'btc_change'}),
                             on='date'
                             )
        merged_data['wld_outperforms'] = merged_data['wld_change'] > merged_data['btc_change']
        merged_data = merged_data.iloc[1:].reset_index(drop=True)
        print(merged_data.head())
        
        def check_strategy_conditions(data,current_idx):
            if current_idx<10:
                False
            
            if not(
               (data['wld_change'].iloc[current_idx-1]<data['btc_change'].iloc[current_idx-1]) 
               and ((data['wld_change'].iloc[current_idx-2] < data['btc_change'].iloc[current_idx-2]))
               and (data['wld_change'].iloc[current_idx-1]<0) and (data['wld_change'].iloc[current_idx-1]<0)
                 
            ):
                return False
            
            idx = current_idx - 3
            three_day_streak_end = None
            
            while idx >= 2:  # 确保有足够的历史数据来检查三天
                if (data['wld_outperforms'].iloc[idx] and 
                    data['wld_outperforms'].iloc[idx-1] and 
                    data['wld_outperforms'].iloc[idx-2]):
                    three_day_streak_end = idx
                    break
                idx -= 1
            
            if three_day_streak_end is None:
                return False
            
            # 检查从三天连续优势期结束到前天这段时间内是否有连续两天WLD表现差于BTC
            for i in range(three_day_streak_end + 1, current_idx - 2):
                if (not data['wld_outperforms'].iloc[i] and 
                    not data['wld_outperforms'].iloc[i+1])   :
                    return False
            
            return True
        signals = []
        signal_details = []
        
        for i in range(len(merged_data)):
            should_short = check_strategy_conditions(merged_data, i)
            signals.append(should_short)
            
            if should_short:
                # 记录信号的详细信息
                idx = i - 3
                streak_end = None
                while idx >= 2:
                    if (merged_data['wld_outperforms'].iloc[idx] and 
                        merged_data['wld_outperforms'].iloc[idx-1] and 
                        merged_data['wld_outperforms'].iloc[idx-2]):
                        streak_end = idx
                        break
                    idx -= 1
                    
                signal_details.append({
                    'signal_date': merged_data['date'].iloc[i],
                    'three_day_streak_end_date': merged_data['date'].iloc[streak_end],
                    'days_since_streak': i - streak_end,
                    'wld_last_two_days': merged_data['wld_change'].iloc[i-2:i].tolist(),
                    'btc_last_two_days': merged_data['btc_change'].iloc[i-2:i].tolist()
                })
        
        merged_data['short_signal'] = signals
        
        return merged_data, signal_details
    def BTC_WLD_hour(df_WLD, df_BTC):
        # 1. 数据预处理：计算小时涨跌幅
        for df in [df_WLD, df_BTC]:
            df['open_time'] = pd.to_datetime(df['open_time'])
            df['hourly_change'] = df['close'].pct_change() * 100

        # 2. 合并WLD和BTC的数据
        merged_data = pd.merge(
            df_WLD[['open_time', 'hourly_change']].rename(columns={'hourly_change': 'wld_change'}),
            df_BTC[['open_time', 'hourly_change']].rename(columns={'hourly_change': 'btc_change'}),
            on='open_time'
        )
        
        # 3. 计算WLD相对BTC的表现
        merged_data['wld_outperforms'] = merged_data['wld_change'] > merged_data['btc_change']
        merged_data = merged_data.iloc[1:].reset_index(drop=True)  # 删除第一行（因为计算涨跌幅后第一行是NaN）
        print(merged_data.head()) 
        def check_strategy_conditions(data, current_idx):
            if current_idx < 10:  # 确保有足够的历史数据
                return False
            
            # 检查最近两个小时的条件
            if not(
                (data['wld_change'].iloc[current_idx-1] < data['btc_change'].iloc[current_idx-1]) and
                (data['wld_change'].iloc[current_idx-2] < data['btc_change'].iloc[current_idx-2]) and
                (data['wld_change'].iloc[current_idx-1] < 0) and 
                (data['wld_change'].iloc[current_idx-2] < 0)
            ):
                return False
            
            # 寻找最近的连续三小时WLD表现好于BTC的时期
            idx = current_idx - 3
            three_hour_streak_end = None
            
            while idx >= 2:
                if (data['wld_outperforms'].iloc[idx] and 
                    data['wld_outperforms'].iloc[idx-1] and 
                    data['wld_outperforms'].iloc[idx-2]):
                    three_hour_streak_end = idx
                    break
                idx -= 1
            
            if three_hour_streak_end is None:
                return False
            
            # 检查从连续三小时优势期结束到前两小时这段时间内是否有连续两小时WLD表现差于BTC
            for i in range(three_hour_streak_end + 1, current_idx - 2):
                if (not data['wld_outperforms'].iloc[i] and 
                    not data['wld_outperforms'].iloc[i+1]):
                    return False
            
            return True
        
        # 4. 生成信号
        signals = []
        signal_details = []
        
        for i in range(len(merged_data)):
            should_short = check_strategy_conditions(merged_data, i)
            signals.append(should_short)
            
            if should_short:
                # 记录信号的详细信息
                idx = i - 3
                streak_end = None
                while idx >= 2:
                    if (merged_data['wld_outperforms'].iloc[idx] and 
                        merged_data['wld_outperforms'].iloc[idx-1] and 
                        merged_data['wld_outperforms'].iloc[idx-2]):
                        streak_end = idx
                        break
                    idx -= 1
                    
                signal_details.append({
                    'signal_time': merged_data['open_time'].iloc[i],
                    'three_hour_streak_end_time': merged_data['open_time'].iloc[streak_end],
                    'hours_since_streak': i - streak_end,
                    'wld_last_two_hours': merged_data['wld_change'].iloc[i-2:i].tolist(),
                    'btc_last_two_hours': merged_data['btc_change'].iloc[i-2:i].tolist()
                })
        
        merged_data['short_signal'] = signals
        
        return merged_data, signal_details
