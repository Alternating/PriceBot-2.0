from playwright.async_api import async_playwright
import os
import time
import settings

async def capture_chart_async(token_type: str = 'tetsuo'):
    """
    Capture chart for specified token using async Playwright
    
    Args:
        token_type (str): Token to capture chart for ('tetsuo' or 'sol')
    
    Returns:
        str: Path to saved screenshot or None if error
    """
    urls = {
        'tetsuo': "https://coinmarketcap.com/dexscan/solana/2KB3i5uLKhUcjUwq3poxHpuGGqBWYwtTk5eG9E5WnLG6/",
        'sol': "https://coinmarketcap.com/currencies/solana/",
    }
    
    if token_type.lower() not in urls:
        print(f"Unsupported token type: {token_type}")
        return None
        
    url = urls[token_type.lower()]
    browser = None
    
    async with async_playwright() as p:
        try:
            print(f"\nStarting chart capture for {token_type.upper()}...")
            
            browser = await p.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                screen={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            page = await context.new_page()
            
            print("\nNavigating to page...")
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Enable dark mode
            # print("\nEnabling dark mode...")
            # await page.locator(".UserDropdown_user-avatar-wrapper__YEFUG > .sc-65e7f566-0 > use").click()
            # await page.get_by_role("tooltip", name="Log In Sign Up Language").locator("span div").click()
            # await page.locator(".HeaderV3_main-header__xTs_o").click()
            try:
                print("\nAttempting to enable dark mode...")
                await page.evaluate("""() => {
                    localStorage.setItem('theme', 'dark');
                    document.documentElement.setAttribute('data-theme', 'dark');
                }""")
            except Exception as e:
                print(f"Dark mode setting failed, continuing anyway: {e}")
            

            print("\nLooking for TradingView iframe...")
            iframe = await page.wait_for_selector("iframe[name^='tradingview_']", timeout=15000)
            frame = await iframe.content_frame()
            
            # Wait for chart elements using exact selectors from codegen
            print("\nWaiting for chart elements...")
            await frame.get_by_label(f"Chart for {'TETSUO/USD' if token_type == 'tetsuo' else 'SOL/USD'}, 1 hour").wait_for(timeout=10000)
            await frame.locator(".price-axis > canvas:nth-child(2)").wait_for(timeout=10000)
            await frame.locator("div:nth-child(2) > div:nth-child(2) > div > canvas:nth-child(2)").wait_for(timeout=10000)
            
            # Set 1h timeframe by clicking the button
            # print("Setting 1h timeframe...")
            # await frame.get_by_role("radio", name="1 hour").click()
            
            # Set timeframe
            timeframe_map = {
                "15m": "15 minutes",
                "30m": "30 minutes",
                "1h": "1 hour",
                "4h": "4 hours",
                "1d": "1 day"
            }
            print(f"Setting {timeframe} timeframe...")
            await frame.get_by_role("button", name="Time Interval").click()
            await frame.get_by_text(timeframe_map[timeframe]).click()

            # Additional wait for chart update
            await page.wait_for_timeout(5000)
            
            print("Taking screenshot...")
            os.makedirs(settings.SCREENSHOT_DIR, exist_ok=True)
            screenshot_path = f"{settings.SCREENSHOT_DIR}/{token_type.lower()}_chart.png"
            
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
    capture_chart('tetsuo')