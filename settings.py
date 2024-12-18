# Discord Bot Token
BOT_TOKEN = 'YOUR_BOT_TOKEN_HERE'

# Cooldown settings (in seconds)
PRICE_COOLDOWN = 300
CHART_COOLDOWN = 15

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

# Cloudflare session settings
CF_COOKIES = [
    {
        "name": "cf_clearance",
        "value": "JbNKrIkR5zRQGreyJVfPu9QvM3bculv4hhCHc70mC8w-1734501689-1.2.1.1-5.6JmgP5bgco8WUBXDH9NVtc3ZqY62uWw_E.Mu26iIykWpBn1szBBsw6OzA82.zwii52yvmelL4cyd_sFJNMYGFN9onTGcwhPt39ngFdlCzV5jjFDYCLEb0SYd5Lgb8QEOg0Cp9f01Wl_jqPwowYrTsI6UGes.blI2MWV5_jV9iD02lKElI6HniTd9u3tJRf3ntDS.lG5LN.hiA0wR7lKrrKnUd9.LUlwKrl4Bt6vzqTQecoCpnQvJgrSVmUUnI.1xPnsNNwma6yqK3HJ5rYTJ0dpkp3BZOwADUGLNllr.3xeSh.Wo3p6Y9AGk_aRPUfrlaGdB8eye1aSN3r6dJnHQh2HJclPDLSNx018qBQvFbeRiDdRFalKRxv_iQcPkc155bZTcOdgErZFSOj6d5BWj2Xi7UHX3fravfAQvzFsu.1vOeT7p9Z7JuTh_Mq07ea",
        "domain": ".dexscreener.com",
        "path": "/"
    }
]

CF_HEADERS = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'accept-language': 'en-US,en;q=0.9',
    'upgrade-insecure-requests': '1'
}

# Screenshot settings
SCREENSHOT_DIR = 'screenshots'