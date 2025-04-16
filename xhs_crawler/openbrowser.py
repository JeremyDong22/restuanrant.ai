# openbrowser.py
# Maintains a persistent Playwright browser session that other scripts can connect to,
# navigating to Xiaohongshu and attempting login on startup.

import asyncio
from playwright.async_api import async_playwright
import os
import signal
import sys
# Import cookie loading function from config
from config import load_cookie_obj

# Port for browser debugging
DEBUG_PORT = 9222
BROWSER_PARAMS = {
    'port': DEBUG_PORT,
    'width': 1280,
    'height': 800
}
XHS_HOMEPAGE = "https://www.xiaohongshu.com/explore"

async def apply_cookie_and_navigate(browser_context, page):
    """Load cookie object from .env, add it to context, and navigate."""
    cookie_obj = load_cookie_obj()
    if not cookie_obj:
        print("No valid cookie object found in .env. Navigating without login.")
        await page.goto(XHS_HOMEPAGE)
        await page.wait_for_load_state("networkidle")
        return

    try:
        print("Attempting to add cookie to context and navigate...")
        # Add the cookie to the browser context *before* navigating
        await browser_context.add_cookies([cookie_obj])
        print("Cookie added to context.")

        # Now navigate to the homepage
        await page.goto(XHS_HOMEPAGE)
        await page.wait_for_load_state("networkidle")

        # Check if login was successful (optional, for feedback)
        try:
            await page.wait_for_selector("li.user.side-bar-component", timeout=5000, state="visible")
            print("Auto-login seems successful (user component found)." )
        except:
            print("Auto-login might not be successful (user component not found). Please check the browser.")

        print(f"Browser navigated to {XHS_HOMEPAGE}.")

    except Exception as e:
        print(f"Error adding cookie or navigating: {e}")
        # Fallback: navigate without cookie if error occurs
        await page.goto(XHS_HOMEPAGE)

async def start_persistent_browser():
    """
    Start a persistent Chromium browser, add cookie, navigate to XHS.
    """
    print(f"Starting persistent browser on debugging port {BROWSER_PARAMS['port']}...")
    print(f"Browser window size: {BROWSER_PARAMS['width']}x{BROWSER_PARAMS['height']}")

    try:
        async with async_playwright() as p:
            browser_type = p.chromium

            # Launch browser with debugging port
            browser_context = await browser_type.launch_persistent_context(
                user_data_dir="./browser_data",
                headless=False,
                args=[
                    f'--remote-debugging-port={BROWSER_PARAMS["port"]}',
                    '--no-sandbox',
                    '--disable-web-security',
                    f'--window-size={BROWSER_PARAMS["width"]},{BROWSER_PARAMS["height"]}'
                ],
                viewport={
                    'width': BROWSER_PARAMS['width'],
                    'height': BROWSER_PARAMS['height']
                }
            )

            # Get the first page or create one if none exists
            pages = browser_context.pages
            if pages:
                page = pages[0]
            else:
                page = await browser_context.new_page()

            # Apply cookie and navigate to Xiaohongshu homepage
            await apply_cookie_and_navigate(browser_context, page)

            # Handle graceful shutdown
            def handle_shutdown(sig, frame):
                print("\nShutting down browser...")
                loop = asyncio.get_event_loop()
                loop.run_until_complete(browser_context.close())
                sys.exit(0)

            # Register signal handlers
            signal.signal(signal.SIGTERM, handle_shutdown)
            signal.signal(signal.SIGINT, handle_shutdown)

            print("Browser started successfully. Press Ctrl+C to close.")
            print(f"Other scripts can connect using: http://localhost:{BROWSER_PARAMS['port']}")

            # Keep browser open
            while True:
                await asyncio.sleep(1)

    except Exception as e:
        print(f"Error starting browser: {e}")
        return 1

def get_connection_parameters():
    """Return browser connection parameters for other scripts to use"""
    return {
        'wsEndpoint': f'ws://localhost:{BROWSER_PARAMS["port"]}'
    }

if __name__ == "__main__":
    # Run the persistent browser
    asyncio.run(start_persistent_browser()) 