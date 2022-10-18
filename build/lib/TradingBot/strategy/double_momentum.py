from .momentum import Momentum
from .__main__ import Strategy
from array import array
from .computation import dif, ema
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from pytz import timezone
from datetime import datetime, timedelta

from copy import deepcopy

class DoubleMomentum(Strategy):
    '''
    - trading using short term momentum(min) but also considering long term momentum(day)
    
    '''
    def __init__(self, shortterm_signal_df:pd.DataFrame, longterm_signal_df:pd.DataFrame, shortterm_momentum_settings, longterm_momentum_settings, longterm_data_interval, verbose=True):
        '''
        prices :
            - pandas dataframe, at least need two variables: timestamp , Close price named ['Close']
            - prices = signal prices (IXIC)
            - long asset: may not be TQQQ
            - short asset: can only be SQQQ
        '''
        super().__init__('doublemomemtum')
        self.big_momemtum_setting = longterm_momentum_settings
        self.small_momentum_setting = shortterm_momentum_settings
        self.verbose = verbose
        self.shortterm_signal_df = shortterm_signal_df
        self.longterm_signal_df = longterm_signal_df
        self.longterm_data_interval = longterm_data_interval

        
        
        # create momentum
        self.shortterm_momentum = Momentum(self.shortterm_signal_df, shortterm_momentum_settings, False)
        self.longterm_momentum = Momentum(self.longterm_signal_df, longterm_momentum_settings, False)
        
        # obtain signal df
        self.short_signal_df = self.shortterm_momentum.signal_df
        self.original_signal_df = deepcopy(self.short_signal_df)
        self.long_signal_df = self.longterm_momentum.signal_df
        
        # obtain final
        self.signal_df = self.double_momentum()
        
        # if verbose
        if verbose:
            self.plot_strategy()
            self.plot_original()
    
    def plot_strategy(self):
        figure_size  = (20, 10)
        fig, ax = plt.subplots(figsize=figure_size)
        ax.plot(self.signal_df['price'], label="signal price")
        #if emas != None:
        #ax.plot(self.signal_df['ema'], label=f'ema{self.momemtum_settings.ema_smooth_factor} of signal price')
        # print long
        ax.vlines(x= np.array(self.signal_df[self.signal_df['doublemo_signal'] == 'long'].index), 
                  ymin=np.min(self.signal_df['price']), 
                  ymax=np.max(self.signal_df['price']), 
                  color='g', linestyle='-.')
        # print short
        ax.vlines(x= np.array(self.signal_df[self.signal_df['doublemo_signal'] == 'short'].index), 
                  ymin=np.min(self.signal_df['price']), 
                  ymax=np.max(self.signal_df['price']), 
                  color='r', linestyle='-.')
        ax.title.set_text('Double Momentum')
        ax.legend()
        
        
    def plot_original(self):
        figure_size  = (20, 10)
        fig, ax = plt.subplots(figsize=figure_size)
        ax.plot(self.original_signal_df['price'], label="signal price")
        #if emas != None:
        #ax.plot(self.signal_df['ema'], label=f'ema{self.momemtum_settings.ema_smooth_factor} of signal price')
        # print long
        ax.vlines(x= np.array(self.original_signal_df[self.original_signal_df['signal'] == 'long'].index), 
                  ymin=np.min(self.original_signal_df['price']), 
                  ymax=np.max(self.original_signal_df['price']), 
                  color='g', linestyle='-.')
        # print short
        ax.vlines(x= np.array(self.original_signal_df[self.original_signal_df['signal'] == 'short'].index), 
                  ymin=np.min(self.original_signal_df['price']), 
                  ymax=np.max(self.original_signal_df['price']), 
                  color='r', linestyle='-.')
        ax.title.set_text('Single Momentum')
        ax.legend()
        
        

        
    def double_momentum(self):
        '''
        according to long term momentum signal, edit short term momentum signal
            - edit will make directly on self.shortterm_momentum.signal_df
        '''
        # adding new var
        self.short_signal_df['daytime'] = self.short_signal_df.apply(lambda row: self.convert_str(row), axis=1)
        self.long_signal_df['daytime'] = self.long_signal_df.apply(lambda row: self.convert_str(row), axis=1)
        
        # 
        self.short_signal_df['doublemo_signal'] = self.short_signal_df.apply(lambda row: self.convert_signal(row), axis=1)
        return self.short_signal_df
    
    def convert_signal(self, row):
        daytime = row['daytime']
        shorterm_sig = row['signal']
        #print(daytime, self.long_signal_df['daytime'].values[-1])
        longterm_sig = self.long_signal_df[self.long_signal_df['daytime'] == daytime]['signal'].values
        
        #print(longterm_sig)
        #print(longterm_sig, shorterm_sig)
        if longterm_sig != shorterm_sig:
            return 'empty'
        else:
            return shorterm_sig
        
        
    def convert_str(self, row):
        '''
        Can only be used when:
            - longterm = day
            - shortterm = intraday
        '''
        if self.longterm_data_interval == '1d':
            return row['time'].strftime('%Y-%m-%d') 
        elif self.longterm_data_interval == '1h':
            return row['time'].strftime('%Y-%m-%d-%H')
        else:
            raise ValueError


            
            
            
                
        
        # def create_signal_with_time(price_df, momentum, momentum_name:str):
        #     nyc = timezone('America/New_York')
        #     def add_str_time(row):
        #         return row['time'].to_pydatetime().astimezone(nyc).strftime('%Y-%m-%d')
            
        #     signal_df = pd.DataFrame({'time':price_df['Date'][1:-1], 
        #                             'long':momentum.signals['long'],
        #                             'short':momentum.signals['short'],
        #                             'empty':momentum.signals['empty']})
        #     signal_df['time_str'] = signal_df.apply(lambda row: add_str_time(row), axis=1)
        #     return signal_df
        
        
        
        
            
        

        
        
        
        
    
    