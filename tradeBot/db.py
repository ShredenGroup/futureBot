import pandas as pd
import numpy as np
import os
import glob
import sqlite3

class DB:
    def __init__(self):
        current_dictionary=os.path.abspath(os.getcwd())
        print(current_dictionary)
        file_path=os.path.join(current_dictionary,"tradeBot","arb_data")
        self.files_path=glob.glob(os.path.join(file_path,"*.csv"))
    def db_init(self):
        dfs=[]
        for file in sorted(self.files_path):
            df=pd.read_csv(file)
            dfs.append(df)
        print('loading completed')
        combined_db=pd.concat(dfs,ignore_index=True)
        combined_db['open_time']=pd.to_datetime(combined_db['open_time'],unit='ms')
        combined_db['close_time']=pd.to_datetime(combined_db['close_time'],unit='ms')
        
        return combined_db
    @staticmethod 
    def read_csv(path):
        return pd.read_csv(path)
    
    @staticmethod
    def caculate_ema(data,span):
       return data['close'].ewm(span=span,adjust=False).mean() 
    @staticmethod 
    def add_MACD(df):
        ema12=DB.caculate_ema(df,12)
        ema26=DB.caculate_ema(df,26)
        df['MACD']=ema12-ema26
        df['MACD'].iloc[:21] = np.nan
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['Signal'].iloc[:29]=np.nan
        df['MACD_Histogram'] = df['MACD'] - df['Signal']

        return df
    @staticmethod
    def add_day_price(df):
      # Convert open_time to datetime if it's not already
        df['open_time'] = pd.to_datetime(df['open_time'])
        
        # Create a helper column with just the date
        df['date'] = df['open_time'].dt.date
        
        # For each date, find the next day's opening price
        day_prices = df.groupby('date')['open'].first().reset_index()
        print(day_prices.head(10))
        # Shift the prices up by one row to get next day's price
        day_prices['day_price'] = day_prices['open'].shift(-1)
        
        # Merge back to original dataframe
        df = df.merge(day_prices[['date', 'day_price']], on='date', how='left')
        
        # Drop the helper column
        df = df.drop('date', axis=1)
        
        return df
    @staticmethod
    def add_day_changes(df):
    # Convert open_time to datetime if not already
        df['open_time'] = pd.to_datetime(df['open_time'])
        
        # For dynamic change (comparing with same time yesterday)
        # Shift the 'open' price by 24 rows (assuming hourly data) to get yesterday's price
        df['yesterday_price'] = df['open'].shift(24)
        df['day_change_dynamic'] = ((df['open'] - df['yesterday_price']) / df['yesterday_price'] * 100).round(2)
        
        # For static change (comparing day_price with yesterday's day_price)
        # First get yesterday's day_price
        df['yesterday_day_price'] = df['day_price'].shift(24)
        df['day_change_static'] = ((df['day_price'] - df['yesterday_day_price']) / df['yesterday_day_price'] * 100).round(2)
        
        # Clean up: remove the temporary columns
        df = df.drop(['yesterday_price', 'yesterday_day_price'], axis=1)
        
        return df 

    @staticmethod
    def export_to_csv(df,path):
        df.to_csv(path,index=False)
        print('Export Successfully')
    @staticmethod
    def format_then_export(path):
        current_dictionary=os.path.abspath(os.getcwd())
        print(current_dictionary)
        
        files_path=glob.glob(os.path.join(path,"*.csv"))
        print(files_path)
        dfs=[]
        for file in sorted(files_path):
            df=pd.read_csv(file)
            dfs.append(df)
        print('loading completed')
        combined_db=pd.concat(dfs,ignore_index=True)
        combined_db['open_time']=pd.to_datetime(combined_db['open_time'],unit='ms')
        combined_db['close_time']=pd.to_datetime(combined_db['close_time'],unit='ms')
        combined_db=DB.add_MACD(DB.add_day_changes(DB.add_day_price(combined_db)))
        DB.export_to_csv(combined_db,'/home/litterpigger/myprojects/futureBot/tradeBot/format_data/OP_format.csv') 


    




   
