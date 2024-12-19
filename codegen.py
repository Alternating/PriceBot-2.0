from playwright.sync_api import sync_playwright
import time

def run_codegen():
    with sync_playwright() as p:
        try:
            print("\nStarting codegen session...")
            
            browser = p.chromium.launch(
                headless=False,
                args=[
                    '--window-size=1920,1080',
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                screen={'width': 1920, 'height': 1080},
                record_video_dir="videos/",
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            # Start recording actions
            context.tracing.start(
                screenshots=True, 
                snapshots=True, 
                sources=True
            )
            
            page = context.new_page()
            
            print("\nNavigating to CMC DEXScan...")
            page.goto("https://coinmarketcap.com/dexscan/solana/2KB3i5uLKhUcjUwq3poxHpuGGqBWYwtTk5eG9E5WnLG6/")
            
            # Wait for chart to load
            time.sleep(5)
            
            print("\nCodegen ready!")
            print("1. Wait for chart to fully load")
            print("2. Look for TradingView widget or native chart")
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