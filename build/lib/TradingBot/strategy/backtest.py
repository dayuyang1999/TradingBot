from turtle import shape
from .momentum import Momentum
from .double_momentum import DoubleMomentum
import yfinance as yf
import numpy as np

from alpaca_trade_api.rest import REST, TimeFrame
from alpaca_trade_api.stream import Stream
import alpaca_trade_api as tradeapi

from datetime import datetime, timedelta

from tqdm import tqdm
from pytz import timezone
from typing import Tuple

from TradingBot.utils import get_data
import pandas as pd


class APISettings:
    API_KEY_ID = "your"
    SECRET_KEY = "your"
    ENDPOINT = 'https://paper-api.alpaca.markets'

    

class RollingBackTest():
    # '''
    # WARINING:
    # for 1m: due to yahoo finance data restriction, must be within the last 30 days
    # - 
    # '''
    def __init__(self, momentum_settings, api_setting:APISettings(), test_strategy:str, start_testing_date, testing_length, 
                 signal_ticker, long_ticker, short_ticker,
                 data_interval, gap, verbose, skip_morning):
        
        self.start_testing_date = start_testing_date
        self.skip_morning = skip_morning
        self.testing_length = testing_length
        self.gap = gap
        self.test_strategy = test_strategy
        self.signal_ticker = signal_ticker
        self.long_ticker = long_ticker
        self.short_ticker = short_ticker
        self.data_interval = data_interval
        self.verbose =  verbose
        self. momentum_settings =  momentum_settings
        self.api = REST(api_setting.API_KEY_ID, api_setting.SECRET_KEY, api_setting.ENDPOINT)
        
        self.total_rets, self.long_rets, self.short_rets, self.rets_noncomp,  start_dates, end_dates = self.testing()
        self.results = pd.DataFrame({'start_date':start_dates, 'end_date':end_dates, 'cum_ret':self.total_rets,'long_cum_ret':self.long_rets, 'short_cum_ret':self.short_rets,
                                'non_cum_ret': self.rets_noncomp})

            
        
    def testing(self):
        start_dates, end_dates = self.create_rolling_dates()
        print("start testing...")
        test_returns = []
        long_returns = []
        short_returns = []
        rets_noncomp = []
        total_sucs = []
        for start_date, end_date in tqdm(zip(start_dates, end_dates), total=len(end_dates)):
            backtest = BackTest(self.test_strategy, self.momentum_settings, start_date, end_date, self.signal_ticker, self.long_ticker, self.short_ticker, self.data_interval, verbose=self.verbose)
            test_returns.append(backtest.return_total)
            long_returns.append(backtest.return_long)
            short_returns.append(backtest.return_short)
            rets_noncomp.append(backtest.total_ret_noncomp)
            total_sucs.append(backtest.total_suc)
            # try:
            #     backtest = BackTest(self.test_strategy, self.momentum_settings, start_date, end_date, self.signal_ticker, self.long_ticker, self.short_ticker, self.data_interval, verbose=self.verbose, skip_morning=self.skip_morning)
            #     test_returns.append(backtest.return_total)
            #     long_returns.append(backtest.return_long)
            #     short_returns.append(backtest.return_short)
            #     rets_noncomp.append(backtest.total_ret_noncomp)
            #     total_sucs.append(backtest.total_suc)
                
            # except:
            #     test_returns.append(1)
            #     long_returns.append(1)
            #     short_returns.append(1)  
            #     rets_noncomp.append(1)
            #     total_sucs.append(0.5)
        
        return  test_returns, long_returns, short_returns, rets_noncomp,  start_dates, end_dates
        
    
    
    def create_rolling_dates(self):
        start_testing = self.start_testing_date

        nyc = timezone('America/New_York')
        #now = datetime.today().astimezone(nyc)
        days_before = datetime.today() - timedelta(self.testing_length)
        days_before_str = days_before.astimezone(nyc).strftime('%Y-%m-%d')
        calendar = self.api.get_calendar(start=start_testing, end=days_before_str) # get the next closet trading day 
        calender_date_str = [date.date for date in calendar] # .strftime('%Y-%m-%d')
        calender_date_str = calender_date_str[0::self.gap]
        starts = []
        ends = []
        for date in calender_date_str:
            starts.append(date.strftime('%Y-%m-%d'))
            end = date + timedelta(days=self.testing_length)
            ends.append(end.strftime('%Y-%m-%d'))
        
        return (starts, ends)
    
    
    
    
    

