from playwright.sync_api import sync_playwright
import time
from datetime import datetime
import os

def capture_dexscreener_chart(token_address):
    """
    Captures a screenshot of a DexScreener chart using headless browser mode.
    
    Args:
        token_address (str): The token address to look up
    
    Returns:
        str: Path to the saved screenshot
    """
    with sync_playwright() as p:
        # Launch browser in headless mode with specific options
        browser = p.chromium.launch(
            headless=True,  # Ensure headless mode is enabled
            args=[
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
        )
        
        # Create context with specific viewport and color scheme
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            color_scheme='dark',  # DexScreener uses dark theme
            force_viewport=True
        )
        
        # Create new page
        page = context.new_page()
        
        try:
            # Navigate to DexScreener with timeout
            url = f"https://dexscreener.com/solana/{token_address}"
            page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Wait for chart element and ensure it's visible
            page.wait_for_selector('.tv-lightweight-charts', state='visible', timeout=30000)
            
            # Additional wait for chart to fully render
            time.sleep(5)
            
            # Create screenshots directory if it doesn't exist
            os.makedirs('screenshots', exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshots/dexscreener_chart_{timestamp}.png"
            
            # Take screenshot of chart element only with higher quality
            chart_element = page.query_selector('.tv-lightweight-charts')
            chart_element.screenshot(
                path=filename,
                type='png',
                quality=100,
                scale='device'
            )
            
            return filename
            
        except Exception as e:
            print(f"Error during screenshot capture: {str(e)}")
            raise
            
        finally:
            # Clean up
            context.close()
            browser.close()

if __name__ == "__main__":
    # Example token address
    token_address = "8i51XNNpGaKaj4G4nDdmQh95v4FKAxw8mhtaRoKd9tE8"
    
    try:
        screenshot_path = capture_dexscreener_chart(token_address)
        print(f"Screenshot successfully saved as: {screenshot_path}")
    except Exception as e:
        print(f"Failed to capture screenshot: {e}")
