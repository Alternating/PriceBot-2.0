from playwright.sync_api import sync_playwright
import time

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

def run_codegen():
    session = CloudflareSession()
    
    with sync_playwright() as p:
        try:
            print("\nStarting codegen session...")
            
            browser = p.chromium.launch(
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--window-size=1920,1080'
                ]
            )
            
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                screen={'width': 1920, 'height': 1080},
                record_video_dir="videos/",
                extra_http_headers=session.headers
            )
            
            context.add_cookies(session.cf_cookies)
            
            # Start recording actions
            context.tracing.start(
                screenshots=True, 
                snapshots=True, 
                sources=True
            )
            
            page = context.new_page()
            
            print("\nNavigating to DexScreener...")
            page.goto("https://dexscreener.com/solana/2kb3i5ulkhucjuwq3poxhpuggqbwywttk5eg9e5wnlg6")
            
            # Wait for chart to load
            time.sleep(5)
            
            print("\nCodegen ready!")
            print("1. Click the 1h timeframe")
            print("2. Wait for chart update")
            print("3. Inspect elements you want to capture")
            print("4. Press Ctrl+C in terminal when done\n")
            
            page.pause()  # This will pause for codegen recording
            
            # Save the trace
            context.tracing.stop(path="trace.zip")
            
        except Exception as e:
            print(f"Error during codegen: {str(e)}")
        finally:
            if 'browser' in locals():
                browser.close()

if __name__ == "__main__":
    run_codegen()