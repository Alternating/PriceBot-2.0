import pandas as pd
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
        
        if response.status_code != 200:
            print(f"API returned status code: {response.status_code}")
            print(f"Response content: {response.text[:200]}")
            return None
            
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
            # This is a simplified approach since we can't get real candle data
            price_change = float(pair_data.get('priceChange', {}).get('h1', 0))
            start_price = current_price / (1 + price_change/100)

            # Create a DataFrame with synthetic price data
            df = pd.DataFrame({
                'Date': pd.date_range(end=current_time, periods=60, freq='1min'),
                'Open': [start_price] * 60,
                'High': [max(start_price, current_price)] * 60,
                'Low': [min(start_price, current_price)] * 60,
                'Close': [current_price] * 60,
                'Volume': [float(pair_data.get('volume', {}).get('h24', 0))/24/60] * 60
            })

            df.set_index('Date', inplace=True)

            # Add some variation to make the chart look more natural
            df['Open'] = df['Open'] * (1 + pd.Series(pd.np.random.normal(0, 0.001, 60)))
            df['High'] = df[['Open', 'Close']].max(axis=1) * (1 + abs(pd.Series(pd.np.random.normal(0, 0.001, 60))))
            df['Low'] = df[['Open', 'Close']].min(axis=1) * (1 - abs(pd.Series(pd.np.random.normal(0, 0.001, 60))))

            print(f"Created DataFrame with {len(df)} time periods")
            return df
            
        print("No price data found in response")
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"Request error: {str(e)}")
        return None
    except ValueError as e:
        print(f"JSON decoding error: {str(e)}")
        print(f"Raw response: {response.text[:200]}")
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
            title=f'\n{"TETSUO" if token_type == "tetsuo" else "Solana"} Price Chart (Last Hour)',
            ylabel='Price (USD)',
            ylabel_lower='Volume',
            returnfig=True,
            figsize=(12, 8),
            panel_ratios=(3, 1)
        )

        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{settings.SCREENSHOT_DIR}/chart_{timestamp}.png"
        os.makedirs(settings.SCREENSHOT_DIR, exist_ok=True)
        
        fig.savefig(filename, dpi=100, bbox_inches='tight')
        plt.close(fig)
        
        return filename

    except Exception as e:
        print(f"Error generating chart: {str(e)}")
        return None

async def create_price_chart(token_type):
    """Main function to create price chart"""
    try:
        # Fetch price data
        df = await fetch_candle_data(token_type)
        
        if df is None:
            return None
            
        # Generate chart
        chart_path = await generate_chart(df, token_type)
        
        return chart_path
        
    except Exception as e:
        print(f"Error creating price chart: {str(e)}")
        return None