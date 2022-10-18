from .__main__ import Strategy
from array import array
from .computation import dif, ema
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np


class Aroon_settings:
    aroon_up_i = 9
    aroon_down_i = 8

    
class Aroon(Strategy):
    def __init__(self, signal_price, long_asset_prices, if_plot, aroon_settings:Aroon_settings()) -> None:
        '''
        Arron
            - 
        
        signal_price_df: 
            - dataframe 
            

        
        '''
        super().__init__('arron')
        self.aroon_settings = aroon_settings
        self.if_plot = if_plot
        self.signal_price = signal_price
        self.long_asset_prices = long_asset_prices
    
    
    def create_signal(self):
        df = pd.DataFrame({'Close':self.signal_price})
        i = 0
        df['aroon_up'] = df.apply(lambda row: self.arron_up(self.aroon_settings.aroon_up_i, df), axis=1)
        i = 0
        df['aroon_down'] = df.apply(lambda row: self.arron_down(self.aroon_settings.aroon_down_i, df), axis=1)
        
        
        
        
    
    def aroon_up(self, aroon_i, df):
        global i
        i = i + 1 
        if ( i > aroon_i ):
            t = i - df['Close'][i-aroon_i:i].idxmax()
            return (t/aroon_i)*100
        else:
            return 0


    def aroon_down(self, aroon_i, df):
            global i
            i = i + 1
            if(i>aroon_i):
                t = i - df['Close'][i-aroon_i:i].idxmin()
                return (t/aroon_i)*100
            else:
                return 0