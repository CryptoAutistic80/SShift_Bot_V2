import ccxt.async_support as ccxt_async
import matplotlib.pyplot as plt
import mplfinance.original_flavor as mpf_of
import mplfinance as mpf
from datetime import datetime
import httpx
import pandas as pd
import numpy as np
import asyncio

async def get_crypto_data_with_indicators_binance(token_names):
    binance = ccxt_async.binance()
    await binance.load_markets()
  
    if binance.symbols is None:
        return "Failed to load market data."
  
    result_data = {}
  
    for token_name in token_names:
        symbol = f"{token_name.upper()}/USDT"
  
        if symbol not in binance.symbols:
            result_data[token_name] = f"Token {token_name} not found."
            continue  # Skip to the next token if this one is not found
  
        ohlcv = await binance.fetch_ohlcv(symbol, '1d', limit=144)
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
  
        result_data[token_name] = {
            'current_price': current_price,
            'short_term': {
                '7-day_sma': sma_7_day,
                '8-day_ema': ema_8_day,
                '14-day_rsi': rsi_14_day,
                'macd_histogram': (macd_line_short - macd_line_short.ewm(span=9, adjust=False).mean()).iloc[-1],
            },
            'long_term': {
                '200-day_sma': sma_200_day,
                '144-day_ema': ema_144_day,
                '50-day_rsi': rsi_50_day,
                'macd_histogram': (macd_line_long - macd_line_long.ewm(span=18, adjust=False).mean()).iloc[-1],
            }
        }
  
    await binance.close()
  
    print(result_data)
    return result_data
  

async def get_crypto_chart(symbol, timeframe):
    binance = ccxt_async.binance()
    await binance.load_markets()

    full_symbol = f"{symbol.upper()}/USDT"
    if full_symbol not in binance.symbols:
        await binance.close()
        return f"Token {symbol} not found."

    ohlcv = await binance.fetch_ohlcv(full_symbol, timeframe)

    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)

    # Determine the number of recent trades based on timeframe
    num, unit = int(timeframe[:-1]), timeframe[-1]
    if unit == 'm':
        recent_trades = num * 2
    elif unit == 'h':
        recent_trades = num * 120
    elif unit == 'd':
        recent_trades = num * 2880
    else:
        recent_trades = 100  # Default value

    df = df.iloc[-recent_trades:]

    # Create a unique filename using a timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{symbol}_candlestick_chart_{timestamp}.png"

    # Define custom colors and style
    mc = mpf.make_marketcolors(up='green', down='red', edge='inherit', wick='inherit', volume='inherit')
    style = mpf.make_mpf_style(base_mpf_style='nightclouds', marketcolors=mc)

    # Define the size of the image (width, height) in inches
    figsize = (16, 9)

    save_config = {
        'fname': f'static/charts/{filename}',
        'dpi': 120  # Set to produce 1920x1080 pixels image
    }

    mpf.plot(df, type='candle', style=style, volume=True, title=f'{symbol.upper()} Candlestick Chart ({timeframe})', ylabel='Price', ylabel_lower='Volume', figratio=figsize, savefig=save_config)

    await binance.close()

    local_url = f'https://sshift-bot-v2.cryptoautistic8.repl.co/view_chart/{filename}'
    return local_url
    

async def get_trending_cryptos():
    async with httpx.AsyncClient() as client:
        response = await client.get('https://api.coingecko.com/api/v3/search/trending')
        response.raise_for_status()
        trending_data = response.json()
  
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