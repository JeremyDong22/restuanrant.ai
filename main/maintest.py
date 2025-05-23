# Updated by AI assistant: Replaced interactive prompts with configuration settings from main/config.py for full automation.
# Updated by AI assistant: Added user prompt to skip XHS login steps if already logged in.
# Updated by AI assistant: Modified run_script to stream output directly.
# Updated by AI assistant: Updated refresh.py and get_brand.py paths to dzdp_crawler and xhs_crawler folders respectively.
# Updated by AI assistant: Added step 3.4 to upload XHS images directly.
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

# --- Add project root to Python path --- 
# This ensures Python can find modules in sibling directories (like xhs_crawler)
# when running main.py directly.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
# --- End Path Addition ---

# --- Import the new content filter function --- 
from xhs_crawler.content_filter import filter_json_files
# --- Import XHS image upload function --- 
from xhs_crawler import image_direct_upload

# Define other necessary paths using the already defined PROJECT_ROOT and SCRIPT_DIR
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
        print("=======================================")
        print("=== Starting Pipeline Controller ====")
        print("=======================================")

        # --- Module 1: Preparation ---
        print("\n===== Module 1: Preparation =======")

        # --- Ask user about XHS login status ---
        #skip_xhs_login = input(\"Is a browser already open and logged into Xiaohongshu? (yes/no): \").strip().lower()
        # Decide XHS steps based on config flags

        #if skip_xhs_login != 'yes':
    
     


        # --- Module 3: XHS Crawling (Keep capturing output) ---
        print("\n===== Module 3: XHS Crawling =======")
        # Step 3.1: Refresh brand table and get brands for config
        # Run refresh and get_brand sequentially for simplicity first
        # Async/parallel execution can be added later if needed and beneficial
        print("\nStep 3.1a: Refreshing Brand Table...")
        # Now uses the modified run_script with updated path to dzdp_crawler
       
        # Step 3.3: Upload XHS Data
        print("\nStep 3.3: Uploading XHS Data (posts and relations)...")
        if not run_script(["upload.py"], cwd=XHS_CRAWLER_DIR, description="XHS Upload Data"):
                print("Error during XHS data upload. Stopping XHS module.")
        else:
                print("XHS data upload complete.")
                # --- ADDED STEP 3.4 --- 
                print("\nStep 3.4: Uploading XHS Images directly to Storage...")
                try:
                    # Call the main function from the imported image upload script
                    image_direct_upload.find_and_process_json_files()
                    print("XHS image direct upload process finished.")
                except Exception as img_upload_e:
                    print(f"Error during XHS image direct upload: {img_upload_e}")
                    # Decide if this should be fatal or just a warning
                    print("Continuing pipeline despite image upload error.")
                # --- END ADDED STEP 3.4 ---

        print("===== Module 3: XHS Crawling Complete =====")

        # --- Module 4: Cleanup (Conditional based on config) ---
        print("\n===== Module 4: Cleanup =======")
        # Always attempt cleanup if PERFORM_CLEANUP is True
        if PERFORM_CLEANUP:
            print("Performing cleanup based on config (PERFORM_CLEANUP=True)...")

            # Call main/clean.py
            print("   Attempting to run main/clean.py...")
            try:
                # Construct the path to clean.py relative to main.py
                main_dir = os.path.dirname(__file__)
                clean_script_path = os.path.join(main_dir, 'clean.py')
                clean_script_path = os.path.normpath(clean_script_path) # Normalize path

                if os.path.exists(clean_script_path):
                     # Use sys.executable to ensure the correct python interpreter
                    # Ensure cwd is the directory containing clean.py for relative paths within clean.py
                    result = subprocess.run(
                        [sys.executable, clean_script_path],
                        check=True, capture_output=True, text=True, cwd=main_dir
                    )
                    print(f"   main/clean.py executed successfully.")
                    # Log output if needed
                    # if result.stdout:
                    #     print(f"      Output:\n{result.stdout.strip()}")
                    # if result.stderr:
                    #      print(f"      Errors:\n{result.stderr.strip()}") # Should be empty if check=True passed
                else:
                    print(f"   Error: clean.py not found at {clean_script_path}")

            except subprocess.CalledProcessError as cpe:
                 print(f"   Error executing main/clean.py: Process returned non-zero exit code {cpe.returncode}")
                 print(f"      Stdout: {cpe.stdout.strip()}")
                 print(f"      Stderr: {cpe.stderr.strip()}")
            except Exception as clean_err:
                print(f"   Error running main/clean.py: {clean_err}")

        if KILL_BROWSER_PROCESS:
            print("Performing cleanup based on config (KILL_BROWSER_PROCESS=True)...")
            if browser_proc:
                print("   Terminating background browser process...")
                try:
                    browser_proc.terminate()
                    browser_proc.wait(timeout=5) # Wait a bit for graceful termination
                    print("   Browser process terminated.")
                except subprocess.TimeoutExpired:
                    print("   Browser process did not terminate gracefully, killing...")
                    browser_proc.kill()
                    print("   Browser process killed.")
                except Exception as term_err:
                    print(f"   Error terminating browser process: {term_err}")
            
            

            # Example: Add command to close emulator if needed (existing commented code)
            # print("   Attempting to close emulator (example - adjust command)...")
            # try:
            #    subprocess.run(["adb", "emu", "kill"], check=True, capture_output=True)
            #    print("   Emulator close command sent.")
            # except Exception as emu_err:
            #    print(f"   Error closing emulator: {emu_err}")
            
            print("Cleanup attempt finished.")
        else:
             print("Skipping cleanup based on config (PERFORM_CLEANUP=False).")
        
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