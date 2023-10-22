from warnings import resetwarnings
from pycoingecko import CoinGeckoAPI
import pandas as pd
import numpy as np
import ccxt
import json

def get_crypto_data_with_indicators_binance(token_name):
    # Initialize the ccxt binance object
    binance = ccxt.binance()

    # Load markets
    binance.load_markets()

    if binance.symbols is None:
        return f"Failed to load market data."

    symbol = f"{token_name.upper()}/USDT"

    # Check if the symbol exists on Binance
    if symbol not in binance.symbols:
        return f"Token {token_name} not found."

    ohlcv = binance.fetch_ohlcv(symbol, '1d', limit=30)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)

    # 7-day SMA
    sma_7_day = df['close'].rolling(window=7, min_periods=1).mean().iloc[-1]
    # 7-day EMA
    ema_7_day = df['close'].ewm(span=7, adjust=False).mean().iloc[-1]
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0))
    loss = (-delta.where(delta < 0, 0))
    avg_gain = gain.rolling(window=14, min_periods=1).mean()
    avg_loss = loss.rolling(window=14, min_periods=1).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs)).iloc[-1]

    # Fibonacci retracement levels
    max_price = df['close'].max()
    min_price = df['close'].min()
    fib_levels = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1]
    fib_values = {level: min_price + level * (max_price - min_price) for level in fib_levels}

    # Volume Oscillator
    short_term_vol = df['volume'].rolling(window=5).mean()
    long_term_vol = df['volume'].rolling(window=20).mean()
    volume_oscillator = (short_term_vol - long_term_vol) / long_term_vol

    # Chaikin Money Flow (CMF)
    high_price = df['high'].rolling(window=20).max()
    low_price = df['low'].rolling(window=20).min()
    cmf = ((df['close'] - low_price) - (high_price - df['close'])) / (high_price - low_price)
    cmf = cmf.rolling(window=20).sum() / df['volume'].rolling(window=20).sum()

    # Standard Deviation
    std_dev = df['close'].rolling(window=20).std()

    # Average True Range (ATR)
    prev_close = df['close'].shift(1)
    high_low = high_price - low_price
    high_close = (high_price - prev_close).abs()
    low_close = (low_price - prev_close).abs()
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    atr = ranges.max(axis=1).rolling(window=14).mean()

    # Stochastic Oscillator
    stoch_oscillator = 100 * (df['close'] - low_price) / (high_price - low_price)

    # MACD Histogram
    macd_line = df['close'].ewm(span=12, adjust=False).mean() - df['close'].ewm(span=26, adjust=False).mean()
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    macd_histogram = macd_line - signal_line

    # Create a dictionary to hold the relevant data and indicators
    result_data = {
        '7-day_sma': sma_7_day,
        '7-day_ema': ema_7_day,
        'rsi': rsi,
        'fibonacci': fib_values,
        'volume_oscillator': volume_oscillator.iloc[-1],
        'chaikin_money_flow': cmf.iloc[-1],
        'standard_deviation': std_dev.iloc[-1],
        'average_true_range': atr.iloc[-1],
        'stochastic_oscillator': stoch_oscillator.iloc[-1],
        'macd_histogram': macd_histogram.iloc[-1]
    }

    return result_data
    print(result_data)
    

def get_trending_cryptos():
    cg = CoinGeckoAPI()
    trending_data = cg.get_search_trending()
    trending_coins = trending_data['coins']
    trending_list = []
    for coin in trending_coins:
        coin_info = {
            'name': coin['item']['name'],
            'symbol': coin['item']['symbol'],
            'market_cap_rank': coin['item']['market_cap_rank'],
        }
        trending_list.append(coin_info)
  
    return trending_list