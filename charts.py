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
        volatility = 0.01  # Reduced for more natural movements
        momentum = 0
        
        for i in range(1, num_periods):
            random_change = np.random.normal(0, volatility)
            momentum = momentum * 0.95 + random_change * 0.5
            trend_factor = 0.03 * (current_price - price_trend[i-1]) / current_price
            
            total_change = random_change + momentum + trend_factor
            price_trend[i] = price_trend[i-1] * (1 + total_change)
            
            if np.random.random() < 0.1:
                price_trend[i] *= (1 + np.random.normal(0, volatility * 2))

        # Ensure last price matches current price
        price_trend = np.interp(np.linspace(0, 1, num_periods),
                              [0, 1],
                              [price_trend[0], current_price])
        
        # Generate OHLC data with more pronounced candles
        opens = price_trend.copy()
        closes = np.roll(price_trend, -1)
        closes[-1] = current_price
        
        # Initialize highs and lows arrays
        highs = np.zeros(num_periods)
        lows = np.zeros(num_periods)
        
        # Generate more realistic highs and lows based on candle direction
        high_low_range = 0.005  # Reduced for more realistic wicks
        for i in range(num_periods):
            is_upcandle = closes[i] > opens[i]
            wick_range = high_low_range * (1 + np.random.uniform(-0.5, 0.5))
            
            if is_upcandle:
                highs[i] = closes[i] * (1 + wick_range)
                lows[i] = opens[i] * (1 - wick_range * 0.5)
            else:
                highs[i] = opens[i] * (1 + wick_range * 0.5)
                lows[i] = closes[i] * (1 - wick_range)
        
        # Generate more realistic volume data
        base_volume = float(pair_data.get('volume', {}).get('h24', 0) or 0) / 24
        volume_volatility = 0.5
        volumes = np.random.lognormal(np.log(base_volume), volume_volatility, num_periods)
        volumes = np.clip(volumes, base_volume * 0.2, base_volume * 3.0)
        
        # Create DataFrame with volume color
        df = pd.DataFrame({
            'Open': opens,
            'High': highs,
            'Low': lows,
            'Close': closes,
            'Volume': volumes,
            'VolumeColor': np.where(closes >= opens, 1, -1)  # 1 for green, -1 for red
        }, index=dates)
        
        return df
        
    except Exception as e:
        print(f"Error fetching price data: {str(e)}")
        return None

async def generate_chart(df, token_type):
    """Generate chart using mplfinance with DexScreener-like styling"""
    try:
        # Define colors for the chart
        mc = mpf.make_marketcolors(
            up='#26a69a',      # Bright green for up candles
            down='#ef5350',    # Bright red for down candles
            edge={'up': '#26a69a', 'down': '#ef5350'},
            wick={'up': '#26a69a', 'down': '#ef5350'},
            volume={'up': '#26a69a', 'down': '#ef5350'}
        )

        # Create custom style
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

        # Create figure with more defined candlestick settings
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
            show_nontrading=True,
            volume_panel=1,
            scale_width_adjustment=dict(candle=1.5, volume=0.8),  # Make candles wider
            scale_padding=dict(left=0.1, right=0.1),
            mav=(20,),  # Add a 20-period moving average
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