
import numpy as np; import pandas as pd

def ema(S,N):             #指数移动平均,为了精度 S>4*N  EMA至少需要120周期     alpha=2/(span+1)    
    return pd.Series(S).ewm(span=N, adjust=False).mean().values   

def dif(data):
    later_1day = data[1:]
    before_1day = data[:-1]
    return later_1day - before_1day