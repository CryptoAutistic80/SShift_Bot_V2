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

    ohlcv = binance.fetch_ohlcv(symbol, '1d', limit=144)  # Reduced limit to 144 for long-term EMA
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)

    # Current Market Price
    current_price = df['close'].iloc[-1]

    # Short-Term Indicators
    sma_7_day = df['close'].rolling(window=7, min_periods=1).mean().iloc[-1]
    ema_8_day = df['close'].ewm(span=8, adjust=False).mean().iloc[-1]
    rsi_14_day = 100 - (100 / (1 + df['close'].diff().where(lambda x: x > 0, 0).rolling(window=14).mean() /
                              df['close'].diff().where(lambda x: x < 0, 0).abs().rolling(window=14).mean())).iloc[-1]

    # Long-Term Indicators
    sma_200_day = df['close'].rolling(window=200, min_periods=1).mean().iloc[-1]  # Kept for comparison
    ema_144_day = df['close'].ewm(span=144, adjust=False).mean().iloc[-1]  # Adjusted to 144-day
    rsi_50_day = 100 - (100 / (1 + df['close'].diff().where(lambda x: x > 0, 0).rolling(window=50).mean() /
                              df['close'].diff().where(lambda x: x < 0, 0).abs().rolling(window=50).mean())).iloc[-1]

    # Common Indicators
    # MACD for both short-term and long-term
    macd_line_short = df['close'].ewm(span=12, adjust=False).mean() - df['close'].ewm(span=26, adjust=False).mean()
    macd_line_long = df['close'].ewm(span=26, adjust=False).mean() - df['close'].ewm(span=52, adjust=False).mean()

    result_data = {
        'current_price': current_price,
        'short_term': {
            '7-day_sma': sma_7_day,
            '8-day_ema': ema_8_day,
            '14-day_rsi': rsi_14_day,
            'macd_histogram': (macd_line_short - macd_line_short.ewm(span=9, adjust=False).mean()).iloc[-1],
        },
        'long_term': {
            '200-day_sma': sma_200_day,  # Kept for comparison
            '144-day_ema': ema_144_day,  # Adjusted to 144-day
            '50-day_rsi': rsi_50_day,
            'macd_histogram': (macd_line_long - macd_line_long.ewm(span=18, adjust=False).mean()).iloc[-1],
        }
    }

    print(result_data)
    return result_data
    

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