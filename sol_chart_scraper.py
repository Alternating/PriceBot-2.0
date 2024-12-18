from playwright.async_api import async_playwright
import time
import os
import settings

class CloudflareSession:
    def __init__(self):
        self.cf_cookies = settings.CF_COOKIES
        self.headers = settings.CF_HEADERS

async def capture_sol_chart_async(headless=True):
    """Async function to capture SOL chart"""
    session = CloudflareSession()
    url = "https://dexscreener.com/osmosis/1960"
    
    async with async_playwright() as p:
        try:
            print("\nStarting SOL chart capture...")
            
            browser = await p.chromium.launch(
                headless=headless,
                args=['--disable-blink-features=AutomationControlled']
            )
            
            context = await browser.new_context(
                extra_http_headers=session.headers,
                viewport={'width': 1920, 'height': 1080},
                screen={'width': 1920, 'height': 1080}
            )
            
            await context.add_cookies(session.cf_cookies)
            page = await context.new_page()
            
            print("\nNavigating to page...")
            response = await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            print(f"Initial page load status: {response.status}")
            
            print("\nLooking for TradingView iframe...")
            iframe = await page.wait_for_selector("iframe[name^='tradingview_']", timeout=10000)
            frame_name = await iframe.get_attribute('name')
            print(f"Found iframe with name: {frame_name}")
            
            frame = await iframe.content_frame()
            
            print("\nWaiting for chart elements to load...")
            try:
                chart_label = await frame.wait_for_selector("text='Chart for SOL/USDC'", timeout=10000)
                print("✅ Chart label found")
            except Exception as e:
                print(f"❌ Check Session cookie | Chart label not found: {str(e)}")
                
            try:
                price_axis = await frame.wait_for_selector(".price-axis > canvas", timeout=10000)
                print("✅ Price axis found")
            except Exception as e:
                print(f"❌ Check Session cookie | Price axis not found: {str(e)}")
                
            try:
                chart_canvas = await frame.wait_for_selector("div:nth-child(2) > div:nth-child(2) > div > canvas", timeout=10000)
                print("✅ Chart canvas found")
            except Exception as e:
                print(f"❌ Check Session cookie | Chart canvas not found: {str(e)}")
            
            print("\nSetting 1h timeframe...")
            await frame.get_by_role("radio", name="1 hour").click()
            
            print("\nWaiting for chart to stabilize...")
            await page.wait_for_timeout(5000)
            
            print("\nTaking screenshot...")
            os.makedirs("screenshots", exist_ok=True)
            screenshot_path = "screenshots/sol_chart.png"
            
            chart_widget = frame.locator(".chart-widget").first
            await chart_widget.screenshot(path=screenshot_path)
            
            print(f"\n✅ Screenshot saved to: {screenshot_path}")
            
            if not headless:
                print("\nKeeping browser open for 10 seconds...")
                await page.wait_for_timeout(10000)
            
            await browser.close()
            return screenshot_path
            
        except Exception as e:
            print(f"\n❌ Check Session cookie | Error during capture: {str(e)}")
            if not headless:
                input("\nPress Enter to close the browser...")
            if 'browser' in locals():
                await browser.close()
            return None

# Sync wrapper for running directly
def debug_sol_chart(headless=False):
    """Synchronous wrapper for debugging"""
    import asyncio
    return asyncio.run(capture_sol_chart_async(headless=headless))

if __name__ == "__main__":
    debug_sol_chart(headless=False)  # Run in visible mode when run directly