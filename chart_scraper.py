from playwright.async_api import async_playwright
import time
import os

class CloudflareSession:
    def __init__(self):
        self.cf_cookies = [
            {
                "name": "cf_clearance",
                "value": "0mBg5GJTKnBffTGYbk3IsZ.XYsk5f4bPTW2m7M73A44-1734386419-1.2.1.1-gfMuswlWrgsh0D.WAX0jH00y316mimWSZ4EnnXNSq0LWI5WuFNHdhlnV1mSzLr1Cxytd5oebnC5MWc.C2FLgnEdnAzzIsm5VIPFHDsTCbMj4PdA473ph7HfK3.2rGSOM2_gmQwSrxQa4PLF8odRWPbswmv1g6yFfNDNCcF98DjU8Bn1Fri4gkqu18q4OEqXPd55353leKq5NxCHZmuS_8ZPPEQakV_jp5WJ_klmTNT4PCRXDuxskyQipcE6A8tyU5cisUo3g4vPyPoKmukDSqk.JN25sFo31Do5BIgTZzXWFnTc8L59HOPRxOLwPkocwyqlNJGSw56EpYT6R9AGBC4JbaNyXqMRwTPAEl5X5pU_dqrONDo3OqL.0PY3kCJQ1XERvYf6N4WofgPlapRCeV8G5mZts64qun3CgbWdbQRcu6uvwSGY6deij0jM.jsx_",
                "domain": ".dexscreener.com",
                "path": "/"
            }
        ]
        
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'en-US,en;q=0.9',
            'upgrade-insecure-requests': '1'
        }

async def wait_for_chart_elements(frame, token_type):
    """Wait for specific chart elements based on token type"""
    try:
        if token_type == 'sol':
            # Wait for the chart label to be visible
            await frame.wait_for_selector("text='Chart for SOL/USDC'", timeout=10000)
            # Wait for price axis
            await frame.wait_for_selector(".price-axis > canvas", timeout=10000)
            # Wait for main chart canvas
            await frame.wait_for_selector("div:nth-child(2) > div:nth-child(2) > div > canvas", timeout=10000)
        else:
            # For TETSUO, wait for any chart canvas to be visible
            await frame.wait_for_selector(".chart-widget canvas", timeout=10000)

    except Exception as e:
        print(f"Error waiting for chart elements: {str(e)}")
        raise

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
    
    async with async_playwright() as p:
        browser = None
        try:
            print(f"\nStarting chart capture for {token_type.upper()}...")
            
            browser = await p.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )
            
            context = await browser.new_context(
                extra_http_headers=session.headers,
                viewport={'width': 1920, 'height': 1080},
                screen={'width': 1920, 'height': 1080}
            )
            
            await context.add_cookies(session.cf_cookies)
            page = await context.new_page()
            
            print("\nAccessing page...")
            # Use shorter initial timeout for page load
            await page.goto(url, wait_until='domcontentloaded', timeout=20000)
            
            # Wait for tradingview iframe with retry logic
            iframe = None
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    iframe = await page.wait_for_selector("iframe[name^='tradingview_']", timeout=10000)
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    print(f"Retry {attempt + 1}/{max_retries} waiting for iframe...")
                    await page.reload()

            frame = await iframe.content_frame()
            
            print("Setting 1h timeframe...")
            await frame.get_by_role("radio", name="1 hour").click()
            
            print("Waiting for chart elements...")
            await wait_for_chart_elements(frame, token_type.lower())
            
            # Additional wait for chart to stabilize
            await page.wait_for_timeout(2000)
            
            print("Taking screenshot...")
            os.makedirs("screenshots", exist_ok=True)
            
            screenshot_path = f"screenshots/{token_type.lower()}_chart.png"
            
            # Get chart widget and take screenshot
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
    capture_chart('tetsuo')