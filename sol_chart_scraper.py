from playwright.async_api import async_playwright
import time
import os
import settings

async def capture_sol_chart_async(headless=True):
    """Async function to capture SOL chart from CMC"""
    url = "https://coinmarketcap.com/currencies/solana/"
    browser = None
    
    async with async_playwright() as p:
        try:
            print("\nStarting SOL chart capture...")
            
            browser = await p.chromium.launch(
                headless=headless,
                args=['--disable-blink-features=AutomationControlled']
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                screen={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            page = await context.new_page()
            
            print("\nNavigating to CMC...")
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Enable dark mode and handle initial page setup
            print("\nSetting up page preferences...")
            await page.locator(".UserDropdown_user-avatar-wrapper__YEFUG > .sc-65e7f566-0 > use").click()
            await page.get_by_role("tooltip", name="Log In Sign Up Language").locator("span").nth(2).click()
            
            # Switch to TradingView chart if needed
            try:
                await page.get_by_role("button", name="TradingView").click()
            except:
                print("Already on TradingView chart or button not found")
                
            # Handle cookie consent if it appears
            try:
                await page.get_by_role("button", name="Accept Cookies and Continue").click()
            except:
                print("No cookie consent needed")
            
            print("\nLooking for TradingView iframe...")
            iframe = await page.wait_for_selector("iframe[name^='tradingview_']", timeout=15000)
            frame = await iframe.content_frame()
            
            # Wait for chart elements
            print("\nWaiting for chart elements...")
            await frame.get_by_label("Chart for SOL/USD, 1 hour").wait_for(timeout=10000)
            await frame.locator(".price-axis > canvas:nth-child(2)").wait_for(timeout=10000)
            await frame.locator("div:nth-child(2) > div:nth-child(2) > div > canvas:nth-child(2)").wait_for(timeout=10000)
            
            # Set 1h timeframe
            print("\nSetting 1h timeframe...")
            await frame.get_by_role("radio", name="1 hour").click()
            
            # Wait for chart to stabilize
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
            print(f"\n❌ Error during capture: {str(e)}")
            if browser:
                await browser.close()
            return None

# Sync wrapper for running directly
def debug_sol_chart(headless=False):
    """Synchronous wrapper for debugging"""
    import asyncio
    return asyncio.run(capture_sol_chart_async(headless=headless))

if __name__ == "__main__":
    debug_sol_chart(headless=False)  # Run in visible mode when run directly