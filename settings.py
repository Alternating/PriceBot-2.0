# Discord Bot Token
BOT_TOKEN = 'YOUR_BOT_TOKEN_HERE'

# Cooldown settings (in seconds)
PRICE_COOLDOWN = 300
CHART_COOLDOWN = 300

# Token addresses and API endpoints
TETSUO = {
    'address': '8i51XNNpGaKaj4G4nDdmQh95v4FKAxw8mhtaRoKd9tE8',
    'dex_api': 'https://api.dexscreener.com/latest/dex/tokens/8i51XNNpGaKaj4G4nDdmQh95v4FKAxw8mhtaRoKd9tE8',
    'chart_url': 'https://dexscreener.com/solana/8i51XNNpGaKaj4G4nDdmQh95v4FKAxw8mhtaRoKd9tE8'
}

SOL = {
    'address': 'sol',
    'dex_api': 'https://api.dexscreener.com/latest/dex/pairs/osmosis/1960',
    'chart_url': 'https://dexscreener.com/solana/sol'
}

# Screenshot settings
SCREENSHOT_DIR = 'screenshots'
VIEWPORT_SETTINGS = {
    'width': 1280,
    'height': 800
}

# Chart selectors for web scraping
CHART_SELECTORS = [
    '.tv-lightweight-charts',
    '#chart-container',
    '[data-qa="chart"]',
    '.tradingview-chart',
    '.chart-container'
]

TIMEFRAME_SELECTORS = [
    'button:has-text("1h")',
    '[data-qa="time-resolution-button"]:has-text("1h")',
    'button[data-resolution="60"]',
    'button.resolution-button:has-text("1h")'
]

# Browser launch arguments
BROWSER_ARGS = [
    '--disable-gpu',
    '--no-sandbox',
    '--disable-dev-shm-usage',
    '--disable-setuid-sandbox',
    '--no-first-run',
    '--no-zygote',
    '--deterministic-fetch',
    '--disable-features=IsolateOrigins',
    '--disable-site-isolation-trials'
]