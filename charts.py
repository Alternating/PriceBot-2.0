import pandas as pd
import mplfinance as mpf
from io import BytesIO
import matplotlib.pyplot as plt
import os
from datetime import datetime
import requests
import settings

async def fetch_candle_data(token_type):
    """Fetch candlestick data from DexScreener"""
    try:
        # Get pair address based on token type
        pair_address = settings.TETSUO['pair_address'] if token_type == 'tetsuo' else settings.SOL['pair_address']
        
        # DexScreener candles endpoint
        url = f"https://api.dexscreener.com/latest/dex/candles/solana/{pair_address}?from=1h"
        
        response = requests.get(url)
        data = response.json()
        
        if 'candles' in data:
            # Convert to pandas DataFrame
            df = pd.DataFrame(data['candles'])
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Rename columns to match mplfinance requirements
            df = df.rename(columns={
                'timestamp': 'Date',
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume'
            })
            
            # Set index to Date
            df.set_index('Date', inplace=True)
            
            return df
        
        return None
    except Exception as e:
        print(f"Error fetching candle data: {str(e)}")
        return None

async def generate_chart(df, token_type):
    """Generate chart using mplfinance"""
    try:
        # Create custom style
        mc = mpf.make_marketcolors(
            up=settings.CHART_COLORS['up_candle'],
            down=settings.CHART_COLORS['down_candle'],
            edge=settings.CHART_COLORS['edge_color'],
            volume=settings.CHART_COLORS['volume_up'],
            volume_down=settings.CHART_COLORS['volume_down']
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
            title=f'\n{"Tetsuo" if token_type == "tetsuo" else "Solana"} Price Chart (1H)',
            ylabel='Price (USD)',
            ylabel_lower='Volume',
            returnfig=True,
            figsize=(12, 8),
            panel_ratios=(3, 1)
        )

        # Save to BytesIO
        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{settings.SCREENSHOT_DIR}/chart_{timestamp}.png"
        os.makedirs(settings.SCREENSHOT_DIR, exist_ok=True)
        
        with open(filename, 'wb') as f:
            f.write(buf.getvalue())
        
        return filename

    except Exception as e:
        print(f"Error generating chart: {str(e)}")
        return None

async def create_price_chart(token_type):
    """Main function to create price chart"""
    try:
        # Fetch candle data
        df = await fetch_candle_data(token_type)
        
        if df is None:
            return None
            
        # Generate chart
        chart_path = await generate_chart(df, token_type)
        
        return chart_path
        
    except Exception as e:
        print(f"Error creating price chart: {str(e)}")
        return None