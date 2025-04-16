# get_cookie.py
# Script to help user login and get cookies from Xiaohongshu using Playwright

import asyncio
import json
from playwright.async_api import async_playwright
import config

async def get_cookies():
    """
    Open a browser window for user to login, then extract and save the essential
    authentication cookie object as a JSON string after login is confirmed.
    """
    async with async_playwright() as p:
        # Launch a browser
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Go to Xiaohongshu
        await page.goto("https://www.xiaohongshu.com/explore")
        
        print("Please login to Xiaohongshu in the browser window.")
        print("After login, press Enter in this console to save cookies.")
        
        # Wait for user to login manually
        input()
        
        # Check if login was successful by looking for user info element
        try:
            # Wait for login element to be visible
            await page.wait_for_selector("li.user.side-bar-component", 
                                         state="visible", 
                                         timeout=5000)
            print("Login detected.")
        except Exception:
            print("Login element not found. Please make sure you are logged in before continuing.")
            print("If you are already logged in, press Enter to continue anyway.")
            input()
        
        # Get cookies
        cookies = await context.cookies()
        
        # Find the authentication cookie (usually named "web_session" or similar)
        auth_cookie_obj = None
        for cookie in cookies:
            # Ensure essential fields are present
            if cookie.get("name") == "web_session" and all(k in cookie for k in ["name", "value", "domain", "path"]):
                # Select only necessary fields for add_cookies
                auth_cookie_obj = {
                    "name": cookie["name"],
                    "value": cookie["value"],
                    "domain": cookie["domain"],
                    "path": cookie["path"],
                    # Optional but recommended fields
                    "expires": cookie.get("expires", -1), # Use -1 if not present
                    "httpOnly": cookie.get("httpOnly", False),
                    "secure": cookie.get("secure", False),
                    "sameSite": cookie.get("sameSite", "Lax") # Default to Lax if not specified
                }
                break
            
        if not auth_cookie_obj:
            print("Could not find the essential 'web_session' cookie object.")
            print("Please ensure you are logged in correctly.")
            await browser.close()
            return None
        
        # Convert cookie object to JSON string
        cookie_json_str = json.dumps(auth_cookie_obj)
        
        # Save cookie JSON string to .env
        config.save_cookie(cookie_json_str)
        print("Cookie object saved successfully to .env.")
        
        # Close browser
        await browser.close()
        
        return cookie_json_str

if __name__ == "__main__":
    asyncio.run(get_cookies()) 