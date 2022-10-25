import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
#from tradebot1 import *
#import backtrader as bt
import warnings
warnings.filterwarnings("ignore")

import yfinance as yf
from .tradebot import EMA, RD, MA


def get_data(tiker='^IXIC', start="2022-05-05", end="2022-05-06", which='Close', interval='1m', premarket=False):
    '''
    get_data from yahoo finance
    
    # Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
    # Valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
    # see https://github.com/ranaroussi/yfinance/blob/9eef951acc70121e65825ad25e7afd2edd4c3e4b/yfinance/multi.py
    '''
    def reformulate_date(df):
        df.columns = df.columns.map(''.join)
        df = df.rename_axis('Date').reset_index()
        return df
    data = yf.download(tickers = tiker, start=start, end=end, interval = interval, progress=False, prepost=premarket)
    data['pct_change'] = data[which].pct_change()
    data['log_ret'] = np.log(data[which].shift(-1)) - np.log(data[which])
    data = reformulate_date(data)
    #print("most recent date is ", data.iloc[-1, 0])
    return data