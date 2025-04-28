# crawler.py
# Web scraper for Xiaohongshu that extracts posts based on brand names
# Changes:
# - Modified save_data_to_json to save only the current brand's data, overwriting existing file.
# - Added _wait_randomly method and calls for anti-detection.
# - Improved post_id extraction and handling.
# - Added intra-brand deduplication in crawl_posts.
# - Corrected data directory path to be relative to the script file (xhs_crawler/data).
# - Removed brand-based pause logic.
# - Corrected config variable from BRANDS_TO_SEARCH back to BRANDS.
# - Added simplified random_like_post function (1/3 chance, no active check) called from open_post_detail.
# - Implemented 60-minute timer and 300-post click limit logic in extract_post_data.

import asyncio
import json
import os
import random
import sys
import time
from datetime import datetime
from playwright.async_api import async_playwright, Error as PlaywrightError, Playwright
import config
from tqdm import tqdm
import re # Ensure re is imported
import shutil # Add shutil import for potential future use, and helps group os/pathlib
from pathlib import Path # Ensure Path is imported

class XHSCrawler:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.base_url = "https://www.xiaohongshu.com/explore"
        self.current_brand = None
        # self.posts_data = [] # No longer needed to accumulate across brands here
        self.browser_width = 1280
        self.browser_height = 800
        # --- Make data_dir relative to this script file ---
        script_dir = Path(__file__).parent # Get the directory containing crawler.py
        self.data_dir = script_dir / "data" # Make 'data' relative to the script's dir
        # --- End change ---
        self.data_dir.mkdir(parents=True, exist_ok=True) # Ensure directory exists
        self.post_click_count = 0
        self.window_start_time = 0 # Will be set in run()
        self.POST_CLICK_LIMIT = 300
        self.TIME_WINDOW_SECONDS = 3600 # 60 minutes
        
    async def connect_to_existing_browser(self, p: Playwright):
        """Connect to an already running browser instance and use its existing page."""
        try:
            cdp_url = "http://localhost:9222"
            print(f"Attempting to connect via CDP: {cdp_url}")
            self.browser = await p.chromium.connect_over_cdp(cdp_url)
            print("Browser connected.")

            contexts = self.browser.contexts
            if not contexts:
                print("Error: No browser context found in the existing browser.")
                print("Make sure openbrowser.py is running and has initialized correctly.")
                await self.browser.close() # Close the potentially broken connection
                return False
            self.context = contexts[0]
            print("Context obtained.")

            # --- Start: Revised logic - Use existing page --- 
            existing_pages = self.context.pages
            if existing_pages:
                print(f"Found {len(existing_pages)} existing page(s). Using the first one.")
                self.page = existing_pages[0]
                # Verify if the page is at the expected URL
                print(f"Existing page URL: {self.page.url}")
                if not self.page.url.startswith(self.base_url):
                    print(f"Warning: Existing page is not at {self.base_url}. Navigating...")
                    try:
                        await self.page.goto(self.base_url)
                        await self.page.wait_for_selector("#app", state="visible", timeout=20000)
                        print("Existing page navigated to base URL and #app is visible.")
                    except Exception as nav_err:
                        print(f"Error navigating existing page to base URL: {nav_err}. Attempting reload.")
                        try: 
                             await self.page.reload()
                             await self.page.wait_for_selector("#app", state="visible", timeout=20000)
                             print("Existing page reloaded and #app is visible.")
                        except Exception as reload_err:
                              print(f"Error reloading existing page: {reload_err}")
                              await self.browser.close()
                              return False
                else:
                    print("Existing page is already at the correct base URL.")
            else:
                # Fallback: If no page exists (unexpected), create one
                print("Warning: No existing page found. Creating a new page...")
                self.page = await self.context.new_page()
                print("New page created.")
                # Navigate the new page to the base URL
                print(f"Navigating new page to {self.base_url}...")
                try:
                    await self.page.goto(self.base_url)
                    await self.page.wait_for_selector("#app", state="visible", timeout=20000)
                    print("Page navigated successfully and #app is visible.")
                except Exception as nav_err:
                    print(f"Error navigating new page to base URL: {nav_err}")
                    await self.browser.close()
                    return False
            # --- End: Revised logic - Use existing page --- 

            print("Successfully connected to existing browser and page is ready.")
            # Verify login state on the page we are using
            try:
                await self.page.wait_for_selector("li.user.side-bar-component", timeout=10000, state="visible")
                print("Verified: Logged in state detected in connected browser.")
                return True
            except PlaywrightError:
                print("Warning: Could not verify login state in connected browser (user component not found). Login might be required.")
                return True # Allow proceeding, assuming openbrowser handled it

        except PlaywrightError as e:
            print(f"Playwright Error connecting to existing browser: {e}")
            print("Please ensure openbrowser.py is running and accessible.")
            # Clean up browser object if connection failed partially
            if self.browser and self.browser.is_connected():
                await self.browser.close()
            self.browser = None 
            return False
        except Exception as e:
            print(f"General Error connecting to existing browser: {e}")
            print("Please ensure openbrowser.py is running and accessible.")
            if self.browser and self.browser.is_connected():
                 await self.browser.close()
            self.browser = None
            return False
    
    async def _wait_randomly(self, min_seconds=1, max_seconds=3):
        """Waits for a random amount of time between min_seconds and max_seconds."""
        wait_time = random.uniform(min_seconds, max_seconds)
        print(f"Waiting randomly for {wait_time:.2f} seconds...")
        await asyncio.sleep(wait_time)
    
    async def search_brand(self, brand_name):
        """Search for a brand name on Xiaohongshu"""
        if not self.page or self.page.is_closed():
            print("Error: Page is not available or closed before searching.")
            return False
        
        self.current_brand = brand_name
        print(f"Searching for brand: {brand_name}")
        
        try:
            # Ensure page is on the explore page before searching
            try:
                if not self.page.url.startswith(self.base_url):
                    print(f"Navigating back to {self.base_url} before searching...")
                    await self.page.goto(self.base_url)
                    await self.page.wait_for_selector("#app", state="visible", timeout=15000)
            except Exception as nav_err:
                 print(f"Error ensuring base URL before search: {nav_err}. Attempting to continue...")

            # Click search box
            print("Locating search input...")
            search_box = self.page.locator("input.search-input")
            await search_box.wait_for(state="visible", timeout=10000)
            print("Clicking search input...")
            await search_box.click()
            print(f"Filling search input with: {brand_name}")
            await search_box.fill(brand_name)
            print("Pressing Enter...")
            await self.page.keyboard.press("Enter")

            # Wait for search results page to load
            print("Waiting 2 seconds for search results to load...")
            await self._wait_randomly(2.0, 3.5) # Increased and randomized wait
            print("Search results assumed loaded.")

            # Click on "图文" (image and text) tab using the precise selector
            try:
                image_text_tab_locator = 'div.channel#image' # Precise locator based on ID and class
                print(f"Locating and clicking '图文' tab using selector: {image_text_tab_locator}...")
                
                image_text_tab = self.page.locator(image_text_tab_locator)
                # Wait for the element to be present and visible
                await image_text_tab.wait_for(state="visible", timeout=15000) # Increased timeout
                
                # Optional: Add a small delay before clicking if needed
                await self._wait_randomly(0.5, 1.0)
                
                await image_text_tab.click()
                print("Clicked on 图文 tab")
                
                # Wait after clicking tab 
                print("Waiting 2 seconds after clicking '图文' tab...")
                await self._wait_randomly(2.0, 3.5)
                print("'图文' tab assumed loaded.")
                
            except Exception as e:
                print(f"Error clicking 图文 tab using selector '{image_text_tab_locator}': {e}")
                # Add screenshot for debugging tab clicking issue
                try:
                    await self.page.screenshot(path=f"error_clicking_tab_{brand_name}.png")
                    print(f"Screenshot saved to error_clicking_tab_{brand_name}.png")
                except Exception as ss_err:
                    print(f"Could not save screenshot: {ss_err}")
                return False # Failed to click the correct tab

            # Click on filter and sort by most likes
            print("Applying 'most likes' filter...")
            if not await self.apply_like_filter():
                print("Failed to apply like filter.")
                return False

            print(f"Search setup complete for {brand_name}.")
            return True
        except PlaywrightError as e:
             if "Target page, context or browser has been closed" in str(e):
                 print(f"Error searching for brand {brand_name}: Page closed unexpectedly. {e}")
             else:
                 print(f"Playwright Error searching for brand {brand_name}: {e}")
             return False
        except Exception as e:
            print(f"General Error searching for brand {brand_name}: {e}")
            # Add screenshot for debugging unknown errors
            try:
                await self.page.screenshot(path=f"error_search_{brand_name}.png")
                print(f"Screenshot saved to error_search_{brand_name}.png")
            except Exception as ss_err:
                 print(f"Could not save screenshot: {ss_err}")
            return False
    
    async def apply_like_filter(self):
        """Apply filter to sort by most likes"""
        if not self.page or self.page.is_closed():
            print("Error: Page is not available or closed before applying filter.")
            return False
        
        try:
            # Hover over filter button
            print("Locating and hovering filter button...")
            filter_button = self.page.locator('div.filter')
            await filter_button.wait_for(state="visible", timeout=10000)
            await filter_button.hover()
            
            # Wait for filter panel to appear and click on "最多点赞" (most likes)
            print("Locating and clicking '最多点赞' option...")
            most_likes_option = self.page.locator('div.filter-panel span:has-text("最多点赞")')
            await most_likes_option.wait_for(state="visible", timeout=10000)
            await most_likes_option.click()
            
            print("Sorted by most likes")
            # Wait after clicking filter (Replaced complex waits with sleep)
            print("Waiting 4 seconds after applying filter...")
            await self._wait_randomly(3.5, 5.5) # Increased and randomized wait
            print("Filter assumed applied.")
            return True
        except Exception as e:
            print(f"Error applying like filter: {e}")
            return False
    
    async def random_like_post(self):
        """Randomly likes the currently open post with a 1/3 probability."""
        try:
            if random.random() < 1/3:
                print(f"Attempting random like (1/3 chance occurred)...")
                # Selector assumes the detail mask is open
                like_wrapper = self.page.locator("div.note-detail-mask .like-wrapper")

                if await like_wrapper.count() > 0:
                    print(f"Like button found. Clicking like...")
                    await like_wrapper.first.click()
                    await self._wait_randomly(0.8, 1.8) # Short wait after liking
                    print(f"Successfully liked post randomly.")
                else:
                    print(f"Like button (.like-wrapper inside mask) not found.")
            else:
                 print(f"Random like condition not met (2/3 chance). Skipping like.")

        except Exception as e:
            print(f"Error during random like attempt: {e}")

    async def extract_post_data(self, post_element, data_index):
        """Extract basic data from a post card using ElementHandle methods."""
        post_data = {"brand": self.current_brand, "data_index": data_index, "likes": 0}
        post_id_for_error = f"brand_{self.current_brand}_idx_{data_index}" # Default identifier

        # --- Time/Click Limit Check --- BEFORE attempting to click/open
        try:
            current_time = time.monotonic()
            elapsed_time = current_time - self.window_start_time

            # Check if time window expired
            if elapsed_time >= self.TIME_WINDOW_SECONDS:
                print(f"\n*** Time window ({self.TIME_WINDOW_SECONDS}s) elapsed. Resetting post click count ({self.post_click_count} -> 0) and timer. ***")
                self.post_click_count = 0
                self.window_start_time = current_time
                elapsed_time = 0 # Reset elapsed time for the current check

            # Check if post click limit reached
            if self.post_click_count >= self.POST_CLICK_LIMIT:
                print(f"\n--- Post click limit ({self.POST_CLICK_LIMIT}) reached. Checking time window... ---")
                remaining_time = self.TIME_WINDOW_SECONDS - elapsed_time
                if remaining_time > 0:
                    print(f"---> Time window has {remaining_time:.2f} seconds remaining.")
                    print(f"---> PAUSING script for {remaining_time:.2f} seconds to respect limit...")
                    await asyncio.sleep(remaining_time + 1) # Add 1s buffer
                    print(f"---> RESUMING script after pause.")
                else:
                    print(f"---> Time window already elapsed or finished.")
                
                # Reset counter and timer after waiting or if window was already done
                print(f"---> Resetting post click count ({self.post_click_count} -> 0) and timer.")
                self.post_click_count = 0
                self.window_start_time = time.monotonic()

            # Increment count *before* the action that consumes the limit (opening detail)
            self.post_click_count += 1
            print(f"[Limit Status] Post Count: {self.post_click_count}/{self.POST_CLICK_LIMIT}, Time Elapsed: {elapsed_time:.2f}/{self.TIME_WINDOW_SECONDS}s")

        except Exception as limit_check_err:
            print(f"Error during post click limit check: {limit_check_err}")
            # Decide if we should continue or stop? For now, let's continue but log.
        # --- End Time/Click Limit Check ---

        try:
            # Use query_selector relative to the post_element (ElementHandle)
            # Title
            title_element = await post_element.query_selector('div.footer a.title')
            if title_element:
                 post_data["title"] = await title_element.inner_text()
            
            # Author
            author_element = await post_element.query_selector('div.card-bottom-wrapper a.author div.name span.name')
            if author_element:
                 post_data["author"] = await author_element.inner_text()
            
            # Publish Time
            time_element = await post_element.query_selector('div.card-bottom-wrapper a.author span.time')
            if time_element:
                 post_data["publish_date"] = await time_element.inner_text()
            
            # Like Count
            like_element = await post_element.query_selector('span.like-wrapper span.count') 
            if like_element:
                like_text = await like_element.inner_text()
                like_text = like_text.strip()
                if like_text:
                    if "万" in like_text:
                        like_count = float(like_text.replace('万', '')) * 10000
                    elif like_text.isdigit(): 
                        like_count = int(like_text)
                    else: 
                        like_count = 0 
                    post_data["likes"] = int(like_count)
            
            # Check like threshold
            if post_data["likes"] < config.LIKE_THRESHOLD:
                print(f'Post {data_index} has {post_data["likes"]} likes, below threshold of {config.LIKE_THRESHOLD}')
                # Clean up handles if query_selector was used
                if title_element: await title_element.dispose()
                if author_element: await author_element.dispose()
                if time_element: await time_element.dispose()
                if like_element: await like_element.dispose()
                return None # Signal to stop crawling this brand
            
            # Clean up handles
            if title_element: await title_element.dispose()
            if author_element: await author_element.dispose()
            if time_element: await time_element.dispose()
            if like_element: await like_element.dispose()
            return post_data
            
        except Exception as e:
            print(f"Error extracting post data for index {data_index}: {e}")
            # Clean up handles in case of error during processing
            if 'title_element' in locals() and title_element: await title_element.dispose()
            if 'author_element' in locals() and author_element: await author_element.dispose()
            if 'time_element' in locals() and time_element: await time_element.dispose()
            if 'like_element' in locals() and like_element: await like_element.dispose()
            return post_data # Return partial data or default likes=0
    
    async def open_post_detail(self, post_element):
        """Open post detail page and extract additional data using ElementHandle methods."""
        if not self.page or self.page.is_closed():
            print("Error: Page is not available or closed before opening post detail.")
            return None
        
        post_detail = {}
        post_id_for_error = "unknown"
        detail_page_selector = "div.note-detail-mask"
        cover_element = None # Define for potential cleanup
        
        try:
            # Locate the post cover using query_selector on the element handle
            cover_element = await post_element.query_selector('a.cover.mask.ld') 
            if not cover_element:
                print("Cover element not found using query_selector. This might be an ad or recommendation.")
                return None
            
            # Ensure cover is ready before clicking
            print("Waiting for post cover to be ready...")
            # Note: wait_for is not available on ElementHandle, visibility check is implicit in click
            # We rely on the element being found by query_selector
            await self._wait_randomly(0.5, 1.0)
                
            print("Clicking post cover...")
            await cover_element.click()
            await cover_element.dispose() # Dispose handle after use
            cover_element = None # Reset
            await self._wait_randomly(2.0, 3.5) # Increased and randomized wait
            # Wait for detail page mask to appear (using wait_for_selector on page)
            print("Waiting for note detail mask to appear...")
            await self.page.wait_for_selector(detail_page_selector, timeout=20000, state="visible")
            # Locate the mask itself to scope searches
            detail_mask = self.page.locator(detail_page_selector)
            print("Note detail mask appeared.")
            
            # Extract note ID from the mask attribute if possible, fallback to URL. 
            # In Element, note-id is correct but we call it post-id.
            post_id = await detail_mask.get_attribute("note-id")
            if not post_id:
                 print("Could not get post-id from mask attribute, trying URL.")
                 try:
                      await self.page.wait_for_url("**/discovery/item/**", timeout=5000)
                      current_url = self.page.url
                      post_id = current_url.split('/item/')[-1].split('?')[0] if '/item/' in current_url else None
                 except Exception:
                      print("Timeout waiting for item URL.")
                      post_id = None
                 if not post_id:
                      print("Could not extract post_id from URL either.")
                      post_id = f"unknown_{datetime.now().timestamp()}" 
                      
            post_id_for_error = post_id 
            post_detail["post_id"] = post_id
            print(f"Post ID: {post_id}")
            
            # --- Refined Content Extraction (Hashtag part removed) --- 
            content_element = detail_mask.locator('#detail-desc') 
            full_content = ""
            if await content_element.count() > 0:
                # Use JavaScript evaluation to reconstruct content correctly
                node_data = await content_element.evaluate("""(element) => {
                    let data = { text: [] }; // Removed hashtags array
                    element.childNodes.forEach(node => {
                        if (node.nodeType === Node.TEXT_NODE) { // Text node
                            data.text.push(node.textContent);
                        } else if (node.nodeType === Node.ELEMENT_NODE) { // Element node
                            let text = node.textContent;
                            if (text) data.text.push(text); // Add text content of element
                        }
                    });
                    // Join text pieces, preserving spaces between elements/nodes
                    data.fullText = data.text.map(t => t.trim()).filter(t => t).join(' '); 
                    return data;
                }""")
                full_content = node_data.get("fullText", "")
                print(f"Extracted content length: {len(full_content)}")
            else:
                print("Content element #detail-desc not found.")
            post_detail["content"] = full_content
            # --- End Refined Content Extraction --- 

            # --- Start: Modified Image Extraction --- 
            print("Extracting images...")
            image_srcs_all = []
            # Try slider images first
            image_elements = await detail_mask.locator('div.swiper-slide img.note-slider-img').all()
            if image_elements:
                print(f"Found {len(image_elements)} slider image elements.")
                for img in image_elements:
                    src = await img.get_attribute('src')
                    if src:
                        image_srcs_all.append(src)
            else: # Fallback for single image notes not in a slider
                 single_image = detail_mask.locator('img.note-image') # Common class for single image
                 if await single_image.count() > 0:
                     print("Found single image element.")
                     src = await single_image.first.get_attribute('src')
                     if src: image_srcs_all.append(src)
                 else:
                      print("No slider images or single image found.")
                     
            print(f"Initially extracted {len(image_srcs_all)} image URLs.")

            # Discard first and last image if more than 2 images were found
            image_srcs_final = []
            if len(image_srcs_all) > 2:
                image_srcs_final = image_srcs_all[1:-1] 
                print(f"Discarding first and last images. Keeping {len(image_srcs_final)} images.")
            elif len(image_srcs_all) <= 2 and len(image_srcs_all) > 0: 
                 print(f"Found {len(image_srcs_all)} images, discarding them as per rule.")
                 image_srcs_final = [] 
            else: 
                 image_srcs_final = []
                 
            # Join the final list with ", " (comma and space)
            post_detail["images"] = ", ".join(image_srcs_final)
            print(f"Saved {len(image_srcs_final)} image URLs (comma-space separated).")
            # --- End: Modified Image Extraction --- 
            
            # Locate the main actions container
            counts_area = detail_mask.locator("div.engage-bar") # Updated selector based on screenshots
            if await counts_area.count() == 0:
                 # Fallback if engage-bar not found
                 counts_area = detail_mask.locator("div.action-container")
                 if await counts_area.count() == 0:
                     print(f"Post {post_id_for_error}: Could not find counts area (engage-bar or action-container). Counts will be 0.")
                     counts_area = None # Ensure it's None if not found
                 else:
                      print("Using fallback counts area: div.action-container")
            else:
                 print("Located counts area: div.engage-bar")
            
            # Extract counts using updated selectors within the detail view
            post_detail["collections"] = 0 # Default
            post_detail["comments"] = 0 # Default

            if counts_area: # Proceed only if counts_area was found
                # --- Collections --- #
                try:
                    collection_element = counts_area.locator(".collect-wrapper span.count") # Screenshot selector
                    if await collection_element.count() > 0:
                        collection_text = await collection_element.first.inner_text()
                        collection_text = collection_text.strip()
                        if "万" in collection_text:
                            post_detail["collections"] = int(float(collection_text.replace('万', '')) * 10000)
                        elif collection_text.isdigit():
                            post_detail["collections"] = int(collection_text)
                    print(f"Collection count: {post_detail['collections']}")
                except Exception as e:
                    print(f"Post {post_id_for_error}: Error extracting collection count: {e}")
                
                # --- Comments --- #
                try:
                    comment_element = counts_area.locator(".chat-wrapper span.count") # Screenshot selector
                    if await comment_element.count() > 0:
                        comment_text = await comment_element.first.inner_text()
                        comment_text = comment_text.strip()
                        if "万" in comment_text:
                            post_detail["comments"] = int(float(comment_text.replace('万', '')) * 10000)
                        elif comment_text.isdigit():
                            post_detail["comments"] = int(comment_text)
                    print(f"Comment count: {post_detail['comments']}")
                except Exception as e:
                    print(f"Post {post_id_for_error}: Error extracting comment count: {e}")
            
            # --- Attempt Random Like before closing ---
            await self.random_like_post()
            # ----------------------------------------

            # Close detail page by clicking the close button within the mask
            # Using a potentially more robust selector within the mask
            close_button = detail_mask.locator('div.close') 
            if await close_button.count() > 0:
                print("Closing note detail...")
                await close_button.first.click()
                # Wait for the mask to become hidden
                await detail_mask.wait_for(state="hidden", timeout=5000)
                print("Note detail closed.")
            else:
                print("Could not find close button (div.close) within mask. Going back.")
                await self.page.go_back()
                await self.page.wait_for_selector("#app", state="visible", timeout=15000)
                print("Navigated back and #app is visible.")
            
            return post_detail
        except Exception as e:
            print(f"Error processing post detail for post {post_id_for_error}: {e}")
            # Clean up handles
            if cover_element: await cover_element.dispose()
            # Try to close if still open
            try:
                 detail_mask = self.page.locator(detail_page_selector)
                 if await detail_mask.is_visible(timeout=1000):
                      close_button = detail_mask.locator('div.close')
                      if await close_button.count() > 0:
                           await close_button.first.click()
                           await detail_mask.wait_for(state="hidden", timeout=3000)
                      else:
                          if '/item/' in self.page.url:
                              await self.page.go_back()
                              await self.page.wait_for_selector("#app", state="visible", timeout=15000)
                              print("Navigated back after error and #app is visible.")
            except Exception as close_err:
                print(f"Error trying to close detail view after error: {close_err}")
            
            return None 
    
    async def scroll_page(self, distance=None):
        """Scroll the page to load more content"""
        if not self.page or self.page.is_closed():
             print("Error: Page is not available or closed before scrolling.")
             return False # Indicate failure
        if not distance:
            distance = random.randint(700, 1400) # Slightly larger scroll
        print(f"Scrolling down by {distance} pixels...")
        try:
            await self.page.mouse.wheel(0, distance)
            await asyncio.sleep(random.uniform(2.0, 3.0)) # Wait longer for content
            return True # Indicate success
        except Exception as e:
             print(f"Error during scrolling: {e}")
             return False # Indicate failure
    
    async def crawl_posts(self):
        """Crawl posts sequentially using data-index attribute."""
        if not self.page or self.page.is_closed():
             print("Error: Page is not available or closed at start of crawl_posts.")
             return []
        if not self.current_brand:
            print("No brand selected for crawling")
            return []

        posts_data = []
        expected_index = 0
        missing_index_attempts = 0
        stop_crawling = False

        print(f"Starting sequential crawl for {self.current_brand} from index {expected_index}")

        while missing_index_attempts < 3 and not stop_crawling:
            if not self.page or self.page.is_closed():
                print("Error: Page closed during crawl loop. Stopping.")
                stop_crawling = True
                break

            post_locator = self.page.locator(f'section.note-item[data-index="{expected_index}"]')
            post_element = None

            try:
                # Wait briefly for the specific element to potentially appear
                await post_locator.wait_for(state='attached', timeout=2000) # Wait for element to be in DOM
                if await post_locator.count() > 0:
                     # Check visibility as well before proceeding
                     if await post_locator.is_visible():
                          post_element = await post_locator.element_handle()
                          print(f"Found post with expected index {expected_index}.")
                     else:
                          print(f"Post with index {expected_index} found but not visible. Might need scroll.")
                          # Treat as missing for scroll logic
                # If count is 0 or not visible, post_element remains None
            except Exception:
                # Timeout waiting for attached state means it's likely not loaded yet
                print(f"Post with index {expected_index} not found in DOM yet.")
                pass # post_element is already None

            if post_element:
                # Found the expected post
                missing_index_attempts = 0 # Reset attempts

                # Check if it's a placeholder (no cover link)
                if await post_locator.locator('a.cover').count() == 0:
                    print(f"Index {expected_index} is a placeholder/ad. Skipping.")
                    expected_index += 1
                    await self._wait_randomly(0.1, 0.4) # Tiny pause before next index check
                    continue # Move to next expected index

                # Process the valid post element
                print(f"Processing post index {expected_index}...")
                post_data = await self.extract_post_data(post_element, expected_index)

                # Check if like threshold met or critical error occurred
                if post_data is None:
                    print(f"Stopping crawl for {self.current_brand}: Post {expected_index} below threshold or extraction failed.")
                    stop_crawling = True
                    break

                # Open detail view
                post_detail = await self.open_post_detail(post_element)

                if post_detail:
                    post_data.update(post_detail)
                    if "data_index" in post_data:
                        del post_data["data_index"] # Remove internal index before saving
                    posts_data.append(post_data)
                    print(f"Successfully processed post index {expected_index} (ID: {post_data.get('note_id', 'N/A')}).")
                else:
                    print(f"Failed to get details for post index {expected_index}. Skipping.")

                # Move to the next expected index
                expected_index += 1
                await asyncio.sleep(random.uniform(1.0, 2.0)) # Pause between processing posts

            else:
                # Expected post not found/visible
                missing_index_attempts += 1
                print(f"Post with index {expected_index} not found/visible. Scroll attempt {missing_index_attempts}/3...")

                if missing_index_attempts >= 3:
                    print(f"Could not find post index {expected_index} after {missing_index_attempts} scroll attempts. Stopping crawl for {self.current_brand}.")
                    stop_crawling = True
                    break

                # Scroll down to try and load the missing element
                if not await self.scroll_page():
                    print("Scrolling failed. Stopping crawl.")
                    stop_crawling = True
                    break
                # Loop will continue and try to find expected_index again after scroll

        print(f"Finished sequential crawl for {self.current_brand}. Processed up to index {expected_index -1}. Found {len(posts_data)} valid posts.")
        return posts_data
    
    async def save_data_to_json(self, data):
        """Save data for the current brand to a JSON file, overwriting if exists."""
        if not data:
            print(f"No data provided to save for brand {self.current_brand}.")
            return

        if not self.current_brand:
            print("Error: Cannot save data, current brand name is not set.")
            return

        # Ensure the data directory exists
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            # print(f"Ensured data directory exists: {self.data_dir.resolve()}") # Less verbose
        except OSError as e:
            print(f"Error creating data directory {self.data_dir}: {e}")
            return

        # Sanitize brand name for filename
        sanitized_brand_name = re.sub(r'[\\/:*?"<>|]', '_', self.current_brand)
        sanitized_brand_name = sanitized_brand_name[:100]
        filename = self.data_dir / f"{sanitized_brand_name}.json"

        # Save the data (overwrite existing file)
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                # Directly dump the passed 'data' list (contains only this brand's data)
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"Successfully saved data for {self.current_brand} to {filename}")
        except IOError as e:
            print(f"Error writing data to {filename}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred while saving data to {filename}: {e}")
    
    async def run(self):
        """Main method to run the crawler for all brands."""
        async with async_playwright() as p:
            if not await self.connect_to_existing_browser(p):
                print("Failed to connect to the browser session started by openbrowser.py.")
                print("Please ensure openbrowser.py is running and logged in.")
                return

            if not self.page or self.page.is_closed():
                print("Error: Page object is invalid after connection attempt. Exiting.")
                if self.browser and self.browser.is_connected():
                    # Attempt to close browser connection if possible
                    try: await self.browser.close()
                    except Exception: pass
                return

            # Ensure data directory exists before starting loop
            try:
                self.data_dir.mkdir(parents=True, exist_ok=True)
                print(f"Data directory ensured: {self.data_dir.resolve()}")
            except OSError as e:
                print(f"Fatal Error: Could not create data directory {self.data_dir}: {e}. Exiting.")
                # Attempt to close browser connection if possible
                if self.browser and self.browser.is_connected():
                    try: await self.browser.close()
                    except Exception: pass
                return

            playwright_instance = None
            brand_counter = 0 # Keep for logging if desired, but not for pausing

            try:
                async with async_playwright() as p:
                    playwright_instance = p
                    connected = await self.connect_to_existing_browser(playwright_instance)
                    if not connected:
                        print("Could not connect to existing browser. Exiting.")
                        return

                    print("\n--- Starting Brand Crawl ---")
                    self.window_start_time = time.monotonic() # Initialize timer window
                    print(f"Initialized post click limit timer window. Limit: {self.POST_CLICK_LIMIT} clicks per {self.TIME_WINDOW_SECONDS} seconds.")
                    brands = config.BRANDS # Corrected variable name
                    total_brands = len(brands)
                    print(f"Found {total_brands} brands in config.")

                    for i, brand in enumerate(brands):
                        print(f"\n--- Processing Brand {i+1}/{total_brands}: {brand} ---")
                        brand_counter += 1 # Increment counter for each brand processed

                        # --- Search and Crawl ---
                        if await self.search_brand(brand):
                            print(f"Starting post crawl for {brand}...")
                            brand_posts = await self.crawl_posts() # Returns list of posts for current brand
                            if brand_posts:
                                 print(f"Found {len(brand_posts)} posts for {brand} before saving.")
                                 await self.save_data_to_json(brand_posts) # Pass current brand's posts
                            else:
                                 print(f"No posts found or extracted for {brand}.")
                        else:
                            print(f"Failed to search or set up filter for brand: {brand}. Skipping.")

                        # --- Pause Logic Removed ---
                        # The old brand-based pause logic is removed.
                        # New time/click-based logic is in extract_post_data.

                    print("\n--- Brand Crawl Complete ---")

                    # --- Deduplication after all brands are processed --- Removed
                    # print("\n--- Starting Global Deduplication ---")
                    # await self.deduplicate_all_data()
                    # print("--- Global Deduplication Complete ---")

            except Exception as e:
                print(f"Error during brand crawl: {e}")
                # Explicitly disconnect (optional, as 'async with' handles it, but good practice with connect_over_cdp)
                if self.browser and self.browser.is_connected():
                   print("Disconnecting browser connection...")
                   try:
                       await self.browser.close()
                   except Exception as close_err:
                       print(f"Error during browser disconnect: {close_err}")

# Run crawler if script is executed directly
if __name__ == "__main__":
    crawler = XHSCrawler()
    asyncio.run(crawler.run()) 