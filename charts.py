import pandas as pd
import numpy as np
import mplfinance as mpf
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import requests
import os
import settings

async def fetch_candle_data(token_type):
    """Fetch price data and create 96 hours of 1-hour candles"""
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
        start_time = end_time - timedelta(hours=96)  # Get 96 hours
        
        # Create datetime range with 1-hour intervals
        dates = pd.date_range(start=start_time, end=end_time, freq='1H')
        
        # Get price changes
        price_changes = pair_data.get('priceChange', {})
        h24_change = float(price_changes.get('h24', 0) or 0)
        
        # Calculate starting price based on 24h change
        start_price = current_price / (1 + h24_change/100) if h24_change != -100 else current_price
        
        # Generate price trend
        num_periods = len(dates)
        price_trend = np.zeros(num_periods)
        price_trend[0] = start_price
        
        # Create price movements
        volatility = 0.005
        for i in range(1, num_periods):
            # Random walk with drift towards current price
            change = np.random.normal(0, volatility)
            trend_factor = 0.02 * (current_price - price_trend[i-1]) / current_price
            price_trend[i] = price_trend[i-1] * (1 + change + trend_factor)
        
        # Ensure last price matches current price
        price_trend[-1] = current_price
        
        # Generate OHLC data
        opens = price_trend.copy()
        closes = np.roll(price_trend, -1)
        closes[-1] = current_price
        
        # Calculate highs and lows
        highs = np.maximum(opens, closes) * (1 + np.random.uniform(0.001, 0.002, num_periods))
        lows = np.minimum(opens, closes) * (1 - np.random.uniform(0.001, 0.002, num_periods))
        
        # Generate hourly volume data
        base_volume = float(pair_data.get('volume', {}).get('h24', 0) or 0) / 24
        volumes = np.random.normal(base_volume, base_volume * 0.2, num_periods)
        volumes = np.maximum(volumes, 0)  # Ensure no negative volumes
        
        # Create DataFrame
        df = pd.DataFrame({
            'Open': opens,
            'High': highs,
            'Low': lows,
            'Close': closes,
            'Volume': volumes
        }, index=dates)
        
        # Ensure OHLC relationships are maintained
        df['High'] = df[['Open', 'High', 'Close']].max(axis=1)
        df['Low'] = df[['Open', 'Low', 'Close']].min(axis=1)
        
        print(f"Created DataFrame with {len(df)} hourly candles over 96 hours")
        return df
        
    except Exception as e:
        print(f"Error fetching price data: {str(e)}")
        return None

async def generate_chart(df, token_type):
    """Generate chart using mplfinance with DexScreener-like styling"""
    try:
        mc = mpf.make_marketcolors(
            up='#26a69a',      # Green
            down='#ef5350',    # Red
            edge='inherit',
            wick='inherit',
            volume={'up': '#26a69a', 'down': '#ef5350'}
        )

        s = mpf.make_mpf_style(
            base_mpf_style='charles',
            marketcolors=mc,
            gridstyle='dotted',
            gridcolor='#192734',
            facecolor='#0B1217',
            figcolor='#0B1217',
            rc={
                'axes.labelcolor': '#A7B1B7',
                'axes.edgecolor': '#192734',
                'xtick.color': '#A7B1B7',
                'ytick.color': '#A7B1B7'
            }
        )

        # Create figure
        fig, axlist = mpf.plot(
            df,
            type='candle',
            volume=True,
            style=s,
            ylabel='Price (USD)',
            ylabel_lower='Volume',
            returnfig=True,
            figsize=(12, 7),
            panel_ratios=(3, 1),
            tight_layout=False,
            xrotation=0,
            datetime_format='%m-%d %H:%M',
            show_nontrading=True
        )

        # Get the main price axis
        ax_main = axlist[0]
        ax_volume = axlist[2]
        
        # Format axes
        ax_main.yaxis.set_label_position('right')
        ax_main.yaxis.tick_right()
        ax_volume.yaxis.set_label_position('right')
        ax_volume.yaxis.tick_right()

        # Add pair name in upper left corner
        pair_name = f"{token_type.upper()}/{'SOL' if token_type == 'tetsuo' else 'USD'}"
        ax_main.text(0.02, 0.98, pair_name,
                    transform=ax_main.transAxes,
                    color='white',
                    fontweight='bold',
                    fontsize=12,
                    verticalalignment='top')

        # Get current price (last close price from DataFrame)
        current_price = df['Close'].iloc[-1]
        
        # Format price based on value
        if current_price < 0.01:
            price_text = f"${current_price:.6f}"
        elif current_price < 1:
            price_text = f"${current_price:.4f}"
        else:
            price_text = f"${current_price:.2f}"

        # Add current price in upper right corner
        ax_main.text(0.98, 0.98, price_text,
                    transform=ax_main.transAxes,
                    color='white',
                    fontweight='bold',
                    fontsize=12,
                    verticalalignment='top',
                    horizontalalignment='right')
        
        # Adjust layout
        plt.subplots_adjust(left=0.05, right=0.95, top=0.95)
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{settings.SCREENSHOT_DIR}/chart_{timestamp}.png"
        os.makedirs(settings.SCREENSHOT_DIR, exist_ok=True)
        
        fig.savefig(filename, 
                   dpi=100, 
                   bbox_inches='tight', 
                   facecolor='#0B1217',
                   edgecolor='none',
                   pad_inches=0.5)
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