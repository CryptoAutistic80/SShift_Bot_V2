import ccxt.async_support as ccxt_async
import httpx
import pandas as pd
import numpy as np
import asyncio

# Individual functions for each indicator and spot market price
def get_current_price(df):
    return df['close'].iloc[-1]

def get_sma_7_day(df):
    return df['close'].rolling(window=7, min_periods=1).mean().iloc[-1]

def get_ema_8_day(df):
    return df['close'].ewm(span=8, adjust=False).mean().iloc[-1]

def get_rsi_14_day(df):
    return 100 - (100 / (1 + df['close'].diff().where(lambda x: x > 0, 0).rolling(window=14).mean() /
                          df['close'].diff().where(lambda x: x < 0, 0).abs().rolling(window=14).mean())).iloc[-1]

def get_sma_200_day(df):
    return df['close'].rolling(window=200, min_periods=1).mean().iloc[-1]

def get_ema_144_day(df):
    return df['close'].ewm(span=144, adjust=False).mean().iloc[-1]

def get_rsi_50_day(df):
    return 100 - (100 / (1 + df['close'].diff().where(lambda x: x > 0, 0).rolling(window=50).mean() /
                          df['close'].diff().where(lambda x: x < 0, 0).abs().rolling(window=50).mean())).iloc[-1]

def get_macd_short(df):
    macd_line_short = df['close'].ewm(span=12, adjust=False).mean() - df['close'].ewm(span=26, adjust=False).mean()
    return (macd_line_short - macd_line_short.ewm(span=9, adjust=False).mean()).iloc[-1]

def get_macd_long(df):
    macd_line_long = df['close'].ewm(span=26, adjust=False).mean() - df['close'].ewm(span=52, adjust=False).mean()
    return (macd_line_long - macd_line_long.ewm(span=18, adjust=False).mean()).iloc[-1]

async def get_crypto_data_with_indicators_binance(token_name):
    binance = ccxt_async.binance()
    await binance.load_markets()

    if binance.symbols is None:
        return "Failed to load market data."

    symbol = f"{token_name.upper()}/USDT"

    if symbol not in binance.symbols:
        return f"Token {token_name} not found."

    ohlcv = await binance.fetch_ohlcv(symbol, '1d', limit=144)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)

    result_data = {
        'current_price': get_current_price(df),
        'short_term': {
            '7-day_sma': get_sma_7_day(df),
            '8-day_ema': get_ema_8_day(df),
            '14-day_rsi': get_rsi_14_day(df),
            'macd_histogram': get_macd_short(df),
        },
        'long_term': {
            '200-day_sma': get_sma_200_day(df),
            '144-day_ema': get_ema_144_day(df),
            '50-day_rsi': get_rsi_50_day(df),
            'macd_histogram': get_macd_long(df),
        }
    }
    await binance.close()

    print(result_data)
    return result_data

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