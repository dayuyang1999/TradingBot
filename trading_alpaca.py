API_KEY_ID = "yours"
SECRET_KEY = "yours"
ENDPOINT = 'https://paper-api.alpaca.markets'




# document of alpaca api: https://github.com/alpacahq/alpaca-trade-api-python
# transaction cost: https://www.webull.com/pricing

# 200 per minute query limit alpaca has in place.
from alpaca_trade_api.rest import REST, TimeFrame
from alpaca_trade_api.stream import Stream
import alpaca_trade_api as tradeapi

import time
import numpy as np
from datetime import datetime, timedelta
from pytz import timezone


from TradingBot.strategy.momentum import Momentum
import yfinance as yf
from TradingBot.utils.tradebot import RD, EMA
from TradingBot.utils.data import get_data




def sell_everything():
    '''
    focal_ticker:
        - str
    refer to: https://github.com/alpacahq/alpaca-trade-api-python/blob/a9055b9b55b4da9c39d849d21e73af5601fbe832/alpaca_trade_api/rest.py
    '''
    existing_positions = api.list_positions()
    start_time = time.time()
    for position in existing_positions:
        api.submit_order(
            symbol=position.symbol,
            qty = position.qty,
            side='sell',
            type='market',
            time_in_force='day'
        )
        
    ##### double check sell out
    total = 0
    while True:
        if len(api.list_orders(status='open', side='sell')) == 0:
            break
        else:
            time.sleep(0.5)
            total += 1
            assert total < 10
            
    total = 0        
    while True:
        position_lst = api.list_positions()
        if len(position_lst) == 0:
            break
        else:
            time.sleep(0.5)
            total += 1
            assert total < 10
    
    total = 0
    # while True:
    #     try:
    #         assert len(existing_positions) == 0 
    #         break
    #     except:
    #         time.sleep(0.5)
    #         total += 1
    #         assert total < 10
            
            
    # assert len(existing_positions) == 0 
    trans_time = time.time() - start_time
    print(f"Sell everything ||| Trans time:"+"{:.2f} seconds".format(round(trans_time, 2)))
    
    
    
    
def full_sell(focal_ticker):
    '''
    focal_ticker:
        - str
    refer to: https://github.com/alpacahq/alpaca-trade-api-python/blob/a9055b9b55b4da9c39d849d21e73af5601fbe832/alpaca_trade_api/rest.py
    '''
    focal_position = api.get_position(focal_ticker)
    sell_quantity = focal_position.qty
    start_time = time.time()
    api.submit_order(
        symbol=focal_ticker,
        qty = sell_quantity,
        side='sell',
        type='market',
        time_in_force='day'
    )
    
    # double check
    while True:
        if len(api.list_orders(status='open', side='sell')) == 0:
            break
        else:
            time.sleep(0.4)
        
    while True:
        try:
            api.get_position(focal_ticker) # if ==0, not exist error
            time.sleep(0.001)
        except:
            break
    trans_time = time.time() - start_time
    print(f"Sell: {focal_ticker} ||| Quantity: {sell_quantity} ||| Trans time:"+"{:.2f} seconds".format(round(trans_time, 2)))



def full_buy(focal_ticker, bp_portion):
    '''
    balance:
        - float
    focal_ticker:
        - str
    TODO: get_postion function has delayed.....not working
    Attention: Buying power is fluctuating since equity value fluctuate
    '''
    bp = float(api.get_account().buying_power)
    notional = bp*bp_portion
    print(notional, bp)
    # get_qty
    # try:
    #     old_qty = float(api.get_position(focal_ticker).qty)
    # except:
    #     old_qty = 0
    if bp > 1: # 
        start_time = time.time()
        api.submit_order(
            symbol=focal_ticker,
            notional=notional, # sometimes 
            side='buy',
            type='market',
            time_in_force='day'
        )
        while True:
            if len(api.list_orders(status='open', side='buy')) == 0:
                break
            else:
                time.sleep(0.4)
        # # get qty
        # try:
        #     new_qty = float(api.get_position(focal_ticker).qty)
        # except:
        #     new_qty = 0
        # # make sure order complete
        # while True:
        #     if new_qty > old_qty:
        #         break
        #     else:
        #         time.sleep(0.001)
        trans_time = time.time() - start_time
        
        print(f"Buy: {focal_ticker} ||| Ammount: ${bp*bp_portion} ||| Trans time:"+"{:.2f} seconds".format(round(trans_time, 2)))
    
    else:
        pass        
            
