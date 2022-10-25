#from webbrowser import MacOSX
from .__main__ import Strategy
from array import array
from .computation import dif, ema
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from datetime import datetime, timedelta
from pytz import timezone

from distfit import distfit

class Momentum_settings:
    '''
    Intro:
        - An example of momentum settings
    if you found it is more likely to enter "long stage"
        - you should set higher threshold for short, but lower threshold for long
    '''
    long_buy_thres = 0 # percentage * 100
    long_sell_thres = 0
    short_buy_thres = 0
    short_sell_thres = 0
    slow_smooth_factor = 5 # long-term indicator as ema smooth factor
    # if larger, slower track of current price, more consistent
    fast_smooth_factor = 2
    #fast_smooth_factor = 2 # price smooth factor for computing momentum
    
    
    
    

class Momentum(Strategy):
    '''
    ema enhanced momentum strategy
    '''
    def __init__(self, signal_df, momentum_settings, verbose=False, time_restrictive = False):
        '''
        Purpose:
            input data, output signal(long? short? empty?) to the corresponding **time period** 
                - **time period** represents as its start time point, datetime.datetime
        
        Args:
            signal_df: contains 2 columns:
                - ['time']: datetime.datetime
                - ['price']: price wrt the time point
            
            momentum_setting:
        
        WARINING:
            - when backtest, price = the price of corresponding timepoint (use Open)
            - when real-time, price = the price of corresponding timepoint + 1 interval (use Close)
        '''
        
        super().__init__('momentum')
        self.time_restrictive = time_restrictive
        self.signal_df = signal_df
        self.momentum_settings = momentum_settings
        self.verbose = verbose
        
        ####### main process
        # create long term indicator
        self.long_term_momentum()
        #self.signal_df['ema']  = self.long_term_momentum()
        # create short term momentum 
        
        self.compute_momentum(self.momentum_settings.fast_smooth_factor) ## will add new col: smoothed_pct_change

        
        # create signal
        self.create_signal() # will add one more column into signal_df['signal']
       
        
        if verbose:
            self.plot_strategy()
            

    def obtain_stat_filer_boundary(self, thres, sig_values):
        '''
        sig_values: array
        '''
        dist = distfit(alpha=(1-thres)/2, smooth=4)

        dist.fit_transform(sig_values, verbose=0)
        # dist.plot(sig, figsize=(10, 3))
        # # Search for best theoretical fit on your empirical data

        # plt.figure(figsize=(10, 3))
        # plt.plot(sig)
        # plt.axhline(dist.model['CII_min_alpha'], linestyle='--', c='r', label='CII low')
        # plt.axhline(dist.model['CII_max_alpha'], linestyle='--', c='r', label='CII high')
        return dist.model['CII_min_alpha'], dist.model['CII_max_alpha']
    
    def plot_strategy(self):


        figure_size  = (20, 10)
        fig, ax = plt.subplots(figsize=figure_size)

        ax.plot(self.signal_df['price'], label="signal price")
        #if emas != None:
        ax.plot(self.signal_df['ema'], label=f'ema{self.momentum_settings.slow_smooth_factor} of signal price')
        # print long
        ax.vlines(x= np.array(self.signal_df[self.signal_df['signal'] == 'long'].index), 
                  ymin=np.min(self.signal_df['price']), 
                  ymax=np.max(self.signal_df['price']), 
                  color='g', linestyle='-.')
        # print short
        ax.vlines(x= np.array(self.signal_df[self.signal_df['signal'] == 'short'].index), 
                  ymin=np.min(self.signal_df['price']), 
                  ymax=np.max(self.signal_df['price']), 
                  color='r', linestyle='-.')
        
        ax.legend()
        #pass
    
    
    def convert_time(self, row, colname='Date'):
        nyc = timezone('America/New_York')
        return row[colname].to_pydatetime().astimezone(nyc)
    

            
            

        
        
    def long_term_momentum(self):
        '''
        use ema20 as default for minites trade
        '''
        #return ema(self.signal_df['price'], self.momentum_settings.slow_smooth_factor)
        self.signal_df['ema'] = self.signal_df['price'].ewm(span=self.momentum_settings.slow_smooth_factor, min_periods=self.momentum_settings.slow_smooth_factor).mean()
    
    
    def compute_momentum(self, dif_sf, focal_row_nums=[]):
        '''
        1st differential
        
        - possible improvement:
            - 1st differential is related to the abosolute index value
            - so divided by index value  / self.prices[-1]
        '''
        #self.signal_df['smoothed_dif'] = self.signal_df['price'].diff().ewm(span=self.momentum_settings.fast_smooth_factor, min_periods=self.momentum_settings.fast_smooth_factor).mean()
        self.signal_df['smoothed_pct_change'] = self.signal_df['pct_change'].ewm(span=self.momentum_settings.fast_smooth_factor, min_periods=self.momentum_settings.fast_smooth_factor).mean()
        
        
        ma_dif = np.nan_to_num(self.signal_df['smoothed_pct_change'].values, nan=0)
        #assert len(dif_ma) == self.signal_df.shape[0] - 1
        
        # self.buy_lower_thres, self.buy_upper_thres = self.obtain_filer_boundary(self.momentum_settings.buy_thres, ma_dif)
        # self.sell_lower_thres, self.sell_upper_thres = self.obtain_filer_boundary(self.momentum_settings.sell_thres, ma_dif)

        if self.verbose:
            
            # #if you want to plot prices in a seperated plot, uncomment it.
            # fig, ax = plt.subplots(figsize=figure_size)
            # ax.plot(ori_data, label="Price")
            
            # if len(focal_row_nums) != 0:
            #     for focal_row_num in focal_row_nums:
            #         ax.vlines(ymin=np.min(ori_data), ymax=np.max(ori_data), x=focal_row_num, color='r', linestyle='-.')
            # ax.legend()
            
            figure_size  = (20, 10)
            fig, ax = plt.subplots(figsize=figure_size)
            #ax.plot(dif, label="dif: divergence")
            ax.hlines(xmin=0, xmax=ma_dif.shape[0], y = 0, color='r', linestyle='-.')
            #assert dif.shape[0] == ori_data.shape[0] == ma_dif.shape[0]
            for focal_row_num in focal_row_nums:
                ax.vlines(ymin=np.min(ma_dif), ymax=np.max(ma_dif), x=focal_row_num, color='r', linestyle='-.')
        
            ax.axhline(self.momentum_settings.long_buy_thres/100, linestyle='--', c='g', label='buy long thres')
            ax.axhline(-self.momentum_settings.short_buy_thres/100, linestyle='--', c='g', label='buy short thres')
            ax.plot(ma_dif, label=f"MA {self.momentum_settings.fast_smooth_factor} of percentage change: denoised(smoothed) divergence")

            #ax.plot(ema_ema, label="EMA of EMA")
            #ax.plot(macd, label="macd")
            ax.legend()
        
        


    def create_signal(self):
        '''
        dependes on previous states
        '''
        
        # no data for first differential for 1st data point

        signal_col = []
        prev_price = 0
        for i, row in self.signal_df.iterrows():
            price = row['price']
            pct_change = row['smoothed_pct_change']
            ema = row['ema']
            time = row['time']
            
            if i != 0:
                previous_state = signal_col[i-1]
     
            else:
                previous_state = 'empty'
            
            
            if not self.time_restrictive:
                if (pct_change == np.nan) or (ema == np.nan): 
                    cur_sig = 'empty'
                else:
                    if previous_state != 'empty': # hold in prev state
                        if previous_state == 'short': # if prev short
                            if (pct_change*100 > self.momentum_settings.long_buy_thres) and (price > ema):
                                cur_sig = 'long' # reverse
                            elif pct_change*100 > - self.momentum_settings.short_sell_thres: # -1 > -2
                                cur_sig = 'empty'
                            else:
                                cur_sig = previous_state
                        elif previous_state == 'long':
                            if (pct_change*100 < - self.momentum_settings.short_buy_thres) and (price < ema): # reverse
                                cur_sig = 'short'
                            elif pct_change*100 < self.momentum_settings.long_sell_thres: # sell
                                cur_sig = 'empty'
                            else:
                                cur_sig = previous_state
                    
                    else: # prev is empty
                        if (pct_change*100 > self.momentum_settings.long_buy_thres) and (price > ema): # large enough to long
                            cur_sig = 'long'
                        elif (pct_change*100 < - self.momentum_settings.short_buy_thres) and (price < ema):
                            cur_sig = 'short'
                        else:
                            cur_sig = 'empty'
                    
            else: # if time restrictive
                if (dif == np.nan) or ((int(time.strftime('%H')) in self.momentum_settings.restrictive_hours)): 
                    cur_sig = 'empty'
                else:
                    if previous_state != 'empty': # hold in prev state
                        if previous_state == 'short': # if prev short
                            if (pct_change*100 > self.momentum_settings.long_buy_thres) and (price > ema):
                                cur_sig = 'long' # reverse
                            elif pct_change*100 > - self.momentum_settings.short_sell_thres: # -1 > -2
                                cur_sig = 'empty'
                            else:
                                cur_sig = previous_state
                        elif previous_state == 'long':
                            if (pct_change*100 < - self.momentum_settings.short_buy_thres) and (price < ema): # reverse
                                cur_sig = 'short'
                            elif pct_change*100 < self.momentum_settings.long_sell_thres: # sell
                                cur_sig = 'empty'
                            else:
                                cur_sig = previous_state
                    
                    else: # prev is empty
                        if (pct_change*100 > self.momentum_settings.long_buy_thres) and (price > ema): # large enough to long
                            cur_sig = 'long'
                        elif (pct_change*100 < - self.momentum_settings.short_buy_thres) and (price < ema):
                            cur_sig = 'short'
                        else:
                            cur_sig = 'empty'
                
                
            
            
            ### updates
            signal_col.append(cur_sig)
        
        assert len(signal_col) == self.signal_df.shape[0]
        
        self.signal_df['signal'] = signal_col
        
        
                    
                    
                
    # decreciated
            
        
    # def create_signal_row(self, row):
    #     '''
    #     if not depends on previous states
    #     '''
    #     price = row['price']
    #     pct_change = row['smoothed_pct_change']
    #     ema = row['ema']
    #     time = row['time']
        
    #     if self.only_morning == False:
    #         if dif == np.nan:
    #             return 'empty'
    #         else:
    #             if dif > self.buy_upper_thres and price > ema: # long
    #                 return 'long'
    #             elif dif < - self.buy_lower_thres and price < ema:
    #                 return 'short'
    #             else:
    #                 return 'empty'
    #     else:
    #         if dif == np.nan:
    #             return 'empty'
    #         else:
    #             if dif > self.upper_thres and price > ema and int(time.strftime('%H')) < 10: # long
    #                 return 'long'
    #             elif dif < -self.lower_thres and price < ema and int(time.strftime('%H')) < 10:
    #                 return 'short'
    #             else:
    #                 return 'empty'
    
    # def  create_signal_row(self, row):
            
        # emas = self.long_term_indicator
        # prices = self.signal_df['Close'].values[1:]
        # times = self.signal_df['pydate'].values[1:]
        # emas = emas[1:]
        
        # # create signal
        # delta_diver = self.differentials
        # long = []
        # short = []
        # empty = []
        # for i, value in enumerate(delta_diver):
            
        #     if i==0: # when time =0, only consider when to buy
        #         if value > self.upper_thres: # buy long 
        #             long.append(1)
        #             short.append(0)
        #             empty.append(0)
        #         elif value < - self.momentum_settings.short_buy_thres: # buy short
        #             long.append(0)
        #             short.append(1)
        #             empty.append(0)
        #         else:
        #             long.append(0)
        #             short.append(0)
        #             empty.append(1)
        #     else: # when time >0, obtain prev status and consider current operation
        #         if long[i-1] == 1: # if prev hold long, consider when to sell long
        #             if value < self.momentum_settings.long_sell_thres: # if <= long_sell_thres, sell
        #                 if value < - self.momentum_settings.short_buy_thres: # if buy short instead? < -thres
        #                     long.append(0)
        #                     short.append(1)
        #                     empty.append(0)
        #                 else:
        #                     long.append(0)
        #                     short.append(0)
        #                     empty.append(1)   
        #             else: # continue to hold
        #                 long.append(1)
        #                 short.append(0)
        #                 empty.append(0)
                        
        #         elif short[i-1] == 1: # if prev hold short
        #             if value > - self.momentum_settings.short_sell_thres: # sell short
        #                 if value > self.upper_thres: # buy long instead?
        #                     long.append(1)
        #                     short.append(0)
        #                     empty.append(0)
        #                 else:
        #                     long.append(0)
        #                     short.append(0)
        #                     empty.append(1)
        #             else: # continue to hold
        #                 long.append(0)
        #                 short.append(1)
        #                 empty.append(0)
                
        #         elif empty[i-1] == 1: # prev did not hold anything
        #             if value > self.upper_thres:
        #                 long.append(1)
        #                 short.append(0)
        #                 empty.append(0)
        #             elif value < - self.lower_thres:
        #                     long.append(0)
        #                     short.append(1)
        #                     empty.append(0)
        #             else:
        #                 long.append(0)
        #                 short.append(0)
        #                 empty.append(1)

        #     if emas[i] > prices[i]: # go down trend
        #         if long[i] == 1:
        #             long[i] = 0
        #             empty[i]=1
        #     elif emas[i] <= prices[i]:
        #         if short[i] == 1:
        #             short[i] = 0
        #             empty[i]=1
                             
                
        
        # assert len(prices) == len(emas) == len(long)
        # for long_, short_, empty_ in zip(long, short, empty):
        #     assert ((long_ + short_ + empty_) == 1)

        # signals = {'long':long, 'short':short, 'empty':empty, 'signal_time':times}
        
        
        
        # return signals # last signal is useless   