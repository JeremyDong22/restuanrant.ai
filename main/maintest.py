# Updated by AI assistant: Replaced interactive prompts with configuration settings from main/config.py for full automation.
# Updated by AI assistant: Added user prompt to skip XHS login steps if already logged in.
# Updated by AI assistant: Modified run_script to stream output directly.
# Updated by AI assistant: Updated refresh.py and get_brand.py paths to dzdp_crawler and xhs_crawler folders respectively.
# Created by AI assistant.
# main/main.py
# Main controller script for the pipeline.

import os
import re
import sys
import subprocess # To run other scripts
import config as main_config # Import config from the same directory
# Import automation settings from config
from config import RELOCATE_EMULATOR, GET_NEW_XHS_COOKIE, OPEN_NEW_BROWSER, PERFORM_CLEANUP, KILL_BROWSER_PROCESS
import time # For sleeps and TIMER
import json
from datetime import datetime # For TIMER timestamp
from pathlib import Path

# Define paths relative to this script's location
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent # Assuming main.py is in a subdirectory like 'main'
DZDP_CRAWLER_DIR = PROJECT_ROOT / "dzdp_crawler"
XHS_CRAWLER_DIR = PROJECT_ROOT / "xhs_crawler"
DZDP_CONFIG_PATH = os.path.join(DZDP_CRAWLER_DIR, 'Config.py')
LOG_FILE_PATH = SCRIPT_DIR / "timer_log.txt" # Define log file path

def run_script(command, cwd, description):
    """
    Helper function to run a script using subprocess and stream its output.
    Handles errors.
    """
    executable_command = [sys.executable] + command
    print(f"\n--- Running: {description} --- ")
    print(f"Command: {' '.join(executable_command)}")
    print(f"Working Directory: {cwd}")
    try:
        # Run and let the output stream directly to the console
        process = subprocess.run(executable_command, check=True, cwd=cwd, text=True, encoding='utf-8')
        print(f"--- Finished: {description} (Exit Code: {process.returncode}) --- ")
        return True
    except FileNotFoundError:
        script_name = command[0] if command else "<unknown script>"
        print(f"Error: Could not find the Python executable '{sys.executable}' or script '{script_name}'. Check paths and permissions.")
        return False
    except subprocess.CalledProcessError as e:
        # Output was already streamed, just report the error
        print(f"Error running {description}. Exit code: {e.returncode}")
        # e.stdout and e.stderr will be None because we didn't capture
        # print("--- STDERR ---")
        # print(e.stderr)
        return False
    except Exception as e:
         print(f"An unexpected error occurred while running {description}: {e}")
         return False

def run_script_background(command, cwd, description):
    """Helper function to run a script in the background."""
    executable_command = [sys.executable] + command # Correct: Use the full command list
    print(f"\n--- Running in background: {description} --- ")
    print(f"Command: {' '.join(executable_command)}")
    print(f"Working Directory: {cwd}")
    try:
        # Use Popen for background process
        # Redirect stdout/stderr to DEVNULL if you don't need to see their output later
        process = subprocess.Popen(executable_command, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"--- Started Background Process (PID: {process.pid}): {description} --- ")
        # Return the process object so it can be managed later
        return process
    except FileNotFoundError:
        # Corrected index for script name in error message
        script_name = command[0] if command else "<unknown script>"
        print(f"Error: Could not find the Python executable '{sys.executable}' or script '{script_name}'. Check paths and permissions.")
        return None
    except Exception as e:
         print(f"An unexpected error occurred while starting background {description}: {e}")
         return None

