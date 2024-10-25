import pandas as pd
import numpy as np
import os
import glob
import sqlite3

class DB:
    def __init__(self):
        current_dictionary=os.path.abspath(os.getcwd())
        print(current_dictionary)
        file_path=os.path.join(current_dictionary,"futureBot","btc_data")
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
    
    def caculate_ema(self,data,span):
       return data['close'].ewm(span=span,adjust=False).mean() 
    
    def add_MACD(self,df):
        ema12=self.caculate_ema(df,12)
        ema26=self.caculate_ema(df,26)
        df['MACD']=ema12-ema26
        df['MACD'].iloc[:21] = np.nan
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['Signal'].iloc[:29]=np.nan
        df['MACD_Histogram'] = df['MACD'] - df['Signal']
        df=df.drop(columns=['ignore','taker_buy_quote_volume','count','taker_buy_volume'],errors='ignore')

        return df

    def export_to_csv(self,df,path):
        df.to_csv(path,index=False)
        print('Export Successfully')




   