class BackTest:
    def __init__(self, test_strategy, momentum_settings, start_date, end_date, signal_ticker, long_ticker, short_ticker, data_inverval, which='Close', verbose=True, skip_morning=False):
        '''
        date format like '2022-05-04'
        
        WARNING:
        match dfs took a lot of time.
        
        '''
        # get data
        nasdaq = get_data(tiker=signal_ticker, start=start_date, end=end_date, which=which, interval = data_inverval)
        tqqq = get_data(tiker=long_ticker, start=start_date, end=end_date, which=which,interval = data_inverval)
        sqqq =  get_data(tiker=short_ticker, start=start_date, end=end_date, which=which, interval = data_inverval)
        # remove the last row, since the last row sometimes contains the latest datapoint (Bug of yfinance)
        nasdaq = nasdaq[:-1]
        tqqq = tqqq[:-1]
        sqqq = sqqq[:-1]
        #print(start_date, end_date, nasdaq.shape[0], tqqq.shape[0], sqqq.shape[0])
        
        # add str date (min-level)
        nasdaq = self.convert_time(nasdaq)
        tqqq = self.convert_time(tqqq)
        sqqq = self.convert_time(sqqq)
        
        # if daily or hourly, you can comment this line to save time.
        nasdaq, tqqq, sqqq = self.match_dfs(nasdaq, tqqq, sqqq)
        
        #print(start_date, end_date, nasdaq.shape[0], tqqq.shape[0], sqqq.shape[0])
        
        assert  nasdaq.shape[0] == tqqq.shape[0] == sqqq.shape[0]
        
        
        self.signal_df = self.convertdata_yfinance(nasdaq)
        self.long_df = self.convertdata_yfinance(tqqq)
        self.short_df = self.convertdata_yfinance(sqqq)
        
        # adding log ret to asset df
        # WARNING: ret on 15:45 = given a strategy on time point 15:45, return you can get (during 15:45 ~ 16:00)
        self.long_df['log_ret'] = np.log(self.long_df['price'].shift(-1)) - np.log(self.long_df['price'])
        self.short_df['log_ret'] = np.log(self.short_df['price'].shift(-1)) - np.log(self.short_df['price'])
        # replace nan to 0
        self.long_df['log_ret'].replace(np.nan, 0, inplace=True)
        self.short_df['log_ret'].replace(np.nan, 0, inplace=True)
        assert self.long_df.shape[0] == self.short_df.shape[0] == self.signal_df.shape[0]
        
        
        # get signal
        if test_strategy == 'momentum':
            self.momentum = Momentum(self.signal_df, momentum_settings, verbose, skip_morning)
        
        # converting signal to vector 
        self.signal_df = self.momentum.signal_df # update
        self.signal_df['long_sig'] = np.squeeze(np.array([self.signal_df['signal'] == 'long']))
        self.signal_df['short_sig'] = np.squeeze(np.array([self.signal_df['signal'] == 'short']))
        
        
        
        # print return 
        self.return_total, self.return_long, self.return_short, self.totals, self.longs, self.shorts = self.compute_comp_return()
        self.total_ret_noncomp, self.long_ret_noncomp, self.short_ret_noncomp = self.compute_noncomp_return()
        self.total_suc, self.long_suc, self.short_suc = self.success_rate()


    def match_dfs(self, df1, df2, df3):
        dfs = [df1, df2, df3]
        all_dates = list(set(list(df1['str_time'].values)))+  list(set(list(df2['str_time'].values))) + list(set(list(df3['str_time'].values)))
        valid_dates = [date for date in all_dates if all_dates.count(date)==3]
        valid_dates = set(valid_dates)
        valid_dates = list(valid_dates)
        
        new_dfs = []
        for df in dfs:
            new_dfs.append(df[df['str_time'].isin(valid_dates)])
        

        return new_dfs[0].sort_values('Date').reset_index(drop=True), new_dfs[1].sort_values('Date').reset_index(drop=True), new_dfs[2].sort_values('Date').reset_index(drop=True)

        
    
    def convertdata_yfinance(self, yfi_data):
        '''
        use open during eval
        
        '''
        def convert_time(row):
            nyc = timezone('America/New_York')
            return row['Date'].to_pydatetime().astimezone(nyc)
        
        yfi_data['time'] = yfi_data.apply(lambda row: convert_time(row), axis=1)
        yfi_data.rename(columns={'Open':'price'}, inplace=True)
        return yfi_data[['time', 'price']]
    

    def convert_time(self, yfi_data):
        '''
        
        
        '''
        def convert_(row):
            return row['Date'].to_pydatetime().strftime('%Y-%m-%d-%H-%M') 
        yfi_data['str_time'] = yfi_data.apply(lambda row: convert_(row), axis=1)
        return yfi_data
        
    
    
    def compute_comp_return(self):
        return_totals = []
        return_longs = []
        return_shorts = []
        for i in range(self.long_df.shape[0]): #len(self.tqqq['log_ret'].values[2:])):
            return_long = np.array(self.long_df['log_ret'].values)[:i+1].dot(np.array(self.signal_df['long_sig'])[:i+1])
            return_longs.append(return_long)
            return_short = np.array(self.short_df['log_ret'].values)[:i+1].dot(np.array(self.signal_df['short_sig'])[:i+1])
            return_shorts.append(return_short)
            return_total = np.exp(return_long + return_short)
            return_totals.append(return_total)
        
        return_long = self.long_df['log_ret'].values.dot(self.signal_df['long_sig'].values)
        return_short = self.short_df['log_ret'].values.dot(self.signal_df['short_sig'].values)
        return_total = return_long + return_short
        
        
        return np.exp(return_total), np.exp(return_long), np.exp(return_short) , return_totals, return_longs, return_shorts
    
    def compute_noncomp_return(self):
        
        return_long = np.mean(np.exp(np.multiply(np.array(self.long_df['log_ret'].values), np.array(self.signal_df['long_sig']))))
        return_short = np.mean(np.exp(np.multiply(np.array(self.short_df['log_ret'].values), np.array(self.signal_df['short_sig']))))
        return_total = (return_long + return_short) / 2
        return return_total, return_long, return_short
        
        
        
    def success_rate(self):
        long_arr = np.array(self.long_df['log_ret'].values)
        short_arr = np.array(self.short_df['log_ret'].values)
        try:
            rate_long = (np.array(long_arr > 0).astype(int).dot(self.signal_df['long_sig'].values.astype(int))) / sum(self.signal_df['long_sig'].values)
        except:
            rate_long = 1
        try:
            rate_short = (np.array(short_arr > 0).astype(int).dot(self.signal_df['short_sig'].values.astype(int))) / sum(self.signal_df['short_sig'].values)
        except:
            rate_short = 1
        try:
            total_rate = ((np.array(long_arr > 0).astype(int).dot(np.array(self.signal_df['long_sig']).astype(int))) + (np.array(short_arr > 0).astype(int).dot(np.array(self.signal_df['short_sig']).astype(int))) ) / (sum(self.signal_df['long_sig'])+sum(self.signal_df['short_sig']))
        except:
            total_rate = 1
        return total_rate, rate_long, rate_short
        
    # def get_data(self, tiker='^IXIC', start="2022-05-05", end="2022-05-06", which='Close', interval='1m'):
    #     '''
    #     # Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
    #     # Valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
    #     # see https://github.com/ranaroussi/yfinance/blob/9eef951acc70121e65825ad25e7afd2edd4c3e4b/yfinance/multi.py
    #     '''
    #     def reformulate_date(df):
    #         df.columns = df.columns.map(''.join)
    #         df = df.rename_axis('Date').reset_index()
    #         return df
    #     data = yf.download(tickers = tiker, start=start, end=end, interval = interval, progress=False)
    #     data['pct_change'] = data[which].pct_change()
    #     data['log_ret'] = np.log(data[which]) - np.log(data[which].shift(1))
    #     data = reformulate_date(data)
    #     data = data[:-1]
    #     #print("most recent date is ", data.iloc[-1, 0])
    #     return data
        



