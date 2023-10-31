import ccxt.async_support as ccxt_async
import matplotlib.pyplot as plt
import mplfinance as mpf
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
  
    fig, ax = plt.subplots()
    mpf.candlestick2_ochl(ax, df['open'], df['close'], df['high'], df['low'], width=0.6, colorup='g', colordown='r')
  
    ax.set_title(f'{symbol.upper()} Candlestick Chart ({timeframe})')
    ax.set_xlabel('Timestamp')
    ax.set_ylabel('Price (USDT)')
    ax.xaxis_date()
  
    file_path = f'static/charts/{symbol}_candlestick_chart.png'
    plt.savefig(file_path)
    plt.close(fig)
  
    await binance.close()
  
    local_url = f'http://127.0.0.1:8080/charts/{symbol}_candlestick_chart.png'
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