def my_submit_order(sig, long_ticker,  short_ticker, bp_portion):
    '''
    run once
        - transact once
    long_signal: 
        - bool
        - if True, 
            - if hold short
                - sell short and buy long asset
            - if hold long
                - nothing to do
    
    long_ticker:
        - str
    '''
    #print(sig)
    # get position quantity
    try:
        short_position = float(api.get_position(short_ticker).qty)
    except:
        short_position = 0
    try:
        long_position = float(api.get_position(long_ticker).qty)
    except:
        long_position = 0
    
    action_lst = []
    # decide operation: sell something, buy something
    # long_sig = signals['long'][-1]
    # short_sig = signals['short'][-1]
    #empty_sig = signals['empty'][-1]
    
    
    if (short_position==0) and (long_position==0): # empty
        if sig == 'long':# buy long
            action_lst.append('buy long')
        elif sig == 'short':
            action_lst.append('buy short')

    else:
        if short_position > 0: # consider hold or sell short
            if sig != 'short': # sell short
                action_lst.append('sell short')
                if sig == 'long':
                    action_lst.append('buy long')
        elif long_position > 0: # consider hold or sell long
            if sig != 'long':
                action_lst.append('sell long')
                if sig == 'short':
                    action_lst.append('buy short')
    
    # execution
    for act in action_lst:
        if act == 'buy long':
            full_buy(long_ticker, bp_portion)
        elif act == 'buy short':
            full_buy(short_ticker, bp_portion)
        elif act == 'sell long':
            full_sell(long_ticker)
        elif act == 'sell short':
            full_sell(short_ticker)
            
            
           
    time.sleep(0.4)          
    # renew position qty    
    try:
        short_position = float(api.get_position(short_ticker).qty)
        time.sleep(0.4) 
    except:
        short_position = 0
    try:
        long_position = float(api.get_position(long_ticker).qty)
    except:
        long_position = 0
    # must be each of the case
    # error : long position 0, short position 0, long signal 0
    print(f"Current sig: {sig}. Acted: {action_lst}. HOLD at {datetime.today().astimezone(nyc)}: long position {long_position}, short position {short_position} \n")

    # you cannot hold long and short at the same time.
    if ((long_position>0) and (short_position>0)):
        print("Warining: hold long and short at the same time.")
        sell_everything()
        while True:
            if not ((long_position>0) and (short_position>0)):
                break
            else:
                print("Warining: hold long and short at the same time.")
                time.sleep(5)
    assert (not ((long_position>0) and (short_position>0)))

    
    



def convertdata_yfinance(yfi_data):
    '''
    use 'Close' data in Live
    '''
    def convert_time(row):
        nyc = timezone('America/New_York')
        return row['Date'].to_pydatetime().astimezone(nyc)
    
    yfi_data['time'] = yfi_data.apply(lambda row: convert_time(row), axis=1)
    yfi_data.rename(columns={'Close':'price'}, inplace=True)
    return yfi_data[['time', 'price', 'pct_change']]

####
# 
#
#
#
#
########
# 
#
#
#
#
####