class BackTest_Doublemomentum:
    def __init__(self, shortterm_momentum_settings, longterm_momentum_settings, 
                 shortterm_start_date, longterm_start_date, end_date, 
                 signal_ticker, long_ticker, short_ticker, 
                 shortterm_data_inverval, longterm_data_interval, 
                 which='Close', verbose=True):
        '''
        date format like '2022-05-04'
        
        '''
        # get data
        nasdaq = get_data(tiker=signal_ticker, start=shortterm_start_date, end=end_date, which=which, interval = shortterm_data_inverval)
        nasdaq_long = get_data(tiker=signal_ticker, start=longterm_start_date, end=end_date, which=which, interval = longterm_data_interval)
        
        tqqq = get_data(tiker=long_ticker, start=shortterm_start_date, end=end_date, which=which,interval = shortterm_data_inverval)
        sqqq =  get_data(tiker=short_ticker, start=shortterm_start_date, end=end_date, which=which, interval = shortterm_data_inverval)

        nasdaq = nasdaq[:-1]
        tqqq = tqqq[:-1]
        sqqq = sqqq[:-1]
        nasdaq_long = nasdaq_long[:-1]
        #print(start_date, end_date, nasdaq.shape[0], tqqq.shape[0], sqqq.shape[0])
        
        # add str date (min-level)
        nasdaq = self.convert_time(nasdaq)
        nasdaq_long = self.convert_time(nasdaq_long)
        tqqq = self.convert_time(tqqq)
        sqqq = self.convert_time(sqqq)
        
        # if daily or hourly, you can comment this line to save time.
        nasdaq, tqqq, sqqq = self.match_dfs(nasdaq, tqqq, sqqq)
        
        
        assert  nasdaq.shape[0] == tqqq.shape[0] == sqqq.shape[0]
        
        
        self.short_signal_df = self.convertdata_yfinance(nasdaq)
        self.long_signal_df = self.convertdata_yfinance(nasdaq_long)
        self.long_df = self.convertdata_yfinance(tqqq)
        self.short_df = self.convertdata_yfinance(sqqq)
        
        # adding log ret to asset df
        # WARNING: ret on 15:45 = given a strategy on time point 15:45, return you can get (during 15:45 ~ 16:00)
        self.long_df['log_ret'] = np.log(self.long_df['price'].shift(-1)) - np.log(self.long_df['price'])
        self.short_df['log_ret'] = np.log(self.short_df['price'].shift(-1)) - np.log(self.short_df['price'])
        # replace nan to 0
        self.long_df['log_ret'].replace(np.nan, 0, inplace=True)
        self.short_df['log_ret'].replace(np.nan, 0, inplace=True)
        assert self.long_df.shape[0] == self.short_df.shape[0] == self.short_signal_df.shape[0]
        
        
        # get signal
        self.doublemomentum = DoubleMomentum(self.short_signal_df, self.long_signal_df, shortterm_momentum_settings,longterm_momentum_settings, longterm_data_interval,  verbose)
        
        # converting signal to vector 
        self.signal_df = self.doublemomentum.signal_df # update
        self.signal_df['long_sig'] = np.squeeze(np.array([self.signal_df['doublemo_signal'] == 'long']))
        self.signal_df['short_sig'] = np.squeeze(np.array([self.signal_df['doublemo_signal'] == 'short']))
        
        
        
        # print return 
        self.return_total, self.return_long, self.return_short, self.totals, self.longs, self.shorts = self.compute_comp_return()
        self.total_ret_noncomp, self.long_ret_noncomp, self.short_ret_noncomp = self.compute_noncomp_return()
        self.total_suc, self.long_suc, self.short_suc = self.success_rate()
        # uncomment if you need this info
        # if if_plot:
        #     print(f"total componented return during {start_date} and {end_date} is: ", self.total_ret)
        #     print(f"long componented return during {start_date} and {end_date} is: ", self.return_long)
        #     print(f"short componented return during {start_date} and {end_date} is: ", self.return_short, '\n')

        #     print(f"total non-componented return during {start_date} and {end_date} is: ", self.total_ret_noncomp)
        #     print(f"long non-componented return during {start_date} and {end_date} is: ", self.long_ret_noncomp)
        #     print(f"short non-componented return during {start_date} and {end_date} is: ", self.short_ret_noncomp, '\n')


        #     print(f"total sucess rate during {start_date} and {end_date} is: ", self.total_suc)
        #     print(f"long sucess rate during {start_date} and {end_date} is: ", self.long_suc)
        #     print(f"short sucess rate during {start_date} and {end_date} is: ", self.short_suc)   

    def convert_time(self, yfi_data):
        '''
        
        
        '''
        def convert_(row):
            return row['Date'].to_pydatetime().strftime('%Y-%m-%d-%H-%M') 
        yfi_data['str_time'] = yfi_data.apply(lambda row: convert_(row), axis=1)
        return yfi_data

    def match_dfs(self, df1, df2, df3):
        dfs = [df1, df2, df3]
        all_dates = list(set(list(df1['str_time'].values)))+  list(set(list(df2['str_time'].values))) + list(set(list(df3['str_time'].values)))
        valid_dates = [date for date in all_dates if all_dates.count(date)==3]
        valid_dates = set(valid_dates)
        valid_dates = list(valid_dates)
        
        new_dfs = []
        for df in dfs:
            new_dfs.append(df[df['str_time'].isin(valid_dates)])
        

        return new_dfs[0].sort_values('Date').reset_index(drop=True), new_dfs[1].sort_values('Date').reset_index(drop=True), new_dfs[2].sort_values('Date').reset_index(drop=True)

    
    def convertdata_yfinance(self, yfi_data):
        '''
        use open during eval
        
        '''
        def convert_time(row):
            nyc = timezone('America/New_York')
            return row['Date'].to_pydatetime().astimezone(nyc)
        
        yfi_data['time'] = yfi_data.apply(lambda row: convert_time(row), axis=1)
        yfi_data.rename(columns={'Open':'price'}, inplace=True)
        return yfi_data[['time', 'price']]
    

        
    
    
    def compute_comp_return(self):
        return_totals = []
        return_longs = []
        return_shorts = []
        for i in range(self.long_df.shape[0]): #len(self.tqqq['log_ret'].values[2:])):
            return_long = np.array(self.long_df['log_ret'].values)[:i+1].dot(np.array(self.signal_df['long_sig'])[:i+1])
            return_longs.append(return_long)
            return_short = np.array(self.short_df['log_ret'].values)[:i+1].dot(np.array(self.signal_df['short_sig'])[:i+1])
            return_shorts.append(return_short)
            return_total = np.exp(return_long + return_short)
            return_totals.append(return_total)
        
        return_long = self.long_df['log_ret'].values.dot(self.signal_df['long_sig'].values)
        return_short = self.short_df['log_ret'].values.dot(self.signal_df['short_sig'].values)
        return_total = return_long + return_short
        
        
        return np.exp(return_total), np.exp(return_long), np.exp(return_short) , return_totals, return_longs, return_shorts
    
    def compute_noncomp_return(self):
        
        return_long = np.mean(np.exp(np.multiply(np.array(self.long_df['log_ret'].values), np.array(self.signal_df['long_sig']))))
        return_short = np.mean(np.exp(np.multiply(np.array(self.short_df['log_ret'].values), np.array(self.signal_df['short_sig']))))
        return_total = (return_long + return_short) / 2
        return return_total, return_long, return_short
        
        
        
    def success_rate(self):
        long_arr = np.array(self.long_df['log_ret'].values)
        short_arr = np.array(self.short_df['log_ret'].values)
        try:
            rate_long = (np.array(long_arr > 0).astype(int).dot(self.signal_df['long_sig'].values.astype(int))) / sum(self.signal_df['long_sig'].values)
        except:
            rate_long = 1
        try:
            rate_short = (np.array(short_arr > 0).astype(int).dot(self.signal_df['short_sig'].values.astype(int))) / sum(self.signal_df['short_sig'].values)
        except:
            rate_short = 1
        try:
            total_rate = ((np.array(long_arr > 0).astype(int).dot(np.array(self.signal_df['long_sig']).astype(int))) + (np.array(short_arr > 0).astype(int).dot(np.array(self.signal_df['short_sig']).astype(int))) ) / (sum(self.signal_df['long_sig'])+sum(self.signal_df['short_sig']))
        except:
            total_rate = 1
        return total_rate, rate_long, rate_short
    


    # def __init__(self, shortterm_momentum_settings, longterm_momentum_settings, 
    #              shortterm_start_date, longterm_start_date, end_date, 
    #              signal_ticker, long_ticker, short_ticker, 
    #              shortterm_data_inverval, longterm_data_interval, 
    #              which='Close', verbose=True): 

