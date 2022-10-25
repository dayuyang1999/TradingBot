:warning: Trading stock carries a high level of risk, and may not be suitable for all investors. Past performance is not indicative of future results. The high degree of leverage can work against you as well as for you. Before deciding to invest in stock market you should carefully consider your investment objectives, level of experience, and risk appetite. The possibility exists that you could sustain a loss of some or all of your initial investment and therefore you should not invest money that you cannot afford to lose. You should be aware of all the risks associated with stock trading, and seek advice from an independent financial advisor if you have any doubts.

:warning: One more thing I would like to emphasize that because my motivation is more on demonstrating how to build an algorithm trading platform by your own. Earning money is not guaranteed. You are more than welcome to take this repo as a reference point and add more stock prediction related ideas to improve it. Enjoy.



# Recent Updates Log

- 2022-10-24: 
  - change momentum signal from absolute value to percentage (also change the threshold settings)
  - update the momemtum trading pattern: the previous position will effect the currect trading decision.
  - support aftermarket data


# To-dos


- support robinhood API
- support Deep Learning methods
  - LSTM and Transformers will be top try-outs
  - Data engineering
    - price
      - EMA5
      - EMA10
      - EMA20
      - EMA30
      - ...
    - volumn
    - volatility


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

How to use this module? Basically you need the following tools:
- APIs
  - data source
  - broker

Scripts you need to build:
- a strategy
- backtesting
  - (If backtesting works good), try live trading on paper at first
- live trading



## Data

Data with minimum delay is the first prerequisite for trading on stock market. So far, I have tried [Alpaca](https://github.com/alpacahq/alpaca-trade-api-py) and [YahooFinance](https://github.com/ranaroussi/yfinance). Eventually I decided to use `yfinance`.

### Understanding data of `yfinance`

#### Limitation
Generally, `yfinance` has limitation wrt `one-time downloading bandwidth` and `remote storage space`.

- For example, for 1min data, you can only retrieval max 7 days one time. yfinance will only storage the recent 30 days.

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

### Basic Log of strategy design

1. using technical indicator(factors) to make the conditional probability $P(\text{\(Return > 0\)}_{t}|\text{historical observation}_{t-})$ deviates from 0.5 as large as possible.
2. using statistics to make the process submartingales

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





- after(extended) market data is equally important. If we do not have them, the momentum strategy bears high risk in the morning.
  - It is like to gamble: "price of after market rise, price of the morning will rise as well".

![](https://cdn.mathpix.com/snip/images/QOkXeWy1pyNujEVk6AmCgjsNo6EN_rrlhWYs2ejA8r0.original.fullsize.png)

see the EMA5, EMA20, EMA30 is hard to follow the huge gap between 16:00 and 9:30, and therefore wrongly identify the momentum as extremely strong.


#### momentum strategy

- Momentum strategy is promising to win. The reason is "Momentum" will always exist as long as some people in the market believe momentum (and it is human nature to buy something that is continuously rising for now.). However, the key is:
  - When to buy? (if too early, may be fooled by many noise signals. if too late, the momentum may have ended and inverse, which causes you lose more!)
  - When to sell?
  - What is the signal? (There are tons of default indicators in the market. Personally speaking, I did not believe any of them. I'd rather build my own momentum indicator which maintain enough flexibility, or degree of freedom, to fit the focal trading patterns)
  - more, refer to [explore](/explore/explorer_momentum_trade.ipynb)

##### Hyperparameters
Hyperparameters require a manually tuning step.

1. filter
  
see signal sequence below:

![](https://cdn.mathpix.com/snip/images/SoR1G1H3XBj42u9kp4Xa7CpLvc9SDW2rZ-me2hFwxaM.original.fullsize.png)

we should filter the noise signal to:
1. decrease the number of trading to alleviate trading cost
2. many noisy signal behave like bounce: `t-1: price increse, t: price decrese`. This is only cause loss because we may be fooled by the noisy signal `t-1: price increse` and obtain long position at t.

another observation from the signal is the distribution is negatively skewed. This follows the intuition that people tend to over-react with price drop compared with price rise.(**momentum strategy may work better for short than long? or filter for short should be larger for long?**)

![](https://cdn.mathpix.com/snip/images/qLNXTYAhYvlsoID-RsYPlj9Si3Uvb_MfhiUD1jJl9KE.original.fullsize.png)

Back to the filter hyperparameter, we need to filter out the noisy signal in the middle of red band as shown below:

![](https://cdn.mathpix.com/snip/images/4et00xEU2MusbMLbI8R0Q2MhuxYN-46zuqbp90abykI.original.fullsize.png)

Another observation is that for aftermarket, the volatility is definitely smaller than common trading hours. (**momentum strategy may work better for common trading than afterhour? or filter for aftermarket should be smaller for aftermarket?**)



## Backtesting

Backtesting is achieved by vector product here, so it is fast. However I did not consider transaction cost because: 1. It depends on which broker you use. 2. It can be ignored If your trading time is below 50 times a day. According to [Alpaca Pricing](https://forum.alpaca.markets/t/pricing-and-fees/2309), the price is about 0.004% (If you do not use margin! Margin will incraese your transaction cost a lot!)

- Margin will increase your transaction cost a lot.
- Alpaca Paper trading does not consider transaction cost.


### Live vs Backtesting

- use `Open` as `price` in backtesting, use `Close` as `price` in Live trading


# Useful resources

- [Strategy introduction from Earnforex](https://www.earnforex.com/cn/%E5%A4%96%E6%B1%87%E7%AD%96%E7%95%A5/)