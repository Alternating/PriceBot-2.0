import pandas as pd
import numpy as np
import mplfinance as mpf
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import requests
import os
import settings

async def fetch_candle_data(token_type):
    """Fetch price data and create 120 hours of 1-hour candles"""
    try:
        url = settings.TETSUO['dex_api'] if token_type == 'tetsuo' else settings.SOL['dex_api']
        print(f"Fetching data from: {url}")
        
        response = requests.get(url, timeout=10)
        data = response.json()
        
        # Extract price data
        if token_type == 'tetsuo':
            pair_data = data['pairs'][0] if data and 'pairs' in data and data['pairs'] else None
        else:
            pair_data = data.get('pair')
            
        if not pair_data:
            print(f"No pair data found for {token_type.upper()}")
            return None

        # Get current price and create time series
        current_price = float(pair_data['priceUsd'])
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=120)
        
        # Create datetime range with 1-hour intervals
        dates = pd.date_range(start=start_time, end=end_time, freq='1H')
        
        # Get price changes
        price_changes = pair_data.get('priceChange', {})
        h24_change = float(price_changes.get('h24', 0) or 0)
        
        # Calculate starting price based on 24h change
        start_price = current_price / (1 + h24_change/100) if h24_change != -100 else current_price
        
        # Generate more realistic price movements
        num_periods = len(dates)
        price_trend = np.zeros(num_periods)
        price_trend[0] = start_price
        
        # Enhanced price movement generation
        volatility = 0.02  # Increased for more pronounced movements
        momentum = 0  # Add momentum factor
        for i in range(1, num_periods):
            # Random walk with momentum and mean reversion
            random_change = np.random.normal(0, volatility)
            momentum = momentum * 0.95 + random_change * 0.5  # Momentum decay and update
            trend_factor = 0.03 * (current_price - price_trend[i-1]) / current_price
            
            # Combined price movement
            total_change = random_change + momentum + trend_factor
            price_trend[i] = price_trend[i-1] * (1 + total_change)
            
            # Add occasional larger moves
            if np.random.random() < 0.1:  # 10% chance of larger move
                price_trend[i] *= (1 + np.random.normal(0, volatility * 2))

        # Ensure last price matches current price
        price_trend = np.interp(np.linspace(0, 1, num_periods),
                              [0, 1],
                              [price_trend[0], current_price])
        
        # Generate OHLC data with more pronounced candles
        opens = price_trend.copy()
        closes = np.roll(price_trend, -1)
        closes[-1] = current_price
        
        # More pronounced highs and lows
        high_low_range = 0.015  # Increased range for more visible candles
        highs = np.maximum(opens, closes) * (1 + np.random.uniform(0, high_low_range, num_periods))
        lows = np.minimum(opens, closes) * (1 - np.random.uniform(0, high_low_range, num_periods))
        
        # Generate more realistic volume data
        base_volume = float(pair_data.get('volume', {}).get('h24', 0) or 0) / 24
        volume_volatility = 0.5
        volumes = np.random.lognormal(np.log(base_volume), volume_volatility, num_periods)
        volumes = np.clip(volumes, base_volume * 0.2, base_volume * 3.0)  # Clip extreme values
        
        # Create DataFrame
        df = pd.DataFrame({
            'Open': opens,
            'High': highs,
            'Low': lows,
            'Close': closes,
            'Volume': volumes
        }, index=dates)
        
        return df
        
    except Exception as e:
        print(f"Error fetching price data: {str(e)}")
        return None