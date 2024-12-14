# Discord Bot Token
BOT_TOKEN = 'YOUR_BOT_TOKEN_HERE'

# Cooldown settings (in seconds)
PRICE_COOLDOWN = 300
CHART_COOLDOWN = 300

# Token addresses and API endpoints
TETSUO = {
    'address': '8i51XNNpGaKaj4G4nDdmQh95v4FKAxw8mhtaRoKd9tE8',
    'dex_api': 'https://api.dexscreener.com/latest/dex/tokens/8i51XNNpGaKaj4G4nDdmQh95v4FKAxw8mhtaRoKd9tE8',
    'pair_address': '6MXwJvp4U46YK7aM6pzMX7YYCyPx4dTaDXTnkjDXR35i'  # Raydium pair address
}

SOL = {
    'address': 'sol',
    'dex_api': 'https://api.dexscreener.com/latest/dex/pairs/osmosis/1960',
    'pair_address': 'SOL'  # Special case for SOL
}

# Chart settings
CHART_COLORS = {
    'up_candle': '#26a69a',    # Green for up candles
    'down_candle': '#ef5350',  # Red for down candles
    'edge_color': '#131722',   # Dark background color
    'background': '#131722',   # Dark background
    'grid': '#363c4e',        # Grid color
    'volume_up': '#26a69a',    # Volume colors
    'volume_down': '#ef5350'
}

# Screenshot settings
SCREENSHOT_DIR = 'screenshots'