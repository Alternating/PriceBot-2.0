from playwright.async_api import async_playwright
import os
import time
import settings

class CloudflareSession:
    def __init__(self):
        self.cf_cookies = settings.CF_COOKIES
        self.headers = settings.CF_HEADERS
        
async def capture_chart_async(token_type: str = 'tetsuo'):
    """
    Capture chart for specified token using async Playwright
    
    Args:
        token_type (str): Token to capture chart for ('tetsuo' or 'sol')
    
    Returns:
        str: Path to saved screenshot or None if error
    """
    urls = {
        'tetsuo': "https://dexscreener.com/solana/2kb3i5ulkhucjuwq3poxhpuggqbwywttk5eg9e5wnlg6",
        'sol': "https://dexscreener.com/osmosis/1960"
    }
    
    if token_type.lower() not in urls:
        print(f"Unsupported token type: {token_type}")
        return None
        
    session = CloudflareSession()
    url = urls[token_type.lower()]
    browser = None
    
    async with async_playwright() as p:
        try:
            print(f"\nStarting chart capture for {token_type.upper()}...")
            
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage'
                ]
            )
            
            context = await browser.new_context(
                extra_http_headers=session.headers,
                viewport={'width': 1920, 'height': 1080},
                screen={'width': 1920, 'height': 1080}
            )
            
            await context.add_cookies(session.cf_cookies)
            page = await context.new_page()
            
            print("\nAccessing page...")
            
            # Different load strategy based on token type
            if token_type.lower() == 'sol':
                # More lenient load strategy for SOL
                response = await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                await page.wait_for_selector('.chakra-container', timeout=20000)
            else:
                # Keep existing strategy for TETSUO
                response = await page.goto(url, wait_until='networkidle', timeout=30000)
                
            print(f"Initial page load status: {response.status}")
            
            # Additional wait after page load
            await page.wait_for_timeout(5000)
            
            print("Looking for TradingView iframe...")
            iframe = await page.wait_for_selector("iframe[name^='tradingview_']", timeout=15000)
            frame = await iframe.content_frame()
            
            # Wait for chart elements based on token type
            if token_type.lower() == 'sol':
                print("Waiting for SOL chart elements...")
                try:
                    await frame.wait_for_selector("text='Chart for SOL/USDC'", timeout=10000)
                    print("Chart label found")
                    await frame.wait_for_selector(".price-axis > canvas", timeout=10000)
                    print("Price axis found")
                    await frame.wait_for_selector("div:nth-child(2) > div:nth-child(2) > div > canvas", timeout=10000)
                    print("Chart canvas found")
                except Exception as e:
                    print(f"Error waiting for chart elements: {str(e)}")
                    raise
            
            print("Setting 1h timeframe...")
            await frame.get_by_role("radio", name="1 hour").click()
            
            # Wait for chart to update after timeframe change
            await page.wait_for_timeout(5000)
            
            print("Taking screenshot...")
            os.makedirs("screenshots", exist_ok=True)
            screenshot_path = f"screenshots/{token_type.lower()}_chart.png"
            
            # Get the chart widget and take screenshot
            chart_widget = frame.locator(".chart-widget").first
            await chart_widget.screenshot(path=screenshot_path)
            
            print(f"✅ Screenshot saved to: {screenshot_path}")
            await browser.close()
            return screenshot_path
            
        except Exception as e:
            print(f"Error during capture: {str(e)}")
            if browser:
                await browser.close()
            return None

def capture_chart(token_type: str = 'tetsuo'):
    """Synchronous wrapper for capture_chart_async"""
    import asyncio
    return asyncio.run(capture_chart_async(token_type))

if __name__ == "__main__":
    capture_chart('tetsuo')  # Will save as tetsuo_chart.png
    # capture_chart('sol')   # Will save as sol_chart.png