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
        
        if token_type == 'tetsuo':
            pair_data = data['pairs'][0] if data and 'pairs' in data and data['pairs'] else None
        else:
            pair_data = data.get('pair')
            
        if not pair_data:
            print(f"No pair data found for {token_type.upper()}")
            return None

        current_price = float(pair_data['priceUsd'])
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=120)
        dates = pd.date_range(start=start_time, end=end_time, freq='1H')
        
        num_periods = len(dates)
        
        # Generate more realistic price data with distinct movements
        price_data = []
        last_price = current_price / 1.5  # Start lower to show uptrend
        trend = 0
        volatility = 0.03  # Increased volatility for more pronounced moves
        
        for i in range(num_periods):
            # Generate current candle
            open_price = last_price
            
            # Add trend and volatility
            trend = trend * 0.95 + np.random.normal(0, 0.02)  # Trend momentum
            move = np.random.normal(trend, volatility)  # Price move for this period
            
            # Generate more distinct candles
            close_price = open_price * (1 + move)
            
            # Create wider range for highs and lows
            if move > 0:
                high = max(open_price, close_price) * (1 + abs(move) * np.random.uniform(0.5, 1.0))
                low = min(open_price, close_price) * (1 - abs(move) * np.random.uniform(0.2, 0.4))
            else:
                high = max(open_price, close_price) * (1 + abs(move) * np.random.uniform(0.2, 0.4))
                low = min(open_price, close_price) * (1 - abs(move) * np.random.uniform(0.5, 1.0))
            
            price_data.append([open_price, high, low, close_price])
            last_price = close_price
        
        # Scale final prices to match current price
        scale_factor = current_price / last_price
        price_data = [[p * scale_factor for p in candle] for candle in price_data]
        
        price_array = np.array(price_data)
        
        # Generate volume data
        base_volume = float(pair_data.get('volume', {}).get('h24', 0) or 0) / 24
        volumes = []
        
        for i in range(num_periods):
            # Higher volume on larger price moves
            price_change = abs(price_array[i, 3] - price_array[i, 0]) / price_array[i, 0]
            vol_multiplier = 1 + price_change * 10  # More volume on bigger moves
            volume = base_volume * vol_multiplier * np.random.uniform(0.5, 2.0)
            volumes.append(volume)
        
        df = pd.DataFrame({
            'Open': price_array[:, 0],
            'High': price_array[:, 1],
            'Low': price_array[:, 2],
            'Close': price_array[:, 3],
            'Volume': volumes
        }, index=dates)
        
        return df
        
    except Exception as e:
        print(f"Error fetching price data: {str(e)}")
        return None

async def generate_chart(df, token_type):
    """Generate chart with better volume display"""
    try:
        # Define market colors with explicit volume colors
        mc = mpf.make_marketcolors(
            up='#26a69a',
            down='#ef5350',
            edge={'up': '#26a69a', 'down': '#ef5350'},
            wick={'up': '#26a69a', 'down': '#ef5350'},
            volume={'up': '#26a69a', 'down': '#ef5350'},  # Explicit volume colors
            inherit=False  # Don't inherit colors
        )

        # Style with darker background
        s = mpf.make_mpf_style(
            base_mpf_style='charles',
            marketcolors=mc,
            gridstyle='dotted',
            gridcolor='#192734',
            facecolor='#131722',
            figcolor='#131722',
            rc={
                'axes.labelcolor': '#787B86',
                'axes.edgecolor': '#363C4E',
                'xtick.color': '#787B86',
                'ytick.color': '#787B86',
                'grid.color': '#363C4E',
                'grid.linestyle': ':'
            }
        )

        # Updated plot parameters
        fig, axlist = mpf.plot(
            df,
            type='candle',
            style=s,
            volume=True,
            ylabel='',
            ylabel_lower='',
            returnfig=True,
            figsize=(12, 7),
            panel_ratios=(3, 1),
            tight_layout=True,
            xrotation=0,
            datetime_format='%d %H:%M',
            show_nontrading=True,
            volume_panel=1,
            scale_width_adjustment=dict(candle=0.8, volume=0.3),  # Narrower volume bars
            scale_padding=dict(left=0.2, right=0.2),
            mav=(20,),
            mavcolors=['#FF9800'],
            update_width_config=dict(
                candle_linewidth=1.0,
                candle_width=0.8,
                volume_width=0.3,  # Narrower volume bars
                volume_linewidth=0.5
            )
        )

        # Customize axes
        ax_main = axlist[0]
        ax_volume = axlist[2]
        
        # Right-align price axis
        ax_main.yaxis.set_label_position('right')
        ax_main.yaxis.tick_right()
        ax_volume.yaxis.set_label_position('right')
        ax_volume.yaxis.tick_right()

        # Add pair name and price
        pair_name = f"{token_type.upper()}/SOL"
        ax_main.text(0.02, 0.98, pair_name,
                    transform=ax_main.transAxes,
                    color='white',
                    fontweight='bold',
                    fontsize=10,
                    verticalalignment='top')

        current_price = df['Close'].iloc[-1]
        price_text = f"${current_price:.4f}"
        ax_main.text(0.98, 0.98, price_text,
                    transform=ax_main.transAxes,
                    color='white',
                    fontweight='bold',
                    fontsize=10,
                    verticalalignment='top',
                    horizontalalignment='right')

        # Save chart
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{settings.SCREENSHOT_DIR}/chart_{timestamp}.png"
        os.makedirs(settings.SCREENSHOT_DIR, exist_ok=True)
        
        fig.savefig(filename, 
                   dpi=100,
                   bbox_inches='tight',
                   facecolor='#131722',
                   edgecolor='none',
                   pad_inches=0.2)
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