class RollingBackTest_DoubleMomentum():
    # '''
    # WARINING:
    # for 1m: due to yahoo finance data restriction, must be within the last 30 days
    # - 
    # '''
    def __init__(self, api_setting:APISettings(),
                 shortterm_momentum_settings, longterm_momentum_settings,  
                 start_date, testing_length, gap, shortterm_datainterval, longterm_datainterval,
                 signal_ticker, long_ticker, short_ticker,
                 verbose):
        
        self.start_date = start_date
        self.testing_length = testing_length
        self.gap = gap
        self.signal_ticker = signal_ticker
        self.long_ticker = long_ticker
        self.short_ticker = short_ticker
        self.shortterm_datainterval = shortterm_datainterval
        self.longterm_datainterval = longterm_datainterval
        self.verbose =  verbose
        self.shortterm_momentum_settings =  shortterm_momentum_settings
        self.longterm_momentum_settings = longterm_momentum_settings
        self.api = REST(api_setting.API_KEY_ID, api_setting.SECRET_KEY, api_setting.ENDPOINT)
        
        self.total_rets, self.long_rets, self.short_rets, self.rets_noncomp = self.testing()

    def create_longterm_startdate(self, shortterm_startdate:str, longterm_interval:str):
        # define long term back days
        if longterm_interval in ['15m', '30m']:
            backdays = 29
        elif longterm_interval == '1h':
            backdays = 59
        elif longterm_interval == '1d':
            backdays = 100
        shortterm = datetime.strptime(shortterm_startdate, '%Y-%m-%d')
        longterm = shortterm - timedelta(days=backdays)
        longterm_str = longterm.strftime('%Y-%m-%d')
        return longterm_str
        
        
    def testing(self):
        start_dates, end_dates = self.create_rolling_dates()
        print("start testing...")
        test_returns = []
        long_returns = []
        short_returns = []
        rets_noncomp = []
        total_sucs = []
        for start_date, end_date in tqdm(zip(start_dates, end_dates), total=len(end_dates)):


            backtest = BackTest_Doublemomentum(self.shortterm_momentum_settings, self.longterm_momentum_settings,
                                                start_date, self.create_longterm_startdate(start_date, self.longterm_datainterval), end_date,
                                                self.signal_ticker, self.long_ticker, self.short_ticker,
                                                self.shortterm_datainterval, self.longterm_datainterval, 
                                                verbose=self.verbose)
            test_returns.append(backtest.return_total)
            long_returns.append(backtest.return_long)
            short_returns.append(backtest.return_short)
            rets_noncomp.append(backtest.total_ret_noncomp)
            total_sucs.append(backtest.total_suc)
            # try:
            #     backtest = BackTest_Doublemomentum(self.shortterm_momentum_settings, self.longterm_momentum_settings,
            #                                        start_date, self.create_longterm_startdate(start_date), end_date,
            #                                        self.signal_ticker, self.long_ticker, self.short_ticker,
            #                                        self.shortterm_datainterval, self.longterm_datainterval, 
            #                                        verbose=self.verbose)
            #     test_returns.append(backtest.return_total)
            #     long_returns.append(backtest.return_long)
            #     short_returns.append(backtest.return_short)
            #     rets_noncomp.append(backtest.total_ret_noncomp)
            #     total_sucs.append(backtest.total_suc)
                
            # except:
            #     test_returns.append(1)
            #     long_returns.append(1)
            #     short_returns.append(1)  
            #     rets_noncomp.append(1)
            #     total_sucs.append(0.5)
        
        return  test_returns, long_returns, short_returns, rets_noncomp
        
    
    
    def create_rolling_dates(self):
        start_testing = self.start_date

        nyc = timezone('America/New_York')
        #now = datetime.today().astimezone(nyc)
        days_before = datetime.today() - timedelta(self.testing_length)
        days_before_str = days_before.astimezone(nyc).strftime('%Y-%m-%d')
        calendar = self.api.get_calendar(start=start_testing, end=days_before_str) # get the next closet trading day 
        calender_date_str = [date.date for date in calendar] # .strftime('%Y-%m-%d')
        calender_date_str = calender_date_str[0::self.gap]
        starts = []
        ends = []
        for date in calender_date_str:
            starts.append(date.strftime('%Y-%m-%d'))
            end = date + timedelta(days=self.testing_length)
            ends.append(end.strftime('%Y-%m-%d'))
        
        return (starts, ends)