def update_dzdp_cities():
    """Updates the search_cities list in dzdp_crawler/Config.py with the CITIES from main/config.py."""
    print("\n--- Updating DZDP Crawler Cities --- ")
    target_cities = main_config.CITIES
    if not isinstance(target_cities, list):
        print("Error: CITIES definition in main/config.py is not a list.")
        return False
    
    print(f"Target cities from main/config.py: {target_cities}")
    print(f"Target DZDP config file: {DZDP_CONFIG_PATH}")

    if not os.path.exists(DZDP_CONFIG_PATH):
        print(f"Error: DZDP config file not found at {DZDP_CONFIG_PATH}")
        return False

    try:
        with open(DZDP_CONFIG_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        start_line = -1
        end_line = -1
        in_cities_list = False

        # Find the existing search_cities list definition
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            # Simpler regex to find the start of the list assignment
            if re.match(r'^search_cities\s*=\s*\[', stripped_line):
                start_line = i
                in_cities_list = True
                # Check if list ends on the same line
                if ']' in stripped_line: # Check if closing bracket is anywhere on the line
                     end_line = i
                     break
            elif in_cities_list and stripped_line.startswith(']'): # Check if line starts with closing bracket
                 end_line = i
                 break

        if start_line != -1 and end_line != -1:
            # Construct the new list string
            formatted_cities = [f'    "{city.replace("\"", "\\\"")}",' # Comma moved outside f-string
                              for city in target_cities]
            new_cities_content = "search_cities = [\n" + '\n'.join(formatted_cities) + "\n]"
            
            # Add comment indicating it was updated
            new_cities_content += " # Updated by main/main.py\n"

            # Replace the old list definition
            new_lines = lines[:start_line] + [new_cities_content] + lines[end_line+1:]

            with open(DZDP_CONFIG_PATH, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            print(f"Successfully updated search_cities list in {DZDP_CONFIG_PATH}.")
            return True
        else:
            print("Error: Could not find the 'search_cities = [...] ' list definition in the DZDP config file.")
            print(f"Please check the format of {DZDP_CONFIG_PATH}.")
            return False
            
    except Exception as e:
        print(f"Error updating DZDP config file: {e}")
        import traceback
        traceback.print_exc()
        return False

# --- Main Pipeline Execution ---
if __name__ == "__main__":
    start_time = time.monotonic() # Record start time for duration calculation
    start_timestamp = datetime.now().strftime("%Y/%m/%d/%H/%M/%S")
    print(f"Pipeline started at: {start_timestamp}")

    browser_proc = None # Initialize browser process variable
    try:


        # --- Module 3: XHS Crawling (Keep capturing output) ---
        print("\n===== Module 3: XHS Crawling =======")
        # Step 3.1: Refresh brand table and get brands for config
        # Run refresh and get_brand sequentially for simplicity first
        # Async/parallel execution can be added later if needed and beneficial
      

        print("\nStep 3.1b: Getting brands and updating XHS config...")
        # Now uses the modified run_script with updated path to xhs_crawler

            # Step 3.2: Run XHS Crawler - Now uses the modified run_script
        if not run_script(["crawler.py"], cwd=XHS_CRAWLER_DIR, description="XHS Crawl Posts"):
            print("Error during XHS crawl. Stopping XHS module.")
        else:
            # Step 3.3: Upload Data - Now uses the modified run_script
            if not run_script(["upload.py"], cwd=XHS_CRAWLER_DIR, description="XHS Upload Data"):
                print("Error uploading XHS data.")
                # Decide if we should stop or attempt image upload anyway
            else:
                print("XHS data upload completed.")
                # Step 3.4: Direct Image Upload to Supabase - Now uses the modified run_script
                if not run_script(["image_direct_upload.py"], cwd=XHS_CRAWLER_DIR, description="XHS Direct Image Upload"):
                    print("Error during direct XHS image upload.")
                else:
                    print("XHS Crawling Module Completed Successfully.")


        print("===== Module 3: XHS Crawling & Image Upload Complete =====")

       
        print("Cleanup attempt finished.")
     
        print("=======================================")
        print("======= Pipeline Controller END =======")
        print("=======================================")

    except Exception as e:
        print(f"\n!!!!!!!! An unexpected error occurred in the main pipeline: {e} !!!!!!!!")
        import traceback
        traceback.print_exc()

    finally:
        # --- Timer Logging --- 
        end_time = time.monotonic()
        duration_seconds = end_time - start_time
        hours, remainder = divmod(duration_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        end_timestamp = datetime.now().strftime("%Y/%m/%d/%H/%M/%S")
        
        duration_str = f"{int(hours)}时{int(minutes)}分{seconds:.2f}秒"
        log_entry = f"{end_timestamp} - 总时长记录: {duration_str}\n"
        
        print(f"\nPipeline ended at: {end_timestamp}")
        print(f"Total execution time: {duration_str}")
        
        try:
            with open(LOG_FILE_PATH, 'a', encoding='utf-8') as f:
                f.write(log_entry)
            print(f"Execution time logged to: {LOG_FILE_PATH}")
        except Exception as log_e:
            print(f"Error writing to log file {LOG_FILE_PATH}: {log_e}")

        # --- Background Process Cleanup ---
        #if browser_proc and browser_proc.poll() is None: # Check if process exists and is running
        #    print("\nTerminating background browser process...")
        #    try:
        #        browser_proc.terminate() # Send SIGTERM first
        #    browser_proc.wait(timeout=5) # Wait a bit for graceful exit
        #    print("Background browser process terminated.")
        #    except subprocess.TimeoutExpired:
        #        print("Browser process did not terminate gracefully, forcing kill...")
        #        browser_proc.kill() # Force kill if terminate didn't work
        #        browser_proc.wait()
        #        print("Background browser process killed.")
        #    except Exception as term_e:
        #        print(f"Error terminating background browser process: {term_e}")

        print("=======================================")
        print("======= Pipeline Controller END =======")
        print("=======================================")

    print("\nPipeline Controller finished.") 