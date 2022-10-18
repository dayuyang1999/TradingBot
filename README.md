:warning: Trading stock carries a high level of risk, and may not be suitable for all investors. Past performance is not indicative of future results. The high degree of leverage can work against you as well as for you. Before deciding to invest in stock market you should carefully consider your investment objectives, level of experience, and risk appetite. The possibility exists that you could sustain a loss of some or all of your initial investment and therefore you should not invest money that you cannot afford to lose. You should be aware of all the risks associated with stock trading, and seek advice from an independent financial advisor if you have any doubts.

:warning: One more thing I would like to emphasize that because my motivation is more on demonstrating how to build an algorithm trading platform by your own. Earning money is not guaranteed. You are more than welcome to take this repo as a reference point and add more stock prediction related ideas to improve it. Enjoy.

# To-dos

- support aftermarket data and merge it to `yfinance`


# TradingBot

An algorithm stock trading tool ( :construction: under constructuion) that can achieve:
- A universal data feed design
- A universal format of stock trading strategy design (refer to `./strategy/__main__.py`)
- Backtesting 
- Live trading (support Alpaca API for now)


# Usage

1. Installation, refer to [Installation Instruction](/usa/dayu/investment/TradingBot/project-description.md)
2.  Replacing all the `API_KEY` to your own.
3.  For live trading, run:

```
python3 TradingBot.py
```

How to use this module? Basically you need:
- data source
- a strategy
- backtesting
- (If backtesting works good), try live trading on paper at first
- live trading on your real money



## Data

Data with minimum delay is the first prerequisite for trading on stock market. So far, I have tried [Alpaca](https://github.com/alpacahq/alpaca-trade-api-py) and [YahooFinance](https://github.com/ranaroussi/yfinance). Eventually I decided to use `yfinance`.

### Understanding data of `yfinance`

#### Speed
- The minimum interval is `1min`
- Delay is about 1~2 seconds 

#### Data format

What is a row retrieving from `yfinance` means? You may not truely understand. Here is a snapshot.

![](https://cdn.mathpix.com/snip/images/XqdHjVJirKk0uXRt-K17jPwpbkvt-Ivgr9fuJAr1ehQ.original.fullsize.png)

Taking the 2nd last row as an example:
- 15:45 Open=10873.5, Close=10873.6,  Low = 10832.45, High=10876.14, 

This means:
- this row is data from 15:45:00 ~ 15:59:59
- at 16:00:00, `yfinance` will refresh a row for 15:45, (2nd last shown here, that is why we should took `Close` data as the latest datapoint.)
- `Close` of `row 15:45` = price at data point 16:00:00.
- `Open` of `row 15:45` = price at data point 15:45:00


## Strategy

The format of a `Strategy` can be refered to `./strategy/__main__.py`. Basically, Strategy is a Python object that take data as input, creating a signal pandas DataFrame that contains two columns: time and signal. where `signal` for each corresponding datapoint is a str type in any of these three: (empty, long, short).

### Thinking

Here I recorded some random thoughts of mine that helps me designing strategy.

#### From Finance
- The trading clock should not follow the "natural clock". The major reason is the "pattern of trading" is very likely to be the same for morning, noon, and afternoon(M shape on "number of trades"). Please see [this paper](/reference/finance/Ane_Geman_on_trading_time_and_normality_JF_2000.pdf)
and [my data analysis](/reference/finance/trading_time_analysis.pdf).
  - If the trading strategy is "natural-clock" strategy, at least we should set 3 different trading pattern for different time span.


#### From Statistics
- we are trying to maximizing the conditional probability $\mathbf{P}(\text{win} | \text{Given something...})$. The `Given something` is our signal source.
- We do not need to have a positive Expectation to win, see [Martingale](https://en.wikipedia.org/wiki/Martingale_(probability_theory))


#### From Experience 
- Almost all the ``indicators" in the stock market are momentum indicators (MACD, EMA, RSI, Bollinger Bands, ...). If you follow any of this, your trading strategy is called "Momentum" strategy.

but their assumption is different. Some of them (MACD, EMA) is based on the assumption "if price is rising, then the price will continue rising for a while". I call them "positive momentum indicator". Some of them (RSI, Bollinger Bands) are, on the contracy, assuming "if price is going high, then the price will more likely to drop down". I call them "negative momentum indicator". Both of their assumption I think are correct.


- Momentum strategy is promising to win. The reason is "Momentum" will always exist as long as some people in the market believe momentum (and it is human nature to buy something that is continuously rising for now.). However, the key is:
  - When to buy? (if too early, may be fooled by many noise signals. if too late, the momentum may have ended and inverse, which causes you lose more!)
  - When to sell?
  - What is the signal? (There are tons of default indicators in the market. Personally speaking, I did not believe any of them. I'd rather build my own momentum indicator which maintain enough flexibility, or degree of freedom, to fit the focal trading patterns)


- after(extended) market data is equally important. If we do not have them, the momentum strategy bears high risk in the morning.
  - It is like to gamble: "price of after market rise, price of the morning will rise as well".

![](https://cdn.mathpix.com/snip/images/QOkXeWy1pyNujEVk6AmCgjsNo6EN_rrlhWYs2ejA8r0.original.fullsize.png)

see the EMA5, EMA20, EMA30 is hard to follow the huge gap between 16:00 and 9:30, and therefore wrongly identify the momentum as extremely strong.



## Backtesting

Backtesting is achieved by vector product here, so it is fast. However I did not consider transaction cost because: 1. It depends on which broker you use. 2. It can be ignored If your trading time is below 50 times a day. According to [Alpaca Pricing](https://forum.alpaca.markets/t/pricing-and-fees/2309), the price is about 0.004% (If you do not use margin! Margin will incraese your transaction cost a lot!)

- Margin will increase your transaction cost a lot.
- Alpaca Paper trading does not consider transaction cost.




# Useful resources

- [Strategy introduction from Earnforex](https://www.earnforex.com/cn/%E5%A4%96%E6%B1%87%E7%AD%96%E7%95%A5/)