def daily(trade_freq, signal_ticker, long_ticker, short_ticker, bp_portion, trade_extended_hour: bool):
    '''
    Intro:
        - should stay in this function during the trading hours
        - once enter the `daily` function, it will only get out once the time is ended or any security wall has been triggered
    
    
    
    '''
    # check account status
    account = api.get_account()
    assert account.status == 'ACTIVE'
    # get today
    #now = datetime.today().astimezone(nyc)
    today_str = datetime.today()+ timedelta(1)
    today_str = today_str.astimezone(nyc).strftime('%Y-%m-%d')
    if trade_extended_hour:
        market_open = now.replace(
            hour=4,
            minute=0,
            second=0
        )
        market_open = market_open.astimezone(nyc)   
        market_close = now.replace(
            hour=20,
            minute=0,
            second=0
        )
        market_close = market_close.astimezone(nyc)
    else:
        # get market open/close datetime 
        market_open = now.replace(
            hour=calendar.open.hour,
            minute=calendar.open.minute,
            second=0
        )
        market_open = market_open.astimezone(nyc)
        market_close = now.replace(
            hour=calendar.close.hour,
            minute=calendar.close.minute,
            second=0
        )
        market_close = market_close.astimezone(nyc)
    # get current datetime
    #current_dt = datetime.today().astimezone(nyc)
    # how much the time has pass since market open
    #since_market_open = current_dt - market_open
    # how much the time remain before market close
    #remain_market_open = market_close - current_dt
    if trade_freq == '1m':
        seconds_per_turn = 60
        time_delta = 5
    if trade_freq == '5m':
        seconds_per_turn = 60*5
        time_delta = 5
    if trade_freq == '1h':
        seconds_per_turn = 60*60
        time_delta = 100
        
        
    # today's start buying power
    daily_start_all_value = float(api.get_account().equity)
    old_length_of_price = 0
    
    suspend_secs = 5 # suspend for a loop try
    
    
    #### trading loop
    while True:
        start_time = time.time()
        # get signal
        
        while True:
            try:
                days_before = datetime.today() - timedelta(time_delta) # 5 
                data_start_date = days_before.astimezone(nyc).strftime('%Y-%m-%d') # to make sure EMA is good enough, need to trace back at least `fast_smooth_factor` datapoints
                df = get_data(tiker=signal_ticker, start = data_start_date, end=today_str, which='Close', interval=trade_freq, premarket=True)
                df = df[:-1] # remove the last line (its the varying live price, see introduction of yfinance data in README)
                length_of_price = df.shape[0]
                lastdata_timestamp = df.iloc[-1, 0]
                break
            except:
                print("Getting data meets error, sleep 5 seconds and try again.")
                time.sleep(5)
                
        
        if length_of_price > old_length_of_price: # get updated price info
            print('Latest data point at:', lastdata_timestamp)
            # formulate df 
            new_df = convertdata_yfinance(df)
            # get current signal
            momentum = Momentum(signal_df=new_df, momentum_settings=Momentum_settings(), verbose=False, time_restrictive=True)
            sigs = momentum.signal_df['signal'].values[-1] # a string

    
            my_submit_order(sigs, long_ticker, short_ticker, bp_portion)
            old_length_of_price = length_of_price
            time.sleep(0.5)
        
        current_dt = datetime.today().astimezone(nyc)
        #since_market_open = current_dt - market_open
        remain_market_open = market_close - current_dt
        remain_market_open = remain_market_open.total_seconds()
        
        ##### Security Wall ##### 
        
        ##### time out
        #print('remain trade time today:', remain_market_open.seconds)
        if remain_market_open <= 20:
            sell_everything()
            print(f"############### Trade at date {today_str} ends ##############")

            break
        
        
        ##### Loss
        # once loss 10%, stop trading today
        all_value = float(api.get_account().equity)
        if all_value/daily_start_all_value < (1-0.1): # max loss = 10%
            break
 
        
        ############################
        
        #### time helper
        if (suspend_secs - (time.time() - start_time)) > 0:
            time.sleep(suspend_secs - (time.time() - start_time)) # make sure suspend 5 seconds 







####
# 
#
#
#
#
####
####
# 
#
#
#
#
####
    
