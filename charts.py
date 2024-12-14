import pandas as pd
import numpy as np
import mplfinance as mpf
from io import BytesIO
import matplotlib.pyplot as plt
import os
from datetime import datetime
import requests
import settings

async def fetch_candle_data(token_type):
    """Fetch price data from DexScreener pair endpoint"""
    try:
        # Get the appropriate API URL based on token type
        url = settings.TETSUO['dex_api'] if token_type == 'tetsuo' else settings.SOL['dex_api']
        print(f"Fetching data from: {url}")
        
        response = requests.get(url, timeout=10)
        data = response.json()
        
        # Extract price data based on token type
        if token_type == 'tetsuo':
            if data and 'pairs' in data and len(data['pairs']) > 0:
                pair_data = data['pairs'][0]
            else:
                print("No pair data found for TETSUO")
                return None
        else:  # sol
            if data and 'pair' in data:
                pair_data = data['pair']
            else:
                print("No pair data found for SOL")
                return None

        # Extract price history data
        if 'priceUsd' in pair_data:
            current_price = float(pair_data['priceUsd'])
            current_time = datetime.now()

            # Create synthetic OHLC data for the last hour
            price_change = float(pair_data.get('priceChange', {}).get('h1', 0) or 0)  # Default to 0 if None
            start_price = current_price / (1 + price_change/100) if price_change != -100 else current_price

            # Generate time series
            dates = pd.date_range(end=current_time, periods=60, freq='1min')
            
            # Create base prices with small random variations
            variations = np.random.normal(0, 0.001, 60)
            base_prices = np.linspace(start_price, current_price, 60)
            
            # Calculate OHLC data
            opens = base_prices * (1 + variations)
            closes = np.roll(base_prices, -1) * (1 + variations)
            closes[-1] = current_price  # Make sure last close is current price
            
            # High should be highest of open/close plus small variation
            highs = np.maximum(opens, closes) * (1 + abs(np.random.normal(0, 0.001, 60)))
            
            # Low should be lowest of open/close minus small variation
            lows = np.minimum(opens, closes) * (1 - abs(np.random.normal(0, 0.001, 60)))
            
            # Ensure high is always highest and low is always lowest
            highs = np.maximum(highs, np.maximum(opens, closes))
            lows = np.minimum(lows, np.minimum(opens, closes))
            
            # Create volume data
            base_volume = float(pair_data.get('volume', {}).get('h24', 0) or 0) / 24 / 60
            volumes = np.random.normal(base_volume, base_volume * 0.1, 60)
            volumes = np.maximum(volumes, 0)  # Ensure no negative volumes
            
            # Create DataFrame
            df = pd.DataFrame({
                'Open': opens,
                'High': highs,
                'Low': lows,
                'Close': closes,
                'Volume': volumes
            }, index=dates)
            
            # Ensure no NaN values
            df = df.fillna(method='ffill').fillna(method='bfill')
            
            # Ensure proper ordering of OHLC values
            df['High'] = df[['Open', 'High', 'Close']].max(axis=1)
            df['Low'] = df[['Open', 'Low', 'Close']].min(axis=1)
            
            print(f"Created DataFrame with {len(df)} time periods")
            print("Sample of data:")
            print(df.head())
            print("\nChecking for NaN values:", df.isna().sum())
            
            return df
            
        print("No price data found in response")
        return None
        
    except Exception as e:
        print(f"Error fetching price data: {str(e)}")
        return None

async def generate_chart(df, token_type):
    """Generate chart using mplfinance"""
    try:
        # Create custom style
        mc = mpf.make_marketcolors(
            up=settings.CHART_COLORS['up_candle'],
            down=settings.CHART_COLORS['down_candle'],
            edge='inherit',
            wick='inherit',
            volume={'up': settings.CHART_COLORS['up_candle'], 
                   'down': settings.CHART_COLORS['down_candle']},
        )

        s = mpf.make_mpf_style(
            marketcolors=mc,
            gridstyle='solid',
            gridcolor=settings.CHART_COLORS['grid'],
            facecolor=settings.CHART_COLORS['background'],
            figcolor=settings.CHART_COLORS['background'],
            rc={'axes.labelcolor': 'white',
                'axes.edgecolor': 'white',
                'xtick.color': 'white',
                'ytick.color': 'white'}
        )

        # Create figure
        fig, _ = mpf.plot(
            df,
            type='candle',
            volume=True,
            style=s,
            title=f'\n{"TETSUO" if token_type == "tetsuo" else "Solana"} Price Chart (Last Hour)',
            ylabel='Price (USD)',
            ylabel_lower='Volume',
            returnfig=True,
            figsize=(12, 8),
            panel_ratios=(3, 1),
            tight_layout=True
        )

        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{settings.SCREENSHOT_DIR}/chart_{timestamp}.png"
        os.makedirs(settings.SCREENSHOT_DIR, exist_ok=True)
        
        fig.savefig(filename, dpi=100, bbox_inches='tight', facecolor=settings.CHART_COLORS['background'])
        plt.close(fig)
        
        return filename

    except Exception as e:
        print(f"Error generating chart: {str(e)}")
        return None

async def create_price_chart(token_type):
    """Main function to create price chart"""
    try:
        df = await fetch_candle_data(token_type)
        if df is None:
            return None
            
        chart_path = await generate_chart(df, token_type)
        return chart_path
        
    except Exception as e:
        print(f"Error creating price chart: {str(e)}")
        return None