from playwright.sync_api import sync_playwright
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

def debug_sol_chart(headless=True):
    """Debug function to capture SOL chart with visual feedback"""
    session = CloudflareSession()
    url = "https://dexscreener.com/osmosis/1960"
    
    with sync_playwright() as p:
        try:
            print("\nStarting SOL chart debug capture...")
            
            browser = p.chromium.launch(
                headless=headless,
                args=['--disable-blink-features=AutomationControlled']
            )
            
            context = browser.new_context(
                extra_http_headers=session.headers,
                viewport={'width': 1920, 'height': 1080},
                screen={'width': 1920, 'height': 1080}
            )
            
            context.add_cookies(session.cf_cookies)
            page = context.new_page()
            
            print("\nNavigating to page...")
            response = page.goto(url, wait_until='domcontentloaded', timeout=30000)
            print(f"Initial page load status: {response.status}")
            
            print("\nLooking for TradingView iframe...")
            iframe = page.wait_for_selector("iframe[name^='tradingview_']", timeout=10000)
            frame_name = iframe.get_attribute('name')
            print(f"Found iframe with name: {frame_name}")
            
            frame = iframe.content_frame()
            
            print("\nWaiting for chart elements to load...")
            try:
                chart_label = frame.wait_for_selector("text='Chart for SOL/USDC'", timeout=10000)
                print("✅ Chart label found")
            except Exception as e:
                print(f"❌ Chart label not found: {str(e)}")
                
            try:
                price_axis = frame.wait_for_selector(".price-axis > canvas", timeout=10000)
                print("✅ Price axis found")
            except Exception as e:
                print(f"❌ Price axis not found: {str(e)}")
                
            try:
                chart_canvas = frame.wait_for_selector("div:nth-child(2) > div:nth-child(2) > div > canvas", timeout=10000)
                print("✅ Chart canvas found")
            except Exception as e:
                print(f"❌ Chart canvas not found: {str(e)}")
            
            print("\nSetting 1h timeframe...")
            frame.get_by_role("radio", name="1 hour").click()
            
            print("\nWaiting for chart to stabilize...")
            page.wait_for_timeout(5000)
            
            print("\nTaking screenshot...")
            os.makedirs("screenshots", exist_ok=True)
            screenshot_path = "screenshots/sol_chart.png"
            
            chart_widget = frame.locator(".chart-widget").first
            chart_widget.screenshot(path=screenshot_path)
            
            print(f"\n✅ Screenshot saved to: {screenshot_path}")
            
            if not headless:
                print("\nKeeping browser open for 10 seconds...")
                time.sleep(10)
            
            browser.close()
            return screenshot_path
            
        except Exception as e:
            print(f"\n❌ Error during capture: {str(e)}")
            if not headless:
                input("\nPress Enter to close the browser...")
            if 'browser' in locals():
                browser.close()
            return None

if __name__ == "__main__":
    debug_sol_chart(headless=False)  # Run in visible mode when run directly