class Momentum_settings:
    '''
    if you found it is more likely to enter "long stage"
        - you should set higher threshold for short, but lower threshold for long
    '''
    long_buy_thres = 0.0
    long_sell_thres = 0.0
    short_buy_thres = 0.0
    short_sell_thres = 0.0
    slow_smooth_factor = 200
    # long-term indicator as ema smooth factor
    # if larger, slower track of current price, more consistent
    fast_smooth_factor = 12 # price smooth factor for computing momentum
    #restrictive_hours = [4, 5, 6 ,7, 8, 17, 18, 19, 20]
    restrictive_hours = [4]
    restrictive_mins = []

    
####
# 
#
#
#
#
########
# 
#
#
#
#
####

if __name__ == '__main__':
    api = REST(API_KEY_ID, SECRET_KEY, ENDPOINT)
    
    # hyperparam
    trade_freq = '5m' # change this 
    signal_ticker = 'TQQQ'
    long_ticker = 'TQQQ'
    short_ticker = 'SQQQ'
    bp_portion = 1/4
    trading_extended_hour = True
    
    
    
    
    
    
     
    
    if trade_freq == '1m':
        seconds_per_turn = 60
    if trade_freq == '5m':
        seconds_per_turn = 60*5
    if trade_freq == '15m':
        seconds_per_turn = 60*15
    if trade_freq == '1h':
        seconds_per_turn = 60*60
    
    while True:
        '''
        end trading at 16:05
        start trading at 04:59
        '''
        nyc = timezone('America/New_York')
        now = datetime.today().astimezone(nyc)
        today_str = datetime.today().astimezone(nyc).strftime('%Y-%m-%d')
        
        # if today is a trading day.. return today
        calendar = api.get_calendar(start=today_str, end=today_str)[0] # get the next closet trading day 
        
        # judge if today is a trading day
        is_today_tradingday = (today_str == datetime.strptime(str(calendar.date), '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d'))
        
        # get market open/close datetime 
        market_open_time = now.replace(
            hour=calendar.open.hour,
            minute=calendar.open.minute,
            second=0
        )
        market_open_time = market_open_time.astimezone(nyc)
        market_close_time = now.replace(
            hour=calendar.close.hour,
            minute=calendar.close.minute,
            second=0
        )
        market_close_time = market_close_time.astimezone(nyc)
        
        # get extended time
        extended_market_open_time =  now.replace(
            hour=4,
            minute=0,
            second=0
        )
        extended_market_close_time =  now.replace(
            hour=20,
            minute=0,
            second=0
        )
        
        
        if trading_extended_hour:
            since_market_open = now - extended_market_open_time
            since_market_open = since_market_open.total_seconds()
            remain_market_open = extended_market_close_time - now # seconds
            remain_market_open = remain_market_open.total_seconds()
        else:
            # how much the time has pass since market open
            since_market_open = now - market_open_time # seconds
            since_market_open = since_market_open.total_seconds()
            # how much the time remain before market close
            remain_market_open = market_close_time - now # seconds
            remain_market_open = remain_market_open.total_seconds()
            
        # if trading time
        # start before open, stop before close, avoid first 30 min for extended hours
        # if trading_extended_hour:
        #     is_trading_running =  (since_market_open > 60*30) and (remain_market_open > 60*5) #(now >= market_open_time) and (now <= market_close_time) and (remain_market_open.seconds // seconds_per_turn > stop_before_close) and (since_market_open.seconds // seconds_per_turn >= stop_after_open)
        # else:
        is_trading_running =  (since_market_open > 60*1) and (remain_market_open > 60*3)

        if is_today_tradingday and is_trading_running:
            daily(trade_freq = trade_freq, signal_ticker=signal_ticker, long_ticker=long_ticker, short_ticker=short_ticker, bp_portion=bp_portion, trade_extended_hour=trading_extended_hour) 
        else:
            time.sleep(10)
            print(f"Sleep at {now}...Waiting for market open...\n")
   